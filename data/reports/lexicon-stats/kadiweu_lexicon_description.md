# Describing the Kadiwéu lexicon

## Scope and interpretation

The lexicon discussed here contains **7,360 records**. It is a substantial source of lexical, grammatical, and morphological information, but its records should not be treated as a fully deduplicated dictionary. Counts of repeated names describe repeated **record spellings**, not necessarily repeated lexical items. A repeated spelling can correspond to different tags, meanings, or morphological analyses. The summary statistics were computed by exact string comparison: capitalization, diacritics, whitespace, and characters such as `G` and `ǥ` are preserved.

## Illustrative examples

| Category | Example | What it illustrates |
|---|---|---|
| Lexical detail | *eǥyadi* is tagged `N`, glossed “macaco bugio,” and has the scientific-name attribute `allouatta caraya`. | Entries can include grammatical information, definitions, senses, and domain-specific metadata. |
| Morphological analysis | *aGeewi* is tagged `NEG+PRO+ADJ` and segmented as `aG` (`Neg`, `functional: true`) + `ee` (`Pro`, `functional: true`) + `ewi` (`a`). | The lexicon records components and grammatical features. This entry has no definition or sense, so the morphological analysis is more informative than the glossing. |
| One spelling, different analyses or meanings | *ida* occurs six times. Its records include `D` entries glossed “está lá” and “aquele lá, aí,” and `Q` entries glossed “este.” Some records also analyze it as `i` + `da`. | A shared written form may have different tags, meanings, or analyses. Review is needed before deciding whether records should be consolidated. |
| Exact duplicate content | *diniǥeke* occurs twice with the same information and definition: “mediador (alguém que vai na frente para representar, pode ser capitão novo).” | These records differ in record identity but have the same lexical content, making this a clear example of redundancy. |
| Quasi-redundancy | *wetiǥa* occurs with “pedra, morro” and in three records with “pedra.” | The records overlap, but “pedra, morro” is broader than “pedra”; deciding whether they are duplicates or separate sense records requires editorial judgment. |

## What the inventory counts show

- **7,360 records** have a nonempty name; none are missing a name.
- There are **6,752 distinct exact name strings**. Of these, **451 names** occur more than once, covering **1,059 records**. Those repeated-name groups contain **608 extra records** beyond one record per distinct name.
- Among repeated-name groups, **175** have multiple tags, **392** have multiple definition-or-sense signatures, and **418** have multiple tag-and-meaning combinations. These categories overlap; they should not be added together.
- **55 repeated-name groups** contain records whose lexical content is redundant after record IDs and audit/history fields are ignored. These groups contain **92 matching-content record pairs**. This is a review signal, not a recommendation to delete records automatically.
- **818 records** contain a `morphemes` field; **815** have nonempty morpheme data and **3** have an empty or null value. Thus about **11%** of all records have a populated morphemes field. Other records may still have useful lexical information.

## Strengths and areas for improvement

The lexicon provides a large lexical inventory and can combine part-of-speech or grammatical labels, Portuguese definitions, senses, morpheme segmentation, functional features, and specialized metadata. The entry for *aGeewi*, for instance, exposes a three-part analysis and marks two components as functional.

Coverage and record structure are uneven. Some analyzed entries lack definitions or senses, while many entries have no populated morpheme analysis. Repeated names can reflect legitimate differences in meaning or analysis, but the inventory also reveals exact duplicate content and near-duplicates. These cases merit review and clearer sense/entry organization; exact-name repetition alone is not enough to justify merging records.

## Summary

> The Kadiwéu lexicon contains 7,360 records and provides lexical, grammatical, and, for a subset of entries, morphological information. Entries may include part-of-speech labels, Portuguese definitions and senses, morpheme analyses with grammatical features, and specialized attributes. The data are not fully normalized: 451 exact name strings occur in multiple records, sometimes with different tags or meanings, and some repeated-name groups contain identical or near-identical lexical content. These patterns indicate areas for curation, although repeated spellings cannot be equated automatically with duplicate lexical items. Morpheme analyses are present for 815 entries, so morphological coverage is useful but limited to a subset of the lexicon.

*Examples and figures above are based on the 7,360-entry `lexicon-kadiweu.json` analyzed by `kadiweu_lexicon_stats.py`. The statistics characterize records; they do not by themselves establish which records should be merged.*
