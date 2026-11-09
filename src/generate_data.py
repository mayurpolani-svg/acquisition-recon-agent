#!/usr/bin/env python3
"""
Generate the Sparrow Pizza -> Larkspur Restaurant Group post-acquisition
reconciliation benchmark.

  *** ALL DATA IS SYNTHETIC ***
  Every company, person, vendor, store and figure is fictional. Any resemblance
  to real entities is coincidental. Built for portfolio / benchmarking purposes.

Scenario
  Larkspur Restaurant Group (acquirer, Oracle HFM consolidation) closed on
  Sparrow Pizza Co. (target, NetSuite GL). Sparrow's Q3 FY2026 trial balance
  was mapped and loaded into Larkspur HFM. The two systems should tie. They
  don't. 33 issues are seeded across 10 issue types; the answer key lists each
  one with its root cause, dollar impact and the correcting entry.

Run:  python src/generate_data.py      (deterministic: same seed, same files)
"""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

SEED = 2026
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
DATA, KEY = ROOT / "data", ROOT / "answer_key"
NOTICE = ("SYNTHETIC DATA — fictional companies, people and figures. "
          "Built for a portfolio reconciliation benchmark. Not real financial information.")

PERIODS = ["Jul", "Aug", "Sep"]
PER = {7: "Jul", 8: "Aug", 9: "Sep"}
NEXT = {"Jul": "Aug", "Aug": "Sep"}
Q_START, Q_END = date(2026, 7, 1), date(2026, 9, 30)
LOAD_TS = {"Jul": datetime(2026, 8, 4, 18, 12), "Aug": datetime(2026, 9, 3, 17, 48),
           "Sep": datetime(2026, 10, 5, 19, 2)}
# Larkspur Treasury official rates, USD per 1 CAD
FX = {"Jul": {"avg": 0.7312, "close": 0.7288},
      "Aug": {"avg": 0.7265, "close": 0.7178},
      "Sep": {"avg": 0.7234, "close": 0.7259}}

ENT = {
    "SPZ_US": dict(legal="Sparrow Pizza USA, Inc.", ccy="USD"),
    "SPZ_CA": dict(legal="Sparrow Pizza Canada Ltd.", ccy="CAD"),
    "SPZ_FR": dict(legal="Sparrow Franchising LLC", ccy="USD"),
}
NS_SUB = {k: f"Sparrow Pizza Holdings : {v['legal']}" for k, v in ENT.items()}

# --------------------------------------------------------------------------
# Charts of accounts
# --------------------------------------------------------------------------
HFM_COA = [
    ("R1000", "Company Restaurant Sales", "Revenue"),
    ("R1100", "Delivery & Service Fee Revenue", "Revenue"),
    ("R1200", "Sales Discounts & Promotions", "Revenue (contra)"),
    ("R2000", "Franchise Royalty Revenue", "Revenue"),
    ("R2100", "Franchise Advertising Fund Revenue", "Revenue"),
    ("R2200", "Initial & Renewal Franchise Fees", "Revenue"),
    ("R9000", "Intercompany Royalty Revenue", "Revenue"),
    ("C1000", "Food & Paper Cost", "Expense"),
    ("C1100", "Third-Party Delivery Commissions", "Expense"),
    ("C2000", "Restaurant Labor", "Expense"),
    ("C2100", "Payroll Taxes & Benefits", "Expense"),
    ("C3000", "Occupancy", "Expense"),
    ("C3100", "Other Restaurant Operating Costs", "Expense"),
    ("C4000", "Advertising", "Expense"),
    ("C5000", "Payment Processing & Technology", "Expense"),
    ("G1000", "General & Administrative", "Expense"),
    ("G1100", "Professional Fees", "Expense"),
    ("G9000", "Intercompany Royalty Expense", "Expense"),
    ("D1000", "Depreciation & Amortization", "Expense"),
    ("I1000", "Interest Expense", "Expense"),
    ("X1000", "Transaction & Integration Costs", "Expense"),
    ("T1000", "Income Tax Expense", "Expense"),
]
HFM_DESC = {a: d for a, d, _ in HFM_COA}

COA = {}  # acct -> name, parent, nat, correct HFM target


def A(num, parent, name, nat, hfm):
    COA[num] = dict(parent=parent, name=name, nat=nat, hfm=hfm)


A(40100, "Revenue", "Company Sales - Carryout", "CR", "R1000")
A(40110, "Revenue", "Company Sales - Delivery", "CR", "R1000")
A(40120, "Revenue", "Company Sales - Dine-In", "CR", "R1000")
A(40200, "Revenue", "Delivery Fee Income", "CR", "R1100")
A(40300, "Revenue", "Discounts & Promotions", "CR", "R1200")
A(40400, "Revenue", "Third-Party Marketplace Sales", "CR", "R1000")
A(40410, "Revenue", "Catering Sales", "CR", "R1000")
A(41100, "Franchise Revenue", "Franchise Royalty Income", "CR", "R2000")
A(41200, "Franchise Revenue", "Franchise Advertising Contributions", "CR", "R2100")
A(41300, "Franchise Revenue", "Initial & Renewal Franchise Fees", "CR", "R2200")
A(42100, "Intercompany", "Intercompany Royalty Income", "CR", "R9000")
A(50100, "Cost of Sales", "Food Cost - Cheese", "DR", "C1000")
A(50110, "Cost of Sales", "Food Cost - Dough & Flour", "DR", "C1000")
A(50120, "Cost of Sales", "Food Cost - Proteins", "DR", "C1000")
A(50130, "Cost of Sales", "Food Cost - Produce & Other", "DR", "C1000")
A(50200, "Cost of Sales", "Packaging", "DR", "C1000")
A(50300, "Cost of Sales", "Marketplace Commissions", "DR", "C1100")
A(51100, "Labor", "Restaurant Hourly Wages", "DR", "C2000")
A(51110, "Labor", "Restaurant Management Salaries", "DR", "C2000")
A(51200, "Labor", "Payroll Taxes", "DR", "C2100")
A(51300, "Labor", "Employee Benefits", "DR", "C2100")
A(51400, "Labor", "Delivery Driver Reimbursement", "DR", "C2000")
A(52100, "Occupancy", "Rent - Restaurants", "DR", "C3000")
A(52200, "Occupancy", "Utilities", "DR", "C3000")
A(52300, "Restaurant Operating", "Repairs & Maintenance", "DR", "C3100")
A(52400, "Restaurant Operating", "Restaurant Supplies", "DR", "C3100")
A(53100, "Marketing", "Local Store Marketing", "DR", "C4000")
A(53200, "Marketing", "National Advertising Fund Contribution", "DR", "C4000")
A(54100, "Restaurant Operating", "Credit Card Processing Fees", "DR", "C5000")
A(54200, "Restaurant Operating", "Technology & POS Fees", "DR", "C5000")
A(60100, "G&A", "G&A Salaries", "DR", "G1000")
A(60200, "G&A", "Professional Fees", "DR", "G1100")
A(60300, "G&A", "Travel & Entertainment", "DR", "G1000")
A(60400, "G&A", "Corporate Rent", "DR", "G1000")
A(60500, "G&A", "Insurance", "DR", "G1000")
A(61100, "Intercompany", "Intercompany Royalty Expense", "DR", "G9000")
A(62100, "D&A", "Depreciation", "DR", "D1000")
A(62200, "D&A", "Amortization", "DR", "D1000")
A(63100, "Other Expense", "Interest Expense", "DR", "I1000")
A(64100, "Other Expense", "Transaction Costs - M&A", "DR", "X1000")
A(70100, "Tax", "Income Tax Expense", "DR", "T1000")

CORRECT_MAP = {a: v["hfm"] for a, v in COA.items()}
# Mapping v3 DRAFT as actually used for the HFM load (seeded errors)
LOADED_MAP = dict(CORRECT_MAP)
LOADED_MAP[40200] = "R2000"   # SI-01 delivery fees -> franchise royalties
LOADED_MAP[53200] = "G1000"   # SI-02 national ad fund -> G&A
LOADED_MAP[51400] = "C3100"   # SI-03 driver reimbursement -> other operating
del LOADED_MAP[64100]         # SI-04 unmapped
del LOADED_MAP[40410]         # SI-05 unmapped


def acct_label(a):
    return f"{a} {COA[a]['parent']} : {COA[a]['name']}"


# --------------------------------------------------------------------------
# Posting engine (NetSuite-style GL detail)
# --------------------------------------------------------------------------
ROWS = []
SEQ = {"id": 4_810_000, "JE": 1200, "BILL": 58_000, "INV": 21_400, "ER": 9_100}
AP_US = ["j.chen", "t.nguyen", "k.brooks", "m.reyes"]
AP_CA = ["e.tremblay", "l.gagnon"]
GL_USERS = ["s.whitaker", "d.alvarez", "r.kim"]


def nid():
    SEQ["id"] += int(rng.integers(1, 9))
    return SEQ["id"]


def doc(kind):
    SEQ[kind] += int(rng.integers(1, 4))
    return {"JE": f"JE{SEQ['JE']:05d}", "BILL": f"BILL-{SEQ['BILL']:06d}",
            "INV": f"INV-{SEQ['INV']:06d}", "ER": f"ER-{SEQ['ER']:05d}"}[kind]


def fmt_date(d):
    return f"{d.month}/{d.day}/{d.year}"


def fmt_ts(t):
    h = t.hour % 12 or 12
    return f"{t.month}/{t.day}/{t.year} {h}:{t.minute:02d} {'am' if t.hour < 12 else 'pm'}"


def default_created(d, per):
    t = datetime(d.year, d.month, d.day, int(rng.integers(7, 19)), int(rng.integers(0, 60)))
    t += timedelta(days=int(rng.choice([0, 0, 1, 1, 2])))
    return min(t, LOAD_TS[per] - timedelta(hours=2))


def post(ent, d, acct, amt, *, typ="Journal", docno=None, name="", memo="", ref="",
         dept="", loc="", created=None, by=None, ic="", late=False, tag=""):
    amt = round(float(amt), 2)
    if abs(amt) < 0.005:
        return None
    d = min(d, Q_END)
    is_dr = (COA[acct]["nat"] == "DR") == (amt > 0)
    per = PER[d.month]
    created = created or default_created(d, per)
    if by is None:
        pool = AP_CA if ent == "SPZ_CA" else AP_US
        by = rng.choice(pool) if typ == "Bill" else rng.choice(GL_USERS)
    rid = nid()
    ROWS.append({
        "Internal ID": rid, "Document Number": docno or doc("JE"), "Type": typ,
        "Date": d, "Period": f"{per} 2026", "Subsidiary": NS_SUB[ent],
        "Account": acct_label(acct), "Department": dept, "Location": loc,
        "Name": name, "Memo": memo, "Ref No.": ref,
        "Debit": abs(amt) if is_dr else None, "Credit": None if is_dr else abs(amt),
        "Currency": ENT[ent]["ccy"],
        "Intercompany Entity": NS_SUB[ic] if ic else "",
        "Created Date": created, "Created By": by,
        # internal (dropped on export)
        "_ent": ent, "_per": per, "_acct": acct, "_nat": amt, "_ic": ic,
        "_late": late, "_tag": tag,
    })
    return rid


def days():
    d = Q_START
    while d <= Q_END:
        yield d
        d += timedelta(days=1)


def month_days(per):
    m = {"Jul": 7, "Aug": 8, "Sep": 9}[per]
    return [d for d in days() if d.month == m]


def ln(mu=1.0, s=0.06):
    return float(mu * rng.lognormal(0, s))


# --------------------------------------------------------------------------
# Operating footprint
# --------------------------------------------------------------------------
REGIONS = {
    "SPZ_US": {"Texas North": 78, "Texas South": 64, "Oklahoma": 52,
               "Arkansas": 34, "Louisiana": 48, "Kansas": 36},
    "SPZ_CA": {"Ontario West": 34, "Ontario East": 30},
}
DAILY_AUV = {"SPZ_US": 3250.0, "SPZ_CA": 3350.0}
DOW = [0.85, 0.88, 0.92, 0.98, 1.22, 1.20, 0.95]
SEASON = {"Jul": 1.02, "Aug": 0.99, "Sep": 0.97}
MIX = {"SPZ_US": {40100: .44, 40110: .30, 40120: .12, 40400: .14},
       "SPZ_CA": {40100: .40, 40110: .32, 40120: .14, 40400: .14}}
COMPANY_SALES = [40100, 40110, 40120, 40400, 40410]

stores = {}
_us_nums = rng.choice(np.arange(2001, 2999), 312, replace=False)
_ca_nums = rng.choice(np.arange(7001, 7199), 64, replace=False)
i = 0
for r, n in REGIONS["SPZ_US"].items():
    stores[r] = sorted(int(x) for x in _us_nums[i:i + n]); i += n
i = 0
for r, n in REGIONS["SPZ_CA"].items():
    stores[r] = sorted(int(x) for x in _ca_nums[i:i + n]); i += n

LANDLORDS = [f"{a} {b} {c}" for a in ["Brazos", "Cimarron", "Trinity", "Red River", "Pecan",
                                       "Bluestem", "Prairie", "Cypress", "Ozark", "Sabine"]
             for b in ["Retail", "Commons", "Crossing"] for c in ["Partners LP", "Holdings LLC"]]
CA_LANDLORDS = [f"{a} {b} Inc." for a in ["Lakeshore", "Bayview", "Grand River", "Maple Ridge",
                                          "Huron", "Escarpment"] for b in ["Properties", "Realty"]]
landlord = {s: (rng.choice(CA_LANDLORDS) if r.startswith("Ontario") else rng.choice(LANDLORDS))
            for r in stores for s in stores[r]}
rent = {s: round(ln(8400 if r.startswith("Ontario") else 7800, 0.18), 2)
        for r in stores for s in stores[r]}

daily_sales = {}       # (ent, region, date) -> company sales (local ccy)
month_sales = {}       # (ent, per) -> company sales
month_delivery = {}    # (ent, per) -> delivery channel sales
month_aggr = {}        # (ent, per) -> marketplace sales

# --------------------------------------------------------------------------
# 1. Revenue: POS daily sales summaries
# --------------------------------------------------------------------------
for ent, regs in REGIONS.items():
    for d in days():
        per = PER[d.month]
        for reg, n in regs.items():
            base = n * DAILY_AUV[ent] * DOW[d.weekday()] * SEASON[per] * ln(1, 0.05)
            if d == date(2026, 7, 4) and ent == "SPZ_US":
                base *= 1.18
            if d == date(2026, 7, 1) and ent == "SPZ_CA":
                base *= 1.12
            dn = f"POS-{d:%Y%m%d}-{reg.split()[0][:3].upper()}{reg.split()[-1][0]}"
            cts = datetime(d.year, d.month, d.day, 3, 15) + timedelta(days=1)
            memo = f"POS daily sales summary - {reg}"
            tot = 0.0
            for acct, share in MIX[ent].items():
                amt = base * share * ln(1, 0.03)
                post(ent, d, acct, amt, docno=dn, memo=memo, loc=reg, dept="Restaurant Operations",
                     created=cts, by="integration.pos")
                tot += amt
                if acct == 40110:
                    month_delivery[(ent, per)] = month_delivery.get((ent, per), 0) + amt
                    post(ent, d, 40200, amt * 0.085 * ln(1, 0.04), docno=dn, memo=memo, loc=reg,
                         dept="Restaurant Operations", created=cts, by="integration.pos")
                if acct == 40400:
                    month_aggr[(ent, per)] = month_aggr.get((ent, per), 0) + amt
            if ent == "SPZ_US" and d >= date(2026, 8, 3) and d.weekday() < 5:
                cat = base * 0.012 * ln(1, 0.25)
                post(ent, d, 40410, cat, docno=dn, memo=memo, loc=reg,
                     dept="Restaurant Operations", created=cts, by="integration.pos")
                tot += cat
            post(ent, d, 40300, -tot * 0.065 * ln(1, 0.05), docno=dn, memo=memo, loc=reg,
                 dept="Restaurant Operations", created=cts, by="integration.pos")
            daily_sales[(ent, reg, d)] = tot
            month_sales[(ent, per)] = month_sales.get((ent, per), 0) + tot


def week_sales(ent, reg, monday):
    vals = [daily_sales.get((ent, reg, monday - timedelta(days=k))) for k in range(1, 8)]
    vals = [v for v in vals if v is not None]
    return sum(vals) * 7 / len(vals) if vals else 0


mondays = [d for d in days() if d.weekday() == 0]

# --------------------------------------------------------------------------
# 2. Food & paper, marketplace commissions, supplies (weekly vendor bills)
# --------------------------------------------------------------------------
FOOD_US = {50100: ("Valley Dairy Cheese Co.", "VDC", .082), 50110: ("Heartland Mills Flour", "HMF", .045),
           50120: ("Lone Star Proteins", "LSP", .070), 50130: ("Gulf Coast Produce", "GCP", .038),
           50200: ("Redline Packaging Supply", "RPS", .025)}
FOOD_CA = {50100: ("Northern Dairy Co-op", "NDC", .085), 50110: ("Maple Leaf Foodservice", "MLF", .046),
           50120: ("Maple Leaf Foodservice", "MLF", .071), 50130: ("Maple Leaf Foodservice", "MLF", .039),
           50200: ("Redline Packaging Supply", "RPS", .026)}
for ent, regs in REGIONS.items():
    food = FOOD_US if ent == "SPZ_US" else FOOD_CA
    for mon in mondays:
        for reg in regs:
            ws = week_sales(ent, reg, mon)
            for acct, (vend, pfx, pct) in food.items():
                bd = mon + timedelta(days=int(rng.integers(0, 3)))
                post(ent, bd, acct, ws * pct * ln(1, 0.04), typ="Bill", docno=doc("BILL"), name=vend,
                     ref=f"{pfx}-{int(rng.integers(100000, 999999))}", loc=reg, dept="Supply Chain",
                     memo=f"Weekly delivery - w/e {(mon - timedelta(days=1)):%m/%d} - {reg}")
            post(ent, mon + timedelta(days=1), 52400, ws * 0.011 * ln(1, 0.08), typ="Bill",
                 docno=doc("BILL"), name="Redline Restaurant Supply", ref=f"RRS{int(rng.integers(10000, 99999))}",
                 loc=reg, dept="Restaurant Operations", memo=f"Smallwares & cleaning supplies - {reg}")
        wk_aggr = sum(week_sales(ent, r, mon) for r in regs) * MIX[ent][40400]
        for plat, share, pfx in [("DashCart Inc.", .6, "DC"), ("GoBite Technologies", .4, "GB")]:
            post(ent, mon + timedelta(days=2), 50300, wk_aggr * share * 0.22 * ln(1, 0.03), typ="Bill",
                 docno=doc("BILL"), name=plat, ref=f"{pfx}-STMT-{mon:%y%m%d}",
                 dept="Restaurant Operations", memo=f"Marketplace commission statement w/e {(mon - timedelta(days=1)):%m/%d}")

# --------------------------------------------------------------------------
# 3. Labor (semi-monthly payroll by region)
# --------------------------------------------------------------------------
for ent, regs in REGIONS.items():
    for per in PERIODS:
        md = month_days(per)
        for pay in (md[14], md[-1]):
            for reg in regs:
                half = sum(daily_sales[(ent, reg, d)] for d in md) / 2
                dn = doc("JE")
                hourly = half * 0.210 * ln(1, 0.03)
                mgmt = half * 0.050 * ln(1, 0.02)
                kw = dict(docno=dn, name="PayCore Payroll Services", loc=reg, dept="Restaurant Operations",
                          memo=f"Payroll {pay:%m/%d} - {reg}", by="integration.payroll",
                          created=min(datetime(pay.year, pay.month, pay.day, 21, 5),
                                      LOAD_TS[per] - timedelta(hours=3)))
                post(ent, pay, 51100, hourly, **kw)
                post(ent, pay, 51110, mgmt, **kw)
                post(ent, pay, 51200, (hourly + mgmt) * 0.078 * ln(1, 0.02), **kw)
                post(ent, pay, 51300, (hourly + mgmt) * 0.042 * ln(1, 0.03), **kw)
                dshare = month_delivery[(ent, per)] / 2 * regs[reg] / sum(regs.values())
                post(ent, pay, 51400, dshare * 0.031 * ln(1, 0.04), **kw)

# --------------------------------------------------------------------------
# 4. Occupancy: rent per store, utilities with accrual / reversal cycle
# --------------------------------------------------------------------------
util_accr_ids = {}
for ent, regs in REGIONS.items():
    vend_util = "Lakeshore Hydro" if ent == "SPZ_CA" else "TriCounty Power & Light"
    unit = 2300 if ent == "SPZ_CA" else 2100
    for per in PERIODS:
        md = month_days(per)
        for reg in regs:
            for s in stores[reg]:
                post(ent, md[0], 52100, rent[s], typ="Bill", docno=doc("BILL"), name=landlord[s],
                     ref=f"RENT-{s}-{md[0]:%y%m}", loc=reg, dept="Restaurant Operations",
                     memo=f"Base rent - Store #{s} - {per} 2026")
                post(ent, md[14] + timedelta(days=int(rng.integers(-3, 4))), 52200, unit * ln(1, 0.15),
                     typ="Bill", docno=doc("BILL"), name=vend_util, ref=f"UT{s}{md[0]:%m}",
                     loc=reg, dept="Restaurant Operations", memo=f"Utilities - Store #{s} - prior month service")
            est = len(stores[reg]) * unit * ln(1, 0.03)
            # reversal of prior-month accrual (June accrual for July)
            prev_est = util_accr_ids.get((ent, reg, "prev"), len(stores[reg]) * unit)
            post(ent, md[0], 52200, -prev_est, docno=doc("JE"), loc=reg, dept="Finance",
                 memo=f"REV - ACCR utilities unbilled - {reg}", by="auto.reversal",
                 created=datetime(md[0].year, md[0].month, md[0].day, 6, 0), tag=f"REV-UTIL-{ent}-{reg}-{per}")
            rid = post(ent, md[-1], 52200, est, docno=doc("JE"), loc=reg, dept="Finance",
                       memo=f"ACCR - {per} utilities unbilled - {reg}", tag=f"ACCR-UTIL-{ent}-{reg}-{per}")
            util_accr_ids[(ent, reg, "prev")] = est

# --------------------------------------------------------------------------
# 5. Repairs, marketing, payments & tech
# --------------------------------------------------------------------------
RM_US = ["Keystone Kitchen Service", "Apex Refrigeration", "Precision HVAC Group", "Ironclad Plumbing",
         "Brightline Electrical", "Summit Floor Care"]
RM_CA = ["Northshore Mechanical", "Great Lakes Refrigeration", "Kingsway Plumbing"]
for ent, regs in REGIONS.items():
    for mon in mondays:
        for reg, n in regs.items():
            for _ in range(int(rng.poisson(n / 12))):
                post(ent, mon + timedelta(days=int(rng.integers(0, 5))), 52300, ln(1350, 0.6), typ="Bill",
                     docno=doc("BILL"), name=rng.choice(RM_CA if ent == "SPZ_CA" else RM_US),
                     ref=f"WO-{int(rng.integers(100000, 999999))}", loc=reg, dept="Facilities",
                     memo=f"Service call - Store #{rng.choice(stores[reg])}")
    for per in PERIODS:
        md = month_days(per)
        ms = month_sales[(ent, per)]
        for _ in range(12):
            post(ent, md[int(rng.integers(0, len(md)))], 53100, ms * 0.012 / 12 * ln(1, 0.4), typ="Bill",
                 docno=doc("BILL"), name=rng.choice(["Bluebonnet Print & Media", "Signal Social Agency",
                                                     "Crossroads Outdoor"]),
                 ref=f"MK{int(rng.integers(10000, 99999))}", dept="Marketing", memo="Local store marketing")
        post(ent, md[-1], 53200, ms * 0.04, docno=doc("JE"), name="Sparrow National Advertising Fund",
             dept="Marketing", memo=f"National ad fund contribution 4% - {per} 2026")
        post(ent, md[2], 54200, sum(len(stores[r]) for r in regs) * 189, typ="Bill", docno=doc("BILL"),
             name="OrderLoop POS", ref=f"OL-{ent[-2:]}-{md[0]:%y%m}", dept="IT",
             memo=f"POS subscription - {per} 2026")

# Card processing: statement for prior month on ~5th, accrual at month-end, reversal on 1st
cc_prev = {}
for ent in REGIONS:
    for per in PERIODS:
        md = month_days(per)
        cur = (month_sales[(ent, per)] - month_aggr[(ent, per)]) * 0.0235
        prev = cc_prev.get(ent, cur * 1.01)
        post(ent, md[0], 54100, -prev * 0.98, docno=doc("JE"), dept="Finance", by="auto.reversal",
             memo="REV - ACCR card processing fees", created=datetime(md[0].year, md[0].month, 1, 6, 0),
             tag=f"REV-CC-{ent}-{per}")
        post(ent, md[4], 54100, prev, typ="Bill", docno=doc("BILL"), name="Frontier Merchant Services",
             ref=f"FMS-{ent[-2:]}-{md[0]:%y%m}", dept="Finance", memo="Card processing statement - prior month")
        post(ent, md[-1], 54100, cur * 0.98, docno=doc("JE"), dept="Finance",
             memo=f"ACCR - {per} card processing fees", tag=f"ACCR-CC-{ent}-{per}")
        cc_prev[ent] = cur

# --------------------------------------------------------------------------
# 6. Franchising revenue (SPZ_FR)
# --------------------------------------------------------------------------
GROUP_NAMES = ["Alamo", "Brazos Valley", "Caddo", "Cross Timbers", "Gulf Breeze", "Hill Country",
               "Llano", "Mesquite", "Neches", "Ouachita", "Palo Duro", "Piney Woods", "Red Oak",
               "Rio Grande", "Sabine Pass", "Sandhills", "Tallgrass", "Twin Rivers", "Wichita Falls",
               "Bayou", "Big Thicket", "Chisholm", "Concho", "Flint Hills", "Guadalupe", "Lavaca",
               "Lone Prairie", "Medina", "Nueces", "Pedernales", "San Saba", "Sulphur Springs",
               "Washita", "Wildflower"]
units = rng.multinomial(410 - 34, np.ones(34) / 34) + 1
for g, u in zip(GROUP_NAMES, units):
    cust = f"{g} Pizza Partners LLC"
    for mon in mondays:
        rep = u * 19500 * ln(1, 0.06)
        dn = doc("INV")
        kw = dict(typ="Invoice", docno=dn, name=cust, dept="Franchise Services",
                  memo=f"Weekly royalty & ad fund - w/e {(mon - timedelta(days=1)):%m/%d} - {u} units")
        post("SPZ_FR", mon + timedelta(days=1), 41100, rep * 0.055, **kw)
        post("SPZ_FR", mon + timedelta(days=1), 41200, rep * 0.04, **kw)
    if rng.random() < 0.25:
        post("SPZ_FR", date(2026, 8, int(rng.integers(10, 25))), 41100, -ln(2400, 0.4), typ="Credit Memo",
             docno=doc("INV"), name=cust, dept="Franchise Services", memo="Royalty credit - sales restatement")
for d, n, memo in [(date(2026, 7, 16), 3, "Initial franchise fees - 3 units"),
                   (date(2026, 8, 12), 9, "Development agreement - 9 units, Gulf Coast expansion (signed 8/12)"),
                   (date(2026, 8, 27), 2, "Renewal fees - 2 units (10-yr renewal)"),
                   (date(2026, 9, 10), 3, "Initial franchise fees - 3 units")]:
    post("SPZ_FR", d, 41300, n * 25000, typ="Invoice", docno=doc("INV"), name=rng.choice(GROUP_NAMES) +
         " Pizza Partners LLC", dept="Franchise Development", memo=memo)

# --------------------------------------------------------------------------
# 7. G&A, D&A, interest, tax
# --------------------------------------------------------------------------
GA = {"SPZ_US": dict(sal=330000, crent=142000, ins=186000, te=300, dep=2150000, amort=140000, tax=240000),
      "SPZ_CA": dict(sal=70000, crent=21000, ins=28000, te=50, dep=410000, amort=0, tax=60000),
      "SPZ_FR": dict(sal=210000, crent=38000, ins=12000, te=120, dep=35000, amort=260000, tax=910000)}
EMP = ["A. Ramirez", "B. Foster", "C. Lindqvist", "D. Osei", "E. Hart", "F. Mendoza", "G. Byrne",
       "H. Castillo", "I. Novak", "J. Whitlock", "K. Duarte", "L. Sato"]
fr_rent_rows = {}
for ent, g in GA.items():
    for per in PERIODS:
        md = month_days(per)
        for pay in (md[14], md[-1]):
            post(ent, pay, 60100, g["sal"] * ln(1, 0.02), docno=doc("JE"), name="PayCore Payroll Services",
                 dept="Corporate", memo=f"Corporate payroll {pay:%m/%d}", by="integration.payroll",
                 created=min(datetime(pay.year, pay.month, pay.day, 21, 5), LOAD_TS[per] - timedelta(hours=3)))
        office = {"SPZ_US": "Preston Ridge Office Partners LP", "SPZ_FR": "Preston Ridge Office Partners LP",
                  "SPZ_CA": "Bayview Realty Inc."}[ent]
        rid = post(ent, md[0], 60400, g["crent"], typ="Bill", docno=doc("BILL"), name=office,
                   ref=f"PROP-{ent[-2:]}-{md[0]:%y%m}", dept="Corporate", memo=f"HQ office rent - {per} 2026")
        fr_rent_rows[(ent, per)] = rid
        post(ent, md[0], 60500, g["ins"] * ln(1, 0.01), docno=doc("JE"), dept="Finance",
             memo=f"Prepaid insurance amortization - {per}")
        post(ent, md[-1], 62100, g["dep"] * ln(1, 0.01), docno=doc("JE"), dept="Finance",
             memo=f"Monthly depreciation - {per}", by="auto.fixedassets")
        post(ent, md[-1], 62200, g["amort"], docno=doc("JE"), dept="Finance",
             memo=f"Monthly amortization - {per}", by="auto.fixedassets")
        post(ent, md[-1], 70100, g["tax"] * ln(1, 0.05), docno=doc("JE"), dept="Tax",
             memo=f"Income tax provision - {per}")
        for _ in range(int(g["te"] / 3)):
            post(ent, md[int(rng.integers(0, len(md)))], 60300, ln(420, 0.8), typ="Expense Report",
                 docno=doc("ER"), name=rng.choice(EMP), dept="Corporate", memo="Employee expense report")
    if ent == "SPZ_US":
        for per in PERIODS:
            post(ent, month_days(per)[-1], 63100, 1_380_000 * ln(1, 0.005), docno=doc("JE"),
                 name="Term Loan B - Agent", dept="Treasury", memo=f"Interest expense - Term Loan B - {per}")
post("SPZ_US", date(2026, 7, 9), 60500, 74_210.00, docno=doc("JE"), dept="Finance",
     memo="Annual GL policy premium true-up (renewal 7/1)")

PROF = [("Harlow & Pierce LLP", "HP"), ("Whitfield Brennan LLP", "WB"), ("Calder Tax Advisors", "CTA")]
for ent, k in [("SPZ_US", 6), ("SPZ_CA", 2), ("SPZ_FR", 3)]:
    for per in PERIODS:
        md = month_days(per)
        for _ in range(k):
            v, p = PROF[int(rng.integers(0, 3))]
            post(ent, md[int(rng.integers(0, len(md) - 2))], 60200, ln(18000, 0.5), typ="Bill",
                 docno=doc("BILL"), name=v, ref=f"{p}-2026-{int(rng.integers(1000, 9999))}",
                 dept="Corporate", memo="Professional services")

# FR legal accrual cycle (Jul and Aug accrued, reversed next month, billed ~18th)
for per, amt, billed in [("Jul", 118_400, 121_050), ("Aug", 142_600, 139_850)]:
    md = month_days(per)
    nxt = month_days(NEXT[per])
    post("SPZ_FR", md[-1], 60200, amt, docno=doc("JE"), name="Harlow & Pierce LLP", dept="Legal",
         memo=f"ACCR - {per} legal fees unbilled - Harlow & Pierce LLP", tag=f"ACCR-LEGAL-{per}")
    post("SPZ_FR", nxt[0], 60200, -amt, docno=doc("JE"), name="Harlow & Pierce LLP", dept="Legal",
         memo=f"REV - ACCR {per} legal fees - Harlow & Pierce LLP", by="auto.reversal",
         created=datetime(nxt[0].year, nxt[0].month, 1, 6, 0), tag=f"REV-LEGAL-{per}")
    post("SPZ_FR", nxt[17], 60200, billed, typ="Bill", docno=doc("BILL"), name="Harlow & Pierce LLP",
         ref=f"HP-2026-{int(rng.integers(1000, 9999))}", dept="Legal", memo=f"Franchise legal services - {per}")

# M&A transaction costs (new account 64100 opened 8/1)
for d, v, amt, memo in [(date(2026, 8, 6), "Northgate Advisors", 1_250_000.00, "Sell-side advisory - success fee (1st tranche)"),
                        (date(2026, 8, 19), "Harlow & Pierce LLP", 384_620.50, "M&A legal - SPA negotiation & closing"),
                        (date(2026, 9, 9), "Whitfield Brennan LLP", 215_000.00, "Quality of earnings support - buyer requests"),
                        (date(2026, 9, 23), "Harlow & Pierce LLP", 141_880.25, "Post-closing legal - integration matters")]:
    post("SPZ_US", d, 64100, amt, typ="Bill", docno=doc("BILL"), name=v,
         ref=f"{''.join(w[0] for w in v.split()[:2])}-MA-{int(rng.integers(100, 999))}", dept="Corporate", memo=memo)

# Intercompany royalties: 5% of company sales, billed by SPZ_FR at month-end
ic_rows = {}
for ent in ["SPZ_US", "SPZ_CA"]:
    for per in PERIODS:
        md = month_days(per)
        roy = month_sales[(ent, per)] * 0.05
        dn = doc("JE")
        ic_rows[(ent, per)] = post(ent, md[-1], 61100, roy, docno=dn, name="Sparrow Franchising LLC",
                                   ic="SPZ_FR", dept="Finance", memo=f"IC royalty 5% - {per} 2026")
        usd = roy * (FX[per]["avg"] if ent == "SPZ_CA" else 1)
        post("SPZ_FR", md[-1], 42100, usd, docno=doc("JE"), name=ENT[ent]["legal"], ic=ent,
             dept="Finance", memo=f"IC royalty 5% - {ENT[ent]['legal']} - {per} 2026")

# Late-posted entries (posted to period, created after the HFM YTD extract) — cutoff seeds
CUTOFF = [
    ("SI-06", "SPZ_US", date(2026, 7, 31), 50120, 486_215.40, "Bill", "Lone Star Proteins",
     "Protein invoices w/e 7/31 - all regions (received late)", datetime(2026, 8, 6, 10, 14)),
    ("SI-07", "SPZ_FR", date(2026, 7, 31), 60200, 238_750.00, "Bill", "Harlow & Pierce LLP",
     "FDD annual update & state registrations - July", datetime(2026, 8, 7, 15, 41)),
    ("SI-08", "SPZ_US", date(2026, 7, 31), 63100, 197_333.33, "Journal", "Term Loan B - Agent",
     "Interest true-up - Term Loan B SOFR reset (Jul)", datetime(2026, 8, 5, 9, 2)),
    ("SI-09", "SPZ_US", date(2026, 8, 31), 50300, 312_480.66, "Journal", "DashCart Inc.",
     "Marketplace commission true-up per August platform statement", datetime(2026, 9, 8, 11, 37)),
    ("SI-10", "SPZ_FR", date(2026, 8, 31), 41100, 164_902.18, "Journal", "",
     "Royalty true-up - franchisee sales audit findings (Aug)", datetime(2026, 9, 9, 16, 20)),
    ("SI-11", "SPZ_US", date(2026, 8, 31), 70100, 655_000.00, "Journal", "",
     "Q3 tax provision true-up - Aug", datetime(2026, 9, 10, 14, 5)),
]
cutoff_ids = {}
for sid, ent, d, acct, amt, typ, name, memo, cts in CUTOFF:
    cutoff_ids[sid] = post(ent, d, acct, amt, typ=typ, docno=doc("BILL" if typ == "Bill" else "JE"),
                           name=name, memo=memo, ref=(f"LSP-{int(rng.integers(100000, 999999))}" if typ == "Bill" else ""),
                           dept="Finance", created=cts, by=rng.choice(GL_USERS), late=True, tag=sid)

GL_CLEAN = pd.DataFrame(ROWS)

# --------------------------------------------------------------------------
# Source-system (NetSuite) data-quality issues: mutators on the GL
# --------------------------------------------------------------------------


def pick(df, ent, per, acct, name=None, typ=None):
    m = (df._ent == ent) & (df._per == per) & (df._acct == acct)
    if name:
        m &= df.Name.str.strip() == name
    if typ:
        m &= df.Type == typ
    sub = df[m]
    return sub.loc[(sub._nat.abs()).idxmax()]


def add_rows(df, rows):
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)


SOURCE_ISSUES = []  # (sid, type, mutator, meta)


def dup_entry(sid, ent, per, acct, name, ref_variant=None, days_later=6):
    base = pick(GL_CLEAN, ent, per, acct, name=name, typ="Bill")

    def mut(df):
        r = base.to_dict()
        r["Internal ID"] = int(SEQ["id"] + 50_000 + int(sid[-2:]))
        r["Document Number"] = f"BILL-{int(base['Document Number'][5:]) + 7_311:06d}"
        # keyed days later, but still before that month's HFM extract (so it flows into HFM)
        cap = LOAD_TS[per] - timedelta(hours=3)
        r["Created Date"] = max(min(base["Created Date"] + timedelta(days=days_later, hours=2), cap),
                                base["Created Date"] + timedelta(hours=1))
        r["Created By"] = [u for u in (AP_CA if ent == "SPZ_CA" else AP_US) if u != base["Created By"]][0]
        if ref_variant:
            r["Ref No."] = ref_variant(base["Ref No."])
        r["_tag"] = sid
        return add_rows(df, [r]), r
    return base, mut


def capex(sid, ent, d, acct, amt, name, memo, ref):
    def mut(df):
        r = dict(GL_CLEAN.iloc[0])
        per = PER[d.month]
        is_dr = amt > 0
        r.update({"Internal ID": int(SEQ["id"] + 60_000 + int(sid[-2:])), "Document Number": f"BILL-{59_900 + int(sid[-2:]):06d}",
                  "Type": "Bill", "Date": d, "Period": f"{per} 2026", "Subsidiary": NS_SUB[ent],
                  "Account": acct_label(acct), "Department": "Facilities" if acct == 52300 else ("IT" if acct == 54200 else "Corporate"),
                  "Location": "", "Name": name, "Memo": memo, "Ref No.": ref,
                  "Debit": amt, "Credit": None, "Currency": ENT[ent]["ccy"], "Intercompany Entity": "",
                  "Created Date": datetime(d.year, d.month, d.day, 13, 22) + timedelta(days=1),
                  "Created By": (AP_CA if ent == "SPZ_CA" else AP_US)[0],
                  "_ent": ent, "_per": per, "_acct": acct, "_nat": amt, "_ic": "", "_late": False, "_tag": sid})
        return add_rows(df, [r]), r
    return mut


def drop_tag(tag):
    def mut(df):
        r = df[df._tag == tag].iloc[0].to_dict()
        return df[df._tag != tag].copy(), r
    return mut


def drop_row(rid):
    def mut(df):
        return df[df["Internal ID"] != rid].copy(), df[df["Internal ID"] == rid].iloc[0].to_dict()
    return mut


def scale_row(rid, new_amt_fn, sid):
    def mut(df):
        df = df.copy()
        ix = df.index[df["Internal ID"] == rid][0]
        new = round(new_amt_fn(df.at[ix, "_nat"]), 2)
        df.at[ix, "_nat"] = new
        df.at[ix, "Debit"] = new
        df.at[ix, "_tag"] = sid
        return df, df.loc[ix].to_dict()
    return mut


def transpose(x):
    s = f"{x:.2f}"
    whole, cents = s.split(".")
    w = list(whole)
    w[1], w[2] = w[2], w[1]
    return float("".join(w) + "." + cents)


# DUPLICATE_GL_ENTRY
_b, m = dup_entry("SI-21", "SPZ_US", "Sep", 50100, "Valley Dairy Cheese Co.")
SOURCE_ISSUES.append(("SI-21", "DUPLICATE_GL_ENTRY", m, dict(base=_b, note="exact duplicate (same vendor, Ref No., amount)")))
_b, m = dup_entry("SI-22", "SPZ_US", "Jul", 60200, "Whitfield Brennan LLP", ref_variant=lambda r: r.replace("WB-", "WB"))
SOURCE_ISSUES.append(("SI-22", "DUPLICATE_GL_ENTRY", m, dict(base=_b, note="near-duplicate (Ref No. keyed without hyphen)")))
_b, m = dup_entry("SI-23", "SPZ_CA", "Jul", 50110, "Maple Leaf Foodservice", days_later=9)
SOURCE_ISSUES.append(("SI-23", "DUPLICATE_GL_ENTRY", m, dict(base=_b, note="exact duplicate (same vendor, Ref No., amount)")))
_b, m = dup_entry("SI-24", "SPZ_FR", "Aug", 60400, "Preston Ridge Office Partners LP", ref_variant=lambda r: r + "A", days_later=11)
SOURCE_ISSUES.append(("SI-24", "DUPLICATE_GL_ENTRY", m, dict(base=_b, note="near-duplicate (suffix 'A' added to Ref No.)")))
_b, m = dup_entry("SI-25", "SPZ_US", "Aug", 54200, "OrderLoop POS", ref_variant=lambda r: r.replace("OL-", "OL"), days_later=4)
SOURCE_ISSUES.append(("SI-25", "DUPLICATE_GL_ENTRY", m, dict(base=_b, note="near-duplicate (Ref No. keyed without hyphen)")))

# MISSING_ACCRUAL_REVERSAL
for sid, tag in [("SI-26", "REV-UTIL-SPZ_US-Texas North-Aug"), ("SI-27", "REV-LEGAL-Aug"), ("SI-28", "REV-CC-SPZ_US-Sep")]:
    SOURCE_ISSUES.append((sid, "MISSING_ACCRUAL_REVERSAL", drop_tag(tag), dict(tag=tag)))

# CAPEX_EXPENSED
SOURCE_ISSUES.append(("SI-29", "CAPEX_EXPENSED", capex("SI-29", "SPZ_US", date(2026, 8, 18), 52300, 412_860.00,
                      "Mid-South Oven Co.", "Oven replacement program - 14 new conveyor ovens, purchase & install", "MSO-88213"), {}))
SOURCE_ISSUES.append(("SI-30", "CAPEX_EXPENSED", capex("SI-30", "SPZ_CA", date(2026, 7, 22), 54200, 318_400.00,
                      "OrderLoop POS", "POS terminal hardware - 64 restaurants (new terminals, 5-yr life)", "OL-HW-7731"), {}))
SOURCE_ISSUES.append(("SI-31", "CAPEX_EXPENSED", capex("SI-31", "SPZ_FR", date(2026, 9, 14), 60400, 287_500.00,
                      "Crestview Build Group", "Franchise training center build-out - progress billing #2", "CBG-2026-114"), {}))

# INTERCOMPANY_MISMATCH
SOURCE_ISSUES.append(("SI-32", "INTERCOMPANY_MISMATCH", scale_row(ic_rows[("SPZ_CA", "Jul")], lambda x: x * 0.9, "SI-32"),
                      dict(note="CA booked royalty at superseded 4.5% rate; SPZ_FR billed 5%")))
SOURCE_ISSUES.append(("SI-33", "INTERCOMPANY_MISMATCH", drop_row(ic_rows[("SPZ_US", "Sep")]),
                      dict(note="US never booked Sep IC royalty expense; SPZ_FR booked income")))
SOURCE_ISSUES.append(("SI-34", "INTERCOMPANY_MISMATCH", scale_row(ic_rows[("SPZ_US", "Aug")], transpose, "SI-34"),
                      dict(note="digit transposition when keying the US Aug royalty")))

GL_FINAL = GL_CLEAN.copy()
SOURCE_EVIDENCE = {}
for sid, typ, mut, meta in SOURCE_ISSUES:
    GL_FINAL, row = mut(GL_FINAL)
    SOURCE_EVIDENCE[sid] = row

# --------------------------------------------------------------------------
# HFM build
# --------------------------------------------------------------------------


def rate_correct(ent, per):
    return FX[per]["avg"] if ENT[ent]["ccy"] == "CAD" else 1.0


def rate_loaded(ent, per):
    if ENT[ent]["ccy"] != "CAD":
        return 1.0
    if per == "Aug":
        return FX["Aug"]["close"]   # SI-12 closing rate used for P&L
    if per == "Sep":
        return FX["Aug"]["avg"]     # SI-13 stale rate table
    return FX[per]["avg"]


LEGIT_JNL = [
    ("JNL-26-0711", "SPZ_US", "Jul", "D1000", 412_500.00, "PPA - depreciation on fair-value step-up of restaurant equipment", "a.lindgren", "PPA memo v2 / valuation rpt s4.3"),
    ("JNL-26-0812", "SPZ_US", "Aug", "D1000", 412_500.00, "PPA - depreciation on fair-value step-up of restaurant equipment", "a.lindgren", "PPA memo v2 / valuation rpt s4.3"),
    ("JNL-26-0913", "SPZ_US", "Sep", "D1000", 412_500.00, "PPA - depreciation on fair-value step-up of restaurant equipment", "a.lindgren", "PPA memo v2 / valuation rpt s4.3"),
    ("JNL-26-0714", "SPZ_US", "Jul", "C3000", -118_340.00, "ASC 842 alignment - straight-line rent adjustment (LRG policy)", "p.mbeki", "Lease schedule LS-SPZ-Q3"),
    ("JNL-26-0815", "SPZ_US", "Aug", "C3000", -118_340.00, "ASC 842 alignment - straight-line rent adjustment (LRG policy)", "p.mbeki", "Lease schedule LS-SPZ-Q3"),
    ("JNL-26-0916", "SPZ_US", "Sep", "C3000", -118_340.00, "ASC 842 alignment - straight-line rent adjustment (LRG policy)", "p.mbeki", "Lease schedule LS-SPZ-Q3"),
    ("JNL-26-0917", "SPZ_US", "Sep", "G1100", 185_000.00, "Accrue Q3 statutory audit fee - Whitfield Brennan LLP", "p.mbeki", "Engagement letter EL-2026-SPZ"),
    ("JNL-26-0818", "SPZ_US", "Aug", "C2100", 96_400.00, "Workers' comp reserve true-up per actuarial study (Q3)", "a.lindgren", "Actuarial rpt 2026-Q3"),
]
DUP_JNL = [  # (sid, duplicates, new id, description variant)
    ("SI-14", "JNL-26-0812", "JNL-26-0831", None),
    ("SI-15", "JNL-26-0916", "JNL-26-0934", None),
    ("SI-16", "JNL-26-0917", "JNL-26-0935", "Accrue Q3 audit fee - Whitfield Brennan"),
    ("SI-17", "JNL-26-0818", "JNL-26-0829", None),
]


def journal_rows(include_dups=True, only_dup=None):
    out = []
    for j in LEGIT_JNL:
        out.append(dict(zip(["JE_ID", "Entity", "Period", "Account", "Amount_USD", "Description", "Created_By", "Support"], j)))
    for sid, src, new, desc in DUP_JNL:
        if include_dups or only_dup == sid:
            s = next(o for o in out if o["JE_ID"] == src)
            d = dict(s, JE_ID=new, Description=desc or s["Description"], _sid=sid)
            out.append(d)
    return out


def build(gl, mapping, rate_fn, cutoff=False, flips=(), journals=None):
    g = gl[["_ent", "_per", "_acct", "_nat", "_ic", "_late"]].copy()
    g["hp"] = g["_per"]
    if cutoff:
        m = g._late & g._per.isin(NEXT.keys())
        g.loc[m, "hp"] = g.loc[m, "_per"].map(NEXT)
    g["hfm"] = g._acct.map(mapping)
    g = g.dropna(subset=["hfm"])
    g["icp"] = np.where(g.hfm.isin(["R9000", "G9000"]), g._ic, "[ICP None]")
    agg = g.groupby(["_ent", "hp", "hfm", "icp"])._nat.sum().reset_index()
    agg["usd"] = [round(n * rate_fn(e, p), 2) for e, p, n in zip(agg._ent, agg.hp, agg._nat)]
    s = agg.set_index(["_ent", "hp", "hfm", "icp"]).usd
    s.index.names = ["entity", "period", "account", "icp"]
    for j in (journals or []):
        k = (j["Entity"], j["Period"], j["Account"], "[ICP None]")
        s.loc[k] = round(s.get(k, 0.0) + j["Amount_USD"], 2)
    for (e, p, a) in flips:
        idx = [k for k in s.index if k[:3] == (e, p, a)]
        s.loc[idx] = -s.loc[idx]
    return s.sort_index()


FLIPS = {"SI-18": ("SPZ_US", "Jul", "R1200"), "SI-19": ("SPZ_FR", "Sep", "R2200")}

legit = journal_rows(include_dups=False)
HFM_CORRECT = build(GL_FINAL, CORRECT_MAP, rate_correct, journals=legit)
HFM_ACTUAL = build(GL_FINAL, LOADED_MAP, rate_loaded, cutoff=True, flips=list(FLIPS.values()),
                   journals=journal_rows(include_dups=True))


def cell_diff(a, b):
    a = a.groupby(level=[0, 1, 2]).sum()
    b = b.groupby(level=[0, 1, 2]).sum()
    d = a.sub(b, fill_value=0).round(2)
    return d[d.abs() >= 0.01]


def hfm_issue_cells(sid):
    mp, rf, co, fl, jn = CORRECT_MAP, rate_correct, False, [], legit
    if sid in ("SI-01", "SI-02", "SI-03"):
        mp = dict(CORRECT_MAP); acct = {"SI-01": 40200, "SI-02": 53200, "SI-03": 51400}[sid]
        mp[acct] = LOADED_MAP[acct]
    elif sid in ("SI-04", "SI-05"):
        mp = dict(CORRECT_MAP); del mp[{"SI-04": 64100, "SI-05": 40410}[sid]]
    elif sid in ("SI-12", "SI-13"):
        tp = "Aug" if sid == "SI-12" else "Sep"
        # FX error measured as it shows in HFM (i.e. on the accounts as loaded)
        rf = lambda e, p: rate_loaded(e, p) if p == tp else rate_correct(e, p)
        return cell_diff(build(GL_FINAL, LOADED_MAP, rf, journals=legit),
                         build(GL_FINAL, LOADED_MAP, rate_correct, journals=legit))
    elif sid in FLIPS:
        fl = [FLIPS[sid]]
    elif sid in [d[0] for d in DUP_JNL]:
        jn = journal_rows(include_dups=False, only_dup=sid)
    if sid in [c[0] for c in CUTOFF]:
        g = GL_FINAL.copy()
        g["_late"] = g._tag == sid
        return cell_diff(build(g, mp, rf, cutoff=True, journals=jn), HFM_CORRECT)
    return cell_diff(build(GL_FINAL, mp, rf, cutoff=False, flips=fl, journals=jn), HFM_CORRECT)


def source_issue_cells(sid):
    g = GL_CLEAN.copy()
    for s, _, mut, _ in SOURCE_ISSUES:
        if s == sid:
            g, _ = mut(g)
    return cell_diff(build(g, CORRECT_MAP, rate_correct, journals=legit),
                     build(GL_CLEAN, CORRECT_MAP, rate_correct, journals=legit))


# --------------------------------------------------------------------------
# Answer key
# --------------------------------------------------------------------------
REV_MAP = {}
for a, h in CORRECT_MAP.items():
    REV_MAP.setdefault(h, []).append(a)

ISSUES = []


def money(x):
    return f"${abs(x):,.2f}"


def add_issue(sid, typ, category, title, cells, root_cause, fix, evidence, two_sided=False,
              source_accounts=None, extra_cells=()):
    cell_list = []
    for (e, p, a), v in cells.items():
        sa = source_accounts.get(a) if isinstance(source_accounts, dict) else source_accounts
        cell_list.append(dict(entity=e, period=p, hfm_account=a, source_account=sa, impact_usd=round(float(v), 2)))
    for c in extra_cells:
        cell_list.append(c)
    impact = round(sum(abs(c["impact_usd"]) for c in cell_list) / (2 if two_sided else 1), 2)
    ents = sorted({c["entity"] for c in cell_list})
    pers = [p for p in PERIODS if p in {c["period"] for c in cell_list}]
    adj = [dict(system="HFM" if category == "GL vs HFM break" else "NetSuite", entity=c["entity"], period=c["period"],
                account=c["hfm_account"], amount_usd=round(-c["impact_usd"], 2),
                note="reverse misstatement (natural sign, USD)") for c in cell_list if c["impact_usd"]]
    ISSUES.append(dict(issue_id=sid, issue_type=typ, category=category, title=title, entities=ents, periods=pers,
                       impact_usd=impact, root_cause=root_cause, recommended_fix=fix, evidence=evidence,
                       cells=cell_list, correcting_entries=adj))


CAT_B, CAT_S = "GL vs HFM break", "Source data quality"

# Mapping errors
for sid, acct, wrong in [("SI-01", 40200, "R2000"), ("SI-02", 53200, "G1000"), ("SI-03", 51400, "C3100")]:
    right = CORRECT_MAP[acct]
    c = hfm_issue_cells(sid)
    add_issue(sid, "MAPPING_ERROR", CAT_B,
              f"{acct} {COA[acct]['name']} mapped to {wrong} ({HFM_DESC[wrong]}) instead of {right} ({HFM_DESC[right]})",
              c, f"Mapping v3 DRAFT row for {acct} points to {wrong}. HFM is internally consistent with the faulty map, "
                 f"so a standard tie-out shows no break; the error is only visible by judging whether the account belongs there.",
              f"Correct mapping row {acct} -> {right}; reclass in HFM for all affected entities/periods; re-run FDMEE validation.",
              [f"Mapping file row {acct}", f"HFM {wrong} balances at company-operated entities"], two_sided=True,
              source_accounts=acct)

# Unmapped
for sid, acct in [("SI-04", 64100), ("SI-05", 40410)]:
    c = hfm_issue_cells(sid)
    add_issue(sid, "UNMAPPED_ACCOUNT", CAT_B,
              f"New NetSuite account {acct} {COA[acct]['name']} missing from mapping - excluded from HFM load",
              c, f"Account {acct} was opened in August and never added to mapping v3. FDMEE rejected the rows (see load log), "
                 f"so HFM {CORRECT_MAP[acct]} is understated.",
              f"Add mapping {acct} -> {CORRECT_MAP[acct]}; reload Aug and Sep.",
              [f"GL account {acct} activity Aug-Sep", "Load log: rows rejected Aug/Sep"], source_accounts=acct)

# Cutoff
for sid, ent, d, acct, amt, typ, name, memo, cts in CUTOFF:
    c = hfm_issue_cells(sid)
    per = PER[d.month]
    add_issue(sid, "CUTOFF_TIMING", CAT_B,
              f"{ent} {acct} {COA[acct]['name']}: {money(amt)} posted to {per} after the {per} HFM extract - landed in {NEXT[per]}",
              c, f"Entry dated {fmt_date(d)} was created {fmt_ts(cts)}, after the {per} YTD extract ({fmt_ts(LOAD_TS[per])}). "
                 f"HFM loads YTD, so the amount surfaced in {NEXT[per]} periodic.",
              f"Post prior-period adjustment in HFM: move {money(amt)} from {NEXT[per]} to {per} on {CORRECT_MAP[acct]}.",
              [f"NetSuite Internal ID {cutoff_ids[sid]}", f"Load log {per} extract timestamp"], two_sided=True,
              source_accounts=acct)

# FX
for sid, per, wrong in [("SI-12", "Aug", f"Aug closing rate {FX['Aug']['close']}"), ("SI-13", "Sep", f"Aug average rate {FX['Aug']['avg']}")]:
    c = hfm_issue_cells(sid)
    add_issue(sid, "FX_TRANSLATION", CAT_B,
              f"SPZ_CA {per} P&L translated at {wrong} instead of {per} average {FX[per]['avg']}",
              c, f"HFM rate table for {per} carried the wrong AvgRate for CAD. P&L accounts must translate at the monthly average rate.",
              f"Correct HFM CAD AvgRate for {per} to {FX[per]['avg']}; re-consolidate SPZ_CA.",
              ["LRG Treasury FX rates file", f"Every SPZ_CA {per} account off by the same ratio"],
              source_accounts=None)

# Duplicate HFM journals
for sid, src, new, desc in DUP_JNL:
    c = hfm_issue_cells(sid)
    add_issue(sid, "DUPLICATE_HFM_JOURNAL", CAT_B,
              f"Top-side journal {src} posted twice (duplicate {new})",
              c, f"{new} repeats {src} (same entity, account, amount and support). Posted a day later by a different preparer.",
              f"Reverse {new} in HFM; add duplicate-check control to journal approval.",
              [f"HFM journal register {src} and {new}"])

# Sign flips
for sid, (e, p, a) in FLIPS.items():
    c = hfm_issue_cells(sid)
    add_issue(sid, "SIGN_FLIP", CAT_B, f"{e} {p} {a} {HFM_DESC[a]} loaded with reversed sign",
              c, "Load file for this cell carried the wrong sign (natural-sign conversion skipped).",
              f"Reload {e} {p} {a} with correct sign.", [f"HFM extract {e} {a} {p} vs adjacent periods"],
              source_accounts={"R1200": 40300, "R2200": 41300}[a])

# Source issues
for sid, typ, mut, meta in SOURCE_ISSUES:
    c = source_issue_cells(sid)
    row = SOURCE_EVIDENCE[sid]
    acct = int(row["_acct"])
    if typ == "DUPLICATE_GL_ENTRY":
        b = meta["base"]
        add_issue(sid, typ, CAT_S, f"{row['_ent']} {acct}: {row['Name'].strip()} bill entered twice ({money(row['_nat'])} {ENT[row['_ent']]['ccy']})",
                  c, f"Internal ID {row['Internal ID']} duplicates {b['Internal ID']} - {meta['note']}. Flows to HFM, so no tie-out break.",
                  f"Void Internal ID {row['Internal ID']} in NetSuite (or reverse if paid); reload HFM {row['_per']}.",
                  [f"NetSuite Internal ID {b['Internal ID']}", f"NetSuite Internal ID {row['Internal ID']}"], source_accounts=acct)
    elif typ == "MISSING_ACCRUAL_REVERSAL":
        add_issue(sid, typ, CAT_S, f"{row['_ent']} {acct}: accrual not reversed in {row['_per']} - expense double-counted ({money(row['_nat'])})",
                  c, f"Expected auto-reversal '{row['Memo']}' on {fmt_date(row['Date'])} is missing; the actual bill also posted.",
                  f"Post the reversal in {row['_per']} for {money(row['_nat'])}; reload HFM.",
                  [f"Accrual memo '{row['Memo'].replace('REV - ', '')}' with no matching REV entry"], source_accounts=acct)
    elif typ == "CAPEX_EXPENSED":
        add_issue(sid, typ, CAT_S, f"{row['_ent']} {acct}: capital purchase expensed ({money(row['_nat'])} {ENT[row['_ent']]['ccy']})",
                  c, f"'{row['Memo']}' is a long-lived asset, recorded to {acct} {COA[acct]['name']}.",
                  "Reclass to fixed assets (capitalize) and start depreciation; reload HFM.",
                  [f"NetSuite Internal ID {row['Internal ID']}"], source_accounts=acct)
    else:
        ent, per = row["_ent"], row["_per"]
        cp = dict(entity="SPZ_FR", period=per, hfm_account="R9000", source_account=42100, impact_usd=0.0)
        add_issue(sid, typ, CAT_S, f"IC royalty mismatch: {ent} G9000 vs SPZ_FR R9000 ({per}) - {money(sum(v for v in c))} USD",
                  c, meta["note"] + ". SPZ_FR side is correct (5% of sales).",
                  f"Book true-up in {ent} 61100 to agree to SPZ_FR billing; confirm IC rate schedule.",
                  [f"NetSuite Internal ID {row['Internal ID']}", "HFM ICP matching report"],
                  source_accounts=61100, extra_cells=[cp])

ISSUES.sort(key=lambda x: x["issue_id"])
# public IDs run SI-01..SI-33 contiguously
for n, iss in enumerate(ISSUES, start=1):
    iss["issue_id"] = f"SI-{n:02d}"
assert len(ISSUES) == 33, len(ISSUES)

# --------------------------------------------------------------------------
# Write outputs
# --------------------------------------------------------------------------
ARIAL = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1F3A5F")
NOTE_FILL = PatternFill("solid", fgColor="FFF4CC")
THIN = Side(style="thin", color="D0D7E2")


def banner(ws, lines, ncols):
    for i, (txt, bold, fill) in enumerate(lines, start=1):
        ws.cell(row=i, column=1, value=txt).font = Font(name=ARIAL, bold=bold, size=11 if i == 1 else 9,
                                                        color="7A4B00" if fill else "1F3A5F")
        if fill:
            for c in range(1, ncols + 1):
                ws.cell(row=i, column=c).fill = NOTE_FILL


def table(ws, df, start_row, money_cols=(), widths=None):
    for j, col in enumerate(df.columns, start=1):
        c = ws.cell(row=start_row, column=j, value=col)
        c.font = Font(name=ARIAL, bold=True, color="FFFFFF", size=10)
        c.fill = HDR_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, row in enumerate(df.itertuples(index=False), start=start_row + 1):
        for j, v in enumerate(row, start=1):
            c = ws.cell(row=i, column=j, value=None if (isinstance(v, float) and np.isnan(v)) else v)
            c.font = Font(name=ARIAL, size=10)
            c.border = Border(bottom=THIN)
            if df.columns[j - 1] in money_cols:
                c.number_format = '#,##0.00;(#,##0.00);"-"'
    for j, col in enumerate(df.columns, start=1):
        w = (widths or {}).get(col) or min(max(len(str(col)), *(len(str(x)) for x in df[col].head(200))) + 2, 60)
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    ws.auto_filter.ref = f"A{start_row}:{get_column_letter(len(df.columns))}{start_row + len(df)}"


for sub in ["sparrow_netsuite", "larkspur_hfm", "mapping", "reference"]:
    (DATA / sub).mkdir(parents=True, exist_ok=True)
KEY.mkdir(exist_ok=True)

# NetSuite GL detail (sorted like a saved search: by date, then internal id)
out = GL_FINAL.sort_values(["Date", "Internal ID"]).copy()
mess = rng.random(len(out)) < 0.006
out.loc[mess, "Name"] = out.loc[mess, "Name"].astype(str) + " "
out["Date"] = out["Date"].map(fmt_date)
out["Created Date"] = out["Created Date"].map(fmt_ts)
cols = [c for c in out.columns if not c.startswith("_")]
out[cols].to_csv(DATA / "sparrow_netsuite" / "SPZ_GL_Detail_FY26Q3_IncomeStatement.csv", index=False, float_format="%.2f")

pd.DataFrame([dict(Account=a, Name=v["name"], Parent=v["parent"],
                   Type="Income" if a < 50000 else "Expense",
                   **{"Normal Balance": "Credit" if v["nat"] == "CR" else "Debit"},
                   **{"Date Opened": "8/1/2026" if a in (40410, 64100) else "1/1/2019"})
              for a, v in COA.items()]).to_csv(DATA / "sparrow_netsuite" / "SPZ_Chart_of_Accounts.csv", index=False)

# HFM extract (Smart View style, periodic, USD)
hx = HFM_ACTUAL.reset_index()
hx.columns = ["Entity", "Period", "Account", "ICP", "USD"]
wide = hx.pivot_table(index=["Entity", "Account", "ICP"], columns="Period", values="USD", aggfunc="sum").reindex(columns=PERIODS)
wide = wide.reset_index()
wide.insert(2, "Account Description", wide.Account.map(HFM_DESC))
wide = wide.sort_values(["Entity", "Account", "ICP"]).fillna(0.0)
wb = Workbook(); ws = wb.active; ws.title = "SPZ_Q3_Periodic"
banner(ws, [("Larkspur Restaurant Group  |  HFM application: LRGCONS", True, False),
            ("Ad hoc grid - Smart View extract", False, False),
            ("POV: Scenario=Actual | Year=FY2026 | View=Periodic | Value=<Entity Curr Total> translated to USD | Parent=SPZ_TOTAL", False, False),
            ("Extracted 10/6/2026 8:41 AM by r.okafor", False, False),
            (NOTICE, True, True)], 7)
table(ws, wide, 7, money_cols=PERIODS, widths={"Account Description": 36, "Jul": 16, "Aug": 16, "Sep": 16, "ICP": 13})
wb.save(DATA / "larkspur_hfm" / "LRG_HFM_Extract_SPZ_FY26Q3.xlsx")

jr = pd.DataFrame(journal_rows(include_dups=True))
created = {"JNL-26-0711": "8/6/2026 2:10 PM", "JNL-26-0812": "9/5/2026 10:03 AM", "JNL-26-0913": "10/6/2026 9:15 AM",
           "JNL-26-0714": "8/6/2026 3:44 PM", "JNL-26-0815": "9/5/2026 11:20 AM", "JNL-26-0916": "10/6/2026 9:52 AM",
           "JNL-26-0917": "10/6/2026 10:31 AM", "JNL-26-0818": "9/5/2026 4:02 PM", "JNL-26-0831": "9/6/2026 9:14 AM",
           "JNL-26-0934": "10/7/2026 8:47 AM", "JNL-26-0935": "10/7/2026 9:05 AM", "JNL-26-0829": "9/6/2026 9:40 AM"}
dup_by = {"JNL-26-0831": "c.huang", "JNL-26-0934": "c.huang", "JNL-26-0935": "c.huang", "JNL-26-0829": "c.huang"}
jr["Created_By"] = [dup_by.get(j, c) for j, c in zip(jr.JE_ID, jr.Created_By)]
jr["Created_On"] = jr.JE_ID.map(created)
jr["ICP"] = "[ICP None]"
jr["Approved_By"] = "m.castellano"
jr["Status"] = "Posted"
jr["Account_Description"] = jr.Account.map(HFM_DESC)
jr = jr.sort_values(["Period", "JE_ID"], key=lambda s: s.map({p: i for i, p in enumerate(PERIODS)}) if s.name == "Period" else s)
jr[["JE_ID", "Entity", "Period", "Account", "Account_Description", "ICP", "Amount_USD", "Description", "Support",
    "Created_By", "Created_On", "Approved_By", "Status"]].to_csv(DATA / "larkspur_hfm" / "LRG_HFM_Journal_Register_FY26Q3.csv", index=False)

pd.DataFrame([
    dict(Period=p, Load_Type="YTD", Source="NetSuite saved search 'SPZ TB by Acct - HFM'", Extract_Timestamp=fmt_ts(LOAD_TS[p]),
         Load_Timestamp=fmt_ts(LOAD_TS[p] + timedelta(minutes=37)), Loaded_By="r.okafor", Mapping_Version="v3 DRAFT",
         Entities="SPZ_US, SPZ_CA, SPZ_FR",
         Rows_Rejected={"Jul": 0, "Aug": 2, "Sep": 2}[p],
         Validation_Note={"Jul": "All rows mapped", "Aug": "2 rows rejected - unmapped source accounts (SPZ_US). Load forced.",
                          "Sep": "2 rows rejected - unmapped source accounts (SPZ_US). Load forced."}[p])
    for p in PERIODS]).to_csv(DATA / "larkspur_hfm" / "LRG_HFM_Load_Log_FY26Q3.csv", index=False)

pd.DataFrame([dict(Account=a, Description=d, Type=t, Natural_Sign="Negative" if a == "R1200" else "Positive")
              for a, d, t in HFM_COA]).to_csv(DATA / "larkspur_hfm" / "LRG_HFM_Chart_of_Accounts.csv", index=False)

# Mapping workbook (v3 DRAFT, as used for the load)
mrows = []
preparers = ["j.patel", "r.okafor"]
for a, v in COA.items():
    if a not in LOADED_MAP:
        continue
    h = LOADED_MAP[a]
    mrows.append({"SPZ Account": a, "SPZ Account Name": v["name"], "SPZ Type": "Income" if a < 50000 else "Expense",
                  "LRG HFM Account": h, "LRG HFM Description": HFM_DESC[h],
                  "ICP Rule": "From NetSuite 'Intercompany Entity'" if h in ("R9000", "G9000") else "[ICP None]",
                  "Sign Rule": "Flip (CR natural)" if v["nat"] == "CR" else "As is (DR natural)",
                  "Status": "Approved" if a not in (51400,) else "Pending review",
                  "Prepared By": preparers[a % 2], "Reviewed By": "m.castellano" if a not in (51400,) else "",
                  "Comment": {40200: "Fee income - grouped with royalty-type revenue", 53200: "Fund contribution treated as overhead",
                              51400: "Driver reimbursements - operating cost?"}.get(a, "")})
mp = pd.DataFrame(mrows)
wb = Workbook(); ws = wb.active; ws.title = "Mapping"
banner(ws, [("Sparrow Pizza (NetSuite) -> Larkspur (HFM LRGCONS) chart of accounts mapping", True, False),
            ("Version 3 DRAFT  |  Used for FY26 Q3 loads  |  Owner: LRG Consolidations", False, False),
            (NOTICE, True, True)], 11)
table(ws, mp, 5, widths={"SPZ Account Name": 36, "LRG HFM Description": 34, "ICP Rule": 30, "Comment": 44,
                         "Sign Rule": 20, "Status": 15})
cl = wb.create_sheet("Change Log")
table(cl, pd.DataFrame([
    dict(Version="v1", Date="6/18/2026", Author="j.patel", Change="Initial mapping from SPZ CoA (FY25 TB)"),
    dict(Version="v2", Date="7/22/2026", Author="r.okafor", Change="Added IC royalty accounts and ICP rule"),
    dict(Version="v3 DRAFT", Date="8/2/2026", Author="j.patel", Change="Regrouped revenue/marketing lines; 51400 pending review"),
]), 1, widths={"Change": 60})
wb.save(DATA / "mapping" / "SPZ_to_LRG_CoA_Mapping_v3_DRAFT.xlsx")

pd.DataFrame([dict(Period=p, Year="FY2026", From_Currency="CAD", To_Currency="USD", Average_Rate=FX[p]["avg"],
                   Closing_Rate=FX[p]["close"], Source="LRG Treasury - official month-end rates",
                   Policy="P&L: Average_Rate | Balance sheet: Closing_Rate") for p in PERIODS]
             ).to_csv(DATA / "reference" / "LRG_Treasury_FX_Rates_FY26Q3.csv", index=False)
pd.DataFrame([dict(HFM_Entity=k, NetSuite_Subsidiary=NS_SUB[k], Legal_Name=v["legal"], Functional_Currency=v["ccy"],
                   HFM_Parent="SPZ_TOTAL", Note="Fictional entity")
              for k, v in ENT.items()]).to_csv(DATA / "reference" / "Entity_Map.csv", index=False)


def jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return str(o)


key = dict(dataset="Sparrow Pizza -> Larkspur Restaurant Group, FY26 Q3 (SYNTHETIC)", notice=NOTICE,
           seed=SEED, issue_count=len(ISSUES), total_impact_usd=round(sum(i["impact_usd"] for i in ISSUES), 2),
           issues=ISSUES)
(KEY / "seeded_issues.json").write_text(json.dumps(key, indent=2, default=jsonable))
pd.DataFrame([dict(issue_id=i["issue_id"], issue_type=i["issue_type"], category=i["category"],
                   entities=", ".join(i["entities"]), periods=", ".join(i["periods"]), impact_usd=i["impact_usd"],
                   title=i["title"], recommended_fix=i["recommended_fix"]) for i in ISSUES]
             ).to_csv(KEY / "seeded_issues_summary.csv", index=False)

print(f"GL lines: {len(GL_FINAL):,} | HFM cells: {len(HFM_ACTUAL):,} | seeded issues: {len(ISSUES)} | "
      f"impact ${key['total_impact_usd']:,.0f}")
