# Prediction integration — 2026-09-03

Baseline: main commit `167801d60b5e2875dcebc08bb3523fd47539d4d5`.
The committed converter matched the user's latest upload byte-for-byte.
No changes were pushed and no reference CoNLL-U or JSON was edited.

## What changed and why

- `src/kadiweu_json_to_conllu.py`: invokes partial tree predictions before
  empty-category removal; applies their relations and heads as locks. A
  predicted root supersedes root guessing, including for added punctuation.
- `src/kadiweu_prediction_bridge.py`: maps original source positions to emitted
  word IDs (not MWT range IDs), validates assignments and the combined graph,
  and protects locked core arguments during predicate-local cleanup.
- `tests/test_prediction_integration.py`: regression checks on all three source
  documents plus alignment, cleanup, failure, and CLI tests.
- `tests/fixtures/complement_rules.{psd,conllu}`: restored the exact earlier
  fixtures absent from this main snapshot but required by its existing tests.

Current JSON status is at `sentence.status`. Predictions apply only to DONE;
REVIEW or missing status retains legacy conversion. The historical converter
metadata lookup under `struct.status` is intentionally unchanged: fixing that
would be a separate metadata change.

Defaults now enable predictions for DONE. `--dependency-predictions off`
reproduces the old converter. Existing CLI arguments and resource layers remain.
No new PSD input is required: the original JSON tree is the prediction source.

Only HEAD/DEPREL can change. FORM, LEMMA, UPOS, XPOS, FEATS, DEPS, MISC,
metadata formatting, MWT rows and tokenization retain existing behavior.
Unresolved words use the converter's old heuristics, with the predicted root
available as an attachment target. This means fallback algorithms are retained,
not that their HEAD/DEPREL must stay identical when the root changes.

Tree predictions supersede conflicting legacy trace hints with a diagnostic.
Weak fallbacks cannot overwrite locked predictions. With predictions active,
subject/object cleanup is per predicate, not sentence-wide. Multiple locked
core dependents are retained rather than silently demoted. Invalid combined
graphs restore the whole sentence to legacy output with an stderr warning.
This recovery retains useful old behavior, but does not guarantee that legacy
output itself is linguistically or structurally error-free.

Diagnostics go to stderr, never into CoNLL-U: applied/fallback word counts,
rejected alignment or tree construction, conflicting trace hints, and rollback.
Programmer errors/import failures are not silently swallowed.

## Verification

110 tests pass on Python 3.12.13; Python 3.8 syntax parsing also passes, but
Python 3.8 runtime testing is still needed locally. The baseline regression
test uses `git show` on the pinned commit; it skips if that commit is unavailable.

| Source | Sentences | DONE with applied predictions | Sentences with changed output |
| --- | ---: | ---: | ---: |
| ped-gramm | 61 | 49 | 21 |
| hil-data | 70 | 65 | 35 |
| van-data | 75 | 69 | 36 |
| Total | 206 | 183 | 92 |

Across all 206 sentences, legacy mode is byte-for-byte equal to the original
converter with timestamps held fixed. All non-HEAD/DEPREL fields remain equal
in prediction mode. All accepted predictions survive serialization, and all
183 resulting DONE graphs pass head/root/cycle checks. No prediction batch
was rejected or rolled back on these inputs. REVIEW output remains identical.

These are integration checks, not a claim of perfect linguistic accuracy.
In particular, the known postverbal determiner heuristic disagreements in
hil-data,0.17 and 0.18 remain: reference nsubj is retained, and the source verb
classification awaits adjudication. No sentence-specific exception was added.

## Install

Commit/back up local work before replacing files. This archive contains only
the changed converter, new bridge/test, missing fixtures, and this document;
it relies on the other modules already present in the verified main snapshot.

```bash
unzip ~/Downloads/kadiweu-converter-integration-20260903.zip -d ~/kadiweu
cd ~/kadiweu
sha256sum -c INTEGRATION_SHA256SUMS
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Keep the full tests/fixtures directory. Unzip prompts before replacing matching
files and leaves unrelated files alone. The checksum file identifies this
delivery's exact bytes; it need not be committed after verification.

## Run

Normal use now enables predictions on DONE automatically:

```bash
cd ~/kadiweu/src
python3 kadiweu_json_to_conllu.py ../data/hil-data.json > ../data/treebank/draft-hil-data.conllu
```

The redirect replaces that draft file; choose another output name to retain it.
Run separately for ped-gramm.json and van-data.json. No-argument use still
defaults to data/ped-gramm.json.

To reproduce old dependency behavior:

```bash
python3 kadiweu_json_to_conllu.py ../data/hil-data.json --dependency-predictions off > ../data/treebank/draft-hil-data-legacy.conllu
```

Do not redirect generated drafts over the manually reviewed reference.
