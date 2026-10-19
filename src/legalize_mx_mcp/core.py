"""The tools, as plain functions returning JSON-able dicts. server.py and cli.py wrap them."""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from datetime import date

from legalize_mx_mcp import config, index, remote

ORDINALS = {
    "primero": "1",
    "segundo": "2",
    "tercero": "3",
    "cuarto": "4",
    "quinto": "5",
    "sexto": "6",
    "septimo": "7",
    "octavo": "8",
    "noveno": "9",
    "decimo": "10",
    "unico": "unico",
}
_NORMATIVE = re.compile(
    r"\b(DECRETO|ACUERDO|REGLAMENTO|NORMA OFICIAL|NOM-|LINEAMIENTOS?|REGLAS|DISPOSICIONES|"
    r"CIRCULAR|ESTATUTO|MANUAL|RESOLUCI[ÓO]N MISCEL[ÁA]NEA|CRITERIOS|LEY)\b",
    re.IGNORECASE,
)
_NOT_NORMATIVE = re.compile(
    r"^\s*(AVISO|CONVOCATORIA|EDICTO|LICITACI|FE DE ERRATAS)", re.IGNORECASE
)


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _notice(out: dict) -> dict:
    """Attach a notice when the local index is behind the published one or old."""
    try:
        msg = index.staleness()
    except Exception:  # noqa: BLE001 — a failed freshness check must not break an answer
        msg = None
    if msg:
        out["aviso_indice"] = msg
    return out


def _text_warning(meta: dict) -> str | None:
    """What the reader must know about a text that is not a consolidated version."""
    parts = []
    if meta.get("text_state") == "as_enacted":
        parts.append(
            "Texto tal como se publicó en el periódico oficial: no incorpora reformas posteriores "
            "(historial() lista las que tuvo; sus textos están en los documentos oficiales)."
        )
    if meta.get("text_source") == "ocr":
        parts.append(
            "Obtenido por OCR de un documento escaneado: puede tener errores de lectura en "
            "palabras y cifras; verifica lo importante con el PDF oficial (fuentes())."
        )
    elif meta.get("text_source") == "pdf":
        parts.append("Extraído de la capa de texto del PDF oficial; el formato puede variar.")
    return " ".join(parts) or None


def _not_found(rid: str) -> dict:
    return {
        "error": f"no encontré la norma {rid!r}",
        "sugerencia": "usa buscar_norma para obtener su id",
    }


def _split(markdown: str) -> tuple[dict, str]:
    """(frontmatter as a flat dict, body). The frontmatter is simple `key: "value"` YAML."""
    if not markdown.startswith("---"):
        return {}, markdown
    fm, _, body = markdown[4:].partition("\n---\n")
    meta = {}
    for line in fm.splitlines():
        k, sep, v = line.partition(":")
        if sep:
            meta[k.strip()] = v.strip().strip('"')
    return meta, body.lstrip("\n")


def _page(text: str, offset: int, max_chars: int) -> dict:
    chunk = text[offset : offset + max_chars]
    out = {"texto": chunk, "caracteres_totales": len(text), "desde": offset}
    if offset + max_chars < len(text):
        out["siguiente_desde"] = offset + max_chars
        out["nota"] = f"texto parcial; pide desde={offset + max_chars} para continuar"
    return out


def _article_key(label: str) -> str:
    t = _fold(label)
    t = re.sub(r"^(art[ií]culo|art\.)\s*", "", t)
    t = re.sub(r"[°º.\-–:]", " ", t)
    t = re.sub(r"(\d+)\s*o\b", r"\1", t)  # 1o → 1
    words = t.split()
    words = [ORDINALS.get(w, w) for w in words]
    return " ".join(words).strip()


def articles(body: str) -> list[tuple[str, str, str]]:
    """(key, heading, text) for every '#… Artículo N' section of a law's Markdown."""
    out = []
    parts = re.split(r"(?m)^(#{1,6} .*)$", body)
    for i in range(1, len(parts), 2):
        heading = parts[i].lstrip("#").strip()
        if re.match(r"(articulo\b|art\.)", _fold(heading)):  # 1917 texts say "Art. 27."
            out.append((_article_key(heading), heading, parts[i + 1].strip()))
    return out


# ------------------------------------------------------------------------------- tools


def buscar_norma(
    texto: str = "",
    estado: str | None = None,
    municipio: str | None = None,
    tipo: str | None = None,
    vigente: bool | None = None,
    con_texto: bool | None = None,
    fuente: str | None = None,
    limite: int = 20,
    desde: int = 0,
) -> dict:
    rows = index.search(texto, estado, municipio, tipo, vigente, con_texto, fuente, limite, desde)
    for r in rows:
        r["has_text"] = bool(r["has_text"])
    return _notice(
        {
            "resultados": rows,
            "n": len(rows),
            "siguiente_desde": desde + len(rows) if len(rows) == limite else None,
        }
    )


def leer_norma(
    id: str,
    fecha: str | None = None,
    desde: int = 0,
    max_caracteres: int = 60_000,
    extraer_en_vivo: bool = False,
) -> dict:
    n = index.find(id)
    if not n:
        return _not_found(id)
    head = {
        k: n[k]
        for k in (
            "id",
            "title",
            "origin",
            "state",
            "municipality",
            "rank",
            "status",
            "publication_date",
            "last_updated",
        )
    }
    if n["has_text"] and n["repo_path"]:
        ref, version = None, None
        if fecha:
            version = remote.version_on(n["repo_path"], date.fromisoformat(fecha))
            if version is None:
                return {
                    **head,
                    "error": f"la norma no existía el {fecha}",
                    "publicada": n["publication_date"],
                }
            ref = version["sha"]
        meta, body = _split(remote.text_at(n["repo_path"], ref))
        out = {
            **head,
            "texto_estado": meta.get("text_state", "point_in_time"),
            "fuente_texto": meta.get("text_source", "docx"),
            "vigente_al": (version or {}).get("fecha") or meta.get("last_updated"),
            **_page(body, desde, max_caracteres),
        }
        warning = _text_warning(meta)
        if warning:
            out["aviso_texto"] = warning
        if version:
            out["version"] = {
                "fecha": version.get("fecha") or version["fecha_commit"],
                **{k: version.get(k) for k in ("tipo", "disposicion", "sha")},
            }
        out["fuente_oficial"] = n["url"]
        return out
    docs = _documents(n)
    out = {
        **head,
        "texto_disponible": False,
        "motivo": n["text_note"] or "aún no tenemos el texto procesado de esta norma",
        "documentos_oficiales": docs,
    }
    if not extraer_en_vivo:
        out["nota"] = "pasa extraer_en_vivo=true para bajar y extraer el documento oficial ahora"
        return out
    if fecha:
        out["nota"] = (
            "la extracción en vivo da el documento tal como se publicó, no una versión por fecha"
        )
    if n["origin"] == "dof":  # DOF notes come from its API, not as a file
        try:
            note = remote.dof_note(n["id"].split(":", 1)[1])
        except Exception as exc:  # noqa: BLE001 — the DOF API is down or slow
            out["error"] = f"no pude leer la nota del DOF: {exc}"
            return out
        if not note["caracteres"]:
            page = json.loads(n["extra"] or "{}").get("page")
            out["nota"] = (
                "el DOF no publica esta nota como texto: solo está en el PDF de la edición"
                + (f", página {page}" if page else "")
                + "; usa los documentos_oficiales"
            )
            return out
        out["extraido_en_vivo"] = {"fuente": "API del DOF", "caracteres": note["caracteres"]}
        out.update(_page(note["texto"], desde, max_caracteres))
        return out
    best = next(
        (d for d in docs if d.get("url") and d.get("tipo") in ("docx", "texto", "html")), None
    ) or next((d for d in docs if d.get("url")), None)
    if not best:
        out["error"] = "la fuente no enlaza ningún documento descargable"
        return out
    try:
        live = remote.fetch_and_extract(best["url"])
    except Exception as exc:  # noqa: BLE001 — the portal is down, blocked, or moved
        out["error"] = f"no pude bajar el documento oficial: {exc}"
        return out
    out["extraido_en_vivo"] = {k: v for k, v in live.items() if k != "texto"}
    if live.get("texto"):
        out.update(_page(live["texto"], desde, max_caracteres))
    return out


def _documents(n: dict) -> list[dict]:
    docs: list[dict] = []
    extra = json.loads(n["extra"] or "{}")
    if n["origin"] == "scjn":
        reforms = json.loads(n["reforms"] or "[]")
        if extra.get("docx_url"):
            docs.append(
                {"tipo": "docx", "descripcion": "texto vigente (SCJN)", "url": extra["docx_url"]}
            )
        for r in sorted(reforms, key=lambda r: -r.get("position", 0)):
            for kind, field in (("docx", "docx_url"), ("pdf", "pdf_url")):
                if r.get(field):
                    docs.append(
                        {
                            "tipo": kind,
                            "descripcion": f"{r.get('category') or 'publicación'} · {r.get('gazette_section') or ''}".strip(
                                " ·"
                            ),
                            "fecha": r.get("publication_date"),
                            "url": r[field],
                        }
                    )
    else:
        docs.append(
            {
                "tipo": n["format"],
                "descripcion": f"documento en {n['origin']}",
                "url": n["url"],
                "fecha": n["publication_date"],
            }
        )
        for k, v in extra.items():
            if isinstance(v, str) and v.startswith("http") and v != n["url"]:
                docs.append({"tipo": k.replace("_url", ""), "url": v})
    if n["page_url"]:
        docs.append(
            {"tipo": "ficha", "descripcion": "página oficial de la norma", "url": n["page_url"]}
        )
    return docs


def historial(id: str) -> dict:
    n = index.find(id)
    if not n:
        return _not_found(id)
    out = {"id": n["id"], "title": n["title"]}
    if n["has_text"] and n["repo_path"]:
        commits = remote.history(n["repo_path"])
        out["versiones"] = [
            {
                "fecha": c.get("fecha") or c.get("fecha_commit"),
                **{
                    k: c.get(k)
                    for k in ("tipo", "disposicion", "cambio", "articulos_afectados", "sha")
                },
            }
            for c in commits
        ]
        out["n_versiones"] = len(commits)
        out["repo"] = (
            f"https://github.com/{config.GITHUB_REPO}/commits/{config.GITHUB_BRANCH}/{n['repo_path']}"
        )
    reforms = json.loads(n["reforms"] or "[]")
    if reforms:
        out["publicaciones_scjn"] = [
            {
                "fecha": r.get("publication_date"),
                "categoria": r.get("category"),
                "seccion": r.get("gazette_section"),
                "pdf": r.get("pdf_url"),
                "docx": r.get("docx_url"),
            }
            for r in sorted(reforms, key=lambda r: -r.get("position", 0))
        ]
    if "versiones" not in out and "publicaciones_scjn" not in out:
        out["nota"] = "la fuente no registra reformas de esta norma"
    return out


def diff(id: str, fecha_a: str, fecha_b: str | None = None, max_caracteres: int = 40_000) -> dict:
    n = index.find(id)
    if not n:
        return _not_found(id)
    if not (n["has_text"] and n["repo_path"]):
        return {
            "id": n["id"],
            "error": "sin historial de texto para esta norma; usa historial() y fuentes()",
        }
    va = remote.version_on(n["repo_path"], date.fromisoformat(fecha_a))
    vb = remote.version_on(n["repo_path"], date.fromisoformat(fecha_b)) if fecha_b else None
    if va is None:
        return {"id": n["id"], "error": f"la norma no existía el {fecha_a}"}
    _, a = _split(remote.text_at(n["repo_path"], va["sha"]))
    _, b = _split(remote.text_at(n["repo_path"], vb["sha"] if vb else None))
    # Compared article by article: a whole-text diff of a 16,000-line law misaligns.
    # The first occurrence of a number is the body's (transitories restart numbering).
    arts_a: dict[str, str] = {}
    arts_b: dict[str, str] = {}
    for k, _, t in articles(a):
        arts_a.setdefault(k, t)
    for k, _, t in articles(b):
        arts_b.setdefault(k, t)
    reformed = sorted(
        (k for k in arts_a.keys() & arts_b.keys() if arts_a[k] != arts_b[k]), key=_natural
    )
    added = sorted(arts_b.keys() - arts_a.keys(), key=_natural)
    removed = sorted(arts_a.keys() - arts_b.keys(), key=_natural)
    out = {
        "id": n["id"],
        "version_a": va.get("fecha") or va["fecha_commit"],
        "version_b": ((vb or {}).get("fecha") or (vb or {}).get("fecha_commit")) or "vigente",
        "articulos_reformados": reformed,
        "articulos_adicionados": added,
        "articulos_derogados_o_eliminados": removed,
        "cambios": [],
    }
    used = 0
    for kind, keys in (("reformado", reformed), ("adicionado", added), ("eliminado", removed)):
        for k in keys:
            before, after = arts_a.get(k, ""), arts_b.get(k, "")
            change = {"articulo": k, "tipo": kind}
            if kind == "reformado":
                change["diff"] = "\n".join(
                    difflib.unified_diff(
                        before.splitlines(),
                        after.splitlines(),
                        "antes",
                        "despues",
                        lineterm="",
                        n=0,
                    )
                )
            else:
                change["texto"] = after or before
            size = len(json.dumps(change, ensure_ascii=False))
            if used + size > max_caracteres:
                out["nota"] = (
                    f"se muestran {len(out['cambios'])} cambios de "
                    f"{len(reformed) + len(added) + len(removed)}; sube max_caracteres "
                    "o pide articulo(id, numero, fecha) para el resto"
                )
                return out
            out["cambios"].append(change)
            used += size
    return out


def _natural(key: str) -> tuple:
    m = re.match(r"(\d+)\s*(.*)", key)
    return (0, int(m.group(1)), m.group(2)) if m else (1, 0, key)


def articulo(id: str, numero: str, fecha: str | None = None) -> dict:
    n = index.find(id)
    if not n:
        return _not_found(id)
    if not (n["has_text"] and n["repo_path"]):
        return {"id": n["id"], "error": "sin texto procesado; usa leer_norma(extraer_en_vivo=true)"}
    ref = None
    if fecha:
        v = remote.version_on(n["repo_path"], date.fromisoformat(fecha))
        if v is None:
            return {"id": n["id"], "error": f"la norma no existía el {fecha}"}
        ref = v["sha"]
    meta, body = _split(remote.text_at(n["repo_path"], ref))
    want = _article_key(numero)
    hits = [(h, t) for k, h, t in articles(body) if k == want]
    if not hits:
        keys = [k for k, _, _ in articles(body)]
        close = difflib.get_close_matches(want, keys, n=5)
        return {
            "id": n["id"],
            "error": f"no encontré el artículo {numero!r}",
            "parecidos": close,
            "total_articulos": len(keys),
        }
    # Decrees open with "ARTÍCULO PRIMERO.- Se expide…" and transitories restart numbering:
    # prefer a heading written the way it was asked (digits vs ordinal word), then the first.
    digits = bool(re.match(r"\d", numero.strip()))
    hits.sort(key=lambda h: bool(re.search(r"\d", h[0])) != digits)
    out = {"id": n["id"], "title": n["title"], "articulo": hits[0][0], "texto": hits[0][1]}
    if len(hits) > 1:
        out["otras_coincidencias"] = [{"articulo": h, "texto": t[:2000]} for h, t in hits[1:4]]
        out["nota"] = "hay más de un artículo con ese número (p. ej. en transitorios)"
    warning = _text_warning(meta)
    if warning:
        out["aviso_texto"] = warning
    return out


def fuentes(id: str) -> dict:
    n = index.find(id)
    if not n:
        return _not_found(id)
    out = {
        "id": n["id"],
        "title": n["title"],
        "origen": n["origin"],
        "documentos_oficiales": _documents(n),
    }
    if n["origin"] == "scjn":
        out["ficha_scjn"] = n["url"]
    if n["has_text"] and n["repo_path"]:
        out["markdown_versionado"] = (
            f"https://github.com/{config.GITHUB_REPO}/blob/{config.GITHUB_BRANCH}/{n['repo_path']}"
        )
        out["historial_git"] = (
            f"https://github.com/{config.GITHUB_REPO}/commits/{config.GITHUB_BRANCH}/{n['repo_path']}"
        )
    out["dataset"] = f"https://huggingface.co/datasets/{config.HF_DATASET}"
    return out


def cobertura(estado: str | None = None, municipio: str | None = None) -> dict:
    out = _notice(index.coverage(estado, municipio))
    out["indice"] = {
        k: v for k, v in index.meta().items() if k in ("version", "built", "norms", "with_text")
    }
    return out


def dof_del_dia(fecha: str | None = None, solo_normativas: bool = True) -> dict:
    day = date.fromisoformat(fecha) if fecha else date.today()
    notes = remote.dof_day(day)
    if solo_normativas:
        notes = [
            x
            for x in notes
            if _NORMATIVE.search(x["titulo"]) and not _NOT_NORMATIVE.match(x["titulo"])
        ]
    return {
        "fecha": day.isoformat(),
        "fuente": "API oficial del DOF (en vivo)",
        "n": len(notes),
        "notas": notes,
    }


def leer_nota_dof(codigo: str, desde: int = 0, max_caracteres: int = 60_000) -> dict:
    note = remote.dof_note(codigo)
    text = note.pop("texto")
    return {**note, **_page(text, desde, max_caracteres)}


def actualizar_indice() -> dict:
    return index.update()


def info() -> dict:
    return _notice(
        {
            "indice": index.meta(),
            "repo": config.GITHUB_REPO,
            "dataset": config.HF_DATASET,
            "cache": str(config.CACHE_DIR),
        }
    )
