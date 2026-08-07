# Sentence-status comparison: A → B

Sentences are matched by `(dataset, sentence_uid)`. Rows with missing or duplicate identities are excluded and reported as integrity issues.

## Headline results

| Measure | Count |
|---|---:|
| Shared sentences | 206 |
| REVIEW → DONE (improvements) | 16 |
| DONE → REVIEW (regressions) | 0 |
| Net progress among shared sentences | +16 |
| Added sentences | 0 |
| Removed sentences | 0 |
| Other status changes | 0 |
| Integrity issues | 0 |

## DONE accounting

| Measure | State A | State B | Change |
|---|---:|---:|---:|
| DONE sentences (all present rows) | 146/206 | 162/206 | +16 |
| DONE among shared sentences | 146/206 | 162/206 | +16 |
| DONE rate among shared sentences | 70.87% | 78.64% | +7.77 pp |

Added DONE sentences: **0**. Removed DONE sentences: **0**.

## Results by dataset

| Dataset | Shared | Improvements | Regressions | Net progress | Added | Removed |
|---|---:|---:|---:|---:|---:|---:|
| hil-data | 70 | 6 | 0 | +6 | 0 | 0 |
| ped-gramm | 61 | 6 | 0 | +6 | 0 | 0 |
| van-data | 75 | 4 | 0 | +4 | 0 | 0 |

## Improved sentences

- `hil-data`, `0ca977cd-2edf-45d9-b958-068648aebef9`: `REVIEW` → `DONE`
- `hil-data`, `1d10c633-e74d-4e27-ac23-6b6b2dde9647`: `REVIEW` → `DONE`
- `hil-data`, `39f34955-a828-47d7-808d-b3b3565b42d6`: `REVIEW` → `DONE`
- `hil-data`, `435e4b10-ab78-4ee3-84b0-7773dbe10bf7`: `REVIEW` → `DONE`
- `hil-data`, `92838eda-ef9b-4f05-a5eb-38a4709c0337`: `REVIEW` → `DONE`
- `hil-data`, `d3ae6cfd-bec1-49f3-a0f9-4ca0744e3404`: `REVIEW` → `DONE`
- `ped-gramm`, `19401990-aa1d-4cf5-bea1-122254c6b77a`: `REVIEW` → `DONE`
- `ped-gramm`, `2c0248b3-8f68-46e9-b41c-9f7807572c87`: `REVIEW` → `DONE`
- `ped-gramm`, `46bbf9a8-c650-4e4b-a44f-78bfe6c5d979`: `REVIEW` → `DONE`
- `ped-gramm`, `582429f2-67d5-4077-b209-6deb7b5df54f`: `REVIEW` → `DONE`
- `ped-gramm`, `8b1a9983-4dfd-49e8-9285-92c56c84b652`: `REVIEW` → `DONE`
- `ped-gramm`, `eeb42af3-fe5a-4b7d-97ea-b381ab589860`: `REVIEW` → `DONE`
- `van-data`, `3e518fdb-d852-41e5-87a4-f8778597c2a1`: `REVIEW` → `DONE`
- `van-data`, `81048a6f-e084-4b0a-965a-f41fb5c53ff7`: `REVIEW` → `DONE`
- `van-data`, `ebff5ffa-8a9d-4f8b-9960-38f70b344c19`: `REVIEW` → `DONE`
- `van-data`, `ee540050-e6fa-424e-9252-fd0b9312769d`: `REVIEW` → `DONE`

## Regressed sentences

- None.

## Sources

- **A:** `../data/reports/status/A/sentence_status_individual.tsv`
- **B:** `../data/reports/status/B/sentence_status_individual.tsv`
