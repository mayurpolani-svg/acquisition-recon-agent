# Reconciliation memo — Sparrow Pizza → Larkspur HFM, Q3 FY26
*Synthetic data. Prepared by the reconciliation agent for controller review.*

## Summary
The tie-out has 54 breaks, and the mapping review and scans found more errors that a tie-out cannot see. Breaks that net to zero across two months are cutoff items: six entries were created after the Jul or Aug HFM extract and landed a month late. The remaining breaks are four HFM top-side journals posted twice, a US R1200 sign flip, a FR R2200 sign flip, and SPZ_CA translated at the closing rate instead of the average rate in Aug and Sep. Unmapped accounts 40410 (Catering Sales) and 64100 (M&A costs) are excluded from HFM. Accounts 40200 and 53200 are mapped to the wrong HFM accounts, and three of the five capital purchases (ovens, POS hardware, training-center build-out) and five vendor bills are in the GL as expenses or duplicates. Three month-end accruals were never reversed. The intercompany royalty does not agree to the partner's expense in three places. Account 51400 (driver reimbursement, pending review) is left as mapped to C3100 and is not reported as an error. The Chisholm development fee (INV-022309, $225k) was not assessed for ASC 606 deferral, so it is not reported either.

**31 findings · $20,688,793 total misstatement**

| # | Type | Entity | Period | Account | Amount (USD) | Root cause |
|---|---|---|---|---|--:|---|
| A-001 | FX_TRANSLATION | SPZ_CA | * | R1000 | 157,178 | The Aug and Sep P&L loads for the CAD entity used the Treasury month-end closing rate instead of the monthly average rate required for P&L. |
| A-002 | CUTOFF_TIMING | SPZ_US | Jul | C1000 / 50120 | 486,215 | The late-received July invoice was entered after the Jul extract, so HFM picked it up in Aug. |
| A-003 | CUTOFF_TIMING | SPZ_FR | Jul | G1100 / 60200 | 238,750 | The July bill was posted after the Jul extract, so it landed in Aug HFM. |
| A-004 | CUTOFF_TIMING | SPZ_US | Jul | I1000 / 63100 | 197,333 | The Jul interest true-up journal was booked after the Jul extract, so it landed in Aug. |
| A-005 | CUTOFF_TIMING | SPZ_US | Aug | C1100 / 50300 | 312,481 | The Aug true-up was posted after the Aug extract, so it landed in Sep HFM. |
| A-006 | CUTOFF_TIMING | SPZ_FR | Aug | R2000 / 41100 | 164,902 | The Aug royalty true-up was posted after the Aug extract, so it landed in Sep HFM. |
| A-007 | CUTOFF_TIMING | SPZ_US | Aug | T1000 / 70100 | 655,000 | The Aug tax provision true-up was posted after the Aug extract, so it landed in Sep HFM. |
| A-008 | SIGN_FLIP | SPZ_US | Jul | R1200 / 40300 | 4,166,922 | The Jul discount balance was loaded with the wrong sign, so a contra-revenue was loaded as revenue. |
| A-009 | SIGN_FLIP | SPZ_FR | Sep | R2200 / 41300 | 150,000 | The Sep franchise fee revenue was loaded with the wrong sign. |
| A-010 | DUPLICATE_HFM_JOURNAL | SPZ_US | Aug | D1000 | 412,500 | The Aug PPA depreciation journal was posted twice by different preparers. |
| A-011 | DUPLICATE_HFM_JOURNAL | SPZ_US | Aug | C2100 | 96,400 | The same reserve true-up was posted twice. |
| A-012 | DUPLICATE_HFM_JOURNAL | SPZ_US | Sep | C3000 | 118,340 | The Sep ASC 842 journal was posted twice, so occupancy is understated by 118,340. |
| A-013 | DUPLICATE_HFM_JOURNAL | SPZ_US | Sep | G1100 | 185,000 | The audit fee accrual was posted twice. The descriptions differ slightly but the support, amount and account are identical. |
| A-014 | UNMAPPED_ACCOUNT | SPZ_US | * | R1000 / 40410 | 525,231 | A new revenue account was created in NetSuite and never added to mapping v3 DRAFT. The load was forced despite the rejected rows. |
| A-015 | UNMAPPED_ACCOUNT | SPZ_US | * | X1000 / 64100 | 1,991,501 | The M&A cost account is missing from the mapping, so the costs are excluded from HFM. The load was forced. |
| A-016 | MAPPING_ERROR | * | * | R2000 / 40200 | 2,762,522 | The delivery fee income was mapped to the royalty account instead of R1100. |
| A-017 | MAPPING_ERROR | * | * | G1000 / 53200 | 4,298,452 | The ad fund contribution was mapped to G&A, so restaurant-level advertising is understated and G&A overstated. |
| A-018 | DUPLICATE_GL_ENTRY | SPZ_US | Sep | C1000 / 50100 | 152,357 | The same vendor bill was entered twice. |
| A-019 | DUPLICATE_GL_ENTRY | SPZ_US | Jul | G1100 / 60200 | 36,556 | The bill was re-keyed with a normalized ref, which bypassed the duplicate check. |
| A-020 | DUPLICATE_GL_ENTRY | SPZ_CA | Jul | C1000 / 50110 | 30,126 | The same vendor bill was entered twice. |
| A-021 | DUPLICATE_GL_ENTRY | SPZ_FR | Aug | G1000 / 60400 | 38,000 | The monthly rent bill was entered twice, the second time with an 'A' suffix on the ref. |
| A-022 | DUPLICATE_GL_ENTRY | SPZ_US | Aug | C5000 / 54200 | 58,968 | The Aug subscription was entered twice with a different ref format. |
| A-023 | MISSING_ACCRUAL_REVERSAL | SPZ_US | Aug | C3000 / 52200 | 158,231 | The auto-reversal was not generated for this accrual, so Aug utilities are double-counted. |
| A-024 | MISSING_ACCRUAL_REVERSAL | SPZ_US | Sep | C5000 / 54100 | 620,894 | The Aug accrual was not reversed, so the Sep card fees are double-counted. |
| A-025 | MISSING_ACCRUAL_REVERSAL | SPZ_FR | Sep | G1100 / 60200 | 142,600 | The accrual was not reversed when the invoice posted, so the legal fees are double-counted in Sep. |
| A-026 | CAPEX_EXPENSED | SPZ_US | Aug | C3100 / 52300 | 412,860 | A purchase of new equipment was expensed to R&M instead of being capitalized. |
| A-027 | CAPEX_EXPENSED | SPZ_CA | Jul | C5000 / 54200 | 232,814 | Hardware with a 5-year life was expensed to a technology fee account. |
| A-028 | CAPEX_EXPENSED | SPZ_FR | Sep | G1000 / 60400 | 287,500 | A construction billing for a leasehold improvement or build-out was expensed as rent instead of being capitalized (construction in progress). |
| A-029 | INTERCOMPANY_MISMATCH | SPZ_US | Aug | G9000 / 61100 | 90,000 | The partner booked its expense 90,000 higher than the 5% royalty (likely a keying or transposition error). FR income agrees to the 5% policy. |
| A-030 | INTERCOMPANY_MISMATCH | SPZ_US | Sep | G9000 / 61100 | 1,484,199 | SPZ_US did not book the Sep IC royalty expense, so R9000 has no G9000 offset. |
| A-031 | INTERCOMPANY_MISMATCH | SPZ_CA | Jul | G9000 / 61100 | 24,962 | SPZ_CA applied 4.5% instead of the 5% royalty policy rate in Jul. Aug and Sep are at 5%. |

## Proposed corrections

**A-001 · FX_TRANSLATION** — Re-translate SPZ_CA Aug and Sep P&L at 0.7265 and 0.7234 and reload. Fix the rate table in the load. Aug HFM is understated by 117,088.90 net of account direction and Sep is overstated by 40,088.97.  
Entry: `HFM SPZ_CA Aug: per account, add the GL-minus-HFM difference (e.g. Dr R1000 57,022.91 offset by the expense account differences). Sep: reverse the Sep over-translation (e.g. Cr R1000 19,143.33 and the matching expense accounts). Simplest is to reload both periods at average rates.`  
Evidence: Jul ties. Aug and Sep SPZ_CA breaks on every account; implied rates ~0.72 (Aug) and ~0.73 (Sep) match the closing rates 0.7178 and 0.7259 and not the average rates 0.7265 and 0.7234. Example: R1000 Aug GL 4,761,740.38 vs HFM 4,704,717.47 (-57,022.91); Sep GL 4,467,188.32 vs HFM 4,486,331.65 (+19,143.33). Absolute errors across 16 accounts: Aug 117,088.90 and Sep 40,088.97.

**A-002 · CUTOFF_TIMING** — Move 486,215.40 from Aug to Jul in HFM, or re-extract Jul after the late entries.  
Entry: `HFM SPZ_US Jul: Dr C1000 486,215.40 / Cr accrued liabilities 486,215.40. HFM SPZ_US Aug: Cr C1000 486,215.40.`  
Evidence: Lone Star Proteins bill iid 4854908 (LSP-874402), dated 7/31, created 8/6/2026 10:14 by d.alvarez, after the Jul extract at 8/4 6:12pm. HFM Jul C1000 is 486,215.40 low and Aug is 486,215.40 high.

**A-003 · CUTOFF_TIMING** — Move 238,750 of professional fees from Aug to Jul in HFM.  
Entry: `HFM SPZ_FR Jul: Dr G1100 238,750 / Cr accrued liabilities 238,750. HFM SPZ_FR Aug: Cr G1100 238,750.`  
Evidence: Harlow & Pierce bill iid 4854915 (FDD annual update, July), dated 7/31, created 8/7/2026 15:41 by r.kim, after the Jul extract at 8/4 6:12pm. HFM Jul G1100 is 238,750 low and Aug is 238,750 high.

**A-004 · CUTOFF_TIMING** — Move 197,333.33 of interest expense from Aug to Jul in HFM.  
Entry: `HFM SPZ_US Jul: Dr I1000 197,333.33 / Cr accrued interest 197,333.33. HFM SPZ_US Aug: Cr I1000 197,333.33.`  
Evidence: JE01590 (iid 4854920), Term Loan B SOFR reset interest true-up for Jul, dated 7/31, created 8/5/2026 09:02 by r.kim, after the Jul extract at 8/4 6:12pm. HFM Jul I1000 is 197,333.33 low and Aug is 197,333.33 high.

**A-005 · CUTOFF_TIMING** — Move 312,480.66 of commissions from Sep to Aug in HFM.  
Entry: `HFM SPZ_US Aug: Dr C1100 312,480.66 / Cr accrued liabilities 312,480.66. HFM SPZ_US Sep: Cr C1100 312,480.66.`  
Evidence: JE01593 (iid 4854922), DashCart marketplace commission true-up per August statement, dated 8/31, created 9/8/2026 11:37 by r.kim, after the Aug extract at 9/3 5:48pm. HFM Aug C1100 is 312,480.66 low and Sep is 312,480.66 high.

**A-006 · CUTOFF_TIMING** — Move 164,902.18 of royalty revenue from Sep to Aug in HFM.  
Entry: `HFM SPZ_FR Aug: Dr receivables 164,902.18 / Cr R2000 164,902.18. HFM SPZ_FR Sep: Dr R2000 164,902.18.`  
Evidence: JE01594 (iid 4854929), royalty true-up from franchisee sales audit findings (Aug), dated 8/31, created 9/9/2026 16:20 by s.whitaker, after the Aug extract at 9/3 5:48pm. HFM Aug R2000 is 164,902.18 low and Sep is 164,902.18 high.

**A-007 · CUTOFF_TIMING** — Move 655,000 of tax expense from Sep to Aug in HFM.  
Entry: `HFM SPZ_US Aug: Dr T1000 655,000 / Cr income tax payable 655,000. HFM SPZ_US Sep: Cr T1000 655,000.`  
Evidence: JE01596 (iid 4854930), Q3 tax provision true-up for Aug, dated 8/31, created 9/10/2026 14:05 by d.alvarez, after the Aug extract at 9/3 5:48pm. HFM Aug T1000 is 655,000 low and Sep is 655,000 high.

**A-008 · SIGN_FLIP** — Reload Jul R1200 for SPZ_US at -2,083,460.86.  
Entry: `HFM SPZ_US Jul: Dr R1200 4,166,921.72 (net adjustment moves R1200 from +2,083,460.86 to -2,083,460.86); offset against the reloaded balance.`  
Evidence: US Jul R1200 GL is -2,083,460.86 (discounts, natural negative) but HFM shows +2,083,460.86. The break is 4,166,921.72, which is twice the balance.

**A-009 · SIGN_FLIP** — Reload Sep R2200 at +75,000.  
Entry: `HFM SPZ_FR Sep: Cr R2200 150,000.`  
Evidence: FR Sep R2200 GL is +75,000 (INV-022313 Alamo Pizza Partners, iid 4852239) but HFM shows -75,000. The break is 150,000.

**A-010 · DUPLICATE_HFM_JOURNAL** — Reverse duplicate JNL-26-0831.  
Entry: `HFM SPZ_US Aug: Cr D1000 412,500 / Dr the balance sheet side of JNL-26-0831 (reversal of JNL-26-0831).`  
Evidence: PPA depreciation JNL-26-0812 (a.lindgren, 9/5 10:03 AM) and JNL-26-0831 (c.huang, 9/6 9:14 AM) are both 412,500 with the same support (PPA memo v2). The Aug D1000 break equals both journals, but Jul and Sep each have one.

**A-011 · DUPLICATE_HFM_JOURNAL** — Reverse duplicate JNL-26-0829.  
Entry: `HFM SPZ_US Aug: Cr C2100 96,400 / Dr workers' comp reserve 96,400 (reverse JNL-26-0829).`  
Evidence: Workers' comp reserve true-up JNL-26-0818 (a.lindgren, 9/5 4:02 PM) and JNL-26-0829 (c.huang, 9/6 9:40 AM) are both 96,400 with the same actuarial support (Actuarial rpt 2026-Q3).

**A-012 · DUPLICATE_HFM_JOURNAL** — Reverse duplicate JNL-26-0934.  
Entry: `HFM SPZ_US Sep: Dr C3000 118,340 / Cr lease liability 118,340 (reverse JNL-26-0934).`  
Evidence: ASC 842 straight-line rent adjustment JNL-26-0916 (p.mbeki, 10/6 9:52 AM) and JNL-26-0934 (c.huang, 10/7 8:47 AM) are both -118,340 with the same support (LS-SPZ-Q3). Jul and Aug have one each.

**A-013 · DUPLICATE_HFM_JOURNAL** — Reverse duplicate JNL-26-0935.  
Entry: `HFM SPZ_US Sep: Cr G1100 185,000 / Dr accrued audit fees 185,000 (reverse JNL-26-0935).`  
Evidence: Q3 statutory audit fee accrual JNL-26-0917 (p.mbeki, 10/6 10:31 AM) and JNL-26-0935 (c.huang, 10/7 9:05 AM) are both 185,000 with the same support (EL-2026-SPZ).

**A-014 · UNMAPPED_ACCOUNT** — Add 40410 to the mapping as R1000 (Flip, ICP None), get it approved, and reload Aug and Sep.  
Entry: `HFM SPZ_US Aug: Cr R1000 261,928.80. HFM SPZ_US Sep: Cr R1000 263,302.06 (offset to the load suspense).`  
Evidence: Account 40410 Catering Sales is not in the mapping. Aug 261,928.80 (126 lines) and Sep 263,302.06 (132 lines). The Aug and Sep loads rejected 2 rows and the load was forced.

**A-015 · UNMAPPED_ACCOUNT** — Map 64100 to X1000 (Transaction & Integration Costs, As is) and reload Aug and Sep.  
Entry: `HFM SPZ_US Aug: Dr X1000 1,634,620.50. HFM SPZ_US Sep: Dr X1000 356,880.25.`  
Evidence: Account 64100 Transaction Costs - M&A is not in the mapping. Aug 1,634,620.50 (2 lines) and Sep 356,880.25 (2 lines). Includes Whitfield Brennan QoE bill WB-MA-861 for 215,000.

**A-016 · MAPPING_ERROR** — Remap 40200 to R1100 and reclass Q3 US and CA balances.  
Entry: `HFM SPZ_US Q3: Dr R2000 2,375,528.76 / Cr R1100 2,375,528.76. HFM SPZ_CA Q3: Dr R2000 386,992.81 / Cr R1100 386,992.81.`  
Evidence: Account 40200 Delivery Fee Income is mapped to R2000 Franchise Royalty Revenue. It is booked only at SPZ_US (2,375,528.76) and SPZ_CA (386,992.81 at average rate), which are company-operated entities with no franchise royalties. HFM R2000 for US 2,375,529 and CA 385,965 is entirely this account. The comment is 'grouped with royalty-type revenue'. An R1100 Delivery & Service Fee Revenue account exists.

**A-017 · MAPPING_ERROR** — Remap 53200 to C4000 and reclass Q3 balances.  
Entry: `HFM SPZ_US Q3: Dr C4000 3,729,601.96 / Cr G1000 3,729,601.96. HFM SPZ_CA Q3: Dr C4000 568,849.90 / Cr G1000 568,849.90.`  
Evidence: Account 53200 National Advertising Fund Contribution is mapped to G1000 G&A ('treated as overhead'). It is a 4% sales-based advertising contribution by the company-operated entities: SPZ_US 3,729,601.96 (JE01405, JE01408, JE01411) and SPZ_CA 568,849.90. HFM has C4000 Advertising.

**A-018 · DUPLICATE_GL_ENTRY** — Void BILL-066239 (iid 4904951) in NetSuite and reverse in HFM.  
Entry: `NetSuite Sep: Dr AP 152,356.54 / Cr 50100 152,356.54. HFM SPZ_US Sep: Cr C1000 152,356.54.`  
Evidence: Valley Dairy Cheese bill VDC-115295, 152,356.54, Texas North w/e 09/27: original iid 4833187 (BILL-058928, created 9/30 by j.chen) and duplicate iid 4904951 (BILL-066239, created 10/5 16:02 by t.nguyen). The ref, amount, memo and location are identical.

**A-019 · DUPLICATE_GL_ENTRY** — Void iid 4904952 and reverse in HFM.  
Entry: `NetSuite Jul: Dr AP 36,556.03 / Cr 60200 36,556.03. HFM SPZ_US Jul: Cr G1100 36,556.03.`  
Evidence: Whitfield Brennan bill WB-2026-6530 for 36,556.03 (iid 4854678, created 7/30 by j.chen) and WB2026-6530 (iid 4904952, BILL-072121, created 8/4 by t.nguyen). Same date 7/29, amount and memo; the ref differs only in the hyphen.

**A-020 · DUPLICATE_GL_ENTRY** — Void iid 4904953 and reverse in HFM at the Jul average rate 0.7312.  
Entry: `NetSuite Jul: Dr AP CAD 41,200.09 / Cr 50110 CAD 41,200.09. HFM SPZ_CA Jul: Cr C1000 30,125.51.`  
Evidence: Maple Leaf Foodservice bill MLF-237630, CAD 41,200.09 (USD 30,125.51), Ontario West w/e 07/05: original iid 4833359 (created 7/7 by e.tremblay) and duplicate iid 4904953 (BILL-066316, created 7/16 by l.gagnon). The ref is identical.

**A-021 · DUPLICATE_GL_ENTRY** — Void iid 4904954 and reverse in HFM.  
Entry: `NetSuite Aug: Dr AP 38,000 / Cr 60400 38,000. HFM SPZ_FR Aug: Cr G1000 38,000.`  
Evidence: Preston Ridge HQ rent for Aug at SPZ_FR: PROP-FR-2608 (iid 4854250, 38,000, created 8/2) and PROP-FR-2608A (iid 4904954, BILL-072111, created 8/13 by t.nguyen). Same date 8/1, amount and memo. Rent is billed once per month; Jul and Sep have one bill each.

**A-022 · DUPLICATE_GL_ENTRY** — Void iid 4904955 and reverse in HFM.  
Entry: `NetSuite Aug: Dr AP 58,968 / Cr 54200 58,968. HFM SPZ_US Aug: Cr C5000 58,968.`  
Evidence: OrderLoop POS subscription for Aug: OL-US-2608 (iid 4847560, 58,968, created 8/3) and OLUS-2608 (iid 4904955, BILL-071843, created 8/7 by j.chen). Same date 8/3, amount and memo. The subscription is billed once per month.

**A-023 · MISSING_ACCRUAL_REVERSAL** — Post the missing reversal dated 8/1 in NetSuite.  
Entry: `NetSuite Aug: Dr AP/accrued liabilities 158,231.14 / Cr 52200 158,231.14 (Texas North). HFM SPZ_US Aug: Cr C3000 158,231.14.`  
Evidence: Jul 31 accrual iid 4836008 'ACCR - Jul utilities unbilled - Texas North', 158,231.14, has no REV on 8/1. Every other Jul accrual was reversed (e.g. Aug 1 reversals iid 4839587, 4840045).

**A-024 · MISSING_ACCRUAL_REVERSAL** — Post the reversal dated 9/1.  
Entry: `NetSuite Sep: Dr accrued liabilities 620,894.48 / Cr 54100 620,894.48. HFM SPZ_US Sep: Cr C5000 620,894.48.`  
Evidence: Aug 31 accrual iid 4848149 (JE01427) 'ACCR - Aug card processing fees', 620,894.48, was not reversed on 9/1. The earlier month reversals (iid 4848133 and 4848140) posted.

**A-025 · MISSING_ACCRUAL_REVERSAL** — Post the reversal dated 9/1.  
Entry: `NetSuite Sep: Dr accrued liabilities 142,600 / Cr 60200 142,600. HFM SPZ_FR Sep: Cr G1100 142,600.`  
Evidence: Aug 31 accrual iid 4854824 (JE01565) 'ACCR - Aug legal fees unbilled - Harlow & Pierce', 142,600, was not reversed on 9/1. The actual invoice iid 4854840 (139,850, 'Franchise legal services - Aug') was expensed on 9/18.

**A-026 · CAPEX_EXPENSED** — Capitalize to PP&E and start depreciation from in-service date.  
Entry: `NetSuite Aug: Dr PP&E - restaurant equipment 412,860 / Cr 52300 412,860. HFM SPZ_US Aug: Cr C3100 412,860. Then record depreciation over the useful life.`  
Evidence: Mid-South Oven Co. bill iid 4914959, 412,860, 8/18: 'Oven replacement program - 14 new conveyor ovens, purchase & install', created 8/19 by j.chen. Booked to Repairs & Maintenance 52300 (typical line ~1,320).

**A-027 · CAPEX_EXPENSED** — Capitalize and depreciate over 5 years.  
Entry: `NetSuite Jul: Dr PP&E - POS equipment CAD 318,400 / Cr 54200 CAD 318,400. HFM SPZ_CA Jul: Cr C5000 232,814.08. Then record depreciation from the in-service date.`  
Evidence: OrderLoop POS bill iid 4914960, CAD 318,400 (USD 232,814.08 at 0.7312), 7/22: 'POS terminal hardware - 64 restaurants (new terminals, 5-yr life)', created 7/23 by e.tremblay. Booked to Technology & POS Fees 54200 (typical line ~8,816).

**A-028 · CAPEX_EXPENSED** — Capitalize to construction in progress or leasehold improvements. Also review progress billing #1.  
Entry: `NetSuite Sep: Dr CIP - training center 287,500 / Cr 60400 287,500. HFM SPZ_FR Sep: Cr G1000 287,500.`  
Evidence: Crestview Build Group bill iid 4914961 (CBG-2026-114), 287,500, 9/14: 'Franchise training center build-out - progress billing #2', created 9/15 by j.chen. Booked to Corporate Rent 60400 (typical line 38,000).

**A-029 · INTERCOMPANY_MISMATCH** — Correct JE01571 to 1,565,535.00.  
Entry: `NetSuite SPZ_US Aug: Dr IC payable to SPZ_FR 90,000 / Cr 61100 90,000. HFM SPZ_US Aug: Cr G9000 90,000.`  
Evidence: SPZ_US Aug IC royalty expense JE01571 (iid 4854865) is 1,655,535.00. SPZ_FR income JE01573 is 1,565,535.00, which is 5% of US company sales 31,310,699.98. The difference is 90,000.

**A-030 · INTERCOMPANY_MISMATCH** — Book the Sep IC royalty expense at SPZ_US, ICP SPZ_FR.  
Entry: `NetSuite SPZ_US Sep: Dr 61100 1,484,199.23 / Cr IC payable to SPZ_FR 1,484,199.23. HFM SPZ_US Sep: Dr G9000 1,484,199.23 (ICP SPZ_FR).`  
Evidence: SPZ_FR booked Sep IC royalty income JE01576 (iid 4854872) of 1,484,199.23 (5% of US sales). SPZ_US has no 61100 entry for Sep (Jul JE01567 and Aug JE01571 exist). HFM G9000 for US Sep is 0.

**A-031 · INTERCOMPANY_MISMATCH** — Correct JE01578 to CAD 341,378.49 (5%).  
Entry: `NetSuite SPZ_CA Jul: Dr 61100 CAD 34,137.85 / Cr IC payable CAD 34,137.85. HFM SPZ_CA Jul: Dr G9000 24,961.59 (ICP SPZ_FR).`  
Evidence: SPZ_CA Jul IC royalty expense JE01578 (iid 4854874) is CAD 307,240.64 (USD 224,654.36), which is 4.5% of company sales. SPZ_FR income JE01579 is 249,615.95, which is 5% of sales of 4,992,319.15. The difference is 24,961.59.

---
Model `claude-sonnet-5-5` · 7 turns · 26 tool calls · 125s · tokens in 16 (cache read 158,182, cache write 52,639) / out 20,277
