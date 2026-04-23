# Gold-derived overrides report

## Summary

- Gold sentences: **37**
- JSON sentences: **37**
- Aligned sentence pairs: **36**
- `lemma_overrides`: **28**
- `form_feat_overrides`: **26**
- `prontype_overrides`: **5**
- `tag_to_default_prontype`: **1**

## Review items

### json_alignment_issues (8)
- `{"mismatches": [["aG", "aG@"], ["ipegetege", "@ipegetege"]], "sent_id": "ped-gramm-7", "sent_uid": "e553e02e-0d33-4fed-8f6a-b7cf5c9cf9c9", "type": "token_form_mismatch"}`
- `{"mismatches": [["aG", "aG@"], ["lidi", "@lidi"]], "sent_id": "ped-gramm-11", "sent_uid": "fef391af-9e63-419f-8f81-057459193f49", "type": "token_form_mismatch"}`
- `{"mismatches": [["ane", "ane@"], ["napioi", "@napioi"]], "sent_id": "ped-gramm-24", "sent_uid": "2f47b402-9fe7-4714-96e3-c6cbdf405472", "type": "token_form_mismatch"}`
- `{"mismatches": [["me", "me@"], ["ijo", "@ijo"]], "sent_id": "ped-gramm-27", "sent_uid": "7b810df7-6ed0-4027-b2fe-72c64e9ca1dc", "type": "token_form_mismatch"}`
- `{"mismatches": [["eyodi", "Eyodi"]], "sent_id": "ped-gramm-28", "sent_uid": "ee1a1190-7803-404c-83f6-49d3ccf63b0d", "type": "token_form_mismatch"}`
- `{"mismatches": [["eyodi", "Eyodi"]], "sent_id": "ped-gramm-29", "sent_uid": "4bdb4b8f-0176-4303-8a13-e313fbb6d7ad", "type": "token_form_mismatch"}`
- `{"gold_count": 3, "gold_forms": ["eyodi", "ane", "niganaGacanajo"], "json_count": 4, "json_forms": ["Eyodi", "ane", "*T*", "niganaGacanajo"], "sent_id": "ped-gramm-30", "sent_uid": "7b806584-75e5-4017-b9e2-ba97458903bd", "type": "token_count_mismatch"}`
- `{"mismatches": [["aG", "aG@"], ["ipegitegi", "@ipegitegi"]], "sent_id": "ped-gramm-37", "sent_uid": "1da1bf7a-7975-4baf-821b-9df5c75ac297", "type": "token_form_mismatch"}`

### ambiguous_lemmas (2)
- `{"best": "ane", "best_count": 3, "counts": {"ane": 3, "napioi": 1}, "form": "ane", "share": 0.75, "total": 4, "upos": "PRON"}`
- `{"best": "eyodi", "best_count": 2, "counts": {"eyodi": 2, "iodi": 1}, "form": "eyodi", "share": 0.6667, "total": 3, "upos": "NOUN"}`

### ambiguous_feats (4)
- `{"best": "AdvType=Loc|PronType=Dem", "best_count": 1, "counts": {"AdvType=Loc|Deixis=Remt|PronType=Dem": 1, "AdvType=Loc|PronType=Dem": 1}, "form": "digoida", "share": 0.5, "total": 2, "upos": "ADV"}`
- `{"best": "Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1", "best_count": 2, "counts": {"Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1": 2, "_": 1}, "form": "eyodi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 4, "counts": {"Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 4, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitegi", "share": 0.6667, "total": 6, "upos": "VERB"}`
- `{"best": "Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1, "Person[psor]=3": 1}, "form": "lidi", "share": 0.5, "total": 2, "upos": "NOUN"}`

### ambiguous_prontype (0)
_None_

### ambiguous_tag_to_prontype (0)
_None_

### low_evidence_lemmas (21)
- `{"best": "eyodi", "best_count": 1, "counts": {"eyodi": 1}, "form": "Eyodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nigota", "best_count": 1, "counts": {"nigota": 1}, "form": "GanigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nixoa", "best_count": 1, "counts": {"nixoa": 1}, "form": "Ganixoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "joão", "best_count": 1, "counts": {"joão": 1}, "form": "João", "share": 1.0, "total": 1, "upos": "PROPN"}`
- `{"best": "dowediteloco", "best_count": 1, "counts": {"dowediteloco": 1}, "form": "dowediteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "pegi", "best_count": 1, "counts": {"pegi": 1}, "form": "ipegitaGagi", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "pegi", "best_count": 1, "counts": {"pegi": 1}, "form": "ipegitege", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "binie", "best_count": 1, "counts": {"binie": 1}, "form": "libinienigipi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "iona", "best_count": 1, "counts": {"iona": 1}, "form": "lionigipi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "wigo", "best_count": 1, "counts": {"wigo": 1}, "form": "liwigo", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "odawa", "best_count": 1, "counts": {"odawa": 1}, "form": "lodawa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "oigi", "best_count": 1, "counts": {"oigi": 1}, "form": "loigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "oigi", "best_count": 1, "counts": {"oigi": 1}, "form": "loigipodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "oligi", "best_count": 1, "counts": {"oligi": 1}, "form": "loligi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "taGa", "best_count": 1, "counts": {"taGa": 1}, "form": "micoataGa", "share": 1.0, "total": 1, "upos": "SCONJ"}`
- ... and 6 more

### low_evidence_feats (21)
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "Eyodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|Person[psor]=2": 1}, "form": "GanigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "Ganixoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc", "best_count": 1, "counts": {"Gender=Masc": 1}, "form": "João", "share": 1.0, "total": 1, "upos": "PROPN"}`
- `{"best": "Mood=Ind|Person[erg]=3|VerbForm=Fin|Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Person[erg]=3|VerbForm=Fin|Voice=Appl": 1}, "form": "dowediteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Mood=Ind|Number[obj]=Sing|Person[erg]=3|Person[obj]=2|VerbForm=Fin|Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Number[obj]=Sing|Person[erg]=3|Person[obj]=2|VerbForm=Fin|Voice=Appl": 1}, "form": "ipegitaGagi", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 1}, "form": "ipegitege", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Degree=Dim|Gender=Masc|Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Degree=Dim|Gender=Masc|Number=Plur|Person[psor]=3": 1}, "form": "libinienigipi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Gender=Fem|Number=Plur|Person[psor]=3": 1}, "form": "lionigipi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "liwigo", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem,Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Gender=Fem,Masc|Number=Sing|Person[psor]=3": 1}, "form": "lodawa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "loigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Plur|Person[psor]=3": 1}, "form": "loigipodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "loligi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "micoataGa", "share": 1.0, "total": 1, "upos": "SCONJ"}`
- ... and 6 more

### low_evidence_prontype (1)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGajo", "share": 1.0, "total": 1, "upos": "PRON"}`

### low_evidence_tag_to_prontype (3)
- `{"best": "Dem", "best_count": 2, "counts": {"Dem": 2}, "raw_tag": "ADV", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "PRO$", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Rel", "best_count": 3, "counts": {"Rel": 3}, "raw_tag": "WPRO", "share": 1.0, "total": 3, "upos": "PRON"}`

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment prefers `sent_uid`, then falls back to `text_orig` / `text`.
- Token alignment ignores punctuation and MWT lines.
