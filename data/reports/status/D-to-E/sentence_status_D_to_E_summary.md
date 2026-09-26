# Sentence-status comparison: D → E

Sentences are matched by `(dataset, sentence_uid)`. Rows with missing or duplicate identities are excluded and reported as integrity issues.

## Headline results

| Measure | Count |
|---|---:|
| Shared sentences | 206 |
| REVIEW → DONE (improvements) | 6 |
| DONE → REVIEW (regressions) | 0 |
| Net progress among shared sentences | +6 |
| Added sentences | 0 |
| Removed sentences | 0 |
| Other status changes | 0 |
| Integrity issues | 0 |

## DONE accounting

| Measure | State A | State B | Change |
|---|---:|---:|---:|
| DONE sentences (all present rows) | 183/206 | 189/206 | +6 |
| DONE among shared sentences | 183/206 | 189/206 | +6 |
| DONE rate among shared sentences | 88.83% | 91.75% | +2.91 pp |

Added DONE sentences: **0**. Removed DONE sentences: **0**.

## Results by dataset

| Dataset | Shared | Improvements | Regressions | Net progress | Added | Removed |
|---|---:|---:|---:|---:|---:|---:|
| hil-data | 70 | 1 | 0 | +1 | 0 | 0 |
| ped-gramm | 61 | 5 | 0 | +5 | 0 | 0 |
| van-data | 75 | 0 | 0 | +0 | 0 | 0 |

## Improved sentences

- `hil-data`, `79cb0e55-9c06-4cb1-91b3-2b5233e1678f`: `REVIEW` → `DONE`
- `ped-gramm`, `12147353-b422-4ad7-9bef-1d20e70e2a74`: `REVIEW` → `DONE`
- `ped-gramm`, `6d2a809e-0d32-4254-9489-f9e356e22493`: `REVIEW` → `DONE`
- `ped-gramm`, `7b806584-75e5-4017-b9e2-ba97458903bd`: `REVIEW` → `DONE`
- `ped-gramm`, `f081c545-c42b-463d-b57f-db87787f20e7`: `REVIEW` → `DONE`
- `ped-gramm`, `fef391af-9e63-419f-8f81-057459193f49`: `REVIEW` → `DONE`

## Regressed sentences

- None.

## Sources

- **D:** `data/reports/status/D/sentence_status_individual.tsv`
- **E:** `data/reports/status/E/sentence_status_individual.tsv`
