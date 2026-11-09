#!/usr/bin/env python3
"""
Baseline: the standard tie-out a finance team runs by hand.

  NetSuite GL  --(mapping file)-->  expected HFM  vs  actual HFM extract

Rolls the GL up through the mapping, translates CAD at Treasury average
rates, compares to HFM by entity / period / account, and lists every break
over $1. It also flags GL accounts missing from the mapping.

What it cannot do: explain *why* a break exists, see errors baked into the
mapping itself, or catch problems that flow into both systems (duplicate
bills, missing reversals, capex expensed, intercompany mismatches).
That is the job of the agent.

Run:  python src/baseline_recon.py   ->  outputs/baseline_findings.csv
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
PERIODS = ["Jul", "Aug", "Sep"]
TOLERANCE = 1.00

gl = pd.read_csv(D / "sparrow_netsuite" / "SPZ_GL_Detail_FY26Q3_IncomeStatement.csv")
coa = pd.read_csv(D / "sparrow_netsuite" / "SPZ_Chart_of_Accounts.csv")
ents = pd.read_csv(D / "reference" / "Entity_Map.csv")
fx = pd.read_csv(D / "reference" / "LRG_Treasury_FX_Rates_FY26Q3.csv").set_index("Period")
mapping = pd.read_excel(D / "mapping" / "SPZ_to_LRG_CoA_Mapping_v3_DRAFT.xlsx", header=4)
hfm = pd.read_excel(D / "larkspur_hfm" / "LRG_HFM_Extract_SPZ_FY26Q3.xlsx", header=6)

# ---- GL -> natural-sign local amounts
gl["acct"] = gl["Account"].str.split().str[0].astype(int)
gl["entity"] = gl["Subsidiary"].map(dict(zip(ents.NetSuite_Subsidiary, ents.HFM_Entity)))
gl["period"] = gl["Period"].str[:3]
credit_natural = set(coa.loc[coa["Normal Balance"] == "Credit", "Account"])
net_cr = gl["Credit"].fillna(0) - gl["Debit"].fillna(0)
gl["natural"] = net_cr.where(gl.acct.isin(credit_natural), -net_cr)

# ---- unmapped accounts
amap = dict(zip(mapping["SPZ Account"], mapping["LRG HFM Account"]))
findings = []
unm = gl[~gl.acct.isin(amap)].groupby(["entity", "period", "acct"]).natural.sum().reset_index()
for r in unm.itertuples():
    findings.append(dict(issue_type="UNMAPPED_ACCOUNT", entity=r.entity, period=r.period, hfm_account="",
                         source_account=r.acct, amount_usd=round(r.natural, 2),
                         evidence=f"GL account {r.acct} has activity but no mapping row",
                         root_cause="", proposed_fix=""))

# ---- expected HFM from GL
gl["hfm_account"] = gl.acct.map(amap)
exp = gl.dropna(subset=["hfm_account"]).groupby(["entity", "period", "hfm_account"]).natural.sum().reset_index()
ccy = dict(zip(ents.HFM_Entity, ents.Functional_Currency))
exp["expected"] = [round(n * (fx.loc[p, "Average_Rate"] if ccy[e] == "CAD" else 1.0), 2)
                   for e, p, n in zip(exp.entity, exp.period, exp.natural)]

# ---- actual HFM
act = hfm.melt(id_vars=["Entity", "Account"], value_vars=PERIODS, var_name="period", value_name="actual")
act = act.rename(columns={"Entity": "entity", "Account": "hfm_account"})
act = act.groupby(["entity", "period", "hfm_account"]).actual.sum().reset_index()

cmp = exp.merge(act, on=["entity", "period", "hfm_account"], how="outer").fillna({"expected": 0, "actual": 0})
cmp["diff"] = (cmp.actual - cmp.expected).round(2)
breaks = cmp[cmp["diff"].abs() > TOLERANCE]
for r in breaks.itertuples():
    findings.append(dict(issue_type="UNCLASSIFIED", entity=r.entity, period=r.period, hfm_account=r.hfm_account,
                         source_account="", amount_usd=r.diff,
                         evidence=f"HFM {r.actual:,.2f} vs GL-mapped {r.expected:,.2f}",
                         root_cause="", proposed_fix=""))

out = pd.DataFrame(findings)
out.insert(0, "finding_id", [f"B-{i:03d}" for i in range(1, len(out) + 1)])
(ROOT / "outputs").mkdir(exist_ok=True)
out.to_csv(ROOT / "outputs" / "baseline_findings.csv", index=False)
print(f"Baseline tie-out: {len(breaks)} breaks over ${TOLERANCE:.2f}, {len(unm)} unmapped account-periods "
      f"-> outputs/baseline_findings.csv")
