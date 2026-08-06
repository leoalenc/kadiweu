# Generated constituency artifacts

## Purpose

This directory contains constituency exports from the Kadiwéu treebank and regression-test artifacts produced while emulating the Tycho Brahe Platform (TBP) parser with standalone CorpusSearch.

The emulator is intended to support controlled comparison of parser-rule revisions. It does not replace the TBP parser and does not establish a gold analysis by itself. Differences must be interpreted in light of each sentence's `struct_status` and, where necessary, adjudicated manually.

## Source constituency exports

The six principal PSD exports combine three source datasets with two annotation statuses:

| Dataset | `DONE` | `REVIEW` |
|---|---|---|
| `hil-data` | `hil-data.done.psd` | `hil-data.review.psd` |
| `ped-gramm` | `ped-gramm.done.psd` | `ped-gramm.review.psd` |
| `van-data` | `van-data.done.psd` | `van-data.review.psd` |

`DONE` trees are validated references. `REVIEW` trees are provisional and may contain problems in the reference itself. A structural difference involving a `REVIEW` sentence is therefore not automatically a parser regression.

Files with `.corpussearch.psd` in their names are CorpusSearch-oriented variants of the constituency exports. The exact export commands depend on the current `kadiweu_constituency.py` interface; consult its `--help` output before regenerating them.

## Parser-emulation regression suites

### Minimal suite

The minimal suite contains 12 sentences: two from each dataset × status combination. Its canonical artifacts are:

- `kadiweu-parser-minimal-test.pos`: flat POS input supplied to the emulator;
- `kadiweu-parser-minimal-test.gold.psd`: reference trees;
- `kadiweu-parser-minimal-test.psd`: parser output;
- `kadiweu-parser-minimal-test-comparison.tsv`: per-sentence comparison;
- `kadiweu-parser-minimal-test.diff`: genuine structural differences only.

### Expanded suite

The expanded suite contains 36 sentences: six from each dataset × status combination. It retains all 12 minimal-suite sentences and adds 24 sentences chosen to broaden constructional and trace coverage.

Its canonical artifacts are:

| File | Role |
|---|---|
| `kadiweu-parser-expanded-test.pos` | Flat POS input for the runner |
| `kadiweu-parser-expanded-test.gold.psd` | Reference constituency trees |
| `kadiweu-parser-expanded-test-inventory.tsv` | Sentence selection, status, trace information, and selection rationale |
| `kadiweu-parser-expanded-test.psd` | Final emulator output |
| `kadiweu-parser-expanded-test-comparison.tsv` | Per-sentence comparison classification |
| `kadiweu-parser-expanded-test.diff` | Structural differences between output and reference |
| `kadiweu-parser-expanded-test-adjudication.md` | Linguistic and technical adjudication of every remaining structural difference |

The `*-comparison-adjudicated.tsv` and `*-adjudicated.diff` files are derived review aids. Unless they are deliberately adopted as canonical outputs, the original comparison TSV, original diff, and separate adjudication Markdown are sufficient for versioned baselines.

## Comparison categories

The runner assigns one of three results to each sentence:

- `EXACT_MATCH`: the trees are identical after whitespace normalization;
- `TRACE_EQUIVALENT`: the trees differ only in accepted trace notation or coindex numbering after alpha-normalization;
- `STRUCTURAL_DIFFERENCE`: a syntactic difference remains after trace normalization.

The structural diff intentionally excludes trace-equivalent cases so that it focuses on differences that require technical diagnosis or linguistic adjudication.

## Current 36-sentence baseline

The latest documented run, after the Rule 119 correction described below, produced:

| `struct_status` | Exact | Trace-equivalent | Structural difference | Total |
|---|---:|---:|---:|---:|
| `DONE` | 11 | 7 | 0 | 18 |
| `REVIEW` | 11 | 4 | 3 | 18 |
| **Total** | **22** | **11** | **3** | **36** |

All 18 `DONE` trees are structurally compatible with the emulator output. The three remaining differences are `REVIEW` cases and have been adjudicated as reference-tree corrections:

- `hil-data,0.34`;
- `hil-data,0.7`;
- `van-data,0.10`.

See `kadiweu-parser-expanded-test-adjudication.md` for the complete evidence and required changes. `hil-data,0.7` and `van-data,0.10` contain the same sentence and construction in different datasets.

## Parser-rule authorship, provenance, and access

The Kadiwéu parser rules were authored by Maria Filomena Spatti
Sandalo and Charlotte Marie Chambelland Galves, respectively coordinator
and principal researcher of the DACILAT project (FAPESP Grant
No. 22/09158-5). Both are affiliated with the Department of Linguistics
at the University of Campinas (Unicamp).

The TBP Kadiwéu parser rules and definitions were available, at the time of this baseline, only to authorized members of the Unicamp DACILAT project through the TBP web interface. They must not be committed to a public repository until the rights holders approve redistribution under an explicit license.

The rules were copied from the TBP interface because it provides clipboard export rather than a public, version-controlled download. The local filenames are descriptive identifiers created by the researcher; they are not official TBP version identifiers.

The baseline depends on three restricted inputs:

| Local role | Local filename used during validation | SHA-256 |
|---|---|---|
| Original TBP rule export | `kadiweu_parser_300726.txt` | `3f17995a8928a7ba0a1056dc5a438b7fbbf243f0b6e90b29f2db73b1ebe381a8` |
| TBP definitions export | `kadiweu_parser_definitions_050726.txt` | `67765202a6721f4d2e269cbb5564cb4a676027a6218af05ef8f457f999d734ff` |
| CorpusSearch-compatible rule file used for the final baseline | `kadiweu_parser_300726.pdt.txt` | `94397f3831c3aed551914763ba5c32c9284beb321e01e62e560fd3f15f4ce085` |

The hashes identify exact local bytes without granting permission to redistribute them. Recalculate them internally with:

```bash
sha256sum \
  /path/to/kadiweu_parser_300726.txt \
  /path/to/kadiweu_parser_definitions_050726.txt \
  /path/to/kadiweu_parser_300726.pdt.txt
```

The compatible-rule hash above identifies the corrected file used for the final 36-sentence baseline. In particular, Rule 119 contains `(C iDoms me|me@)`.

## TBP definitions and the `possessive` macro

The current runner accepts a TBP definitions export through `--definitions` and expands named terms in rule node/query declarations before writing CorpusSearch query files.

The TBP definitions file establishes that `possessive` is not an unknown hidden class:

```text
possessive: PRO$|PRO$-*|N$
```

Rule 47 (`np-poss`) should therefore retain the upstream condition:

```text
AND ([2]NP iDomsOnly possessive)
```

and the emulator should be invoked with the definitions file. Replacing `possessive` with `N$` was a useful earlier workaround for the tested nouns, but it narrowed the upstream class by excluding `PRO$` and `PRO$-*`. It is obsolete in the current definition-aware workflow and must not be described as the final compatibility solution.

This concerns faithful emulation only. Redesigning possessive constituency so that a nominal possessor projects an embedded `NP` is a separate linguistic change.

## CorpusSearch compatibility changes

The compatible rule file differs from the original TBP export where standalone CorpusSearch syntax or execution behavior requires an explicit adjustment. These changes should remain distinguishable from later linguistic improvements.

| Rule | Compatible change | Reason |
|---|---|---|
| 31 `nbar12a` | Require the selected `NBAR` nodes to be sisters | Prevent `delete_node{1}` after a failed non-sister `extend_span` |
| 69 `cp-d-daǥa` | `daǥa` → `daǥa|daGa` | Recognize both attested/exported spelling variants |
| 70 `cp-daGa` | `daǥa` → `daǥa|daGa` | Recognize both attested/exported spelling variants |
| 76 `cp-c-only` | Index the NP operand and use `extend_span` | Make operands explicit and replace unsupported `expand_span` |
| 119 `cp-me-q` | `me` → `me|me@` | Recognize the boundary-marked complementizer in `hil-data,0.25` |
| 127 `cp-que-6` | `expand_span` → `extend_span` | Use the standalone CorpusSearch revision command |
| 140 `ip-adv` | Insert missing `AND` | Repair invalid standalone query syntax |

Rule 47 is no longer edited: the runner expands its `possessive` macro from the TBP definitions file.

### Rule 31: `nbar12a`

The original query could select non-sister `NBAR` nodes. Standalone CorpusSearch could then reject `extend_span{2, 1}` but still execute the following `delete_node{1}`, destroying an embedded possessor constituent. The compatible query adds sisterhood as an explicit precondition:

```text
query: ([1]{1}NBAR hasSister [2]{2}NBAR)
       AND ([1]NBAR iPrecedes [2]NBAR)
       AND ([2]NBAR iDoms !Q)
       AND ([1]NBAR iDoms N)
       AND ([2]NBAR iDoms N$)
```

This preserves `(NP (N niganigawanigi))` in the accepted output for `van-data,0.31` and produces the intended parallel analysis for `hil-data,0.34`.

`([2]NBAR iDoms !Q)` means that the node immediately dominates at least one daughter whose label is not `Q`; it does not mean “does not dominate Q.” Because the same rule requires an `N$` daughter, this condition appears redundant. A change to `NOT ([2]NBAR iDoms Q)` would alter the rule's semantics and should be tested separately rather than folded into the compatibility patch.

### Rules 69 and 70: `daǥa|daGa`

Both rules broaden the lexical condition:

```text
AND (C iDoms daǥa|daGa)
```

This is a rule-level compatibility/coverage adjustment for orthographic variants. It is not a general instruction to normalize every Kadiwéu terminal globally.

### Rule 76: `cp-c-only`

The current compatible form is:

```text
query: (IP-MAT iDoms {1}CP)
       AND ({2}NP hasSister CP)
       AND (NP iPrecedes CP)
       AND (CP iDomsOnly C)

extend_span{1, 2}:
```

For maximum referential consistency, the remaining unindexed mentions can also be written as `{1}CP` and `{2}NP`; that tightening should be regression-tested before the baseline rule file is changed.

### Rule 119: `cp-me-q`

For the current baseline, change:

```text
AND (C iDoms me)
```

to:

```text
AND (C iDoms me|me@)
```

The controlled edit corrected `hil-data,0.25`, including the downstream `CP-me` and `NP-SBJ` labels, and removed the last structural difference among the 18 `DONE` test sentences. This is a narrow rule-level correction, not evidence that the runner should remove `@` globally.

### Rules 127 and 140

Rule 127 uses:

```text
extend_span{2, 1}:
```

instead of TBP-exported `expand_span{2,1}:`. Rule 140 inserts the required Boolean operator:

```text
query: (VB hasSister {1}IP)
       AND (VB iPrecedes IP)
```

## Regenerating the expanded-test artifacts

Run the following commands from `src/` in the repository. Adjust only the two restricted-input paths. The compatible rules file must include every change listed above, including Rule 119, and its hash should match the hash recorded for the Git baseline.

```bash
TBP_RULES=/private/path/to/kadiweu_parser_300726.pdt.txt
TBP_DEFINITIONS=/private/path/to/kadiweu_parser_definitions_050726.txt

python3 run_kadiweu_parser_rules.py \
  "$TBP_RULES" \
  ../data/generated/constituency/kadiweu-parser-expanded-test.pos \
  --definitions "$TBP_DEFINITIONS" \
  --corpussearch corpussearch \
  --output ../data/generated/constituency/kadiweu-parser-expanded-test.psd \
  --expected ../data/generated/constituency/kadiweu-parser-expanded-test.gold.psd \
  --comparison-report ../data/generated/constituency/kadiweu-parser-expanded-test-comparison.tsv \
  --diff ../data/generated/constituency/kadiweu-parser-expanded-test.diff \
  --work-dir ../data/generated/constituency/kadiweu-parser-expanded-test-run \
  --keep-intermediate \
  --log ../data/generated/constituency/kadiweu-parser-expanded-test-run.tsv
```

The runner exits nonzero when genuine structural differences remain. For the documented baseline, a final `FAIL: 3 structural difference(s)` message is expected and does not mean that rule execution failed; the three cases are adjudicated `REVIEW` reference differences.

To confirm the summary from the comparison table:

```bash
python3 - <<'PY'
import csv
from collections import Counter
from pathlib import Path

path = Path("../data/generated/constituency/kadiweu-parser-expanded-test-comparison.tsv")
rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
for status in ("DONE", "REVIEW"):
    counts = Counter(row["result"] for row in rows if row["struct_status"] == status)
    print(status, dict(counts))
print("TOTAL", dict(Counter(row["result"] for row in rows)))
PY
```

### Rebuilding the fixed 36-sentence input and gold files

Normally, keep the committed `.pos`, `.gold.psd`, and inventory TSV fixed while evaluating a new rule revision. Changing the selected sentences would make results across rule versions less directly comparable.

If the suite must be reconstructed from the six source PSDs, use the sentence IDs in `kadiweu-parser-expanded-test-inventory.tsv` with the runner's extraction mode:

```bash
python3 run_kadiweu_parser_rules.py \
  --extract-from \
    ../data/generated/constituency/hil-data.done.psd \
    ../data/generated/constituency/hil-data.review.psd \
    ../data/generated/constituency/ped-gramm.done.psd \
    ../data/generated/constituency/ped-gramm.review.psd \
    ../data/generated/constituency/van-data.done.psd \
    ../data/generated/constituency/van-data.review.psd \
  --sentence-id 'hil-data,0.1' \
  --sentence-id 'hil-data,0.10' \
  --sentence-id 'hil-data,0.25' \
  --sentence-id 'hil-data,0.34' \
  --sentence-id 'hil-data,0.39' \
  --sentence-id 'hil-data,0.40' \
  --sentence-id 'hil-data,0.42' \
  --sentence-id 'hil-data,0.44' \
  --sentence-id 'hil-data,0.5' \
  --sentence-id 'hil-data,0.6' \
  --sentence-id 'hil-data,0.68' \
  --sentence-id 'hil-data,0.7' \
  --sentence-id 'ped-gramm,0.1' \
  --sentence-id 'ped-gramm,0.11' \
  --sentence-id 'ped-gramm,0.17' \
  --sentence-id 'ped-gramm,0.26' \
  --sentence-id 'ped-gramm,0.28' \
  --sentence-id 'ped-gramm,0.35' \
  --sentence-id 'ped-gramm,0.46' \
  --sentence-id 'ped-gramm,0.49' \
  --sentence-id 'ped-gramm,0.57' \
  --sentence-id 'ped-gramm,0.58' \
  --sentence-id 'ped-gramm,0.6' \
  --sentence-id 'ped-gramm,0.61' \
  --sentence-id 'van-data,0.1' \
  --sentence-id 'van-data,0.10' \
  --sentence-id 'van-data,0.14' \
  --sentence-id 'van-data,0.16' \
  --sentence-id 'van-data,0.24' \
  --sentence-id 'van-data,0.31' \
  --sentence-id 'van-data,0.35' \
  --sentence-id 'van-data,0.38' \
  --sentence-id 'van-data,0.47' \
  --sentence-id 'van-data,0.56' \
  --sentence-id 'van-data,0.66' \
  --sentence-id 'van-data,0.71' \
  --gold-output ../data/generated/constituency/kadiweu-parser-expanded-test.gold.psd \
  --pos-output ../data/generated/constituency/kadiweu-parser-expanded-test.pos
```

Review the reconstructed files before replacing a tagged baseline: changes may reflect edits to the source treebank rather than parser-rule behavior.

## Intermediate run directories

Directories such as `kadiweu-parser-expanded-test-run/`, `kadiweu-parser-expanded-test-run-2/`, and `kadiweu-parser-expanded-test-run-3/` contain generated query files, CorpusSearch reports, per-rule PSD snapshots, and debugging logs. They are valuable during diagnosis but are normally excluded from Git because they are large, reproducible, and tied to local paths.

The same policy applies to one-sentence diagnostic run directories, Python `__pycache__/`, and temporary archives such as `kadiweu-parser-minimal-test-run.tar.gz`.

## Versioning and Git tags

Before changing the compatible rules again:

1. verify that the canonical expanded-suite artifacts and adjudication report are committed;
2. record the SHA-256 hashes of the original rules, definitions, and **actually executed** compatible rules in this README;
3. commit the README without committing the restricted rule files;
4. create an annotated Git tag on that commit.

Suggested commands:

```bash
git add data/generated/constituency/README.md \
  data/generated/constituency/kadiweu-parser-expanded-test.pos \
  data/generated/constituency/kadiweu-parser-expanded-test.gold.psd \
  data/generated/constituency/kadiweu-parser-expanded-test-inventory.tsv \
  data/generated/constituency/kadiweu-parser-expanded-test.psd \
  data/generated/constituency/kadiweu-parser-expanded-test-comparison.tsv \
  data/generated/constituency/kadiweu-parser-expanded-test.diff \
  data/generated/constituency/kadiweu-parser-expanded-test-adjudication.md

git commit -m "Record 36-sentence parser emulator baseline"

git tag -a kadiweu-parser-expanded-test-baseline \
  -m "36-sentence parser emulator baseline after Rule 119 correction"

git show --stat kadiweu-parser-expanded-test-baseline
git push
git push origin kadiweu-parser-expanded-test-baseline
```

Do not stage unrelated working-tree changes or intermediate run directories. A Git tag freezes the public regression artifacts and runner revision; the recorded hashes identify the restricted rule inputs used for the same run.

## Future upstream comparison

When a new TBP rule export becomes available, preserve the old compatible rule set internally and derive a new compatible version from the new upstream export. Keep upstream changes separate from CorpusSearch compatibility patches, run the unchanged 36-sentence suite against both versions, and compare their per-sentence reports. This makes improvements and regressions attributable to specific rule revisions rather than to changes in the test sample.
