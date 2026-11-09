# Scorecard - Agent (claude-sonnet-5-5)

Benchmark: Sparrow Pizza -> Larkspur Restaurant Group, FY26 Q3 (SYNTHETIC)  
Findings file: `agent_findings.csv` (31 rows)

| Metric | Result |
|---|---|
| Issues detected | **31 / 33** (94%) |
| Root cause classified correctly | **31 / 33** (94%) |
| Dollar impact surfaced | $20,648,704 of $21,685,442 (95%) |
| Precision (findings tied to a real issue) | 31 / 31 (100%) |
| False positives | 0 |
| Findings with amount within 5% | 30 / 31 |

| Issue type | Seeded | Detected | Classified |
|---|---:|---:|---:|
| CAPEX_EXPENSED | 3 | 3 | 3 |
| CUTOFF_TIMING | 6 | 6 | 6 |
| DUPLICATE_GL_ENTRY | 5 | 5 | 5 |
| DUPLICATE_HFM_JOURNAL | 4 | 4 | 4 |
| FX_TRANSLATION | 2 | 1 | 1 |
| INTERCOMPANY_MISMATCH | 3 | 3 | 3 |
| MAPPING_ERROR | 3 | 2 | 2 |
| MISSING_ACCRUAL_REVERSAL | 3 | 3 | 3 |
| SIGN_FLIP | 2 | 2 | 2 |
| UNMAPPED_ACCOUNT | 2 | 2 | 2 |

**Missed:** SI-03, SI-13
