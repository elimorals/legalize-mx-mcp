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
import shutil
import sqlite3
import threading
import time
import unicodedata
from pathlib import Path

import httpx

from legalize_mx_mcp import config

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


_STATE_ALIASES = {
    "cdmx": "CMX",
    "df": "CMX",
    "ciudad de mexico": "CMX",
    "edomex": "MEX",
    "estado de mexico": "MEX",
    "nuevo leon": "NLE",
    "jalisco": "JAL",
    "federal": "federal",
    "fed": "federal",
}


def normalize_state(state: str) -> str:
    s = _fold(state).strip()
    return _STATE_ALIASES.get(s, "federal" if s == "federal" else state.strip().upper())


def _download_index() -> Path:
    """Fetch index/latest.json and, if newer than the cached copy, the index file."""
    cache = config.CACHE_DIR
    cache.mkdir(parents=True, exist_ok=True)
    pointer = cache / "index.json"
    current = json.loads(pointer.read_text()) if pointer.exists() else None
    fresh = current and time.time() - pointer.stat().st_mtime < config.INDEX_CHECK_HOURS * 3600
    if current and fresh and (cache / current["local"]).exists():
        return cache / current["local"]
    headers = {"User-Agent": config.USER_AGENT}
    try:
        manifest = (
            httpx.get(
                f"{config.HF_BASE}/index/latest.json",
                headers=headers,
                timeout=config.TIMEOUT,
                follow_redirects=True,
            )
            .raise_for_status()
            .json()
        )
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
        shutil.copyfileobj(src, dst, 1 << 20)
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
            _conn.row_factory = sqlite3.Row
        return _conn


def reset() -> None:
    """Forget the open connection (tests, or after an index update)."""
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None


def meta() -> dict[str, str]:
    return {r["key"]: r["value"] for r in connect().execute("SELECT key, value FROM meta")}


def _fts_query(text: str) -> str:
    """User words → an FTS5 query: every word must appear (prefix match on the last one)."""
    words = re.findall(r"\w+", _fold(text))
    if not words:
        return ""
    terms = [f'"{w}"' for w in words[:-1]] + [f'"{words[-1]}"*']
    return " AND ".join(terms)


def row(rid: str) -> dict | None:
    r = connect().execute("SELECT * FROM norms WHERE id = ?", (rid,)).fetchone()
    return dict(r) if r else None


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
    return dict(r) if r else None


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
