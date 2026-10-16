#!/bin/zsh
# Upload a built index (dist/index-*.sqlite.gz + latest.json) to the dataset's index/ folder.
# Old index files are removed after the new one is live, so the dataset keeps one copy.
set -e
DIST=${1:-dist}
REPO=${LEGALIZE_MX_HF_DATASET:-elimoralsmendox/legalize-mx}
FILE=$(python3 -c "import json;print(json.load(open('$DIST/latest.json'))['file'])")
hf upload "$REPO" "$DIST/$FILE" "index/$FILE" --repo-type dataset --commit-message "index: $FILE"
hf upload "$REPO" "$DIST/latest.json" index/latest.json --repo-type dataset --commit-message "index: latest → $FILE"
for old in $(hf api "datasets/$REPO/tree/main/index" 2>/dev/null | python3 -c "import json,sys;[print(x['path']) for x in json.load(sys.stdin) if x['path'].endswith('.sqlite.gz') and not x['path'].endswith('$FILE')]" 2>/dev/null); do
  hf repo-files delete "$REPO" "$old" --repo-type dataset 2>/dev/null || echo "no pude borrar $old (bórralo a mano)"
done
echo "publicado index/$FILE"
