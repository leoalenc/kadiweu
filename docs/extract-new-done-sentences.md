# Extract new DONE sentences for manual UD review

Run from any directory; defaults are relative to the script's repository:

```bash
python3 ~/kadiweu/src/extract_new_done_sentences.py --dry-run
python3 ~/kadiweu/src/extract_new_done_sentences.py
```

Reads all three `data/treebank/draft-{ped-gramm,hil-data,van-data}.conllu`
files, `data/treebank/kbc_unicamp-ud-test.conllu`, and all three canonical
`data/{ped-gramm,hil-data,van-data}.json` sources.

Writes only `data/treebank/review/new-done-sentences.conllu`. Its parent
directory is created if needed. Existing output is never overwritten, even
when empty; choose a new filename with `--output` for another review batch.
Do not redirect stdout: the script writes the review file itself.

Selection requires source JSON `sentence.status == "DONE"` and a draft
`sent_uid` absent from the reference. Identity uses UID, not sentence text or
number. Source status is necessary because current drafts do not reliably
export it. Adjudicated REVIEW trees are not promoted to DONE. DONE describes
the source tree, not manual review of the draft UD annotation.

The selected draft blocks are copied without altering comments, IDs, forms,
lemmas, tags, features, dependencies, MWT rows or empty nodes. Only blank
sentence separators/final newlines are standardized. Draft ordering is kept:
ped-gramm, hil-data, van-data by default. Source JSON and all CoNLL-U inputs
remain unchanged; no integration into the reference is performed.

Missing/duplicate CoNLL-U IDs and duplicate JSON UIDs cause an error before
writing. A new UID colliding with a reference/selected sent_id also causes an
error. Draft UIDs missing from JSON and non-DONE/missing statuses are excluded
and counted. The counts are disjoint: already-in-reference is checked first.
Unknown-source UIDs produce a warning.

Keep JSON exports and drafts synchronized. This script checks eligibility,
not whether the draft was regenerated after every source-tree revision, and
does not perform linguistic or full CoNLL-U validation. Review all selected
sentences manually before integrating them into the reference.

Override defaults when needed:

```bash
python3 src/extract_new_done_sentences.py \
  --drafts data/treebank/draft-ped-gramm.conllu data/treebank/draft-hil-data.conllu data/treebank/draft-van-data.conllu \
  --reference data/treebank/kbc_unicamp-ud-test.conllu \
  --json data/ped-gramm.json data/hil-data.json data/van-data.json \
  --output data/treebank/review/new-done-batch-2.conllu
```

Tests (standard library only, compatible with Python 3.8 syntax):

```bash
cd ~/kadiweu
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_extract_new_done_sentences.py' -v
```

11 tests passed on Python 3.12. The available repository snapshot at commit
167801d60b5e2875dcebc08bb3523fd47539d4d5 gave: 206 draft sentences,
129 already in reference, 7 additional non-DONE, 0 unknown-source UIDs,
70 selected. These are snapshot results, not a count of your newer local
reference or newly regenerated drafts. No transitional data file is bundled:
run the script locally to extract from your latest drafts.
