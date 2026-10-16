"""Everything fetched on demand: law text and history from the git repo, originals from
the official portals, and the DOF of a given day."""

from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

import httpx

from legalize_mx_mcp import config

_client: httpx.Client | None = None


def client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.TIMEOUT,
            follow_redirects=True,
        )
    return _client


# ---------------------------------------------------------------- git repo (text, history)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", config.LOCAL_REPO, *args], capture_output=True, text=True, check=True
    ).stdout


def text_at(path: str, ref: str | None = None) -> str:
    """The law's Markdown at a commit (default: the branch head)."""
    if config.LOCAL_REPO:
        return _git("show", f"{ref or 'HEAD'}:{path}")
    url = f"https://raw.githubusercontent.com/{config.GITHUB_REPO}/{ref or config.GITHUB_BRANCH}/{path}"
    return client().get(url).raise_for_status().text


def _parse_message(msg: str) -> dict:
    first, _, body = msg.partition("\n")
    m = re.match(r"\[([\w-]+)\]\s*(.*)", first)
    out = {"tipo": m.group(1) if m else None, "resumen": (m.group(2) if m else first).strip()}
    for key, field in (
        ("Disposition", "disposicion"),
        ("Change", "cambio"),
        ("Source-Id", "source_id"),
        ("Source-Date", "fecha"),
        ("Affected articles", "articulos_afectados"),
    ):
        hit = re.search(rf"^{key}:\s*(.+)$", body, re.MULTILINE)
        if hit:
            out[field] = hit.group(1).strip()
    return out


def history(path: str) -> list[dict]:
    """Every commit that touched the file, oldest first: date, type, decree, articles."""
    cache = config.CACHE_DIR / "history" / (hashlib.sha1(path.encode()).hexdigest() + ".json")
    if cache.exists() and time.time() - cache.stat().st_mtime < config.HISTORY_CACHE_HOURS * 3600:
        return json.loads(cache.read_text())
    commits = _history(path)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(commits, ensure_ascii=False))
    return commits


def _history(path: str) -> list[dict]:
    commits: list[dict] = []
    if config.LOCAL_REPO:
        out = _git("log", "--reverse", "--format=%H%x1f%ad%x1f%B%x1e", "--date=short", "--", path)
        for chunk in out.split("\x1e"):
            if not chunk.strip():
                continue
            sha, day, msg = chunk.strip("\n").split("\x1f", 2)
            commits.append({"sha": sha, "fecha_commit": day, **_parse_message(msg)})
        return commits
    headers = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    page = 1
    while True:
        r = client().get(
            f"https://api.github.com/repos/{config.GITHUB_REPO}/commits",
            params={"path": path, "sha": config.GITHUB_BRANCH, "per_page": 100, "page": page},
            headers=headers,
        )
        if r.status_code == 403 and "rate limit" in r.text.lower():
            raise RuntimeError(
                "GitHub limits anonymous API use to 60 requests/hour. Set GITHUB_TOKEN, or "
                "LEGALIZE_MX_REPO to a local clone of the repo."
            )
        r.raise_for_status()
        batch = r.json()
        for c in batch:
            commits.append(
                {
                    "sha": c["sha"],
                    "fecha_commit": c["commit"]["author"]["date"][:10],
                    **_parse_message(c["commit"]["message"]),
                }
            )
        if len(batch) < 100:
            break
        page += 1
    commits.reverse()
    return commits


def version_on(path: str, day: date) -> dict | None:
    """The last version in force on ``day``. Uses each commit's Source-Date trailer: git
    cannot store dates before 1970, so older commits carry 1970-01-02 as their commit date."""
    best = None
    for c in history(path):
        if (c.get("fecha") or c["fecha_commit"]) <= day.isoformat():
            best = c
    return best


# ---------------------------------------------------------------- official originals, live


def _docx_text(data: bytes) -> str:
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))
    paras = []
    for p in root.iter(f"{ns}p"):
        t = "".join(x.text or "" for x in p.iter(f"{ns}t"))
        if t.strip():
            paras.append(t)
    return "\n\n".join(paras)


def _pdf_text(data: bytes) -> str:
    if shutil.which("pdftotext"):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "doc.pdf"
            src.write_bytes(data)
            out = subprocess.run(
                ["pdftotext", "-layout", str(src), "-"],
                check=False,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if out.returncode == 0:
                return out.stdout
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF extraction needs poppler's pdftotext (brew install poppler / apt install "
            "poppler-utils) or `pip install legalize-mx-mcp[pdf]`."
        ) from exc
    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)


def _html_text(data: bytes) -> str:
    html = data.decode("utf-8", errors="ignore")
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h\d>|</li>", "\n", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", text)).strip()


def fetch_and_extract(url: str, max_chars: int = 5_000_000) -> dict:
    """Download an official document and return its text. Scanned PDFs come back (nearly)
    empty: they need OCR, which this live path does not do."""
    r = client().get(url)
    r.raise_for_status()
    data = r.content
    ctype = r.headers.get("content-type", "").lower()
    if data[:4] == b"%PDF":
        kind, text = "pdf", _pdf_text(data)
    elif data[:2] == b"PK":
        kind, text = "docx", _docx_text(data)
    elif data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return {
            "url": url,
            "formato": "doc",
            "texto": None,
            "nota": "Word 97-2003 (.doc): ábrelo con el enlace; la extracción en vivo no lo lee.",
        }
    elif "html" in ctype or data[:200].lstrip().lower().startswith((b"<!doctype", b"<html")):
        kind, text = "html", _html_text(data)
    else:
        return {
            "url": url,
            "formato": ctype or "desconocido",
            "texto": None,
            "nota": "formato no reconocido; usa el enlace",
        }
    text = text.strip()
    out = {"url": url, "formato": kind, "caracteres": len(text), "texto": text[:max_chars]}
    if len(text) > max_chars:
        out["nota"] = f"texto truncado a {max_chars} caracteres"
    if kind == "pdf" and len(text) < 200:
        out["nota"] = "el PDF parece escaneado (sin capa de texto): necesita OCR"
    return out


# ---------------------------------------------------------------- DOF, live

_SIDOF = "https://sidof.segob.gob.mx/dof/sidof"


def dof_day(day: date) -> list[dict]:
    """Every note the Diario Oficial de la Federación published that day (official API)."""
    r = client().get(f"{_SIDOF}/notas/{day:%d-%m-%Y}")
    r.raise_for_status()
    payload = r.json()
    notes = []
    for key in ("NotasMatutinas", "NotasVespertinas", "NotasExtraordinarias"):
        for n in payload.get(key) or []:
            if not (n.get("titulo") or "").strip():  # per-authority headers of the edition
                continue
            notes.append(
                {
                    "codigo": n.get("codNota"),
                    "titulo": n["titulo"].strip(),
                    "dependencia": n.get("codOrgaDos") or n.get("nombreCodOrgaUno"),
                    "seccion": n.get("codSeccion"),
                    "pagina": n.get("pagina"),
                    "edicion": key.removeprefix("Notas").lower(),
                    "url": f"https://www.dof.gob.mx/nota_detalle.php?codigo={n.get('codNota')}"
                    f"&fecha={day:%d/%m/%Y}",
                }
            )
    return notes


def dof_note(code: int | str, max_chars: int = 5_000_000) -> dict:
    """Full text of one DOF note."""
    r = client().get(f"{_SIDOF}/notas/nota/{code}")
    r.raise_for_status()
    nota = r.json().get("Nota") or {}
    text = _html_text((nota.get("cadenaContenido") or "").encode())
    return {
        "codigo": code,
        "titulo": (nota.get("titulo") or "").strip(),
        "fecha": nota.get("fecha"),
        "caracteres": len(text),
        "texto": text[:max_chars],
    }
