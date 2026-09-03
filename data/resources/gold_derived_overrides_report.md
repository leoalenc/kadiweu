# Gold-derived overrides report

## Summary

- Gold sentences: **129**
- JSON sentences: **206**
- UID-matched sentence pairs: **129**
- Usable aligned sentence pairs: **127**
- UID-matched but rejected: **2**
- `lemma_overrides`: **79**
- `form_feat_overrides`: **75**
- `prontype_overrides`: **25**
- `lemma_prontype_overrides`: **3**
- `tag_to_default_prontype`: **4**
## Review items

### json_alignment_issues (6)
- `{"gold_count": 7, "gold_forms": ["eyodi", "dowediteloco", "naodigijedi", "micoataGa", "daGa", "me", "lionigipi"], "json_count": 8, "json_forms": ["Eyodi", "dowediteloco", "nawodigijedi", "me@", "@icawataGa", "daGa", "me", "lionigipi"], "json_path": "$.pages[0].sentences[27]", "sent_id": "ped-gramm-28", "sent_uid": "ee1a1190-7803-404c-83f6-49d3ccf63b0d", "source_file": "../data/ped-gramm.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[12]", "mismatches": [["lomigo", "lomiigo"], ["noatece", "niwatece"]], "sent_id": "van-data-13", "sent_uid": "e9806e26-701d-4f5f-9ca9-63216cccf3d0", "source_file": "../data/van-data.json", "type": "token_form_mismatch"}`
- `{"gold_count": 4, "gold_forms": ["niGijo", "niganigawaanigi", "lomigo", "niwatece"], "json_count": 8, "json_forms": ["Nigaanigawaanigi", "idei", "me@", "@adi", "niwatece", "ane", "adi", "nomiigo"], "json_path": "$.pages[0].sentences[14]", "sent_id": "van-data-15", "sent_uid": "4c41fdf6-0c48-4eb6-91f7-121c21f3e2a7", "source_file": "../data/van-data.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[16]", "mismatches": [["Eyo", "Eeyo"]], "sent_id": "van-data-17", "sent_uid": "86f5c128-e931-4443-90cc-2359748ed69f", "source_file": "../data/van-data.json", "type": "token_form_mismatch"}`
- `{"json_path": "$.pages[0].sentences[29]", "mismatches": [["lodajo", "lodaajo"]], "sent_id": "van-data-30", "sent_uid": "0c7e64fb-f070-4faa-a12a-c110cdf4bf16", "source_file": "../data/van-data.json", "type": "token_form_mismatch"}`
- `{"json_path": "$.pages[0].sentences[41]", "mismatches": [["ijowa", "ijoa"]], "sent_id": "van-data-42", "sent_uid": "44646324-eb90-42f0-b944-21f0452109e2", "source_file": "../data/van-data.json", "type": "token_form_mismatch"}`

### ambiguous_lemmas (9)
- `{"best": "eyo", "best_count": 1, "counts": {"eeyo": 1, "eyo": 1}, "form": "eeyo", "share": 0.5, "total": 2, "upos": "PRON"}`
- `{"best": "eyo", "best_count": 1, "counts": {"eeyo": 1, "eyo": 1}, "form": "eyo", "share": 0.5, "total": 2, "upos": "PRON"}`
- `{"best": "eyodi", "best_count": 3, "counts": {"eyodi": 3, "iodi": 1}, "form": "eyodi", "share": 0.75, "total": 4, "upos": "NOUN"}`
- `{"best": "liwenigi", "best_count": 1, "counts": {"liwenigi": 1, "wenigi": 1}, "form": "liwenigi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "odajo", "best_count": 1, "counts": {"odaajo": 1, "odajo": 1}, "form": "lodajo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "lomigo", "best_count": 2, "counts": {"lomigo": 2, "omigo": 1, "omiigo": 2}, "form": "lomigo", "share": 0.4, "total": 5, "upos": "NOUN"}`
- `{"best": "niganaGacanajo", "best_count": 2, "counts": {"niganaGacanajo": 2, "niganagacanajo": 1}, "form": "niganaGacanajo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "wenigi", "best_count": 2, "counts": {"enigi": 1, "wenigi": 2}, "form": "niwenigi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "wetiGa", "best_count": 3, "counts": {"wetiGa": 3, "wetiga": 1}, "form": "wetiGa", "share": 0.75, "total": 4, "upos": "NOUN"}`

### ambiguous_feats (14)
- `{"best": "_", "best_count": 2, "counts": {"Gender=Masc|Number=Sing": 1, "_": 2}, "form": "akiidi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "Mood=Ind|Number=Sing|Person=3|VerbForm=Fin|Voice=Inv", "best_count": 2, "counts": {"Mood=Ind|Number=Sing|Person=3|VerbForm=Fin": 1, "Mood=Ind|Number=Sing|Person=3|VerbForm=Fin|Voice=Inv": 2, "Mood=Ind|VerbForm=Fin|Voice=Inv": 1}, "form": "dapicoGo", "share": 0.5, "total": 4, "upos": "VERB"}`
- `{"best": "PronType=Ind", "best_count": 2, "counts": {"PronType=Ind": 2, "_": 1}, "form": "eliodi", "share": 0.6667, "total": 3, "upos": "ADV"}`
- `{"best": "Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1", "best_count": 2, "counts": {"Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1": 2, "_": 2}, "form": "eyodi", "share": 0.5, "total": 4, "upos": "NOUN"}`
- `{"best": "Gender[obj]=Fem|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 4, "counts": {"Gender[obj]=Fem|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 4, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitege", "share": 0.6667, "total": 6, "upos": "VERB"}`
- `{"best": "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 8, "counts": {"Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 8, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitegi", "share": 0.8, "total": 10, "upos": "VERB"}`
- `{"best": "Gender=Fem|Number=Plur", "best_count": 1, "counts": {"Gender=Fem|Number=Plur": 1, "_": 1}, "form": "iwaalepodi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1, "Person[psor]=3": 1}, "form": "lidi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Person[psor]=3|Typo=Yes", "best_count": 1, "counts": {"Person[psor]=3": 1, "Person[psor]=3|Typo=Yes": 1}, "form": "ligeladi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Gender=Fem,Masc|Number=Plur|Person[psor]=3": 1, "Gender=Fem|Number=Plur|Person[psor]=3": 1}, "form": "lionigipi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Sing|Person[psor]=3", "best_count": 2, "counts": {"Gender=Fem|Number=Sing|Person[psor]=3": 2, "Person[psor]=3": 1}, "form": "lomiigo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=3", "best_count": 4, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 4, "Number=Sing|Person[psor]=3": 1}, "form": "lotaGa", "share": 0.8, "total": 5, "upos": "NOUN"}`
- `{"best": "_", "best_count": 2, "counts": {"Number=Plur|Person[psor]=3": 1, "Person[psor]=3": 1, "_": 2}, "form": "lotiidi", "share": 0.5, "total": 4, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing", "best_count": 2, "counts": {"Gender=Masc|Number=Sing": 2, "_": 2}, "form": "niweiigi", "share": 0.5, "total": 4, "upos": "NOUN"}`

### ambiguous_prontype (0)
_None_

### ambiguous_lemma_prontype (0)
_None_

### ambiguous_tag_to_prontype (0)
_None_

### low_evidence_lemmas (64)
- `{"best": "ida", "best_count": 1, "counts": {"ida": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "ini", "best_count": 1, "counts": {"ini": 1}, "form": "ani", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "codaa", "best_count": 1, "counts": {"codaa": 1}, "form": "codaa", "share": 1.0, "total": 1, "upos": "CCONJ"}`
- `{"best": "apiko", "best_count": 1, "counts": {"apiko": 1}, "form": "dapikoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "dibixoGo", "best_count": 1, "counts": {"dibixoGo": 1}, "form": "dibixodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "dineigi", "best_count": 1, "counts": {"dineigi": 1}, "form": "dineigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "dowediteloco", "best_count": 1, "counts": {"dowediteloco": 1}, "form": "dowediteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "eniteloco", "best_count": 1, "counts": {"eniteloco": 1}, "form": "eniteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "et", "best_count": 1, "counts": {"et": 1}, "form": "eteeyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "et", "best_count": 1, "counts": {"et": 1}, "form": "eteyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "et", "best_count": 1, "counts": {"et": 1}, "form": "etidi", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "et", "best_count": 1, "counts": {"et": 1}, "form": "etijo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "aaginaGa", "best_count": 1, "counts": {"aaginaGa": 1}, "form": "gaanaginaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "aaginaGa", "best_count": 1, "counts": {"aaginaGa": 1}, "form": "ganaaginaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "aaginaGa", "best_count": 1, "counts": {"aaginaGa": 1}, "form": "ganaginaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- ... and 49 more

### low_evidence_feats (64)
- `{"best": "Gender=Fem|Number=Sing", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Gender=Fem|Number=Sing", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "ani", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "codaa", "share": 1.0, "total": 1, "upos": "CCONJ"}`
- `{"best": "Mood=Ind|Number=Plur|VerbForm=Fin|Voice=Inv", "best_count": 1, "counts": {"Mood=Ind|Number=Plur|VerbForm=Fin|Voice=Inv": 1}, "form": "dapikoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Masc|Number=Plur", "best_count": 1, "counts": {"Gender=Masc|Number=Plur": 1}, "form": "dibixodi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "dineigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Mood=Ind|Person[erg]=3|VerbForm=Fin|Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Person[erg]=3|VerbForm=Fin|Voice=Appl": 1}, "form": "dowediteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Voice=Appl", "best_count": 1, "counts": {"Voice=Appl": 1}, "form": "eniteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin", "best_count": 1, "counts": {"Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin": 1}, "form": "eteeyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin", "best_count": 1, "counts": {"Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin": 1}, "form": "eteyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Masc|Mood=Ind|Number=Sing|Person=3|VerbForm=Fin", "best_count": 1, "counts": {"Gender=Masc|Mood=Ind|Number=Sing|Person=3|VerbForm=Fin": 1}, "form": "etidi", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Masc|Mood=Ind|Number=Sing|Person=3", "best_count": 1, "counts": {"Gender=Masc|Mood=Ind|Number=Sing|Person=3": 1}, "form": "etijo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "gaanaginaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Number=Sing|Person[psor]=2": 1}, "form": "ganaaginaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing|Person[psor]=2", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=2": 1}, "form": "ganaginaGa", "share": 1.0, "total": 1, "upos": "NOUN"}`
- ... and 49 more

### low_evidence_prontype (13)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ani", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idowa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ijoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ijotawece", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ijowa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "nGida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "niGijoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "niGinoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "nigijoa", "share": 1.0, "total": 1, "upos": "DET"}`

### low_evidence_lemma_prontype (4)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "ida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGidi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGijo", "share": 1.0, "total": 1, "upos": "DET"}`

### low_evidence_tag_to_prontype (3)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "PRO$", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Ind", "best_count": 2, "counts": {"Ind": 2}, "raw_tag": "Q", "share": 1.0, "total": 2, "upos": "ADV"}`
- `{"best": "Ind", "best_count": 2, "counts": {"Dem": 1, "Ind": 2}, "raw_tag": "Q", "share": 0.6667, "total": 3, "upos": "DET"}`

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment is UID-only: gold `sent_uid` must match JSON sentence `uid`.
- Token alignment ignores punctuation and MWT lines.
- Source filenames follow stable source identifiers: `ped-gramm`, `hil-data`, and `van-data`.
