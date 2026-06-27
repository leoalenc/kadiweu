# CoNLL-U draft accuracy against gold

Only sentences with matching `sent_uid` are considered. Token-level accuracy is computed only for matched sentences with the same number of syntactic tokens and the same integer token IDs.

| draft_file | matched_sents | comparable_sents | token_count_mismatch_sents | token_id_mismatch_sents | scored_tokens | FORM | LEMMA | UPOS | XPOS | FEATS | UAS | DEPREL | LAS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-all.conllu | 103 | 100 | 3 | 0 | 447 | 98.21 | 97.54 | 96.20 | 96.87 | 95.53 | 83.22 | 78.08 | 74.05 |

## Token-count / token-ID mismatches

| draft_file | sent_uid | gold_sent_id | draft_sent_id | reason | gold_n | draft_n | gold_forms | draft_forms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-all.conllu | `ee1a1190-7803-404c-83f6-49d3ccf63b0d` | `ped-gramm-28` | `gramatica-pedagogica-28` | token_count_mismatch | 8 | 9 | `eyodi dowediteloco naodigijedi micoataGa daGa me lionigipi .` | `Eyodi dowediteloco naodigijedi me icawataGa daGa me lionigipi .` |
| draft-all.conllu | `e349508c-4d86-48b8-9918-057988755e77` | `hil-data-5` | `hil-data-5` | token_count_mismatch | 7 | 6 | `Etogo ane iwaGadi aG dakake lojedi .` | `Etogo ane iwaGadi adakake lojedi .` |
| draft-all.conllu | `1d10c633-e74d-4e27-ac23-6b6b2dde9647` | `hil-data-6` | `hil-data-6` | token_count_mismatch | 7 | 6 | `Etogo ane iwaGadi aG dakake loojedi .` | `Etogo ane iwaGadi adakake loojedi .` |

## Notes

- `UAS` is `HEAD` accuracy.
- `LAS` requires both `HEAD` and `DEPREL` to match.
- `FEATS` are compared after alphabetic normalization of feature order.
- MWT range rows and empty nodes are ignored in token counts and scoring.
- Non-comparable matched sentences are excluded from the accuracy denominators.
