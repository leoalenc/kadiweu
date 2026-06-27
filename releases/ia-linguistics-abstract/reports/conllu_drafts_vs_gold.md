# CoNLL-U draft accuracy against gold

Only sentences with matching `sent_uid` are considered. Token-level accuracy is computed only for matched sentences with the same number of syntactic tokens and the same integer token IDs.

| draft_file | matched_sents | comparable_sents | token_count_mismatch_sents | token_id_mismatch_sents | scored_tokens | FORM | LEMMA | UPOS | XPOS | FEATS | UAS | DEPREL | LAS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-ped-gramm.conllu | 37 | 36 | 1 | 0 | 169 | 98.82 | 98.82 | 97.04 | 95.86 | 94.67 | 86.98 | 83.43 | 81.66 |
| draft-hil.conllu | 34 | 32 | 2 | 0 | 127 | 97.64 | 96.06 | 92.13 | 96.85 | 95.28 | 84.25 | 74.80 | 70.87 |
| draft-van.conllu | 32 | 32 | 0 | 0 | 151 | 98.01 | 97.35 | 98.68 | 98.01 | 96.69 | 78.15 | 74.83 | 68.21 |

## Token-count / token-ID mismatches

| draft_file | sent_uid | gold_sent_id | draft_sent_id | reason | gold_n | draft_n | gold_forms | draft_forms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-ped-gramm.conllu | `ee1a1190-7803-404c-83f6-49d3ccf63b0d` | `ped-gramm-28` | `gramatica-pedagogica-28` | token_count_mismatch | 8 | 9 | `eyodi dowediteloco naodigijedi micoataGa daGa me lionigipi .` | `Eyodi dowediteloco naodigijedi me icawataGa daGa me lionigipi .` |
| draft-hil.conllu | `e349508c-4d86-48b8-9918-057988755e77` | `hil-data-5` | `hil-data-5` | token_count_mismatch | 7 | 6 | `Etogo ane iwaGadi aG dakake lojedi .` | `Etogo ane iwaGadi adakake lojedi .` |
| draft-hil.conllu | `1d10c633-e74d-4e27-ac23-6b6b2dde9647` | `hil-data-6` | `hil-data-6` | token_count_mismatch | 7 | 6 | `Etogo ane iwaGadi aG dakake loojedi .` | `Etogo ane iwaGadi adakake loojedi .` |

## Notes

- `UAS` is `HEAD` accuracy.
- `LAS` requires both `HEAD` and `DEPREL` to match.
- `FEATS` are compared after alphabetic normalization of feature order.
- MWT range rows and empty nodes are ignored in token counts and scoring.
- Non-comparable matched sentences are excluded from the accuracy denominators.
