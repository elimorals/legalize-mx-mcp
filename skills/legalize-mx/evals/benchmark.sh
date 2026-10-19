#!/bin/zsh
# Grade, aggregate and build the static review page for one iteration.
# Usage: benchmark.sh <iteration-dir> [previous-iteration-dir]
set -e
IT=${1:?iteration dir}
SC=${SKILL_CREATOR_DIR:?set SKILL_CREATOR_DIR to the skill-creator skill folder}
python3 -I ~/Developer/legalize-mx-mcp/skills/legalize-mx/evals/extract.py "$IT"
python3 -I ~/Developer/legalize-mx-mcp/skills/legalize-mx/evals/grade.py "$IT"
(cd $SC && python3 -m scripts.aggregate_benchmark "$IT" --skill-name legalize-mx)
PREV=()
[ -n "${2:-}" ] && PREV=(--previous-workspace "$2")
python3 $SC/eval-viewer/generate_review.py "$IT" --skill-name legalize-mx \
  --benchmark "$IT/benchmark.json" --static "$IT/review.html" "${PREV[@]}"
