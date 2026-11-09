#!/usr/bin/env python3
"""
Score a findings file against the seeded answer key.

  python src/evaluate.py outputs/baseline_findings.csv --label "Rules baseline"

Findings schema (CSV, one row per finding):
  finding_id, issue_type, entity, period, hfm_account, source_account,
  amount_usd, evidence, root_cause, proposed_fix
  - entity / period accept "*" for "all"
  - give hfm_account, source_account, or both

A finding matches a seeded issue when entity and period agree and either
account agrees with one of the issue's affected cells (source-data issues
must cite the NetSuite account). Each finding counts
toward one issue (same issue_type preferred, then closest amount).
Findings that match nothing are false positives.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def norm(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip()
    return s[:-2] if s.endswith(".0") else s


def cell_hit(f, c, source_only=False):
    if f["entity"] not in ("*", c["entity"]) or f["period"] not in ("*", c["period"]):
        return False
    src = bool(f["source_account"]) and f["source_account"] == norm(c["source_account"])
    if source_only:  # NetSuite data-quality issues must be pinned to the NetSuite account
        return src
    return src or (bool(f["hfm_account"]) and f["hfm_account"] == c["hfm_account"])


def closeness(amount, issue, cells):
    targets = [abs(c["impact_usd"]) for c in cells if c["impact_usd"]] + [issue["impact_usd"]]
    return min(abs(abs(amount) - t) / max(t, 1) for t in targets)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings")
    ap.add_argument("--key", default=str(ROOT / "answer_key" / "seeded_issues.json"))
    ap.add_argument("--label", default="Submission")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    key = json.loads(Path(a.key).read_text())
    issues = key["issues"]
    fdf = pd.read_csv(a.findings, dtype=str).fillna("")
    found = {i["issue_id"]: [] for i in issues}
    fps, amount_ok = [], 0

    for _, row in fdf.iterrows():
        f = {k: norm(row.get(k, "")) for k in ["finding_id", "issue_type", "entity", "period", "hfm_account", "source_account"]}
        amt = float(row.get("amount_usd") or 0)
        cands = []
        for iss in issues:
            hits = [c for c in iss["cells"] if cell_hit(f, c, iss["category"] == "Source data quality")]
            if hits:
                cands.append((iss["issue_type"] != f["issue_type"], closeness(amt, iss, hits), iss["issue_id"]))
        if not cands:
            fps.append(f["finding_id"])
            continue
        _, dist, iid = min(cands)
        found[iid].append((f["issue_type"], dist))
        amount_ok += dist <= 0.05

    n = len(issues)
    det = [i for i in issues if found[i["issue_id"]]]
    cls = [i for i in det if any(t == i["issue_type"] for t, _ in found[i["issue_id"]])]
    total_usd = sum(i["impact_usd"] for i in issues)
    det_usd = sum(i["impact_usd"] for i in det)
    matched = len(fdf) - len(fps)

    by_type = {}
    for i in issues:
        t = by_type.setdefault(i["issue_type"], [0, 0, 0])
        t[0] += 1
        t[1] += i in det
        t[2] += i in cls

    lines = [f"# Scorecard - {a.label}", "",
             f"Benchmark: {key['dataset']}  ", f"Findings file: `{Path(a.findings).name}` ({len(fdf)} rows)", "",
             "| Metric | Result |", "|---|---|",
             f"| Issues detected | **{len(det)} / {n}** ({len(det) / n:.0%}) |",
             f"| Root cause classified correctly | **{len(cls)} / {n}** ({len(cls) / n:.0%}) |",
             f"| Dollar impact surfaced | ${det_usd:,.0f} of ${total_usd:,.0f} ({det_usd / total_usd:.0%}) |",
             f"| Precision (findings tied to a real issue) | {matched} / {len(fdf)} ({(matched / len(fdf)) if len(fdf) else 0:.0%}) |",
             f"| False positives | {len(fps)} |",
             f"| Findings with amount within 5% | {amount_ok} / {matched} |", "",
             "| Issue type | Seeded | Detected | Classified |", "|---|---:|---:|---:|"]
    for t, (s, d_, c_) in sorted(by_type.items()):
        lines.append(f"| {t} | {s} | {d_} | {c_} |")
    lines += ["", "**Missed:** " + (", ".join(i["issue_id"] for i in issues if i not in det) or "none")]
    if fps:
        lines.append(f"**False positives:** {', '.join(fps)}")
    md = "\n".join(lines) + "\n"
    print(md)
    out = Path(a.out) if a.out else ROOT / "outputs" / (Path(a.findings).stem.replace("_findings", "") + "_scorecard.md")
    out.write_text(md)


if __name__ == "__main__":
    main()
