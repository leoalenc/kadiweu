# Sentence-status comparison: E → F

Sentences are matched by `(dataset, sentence_uid)`. Rows with missing or duplicate identities are excluded and reported as integrity issues.

## Headline results

| Measure | Count |
|---|---:|
| Shared sentences | 206 |
| REVIEW → DONE (improvements) | 1 |
| DONE → REVIEW (regressions) | 0 |
| Net progress among shared sentences | +1 |
| Added sentences | 0 |
| Removed sentences | 0 |
| Other status changes | 0 |
| Integrity issues | 0 |

## DONE accounting

| Measure | State A | State B | Change |
|---|---:|---:|---:|
| DONE sentences (all present rows) | 188/206 | 189/206 | +1 |
| DONE among shared sentences | 188/206 | 189/206 | +1 |
| DONE rate among shared sentences | 91.26% | 91.75% | +0.49 pp |

Added DONE sentences: **0**. Removed DONE sentences: **0**.

## Results by dataset

| Dataset | Shared | Improvements | Regressions | Net progress | Added | Removed |
|---|---:|---:|---:|---:|---:|---:|
| hil-data | 70 | 1 | 0 | +1 | 0 | 0 |
| ped-gramm | 61 | 0 | 0 | +0 | 0 | 0 |
| van-data | 75 | 0 | 0 | +0 | 0 | 0 |

## Improved sentences

- `hil-data`, `79cb0e55-9c06-4cb1-91b3-2b5233e1678f`: `REVIEW` → `DONE`

## Regressed sentences

- None.

## Sources

- **E:** `data/reports/status/E/sentence_status_individual.tsv`
- **F:** `data/reports/status/F/sentence_status_individual.tsv`
