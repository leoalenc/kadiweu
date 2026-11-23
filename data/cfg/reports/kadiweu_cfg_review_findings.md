# CFG evaluation of the 17 REVIEW sentences

## Scope and interpretation

The review PSD files contain 17 sentences: 4 from `hil-data`, 7 from `ped-gramm`, and 6 from `van-data`. Their metadata records the `REVIEW` status, sentence ID, UID, text, and Portuguese prompt, but does not record why a sentence was not assigned `DONE`. The issue labels below are therefore provisional inferences from the tree and prompt, not recovered adjudication notes.

One important reason for `REVIEW` is a plausible structural analysis that does not express the reading in the Portuguese elicitation prompt. The clearest example here is `ped-gramm,0.45`: its tree is an NP corresponding to “João’s dirty house,” whereas the prompt is predicative: “João’s house is dirty.” A CFG rule that licenses that NP would capture a plausible alternative reading, not the prompted reading.

## CFG evaluation

The grammar was induced from the 189 `DONE` trees. The 17 `REVIEW` sentences were parsed from the flat POS trees and compared with their current full trees. The comparison follows the CFG induction normalization: it removes `-NONE-` trace subtrees, strips numeric coindices, abstracts over overt word forms by using POS tags, and ignores the parser’s `ROOT` wrapper. A match to a current `REVIEW` tree establishes compatibility with that analysis; it does not validate the analysis.

- **10 of 17** sentences received at least one parse; together they produced **37 parses**.
- **7** sentences received no parse with the current grammar.
- **2** current REVIEW trees matched a CFG parse exactly: `ped-gramm,0.29` (parse 5) and `ped-gramm,0.42` (parse 1).
- There were **no partial trace matches** in this REVIEW set.
- All 17 input yields aligned with their corresponding full-tree records.

| Sentence | Provisional issue inferred from the tree and prompt | CFG result | Candidate | Note |
|---|---|---:|
| `hil-data,0.40` | Prompt seems compatible; complex relative clause and applicative structure need review | 0 parses | No | Debatable use of commas |
| `hil-data,0.45` | The tree assigns two pronouns and a demonstrative; check how these express “I am here” | 0 | No | Structure under investigation |
| `hil-data,0.46` | Paired comitative example; `CP-me`/`DAPL` analysis needs review | 0 | Yes | There are analogous sentences with pre-verbal subject and `CP-me` verb complement |
| `hil-data,0.47` | Paired comitative example; `CP-me`/`DAPL` analysis needs review | 0 | Yes | See note on `hil-data,0.46` |
| `ped-gramm,0.21` | Elicited NP fragment; the current subject/predicate grouping is not reproduced | 3; no match | No | NP fragment |
| `ped-gramm,0.27` | The analysis of *naGajo* as a possessive pronoun is under debate; it is not clear whether it should be wrapped in a NP. | 0 | Yes | There is a new tree in the source treebank with `DONE` status. |
| `ped-gramm,0.28` | Applicative plus `daGa` comparison structure; attachment is unresolved | 0 | No | |
| `ped-gramm,0.29` | NP fragment with a relative-like `CP-me`; current tree is reproduced | 6; exact match at 5 | No | NP fragment |
| `ped-gramm,0.31` | Conditional fragment; the grammar lacks the `CP-daGa` structure | 6; no match | No | NP fragment |
| `ped-gramm,0.42` | Applicative “be near” construction; current tree is reproduced. **Clear prompt–analysis mismatch:** "city" should be possessor | 1; exact match at 1 | Yes | Inversion of possessor-possessum order |
| `ped-gramm,0.45` | **Clear prompt–analysis mismatch:** NP reading versus predication | 0 | Yes | *napioi* "dirty" should be `NP-PRD`, while *João liGeladi* should be `NP-SBJ`|
| `van-data,0.9` | Heavy/cheap modifiers are represented as stacked nominal material. | 1; no match | No | |
| `van-data,0.15` | **Prompt–analysis mismatch:** Relative clause is not free. It should be attached inside the locative `CP-me` | 4; no match | Yes | Intended structure with a `CP-REL` can be produced by a new CFG rule |
| `van-data,0.16` | **Clear prompt–analysis mismatch:** "canoe" is possessum in the Portuguese translation, not possessor | 2; no match | Yes | Inversion of possessor-possessum order | 
| `van-data,0.42` | **Clear prompt–analysis mismatch:** the tree’s predicate is "her/his/its photo of the beauty", while the prompt describes the eggs of her photo as beautiful | 6; no match | Yes | Check whether the CFG already produces the intended structure; otherwise, create a new rule for that. |
| `van-data,0.45` | **Clear prompt–analysis mismatch:** `CP-me` is actually a relative clause modifying "eggs". | 4; no match | Yes | Check whether the CFG already produces the intended structure; otherwise, create a new rule for that.|
| `van-data,0.46` | **Clear prompt–analysis mismatch:** *liwigo okokodi ligetedi* should constitute the NP-SBJ, *liwigo* 'photo' being the head. Possible recursive structure, given the paraphrase "his/her/its photo of the eggs of the chicken"| 4; no match | Yes | Check whether the CFG already produces the intended structure; otherwise, create a new rule for that.|

## Implications for adding CFG rules

Do not add rules solely to reproduce a REVIEW tree. First establish that the tree expresses the intended elicited reading. This is especially important when the current tree licenses a plausible alternative, as in `ped-gramm,0.45`.

The two current REVIEW analyses already reproduced by the grammar (`ped-gramm,0.29` and `ped-gramm,0.42`) are candidates for further inspection, not confirmed gold examples. Other sentences receive parses, but none of those parses matches the current REVIEW analysis; the missing-production report identifies what would be needed to license those trees. Those productions are diagnostics, not automatic rule recommendations.

## Per-sentence reports

The companion TSV files contain the detailed parser results and missing-rule inventory; their contents are not duplicated here:

- `cfg-review-report.tsv`: parse counts, matching parse numbers, and match type for each sentence.
- `cfg-review-rule-gaps.tsv`: productions missing from the current CFG for each current REVIEW tree.
