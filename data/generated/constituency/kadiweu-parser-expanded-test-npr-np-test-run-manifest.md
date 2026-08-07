# Run manifest: `npr-np-test` on the expanded 36-sentence suite

## Purpose and status

This manifest records the controlled comparison of accepted parser rules **A** with candidate rules **B**, which add an experimental rule projecting a proper-noun possessor (`NPR`) as `NP`.

- Experiment label: `npr-np-test`
- Suite: `kadiweu-parser-expanded-test` (`expanded-36`)
- Scope: 36 sentences (18 `DONE`, 18 `REVIEW`)
- Datasets: `hil-data`, `ped-gramm`, and `van-data`
- Comparison directions: B versus reference; B versus accepted output A
- Disabled TBP rules: 77 (`ip-xp`) and 122 (`CP-D`)
- Run outcome: completed; A and B both reported structural differences against provisional references
- Candidate disposition: **not yet accepted as the new baseline**; the two observed changes have been adjudicated as intended, but focused and full-corpus testing remain outstanding

The corrected run with Rules 77 and 122 skipped supersedes the earlier run in which all baseline rules were executed.

## Rule sets

| Role | File | SHA-256 |
|---|---|---|
| Accepted rules A | `/home/leonel/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.pdt.txt` | `94397f3831c3aed551914763ba5c32c9284beb321e01e62e560fd3f15f4ce085` |
| Candidate rules B | `/home/leonel/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.pdt.npr-np-test.txt` | `aae745826f1ee4e174f5eb3a5584b9ff01a19604f92bae48d54073a5ce073b82` |
| TBP definitions | `/home/leonel/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_050726.txt` | `67765202a6721f4d2e269cbb5564cb4a676027a6218af05ef8f457f999d734ff` |

Candidate B consists of the 168 enabled baseline rules plus the following experimental rule, executed last. Original TBP Rules 77 and 122 are skipped, so the runner reports 168 executed rules for A and 169 for B.

```text
171: np-wrap-sister-npr-test
node: $METAROOT

query: (NP* iDoms [1]N|N$)
    AND ([1]N|N$ hasSister [2]{1}NPR)

add_internal_node{1, 1}: NP
```

## Fixed suite inputs

| Role | File | SHA-256 |
|---|---|---|
| POS input | `/home/leonel/kadiweu/data/generated/constituency/kadiweu-parser-expanded-test.pos` | `d9e6ac0bba424e4f2c88e0499b25d4950a73dffd314fafb1a9ac4b8b688190c2` |
| Reference trees | `/home/leonel/kadiweu/data/generated/constituency/kadiweu-parser-expanded-test.gold.psd` | `dbed90d88091c1a9f89de156dec97dd8d371ee4eb35a309665a3f8355868167a` |

The input and reference files were held constant between A and B.

## Execution configuration

| Field | Recorded value |
|---|---|
| Repository root | `/home/leonel/kadiweu` |
| Orchestration script | `tests/run_npr_np_rule_experiment.sh` |
| Runner | `src/run_kadiweu_parser_rules.py` |
| Python command | `python3` |
| CorpusSearch command | `corpussearch` |
| Definitions loaded | 21 |
| Definitions used | `adverbialC`, `complexC`, `finiteVerb`, `noun`, `numeral`, `possessive`, `unmodifiable-noun`, `vb_et`, `vb_unacc` |
| Skipped rules | `77`, `122` |
| Retain intermediate output | yes (`--keep-intermediate`) |
| Run date and time | not recorded by the experiment script |
| Time zone | not recorded by the experiment script; user environment is `America/Fortaleza` |
| Git commit | not recorded by the experiment script |
| Reference commit | not recorded separately by the experiment script |
| Working-tree state | not recorded by the experiment script |
| Python version | not recorded by the experiment script |
| Java version | not recorded by the experiment script |
| CorpusSearch version | not recorded by the experiment script |

The missing values above cannot be reconstructed reliably after the fact. They must not be inferred from later repository or system state.

## Commands

The experiment was invoked from the repository root with:

```bash
cd ~/kadiweu
tests/run_npr_np_rule_experiment.sh
```

The orchestration script executed the equivalent of the following accepted A run:

```bash
python3 src/run_kadiweu_parser_rules.py \
  /home/leonel/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.pdt.txt \
  data/generated/constituency/kadiweu-parser-expanded-test.pos \
  --definitions /home/leonel/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_050726.txt \
  --corpussearch corpussearch \
  --skip-rule 77 \
  --skip-rule 122 \
  --output data/generated/constituency/kadiweu-parser-expanded-test-A.psd \
  --expected data/generated/constituency/kadiweu-parser-expanded-test.gold.psd \
  --comparison-report data/generated/constituency/kadiweu-parser-expanded-test-A-comparison.tsv \
  --diff data/generated/constituency/kadiweu-parser-expanded-test-A.diff \
  --work-dir data/generated/constituency/kadiweu-parser-expanded-test-A-run-skip-77-122 \
  --keep-intermediate \
  --log data/generated/constituency/kadiweu-parser-expanded-test-A-run.tsv
```

It then executed the equivalent candidate B run:

```bash
python3 src/run_kadiweu_parser_rules.py \
  /home/leonel/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.pdt.npr-np-test.txt \
  data/generated/constituency/kadiweu-parser-expanded-test.pos \
  --definitions /home/leonel/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_050726.txt \
  --corpussearch corpussearch \
  --skip-rule 77 \
  --skip-rule 122 \
  --output data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test.psd \
  --expected data/generated/constituency/kadiweu-parser-expanded-test.gold.psd \
  --accepted-output data/generated/constituency/kadiweu-parser-expanded-test-A.psd \
  --comparison-report data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test-comparison.tsv \
  --transition-report data/generated/constituency/kadiweu-parser-expanded-test-A-to-B-npr-np-test.tsv \
  --diff data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test.diff \
  --work-dir data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test-run-skip-77-122 \
  --keep-intermediate \
  --log data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test-run.tsv
```

The commands are reconstructed from the experiment script, the corrected skip configuration, and the terminal output. The terminal output confirms that both runs skipped Rules 77 and 122. It does not preserve the shell-expanded command line verbatim.

## Results against the reference

### Accepted A

| `struct_status` | Exact | Trace-equivalent | Structural difference | Total |
|---|---:|---:|---:|---:|
| `DONE` | 11 | 7 | 0 | 18 |
| `REVIEW` | 11 | 4 | 3 | 18 |
| **Total** | **22** | **11** | **3** | **36** |

### Candidate B

| `struct_status` | Exact | Trace-equivalent | Structural difference | Total |
|---|---:|---:|---:|---:|
| `DONE` | 11 | 7 | 0 | 18 |
| `REVIEW` | 10 | 3 | 5 | 18 |
| **Total** | **21** | **10** | **5** | **36** |

### Candidate B by dataset and status

| Dataset | Status | Exact | Trace-equivalent | Structural difference | Total |
|---|---|---:|---:|---:|---:|
| `hil-data` | `DONE` | 3 | 3 | 0 | 6 |
| `hil-data` | `REVIEW` | 2 | 2 | 2 | 6 |
| `ped-gramm` | `DONE` | 4 | 2 | 0 | 6 |
| `ped-gramm` | `REVIEW` | 3 | 1 | 2 | 6 |
| `van-data` | `DONE` | 4 | 2 | 0 | 6 |
| `van-data` | `REVIEW` | 5 | 0 | 1 | 6 |

## Direct A-to-B impact

- Changed sentences: 2 of 36
- Trace-equivalent A-to-B changes: 0
- Structural A-to-B changes: 2
- Changed `DONE` sentences: 0
- Changed `REVIEW` sentences: 2
- Affected dataset: `ped-gramm` only

| Sentence | Status | A vs. reference | B vs. reference | A-to-B change | Manual adjudication |
|---|---|---|---|---|---|
| `ped-gramm,0.11` | `REVIEW` | `EXACT_MATCH` | `STRUCTURAL_DIFFERENCE` | structural | Intended improvement: B correctly projects possessor `Maria` as `(NP (NPR Maria))`. Correct the provisional reference. |
| `ped-gramm,0.26` | `REVIEW` | `TRACE_EQUIVALENT` | `STRUCTURAL_DIFFERENCE` | structural | Intended improvement: B correctly projects possessor `João` as `(NP (NPR João))` in `João liGeladi` ‘João’s house’. Correct the provisional reference. |

The automatic transition labels describe agreement with the current reference, not linguistic correctness. Both apparent regressions were manually adjudicated as improvements because the affected proper nouns are possessors and should project `NP` under the adopted annotation policy.

## Generated artifacts

| Artifact | Path |
|---|---|
| A output | `data/generated/constituency/kadiweu-parser-expanded-test-A.psd` |
| A/reference comparison | `data/generated/constituency/kadiweu-parser-expanded-test-A-comparison.tsv` |
| A/reference structural diff | `data/generated/constituency/kadiweu-parser-expanded-test-A.diff` |
| A per-rule log | `data/generated/constituency/kadiweu-parser-expanded-test-A-run.tsv` |
| A intermediate directory | `data/generated/constituency/kadiweu-parser-expanded-test-A-run-skip-77-122/` |
| B output | `data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test.psd` |
| B/reference comparison | `data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test-comparison.tsv` |
| B/reference structural diff | `data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test.diff` |
| B per-rule log | `data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test-run.tsv` |
| B intermediate directory | `data/generated/constituency/kadiweu-parser-expanded-test-B-npr-np-test-run-skip-77-122/` |
| A-to-B transition report | `data/generated/constituency/kadiweu-parser-expanded-test-A-to-B-npr-np-test.tsv` |
| Input hash record | `data/generated/constituency/kadiweu-parser-expanded-test-npr-np-test-hashes.txt` |

## Exit-status interpretation

Both parser invocations returned status 1 because structural differences against the references remained. For this runner, status 1 is a completed comparison result, not an execution failure. The orchestration script therefore continued and completed the experiment. Status 2 or another unexpected value would indicate an execution or configuration failure.

## Reproducibility gaps and completion commands

The following commands should be run in the same repository state before a future run so that the next manifest records the fields absent from this historical run:

```bash
cd ~/kadiweu

date --iso-8601=seconds
git rev-parse HEAD
git status --porcelain=v1
git rev-parse HEAD:data/generated/constituency/kadiweu-parser-expanded-test.gold.psd
python3 --version
java -version
corpussearch --help

sha256sum \
  tests/run_npr_np_rule_experiment.sh \
  src/run_kadiweu_parser_rules.py
```

The CorpusSearch wrapper may be interactive and may not support `--help`. If so, record the version banner printed at startup and then quit normally.

## Acceptance assessment

- [x] A and B used identical POS input, reference trees, definitions, and enabled baseline rules.
- [x] Rules 77 and 122 were skipped in both runs, matching the TBP web configuration.
- [x] Candidate B was compared both with the reference and directly with output A.
- [x] No `DONE` sentence changed.
- [x] Every changed sentence was identified and manually adjudicated.
- [x] Both observed rule applications were judged intended possessor projections.
- [x] Input and rule hashes were recorded.
- [ ] A focused possessor collection with positive and near-miss cases has been run.
- [ ] The full corpus has been run to check for overgeneration outside the 36-sentence suite.
- [ ] Run timestamp, Git revisions, working-tree state, executable versions, and script hashes were captured automatically at execution time.
- [ ] Candidate B has been accepted and promoted to the parser baseline.

## Conclusion

Within the expanded 36-sentence suite, the experimental rule has narrow observed scope: it changes only `ped-gramm,0.11` and `ped-gramm,0.26`, leaves every `DONE` tree unchanged, and supplies the intended NP projection for a proper-noun possessor in both cases. This is positive evidence for the rule, but not yet sufficient for promotion. Acceptance should follow focused near-miss testing and a full-corpus A-to-B comparison.
