#!/bin/zsh
# Description optimization loop from skill-creator (claude -p, train/test split, 5 rounds).
# Usage: optimize_description.sh [model]
SC=/Users/elias/.claude/plugins/cache/claude-plugins-official/skill-creator/ea10b213686c/skills/skill-creator
WS=~/Developer/legalize-mx-mcp/skills/legalize-mx-workspace
cd $SC
python3 -m scripts.run_loop \
  --eval-set $WS/trigger-eval.json \
  --skill-path ~/Developer/legalize-mx-mcp/skills/legalize-mx \
  --model ${1:-claude-opus-5-5} \
  --max-iterations 5 \
  --verbose
