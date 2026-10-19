#!/bin/zsh
# Description optimization loop from skill-creator (claude -p, train/test split, 5 rounds).
# Usage: optimize_description.sh [model]
SC=${SKILL_CREATOR_DIR:?set SKILL_CREATOR_DIR to the skill-creator skill folder}
WS=~/Developer/legalize-mx-mcp/skills/legalize-mx-workspace
cd $SC
python3 -m scripts.run_loop \
  --eval-set $WS/trigger-eval.json \
  --skill-path ~/Developer/legalize-mx-mcp/skills/legalize-mx \
  --model ${1:-claude-opus-5-5} \
  --max-iterations 5 \
  --verbose
