# Sentence-status comparison: B → C

Sentences are matched by `(dataset, sentence_uid)`. Rows with missing or duplicate identities are excluded and reported as integrity issues.

## Headline results

| Measure | Count |
|---|---:|
| Shared sentences | 206 |
| REVIEW → DONE (improvements) | 8 |
| DONE → REVIEW (regressions) | 0 |
| Net progress among shared sentences | +8 |
| Added sentences | 0 |
| Removed sentences | 0 |
| Other status changes | 0 |
| Integrity issues | 0 |

## DONE accounting

| Measure | State A | State B | Change |
|---|---:|---:|---:|
| DONE sentences (all present rows) | 162/206 | 170/206 | +8 |
| DONE among shared sentences | 162/206 | 170/206 | +8 |
| DONE rate among shared sentences | 78.64% | 82.52% | +3.88 pp |

Added DONE sentences: **0**. Removed DONE sentences: **0**.

## Results by dataset

| Dataset | Shared | Improvements | Regressions | Net progress | Added | Removed |
|---|---:|---:|---:|---:|---:|---:|
| hil-data | 70 | 2 | 0 | +2 | 0 | 0 |
| ped-gramm | 61 | 3 | 0 | +3 | 0 | 0 |
| van-data | 75 | 3 | 0 | +3 | 0 | 0 |

## Improved sentences

- `hil-data`, `64f2c803-b436-4202-b4c7-acf5c7205bc3`: `REVIEW` → `DONE`
- `hil-data`, `a74fea0a-dd87-4c4d-8670-9db66f5b5b16`: `REVIEW` → `DONE`
- `ped-gramm`, `10e550d6-df13-4527-8aee-aa23e3f2fcdd`: `REVIEW` → `DONE`
- `ped-gramm`, `881131dd-3f70-411a-ac7e-85557139d1e3`: `REVIEW` → `DONE`
- `ped-gramm`, `95a7d135-4be0-463d-b443-76cc5828fc89`: `REVIEW` → `DONE`
- `van-data`, `0c38eab8-c6b0-4f02-bf05-27ea6285fe70`: `REVIEW` → `DONE`
- `van-data`, `0c7e64fb-f070-4faa-a12a-c110cdf4bf16`: `REVIEW` → `DONE`
- `van-data`, `a7e338a1-5403-40d4-b169-c840cf193aae`: `REVIEW` → `DONE`

## Regressed sentences

- None.

## Sources

- **B:** `../data/reports/status/B/sentence_status_individual.tsv`
- **C:** `../data/reports/status/C/sentence_status_individual.tsv`
