# Scorecard - Rules-based tie-out (baseline)

Benchmark: Sparrow Pizza -> Larkspur Restaurant Group, FY26 Q3 (SYNTHETIC)  
Findings file: `baseline_findings.csv` (58 rows)

| Metric | Result |
|---|---|
| Issues detected | **16 / 33** (48%) |
| Root cause classified correctly | **2 / 33** (6%) |
| Dollar impact surfaced | $9,857,753 of $21,685,442 (45%) |
| Precision (findings tied to a real issue) | 54 / 58 (93%) |
| False positives | 4 |
| Findings with amount within 5% | 50 / 54 |

| Issue type | Seeded | Detected | Classified |
|---|---:|---:|---:|
| CAPEX_EXPENSED | 3 | 0 | 0 |
| CUTOFF_TIMING | 6 | 6 | 0 |
| DUPLICATE_GL_ENTRY | 5 | 0 | 0 |
| DUPLICATE_HFM_JOURNAL | 4 | 4 | 0 |
| FX_TRANSLATION | 2 | 2 | 0 |
| INTERCOMPANY_MISMATCH | 3 | 0 | 0 |
| MAPPING_ERROR | 3 | 0 | 0 |
| MISSING_ACCRUAL_REVERSAL | 3 | 0 | 0 |
| SIGN_FLIP | 2 | 2 | 0 |
| UNMAPPED_ACCOUNT | 2 | 2 | 2 |

**Missed:** SI-01, SI-02, SI-03, SI-20, SI-21, SI-22, SI-23, SI-24, SI-25, SI-26, SI-27, SI-28, SI-29, SI-30, SI-31, SI-32, SI-33
**False positives:** B-045, B-050, B-051, B-056
