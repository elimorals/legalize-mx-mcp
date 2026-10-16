#!/bin/zsh
# Runs every eval twice — with the plugin (MCP + skill) and with the MCP alone — in
# parallel headless Claude Code sessions. Usage: run_iteration.sh <iteration-dir>
set -u
REPO=~/Developer/legalize-mx-mcp
IT=${1:?iteration dir}
EVALS=$REPO/skills/legalize-mx/evals/evals.json
N=$(python3 -c "import json;print(len(json.load(open('$EVALS'))['evals']))")
for i in $(seq 0 $((N-1))); do
  NAME=$(python3 -c "import json;print(json.load(open('$EVALS'))['evals'][$i]['eval_name'])")
  PROMPT=$(python3 -c "import json;print(json.load(open('$EVALS'))['evals'][$i]['prompt'])")
  for CFG in with_skill without_skill; do
    OUT=$IT/eval-$NAME/$CFG/run-1/outputs
    mkdir -p $OUT
    WORK=$(mktemp -d)
    if [ $CFG = with_skill ]; then
      ARGS=(--plugin-dir $REPO --allowedTools "mcp__plugin_legalize-mx_legalize-mx__*" Skill ToolSearch)
    else
      ARGS=(--mcp-config $REPO/.mcp.json --allowedTools "mcp__legalize-mx__*" ToolSearch)
    fi
    (
      cd $WORK
      START=$(date +%s)
      claude -p "$PROMPT" "${ARGS[@]}" --output-format stream-json --verbose > $OUT/transcript.jsonl 2> $OUT/stderr.txt
      END=$(date +%s)
      echo "{\"total_duration_seconds\": $((END-START))}" > $OUT/../timing_raw.json
    ) &
  done
done
wait
echo done
