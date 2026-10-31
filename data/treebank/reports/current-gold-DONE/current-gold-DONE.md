# CoNLL-U draft accuracy against DONE gold sentences

Only sentences with matching `sent_uid` are considered. Token-level accuracy is computed only for matched sentences with the same number of syntactic tokens and the same integer token IDs.

| draft_file | matched_sents | comparable_sents | token_count_mismatch_sents | token_id_mismatch_sents | scored_tokens | FORM | LEMMA | UPOS | XPOS | FEATS | UAS | DEPREL | LAS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| draft-all.current.conllu | 188 | 188 | 0 | 0 | 856 | 99.42 | 96.61 | 98.60 | 98.60 | 87.73 | 99.53 | 98.83 | 98.60 |

## Token-count / token-ID mismatches

No token-count or token-ID mismatches were found in matched sentences.

## Notes

- `UAS` is `HEAD` accuracy.
- `LAS` requires both `HEAD` and `DEPREL` to match.
- `FEATS` are compared after alphabetic normalization of feature order.
- MWT range rows and empty nodes are ignored in token counts and scoring.
- Non-comparable matched sentences are excluded from the accuracy denominators.

## DONE-sentence inventory and coverage

- Gold sentences read: 198
- JSON DONE sentences: 189
  - `ped-gramm.json`: 54
  - `hil-data.json`: 66
  - `van-data.json`: 69
- JSON DONE UIDs present in gold: 188
- JSON DONE UIDs absent from gold: 1
- DONE sentences absent from gold: `79cb0e55-9c06-4cb1-91b3-2b5233e1678f` (hil-data.json)

### `draft-all.current.conllu`

- Draft sentences read: 206
- Draft UIDs matched to DONE gold: 188
- Draft UIDs outside the DONE gold inventory (excluded): 18
- DONE gold UIDs missing from the draft: 0

DONE status is taken from the current TBP JSON sentence records, not from optional `ud_review_status` comments in CoNLL-U. JSON DONE sentences are intersected with the gold inventory by `sent_uid`; only that intersection enters the scores.
