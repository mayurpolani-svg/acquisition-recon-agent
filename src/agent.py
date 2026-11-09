#!/usr/bin/env python3
"""
Acquisition reconciliation agent.

Claude investigates the data room with read-only tools (tie-out, mapping
review, GL queries, duplicate / accrual / large-item / intercompany scans),
decides what is a real error, explains the root cause, and proposes the
correcting entry. Output is scored against the seeded answer key, which the
agent never sees.

  python src/agent.py                 # full run (needs ANTHROPIC_API_KEY in .env)
  python src/agent.py --dry-run       # check tools without calling the API
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import agent_tools as T

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
DEFAULT_MODEL = "claude-sonnet-5-5"

SYSTEM = """You are a senior consolidation accountant on the post-acquisition integration team at Larkspur Restaurant Group.
Larkspur acquired Sparrow Pizza. Sparrow's NetSuite P&L for Q3 FY26 (Jul-Sep) was mapped and loaded into Larkspur's Oracle HFM.
Your job: reconcile NetSuite to HFM, find every error in either system, explain the root cause, and propose the fix.

Work like a controller:
1. get_overview first.
2. run_tieout. Explain every break. Approved, supported top-side journals (e.g. purchase accounting, policy alignment) are legitimate reconciling items, not errors. A journal posted twice is an error.
3. get_mapping. Review every row with judgment. HFM is loaded with this mapping, so a wrong mapping produces NO tie-out break; you must judge whether each account belongs where it is mapped (consider which entities are company-operated vs franchisor, comments, review status).
4. Run every scan: scan_duplicate_bills, scan_accrual_reversals, scan_large_items, intercompany_matching. These problems flow into both systems, so the tie-out cannot see them.
5. Use query_gl to confirm anything before you conclude. Reject false positives (e.g. coincidental equal amounts with different refs, routine items, legitimate one-offs).
6. Call submit_findings exactly once.

Issue types:
- MAPPING_ERROR: source account mapped to the wrong HFM account.
- UNMAPPED_ACCOUNT: source account missing from the mapping, so excluded from HFM.
- CUTOFF_TIMING: entry posted to a period after that period's HFM extract, so HFM shows it a month late.
- FX_TRANSLATION: CAD translated at the wrong rate.
- DUPLICATE_HFM_JOURNAL: top-side journal posted twice.
- SIGN_FLIP: a balance loaded with the wrong sign.
- DUPLICATE_GL_ENTRY: same vendor bill entered twice in NetSuite.
- MISSING_ACCRUAL_REVERSAL: month-end accrual never reversed, so the expense is double-counted.
- CAPEX_EXPENSED: a capital purchase booked to an expense account.
- INTERCOMPANY_MISMATCH: royalty income at SPZ_FR does not agree to the partner's royalty expense because of an error in the partner's books.
- OTHER: anything else that is genuinely wrong.

Finding rules:
- One finding per root cause. Do not split one cause into many findings; do not merge separate causes.
- amount_usd = size of the misstatement in USD, positive. For a sign flip, the misstatement is twice the balance. For FX, the total translation error across accounts.
- entity / period: use * only when one cause spans several (e.g. a mapping error across entities and months).
- hfm_account: the affected HFM account (for mapping errors, the wrong account the balance landed in; for FX, the largest affected account).
- source_account: required for anything that lives in NetSuite (duplicates, accruals, capex, intercompany, cutoff, unmapped, mapping errors).
- For cutoff, period = the period the entry belongs to. For a missing accrual reversal, period = the month that is overstated (where the reversal should have posted).
- evidence must cite specific IDs, amounts and timestamps. proposed_fix and correcting_entry must be specific enough to post.
Be thorough: check every scan result and every break. Be precise: no speculative findings."""


def load_env():
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def set_cache_breakpoint(messages):
    """Keep one moving cache breakpoint on the newest message so each turn reuses the prior prefix."""
    for m in messages:
        if isinstance(m["content"], list):
            for b in m["content"]:
                if isinstance(b, dict):
                    b.pop("cache_control", None)
    last = messages[-1]
    if isinstance(last["content"], str):
        last["content"] = [{"type": "text", "text": last["content"]}]
    last["content"][-1]["cache_control"] = {"type": "ephemeral"}


def block_to_dict(b):
    if b.type == "text":
        return {"type": "text", "text": b.text}
    if b.type == "tool_use":
        return {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input}
    return b.model_dump()


def run(model, max_turns, client=None):
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    OUT.mkdir(exist_ok=True)
    trace = open(OUT / "agent_trace.jsonl", "w")
    messages = [{"role": "user", "content": "Reconcile Sparrow Pizza Q3 FY26 NetSuite to Larkspur HFM. Investigate thoroughly, then submit your findings."}]
    system = [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}]
    usage = dict(input=0, output=0, cache_read=0, cache_write=0)
    submitted, nudges, calls, t0 = None, 0, 0, time.time()

    for turn in range(1, max_turns + 1):
        set_cache_breakpoint(messages)
        resp = client.messages.create(model=model, max_tokens=16000, system=system,
                                      tools=T.TOOL_SPECS, messages=messages)
        u = resp.usage
        usage["input"] += u.input_tokens
        usage["output"] += u.output_tokens
        usage["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
        usage["cache_write"] += getattr(u, "cache_creation_input_tokens", 0) or 0
        messages.append({"role": "assistant", "content": [block_to_dict(b) for b in resp.content]})

        results = []
        for b in resp.content:
            if b.type == "text" and b.text.strip():
                print(f"  \033[90m{b.text.strip()[:220]}\033[0m")
            if b.type != "tool_use":
                continue
            calls += 1
            args = b.input or {}
            shown = ", ".join(f"{k}={v}" for k, v in args.items() if k not in ("findings", "summary"))
            print(f"→ {b.name}({shown})")
            if b.name == "submit_findings":
                submitted = args
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": "Findings received."})
                continue
            out = T.call(b.name, args)
            trace.write(json.dumps({"turn": turn, "tool": b.name, "args": args, "result_chars": len(out)}) + "\n")
            results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})

        if submitted is not None:
            break
        if results:
            messages.append({"role": "user", "content": results})
        elif nudges < 2:
            nudges += 1
            messages.append({"role": "user", "content": "Continue the investigation, then call submit_findings."})
        else:
            break
    trace.close()
    return submitted, usage, calls, turn, time.time() - t0


def write_outputs(sub, usage, calls, turns, secs, model):
    findings = sub.get("findings", [])
    cols = ["finding_id", "issue_type", "entity", "period", "hfm_account", "source_account", "amount_usd",
            "evidence", "root_cause", "proposed_fix", "correcting_entry"]
    with open(OUT / "agent_findings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, x in enumerate(findings, 1):
            w.writerow({c: x.get(c, "") for c in cols} | {"finding_id": f"A-{i:03d}"})

    total = sum(float(x.get("amount_usd") or 0) for x in findings)
    md = ["# Reconciliation memo — Sparrow Pizza → Larkspur HFM, Q3 FY26",
          "*Synthetic data. Prepared by the reconciliation agent for controller review.*", "",
          "## Summary", sub.get("summary", ""), "",
          f"**{len(findings)} findings · ${total:,.0f} total misstatement**", "",
          "| # | Type | Entity | Period | Account | Amount (USD) | Root cause |", "|---|---|---|---|---|--:|---|"]
    for i, x in enumerate(findings, 1):
        acct = " / ".join(a for a in [str(x.get("hfm_account") or ""), str(x.get("source_account") or "")] if a)
        md.append(f"| A-{i:03d} | {x.get('issue_type')} | {x.get('entity')} | {x.get('period')} | {acct} | "
                  f"{float(x.get('amount_usd') or 0):,.0f} | {str(x.get('root_cause', '')).replace('|', '/')} |")
    md += ["", "## Proposed corrections", ""]
    for i, x in enumerate(findings, 1):
        md += [f"**A-{i:03d} · {x.get('issue_type')}** — {x.get('proposed_fix', '')}  ",
               f"Entry: `{x.get('correcting_entry', '') or 'n/a'}`  ", f"Evidence: {x.get('evidence', '')}", ""]
    md += ["---", f"Model `{model}` · {turns} turns · {calls} tool calls · {secs:,.0f}s · "
                  f"tokens in {usage['input']:,} (cache read {usage['cache_read']:,}, cache write {usage['cache_write']:,}) / out {usage['output']:,}"]
    (OUT / "agent_report.md").write_text("\n".join(md) + "\n")


def dry_run():
    for spec in T.TOOL_SPECS:
        if spec["name"] == "submit_findings":
            continue
        out = T.call(spec["name"], {})
        status = "ERROR" if '"error"' in out[:20] else "ok"
        print(f"{status:5} {spec['name']:24} {len(out):>7,} chars")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("RECON_MODEL", DEFAULT_MODEL))
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        return dry_run()
    load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Missing ANTHROPIC_API_KEY. Add it to a .env file in the project folder:\n  ANTHROPIC_API_KEY=sk-ant-...")
    print(f"Reconciliation agent · model {a.model}\n")
    sub, usage, calls, turns, secs = run(a.model, a.max_turns)
    if not sub:
        sys.exit("Agent stopped without submitting findings. See outputs/agent_trace.jsonl.")
    write_outputs(sub, usage, calls, turns, secs, a.model)
    print(f"\n{len(sub.get('findings', []))} findings → outputs/agent_findings.csv, outputs/agent_report.md\n")
    subprocess.run([sys.executable, str(ROOT / "src" / "evaluate.py"), str(OUT / "agent_findings.csv"),
                    "--label", f"Agent ({a.model})"], check=False)


if __name__ == "__main__":
    main()
