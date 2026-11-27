# Kadiwéu *et* morphology and `NumClass`

This package adds a dedicated morphology analyzer for Kadiwéu D-elements and *et* verbs. It preserves the converter's general override mechanism for exceptional token-level decisions, while keeping productive morphology and source evidence in a separate inventory.

## Evidence and analysis policy

The TBP lexicon extractor uses the existing `KadiweuLexicon` reader and selects entries whose first morpheme is `et` tagged `v`. Headwords and variants retain directly associated segmentation. Conjugation paradigms are recorded as surface forms without inheriting the headword segmentation, because a paradigm form can be homographic with a separately analyzed form (for example, `etee`). Griffiths extraction produces contextual candidates for human review; it does not presume that every `et`-initial string is a verb.

The morphology module uses explicit TBP splits first, then registered analyses, then productive form templates. In *et* forms, `Ncl` roots `da`, `ni`, `na`, `di`, `jo`, and `ca` yield `NumClass=Standing`, `Sitting`, `Coming`, `Lying`, `Going`, and `Absent`, respectively. `Gnr` supplies gender. Incorporated personal pronouns such as `ee`, `eeyo`, `akaami`, and `oko` yield person/number where their form is recognized; they do not by themselves imply `NumClass`. The `NumClass` feature is added to D-elements (including pronoun-like D elements) and to *et* verbs with classifier incorporation, not to nouns based on an unsupported tentative annotation.

## Rebuilding the resources

From the repository root, with the TBP lexicon export at `data/lexicon-kadiweu.json`:

```sh
python3 src/extract_griffiths_et_forms.py data/Griffiths-2002.pdf \
  -o data/derived/griffiths_et_candidates.json
python3 src/extract_et_forms_from_lexicon.py data/lexicon-kadiweu.json \
  -o data/derived/et_forms_from_tbp_lexicon.json
python3 src/consolidate_et_morphology.py \
  --griffiths data/derived/griffiths_et_candidates.json \
  --lexicon data/derived/et_forms_from_tbp_lexicon.json \
  -o data/resources/kadiweu_et_morphology.json
```

If the Griffiths PDF is unavailable, omit `--griffiths`; the TBP lexicon remains usable. The Griffiths output contains unreviewed candidates and short contexts and should be adjudicated against the dictionary before it is treated as a confirmed analysis.

## Converter integration and existing CoNLL-U

`src/kadiweu_json_to_conllu.py` calls the dedicated module after the existing feature inference and correction steps. The default resource path is `data/resources/kadiweu_et_morphology.json` relative to the project root. To enrich an existing file while keeping the original:

```sh
python3 src/kadiweu_et_morphology.py input.conllu \
  --inventory data/resources/kadiweu_et_morphology.json \
  -o output.numclass.conllu
```

The enrichment command moves tentative `MISC NumClass` values to `FEATS` only on eligible D-element and *et* verb rows, removes the MISC key, and fills missing features from morphology. Review auto-generated results against the source analysis, especially where the TBP segmentation or paradigm record is incomplete.

## Current export snapshot

The included extracted lexicon inventory was generated from the updated TBP JSON export supplied with this work. The example enriched CoNLL-U is derived from the attached 917-row test file. It added 117 `NumClass` values, moved 6 existing tentative values from MISC, removed 7 MISC `NumClass` values, and identified 13 *et* verb rows for enrichment. The `etee` and `eteyo` analyses retain person/number without `NumClass`; `etadi`, `etini`, and `etijo` have classifier analyses.
