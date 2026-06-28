# Gold-derived overrides report

## Summary

- Gold sentences: **103**
- JSON sentences: **204**
- UID-matched sentence pairs: **103**
- Usable aligned sentence pairs: **100**
- UID-matched but rejected: **3**
- `lemma_overrides`: **62**
- `form_feat_overrides`: **65**
- `prontype_overrides`: **19**
- `lemma_prontype_overrides`: **3**
- `tag_to_default_prontype`: **3**
## Review items

### json_alignment_issues (5)
- `{"gold_count": 7, "gold_forms": ["eyodi", "dowediteloco", "naodigijedi", "micoataGa", "daGa", "me", "lionigipi"], "json_count": 8, "json_forms": ["Eyodi", "dowediteloco", "naodigijedi", "me@", "@icawataGa", "daGa", "me", "lionigipi"], "json_path": "$.pages[0].sentences[27]", "sent_id": "ped-gramm-28", "sent_uid": "ee1a1190-7803-404c-83f6-49d3ccf63b0d", "source_file": "../data/ped-gramm.json", "type": "token_count_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "dakake", "lojedi"], "json_count": 5, "json_forms": ["Etogo", "ane@", "@iwaGadi", "adakake", "lojedi"], "json_path": "$.pages[0].sentences[4]", "sent_id": "hil-data-5", "sent_uid": "e349508c-4d86-48b8-9918-057988755e77", "source_file": "../data/hil-data.json", "type": "token_count_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "dakake", "loojedi"], "json_count": 5, "json_forms": ["Etogo", "ane", "iwaGadi", "adakake", "loojedi"], "json_path": "$.pages[0].sentences[5]", "sent_id": "hil-data-6", "sent_uid": "1d10c633-e74d-4e27-ac23-6b6b2dde9647", "source_file": "../data/hil-data.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[12]", "mismatches": [["lomigo", "lomiigo"], ["noatece", "niwatece"]], "sent_id": "van-data-13", "sent_uid": "e9806e26-701d-4f5f-9ca9-63216cccf3d0", "source_file": "../data/van-data.json", "type": "token_form_mismatch"}`
- `{"json_path": "$.pages[0].sentences[29]", "mismatches": [["niGijo", "nGijo"]], "sent_id": "van-data-30", "sent_uid": "0c7e64fb-f070-4faa-a12a-c110cdf4bf16", "source_file": "../data/van-data.json", "type": "token_form_mismatch"}`

### ambiguous_lemmas (12)
- `{"best": "dakake", "best_count": 2, "counts": {"akake": 1, "dakake": 2}, "form": "dakake", "share": 0.6667, "total": 3, "upos": "ADJ"}`
- `{"best": "eyo", "best_count": 1, "counts": {"eeyo": 1, "eyo": 1}, "form": "eeyo", "share": 0.5, "total": 2, "upos": "PRON"}`
- `{"best": "et", "best_count": 1, "counts": {"VB": 1, "et": 1}, "form": "etee", "share": 0.5, "total": 2, "upos": "VERB"}`
- `{"best": "eyo", "best_count": 1, "counts": {"eeyo": 1, "eyo": 1}, "form": "eyo", "share": 0.5, "total": 2, "upos": "PRON"}`
- `{"best": "eyodi", "best_count": 3, "counts": {"eyodi": 3, "iodi": 1}, "form": "eyodi", "share": 0.75, "total": 4, "upos": "NOUN"}`
- `{"best": "liwenigi", "best_count": 1, "counts": {"liwenigi": 1, "wenigi": 1}, "form": "liwenigi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "odajo", "best_count": 1, "counts": {"odaajo": 1, "odajo": 1}, "form": "lodajo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "lomigo", "best_count": 2, "counts": {"lomigo": 2, "omigo": 1, "omiigo": 2}, "form": "lomigo", "share": 0.4, "total": 5, "upos": "NOUN"}`
- `{"best": "oojedi", "best_count": 3, "counts": {"loojedi": 1, "oojedi": 3}, "form": "loojedi", "share": 0.75, "total": 4, "upos": "NOUN"}`
- `{"best": "niganaGacanajo", "best_count": 2, "counts": {"niganaGacanajo": 2, "niganagacanajo": 1}, "form": "niganaGacanajo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "enigi", "best_count": 1, "counts": {"enigi": 1, "wenigi": 1}, "form": "niwenigi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "wetiGa", "best_count": 3, "counts": {"wetiGa": 3, "wetiga": 1}, "form": "wetiGa", "share": 0.75, "total": 4, "upos": "NOUN"}`

### ambiguous_feats (10)
- `{"best": "Mood=Ind|Number=Sing|Person=3|VerbForm=Fin|Voice=Inv", "best_count": 2, "counts": {"Mood=Ind|Number=Sing|Person=3|VerbForm=Fin": 1, "Mood=Ind|Number=Sing|Person=3|VerbForm=Fin|Voice=Inv": 2}, "form": "dapicoGo", "share": 0.6667, "total": 3, "upos": "VERB"}`
- `{"best": "AdvType=Loc|PronType=Dem", "best_count": 1, "counts": {"AdvType=Loc|Deixis=Remt|PronType=Dem": 1, "AdvType=Loc|PronType=Dem": 1}, "form": "digoida", "share": 0.5, "total": 2, "upos": "ADV"}`
- `{"best": "_", "best_count": 2, "counts": {"PronType=Ind": 2, "_": 2}, "form": "eliodi", "share": 0.5, "total": 4, "upos": "ADV"}`
- `{"best": "Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1", "best_count": 2, "counts": {"Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1": 2, "_": 2}, "form": "eyodi", "share": 0.5, "total": 4, "upos": "NOUN"}`
- `{"best": "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 4, "counts": {"Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 4, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitegi", "share": 0.6667, "total": 6, "upos": "VERB"}`
- `{"best": "Gender=Fem|Number=Plur", "best_count": 1, "counts": {"Gender=Fem|Number=Plur": 1, "_": 1}, "form": "iwaalepodi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1, "Person[psor]=3": 1}, "form": "lidi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Gender=Fem,Masc|Number=Plur|Person[psor]=3": 1, "Gender=Fem|Number=Plur|Person[psor]=3": 1}, "form": "lionigipi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing|Person[psor]=3", "best_count": 2, "counts": {"Gender=Fem|Number=Sing|Person[psor]=3": 2, "Person[psor]=3": 1}, "form": "lomiigo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Number=Plur|Person[psor]=3": 1, "_": 1}, "form": "lotiidi", "share": 0.5, "total": 2, "upos": "NOUN"}`

### ambiguous_prontype (0)
_None_

### ambiguous_lemma_prontype (0)
_None_

### ambiguous_tag_to_prontype (0)
_None_

### low_evidence_lemmas (57)
- `{"best": "ida", "best_count": 1, "counts": {"ida": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "idi", "best_count": 1, "counts": {"idi": 1}, "form": "adi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "ini", "best_count": 1, "counts": {"ini": 1}, "form": "ani", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "akake", "best_count": 1, "counts": {"akake": 1}, "form": "dakake", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "dibixoGo", "best_count": 1, "counts": {"dibixoGo": 1}, "form": "dibixodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "dineigi", "best_count": 1, "counts": {"dineigi": 1}, "form": "dineigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "dowediteloco", "best_count": 1, "counts": {"dowediteloco": 1}, "form": "dowediteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "ee", "best_count": 1, "counts": {"ee": 1}, "form": "ee", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "eliodi", "best_count": 1, "counts": {"eliodi": 1}, "form": "eliodi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "eniteloco", "best_count": 1, "counts": {"eniteloco": 1}, "form": "eniteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "et", "best_count": 1, "counts": {"et": 1}, "form": "eteeyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "et", "best_count": 1, "counts": {"et": 1}, "form": "eteyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "aaginaGa", "best_count": 1, "counts": {"aaginaGa": 1}, "form": "ganaaginaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nigota", "best_count": 1, "counts": {"nigota": 1}, "form": "ganigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "nioxoa", "best_count": 1, "counts": {"nioxoa": 1}, "form": "ganioxoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- ... and 42 more

### low_evidence_feats (57)
- `{"best": "Gender=Fem|Number=Sing", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Gender=Fem|Number=Sing", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "adi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Gender=Fem|Number=Sing", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "ani", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Mood=Ind|Person=3|VerbForm=Fin|Voice=Inv", "best_count": 1, "counts": {"Mood=Ind|Person=3|VerbForm=Fin|Voice=Inv": 1}, "form": "dakake", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Masc|Number=Plur", "best_count": 1, "counts": {"Gender=Masc|Number=Plur": 1}, "form": "dibixodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "dineigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Mood=Ind|Person[erg]=3|VerbForm=Fin|Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Person[erg]=3|VerbForm=Fin|Voice=Appl": 1}, "form": "dowediteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Masc|Number=Sing|Person=1", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person=1|PronType=Prs": 1}, "form": "ee", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "_", "best_count": 1, "counts": {"PronType=Ind": 1}, "form": "eliodi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Voice=Appl", "best_count": 1, "counts": {"Voice=Appl": 1}, "form": "eniteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin", "best_count": 1, "counts": {"Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin": 1}, "form": "eteeyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin", "best_count": 1, "counts": {"Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin": 1}, "form": "eteyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Number=Sing|Person[psor]=2": 1}, "form": "ganaaginaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|Person[psor]=2": 1}, "form": "ganigotGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "ganioxoa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- ... and 42 more

### low_evidence_prontype (19)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "adi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ani", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "form": "ee", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Ind", "best_count": 1, "counts": {"Ind": 1}, "form": "eliodi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idiwa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idowa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ijoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ijowa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ina", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGajo", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGana", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "naGana", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "niGidiwa", "share": 1.0, "total": 1, "upos": "DET"}`
- ... and 4 more

### low_evidence_lemma_prontype (4)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "na", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGida", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGidi", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGijo", "share": 1.0, "total": 1, "upos": "PRON"}`

### low_evidence_tag_to_prontype (7)
- `{"best": "Dem", "best_count": 2, "counts": {"Dem": 2}, "raw_tag": "D", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Dem", "best_count": 3, "counts": {"Dem": 3}, "raw_tag": "DAPL", "share": 1.0, "total": 3, "upos": "DET"}`
- `{"best": "Dem", "best_count": 4, "counts": {"Dem": 4}, "raw_tag": "DAPL", "share": 1.0, "total": 4, "upos": "PRON"}`
- `{"best": "Prs", "best_count": 3, "counts": {"Prs": 3}, "raw_tag": "PRO", "share": 1.0, "total": 3, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "PRO$", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Ind", "best_count": 2, "counts": {"Ind": 2}, "raw_tag": "Q", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Ind", "best_count": 1, "counts": {"Dem": 1, "Ind": 1}, "raw_tag": "Q", "share": 0.5, "total": 2, "upos": "DET"}`

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment is UID-only: gold `sent_uid` must match JSON sentence `uid`.
- Token alignment ignores punctuation and MWT lines.
- Source filenames follow stable source identifiers: `ped-gramm`, `hil-data`, and `van-data`.
