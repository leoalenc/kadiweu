# Sentence-status comparison: C → D

Sentences are matched by `(dataset, sentence_uid)`. Rows with missing or duplicate identities are excluded and reported as integrity issues.

## Headline results

| Measure | Count |
|---|---:|
| Shared sentences | 206 |
| REVIEW → DONE (improvements) | 13 |
| DONE → REVIEW (regressions) | 0 |
| Net progress among shared sentences | +13 |
| Added sentences | 0 |
| Removed sentences | 0 |
| Other status changes | 0 |
| Integrity issues | 0 |

## DONE accounting

| Measure | State A | State B | Change |
|---|---:|---:|---:|
| DONE sentences (all present rows) | 170/206 | 183/206 | +13 |
| DONE among shared sentences | 170/206 | 183/206 | +13 |
| DONE rate among shared sentences | 82.52% | 88.83% | +6.31 pp |

Added DONE sentences: **0**. Removed DONE sentences: **0**.

## Results by dataset

| Dataset | Shared | Improvements | Regressions | Net progress | Added | Removed |
|---|---:|---:|---:|---:|---:|---:|
| hil-data | 70 | 1 | 0 | +1 | 0 | 0 |
| ped-gramm | 61 | 3 | 0 | +3 | 0 | 0 |
| van-data | 75 | 9 | 0 | +9 | 0 | 0 |

## Improved sentences

- `hil-data`, `9527d53d-7184-4b08-8bb2-51b7fff1429d`: `REVIEW` → `DONE`
- `ped-gramm`, `2f47b402-9fe7-4714-96e3-c6cbdf405472`: `REVIEW` → `DONE`
- `ped-gramm`, `3f077b37-aa95-4012-9efb-a21630cdd6e9`: `REVIEW` → `DONE`
- `ped-gramm`, `ef4d298a-643b-4c08-9bdd-f7c6b63ac9ec`: `REVIEW` → `DONE`
- `van-data`, `39925f76-d73f-423f-95cd-f88bd78f2a6e`: `REVIEW` → `DONE`
- `van-data`, `813f2ad7-42fb-4fbd-84b4-1957c68aa4f9`: `REVIEW` → `DONE`
- `van-data`, `969ba2f3-88dc-417e-ad3f-16ce88b4c762`: `REVIEW` → `DONE`
- `van-data`, `a1e15803-1e5e-481f-8137-a84beac6cbcc`: `REVIEW` → `DONE`
- `van-data`, `a2910ce3-a0d2-4eac-bcc3-2da15db88b90`: `REVIEW` → `DONE`
- `van-data`, `b97e5b2f-d0da-4238-8ee6-2c64ded91f76`: `REVIEW` → `DONE`
- `van-data`, `c1b350df-ed1a-4e3b-89a8-a6fa9ca8382e`: `REVIEW` → `DONE`
- `van-data`, `d3095a7e-477d-405e-9ea2-85bfdacad7d3`: `REVIEW` → `DONE`
- `van-data`, `fbae0277-3aad-4812-9229-94179b5a97a0`: `REVIEW` → `DONE`

## Regressed sentences

- None.

## Sources

- **C:** `../data/reports/status/C/sentence_status_individual.tsv`
- **D:** `../data/reports/status/D/sentence_status_individual.tsv`
