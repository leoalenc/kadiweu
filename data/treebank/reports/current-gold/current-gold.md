# CoNLL-U draft accuracy against gold

Only sentences with matching `sent_uid` are considered. Token-level accuracy is computed only for matched sentences with the same number of syntactic tokens and the same integer token IDs.

| draft_file | matched_sents | comparable_sents | token_count_mismatch_sents | token_id_mismatch_sents | scored_tokens | FORM | LEMMA | UPOS | XPOS | FEATS | UAS | DEPREL | LAS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-all.conllu | 199 | 198 | 1 | 0 | 909 | 99.34 | 96.59 | 98.68 | 98.57 | 88.12 | 97.14 | 96.70 | 95.71 |

## Token-count / token-ID mismatches

| draft_file | sent_uid | gold_sent_id | draft_sent_id | reason | gold_n | draft_n | gold_forms | draft_forms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-all.conllu | `ee1a1190-7803-404c-83f6-49d3ccf63b0d` | `ped-gramm-28` | `ped-gramm-28` | token_count_mismatch | 8 | 9 | `eyodi dowediteloco naodigijedi micoataGa daGa me lionigipi .` | `Eyodi dowediteloco nawodigijedi me icawataGa daGa me lionigipi .` |

## Notes

- `UAS` is `HEAD` accuracy.
- `LAS` requires both `HEAD` and `DEPREL` to match.
- `FEATS` are compared after alphabetic normalization of feature order.
- MWT range rows and empty nodes are ignored in token counts and scoring.
- Non-comparable matched sentences are excluded from the accuracy denominators.
