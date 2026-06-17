# Gold-derived overrides report

## Summary

- Gold sentences: **96**
- JSON sentences: **204**
- UID-matched sentence pairs: **96**
- Usable aligned sentence pairs: **93**
- UID-matched but rejected: **3**
- `lemma_overrides`: **108**
- `form_feat_overrides`: **111**
- `prontype_overrides`: **36**
- `lemma_prontype_overrides`: **6**
- `tag_to_default_prontype`: **9**
## Review items

### json_alignment_issues (4)
- `{"gold_count": 7, "gold_forms": ["eyodi", "dowediteloco", "naodigijedi", "micoataGa", "daGa", "me", "lionigipi"], "json_count": 8, "json_forms": ["Eyodi", "dowediteloco", "naodigijedi", "me@", "@icawataGa", "daGa", "me", "lionigipi"], "json_path": "$.pages[0].sentences[27]", "sent_id": "ped-gramm-28", "sent_uid": "ee1a1190-7803-404c-83f6-49d3ccf63b0d", "source_file": "../data/gramatica-pedagogica.json", "type": "token_count_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "dakake", "lojedi"], "json_count": 5, "json_forms": ["Etogo", "ane@", "@iwaGadi", "adakake", "lojedi"], "json_path": "$.pages[0].sentences[4]", "sent_id": "hil-data-5", "sent_uid": "e349508c-4d86-48b8-9918-057988755e77", "source_file": "../data/dados-hil.json", "type": "token_count_mismatch"}`
- `{"gold_count": 6, "gold_forms": ["Etogo", "ane", "iwaGadi", "aG", "dakake", "loojedi"], "json_count": 5, "json_forms": ["Etogo", "ane", "iwaGadi", "adakake", "loojedi"], "json_path": "$.pages[0].sentences[5]", "sent_id": "hil-data-6", "sent_uid": "1d10c633-e74d-4e27-ac23-6b6b2dde9647", "source_file": "../data/dados-hil.json", "type": "token_count_mismatch"}`
- `{"json_path": "$.pages[0].sentences[29]", "mismatches": [["niGijo", "nGijo"]], "sent_id": "van-data-30", "sent_uid": "0c7e64fb-f070-4faa-a12a-c110cdf4bf16", "source_file": "../data/van-data.json", "type": "token_form_mismatch"}`

### ambiguous_lemmas (10)
- `{"best": "dakake", "best_count": 2, "counts": {"akake": 1, "dakake": 2}, "form": "dakake", "share": 0.6667, "total": 3, "upos": "ADJ"}`
- `{"best": "eyodi", "best_count": 3, "counts": {"eyodi": 3, "iodi": 1}, "form": "eyodi", "share": 0.75, "total": 4, "upos": "NOUN"}`
- `{"best": "iwaalo", "best_count": 1, "counts": {"iwaalepodi": 1, "iwaalo": 1}, "form": "iwaalepodi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "liwenigi", "best_count": 1, "counts": {"liwenigi": 1, "wenigi": 1}, "form": "liwenigi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "odajo", "best_count": 1, "counts": {"odaajo": 1, "odajo": 1}, "form": "lodajo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "omigo", "best_count": 1, "counts": {"lomigo": 1, "omigo": 1}, "form": "lomigo", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "oojedi", "best_count": 3, "counts": {"loojedi": 1, "oojedi": 3}, "form": "loojedi", "share": 0.75, "total": 4, "upos": "NOUN"}`
- `{"best": "niganaGacanajo", "best_count": 2, "counts": {"niganaGacanajo": 2, "niganagacanajo": 1}, "form": "niganaGacanajo", "share": 0.6667, "total": 3, "upos": "NOUN"}`
- `{"best": "enigi", "best_count": 1, "counts": {"enigi": 1, "wenigi": 1}, "form": "niwenigi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "wetiGa", "best_count": 3, "counts": {"wetiGa": 3, "wetiga": 1}, "form": "wetiGa", "share": 0.75, "total": 4, "upos": "NOUN"}`

### ambiguous_feats (8)
- `{"best": "AdvType=Loc|PronType=Dem", "best_count": 1, "counts": {"AdvType=Loc|Deixis=Remt|PronType=Dem": 1, "AdvType=Loc|PronType=Dem": 1}, "form": "digoida", "share": 0.5, "total": 2, "upos": "ADV"}`
- `{"best": "_", "best_count": 2, "counts": {"PronType=Ind": 2, "_": 2}, "form": "eliodi", "share": 0.5, "total": 4, "upos": "ADV"}`
- `{"best": "Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1", "best_count": 2, "counts": {"Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1": 2, "_": 2}, "form": "eyodi", "share": 0.5, "total": 4, "upos": "NOUN"}`
- `{"best": "Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl", "best_count": 4, "counts": {"Gender[obj]=Masc|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 4, "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl": 2}, "form": "ipegitegi", "share": 0.6667, "total": 6, "upos": "VERB"}`
- `{"best": "Gender=Fem|Number=Plur", "best_count": 1, "counts": {"Gender=Fem|Number=Plur": 1, "_": 1}, "form": "iwaalepodi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Person[psor]=3", "best_count": 1, "counts": {"Gender=Masc|Number=Sing|Person[psor]=3": 1, "Person[psor]=3": 1}, "form": "lidi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Gender=Fem|Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Gender=Fem,Masc|Number=Plur|Person[psor]=3": 1, "Gender=Fem|Number=Plur|Person[psor]=3": 1}, "form": "lionigipi", "share": 0.5, "total": 2, "upos": "NOUN"}`
- `{"best": "Number=Plur|Person[psor]=3", "best_count": 1, "counts": {"Number=Plur|Person[psor]=3": 1, "_": 1}, "form": "lotiidi", "share": 0.5, "total": 2, "upos": "NOUN"}`

### ambiguous_prontype (0)
_None_

### ambiguous_lemma_prontype (0)
_None_

### ambiguous_tag_to_prontype (1)
- `{"best": "Ind", "best_count": 1, "counts": {"Dem": 1, "Ind": 1}, "raw_tag": "Q", "share": 0.5, "total": 2, "upos": "DET"}`

### low_evidence_lemmas (0)
_None_

### low_evidence_feats (0)
_None_

### low_evidence_prontype (0)
_None_

### low_evidence_lemma_prontype (0)
_None_

### low_evidence_tag_to_prontype (0)
_None_

## Notes

- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.
- In a later step, this can be made residual relative to converter heuristics.
- Sentence alignment is UID-only: gold `sent_uid` must match JSON sentence `uid`.
- Token alignment ignores punctuation and MWT lines.
