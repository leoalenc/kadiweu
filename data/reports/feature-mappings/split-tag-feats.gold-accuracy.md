# CoNLL-U draft accuracy against gold

Only sentences with matching `sent_uid` are considered. Token-level accuracy is computed only for matched sentences with the same number of syntactic tokens and the same integer token IDs.

| draft_file | matched_sents | comparable_sents | token_count_mismatch_sents | token_id_mismatch_sents | scored_tokens | FORM | LEMMA | UPOS | XPOS | FEATS | UAS | DEPREL | LAS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-ped-gramm.before.conllu | 50 | 49 | 1 | 0 | 231 | 99.13 | 97.40 | 97.84 | 96.97 | 93.51 | 89.61 | 87.88 | 86.58 |
| draft-hil.before.conllu | 34 | 32 | 2 | 0 | 127 | 97.64 | 95.28 | 92.13 | 95.28 | 96.85 | 83.46 | 74.02 | 70.08 |
| draft-van.before.conllu | 33 | 32 | 1 | 0 | 153 | 98.04 | 98.04 | 98.69 | 98.04 | 96.08 | 77.12 | 74.51 | 67.97 |
| draft-ped-gramm.after.conllu | 50 | 49 | 1 | 0 | 231 | 99.13 | 97.40 | 97.84 | 96.97 | 93.51 | 89.61 | 87.88 | 86.58 |
| draft-hil.after.conllu | 34 | 32 | 2 | 0 | 127 | 97.64 | 95.28 | 92.13 | 95.28 | 96.85 | 83.46 | 74.02 | 70.08 |
| draft-van.after.conllu | 33 | 32 | 1 | 0 | 153 | 98.04 | 98.04 | 98.69 | 98.04 | 96.08 | 77.12 | 74.51 | 67.97 |

## Token-count / token-ID mismatches

| draft_file | sent_uid | gold_sent_id | draft_sent_id | reason | gold_n | draft_n | gold_forms | draft_forms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-ped-gramm.before.conllu | `ee1a1190-7803-404c-83f6-49d3ccf63b0d` | `ped-gramm-28` | `ped-gramm-28` | token_count_mismatch | 8 | 9 | `eyodi dowediteloco naodigijedi micoataGa daGa me lionigipi .` | `Eyodi dowediteloco naodigijedi me icawataGa daGa me lionigipi .` |
| draft-hil.before.conllu | `e349508c-4d86-48b8-9918-057988755e77` | `hil-data-5` | `hil-data-5` | token_count_mismatch | 7 | 6 | `Etogo ane iwaGadi aG dakake lojedi .` | `Etogo ane iwaGadi adakake lojedi .` |
| draft-hil.before.conllu | `1d10c633-e74d-4e27-ac23-6b6b2dde9647` | `hil-data-6` | `hil-data-6` | token_count_mismatch | 7 | 6 | `Etogo ane iwaGadi aG dakake loojedi .` | `Etogo ane iwaGadi adakake loojedi .` |
| draft-van.before.conllu | `4c41fdf6-0c48-4eb6-91f7-121c21f3e2a7` | `van-data-15` | `van-data-15` | token_count_mismatch | 5 | 8 | `niGijo niganigawaanigi lomigo niwatece .` | `Ijo nigaanigawaanigi idei me adi lomiigo niwatece .` |
| draft-ped-gramm.after.conllu | `ee1a1190-7803-404c-83f6-49d3ccf63b0d` | `ped-gramm-28` | `ped-gramm-28` | token_count_mismatch | 8 | 9 | `eyodi dowediteloco naodigijedi micoataGa daGa me lionigipi .` | `Eyodi dowediteloco naodigijedi me icawataGa daGa me lionigipi .` |
| draft-hil.after.conllu | `e349508c-4d86-48b8-9918-057988755e77` | `hil-data-5` | `hil-data-5` | token_count_mismatch | 7 | 6 | `Etogo ane iwaGadi aG dakake lojedi .` | `Etogo ane iwaGadi adakake lojedi .` |
| draft-hil.after.conllu | `1d10c633-e74d-4e27-ac23-6b6b2dde9647` | `hil-data-6` | `hil-data-6` | token_count_mismatch | 7 | 6 | `Etogo ane iwaGadi aG dakake loojedi .` | `Etogo ane iwaGadi adakake loojedi .` |
| draft-van.after.conllu | `4c41fdf6-0c48-4eb6-91f7-121c21f3e2a7` | `van-data-15` | `van-data-15` | token_count_mismatch | 5 | 8 | `niGijo niganigawaanigi lomigo niwatece .` | `Ijo nigaanigawaanigi idei me adi lomiigo niwatece .` |

## Notes

- `UAS` is `HEAD` accuracy.
- `LAS` requires both `HEAD` and `DEPREL` to match.
- `FEATS` are compared after alphabetic normalization of feature order.
- MWT range rows and empty nodes are ignored in token counts and scoring.
- Non-comparable matched sentences are excluded from the accuracy denominators.
