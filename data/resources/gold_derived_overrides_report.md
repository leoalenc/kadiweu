# Gold-derived overrides report

## Summary

- Gold sentences: **74**
- JSON sentences: **204**
- UID-matched sentence pairs: **74**
- Usable aligned sentence pairs: **71**
- UID-matched but rejected: **3**
- `lemma_overrides`: **43**
- `form_feat_overrides`: **46**
- `prontype_overrides`: **11**
- `tag_to_default_prontype`: **3**

## Review items

### json_alignment_issues (7)
- `{"json_path": "$.pages[0].sentences[17]", "mismatches": [["lidGegi", "lideGegi"]], "sent_id": "ped-gramm-18", "sent_uid": "582429f2-67d5-4077-b209-6deb7b5df54f", "source_file": "../data/gramatica-pedagogica.json", "type": "token_form_mismatch"}`
- `{"gold_count": 7, "gold_forms": ["eyodi", "dowediteloco", "naodigijedi", "micoataGa", "daGa", "me", "lionigipi"], "json_count": 8, "json_forms": ["Eyodi", "dowediteloco", "naodigijedi", "me@", "@icawataGa", "daGa", "me", "lionigipi"], "json_path": "$.pages[0].sentences[27]", "sent_id": "ped-gramm-28", "sent_uid": "ee1a1190-7803-404c-83f6-49d3ccf63b0d", "source_file": "../data/gramatica-pedagogica.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[0]", "mismatches": [["Iwalo", "Iwaalo"]], "sent_id": "hil-data-1", "sent_uid": "fcef38ed-be6b-4f2a-b5cf-fa4db625ecfb", "source_file": "../data/dados-hil.json", "type": "token_form_mismatch"}`
- `{"json_path": "$.pages[0].sentences[1]", "mismatches": [["Iwalo", "Iwaalo"]], "sent_id": "hil-data-2", "sent_uid": "31d3b4c0-4aab-4538-999b-b8ee85c34444", "source_file": "../data/dados-hil.json", "type": "token_form_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "dakake", "lojedi"], "json_count": 5, "json_forms": ["Etogo", "ane@", "@iwaGadi", "adakake", "lojedi"], "json_path": "$.pages[0].sentences[4]", "sent_id": "hil-data-5", "sent_uid": "e349508c-4d86-48b8-9918-057988755e77", "source_file": "../data/dados-hil.json", "type": "token_count_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "akake", "loojedi"], "json_count": 5, "json_forms": ["Etogo", "ane", "iwaGadi", "adakake", "loojedi"], "json_path": "$.pages[0].sentences[5]", "sent_id": "hil-data-6", "sent_uid": "1d10c633-e74d-4e27-ac23-6b6b2dde9647", "source_file": "../data/dados-hil.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[14]", "mismatches": [["Iwalepodi", "Iwaalepodi"]], "sent_id": "hil-data-15", "sent_uid": "baccc279-f303-4b4f-a6d7-4404de699f4a", "source_file": "../data/dados-hil.json", "type": "token_form_mismatch"}`

### ambiguous_lemmas (8)
- `{"best": "iwa", "best_count": 1, "counts": {"iwa": 1, "iwaalo": 1}, "form": "Iwalo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "nitibeci", "best_count": 1, "counts": {"ninitibeci": 1, "nitibece": 1, "nitibeci": 1}, "form": "Ninitibeci", "share": 0.3333, "total": 3, "upos": "VERB"}`
- `{"best": "dakake", "best_count": 1, "counts": {"akake": 1, "dakake": 1}, "form": "dakake", "share": 0.5, "total": 2, "upos": "ADJ"}`
- `{"best": "eyodi", "best_count": 2, "counts": {"eyodi": 2, "iodi": 1}, "form": "eyodi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "omigo", "best_count": 1, "counts": {"lomigo": 1, "omigo": 1}, "form": "lomigo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "niganaGacanajo", "best_count": 2, "counts": {"niganaGacanajo": 2, "niganagacanajo": 1}, "form": "niganaGacanajo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
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

### low_evidence_lemmas (51)
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
- `{"best": "iwaalo", "best_count": 1, "counts": {"iwaalo": 1}, "form": "Iwalepodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "joão", "best_count": 1, "counts": {"joão": 1}, "form": "João", "share": 1.0, "total": 1, "upos": "PROPN"}`
- `{"best": "binie", "best_count": 1, "counts": {"binie": 1}, "form": "Libiniena", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "binie", "best_count": 1, "counts": {"binie": 1}, "form": "Libinienigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "niGijo", "best_count": 1, "counts": {"niGijo": 1}, "form": "NaGajo", "share": 1.0, "total": 1, "upos": "DET"}`
- ... and 36 more

### low_evidence_feats (51)
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
- ... and 36 more

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

### low_evidence_tag_to_prontype (4)
- `{"best": "Dem", "best_count": 2, "counts": {"Dem": 2}, "raw_tag": "D", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "raw_tag": "PRO", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "PRO$", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Ind", "best_count": 2, "counts": {"Ind": 2}, "raw_tag": "Q", "share": 1.0, "total": 2, "upos": "ADV"}`

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment is UID-only: gold `sent_uid` must match JSON sentence `uid`.
- Token alignment ignores punctuation and MWT lines.
