"""
Tools the reconciliation agent can call.

Each tool is a plain read-only query over the data room (never the answer
key). Deterministic code does the arithmetic; the model does the judgment:
which breaks are real, why they happened, and how to fix them.
"""
import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
PERIODS = ["Jul", "Aug", "Sep"]
NEXT = {"Jul": "Aug", "Aug": "Sep"}
ISSUE_TYPES = ["MAPPING_ERROR", "UNMAPPED_ACCOUNT", "CUTOFF_TIMING", "FX_TRANSLATION", "DUPLICATE_HFM_JOURNAL",
               "SIGN_FLIP", "DUPLICATE_GL_ENTRY", "MISSING_ACCRUAL_REVERSAL", "CAPEX_EXPENSED",
               "INTERCOMPANY_MISMATCH", "OTHER"]


def _ts(s):
    return datetime.strptime(s.strip().upper(), "%m/%d/%Y %I:%M %p")


@lru_cache(maxsize=1)
def data():
    ents = pd.read_csv(D / "reference" / "Entity_Map.csv")
    sub2ent = dict(zip(ents.NetSuite_Subsidiary, ents.HFM_Entity))
    ccy = dict(zip(ents.HFM_Entity, ents.Functional_Currency))
    fx = pd.read_csv(D / "reference" / "LRG_Treasury_FX_Rates_FY26Q3.csv")
    avg = dict(zip(fx.Period, fx.Average_Rate))
    coa = pd.read_csv(D / "sparrow_netsuite" / "SPZ_Chart_of_Accounts.csv")
    cr = set(coa.loc[coa["Normal Balance"] == "Credit", "Account"])

    gl = pd.read_csv(D / "sparrow_netsuite" / "SPZ_GL_Detail_FY26Q3_IncomeStatement.csv", dtype={"Ref No.": str})
    g = pd.DataFrame({
        "iid": gl["Internal ID"], "doc": gl["Document Number"], "type": gl["Type"],
        "date": pd.to_datetime(gl["Date"], format="%m/%d/%Y"), "period": gl["Period"].str[:3],
        "entity": gl["Subsidiary"].map(sub2ent), "account": gl["Account"].str.split().str[0].astype(int),
        "account_name": gl["Account"].str.split(" : ").str[-1], "dept": gl["Department"].fillna(""),
        "location": gl["Location"].fillna(""), "name": gl["Name"].fillna("").str.strip(),
        "memo": gl["Memo"].fillna(""), "ref": gl["Ref No."].fillna(""),
        "ic_entity": gl["Intercompany Entity"].fillna("").map(lambda s: sub2ent.get(s, "")),
        "created": gl["Created Date"].map(_ts), "created_by": gl["Created By"],
    })
    net_cr = gl["Credit"].fillna(0) - gl["Debit"].fillna(0)
    g["amount"] = net_cr.where(g.account.isin(cr), -net_cr).round(2)      # natural sign, local ccy
    g["ccy"] = g.entity.map(ccy)
    g["usd"] = [round(a * (avg[p] if c == "CAD" else 1.0), 2) for a, p, c in zip(g.amount, g.period, g.ccy)]

    mp = pd.read_excel(D / "mapping" / "SPZ_to_LRG_CoA_Mapping_v3_DRAFT.xlsx", header=4)
    hx = pd.read_excel(D / "larkspur_hfm" / "LRG_HFM_Extract_SPZ_FY26Q3.xlsx", header=6)
    hfm = hx.melt(id_vars=["Entity", "Account", "Account Description", "ICP"], value_vars=PERIODS,
                  var_name="period", value_name="usd")
    hfm.columns = ["entity", "account", "description", "icp", "period", "usd"]
    jr = pd.read_csv(D / "larkspur_hfm" / "LRG_HFM_Journal_Register_FY26Q3.csv")
    log = pd.read_csv(D / "larkspur_hfm" / "LRG_HFM_Load_Log_FY26Q3.csv")
    log["extract_ts"] = log.Extract_Timestamp.map(_ts)
    hcoa = pd.read_csv(D / "larkspur_hfm" / "LRG_HFM_Chart_of_Accounts.csv")
    return dict(gl=g, coa=coa, mapping=mp, hfm=hfm, journals=jr, log=log, fx=fx, ents=ents, ccy=ccy,
                avg=avg, hcoa=hcoa)


def _r(x):
    return round(float(x), 2)


def _rows(df, n=None):
    df = df.head(n) if n else df
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].dt.strftime("%Y-%m-%d %H:%M").str.replace(" 00:00", "", regex=False)
    return out.to_dict(orient="records")


# ---------------------------------------------------------------- tools
def get_overview():
    d = data()
    return {
        "scenario": "Larkspur Restaurant Group (acquirer, Oracle HFM) acquired Sparrow Pizza (target, NetSuite). "
                    "Sparrow's FY26 Q3 (Jul-Sep 2026) P&L was mapped and loaded into HFM. Reconcile NetSuite to HFM.",
        "entities": _rows(d["ents"][["HFM_Entity", "Legal_Name", "Functional_Currency"]]),
        "conventions": [
            "NetSuite amounts here are natural sign (revenue and expense positive) in local currency.",
            "HFM is periodic USD, natural sign; R1200 discounts are naturally negative.",
            "HFM is loaded YTD from a NetSuite extract each month; entries created after a month's extract "
            "timestamp land in the following month's HFM periodic balance.",
            "P&L translates at the Treasury monthly AVERAGE rate.",
            "Intercompany royalty = 5% of company restaurant sales, billed by SPZ_FR (R9000 vs G9000 by ICP).",
        ],
        "fx_rates_usd_per_cad": _rows(d["fx"][["Period", "Average_Rate", "Closing_Rate"]]),
        "load_log": _rows(d["log"][["Period", "Load_Type", "Extract_Timestamp", "Mapping_Version",
                                    "Rows_Rejected", "Validation_Note"]]),
        "hfm_chart_of_accounts": _rows(d["hcoa"]),
        "gl_line_count": int(len(d["gl"])),
    }


def run_tieout(tolerance=1.0):
    """GL rolled through the mapping file and translated at average rates vs the HFM extract."""
    d = data()
    g, mp = d["gl"].copy(), d["mapping"]
    amap = dict(zip(mp["SPZ Account"], mp["LRG HFM Account"]))
    g["hfm_account"] = g.account.map(amap)
    unm = g[g.hfm_account.isna()].groupby(["entity", "period", "account", "account_name"]).agg(
        local_amount=("amount", "sum"), usd=("usd", "sum"), lines=("iid", "count")).reset_index()
    loc = g.dropna(subset=["hfm_account"]).groupby(["entity", "period", "hfm_account"]).agg(
        gl_local=("amount", "sum")).reset_index()
    loc["gl_usd"] = [_r(n * (d["avg"][p] if d["ccy"][e] == "CAD" else 1)) for e, p, n in
                     zip(loc.entity, loc.period, loc.gl_local)]
    act = d["hfm"].groupby(["entity", "period", "account"]).usd.sum().reset_index().rename(
        columns={"account": "hfm_account", "usd": "hfm_usd"})
    jr = d["journals"].groupby(["Entity", "Period", "Account"]).agg(
        journals_usd=("Amount_USD", "sum"), journal_ids=("JE_ID", lambda s: ", ".join(s))).reset_index()
    jr.columns = ["entity", "period", "hfm_account", "journals_usd", "journal_ids"]
    t = loc.merge(act, on=["entity", "period", "hfm_account"], how="outer").merge(
        jr, on=["entity", "period", "hfm_account"], how="left")
    t = t.fillna({"gl_local": 0, "gl_usd": 0, "hfm_usd": 0, "journals_usd": 0, "journal_ids": ""})
    t["diff_usd"] = (t.hfm_usd - t.gl_usd).round(2)
    t["diff_excl_journals"] = (t.diff_usd - t.journals_usd).round(2)
    t["implied_fx_rate"] = [round((h - j) / l, 5) if d["ccy"][e] == "CAD" and l else None
                            for e, h, j, l in zip(t.entity, t.hfm_usd, t.journals_usd, t.gl_local)]
    br = t[t.diff_usd.abs() > tolerance].sort_values(["entity", "hfm_account", "period"])
    cols = ["entity", "period", "hfm_account", "gl_usd", "hfm_usd", "diff_usd", "journals_usd", "journal_ids",
            "diff_excl_journals", "implied_fx_rate"]
    return {"breaks_over_tolerance": int(len(br)), "tolerance_usd": tolerance,
            "breaks": _rows(br[cols].round(2)),
            "gl_accounts_missing_from_mapping": _rows(unm.round(2)),
            "note": "diff_usd = HFM - GL (natural sign). implied_fx_rate shown for CAD entity only."}


def get_mapping():
    """Mapping v3 DRAFT plus Q3 HFM balances by entity, so you can judge whether each account belongs."""
    d = data()
    mp = d["mapping"].fillna("")
    bal = d["hfm"].groupby(["account", "entity"]).usd.sum().unstack(fill_value=0).round(0)
    bal = bal.reset_index().rename(columns={"account": "hfm_account"})
    return {"mapping_rows": _rows(mp), "hfm_q3_usd_by_entity": _rows(bal),
            "note": "SPZ_US and SPZ_CA operate company restaurants only; SPZ_FR is the franchisor."}


def get_hfm_journals():
    return {"journals": _rows(data()["journals"])}


def query_gl(entity=None, period=None, accounts=None, name_contains=None, memo_contains=None, ref_contains=None,
             min_abs_amount=None, created_after_extract=None, group_by=None, limit=25):
    """Filter NetSuite GL lines; optionally aggregate."""
    d = data()
    g = d["gl"]
    m = pd.Series(True, index=g.index)
    if entity:
        m &= g.entity == entity
    if period:
        m &= g.period == period
    if accounts:
        m &= g.account.isin([int(a) for a in accounts])
    for col, val in [("name", name_contains), ("memo", memo_contains), ("ref", ref_contains)]:
        if val:
            m &= g[col].str.contains(val, case=False, regex=False)
    if min_abs_amount:
        m &= g.amount.abs() >= float(min_abs_amount)
    if created_after_extract is not None:
        ext = dict(zip(d["log"].Period, d["log"].extract_ts))
        late = g.created > g.period.map(ext)
        m &= late if created_after_extract else ~late
    sub = g[m]
    limit = max(1, min(int(limit or 25), 60))
    if group_by:
        gb = [c for c in group_by if c in ("entity", "period", "account", "account_name", "name", "location",
                                           "type", "created_by", "dept")]
        agg = sub.groupby(gb).agg(amount_local=("amount", "sum"), usd=("usd", "sum"), lines=("iid", "count"))
        agg = agg.reset_index().round(2).sort_values("usd", key=abs, ascending=False)
        return {"matching_lines": int(len(sub)), "groups": _rows(agg, limit)}
    cols = ["iid", "doc", "type", "date", "period", "entity", "account", "account_name", "name", "memo", "ref",
            "amount", "ccy", "usd", "location", "created", "created_by"]
    sub = sub.reindex(sub.amount.abs().sort_values(ascending=False).index)
    return {"matching_lines": int(len(sub)), "total_usd": _r(sub.usd.sum()), "rows": _rows(sub[cols], limit)}


def scan_duplicate_bills(window_days=30):
    """Vendor bills with the same entity, vendor, account and amount within N days."""
    g = data()["gl"]
    b = g[g.type == "Bill"].copy()
    b["norm_ref"] = b.ref.str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
    out = []
    for _, grp in b.groupby(["entity", "name", "account", "amount"]):
        if len(grp) < 2:
            continue
        grp = grp.sort_values("date")
        for i in range(len(grp) - 1):
            a, c = grp.iloc[i], grp.iloc[i + 1]
            if (c.date - a.date).days <= window_days:
                out.append(dict(entity=a.entity, vendor=a["name"], account=int(a.account), amount=_r(a.amount),
                                ccy=a.ccy, first_iid=int(a.iid), first_ref=a.ref, first_created=str(a.created),
                                second_iid=int(c.iid), second_ref=c.ref, second_created=str(c.created),
                                second_created_by=c.created_by, period=c.period,
                                ref_similarity="identical" if a.ref == c.ref else
                                ("same after normalizing" if a.norm_ref == c.norm_ref else
                                 ("one ref extends the other" if a.norm_ref.startswith(c.norm_ref) or
                                  c.norm_ref.startswith(a.norm_ref) else "different"))))
    return {"candidate_pairs": out}


def scan_accrual_reversals():
    """Pair month-end 'ACCR' journals with next-month 'REV' journals (same entity, account, location, amount)."""
    g = data()["gl"]
    acc = g[g.memo.str.upper().str.startswith("ACCR")]
    rev = g[g.memo.str.upper().str.startswith("REV")]
    unmatched_acc, used = [], set()
    for _, a in acc.iterrows():
        if a.period not in NEXT:
            continue
        cand = rev[(rev.entity == a.entity) & (rev.account == a.account) & (rev.location == a.location) &
                   (rev.period == NEXT[a.period]) & ((rev.amount + a.amount).abs() < 0.01) & (~rev.iid.isin(used))]
        if len(cand):
            used.add(cand.iloc[0].iid)
        else:
            unmatched_acc.append(a)
    cols = ["iid", "date", "period", "entity", "account", "account_name", "location", "memo", "amount", "ccy", "usd"]
    orphan_rev = rev[~rev.iid.isin(used)]
    return {"accruals_without_reversal": _rows(pd.DataFrame(unmatched_acc)[cols]) if unmatched_acc else [],
            "reversals_without_in_quarter_accrual": _rows(orphan_rev[cols]),
            "note": "Sep accruals reverse in Oct (out of scope). Jul 1 reversals relate to June accruals (out of scope)."}


def scan_large_items(multiple=5.0, min_usd=100000):
    """Lines far above the typical line size for their entity/account."""
    g = data()["gl"]
    med = g.groupby(["entity", "account"]).usd.transform(lambda s: s.abs().median())
    routine = g.memo.str.upper().str.match(r"^(ACCR|REV)\b")   # accruals are covered by scan_accrual_reversals
    m = (g.usd.abs() >= min_usd) & (g.usd.abs() >= multiple * med) & ~routine
    cols = ["iid", "type", "date", "period", "entity", "account", "account_name", "name", "memo", "amount", "ccy",
            "usd", "created", "created_by"]
    sub = g[m].copy()
    sub["typical_line_usd"] = med[m].round(0)
    return {"items": _rows(sub.sort_values("usd", key=abs, ascending=False)[cols + ["typical_line_usd"]])}


def intercompany_matching():
    """Royalty income at SPZ_FR (R9000 by ICP partner) vs royalty expense at the partner (G9000), USD."""
    d = data()
    h = d["hfm"]
    inc = h[h.account == "R9000"].groupby(["icp", "period"]).usd.sum()
    exp = h[h.account == "G9000"].groupby(["entity", "period"]).usd.sum()
    g = d["gl"]
    sales = g[g.account.isin([40100, 40110, 40120, 40400, 40410])].groupby(["entity", "period"]).usd.sum()
    out = []
    for e in ["SPZ_US", "SPZ_CA"]:
        for p in PERIODS:
            i, x = _r(inc.get((e, p), 0)), _r(exp.get((e, p), 0))
            out.append(dict(partner=e, period=p, fr_income_usd=i, partner_expense_usd=x, difference=_r(i - x),
                            company_sales_usd=_r(sales.get((e, p), 0)),
                            implied_rate_income=round(i / sales[(e, p)], 4) if sales.get((e, p)) else None,
                            implied_rate_expense=round(x / sales[(e, p)], 4) if sales.get((e, p)) else None))
    return {"ic_pairs": out, "note": "Royalty policy: 5% of company restaurant sales."}


def submit_findings(findings, summary=""):
    return {"received": len(findings)}


REGISTRY = {f.__name__: f for f in [get_overview, run_tieout, get_mapping, get_hfm_journals, query_gl,
                                    scan_duplicate_bills, scan_accrual_reversals, scan_large_items,
                                    intercompany_matching, submit_findings]}

_ENT = {"type": "string", "enum": ["SPZ_US", "SPZ_CA", "SPZ_FR"]}
_PER = {"type": "string", "enum": PERIODS}
TOOL_SPECS = [
    {"name": "get_overview", "description": "Scenario, entities, conventions, FX rates, HFM load log and HFM chart of accounts. Call first.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "run_tieout", "description": "Standard tie-out: NetSuite GL rolled up through the mapping file (CAD at average rate) vs the HFM extract, by entity/period/HFM account. Shows HFM journals on each cell, the break excluding journals, implied FX rate for CAD, and GL accounts missing from the mapping.",
     "input_schema": {"type": "object", "properties": {"tolerance": {"type": "number", "default": 1.0}}}},
    {"name": "get_mapping", "description": "The CoA mapping file (v3 DRAFT) with status/reviewer/comments, plus Q3 HFM balances by entity for every HFM account. Use to judge whether each source account is mapped to the right place; a tie-out cannot see mapping errors.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "get_hfm_journals", "description": "HFM top-side journal register (preparer, approver, support).",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "query_gl", "description": "Filter NetSuite GL lines (natural-sign local amounts plus USD at average rate), sorted by size, or aggregate with group_by. created_after_extract=true returns lines created after that period's HFM extract timestamp.",
     "input_schema": {"type": "object", "properties": {
         "entity": _ENT, "period": _PER, "accounts": {"type": "array", "items": {"type": "integer"}},
         "name_contains": {"type": "string"}, "memo_contains": {"type": "string"}, "ref_contains": {"type": "string"},
         "min_abs_amount": {"type": "number"}, "created_after_extract": {"type": "boolean"},
         "group_by": {"type": "array", "items": {"type": "string", "enum": ["entity", "period", "account", "account_name", "name", "location", "type", "created_by", "dept"]}},
         "limit": {"type": "integer", "default": 25}}}},
    {"name": "scan_duplicate_bills", "description": "Candidate duplicate vendor bills: same entity, vendor, account and amount within a window. Judge each pair.",
     "input_schema": {"type": "object", "properties": {"window_days": {"type": "integer", "default": 30}}}},
    {"name": "scan_accrual_reversals", "description": "Month-end accruals (memo 'ACCR') with no matching reversal ('REV') the next month, and orphan reversals.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "scan_large_items", "description": "GL lines unusually large for their entity/account (>= multiple x median line and >= min_usd). Judge each: capex, accrual, true-up, legitimate one-off.",
     "input_schema": {"type": "object", "properties": {"multiple": {"type": "number", "default": 5}, "min_usd": {"type": "number", "default": 100000}}}},
    {"name": "intercompany_matching", "description": "HFM intercompany royalty income at SPZ_FR by partner vs the partner's royalty expense, with implied royalty rates on company sales.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "submit_findings", "description": "Submit the final list of findings. Call once, at the end.",
     "input_schema": {"type": "object", "required": ["findings", "summary"], "properties": {
         "summary": {"type": "string", "description": "3-5 sentence executive summary for the controller."},
         "findings": {"type": "array", "items": {"type": "object",
             "required": ["issue_type", "entity", "period", "amount_usd", "evidence", "root_cause", "proposed_fix"],
             "properties": {
                 "issue_type": {"type": "string", "enum": ISSUE_TYPES},
                 "entity": {"type": "string", "description": "SPZ_US, SPZ_CA, SPZ_FR, or * if the root cause spans entities"},
                 "period": {"type": "string", "description": "Jul, Aug, Sep, or * if it spans periods. For cutoff use the period the entry belongs to."},
                 "hfm_account": {"type": "string", "description": "Affected HFM account (for mapping errors: the wrong account it landed in)"},
                 "source_account": {"type": "string", "description": "NetSuite account number. Required for issues that live in NetSuite."},
                 "amount_usd": {"type": "number", "description": "Size of the misstatement in USD (positive)."},
                 "evidence": {"type": "string", "description": "Specific IDs, amounts, timestamps."},
                 "root_cause": {"type": "string"},
                 "proposed_fix": {"type": "string"},
                 "correcting_entry": {"type": "string", "description": "e.g. 'HFM SPZ_US Aug: Dr C1000 486,215.40 / Cr ... '"}}}}}}},
]


def call(name, args):
    try:
        res = REGISTRY[name](**(args or {}))
    except Exception as e:  # surface errors to the model instead of crashing the run
        res = {"error": f"{type(e).__name__}: {e}"}
    txt = json.dumps(res, default=str)
    return txt if len(txt) <= 24000 else txt[:24000] + ' ... [truncated - narrow your query]'
