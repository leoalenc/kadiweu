# Gold-derived overrides report

## Summary

- Gold sentences: **198**
- JSON sentences: **206**
- UID-matched sentence pairs: **198**
- Usable aligned sentence pairs: **197**
- UID-matched but rejected: **1**
- `lemma_overrides`: **109**
- `form_feat_overrides`: **91**
- `prontype_overrides`: **30**
- `lemma_prontype_overrides`: **3**
- `tag_to_default_prontype`: **5**
## Review items

### json_alignment_issues (2)
- `{"gold_count": 7, "gold_forms": ["eyodi", "dowediteloco", "naodigijedi", "micoataGa", "daGa", "me", "lionigipi"], "json_count": 8, "json_forms": ["Eyodi", "dowediteloco", "nawodigijedi", "me@", "@icawataGa", "daGa", "me", "lionigipi"], "json_path": "$.pages[0].sentences[27]", "sent_id": "ped-gramm-28", "sent_uid": "ee1a1190-7803-404c-83f6-49d3ccf63b0d", "source_file": "../data/ped-gramm.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[55]", "mismatches": [["LiGeladi", "IiGeladi"]], "sent_id": "ped-gramm-56", "sent_uid": "edb3d8e5-d0c3-4ee6-97a8-ecb3afc84ded", "source_file": "../data/ped-gramm.json", "type": "token_form_mismatch"}`

### ambiguous_lemmas (11)
- `{"best": "dibixoGo", "best_count": 1, "counts": {"dibixoGo": 1, "dibixodi": 1}, "form": "dibixodi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "ani", "best_count": 2, "counts": {"ani": 2, "eniteloco": 1}, "form": "eniteloco", "share": 0.6667, "total": 3, "upos": "VERB"}`
- `{"best": "eyodi", "best_count": 3, "counts": {"eyodi": 3, "iodi": 1}, "form": "eyodi", "share": 0.75, "total": 4, "upos": "NOUN"}`
- `{"best": "ini", "best_count": 2, "counts": {"idinitibeci": 1, "ini": 2}, "form": "idinitibeci", "share": 0.6667, "total": 3, "upos": "VERB"}`
- `{"best": "ixagodi", "best_count": 1, "counts": {"ixagodi": 1, "xagodi": 1}, "form": "ixagodi", "share": 0.5, "total": 2, "upos": "VERB"}`
- `{"best": "taGagi", "best_count": 1, "counts": {"pegi": 1, "taGagi": 1}, "form": "jipecaGataGagi", "share": 0.5, "total": 2, "upos": "VERB"}`
- `{"best": "liwenigi", "best_count": 1, "counts": {"liwenigi": 1, "wenigi": 1}, "form": "liwenigi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "lomigo", "best_count": 2, "counts": {"lomigo": 2, "omigo": 1}, "form": "lomigo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "niganaGacanajo", "best_count": 2, "counts": {"niganaGacanajo": 2, "niganagacanajo": 1}, "form": "niganaGacanajo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "initibece", "best_count": 1, "counts": {"initibece": 1, "ni": 1}, "form": "ninitibigiwaji", "share": 0.5, "total": 2, "upos": "VERB"}`
- `{"best": "wenigi", "best_count": 2, "counts": {"enigi": 1, "wenigi": 2}, "form": "niwenigi", "share": 0.6667, "total": 3, "upos": "NOUN"}`

### ambiguous_feats (30)
- `{"best": "Gender=Masc|Number=Sing", "best_count": 2, "counts": {"Gender=Masc|Number=Sing": 2, "_": 2}, "form": "akiidi", "share": 0.5, "total": 4, "upos": "NOUN"}`
- `{"best": "Gender=Fem", "best_count": 3, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 2, "Gender=Fem|PronType=Dem": 3}, "form": "ani", "share": 0.6, "total": 5, "upos": "DET"}`
- `{"best": "Mood=Ind|VerbForm=Fin|Voice=Inv", "best_count": 5, "counts": {"Mood=Ind|Number=Sing|Person=3|VerbForm=Fin": 1, "Mood=Ind|Number=Sing|Person=3|VerbForm=Fin|Voice=Inv": 2, "Mood=Ind|VerbForm=Fin|Voice=Inv": 5}, "form": "dapicoGo", "share": 0.625, "total": 8, "upos": "VERB"}`
- `{"best": "Gender=Masc|Number=Plur", "best_count": 1, "counts": {"Gender=Masc|Number=Plur": 1, "_": 1}, "form": "dibixodi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "PronType=Ind", "best_count": 6, "counts": {"PronType=Ind": 6, "_": 1}, "form": "eliodi", "share": 0.8571, "total": 7, "upos": "ADV"}`
- `{"best": "Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Person[erg]=1|Person[obj]=3|VerbForm=Fin|Voice=Appl": 1, "Mood=Ind|Person[erg]=3|Person[obj]=3|Typo=Yes|VerbForm=Fin|Voice=Appl": 1, "Voice=Appl": 1}, "form": "eniteloco", "share": 0.3333, "total": 3, "upos": "VERB"}`
- `{"best": "Gender=Masc|Mood=Ind|Number=Sing|Person=3|VerbForm=Fin", "best_count": 1, "counts": {"Gender=Masc|Mood=Ind|Number=Sing|Person=3|VerbForm=Fin": 1, "Gender=Masc|Mood=Ind|VerbForm=Fin": 1}, "form": "etidi", "share": 0.5, "total": 2, "upos": "VERB"}`
- `{"best": "Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1", "best_count": 2, "counts": {"Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1": 2, "_": 2}, "form": "eyodi", "share": 0.5, "total": 4, "upos": "NOUN"}`
- `{"best": "Number=Sing", "best_count": 2, "counts": {"Number=Sing": 2, "Number=Sing|Number[psor]=Sing|Person[psor]=1": 1}, "form": "iGonagi", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "Gender=Masc|Number=Sing", "best_count": 3, "counts": {"Gender=Masc|Number=Sing|PronType=Dem": 3, "Gender=Masc|PronType=Dem": 2, "PronType=Dem": 2}, "form": "idi", "share": 0.4286, "total": 7, "upos": "DET"}`
- `{"best": "Mood=Ind|VerbForm=Fin", "best_count": 2, "counts": {"Mood=Ind|Number=Sing|Person=1|VerbForm=Fin|Voice=Inv": 1, "Mood=Ind|VerbForm=Fin": 2}, "form": "idinitibeci", "share": 0.6667, "total": 3, "upos": "VERB"}`
- `{"best": "Gender=Masc|Number=Sing", "best_count": 1, "counts": {"Gender=Masc|Number=Plur|PronType=Dem": 1, "Gender=Masc|Number=Sing|PronType=Dem": 1}, "form": "ijowa", "share": 0.5, "total": 2, "upos": "DET"}`
- `{"best": "Gender[obj]=Fem|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 4, "counts": {"Gender[obj]=Fem|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 4, "Mood=Ind|Number[erg]=Sing|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitege", "share": 0.5, "total": 8, "upos": "VERB"}`
- `{"best": "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 8, "counts": {"Gender[obj]=Masc|Mood=Ind|Number[erg]=Sing|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 1, "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 8, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitegi", "share": 0.7273, "total": 11, "upos": "VERB"}`
- `{"best": "Gender=Fem|Number=Plur", "best_count": 1, "counts": {"Gender=Fem|Number=Plur": 1, "_": 1}, "form": "iwaalepodi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- ... and 15 more

### ambiguous_prontype (0)
_None_

### ambiguous_lemma_prontype (0)
_None_

### ambiguous_tag_to_prontype (1)
- `{"best": "Ind", "best_count": 5, "counts": {"Dem": 2, "Ind": 5}, "raw_tag": "Q", "share": 0.7143, "total": 7, "upos": "DET"}`

### low_evidence_lemmas (78)
- `{"best": "ida", "best_count": 1, "counts": {"ida": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "aditaGa", "best_count": 1, "counts": {"aditaGa": 1}, "form": "aditaGa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "akaami", "best_count": 1, "counts": {"akaami": 1}, "form": "akaami", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "biju", "best_count": 1, "counts": {"biju": 1}, "form": "bejoli", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "bijo", "best_count": 1, "counts": {"bijo": 1}, "form": "bijo", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "bijotedi", "best_count": 1, "counts": {"bijotedi": 1}, "form": "bijotedi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "biju", "best_count": 1, "counts": {"biju": 1}, "form": "biju", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "codaa", "best_count": 1, "counts": {"codaa": 1}, "form": "codaa", "share": 1.0, "total": 1, "upos": "CCONJ"}`
- `{"best": "apiko", "best_count": 1, "counts": {"apiko": 1}, "form": "dapikoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "apicoGo", "best_count": 1, "counts": {"apicoGo": 1}, "form": "dapipocoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "dineigi", "best_count": 1, "counts": {"dineigi": 1}, "form": "dineigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "dowediteloco", "best_count": 1, "counts": {"dowediteloco": 1}, "form": "dowediteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "eetaGa", "best_count": 1, "counts": {"eetaGa": 1}, "form": "eetaGa", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "et", "best_count": 1, "counts": {"et": 1}, "form": "eteeyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "et", "best_count": 1, "counts": {"et": 1}, "form": "eteyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- ... and 63 more

### low_evidence_feats (78)
- `{"best": "Gender=Fem|Number=Sing", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Gender=Fem|Number=Sing", "best_count": 1, "counts": {"Gender=Fem|Number=Sing|PronType=Dem": 1}, "form": "aditaGa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Number=Plur", "best_count": 1, "counts": {"Number=Plur|PronType=Prs": 1}, "form": "akaami", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Number=Plur", "best_count": 1, "counts": {"Number=Plur": 1}, "form": "bejoli", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Number=Sing", "best_count": 1, "counts": {"Number=Sing": 1}, "form": "bijo", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Number=Plur", "best_count": 1, "counts": {"Number=Plur": 1}, "form": "bijotedi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Number=Sing", "best_count": 1, "counts": {"Number=Sing": 1}, "form": "biju", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "codaa", "share": 1.0, "total": 1, "upos": "CCONJ"}`
- `{"best": "Mood=Ind|Number=Plur|VerbForm=Fin|Voice=Inv", "best_count": 1, "counts": {"Mood=Ind|Number=Plur|VerbForm=Fin|Voice=Inv": 1}, "form": "dapikoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Mood=Ind|Typo=Yes|VerbForm=Fin|Voice=Inv", "best_count": 1, "counts": {"Mood=Ind|Typo=Yes|VerbForm=Fin|Voice=Inv": 1}, "form": "dapipocoGo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "_", "best_count": 1, "counts": {"_": 1}, "form": "dineigi", "share": 1.0, "total": 1, "upos": "NOUN"}`
- `{"best": "Mood=Ind|Person[erg]=3|VerbForm=Fin|Voice=Appl", "best_count": 1, "counts": {"Mood=Ind|Person[erg]=3|VerbForm=Fin|Voice=Appl": 1}, "form": "dowediteloco", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Number=Sing|Person=1", "best_count": 1, "counts": {"Number=Sing|Person=1|PronType=Prs": 1}, "form": "eetaGa", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin", "best_count": 1, "counts": {"Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin": 1}, "form": "eteeyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- `{"best": "Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin", "best_count": 1, "counts": {"Gender=Fem|Mood=Ind|Number=Sing|Person=1|VerbForm=Fin": 1}, "form": "eteyo", "share": 1.0, "total": 1, "upos": "VERB"}`
- ... and 63 more

### low_evidence_prontype (15)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ada", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "aditaGa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "form": "akaami", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "form": "eetaGa", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "idowa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ijotaGa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "ijotawece", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "nGida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "niGidi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "niGinoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "nigidiwa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "form": "nigijoa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "form": "oko", "share": 1.0, "total": 1, "upos": "PRON"}`

### low_evidence_lemma_prontype (7)
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "aditaGa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "lemma": "eetaGa", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "ida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "ijotaGa", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGida", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGidi", "share": 1.0, "total": 1, "upos": "DET"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "lemma": "niGijo", "share": 1.0, "total": 1, "upos": "DET"}`

### low_evidence_tag_to_prontype (2)
- `{"best": "Prs", "best_count": 1, "counts": {"Prs": 1}, "raw_tag": "DAPL", "share": 1.0, "total": 1, "upos": "PRON"}`
- `{"best": "Dem", "best_count": 1, "counts": {"Dem": 1}, "raw_tag": "PRO$", "share": 1.0, "total": 1, "upos": "DET"}`

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment is UID-only: gold `sent_uid` must match JSON sentence `uid`.
- Token alignment ignores punctuation and MWT lines.
- Source filenames follow stable source identifiers: `ped-gramm`, `hil-data`, and `van-data`.
