# Gold-derived overrides report

## Summary

- Gold sentences: **25**
- JSON sentences: **37**
- Aligned sentence pairs: **24**
- `lemma_overrides`: **23**
- `form_feat_overrides`: **22**
- `prontype_overrides`: **4**
- `tag_to_default_prontype`: **1**

## Review items

### json_alignment_issues (5)
- `{"mismatches": [["aG", "aG@"], ["ipegetege", "@ipegetege"]], "sent_id": "ped-gramm-7", "sent_uid": "e553e02e-0d33-4fed-8f6a-b7cf5c9cf9c9", "type": "token_form_mismatch"}`
- `{"mismatches": [["aG", "aG@"], ["lidi", "@lidi"]], "sent_id": "ped-gramm-11", "sent_uid": "fef391af-9e63-419f-8f81-057459193f49", "type": "token_form_mismatch"}`
- `{"mismatches": [["me", "me@"], ["ijo", "@ijo"]], "sent_id": "ped-gramm-27", "sent_uid": "7b810df7-6ed0-4027-b2fe-72c64e9ca1dc", "type": "token_form_mismatch"}`
- `{"gold_count": 3, "gold_forms": ["Eyodi", "ane", "niganaGacanajo"], "json_count": 4, "json_forms": ["Eyodi", "ane", "*T*", "niganaGacanajo"], "sent_id": "ped-gramm-30", "sent_uid": "7b806584-75e5-4017-b9e2-ba97458903bd", "type": "token_count_mismatch"}`
- `{"mismatches": [["aG", "aG@"], ["ipegitegi", "@ipegitegi"], ["weigi", "weiigi"]], "sent_id": "ped-gramm-37", "sent_uid": "1da1bf7a-7975-4baf-821b-9df5c75ac297", "type": "token_form_mismatch"}`

### ambiguous_lemmas (1)
- `{"best": "wagadi", "best_count": 1, "counts": {"iwaGadi": 1, "wagadi": 1}, "form": "iwaGadi", "share": 0.5, "total": 2, "upos": "VERB"}`

### ambiguous_feats (2)
- `{"best": "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 4, "counts": {"Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 4, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitegi", "share": 0.6667, "total": 6, "upos": "VERB"}`
- `{"best": "Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1, "Person[psor]=3": 1}, "form": "lidi", "share": 0.5, "total": 2, "upos": "NOUN"}`

### ambiguous_prontype (0)
_None_

### ambiguous_tag_to_prontype (0)
_None_

### low_evidence_lemmas (15)
- `{"best": "eyodi", "best_count": 1, "counts": {"eyodi": 1}, "form": "Eyodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nigotaGa", "best_count": 1, "counts": {"nigotaGa": 1}, "form": "GanigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "digoida", "best_count": 1, "counts": {"digoida": 1}, "form": "digoida", "share": 1.0, "total": 1, "upos": "ADV"}`
- `{"best": "pegi", "best_count": 1, "counts": {"pegi": 1}, "form": "ipegitaGagi", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "pegi", "best_count": 1, "counts": {"pegi": 1}, "form": "ipegitege", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "ibinie", "best_count": 1, "counts": {"ibinie": 1}, "form": "libinienigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "odawa", "best_count": 1, "counts": {"odawa": 1}, "form": "lodawa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "oigi", "best_count": 1, "counts": {"oigi": 1}, "form": "loigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "oligi", "best_count": 1, "counts": {"oligi": 1}, "form": "loligi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "jo", "best_count": 1, "counts": {"jo": 1}, "form": "naGajo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "niganagacanajo", "best_count": 1, "counts": {"niganagacanajo": 1}, "form": "niganaGacanajo", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "niganigi", "best_count": 1, "counts": {"niganigi": 1}, "form": "niganigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "gotaGa", "best_count": 1, "counts": {"gotaGa": 1}, "form": "nigotaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nioladi", "best_count": 1, "counts": {"nioladi": 1}, "form": "nioladi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "weigi", "best_count": 1, "counts": {"weigi": 1}, "form": "weigi", "share": 1.0, "total": 1, "upos": "NOUN"}`

### low_evidence_feats (15)
- `{"best": "Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1": 1}, "form": "Eyodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|Person[psor]=2": 1}, "form": "GanigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "AdvType=Loc|PronType=Dem", "best_count": 1, "counts": {"AdvType=Loc|PronType=Dem": 1}, "form": "digoida", "share": 1.0, "total": 1, "upos": "ADV"}`
- `{"best": "Mood=Ind|Number[obj]=Sing|Person[erg]=3|Person[obj]=2|VerbForm=Fin|Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Number[obj]=Sing|Person[erg]=3|Person[obj]=2|VerbForm=Fin|Voice=Appl": 1}, "form": "ipegitaGagi", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 1}, "form": "ipegitege", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Degree=Dim|Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Degree=Dim|Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "libinienigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem,Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Gender=Fem,Masc|Number=Sing|Person[psor]=3": 1}, "form": "lodawa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "loigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "loligi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|PronType=Dem", "best_count": 1, "counts": {"Gender=Fem|PronType=Dem": 1}, "form": "naGajo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Gender=Masc|Number=Sing", "best_count": 1, "counts": {"Gender=Masc|Number=Sing": 1}, "form": "niganaGacanajo", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing", "best_count": 1, "counts": {"Gender=Masc|Number=Sing": 1}, "form": "niganigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing", "best_count": 1, "counts": {"Gender=Fem|Number=Sing": 1}, "form": "nigotaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "nioladi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing", "best_count": 1, "counts": {"Gender=Masc|Number=Sing": 1}, "form": "weigi", "share": 1.0, "total": 1, "upos": "NOUN"}`

### low_evidence_prontype (2)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "digoida", "share": 1.0, "total": 1, "upos": "ADV"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGajo", "share": 1.0, "total": 1, "upos": "PRON"}`

### low_evidence_tag_to_prontype (3)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "ADV", "share": 1.0, "total": 1, "upos": "ADV"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "PRO$", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Rel", "best_count": 1, "counts": {"Rel": 1}, "raw_tag": "WPRO", "share": 1.0, "total": 1, "upos": "PRON"}`

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment prefers `sent_uid`, then falls back to `text_orig` / `text`.
- Token alignment ignores punctuation and MWT lines.
