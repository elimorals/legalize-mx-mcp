"""Build the search index the MCP downloads from Hugging Face (stdlib only).

    python3 scripts/build_index.py --data ~/Developer/legalize-mex/data-mx \
        --repo ~/Developer/legalize-mex/legalize-mx \
        --censo ~/Developer/legalize-mex/research-censo \
        --municipios ~/Developer/legalize-mex/pipeline/src/legalize/fetcher/mx/municipios.json \
        --out dist/

Writes dist/index-<version>.sqlite.gz and dist/latest.json. Upload both to the dataset's
``index/`` folder (scripts/publish_index.sh).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

HEAD_CHARS = 1500  # opening of each text indexed for full-text search
HEADINGS_CHARS = 2500  # titles/chapters (not articles) indexed too

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE norms (
  id TEXT PRIMARY KEY, title TEXT, origin TEXT, scope TEXT, state TEXT,
  municipality TEXT, municipality_fold TEXT, municipality_inegi TEXT,
  rank TEXT, status TEXT, publication_date TEXT, last_updated TEXT,
  has_text INTEGER, repo_path TEXT, url TEXT, page_url TEXT, format TEXT,
  text_note TEXT, reforms TEXT, extra TEXT,
  text_state TEXT,  -- point_in_time (consolidated) | as_enacted (as published) | NULL (no text)
  text_source TEXT  -- docx | pdf | ocr | NULL
);
CREATE VIRTUAL TABLE norms_fts USING fts5(
  id UNINDEXED, title, body, tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TABLE coverage (
  state TEXT, inegi TEXT, name TEXT, name_fold TEXT, classification TEXT, population INTEGER,
  domain TEXT, normatividad_url TEXT, gaceta_url TEXT, state_carrier TEXT, notes TEXT
);
"""

RANKS = (
    ("CONSTITUCION", "constitucion"),
    ("CODIGO", "codigo"),
    ("LEY ORGANICA", "ley_organica"),
    ("LEY GENERAL", "ley_general"),
    ("LEY FEDERAL", "ley_federal"),
    ("LEY DE INGRESOS", "ley_de_ingresos"),
    ("LEY", "ley"),
    ("REGLAMENTO", "reglamento"),
    ("BANDO", "bando"),
    ("ESTATUTO", "estatuto"),
    ("DECRETO", "decreto"),
    ("ACUERDO", "acuerdo"),
    ("LINEAMIENTOS", "lineamientos"),
    ("PRESUPUESTO", "presupuesto"),
    ("TRATADO", "tratado"),
    ("NORMA", "norma"),
    ("MANUAL", "manual"),
    ("REGLAS", "reglas"),
)


# Sources name a few ranks differently from the SCJN catalogue.
RANK_ALIASES = {
    "ley_ingresos": "ley_de_ingresos",
    "ley-ingresos": "ley_de_ingresos",
    "codigo_municipal": "codigo",
}


def fold(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def rank_of(title: str) -> str:
    t = fold(title).upper().lstrip('"“ ')
    return next((r for p, r in RANKS if t.startswith(p)), "otro")


def jsonl(path: Path):
    for line in path.read_text(errors="ignore").splitlines():
        if line.strip():
            try:
                yield json.loads(line)
            except ValueError:
                continue


def repo_laws(repo: Path) -> dict[str, dict]:
    """identifier → {path, frontmatter, head, headings} for every law in the git repo."""
    out = {}
    for md in repo.glob("mx*/**/*.md"):
        text = md.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---"):
            continue
        fm, _, body = text[4:].partition("\n---\n")
        meta = {}
        for line in fm.splitlines():
            k, sep, v = line.partition(":")
            if sep:
                meta[k.strip()] = v.strip().strip('"')
        heads = [
            h.lstrip("#").strip()
            for h in re.findall(r"(?m)^#{1,5} .+$", body)
            if not fold(h.lstrip("# ")).startswith("articulo")
        ]
        plain = re.sub(r"(?m)^#+ ", "", re.sub(r"<[^>]+>", "", body))
        out[meta.get("identifier") or md.stem] = {
            "path": str(md.relative_to(repo)),
            "meta": meta,
            "head": plain[:HEAD_CHARS],
            "headings": " · ".join(heads)[:HEADINGS_CHARS],
        }
    return out


def build(
    data: Path, repo: Path, censo: Path | None, municipios: Path | None, db_path: Path
) -> dict:
    db_path.unlink(missing_ok=True)
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    laws = repo_laws(repo)
    muni_names: dict[str, dict] = json.loads(municipios.read_text()) if municipios else {}
    no_docx = {
        r["identifier"]
        for p in (data / "failures").glob("*.jsonl")
        for r in jsonl(p)
        if r.get("kind") == "no_docx"
    }
    pdf_texts = (
        {p.stem for p in (data / "json-pdf").glob("*.json")}
        if (data / "json-pdf").exists()
        else set()
    )
    rows, fts = [], []

    # 1. SCJN catalogue (federal, CDMX, 31 states, treaties)
    for p in sorted((data / "catalog").glob("*.jsonl")):
        for e in jsonl(p):
            ident = e["identifier"]
            meta_path = data / "meta" / f"{ident}.json"
            reforms = []
            if meta_path.exists():
                for r in json.loads(meta_path.read_text()).get("reforms", []):
                    reforms.append(
                        {
                            k: r.get(k)
                            for k in (
                                "position",
                                "publication_date",
                                "category",
                                "gazette_section",
                                "docx_url",
                                "pdf_url",
                            )
                        }
                    )
            law = laws.get(ident)
            fm = law["meta"] if law else {}
            dated = [r["publication_date"] for r in reforms if r.get("publication_date")]
            extra = {k: v for k, v in (e.get("extra") or {}).items()}
            if e.get("docx_url"):
                extra["docx_url"] = e["docx_url"]
            if e.get("diputados_abbreviation"):
                extra["abbreviation"] = e["diputados_abbreviation"]
            status = fm.get("status") or (
                "in_force" if (e.get("status") or "").upper().startswith("VIGENTE") else "repealed"
            )
            note = None
            if not law:
                note = (
                    "texto extraído del PDF del periódico oficial, pendiente de publicar"
                    if ident in pdf_texts
                    else "la SCJN no publica Word de esta norma (solo el PDF del periódico oficial)"
                    if ident in no_docx
                    else "texto aún no procesado"
                )
            rows.append(
                (
                    ident,
                    e["title"],
                    "scjn",
                    e["scope"],
                    (
                        e.get("state")
                        or {"federal": "federal", "tratados": "federal", "cdmx": "CMX"}.get(
                            e["scope"]
                        )
                    ),
                    extra.get("municipality"),
                    fold(extra.get("municipality")),
                    extra.get("municipality_inegi"),
                    fm.get("rank")
                    or ("tratado" if e["scope"] == "tratados" else rank_of(e["title"])),
                    status,
                    fm.get("publication_date") or (min(dated) if dated else None),
                    fm.get("last_updated") or (max(dated) if dated else e.get("last_update")),
                    1 if law else 0,
                    law["path"] if law else None,
                    f"https://legislacion.scjn.gob.mx/Buscador/Paginas/wfOrdenamientoDetalle.aspx?IdOrd={e['id_ord']}&Vig=1&TPub=6",
                    None,
                    "docx" if e.get("docx_url") else "pdf",
                    note,
                    json.dumps(reforms, ensure_ascii=False) if reforms else None,
                    json.dumps(extra, ensure_ascii=False),
                    (fm.get("text_state") or "point_in_time") if law else None,
                    (fm.get("text_source") or "docx") if law else None,
                )
            )
            fts.append((ident, e["title"], (law["head"] + "\n" + law["headings"]) if law else ""))

    # 2. Every other official source (congresses, gazettes, municipal portals, DOF)
    for cat in sorted((data / "sources").glob("*/catalog.jsonl")):
        slug = cat.parent.name
        latest: dict[str, dict] = {}
        for r in jsonl(cat):
            if r.get("doc_id"):
                latest[r["doc_id"]] = r
        for doc_id, r in latest.items():
            state = r.get("state")
            mun = r.get("municipality")
            mname, minegi = None, None
            if mun and state in muni_names:
                code = str(mun)[-3:].zfill(3)
                mname = muni_names[state]["municipios"].get(code)
                minegi = muni_names[state]["inegi"] + code
            extra = dict(r.get("extra") or {})
            st = (r.get("status") or "").lower()
            rid = f"{slug}:{doc_id}"
            rows.append(
                (
                    rid,
                    r.get("title") or "",
                    slug,
                    "federal" if state == "federal" else ("municipal" if mun else "state"),
                    state,
                    mname,
                    fold(mname),
                    minegi,
                    RANK_ALIASES.get(r.get("rank_hint"), r.get("rank_hint"))
                    or rank_of(r.get("title") or ""),
                    "repealed"
                    if st.startswith("abrog")
                    else "in_force"
                    if st.startswith("vig")
                    else "unknown",
                    r.get("publication_date"),
                    r.get("last_reform_date") or r.get("publication_date"),
                    0,
                    None,
                    r.get("url"),
                    r.get("page_url"),
                    r.get("format"),
                    "documento oficial catalogado; el texto se extrae en vivo",
                    None,
                    json.dumps(extra, ensure_ascii=False, default=str),
                    None,
                    None,
                )
            )
            fts.append((rid, r.get("title") or "", ""))

    db.executemany(f"INSERT OR REPLACE INTO norms VALUES ({','.join('?' * 22)})", rows)
    db.executemany("INSERT INTO norms_fts (id, title, body) VALUES (?, ?, ?)", fts)
    db.execute("CREATE INDEX norms_state ON norms (state, municipality_inegi)")
    db.execute("CREATE INDEX norms_rank ON norms (rank)")
    db.execute("CREATE INDEX norms_origin ON norms (origin)")
    db.execute("CREATE INDEX norms_abbr ON norms (json_extract(extra, '$.abbreviation'))")

    # 3. National census of municipal sources
    n_cov = 0
    if censo:
        for p in sorted(censo.glob("censo-*.jsonl")):
            for c in jsonl(p):
                pop = c.get("poblacion_2020") or c.get("poblacion") or 0
                pop = pop.get("total", 0) if isinstance(pop, dict) else pop
                carrier = c.get("state_carrier")
                db.execute(
                    "INSERT INTO coverage VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        c.get("state"),
                        str(c.get("inegi") or "")[-3:].zfill(3),
                        c.get("name"),
                        fold(c.get("name")),
                        c.get("classification"),
                        int(pop or 0),
                        c.get("domain"),
                        c.get("normatividad_url"),
                        c.get("gaceta_url"),
                        json.dumps(carrier, ensure_ascii=False)
                        if isinstance(carrier, (dict, list))
                        else carrier,
                        (
                            c.get("notes")
                            if isinstance(c.get("notes"), str)
                            else json.dumps(c.get("notes"), ensure_ascii=False)
                        ),
                    ),
                )
                n_cov += 1
        db.execute("CREATE INDEX coverage_state ON coverage (state, inegi)")

    version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    stats = {
        "version": version,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "norms": str(len(rows)),
        "with_text": str(sum(r[12] for r in rows)),
        "sources": str(len({r[2] for r in rows})),
        "municipalities": str(n_cov),
    }
    db.executemany("INSERT INTO meta VALUES (?, ?)", stats.items())
    db.commit()
    db.execute("INSERT INTO norms_fts(norms_fts) VALUES ('optimize')")
    db.commit()
    db.execute("VACUUM")
    db.close()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--censo", type=Path)
    ap.add_argument("--municipios", type=Path)
    ap.add_argument("--out", type=Path, default=Path("dist"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    raw = a.out / "index.sqlite"
    stats = build(
        a.data.expanduser(),
        a.repo.expanduser(),
        a.censo.expanduser() if a.censo else None,
        a.municipios.expanduser() if a.municipios else None,
        raw,
    )
    name = f"index-{stats['version']}.sqlite.gz"
    with raw.open("rb") as src, gzip.open(a.out / name, "wb", compresslevel=6) as dst:
        shutil.copyfileobj(src, dst, 1 << 20)
    sha = hashlib.sha256((a.out / name).read_bytes()).hexdigest()
    manifest = {
        **stats,
        "file": name,
        "sha256": sha,
        "bytes": (a.out / name).stat().st_size,
        "sqlite_bytes": raw.stat().st_size,
    }
    (a.out / "latest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
