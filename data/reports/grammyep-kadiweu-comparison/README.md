# GrammYEP–Kadiwéu stimulus provenance analysis

## Purpose

This directory documents a reproducible comparison between the Portuguese
stimuli in the GrammYEP Nheengatu dataset and the Portuguese elicitation
material associated with three Kadiwéu datasets exported from the Tycho Brahe
Platform.

The immediate goal is to determine which Kadiwéu sentence records can be
related to stimuli in GrammYEP and to distinguish:

1. strict matches recoverable automatically from the Portuguese strings;
2. non-strict derivatives or variants that require linguistic adjudication;
3. cases for which a relationship is possible but not sufficiently secure;
4. records for which no defensible GrammYEP antecedent has been identified.

The analysis concerns **stimulus provenance**. A record classified as deriving
from GrammYEP need not express exactly the same proposition as its GrammYEP
antecedent. Some elicitation stimuli were structurally or semantically modified.

All manual decisions in the current files are a first-pass linguistic
adjudication and remain subject to researcher review.

---

## Input data

### GrammYEP

The Portuguese comparison source is:

`GraYrl-GraPor.txt`

Its structure consists of a GrammYEP sentence identifier (`SENT-n`), a
Nheengatu sentence, and one or more Portuguese equivalents.

The file contains:

- **142 GrammYEP base sentence records**;
- **346 Portuguese equivalent lines**;
- **187 distinct Portuguese strings after conservative normalization**.

A Portuguese string is not necessarily a unique key for a GrammYEP sentence.
In the current data, **29 normalized Portuguese strings correspond to more
than one GrammYEP `SENT-ID`**. Consequently, a Kadiwéu Portuguese stimulus may
be securely related to GrammYEP while its exact GrammYEP `SENT-ID` remains
ambiguous.

### Kadiwéu

Three current Tycho Brahe JSON exports are compared:

| source | records | DONE | REVIEW |
|---|---:|---:|---:|
| `van-data.json` | 75 | 69 | 6 |
| `hil-data.json` | 70 | 66 | 4 |
| `ped-gramm.json` | 61 | 54 | 7 |
| **Total** | **206** | **189** | **17** |

The short source labels used in the TSV files are `van`, `hil`, and `ped`.

The Portuguese string used for matching is the `pt-br` translation associated
with each Kadiwéu sentence record.

---

## Conservative normalization

The first matching stage deliberately uses only orthographic normalization.
It does **not** normalize lexical, grammatical, or semantic differences.

The normalization procedure is:

1. Unicode normalization to NFC;
2. Unicode-aware case folding;
3. removal of leading and trailing whitespace;
4. collapse of internal whitespace sequences;
5. removal of whitespace immediately before punctuation;
6. removal of sentence-final `.`, `?`, or `!`.

Thus differences such as the following remain genuine differences for the
automatic strict-matching stage:

- `é` versus `está`;
- `este` versus `esta`;
- `retrato` versus `fotografia`;
- `tu` versus `você`;
- presence versus absence of a subject pronoun or article.

This conservative policy is intentional: such relationships are evaluated
during linguistic adjudication rather than silently normalized away.

---

## Stage 1: strict matching

Each of the 206 Kadiwéu Portuguese strings is compared against the Portuguese
equivalents associated with all 142 GrammYEP base records.

Two strict categories are distinguished internally:

- `EXACT_RAW`: identical strings before normalization;
- `EXACT_NORMALIZED`: identical strings after the conservative normalization
  described above.

For corpus-level provenance accounting, these categories are combined as
strict matches.

### Strict-matching result

- exact/raw matches: **42/206**;
- exact/raw or conservatively normalized matches: **96/206 (46.60%)**.

By Kadiwéu source:

| source | records | strict matches | percentage |
|---|---:|---:|---:|
| `van` | 75 | 42 | 56.0% |
| `hil` | 70 | 46 | 65.7% |
| `ped` | 61 | 8 | 13.1% |

The 96 strict Kadiwéu records collectively cover **52 of the 142 GrammYEP base
`SENT-ID`s (36.62%)**.

Strict stimulus coverage by source is:

- `van`: 44 GrammYEP `SENT-ID`s;
- `hil`: 49;
- `ped`: 9.

The strict Vanda–Hilário stimulus intersection contains **44 `SENT-ID`s**.
This means that every GrammYEP `SENT-ID` reached by the strict Vanda matches is
also reached by the strict Hilário matches. It does not imply 44 literally
identical Kadiwéu sentences.

Because a normalized Portuguese equivalent may belong to multiple GrammYEP
items, the number of GrammYEP `SENT-ID`s covered can exceed the number of
matching Kadiwéu records.

---

## Stage 2: similarity-based candidate retrieval

The 110 Kadiwéu records without a strict match are compared with GrammYEP using
three string-similarity measures.

### Character similarity

`char_similarity` is the Python `difflib.SequenceMatcher` ratio computed over
the conservatively normalized Portuguese strings.

### Token Jaccard similarity

For normalized whitespace-delimited token sets `A` and `B`:

    token_jaccard = |A ∩ B| / |A ∪ B|

This measure captures lexical overlap independently of token order.

### Combined similarity

The retrieval score is:

    combined_similarity =
        0.75 * char_similarity +
        0.25 * token_jaccard

Character similarity therefore receives three times the weight of token-set
overlap.

The initial candidate-retrieval threshold is:

    combined_similarity >= 0.80

and up to five candidates are retained per unmatched Kadiwéu record.

The threshold is a **candidate-retrieval device**, not a linguistic definition
of derivation.

---

## Stage 3: adjudication of the 47 above-threshold records

The similarity procedure produced at least one candidate at or above 0.80 for
**47 distinct Kadiwéu records**. Because one Kadiwéu record can have multiple
candidate antecedents, the original candidate table contained more rows than
records.

Each of the 47 records was then inspected linguistically. The adjudication
considered together:

- the Kadiwéu sentence;
- its Portuguese stimulus/translation;
- all relevant GrammYEP candidate sentences;
- the corresponding Nheengatu sentence;
- neighboring or paradigmatically related GrammYEP examples where useful.

The similarity score was used for retrieval but did not determine the manual
decision.

First-pass result:

- `DERIVED_VARIANT`: **47**;
- `POSSIBLY_RELATED`: **0**;
- `INDEPENDENT_ORIGIN`: **0**.

Among these 47 records:

- `SAME_PROPOSITION`: **40**;
- `SEMANTIC_VARIANT`: **7**.

The distinction is important. `DERIVED_VARIANT` is a provenance judgment,
whereas `SAME_PROPOSITION` / `SEMANTIC_VARIANT` characterizes the semantic
relationship between the two stimuli.

---

## Stage 4: exhaustive adjudication of the 63 initially unresolved records

The remaining **63 records** had no candidate reaching the 0.80 combined-score
threshold. They were therefore subjected to a second linguistic pass.

For this pass, the 0.80 threshold was not treated as an exclusion criterion.
Each unresolved record was considered against the complete GrammYEP stimulus
inventory. This permits recovery of relationships obscured by substantial
surface changes, including lexical substitution, copular alternation,
relative-clause expansion, constituent reordering, or combinations of several
changes.

First-pass result for these 63 records:

- `DERIVED_VARIANT`: **44**;
- `POSSIBLY_RELATED`: **4**;
- `INDEPENDENT_ORIGIN`: **15**.

This result demonstrates why the 0.80 threshold must not be interpreted as a
boundary between GrammYEP-derived and independent material.

---

## Manual decision categories

### `DERIVED_VARIANT`

There is sufficient linguistic evidence to treat the Kadiwéu Portuguese
stimulus as derived from, or as a variant of, an identifiable GrammYEP
stimulus.

This category does not require semantic identity.

### `POSSIBLY_RELATED`

A GrammYEP antecedent is plausible, but the available evidence is not strong
enough to count the record as GrammYEP-derived without further researcher
review.

These records are excluded from the conservative provenance total.

### `INDEPENDENT_ORIGIN`

No defensible GrammYEP antecedent has been identified in the current
comparison.

This label is an analytical conclusion based on the available GrammYEP
material; it should not be interpreted as a claim that the complete historical
origin of the elicitation sentence has independently been established.

---

## Semantic relationship

For records with a selected GrammYEP antecedent, the following distinction is
used:

### `SAME_PROPOSITION`

The differences are compatible with treating the two stimuli as expressions
of the same basic proposition. Examples include article omission, overt versus
null subject pronouns, and some copular variants.

### `SEMANTIC_VARIANT`

The Kadiwéu stimulus is related to the GrammYEP stimulus but contains a
meaning-relevant modification, such as a change in person, number, deixis,
possessor, argument, or predicational content.

### `UNCERTAIN`

Reserved for cases in which the semantic relationship cannot yet be
classified securely.

---

## Variant types

The `variant_type` field provides a compact linguistic characterization of the
difference. Current labels include, among others:

- `ARTICLE`
- `COPULA`
- `DEMONSTRATIVE`
- `LEXICAL`
- `NUMBER`
- `PERSON`
- `POSSESSION`
- `PREPOSITION`
- `PRONOUN`
- `SUBJECT_OMISSION`
- `WORD_ORDER`
- `PREDICATE_ADDITION`
- `PREDICATE_REDUCTION`
- `RELATIVE_CLAUSE`
- `COMBINED`
- `OTHER`

Multiple labels may be joined with `|`, for example:

    COPULA|POSSESSION

The inventory is descriptive and may be refined during researcher review.

---

## Ambiguous GrammYEP antecedents

The Portuguese pivot does not always uniquely determine a GrammYEP
`SENT-ID`. If two or more GrammYEP items share the relevant Portuguese
equivalent and the current evidence does not justify choosing one, the
adjudication preserves the ambiguity rather than selecting an arbitrary ID.

For example:

    14|50|64

means that the provenance relationship is considered secure at the stimulus
level but the exact GrammYEP item cannot presently be distinguished among
`SENT-14`, `SENT-50`, and `SENT-64`.

This distinction is reflected in the confidence field.

---

## Confidence

Manual decisions receive one of three confidence levels:

- `HIGH`: the proposed relationship and antecedent are well supported;
- `MEDIUM`: the relationship is plausible or strong, but some aspect—often
  exact `SENT-ID` identification or the extent of the transformation—requires
  review;
- `LOW`: substantial uncertainty remains.

Confidence is distinct from string similarity. A low surface-similarity score
can coexist with high linguistic confidence, and a high similarity score does
not by itself establish historical or linguistic derivation.

All `MEDIUM` and `LOW` records are extracted into:

`grammyep_kadiweu_review_medium_low.tsv`

for prioritized researcher review.

---

## Similarity fields in the adjudication tables

For a manually selected GrammYEP antecedent, the following fields describe
that specific pair:

- `char_similarity`
- `token_jaccard`
- `combined_similarity`

The tables separately preserve the algorithm's highest-scoring candidate:

- `automatic_best_sent_id`
- `automatic_best_portuguese`
- `automatic_best_score`

This distinction is essential. The linguistically adjudicated antecedent need
not be the candidate with the highest string-similarity score.

For `INDEPENDENT_ORIGIN`, the adjudicated-antecedent similarity fields are
left blank because no antecedent has been selected. The automatic-best fields
are nevertheless retained to document what the retrieval algorithm considered
most similar.

---

## Audit fields

The adjudication tables retain:

- Kadiwéu source (`van`, `hil`, `ped`);
- source-local record index;
- Tycho sentence UID;
- Kadiwéu sentence;
- Kadiwéu Portuguese stimulus;
- adjudicated GrammYEP `SENT-ID`;
- corresponding Nheengatu sentence;
- GrammYEP Portuguese equivalent;
- all three pairwise similarity measures;
- automatic best candidate and score;
- manual decision;
- variant type;
- semantic relationship;
- confidence;
- adjudicator comment;
- review status.

The intention is to preserve both the computational evidence and the
linguistic reasoning rather than replacing one with the other.

---

## Current first-pass accounting

The complete 206-record Kadiwéu dataset currently partitions as follows:

| category | records | percentage |
|---|---:|---:|
| strict exact/normalized GrammYEP match | 96 | 46.60% |
| non-strict `DERIVED_VARIANT` | 91 | 44.17% |
| `POSSIBLY_RELATED` | 4 | 1.94% |
| `INDEPENDENT_ORIGIN` | 15 | 7.28% |
| **Total** | **206** | **100.00%** |

The conservative first-pass GrammYEP-related total is therefore:

    96 + 91 = 187 / 206 = 90.78%

The four `POSSIBLY_RELATED` records are **not** included in this figure.

If all four were subsequently accepted as derived, the corresponding upper
figure would be:

    191 / 206 = 92.72%

These percentages are provisional until researcher review of the manual
adjudication is complete.

---

## Interpretation of the 187 figure

The value **187/206 (90.78%)** should be interpreted as a first-pass,
conservative estimate of the number of Kadiwéu records that can currently be
related to GrammYEP by either:

1. strict Portuguese-string matching; or
2. manual linguistic adjudication of a non-strict relationship.

It should **not** be interpreted as meaning that 187 Kadiwéu sentences are
literal translations of 187 different GrammYEP sentences.

Reasons include:

- several Kadiwéu records may derive from the same GrammYEP stimulus;
- one Portuguese equivalent can correspond to multiple GrammYEP `SENT-ID`s;
- Vanda and Hilário share a substantial elicitation core;
- some derived stimuli are semantically modified rather than propositionally
  identical.

The unit counted in 187/206 is the **Kadiwéu sentence record**, not the number
of unique GrammYEP stimuli.

---

## Historical provenance and computational evidence

The string comparison and adjudication establish relationships observable in
the datasets. They do not by themselves reconstruct the complete history of
elicitation.

Historical information about how the GrammYEP material was supplied,
translated into Kadiwéu, reused with different consultants, or supplemented
with ad hoc Portuguese stimuli must be documented separately from the
computational matching evidence.

This separation is methodologically important:

- historical provenance is supported by researcher records and firsthand
  knowledge;
- dataset overlap is independently testable through the procedure documented
  here.

The two kinds of evidence can corroborate one another, but they should not be
treated as interchangeable.

---

## Files

### `grammyep_kadiweu_adjudication_47_expanded.tsv`

The 47 non-strict records originally retrieved at or above the 0.80 combined
similarity threshold, with expanded similarity and adjudication information.

### `grammyep_kadiweu_adjudication_63_unresolved.tsv`

The 63 records originally left unresolved by the 0.80 threshold and
subsequently subjected to exhaustive linguistic review.

### `grammyep_kadiweu_adjudication_all_110_nonstrict.tsv`

The canonical combined table for all 110 Kadiwéu records without a strict
exact/normalized match.

### `grammyep_kadiweu_review_medium_low.tsv`

Subset of the combined table containing all records currently assigned
`MEDIUM` or `LOW` confidence. This is the recommended starting point for
researcher review.

### `adjudication_summary.tsv`

Machine-readable summary of the current adjudication counts.

---

## Recommended review workflow

1. Review all `MEDIUM` and `LOW` cases.
2. Review the four `POSSIBLY_RELATED` records explicitly.
3. Change `review_status` from `TO_REVIEW` to an agreed controlled value such
   as `ACCEPTED`, `MODIFIED`, or `REJECTED`.
4. Recompute the provenance totals from the reviewed table rather than
   hard-coding the present 187 figure.
5. Only after review, treat the adjudication table as curated project data and
   integrate it into the reproducible comparison pipeline.

---

## Reproducibility principle

The analysis deliberately separates three layers:

    conservative normalization
        ↓
    automatic matching / similarity-based retrieval
        ↓
    explicit linguistic adjudication

The automatic procedure proposes evidence; it does not decide provenance.
Conversely, manual adjudication does not erase the automatic evidence: the
scores and automatic best candidate remain recorded in the TSV files.

This separation makes it possible to change a similarity threshold or improve
the retrieval algorithm later without silently changing the manually reviewed
provenance analysis.
