"""From each run's transcript.jsonl write answer.md, tools.json and timing.json (+ tokens)."""

import json
import sys
from pathlib import Path

it = Path(sys.argv[1])
for tr in sorted(it.glob("eval-*/*/run-*/outputs/transcript.jsonl")):
    out = tr.parent
    tools, answer, usage, cost = [], "", {}, None
    for line in tr.read_text().splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "assistant":
            for c in d["message"].get("content", []):
                if c.get("type") == "tool_use":
                    tools.append({"tool": c["name"].split("__")[-1], "input": c["input"]})
        if d.get("type") == "result":
            answer = d.get("result") or ""
            usage = d.get("usage") or {}
            cost = d.get("total_cost_usd")
    (out / "answer.md").write_text(answer)
    (out / "tools.json").write_text(json.dumps(tools, ensure_ascii=False, indent=1))
    raw = out.parent / "timing_raw.json"
    t = json.loads(raw.read_text()) if raw.exists() else {}
    tokens = sum(usage.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                                             "cache_creation_input_tokens"))
    (out.parent / "timing.json").write_text(json.dumps(
        {"total_tokens": tokens, "duration_ms": t.get("total_duration_seconds", 0) * 1000,
         "total_duration_seconds": t.get("total_duration_seconds", 0), "cost_usd": cost}))
    print(f"{out.parent.parent.parent.name:42} {out.parent.parent.name:14} tools={len(tools):2} "
          f"{[x['tool'] for x in tools]} answer={len(answer)}c {t.get('total_duration_seconds')}s")
