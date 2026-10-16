#!/bin/zsh
# Upload a built index (dist/index-*.sqlite.gz + latest.json) to the dataset's index/ folder.
# Old index files are removed after the new one is live, so the dataset keeps one copy.
set -e
DIST=${1:-dist}
REPO=${LEGALIZE_MX_HF_DATASET:-elimoralsmendox/legalize-mx}
FILE=$(python3 -c "import json;print(json.load(open('$DIST/latest.json'))['file'])")
hf upload "$REPO" "$DIST/$FILE" "index/$FILE" --repo-type dataset --commit-message "index: $FILE"
hf upload "$REPO" "$DIST/latest.json" index/latest.json --repo-type dataset --commit-message "index: latest → $FILE"
OLD=$(python3 - "$REPO" "$FILE" <<'EOF'
import json, sys, urllib.request
repo, keep = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(f"https://huggingface.co/api/datasets/{repo}/tree/main/index") as r:
    for x in json.load(r):
        if x["path"].endswith(".sqlite.gz") and not x["path"].endswith(keep):
            print(x["path"])
EOF
)
for old in ${(f)OLD}; do
  hf repo-files delete "$REPO" "$old" --repo-type dataset --commit-message "index: remove $old" >/dev/null
  echo "borrado $old"
done
echo "publicado index/$FILE"
