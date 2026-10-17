#!/bin/zsh
# Delete every index/*.sqlite.gz in the dataset except the one given.
# Usage: prune_index.sh <repo> <file-to-keep>
REPO=${1:?repo}
KEEP=${2:?file to keep}
LIST=$(uv run -q --no-project --with httpx python -c "
import sys, httpx
for x in httpx.get('https://huggingface.co/api/datasets/$REPO/tree/main/index', timeout=60).json():
    if x['path'].endswith('.sqlite.gz') and not x['path'].endswith('$KEEP'):
        print(x['path'])
")
for old in ${(f)LIST}; do
  hf repo-files delete "$REPO" "$old" --repo-type dataset >/dev/null && echo "borrado $old"
done
