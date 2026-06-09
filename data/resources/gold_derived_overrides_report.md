# Gold-derived overrides report

## Summary

- Gold sentences: **82**
- JSON sentences: **204**
- UID-matched sentence pairs: **82**
- Usable aligned sentence pairs: **79**
- UID-matched but rejected: **3**
- `lemma_overrides`: **49**
- `form_feat_overrides`: **42**
- `prontype_overrides`: **12**
- `lemma_prontype_overrides`: **14**
- `tag_to_default_prontype`: **3**
## Review items

### json_alignment_issues (4)
- `{"gold_count": 7, "gold_forms": ["eyodi", "dowediteloco", "naodigijedi", "micoataGa", "daGa", "me", "lionigipi"], "json_count": 8, "json_forms": ["Eyodi", "dowediteloco", "naodigijedi", "me@", "@icawataGa", "daGa", "me", "lionigipi"], "json_path": "$.pages[0].sentences[27]", "sent_id": "ped-gramm-28", "sent_uid": "ee1a1190-7803-404c-83f6-49d3ccf63b0d", "source_file": "../data/gramatica-pedagogica.json", "type": "token_count_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "dakake", "lojedi"], "json_count": 5, "json_forms": ["Etogo", "ane@", "@iwaGadi", "adakake", "lojedi"], "json_path": "$.pages[0].sentences[4]", "sent_id": "hil-data-5", "sent_uid": "e349508c-4d86-48b8-9918-057988755e77", "source_file": "../data/dados-hil.json", "type": "token_count_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "dakake", "loojedi"], "json_count": 5, "json_forms": ["Etogo", "ane", "iwaGadi", "adakake", "loojedi"], "json_path": "$.pages[0].sentences[5]", "sent_id": "hil-data-6", "sent_uid": "1d10c633-e74d-4e27-ac23-6b6b2dde9647", "source_file": "../data/dados-hil.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[29]", "mismatches": [["niGijo", "nGijo"]], "sent_id": "van-data-30", "sent_uid": "0c7e64fb-f070-4faa-a12a-c110cdf4bf16", "source_file": "../data/van-data.json", "type": "token_form_mismatch"}`

### ambiguous_lemmas (8)
- `{"best": "nitibeci", "best_count": 1, "counts": {"ninitibeci": 1, "nitibece": 1, "nitibeci": 1}, "form": "Ninitibeci", "share": 0.3333, "total": 3, "upos": "VERB"}`
- `{"best": "dakake", "best_count": 2, "counts": {"akake": 1, "dakake": 2}, "form": "dakake", "share": 0.6667, "total": 3, "upos": "ADJ"}`
- `{"best": "eyodi", "best_count": 2, "counts": {"eyodi": 2, "iodi": 1}, "form": "eyodi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "odajo", "best_count": 1, "counts": {"odaajo": 1, "odajo": 1}, "form": "lodajo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "omigo", "best_count": 1, "counts": {"lomigo": 1, "omigo": 1}, "form": "lomigo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "niganaGacanajo", "best_count": 2, "counts": {"niganaGacanajo": 2, "niganagacanajo": 1}, "form": "niganaGacanajo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "nitibeci", "best_count": 1, "counts": {"nitibece": 1, "nitibeci": 1}, "form": "ninitibeci", "share": 0.5, "total": 2, "upos": "VERB"}`
- `{"best": "wetiGa", "best_count": 3, "counts": {"wetiGa": 3, "wetiga": 1}, "form": "wetiGa", "share": 0.75, "total": 4, "upos": "NOUN"}`

### ambiguous_feats (6)
- `{"best": "AdvType=Loc|PronType=Dem", "best_count": 1, "counts": {"AdvType=Loc|Deixis=Remt|PronType=Dem": 1, "AdvType=Loc|PronType=Dem": 1}, "form": "digoida", "share": 0.5, "total": 2, "upos": "ADV"}`
- `{"best": "_", "best_count": 2, "counts": {"PronType=Ind": 2, "_": 2}, "form": "eliodi", "share": 0.5, "total": 4, "upos": "ADV"}`
- `{"best": "Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1", "best_count": 2, "counts": {"Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1": 2, "_": 1}, "form": "eyodi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 4, "counts": {"Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 4, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitegi", "share": 0.6667, "total": 6, "upos": "VERB"}`
- `{"best": "Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1, "Person[psor]=3": 1}, "form": "lidi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Number=Plur|Person[psor]=3": 1, "_": 1}, "form": "lotiidi", "share": 0.5, "total": 2, "upos": "NOUN"}`

### ambiguous_prontype (0)
_None_

### ambiguous_lemma_prontype (0)
_None_

### ambiguous_tag_to_prontype (0)
_None_

### low_evidence_lemmas (55)
- `{"best": "da", "best_count": 1, "counts": {"da": 1}, "form": "Ada", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "di", "best_count": 1, "counts": {"di": 1}, "form": "Adi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "ni", "best_count": 1, "counts": {"ni": 1}, "form": "Ani", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "apicoGo", "best_count": 1, "counts": {"apicoGo": 1}, "form": "DapicoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "eyo", "best_count": 1, "counts": {"eyo": 1}, "form": "Eyo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "eyodi", "best_count": 1, "counts": {"eyodi": 1}, "form": "Eyodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "odawa", "best_count": 1, "counts": {"odawa": 1}, "form": "Gadodawa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nigota", "best_count": 1, "counts": {"nigota": 1}, "form": "GanigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nioxoa", "best_count": 1, "counts": {"nioxoa": 1}, "form": "Ganioxoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nixoa", "best_count": 1, "counts": {"nixoa": 1}, "form": "Ganixoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "wenigi", "best_count": 1, "counts": {"wenigi": 1}, "form": "Gawenigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "iwaalo", "best_count": 1, "counts": {"iwaalo": 1}, "form": "Iwaalepodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "joão", "best_count": 1, "counts": {"joão": 1}, "form": "João", "share": 1.0, "total": 1, "upos": "PROPN"}`
- `{"best": "binie", "best_count": 1, "counts": {"binie": 1}, "form": "Libiniena", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "binie", "best_count": 1, "counts": {"binie": 1}, "form": "Libinienigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- ... and 40 more

### low_evidence_feats (36)
- `{"best": "Mood=Ind|Person=3|VerbForm=Fin", "best_count": 1, "counts": {"Mood=Ind|Person=3|VerbForm=Fin": 1}, "form": "DapicoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "Eyodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem,Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Fem,Masc|Number=Sing|Person[psor]=2": 1}, "form": "Gadodawa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|Person[psor]=2": 1}, "form": "GanigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "Ganioxoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "Ganixoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "Gawenigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Plur", "best_count": 1, "counts": {"Gender=Fem|Number=Plur": 1}, "form": "Iwaalepodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc", "best_count": 1, "counts": {"Gender=Masc": 1}, "form": "João", "share": 1.0, "total": 1, "upos": "PROPN"}`
- `{"best": "Degree=Dim|Gender=Fem|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Degree=Dim|Gender=Fem|Number=Sing|Person[psor]=3": 1}, "form": "Libiniena", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Degree=Dim|Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 1, "counts": {"Degree=Dim|Gender=Masc|Number=Sing|Person[psor]=3": 1}, "form": "Libinienigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Mood=Ind|Number=Plur|Person=3|VerbForm=Fin", "best_count": 1, "counts": {"Mood=Ind|Number=Plur|Person=3|VerbForm=Fin": 1}, "form": "Ninitibigiwaji", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "Pedilo", "share": 1.0, "total": 1, "upos": "PROPN"}`
- `{"best": "Mood=Ind|VerbForm=Fin", "best_count": 1, "counts": {"Mood=Ind|VerbForm=Fin": 1}, "form": "Te", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "dineigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- ... and 21 more

### low_evidence_prontype (19)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "Ada", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "Adi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "Ani", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "form": "Eyo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NaGajo", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NaGajo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NaGana", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NiGijo", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "NiGinoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "form": "ee", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idiwa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idowa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ijowa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGajo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGana", "share": 1.0, "total": 1, "upos": "DET"}`
- ... and 4 more

### low_evidence_lemma_prontype (10)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "da", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "di", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "lemma": "ee", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "lemma": "eyo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "ida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "idi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Rel", "best_count": 1, "counts": {"Rel": 1}, "lemma": "napioi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "ni", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGidi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGina", "share": 1.0, "total": 1, "upos": "PRON"}`

### low_evidence_tag_to_prontype (5)
- `{"best": "Dem", "best_count": 2, "counts": {"Dem": 2}, "raw_tag": "D", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Prs", "best_count": 2, "counts": {"Prs": 2}, "raw_tag": "PRO", "share": 1.0, "total": 2, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "PRO$", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Ind", "best_count": 2, "counts": {"Ind": 2}, "raw_tag": "Q", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "Q", "share": 1.0, "total": 1, "upos": "DET"}`

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment is UID-only: gold `sent_uid` must match JSON sentence `uid`.
- Token alignment ignores punctuation and MWT lines.
