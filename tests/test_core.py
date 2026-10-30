"""Offline tests: a tiny index + a tiny git repo, no network."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import build_index

LAW_V1 = """---
title: "LEY DE PRUEBA"
identifier: "LP"
rank: "ley"
publication_date: "1917-02-05"
last_updated: "1917-02-05"
status: "in_force"
---
# LEY DE PRUEBA

## TITULO PRIMERO

###### Art. 1o.

Texto original del primero.

###### Art. 27.

La propiedad de las tierras corresponde a la Nación.
"""

LAW_V2 = (
    LAW_V1.replace("Texto original del primero.", "Texto reformado del primero.").replace(
        'last_updated: "1917-02-05"', 'last_updated: "2020-01-10"'
    )
    + "\n###### Artículo 27 Bis.\n\nNuevo artículo.\n"
)


def _git(repo: Path, *args: str, date: str | None = None) -> None:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
        "PATH": "/usr/bin:/bin:/opt/homebrew/bin",
    }
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "mx" / "aa").mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    law = repo / "mx" / "aa" / "LP.md"
    law.write_text(LAW_V1)
    _git(repo, "add", ".")
    # git cannot store pre-1970 dates: the commit says 1970, the trailer says 1917
    _git(
        repo,
        "commit",
        "-q",
        "-m",
        "[bootstrap] LEY DE PRUEBA\n\nSource-Date: 1917-02-05",
        date="1970-01-02T00:00:00Z",
    )
    law.write_text(LAW_V2)
    _git(
        repo,
        "commit",
        "-qam",
        "[reform] LEY DE PRUEBA — art. 1\n\nDisposition: DOF-1\nSource-Date: 2020-01-10",
        date="2020-01-10T00:00:00Z",
    )

    data = tmp_path / "data"
    for d in ("catalog", "meta", "failures", "sources/congreso-x"):
        (data / d).mkdir(parents=True)
    (data / "catalog" / "federal.jsonl").write_text(
        json.dumps(
            {
                "identifier": "LP",
                "id_ord": "1",
                "scope": "federal",
                "state": None,
                "title": "LEY DE PRUEBA",
                "status": "VIGENTE",
                "diputados_abbreviation": "LP",
            }
        )
        + "\n"
        + json.dumps(
            {
                "identifier": "FED-sin-texto-2",
                "id_ord": "2",
                "scope": "federal",
                "state": None,
                "title": "REGLAMENTO SIN TEXTO",
                "status": "VIGENTE",
            }
        )
        + "\n"
    )
    (data / "meta" / "FED-sin-texto-2.json").write_text(
        json.dumps(
            {
                "reforms": [
                    {
                        "position": 1,
                        "publication_date": "2001-01-01",
                        "category": "REGLAMENTO",
                        "pdf_url": "https://example.org/r.pdf",
                    }
                ]
            }
        )
    )
    (data / "sources" / "congreso-x" / "catalog.jsonl").write_text(
        json.dumps(
            {
                "source": "congreso-x",
                "doc_id": "a1",
                "title": "Bando de Policía de Villa Prueba",
                "state": "JAL",
                "municipality": "120",
                "url": "https://example.org/b.docx",
                "format": "docx",
                "status": "vigente",
            }
        )
        + "\n"
    )
    munis = tmp_path / "municipios.json"
    munis.write_text(json.dumps({"JAL": {"inegi": "14", "municipios": {"120": "Zapopan"}}}))
    censo = tmp_path / "censo"
    censo.mkdir()
    (censo / "censo-x.jsonl").write_text(
        json.dumps(
            {
                "state": "JAL",
                "inegi": "120",
                "name": "Zapopan",
                "classification": "abierta",
                "poblacion_2020": 1476491,
                "domain": "www.zapopan.gob.mx",
            }
        )
        + "\n"
    )

    db = tmp_path / "index.sqlite"
    build_index.build(data, repo, censo, munis, db)
    from legalize_mx_mcp import config, index

    monkeypatch.setattr(config, "INDEX_PATH", str(db))
    monkeypatch.setattr(config, "LOCAL_REPO", str(repo))
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    index.reset()
    yield
    index.reset()


def test_search_and_filters(env):
    from legalize_mx_mcp import core

    r = core.buscar_norma("ley prueba", estado="federal")["resultados"]
    assert r[0]["id"] == "LP" and r[0]["has_text"] is True
    r = core.buscar_norma("bando", municipio="Zapopan")["resultados"]
    assert [x["id"] for x in r] == ["congreso-x:a1"]
    assert core.buscar_norma("bando", estado="jal")["n"] == 1


def test_search_without_text_warns_about_ordering(env):
    from legalize_mx_mcp import core

    assert "aviso" in core.buscar_norma()
    assert "aviso" in core.buscar_norma("  ", estado="federal")
    assert "aviso" not in core.buscar_norma("ley prueba")


def test_read_current_and_by_date(env):
    from legalize_mx_mcp import core

    now = core.leer_norma("LP")
    assert "Texto reformado" in now["texto"]
    old = core.leer_norma("LP", fecha="1950-01-01")
    assert "Texto original" in old["texto"] and old["version"]["fecha"] == "1917-02-05"
    assert core.leer_norma("LP", fecha="1900-01-01")["error"]


def test_article_and_old_heading_style(env):
    from legalize_mx_mcp import core

    assert "propiedad" in core.articulo("LP", "27")["texto"]
    assert core.articulo("LP", "27 bis")["texto"] == "Nuevo artículo."
    assert core.articulo("LP", "primero")["articulo"] == "Art. 1o."
    assert "27 bis" not in [k for k, *_ in core.articles(LAW_V1)]


def test_history_and_diff(env):
    from legalize_mx_mcp import core

    h = core.historial("LP")
    assert [v["fecha"] for v in h["versiones"]] == ["1917-02-05", "2020-01-10"]
    d = core.diff("LP", "1950-01-01")
    assert d["articulos_reformados"] == ["1"] and d["articulos_adicionados"] == ["27 bis"]


def test_catalogued_only_gives_official_links(env):
    from legalize_mx_mcp import core

    r = core.leer_norma("FED-sin-texto-2")
    assert r["texto_disponible"] is False
    assert r["documentos_oficiales"][0]["url"] == "https://example.org/r.pdf"
    f = core.fuentes("congreso-x:a1")
    assert f["documentos_oficiales"][0]["url"] == "https://example.org/b.docx"


def test_coverage(env):
    from legalize_mx_mcp import core

    c = core.cobertura("JAL", "Zapopan")
    assert c["municipios"][0]["classification"] == "abierta"
    assert c["municipios"][0]["normas_indexadas"] == 1


def test_docx_extraction():
    import io
    import zipfile

    from legalize_mx_mcp import remote

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/'
            'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Artículo 1.</w:t></w:r></w:p>'
            "</w:body></w:document>",
        )
    assert remote._docx_text(buf.getvalue()) == "Artículo 1."


def test_index_is_readonly(env):
    from legalize_mx_mcp import index

    with pytest.raises(sqlite3.OperationalError):
        index.connect().execute("DELETE FROM norms")


def test_staleness_notice(env, monkeypatch):
    from legalize_mx_mcp import config, core, index

    index.connect()  # open the test index, then behave like a downloaded one
    monkeypatch.setattr(config, "INDEX_PATH", None)
    monkeypatch.setattr(index, "_manifest", lambda: {"version": "999912312359"})
    assert "más reciente" in core.buscar_norma("ley")["aviso_indice"]
    monkeypatch.setattr(index, "_manifest", lambda: {"version": index.meta()["version"]})
    (config.CACHE_DIR / "check.json").unlink(missing_ok=True)
    assert "aviso_indice" not in core.buscar_norma("ley")


def test_text_state_reported(env):
    from legalize_mx_mcp import core

    r = core.buscar_norma("ley prueba", estado="federal")["resultados"][0]
    assert (r["texto_estado"], r["fuente_texto"]) == ("point_in_time", "docx")
    assert "aviso_texto" not in core.leer_norma("LP")
    w = core._text_warning({"text_state": "as_enacted", "text_source": "ocr"})
    assert "tal como se publicó" in w and "OCR" in w
