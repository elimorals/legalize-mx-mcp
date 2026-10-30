"""The search index: a SQLite file (FTS5) published on Hugging Face, cached locally.

Built by ``scripts/build_index.py``. Tables:

* ``norms``     — one row per ordinance: SCJN catalogue + every other official source
                  (congresses, gazettes, municipal portals, DOF), text or not.
* ``norms_fts`` — full-text search over title + the opening of each text.
* ``coverage``  — the national census of municipal sources (one row per municipality).
* ``meta``      — version, build date, counts.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sqlite3
import threading
import time
import unicodedata
import zlib
from datetime import datetime, timezone
from pathlib import Path

import httpx

from legalize_mx_mcp import config

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


# Keys are folded (no accents, lower case). Codes are the ones the index uses.
_STATE_ALIASES = {
    "aguascalientes": "AGU",
    "baja california": "BCN",
    "baja california sur": "BCS",
    "campeche": "CAM",
    "chiapas": "CHP",
    "chihuahua": "CHH",
    "ciudad de mexico": "CMX",
    "cdmx": "CMX",
    "df": "CMX",
    "distrito federal": "CMX",
    "coahuila": "COA",
    "coahuila de zaragoza": "COA",
    "colima": "COL",
    "durango": "DUR",
    "guanajuato": "GUA",
    "guerrero": "GRO",
    "hidalgo": "HID",
    "jalisco": "JAL",
    "estado de mexico": "MEX",
    "edomex": "MEX",
    "mexico": "MEX",
    "michoacan": "MIC",
    "michoacan de ocampo": "MIC",
    "morelos": "MOR",
    "nayarit": "NAY",
    "nuevo leon": "NLE",
    "oaxaca": "OAX",
    "puebla": "PUE",
    "queretaro": "QUE",
    "queretaro de arteaga": "QUE",
    "quintana roo": "ROO",
    "san luis potosi": "SLP",
    "sinaloa": "SIN",
    "sonora": "SON",
    "tabasco": "TAB",
    "tamaulipas": "TAM",
    "tlaxcala": "TLA",
    "veracruz": "VER",
    "veracruz de ignacio de la llave": "VER",
    "yucatan": "YUC",
    "zacatecas": "ZAC",
    "federal": "federal",
    "fed": "federal",
}


def normalize_state(state: str) -> str:
    s = " ".join(_fold(state).split())
    return _STATE_ALIASES.get(s, state.strip().upper())


def _manifest() -> dict:
    return (
        httpx.get(
            f"{config.HF_BASE}/index/latest.json",
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.TIMEOUT,
            follow_redirects=True,
        )
        .raise_for_status()
        .json()
    )


def _download_index(force: bool = False) -> Path:
    """Fetch index/latest.json and, if newer than the cached copy, the index file."""
    cache = config.CACHE_DIR
    cache.mkdir(parents=True, exist_ok=True)
    pointer = cache / "index.json"
    current = json.loads(pointer.read_text()) if pointer.exists() else None
    fresh = current and time.time() - pointer.stat().st_mtime < config.INDEX_CHECK_HOURS * 3600
    if current and fresh and not force and (cache / current["local"]).exists():
        return cache / current["local"]
    headers = {"User-Agent": config.USER_AGENT}
    try:
        manifest = _manifest()
    except httpx.HTTPError:
        if current and (cache / current["local"]).exists():  # offline: keep using what we have
            return cache / current["local"]
        raise
    local = f"index-{manifest['version']}.sqlite"
    if current and current.get("version") == manifest["version"] and (cache / local).exists():
        pointer.touch()
        return cache / local
    tmp = cache / f"{local}.gz.part"
    sha = hashlib.sha256()
    with httpx.stream(
        "GET",
        f"{config.HF_BASE}/index/{manifest['file']}",
        headers=headers,
        timeout=config.TIMEOUT,
        follow_redirects=True,
    ) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                sha.update(chunk)
                f.write(chunk)
    if manifest.get("sha256") and sha.hexdigest() != manifest["sha256"]:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("the downloaded index does not match its checksum; try again")
    with gzip.open(tmp, "rb") as src, (cache / f"{local}.part").open("wb") as dst:
        written = 0
        while chunk := src.read(1 << 20):  # capped: a gzip bomb must not fill the disk
            written += len(chunk)
            if written > config.MAX_INDEX_BYTES:
                dst.close()
                (cache / f"{local}.part").unlink(missing_ok=True)
                tmp.unlink(missing_ok=True)
                raise RuntimeError("the index decompresses beyond the size cap; not used")
            dst.write(chunk)
    (cache / f"{local}.part").replace(cache / local)
    tmp.unlink(missing_ok=True)
    if current and current.get("local") != local:
        (cache / current["local"]).unlink(missing_ok=True)
    pointer.write_text(json.dumps({"version": manifest["version"], "local": local}))
    return cache / local


def connect() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            path = Path(config.INDEX_PATH) if config.INDEX_PATH else _download_index()
            _conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
            # The index is a downloaded file: treat its schema as untrusted (no triggers,
            # views or functions from it run with side effects).
            _conn.execute("PRAGMA trusted_schema = OFF")
            if hasattr(sqlite3, "SQLITE_DBCONFIG_DEFENSIVE"):  # Python 3.12+
                _conn.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
            _conn.row_factory = sqlite3.Row
        return _conn


def staleness() -> str | None:
    """A notice when the open index is behind the published one (checked at most once per
    INDEX_CHECK_HOURS) or older than STALE_DAYS; None when it is current."""
    if config.INDEX_PATH:
        return None
    version = meta().get("version", "")
    check = config.CACHE_DIR / "check.json"
    latest = None
    try:
        c = json.loads(check.read_text())
        if time.time() - c["checked"] < config.INDEX_CHECK_HOURS * 3600:
            latest = c["latest"]
    except (OSError, ValueError, KeyError):
        pass
    if latest is None:
        try:
            latest = _manifest()["version"]
            check.parent.mkdir(parents=True, exist_ok=True)
            check.write_text(json.dumps({"checked": time.time(), "latest": latest}))
        except (httpx.HTTPError, OSError, ValueError, KeyError):
            latest = version
    if latest > version:
        return (
            f"Hay un índice más reciente ({latest}; el tuyo es {version}). "
            "Ejecuta actualizar_indice() para usarlo."
        )
    try:
        built = datetime.fromisoformat(meta()["built"])
        days = (datetime.now(timezone.utc) - built).days
    except (KeyError, ValueError):
        return None
    if days > config.STALE_DAYS:
        return (
            f"El índice tiene {days} días: las normas publicadas después pueden faltar. "
            "Confirma lo reciente con dof_del_dia() o la fuente oficial."
        )
    return None


def update() -> dict:
    """Download the newest published index now and switch to it."""
    before = meta().get("version") if _conn is not None else None
    path = _download_index(force=True)
    reset()
    connect()
    after = meta().get("version")
    (config.CACHE_DIR / "check.json").unlink(missing_ok=True)
    return {"antes": before, "ahora": after, "archivo": str(path), "actualizado": before != after}


def reset() -> None:
    """Forget the open connection (tests, or after an index update)."""
    global _conn, _columns
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None
        _columns = None


def meta() -> dict[str, str]:
    return {r["key"]: r["value"] for r in connect().execute("SELECT key, value FROM meta")}


def _fts_query(text: str) -> str:
    """User words → an FTS5 query: every word must appear (prefix match on the last one)."""
    words = re.findall(r"\w+", _fold(text))
    if not words:
        return ""
    terms = [f'"{w}"' for w in words[:-1]] + [f'"{words[-1]}"*']
    return " AND ".join(terms)


def _norm(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    if isinstance(d.get("reforms"), bytes):  # the hosted index stores it zlib-compressed
        d["reforms"] = zlib.decompress(d["reforms"]).decode()
    return d


def row(rid: str) -> dict | None:
    return _norm(connect().execute("SELECT * FROM norms WHERE id = ?", (rid,)).fetchone())


def find(rid: str) -> dict | None:
    """By id, or by a law abbreviation (LFT, CPEUM…) or exact title as a convenience."""
    hit = row(rid)
    if hit:
        return hit
    r = (
        connect()
        .execute(
            "SELECT * FROM norms WHERE upper(json_extract(extra, '$.abbreviation')) = upper(?) "
            "OR title = ? COLLATE NOCASE ORDER BY has_text DESC LIMIT 1",
            (rid, rid),
        )
        .fetchone()
    )
    return _norm(r)


_columns: set[str] | None = None


def has_column(name: str) -> bool:
    global _columns
    if _columns is None:
        _columns = {r[1] for r in connect().execute("PRAGMA table_info(norms)")}
    return name in _columns


def search(
    text: str = "",
    state: str | None = None,
    municipality: str | None = None,
    rank: str | None = None,
    in_force: bool | None = None,
    with_text: bool | None = None,
    origin: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    where, args = [], []
    if state:
        where.append("n.state = ?")
        args.append(normalize_state(state))
    if municipality:
        if municipality.isdigit():
            where.append("(n.municipality_inegi = ? OR substr(n.municipality_inegi, -3) = ?)")
            args += [municipality, municipality.zfill(3)]
        else:
            where.append("n.municipality_fold LIKE ?")
            args.append(f"%{_fold(municipality)}%")
    if rank:
        where.append("n.rank = ?")
        args.append(rank)
    if in_force is not None:
        where.append("n.status = 'in_force'" if in_force else "n.status != 'in_force'")
    if with_text is not None:
        where.append("n.has_text = ?")
        args.append(1 if with_text else 0)
    if origin:
        where.append("n.origin = ?")
        args.append(origin)
    cols = (
        "n.id, n.title, n.origin, n.scope, n.state, n.municipality, n.rank, n.status, "
        "n.publication_date, n.last_updated, n.has_text, n.url"
    )
    if has_column("text_state"):  # indexes built before 2026-10-19 lack these
        cols += ", n.text_state AS texto_estado, n.text_source AS fuente_texto"
    q = _fts_query(text)
    if q:
        # Title hits first; among them laws with text, then shorter (closer) titles; body-only
        # hits after, by relevance.
        sql = (
            f"SELECT {cols}, snippet(norms_fts, 2, '«', '»', ' … ', 18) AS fragmento, "
            "(n.id IN (SELECT id FROM norms_fts WHERE norms_fts MATCH ?)) AS en_titulo "
            "FROM norms_fts f JOIN norms n ON n.id = f.id WHERE norms_fts MATCH ?"
        )
        args = [f"title : ({q})", q, *args]
        if where:
            sql += " AND " + " AND ".join(where)
        sql += (
            " ORDER BY en_titulo DESC, n.has_text DESC, length(n.title) * en_titulo,"
            " bm25(norms_fts, 0, 8.0, 1.0) LIMIT ? OFFSET ?"
        )
    else:
        sql = f"SELECT {cols}, NULL AS fragmento FROM norms n"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY n.has_text DESC, n.last_updated DESC LIMIT ? OFFSET ?"
    args += [limit, offset]
    return [dict(r) for r in connect().execute(sql, args)]


def coverage(state: str | None = None, municipality: str | None = None) -> dict:
    db = connect()
    out: dict = {}
    where, args = [], []
    if state:
        where.append("state = ?")
        args.append(normalize_state(state))
    w = (" WHERE " + " AND ".join(where)) if where else ""
    if municipality:
        mw = w + (" AND " if w else " WHERE ")
        if municipality.isdigit():
            mw += "(inegi = ? OR substr(inegi, -3) = ?)"
            margs = [*args, municipality, municipality.zfill(3)]
        else:
            mw += "name_fold LIKE ?"
            margs = [*args, f"%{_fold(municipality)}%"]
        munis = [dict(r) for r in db.execute(f"SELECT * FROM coverage{mw}", margs)]
        out["municipios"] = munis
        for m in munis:
            r = db.execute(
                "SELECT count(*) AS n, sum(has_text) AS t FROM norms "
                "WHERE state = ? AND substr(municipality_inegi, -3) = substr(?, -3)",
                (m["state"], m["inegi"]),
            ).fetchone()
            m["normas_indexadas"], m["con_texto"] = r["n"], r["t"] or 0
        return out
    nw = w.replace("state", "n.state") if w else ""
    out["normas"] = {
        r["origin"]: {"total": r["n"], "con_texto": r["t"]}
        for r in db.execute(
            f"SELECT origin, count(*) AS n, sum(has_text) AS t FROM norms n{nw} GROUP BY origin",
            args,
        )
    }
    out["por_rango"] = {
        r["rank"] or "?": r["n"]
        for r in db.execute(
            f"SELECT rank, count(*) AS n FROM norms n{nw} GROUP BY rank ORDER BY n DESC LIMIT 15",
            args,
        )
    }
    out["municipios_por_clasificacion"] = {
        r["classification"]: {"municipios": r["n"], "poblacion": r["p"]}
        for r in db.execute(
            f"SELECT classification, count(*) AS n, sum(population) AS p FROM coverage{w} "
            "GROUP BY classification ORDER BY n DESC",
            args,
        )
    }
    return out
