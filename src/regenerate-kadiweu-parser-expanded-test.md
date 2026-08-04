# Regenerating the 36-sentence Kadiwéu parser expanded test

This document records the commands needed to regenerate the machine-generated artifacts of the 36-sentence expanded parser test. Run the commands from `~/kadiweu/src`.

## Prerequisites

The commands assume that:

- the repository is at `~/kadiweu`;
- `corpussearch` is available on `PATH`;
- `src/kadiweu_constituency.py` is the current constituency exporter;
- `src/run_kadiweu_parser_rules.py` is the current runner, including comparison summaries by both `struct_status` and `dataset × struct_status`;
- the current edited TBP rules are in `~/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.edt.txt`;
- the selection inventory is `data/generated/constituency/kadiweu-parser-expanded-test-inventory.tsv`.

The inventory is a manually curated, version-controlled selection manifest, not a derived parser artifact. It is the authoritative source for the 36 sentence IDs and their order. The commands below regenerate the source PSD files, expanded POS input, expanded gold PSD, parser-produced PSD, comparison TSV, structural-only diff, execution log, and intermediate rule files.

Check the required programs and files before starting:

```bash
cd ~/kadiweu/src

command -v python3
command -v corpussearch

test -f kadiweu_constituency.py
test -f run_kadiweu_parser_rules.py
test -f ../data/generated/constituency/kadiweu-parser-expanded-test-inventory.tsv
test -f ~/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.edt.txt
```

## 1. Regenerate the six status-specific source PSD files

These files are reconstructed from the three Tycho JSON exports. `--trace-format corpussearch` represents empty categories in the form accepted by CorpusSearch, for example `(-NONE- *T*-1)`.

```bash
cd ~/kadiweu/src

./kadiweu_constituency.py ../data/hil-data.json \
    --all \
    --status DONE \
    --format corpussearch \
    --trace-format corpussearch \
    --output-dir ../data/generated/constituency/

./kadiweu_constituency.py ../data/hil-data.json \
    --all \
    --status REVIEW \
    --format corpussearch \
    --trace-format corpussearch \
    --output-dir ../data/generated/constituency/

./kadiweu_constituency.py ../data/ped-gramm.json \
    --all \
    --status DONE \
    --format corpussearch \
    --trace-format corpussearch \
    --output-dir ../data/generated/constituency/

./kadiweu_constituency.py ../data/ped-gramm.json \
    --all \
    --status REVIEW \
    --format corpussearch \
    --trace-format corpussearch \
    --output-dir ../data/generated/constituency/

./kadiweu_constituency.py ../data/van-data.json \
    --all \
    --status DONE \
    --format corpussearch \
    --trace-format corpussearch \
    --output-dir ../data/generated/constituency/

./kadiweu_constituency.py ../data/van-data.json \
    --all \
    --status REVIEW \
    --format corpussearch \
    --trace-format corpussearch \
    --output-dir ../data/generated/constituency/
```

This produces or replaces:

- `hil-data.done.psd`
- `hil-data.review.psd`
- `ped-gramm.done.psd`
- `ped-gramm.review.psd`
- `van-data.done.psd`
- `van-data.review.psd`

## 2. Regenerate the expanded gold PSD and POS input

Read the sentence IDs from the first column of the inventory. `mapfile` preserves their documented order.

```bash
cd ~/kadiweu/src

inventory=../data/generated/constituency/kadiweu-parser-expanded-test-inventory.tsv
output_dir=../data/generated/constituency

mapfile -t expanded_ids < <(tail -n +2 "$inventory" | cut -f1)

sentence_args=()
for sentence_id in "${expanded_ids[@]}"; do
    sentence_args+=(--sentence-id "$sentence_id")
done

./run_kadiweu_parser_rules.py \
    --extract-from \
        "$output_dir/hil-data.done.psd" \
        "$output_dir/hil-data.review.psd" \
        "$output_dir/ped-gramm.done.psd" \
        "$output_dir/ped-gramm.review.psd" \
        "$output_dir/van-data.done.psd" \
        "$output_dir/van-data.review.psd" \
    "${sentence_args[@]}" \
    --gold-output "$output_dir/kadiweu-parser-expanded-test.gold.psd" \
    --pos-output "$output_dir/kadiweu-parser-expanded-test.pos"
```

The extraction mode preserves the inventory order and fails if a requested ID is missing or ambiguous.

## 3. Run all parser rules and regenerate the comparison artifacts

```bash
cd ~/kadiweu/src

rules=~/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.edt.txt
output_dir=../data/generated/constituency

./run_kadiweu_parser_rules.py \
    "$rules" \
    "$output_dir/kadiweu-parser-expanded-test.pos" \
    --corpussearch corpussearch \
    --expected "$output_dir/kadiweu-parser-expanded-test.gold.psd" \
    --output "$output_dir/kadiweu-parser-expanded-test.psd" \
    --diff "$output_dir/kadiweu-parser-expanded-test.diff" \
    --comparison-report "$output_dir/kadiweu-parser-expanded-test-comparison.tsv" \
    --work-dir "$output_dir/kadiweu-parser-expanded-test-run" \
    --log "$output_dir/kadiweu-parser-expanded-test-run.tsv" \
    --keep-intermediate
```

The command regenerates:

- `kadiweu-parser-expanded-test.psd`;
- `kadiweu-parser-expanded-test-comparison.tsv`;
- `kadiweu-parser-expanded-test.diff`;
- `kadiweu-parser-expanded-test-run.tsv`;
- the queries, CorpusSearch output, snapshots, and transcripts under `kadiweu-parser-expanded-test-run/`.

The run directory is regenerable and should normally remain untracked. The inventory, POS input, gold PSD, parser-produced PSD, comparison TSV, structural diff, and any adjudication record are the files normally considered for version control.

### Expected exit status

The runner returns status `1` when genuine structural differences are found. This is the expected result for the current expanded test, which has six `STRUCTURAL_DIFFERENCE` classifications; it does not mean that rule execution failed. Status `2` indicates an execution or input error.

The current expected terminal summary is:

```text
Comparison summary:
struct_status  exact  trace_equivalent  structural_difference  total
DONE              10                 7                      1     18
REVIEW             9                 4                      5     18
TOTAL             19                11                      6     36

Comparison summary by dataset × struct_status:
dataset    struct_status  exact  trace_equivalent  structural_difference  total
hil-data   DONE               2                 3                      1      6
hil-data   REVIEW             2                 2                      2      6
ped-gramm  DONE               4                 2                      0      6
ped-gramm  REVIEW             3                 2                      1      6
van-data   DONE               4                 2                      0      6
van-data   REVIEW             4                 0                      2      6
```

## 4. Verify the regenerated artifacts

The following read-only check verifies the inventory balance and the ID sets in the inventory, POS, gold PSD, parser PSD, and comparison TSV:

```bash
cd ~/kadiweu

python3 - <<'PY'
import csv
import re
from collections import Counter
from pathlib import Path

base = Path("data/generated/constituency")
inventory_path = base / "kadiweu-parser-expanded-test-inventory.tsv"

with inventory_path.open(encoding="utf-8", newline="") as stream:
    inventory = list(csv.DictReader(stream, delimiter="\t"))

inventory_ids = [row["sentence_id"] for row in inventory]
assert len(inventory_ids) == 36
assert len(set(inventory_ids)) == 36

balance = Counter((row["dataset"], row["struct_status"]) for row in inventory)
assert balance == Counter({
    ("hil-data", "DONE"): 6,
    ("hil-data", "REVIEW"): 6,
    ("ped-gramm", "DONE"): 6,
    ("ped-gramm", "REVIEW"): 6,
    ("van-data", "DONE"): 6,
    ("van-data", "REVIEW"): 6,
})

def psd_ids(path):
    text = path.read_text(encoding="utf-8")
    return re.findall(r"\(ID\s+([^()\s]+)\s*\)", text)

for name in (
    "kadiweu-parser-expanded-test.pos",
    "kadiweu-parser-expanded-test.gold.psd",
    "kadiweu-parser-expanded-test.psd",
):
    ids = psd_ids(base / name)
    assert ids == inventory_ids, (name, len(ids))

with (base / "kadiweu-parser-expanded-test-comparison.tsv").open(
    encoding="utf-8", newline=""
) as stream:
    comparison = list(csv.DictReader(stream, delimiter="\t"))

comparison_ids = [row["sentence_id"] for row in comparison]
assert len(comparison_ids) == 36
assert len(set(comparison_ids)) == 36
assert set(comparison_ids) == set(inventory_ids)
assert Counter(row["result"] for row in comparison) == Counter({
    "EXACT_MATCH": 19,
    "TRACE_EQUIVALENT": 11,
    "STRUCTURAL_DIFFERENCE": 6,
})

print("OK: 36 ordered IDs; six DONE and six REVIEW per dataset; 19 exact, 11 trace-equivalent, 6 structural differences.")
PY
```

These assertions intentionally fail if the source annotations, selection, parser rules, runner, or expected classification counts change. When such a change is intentional, inspect and adjudicate it before updating the recorded expectations.

## 5. Record the exact versions used

For a reproducible baseline, record the repository commit and checksums of the runner and rule file alongside the generated artifacts:

```bash
cd ~/kadiweu

git rev-parse HEAD
sha256sum src/run_kadiweu_parser_rules.py
sha256sum ~/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.edt.txt
```

Do not treat the six raw structural differences automatically as six parser regressions. They require the separate manual adjudication specified by the expanded-test issue, especially for `REVIEW` trees.
