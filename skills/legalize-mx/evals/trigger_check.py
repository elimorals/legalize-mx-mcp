"""Does the skill trigger with the real plugin installed? For each query, run a headless
Claude Code session with --plugin-dir and stop at the first tool call: triggered means the
Skill tool was called for legalize-mx before anything else answered the user.

Usage: python3 trigger_check.py <eval-set.json> [--runs N] [--workers N] [--timeout S]
"""

import argparse
import json
import os
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def one(query: str, timeout: int) -> dict:
    cmd = ["claude", "-p", query, "--plugin-dir", str(REPO), "--output-format", "stream-json",
           "--verbose", "--include-partial-messages"]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    start = time.time()
    tools: list[str] = []
    with tempfile.TemporaryDirectory() as cwd:
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        try:
            for line in p.stdout:
                if time.time() - start > timeout:
                    break
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("type") == "assistant":
                    for c in ev["message"].get("content", []):
                        if c.get("type") == "tool_use":
                            name = c["name"]
                            if name == "Skill":
                                name += ":" + str(c["input"].get("skill", ""))
                            tools.append(name)
                    # ToolSearch / other skills first are fine; decide once the skill or an
                    # MCP tool shows up, or after 4 tool calls.
                    if any("legalize-mx" in t for t in tools) or len(tools) >= 4:
                        break
                if ev.get("type") == "result":
                    break
        finally:
            p.kill()
    triggered = any(t.startswith("Skill:") and "legalize-mx" in t for t in tools)
    used_mcp = any("legalize-mx__" in t for t in tools)
    return {"triggered": triggered, "used_mcp": used_mcp, "tools": tools, "seconds": round(time.time() - start)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("eval_set", type=Path)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()
    items = json.loads(a.eval_set.read_text())
    jobs = [(i, it) for i, it in enumerate(items) for _ in range(a.runs)]
    with ThreadPoolExecutor(a.workers) as pool:
        results = list(pool.map(lambda j: (j[0], one(j[1]["query"], a.timeout)), jobs))
    per: dict[int, list[dict]] = {}
    for i, r in results:
        per.setdefault(i, []).append(r)
    tp = fp = tn = fn = 0
    rows = []
    for i, it in enumerate(items):
        rs = per[i]
        rate = sum(r["triggered"] for r in rs) / len(rs)
        ok = (rate >= 0.5) == it["should_trigger"]
        if it["should_trigger"]:
            tp += rate >= 0.5
            fn += rate < 0.5
        else:
            fp += rate >= 0.5
            tn += rate < 0.5
        rows.append({"query": it["query"][:90], "should": it["should_trigger"], "rate": rate, "ok": ok,
                     "first_tools": rs[0]["tools"][:3]})
    for r in rows:
        print(("✓" if r["ok"] else "✗"), "debe" if r["should"] else "no  ", f"{r['rate']:.0%}", r["query"], r["first_tools"])
    n = len(items)
    print(f"\naciertos {tp + tn}/{n} · recall {tp}/{tp + fn} · falsos positivos {fp}/{fp + tn}")
    out = a.eval_set.with_name(a.eval_set.stem + "-results.json")
    out.write_text(json.dumps({"rows": rows, "tp": tp, "fp": fp, "tn": tn, "fn": fn}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
