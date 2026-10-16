"""Where the data lives. Every value can be overridden by an environment variable."""

from __future__ import annotations

import os
from pathlib import Path

from legalize_mx_mcp import __version__

# Hugging Face dataset holding the search index (index/latest.json + the index file).
HF_DATASET = os.environ.get("LEGALIZE_MX_HF_DATASET", "elimoralsmendox/legalize-mx")
HF_BASE = f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main"

# Public git repo with one Markdown file per law and one commit per reform.
GITHUB_REPO = os.environ.get("LEGALIZE_MX_GITHUB_REPO", "elimorals/legalize-mx")
GITHUB_BRANCH = os.environ.get("LEGALIZE_MX_GITHUB_BRANCH", "main")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

CACHE_DIR = Path(os.environ.get("LEGALIZE_MX_CACHE", Path.home() / ".cache" / "legalize-mx"))
# A local index file skips the download (useful offline or for development).
INDEX_PATH = os.environ.get("LEGALIZE_MX_INDEX")
# A local clone of the git repo answers text/history without network.
LOCAL_REPO = os.environ.get("LEGALIZE_MX_REPO")

USER_AGENT = f"legalize-mx-mcp/{__version__} (+https://github.com/elimorals/legalize-mx-mcp)"
TIMEOUT = float(os.environ.get("LEGALIZE_MX_TIMEOUT", "60"))
# Law histories change at most daily: cache them this long (GitHub allows 60 anonymous calls/h).
HISTORY_CACHE_HOURS = float(os.environ.get("LEGALIZE_MX_HISTORY_CACHE_HOURS", "24"))
# Re-check the index manifest at most this often.
INDEX_CHECK_HOURS = float(os.environ.get("LEGALIZE_MX_INDEX_CHECK_HOURS", "24"))
