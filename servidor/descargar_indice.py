"""Build step: fetch the published index from Hugging Face into servidor/index.sqlite.

Each deploy ships the index that was current when it was built (stdlib only: runs before
dependencies are installed). Skips the download when the file is already there.
"""

import gzip
import hashlib
import json
import shutil
import sqlite3
import urllib.request
import zlib
from pathlib import Path

BASE = "https://huggingface.co/datasets/elimoralsmendox/legalize-mx/resolve/main/index"
OUT = Path(__file__).parent / "index.sqlite"


def get(url: str):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "legalize-mx-build"})
    )


if OUT.exists():
    print(f"{OUT.name} ya existe; no se descarga")
else:
    manifest = json.load(get(f"{BASE}/latest.json"))
    gz = OUT.with_suffix(".sqlite.gz")
    sha = hashlib.sha256()
    with get(f"{BASE}/{manifest['file']}") as r, gz.open("wb") as f:
        while chunk := r.read(1 << 20):
            sha.update(chunk)
            f.write(chunk)
    if sha.hexdigest() != manifest["sha256"]:
        raise SystemExit("el índice descargado no coincide con su sha256")
    with gzip.open(gz) as src, OUT.open("wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 20)
    gz.unlink()
    print(f"índice {manifest['version']}: {OUT.stat().st_size // 1_000_000} MB")

# A Vercel function is capped at 500 MB with its dependencies. `reforms` (SCJN publication
# lists, ~96 MB of JSON) is stored zlib-compressed; index.py inflates it when reading a row.
db = sqlite3.connect(OUT)
db.create_function(
    "deflate", 1, lambda s: zlib.compress(s.encode(), 9) if isinstance(s, str) else s
)
db.execute("UPDATE norms SET reforms = deflate(reforms) WHERE typeof(reforms) = 'text'")
db.commit()
db.execute("VACUUM")
db.close()
print(f"compactado: {OUT.stat().st_size // 1_000_000} MB")
