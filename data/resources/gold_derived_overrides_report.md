# Gold-derived overrides report

## Summary

- Gold sentences: **71**
- JSON sentences: **128**
- Aligned sentence pairs: **60**
- `lemma_overrides`: **43**
- `form_feat_overrides`: **46**
- `prontype_overrides`: **11**
- `tag_to_default_prontype`: **2**

## Review items

### json_alignment_issues (27)
- `{"json_path": "$.pages[0].sentences[6]", "mismatches": [["aG", "aG@"], ["ipegetege", "@ipegetege"]], "sent_id": "ped-gramm-7", "sent_uid": "e553e02e-0d33-4fed-8f6a-b7cf5c9cf9c9", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"json_path": "$.pages[0].sentences[10]", "mismatches": [["aG", "aG@"], ["lidi", "@lidi"]], "sent_id": "ped-gramm-11", "sent_uid": "fef391af-9e63-419f-8f81-057459193f49", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"json_path": "$.pages[0].sentences[12]", "mismatches": [["dapiko", "dapico"]], "sent_id": "ped-gramm-13", "sent_uid": "68277d1f-c30b-4c4f-ba9e-c2883cc133af", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"json_path": "$.pages[0].sentences[17]", "mismatches": [["lidGegi", "lideGegi"]], "sent_id": "ped-gramm-18", "sent_uid": "582429f2-67d5-4077-b209-6deb7b5df54f", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"json_path": "$.pages[0].sentences[23]", "mismatches": [["ane", "ane@"], ["napioi", "@napioi"]], "sent_id": "ped-gramm-24", "sent_uid": "2f47b402-9fe7-4714-96e3-c6cbdf405472", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"gold_count": 4, "gold_forms": ["João", "liGeladi", "ane", "napioi"], "json_count": 5, "json_forms": ["João", "liGeladi", "ane", "*T*", "napioi"], "json_path": "$.pages[0].sentences[25]", "sent_id": "ped-gramm-26", "sent_uid": "f081c545-c42b-463d-b57f-db87787f20e7", "source_file": "../data/gramatica-pedagogica.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[26]", "mismatches": [["me", "me@"], ["ijo", "@ijo"]], "sent_id": "ped-gramm-27", "sent_uid": "7b810df7-6ed0-4027-b2fe-72c64e9ca1dc", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"gold_count": 7, "gold_forms": ["eyodi", "dowediteloco", "naodigijedi", "micoataGa", "daGa", "me", "lionigipi"], "json_count": 8, "json_forms": ["Eyodi", "dowediteloco", "naodigijedi", "me@", "@icawataGa", "daGa", "me", "lionigipi"], "json_path": "$.pages[0].sentences[27]", "sent_id": "ped-gramm-28", "sent_uid": "ee1a1190-7803-404c-83f6-49d3ccf63b0d", "source_file": "../data/gramatica-pedagogica.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[28]", "mismatches": [["eyodi", "Eyodi"]], "sent_id": "ped-gramm-29", "sent_uid": "4bdb4b8f-0176-4303-8a13-e313fbb6d7ad", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"gold_count": 3, "gold_forms": ["eyodi", "ane", "niganaGacanajo"], "json_count": 4, "json_forms": ["Eyodi", "ane", "*T*", "niganaGacanajo"], "json_path": "$.pages[0].sentences[29]", "sent_id": "ped-gramm-30", "sent_uid": "7b806584-75e5-4017-b9e2-ba97458903bd", "source_file": "../data/gramatica-pedagogica.json", "type": "token_count_mismatch"}`
- `{"gold_count": 5, "gold_forms": ["iGeladi", "ipegitegi", "naigi", "ane", "napioi"], "json_count": 6, "json_forms": ["iGeladi", "ipegitegi", "naigi", "ane", "*T*", "napioi"], "json_path": "$.pages[0].sentences[34]", "sent_id": "ped-gramm-35", "sent_uid": "014fefb1-d5e3-48c8-9ac3-9e713a41407f", "source_file": "../data/gramatica-pedagogica.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[36]", "mismatches": [["aG", "aG@"], ["ipegitegi", "@ipegitegi"]], "sent_id": "ped-gramm-37", "sent_uid": "1da1bf7a-7975-4baf-821b-9df5c75ac297", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "dakake", "lojedi"], "json_count": 7, "json_forms": ["Etogo", "ane@", "*T*", "@iwaGadi", "aG@", "@dakake", "lojedi"], "json_path": "$.pages[0].sentences[4]", "sent_id": "hil-data-5", "sent_uid": "e349508c-4d86-48b8-9918-057988755e77", "source_file": "../data/dados-hil.json", "type": "token_count_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "akake", "loojedi"], "json_count": 7, "json_forms": ["Etogo", "ane", "*T*", "iwaGadi", "aG@", "@dakake", "loojedi"], "json_path": "$.pages[0].sentences[5]", "sent_id": "hil-data-6", "sent_uid": "1d10c633-e74d-4e27-ac23-6b6b2dde9647", "source_file": "../data/dados-hil.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[9]", "mismatches": [["me", "me@"], ["adi", "@adi"]], "sent_id": "hil-data-10", "sent_uid": "559ba85f-edfc-48dc-9bfb-0c3f8e5ad887", "source_file": "../data/dados-hil.json", "type": "token_form_mismatch"}`
- ... and 12 more

### ambiguous_lemmas (8)
- `{"best": "nitibeci", "best_count": 1, "counts": {"ninitibeci": 1, "nitibece": 1, "nitibeci": 1}, "form": "Ninitibeci", "share": 0.3333, "total": 3, "upos": "VERB"}`
- `{"best": "dakake", "best_count": 1, "counts": {"akake": 1, "dakake": 1}, "form": "dakake", "share": 0.5, "total": 2, "upos": "ADJ"}`
- `{"best": "eyodi", "best_count": 2, "counts": {"eyodi": 2, "iodi": 1}, "form": "eyodi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "omigo", "best_count": 1, "counts": {"lomigo": 1, "omigo": 1}, "form": "lomigo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "niganagacanajo", "best_count": 2, "counts": {"niganaGacanajo": 1, "niganagacanajo": 2}, "form": "niganaGacanajo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "gotaGa", "best_count": 1, "counts": {"gotaGa": 1, "nigota": 1}, "form": "nigotaGa", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "nitibeci", "best_count": 1, "counts": {"nitibece": 1, "nitibeci": 1}, "form": "ninitibeci", "share": 0.5, "total": 2, "upos": "VERB"}`
- `{"best": "wetiGa", "best_count": 3, "counts": {"wetiGa": 3, "wetiga": 1}, "form": "wetiGa", "share": 0.75, "total": 4, "upos": "NOUN"}`

### ambiguous_feats (5)
- `{"best": "AdvType=Loc|PronType=Dem", "best_count": 1, "counts": {"AdvType=Loc|Deixis=Remt|PronType=Dem": 1, "AdvType=Loc|PronType=Dem": 1}, "form": "digoida", "share": 0.5, "total": 2, "upos": "ADV"}`
- `{"best": "PronType=Ind", "best_count": 2, "counts": {"AdvType=Deg": 1, "PronType=Ind": 2, "_": 1}, "form": "eliodi", "share": 0.5, "total": 4, "upos": "ADV"}`
- `{"best": "Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1", "best_count": 2, "counts": {"Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1": 2, "_": 1}, "form": "eyodi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 4, "counts": {"Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 4, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitegi", "share": 0.6667, "total": 6, "upos": "VERB"}`
- `{"best": "Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1, "Person[psor]=3": 1}, "form": "lidi", "share": 0.5, "total": 2, "upos": "NOUN"}`

### ambiguous_prontype (0)
_None_

### ambiguous_tag_to_prontype (0)
_None_

### low_evidence_lemmas (48)
- `{"best": "da", "best_count": 1, "counts": {"da": 1}, "form": "Ada", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "di", "best_count": 1, "counts": {"di": 1}, "form": "Adi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "ni", "best_count": 1, "counts": {"ni": 1}, "form": "Ani", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "apicoGo", "best_count": 1, "counts": {"apicoGo": 1}, "form": "DapicoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "eyodi", "best_count": 1, "counts": {"eyodi": 1}, "form": "Eyodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "odawa", "best_count": 1, "counts": {"odawa": 1}, "form": "Gadodawa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nigota", "best_count": 1, "counts": {"nigota": 1}, "form": "GanigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nioxoa", "best_count": 1, "counts": {"nioxoa": 1}, "form": "Ganioxoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nixoa", "best_count": 1, "counts": {"nixoa": 1}, "form": "Ganixoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "wenigi", "best_count": 1, "counts": {"wenigi": 1}, "form": "Gawenigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "iwa", "best_count": 1, "counts": {"iwa": 1}, "form": "Iwalepodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "joão", "best_count": 1, "counts": {"joão": 1}, "form": "João", "share": 1.0, "total": 1, "upos": "PROPN"}`
- `{"best": "binie", "best_count": 1, "counts": {"binie": 1}, "form": "Libiniena", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "binie", "best_count": 1, "counts": {"binie": 1}, "form": "Libinienigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "niGijo", "best_count": 1, "counts": {"niGijo": 1}, "form": "NaGajo", "share": 1.0, "total": 1, "upos": "DET"}`
- ... and 33 more

### low_evidence_feats (48)
- `{"best": "Gender=Fem|Number=Sing|PronType=Dem", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "Ada", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Gender=Fem|Number=Sing|PronType=Dem", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "Adi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Gender=Fem|Number=Sing|PronType=Dem", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "Ani", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Mood=Ind|Person=3|VerbForm=Fin", "best_count": 1, "counts": {"Mood=Ind|Person=3|VerbForm=Fin": 1}, "form": "DapicoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "Eyodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem,Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Fem,Masc|Number=Sing|Person[psor]=2": 1}, "form": "Gadodawa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|Person[psor]=2": 1}, "form": "GanigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "Ganioxoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "Ganixoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "Gawenigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Plur", "best_count": 1, "counts": {"Gender=Fem|Number=Plur": 1}, "form": "Iwalepodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc", "best_count": 1, "counts": {"Gender=Masc": 1}, "form": "João", "share": 1.0, "total": 1, "upos": "PROPN"}`
- `{"best": "Degree=Dim|Gender=Fem|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Degree=Dim|Gender=Fem|Number=Sing|Person[psor]=3": 1}, "form": "Libiniena", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Degree=Dim|Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Degree=Dim|Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "Libinienigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing|PronType=Dem", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "NaGajo", "share": 1.0, "total": 1, "upos": "DET"}`
- ... and 33 more

### low_evidence_prontype (12)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "Ada", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "Adi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "Ani", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NaGajo", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NaGajo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NaGana", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NiGijo", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NiGinoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "form": "ee", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGajo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGana", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGani", "share": 1.0, "total": 1, "upos": "DET"}`

### low_evidence_tag_to_prontype (5)
- `{"best": "Dem", "best_count": 2, "counts": {"Dem": 2}, "raw_tag": "D", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "raw_tag": "PRO", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "PRO$", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Ind", "best_count": 2, "counts": {"Ind": 2}, "raw_tag": "Q", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Rel", "best_count": 1, "counts": {"Rel": 1}, "raw_tag": "WPRO", "share": 1.0, "total": 1, "upos": "PRON"}`

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment is UID-only: gold `sent_uid` must match JSON sentence `uid`.
- Token alignment ignores punctuation and MWT lines.
