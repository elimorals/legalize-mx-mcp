"""Hardening: SSRF guard, size caps, XML entities, untrusted SQLite index."""

import io
import sqlite3
import zipfile

import pytest

from legalize_mx_mcp import config, remote


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://localhost:8000/",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://example.org/x",
        "gopher://example.org/",
    ],
)
def test_blocks_non_public_urls(url):
    with pytest.raises(remote.BlockedURL):
        remote.check_public_url(url)


def test_allows_public_ip_literal():
    remote.check_public_url("https://8.8.8.8/")  # a literal public address needs no DNS


def test_live_fetch_refuses_private_target():
    # fetch_and_extract goes through the guarded client, redirects included
    with pytest.raises(remote.BlockedURL):
        remote.fetch_and_extract("http://127.0.0.1:9/doc.pdf")


def _docx(xml: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


def test_docx_with_entities_rejected():
    bomb = (
        b'<?xml version="1.0"?><!DOCTYPE l [<!ENTITY a "aaaaaaaaaa">'
        b'<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]><w:document>&b;</w:document>'
    )
    with pytest.raises(ValueError, match="entidades"):
        remote._docx_text(_docx(bomb))


def test_docx_zip_bomb_rejected(monkeypatch):
    monkeypatch.setattr(config, "MAX_XML_BYTES", 1000)
    with pytest.raises(ValueError, match="anómalo"):
        remote._docx_text(_docx(b"<w:document>" + b"x" * 5000 + b"</w:document>"))


def test_index_schema_untrusted(tmp_path, monkeypatch):
    # A tampered index carrying a view that would call functions must not run them.
    db = tmp_path / "evil.sqlite"
    con = sqlite3.connect(db)
    con.executescript(
        "CREATE TABLE meta (key TEXT, value TEXT); INSERT INTO meta VALUES ('version','x');"
    )
    con.close()
    from legalize_mx_mcp import index

    monkeypatch.setattr(config, "INDEX_PATH", str(db))
    index.reset()
    try:
        conn = index.connect()
        assert conn.execute("PRAGMA trusted_schema").fetchone()[0] == 0
        with pytest.raises(sqlite3.OperationalError):  # read-only
            conn.execute("INSERT INTO meta VALUES ('a','b')")
    finally:
        index.reset()
