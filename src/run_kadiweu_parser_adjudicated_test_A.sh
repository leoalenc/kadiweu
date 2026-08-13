#!/usr/bin/env bash
# Run original compatible parser A against the adjudicated Kadiwéu test set.
#
# The adjudicated test is intentionally distinct from the frozen 206-sentence
# full test.  The reference currently contains 182 records:
#   170 DONE + 12 REVIEW.
#
# This script:
#   1. verifies the adjudicated gold hash;
#   2. derives a matching flat POS file from that exact gold reference;
#   3. runs original parser A with the same A-era definitions and disabled rules;
#   4. compares A against the adjudicated gold;
#   5. writes summaries and provenance hashes.
#
# It does NOT overwrite any kadiweu-parser-full-test-* artifact.

set -euo pipefail

readonly EXPECTED_GOLD_SHA256="a0409cfb8f4acd1b2610db2135b8ee8855b5bd7bb35b592982cb9384ac096985"
readonly EXPECTED_RULES_SHA256="94397f3831c3aed551914763ba5c32c9284beb321e01e62e560fd3f15f4ce085"
readonly EXPECTED_DEFINITIONS_SHA256="67765202a6721f4d2e269cbb5564cb4a676027a6218af05ef8f457f999d734ff"
readonly EXPECTED_SENTENCES=182
readonly EXPECTED_DONE=170
readonly EXPECTED_REVIEW=12
readonly EXPECTED_EXECUTED_RULES=168

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
SRC_DIR="$PROJECT_ROOT/src"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency"

RUNNER="${RUNNER:-$SRC_DIR/run_kadiweu_parser_rules.py}"
RULES_A="${RULES_A:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.pdt.txt}"
DEFINITIONS="${DEFINITIONS:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_050726.txt}"
CORPUSSEARCH="${CORPUSSEARCH:-corpussearch}"

GOLD="${ADJUDICATED_GOLD:-$OUT_DIR/kadiweu-parser-adjudicated-test.gold.psd}"
INPUT="$OUT_DIR/kadiweu-parser-adjudicated-test.pos"

OUTPUT="$OUT_DIR/kadiweu-parser-adjudicated-test-A.psd"
COMPARISON="$OUT_DIR/kadiweu-parser-adjudicated-test-A-comparison.tsv"
DIFF="$OUT_DIR/kadiweu-parser-adjudicated-test-A.diff"
RULE_LOG="$OUT_DIR/kadiweu-parser-adjudicated-test-A-run.tsv"
SUMMARY="$OUT_DIR/kadiweu-parser-adjudicated-test-A-summary.tsv"
DATASET_SUMMARY="$OUT_DIR/kadiweu-parser-adjudicated-test-A-dataset-summary.tsv"
HASHES="$OUT_DIR/kadiweu-parser-adjudicated-test-A-hashes.txt"
INPUT_HASHES="$OUT_DIR/kadiweu-parser-adjudicated-test-input-hashes.txt"
CONSOLE_LOG="$OUT_DIR/kadiweu-parser-adjudicated-test-A-console.log"

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

require_file() {
    [[ -f "$1" ]] || die "required file not found: $1"
}

actual_sha256() {
    sha256sum "$1" | awk '{print $1}'
}

mkdir -p "$OUT_DIR"

for command_name in python3 sha256sum awk mktemp tee; do
    command -v "$command_name" >/dev/null 2>&1 \
        || die "required command not found: $command_name"
done

command -v "$CORPUSSEARCH" >/dev/null 2>&1 \
    || die "CorpusSearch command not found: $CORPUSSEARCH"

for required in "$RUNNER" "$RULES_A" "$DEFINITIONS" "$GOLD"; do
    require_file "$required"
done

printf 'Verifying adjudicated gold...\n'

gold_hash="$(actual_sha256 "$GOLD")"
[[ "$gold_hash" == "$EXPECTED_GOLD_SHA256" ]] \
    || die "adjudicated gold hash mismatch: expected $EXPECTED_GOLD_SHA256; found $gold_hash"

rules_hash="$(actual_sha256 "$RULES_A")"
definitions_hash="$(actual_sha256 "$DEFINITIONS")"

[[ "$rules_hash" == "$EXPECTED_RULES_SHA256" ]] \
    || die "rules A hash mismatch: expected $EXPECTED_RULES_SHA256; found $rules_hash"

[[ "$definitions_hash" == "$EXPECTED_DEFINITIONS_SHA256" ]] \
    || die "definitions hash mismatch: expected $EXPECTED_DEFINITIONS_SHA256; found $definitions_hash"

printf 'Adjudicated gold, rules A, and definitions hashes: OK\n'

# Validate the adjudicated reference and derive a flat POS input from exactly
# these 182 records.  We reuse the runner's own PSD parsing/POS conversion
# functions so input derivation follows the same implementation as the emulator.
python3 - "$RUNNER" "$GOLD" "$INPUT" \
    "$EXPECTED_SENTENCES" "$EXPECTED_DONE" "$EXPECTED_REVIEW" <<'PY'
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

runner_path = Path(sys.argv[1])
gold_path = Path(sys.argv[2])
pos_path = Path(sys.argv[3])
expected_sentences = int(sys.argv[4])
expected_done = int(sys.argv[5])
expected_review = int(sys.argv[6])

spec = importlib.util.spec_from_file_location("kadiweu_runner", runner_path)
if spec is None or spec.loader is None:
    raise SystemExit(f"cannot load runner module from {runner_path}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

records = module.read_records(gold_path)

if len(records) != expected_sentences:
    raise SystemExit(
        f"expected {expected_sentences} adjudicated records; found {len(records)}"
    )

ids = [record.sentence_id for record in records]
if len(set(ids)) != expected_sentences:
    raise SystemExit("adjudicated gold contains duplicate sentence IDs")

statuses = Counter(module.record_status(record) for record in records)
if statuses["DONE"] != expected_done or statuses["REVIEW"] != expected_review:
    raise SystemExit(
        "unexpected adjudicated status counts: "
        f"DONE={statuses['DONE']} REVIEW={statuses['REVIEW']}; "
        f"expected DONE={expected_done} REVIEW={expected_review}"
    )

module.write_records(
    pos_path,
    (module.record_to_pos(record) for record in records),
)

pos_records = module.read_records(pos_path)
if len(pos_records) != expected_sentences:
    raise SystemExit(
        f"derived POS must contain {expected_sentences} records; "
        f"found {len(pos_records)}"
    )

pos_ids = [record.sentence_id for record in pos_records]
if pos_ids != ids:
    raise SystemExit("derived POS IDs/order differ from adjudicated gold")

print(
    f"Adjudicated reference: {len(records)} records "
    f"(DONE={statuses['DONE']}, REVIEW={statuses['REVIEW']})"
)
print(f"Derived matching POS input: {pos_path}")
PY

require_file "$INPUT"

sha256sum "$GOLD" "$INPUT" > "$INPUT_HASHES"

printf 'Adjudicated test input hashes written to %s\n' "$INPUT_HASHES"

RUN_DIR="$(mktemp -d "$OUT_DIR/kadiweu-parser-adjudicated-test-A-run-XXXXXXXX")"
printf 'Intermediate run directory: %s\n' "$RUN_DIR"

set +e
python3 -u "$RUNNER" \
    "$RULES_A" \
    "$INPUT" \
    --definitions "$DEFINITIONS" \
    --corpussearch "$CORPUSSEARCH" \
    --skip-rule 77 \
    --skip-rule 122 \
    --output "$OUTPUT" \
    --expected "$GOLD" \
    --comparison-report "$COMPARISON" \
    --diff "$DIFF" \
    --work-dir "$RUN_DIR" \
    --keep-intermediate \
    --log "$RULE_LOG" \
    2>&1 | tee "$CONSOLE_LOG"
runner_status=${PIPESTATUS[0]}
set -e

case "$runner_status" in
    0)
        printf 'Emulator completed with no structural differences against adjudicated gold.\n'
        ;;
    1)
        printf 'Emulator completed; structural differences against adjudicated gold were found.\n'
        ;;
    2)
        die "emulator execution/configuration failure; see $CONSOLE_LOG and $RUN_DIR"
        ;;
    *)
        die "unexpected emulator exit status $runner_status; see $CONSOLE_LOG"
        ;;
esac

for artifact in "$OUTPUT" "$COMPARISON" "$DIFF" "$RULE_LOG" "$CONSOLE_LOG"; do
    require_file "$artifact"
done

comparison_rows="$(awk 'END {print NR - 1}' "$COMPARISON")"
rule_rows="$(awk 'END {print NR - 1}' "$RULE_LOG")"

[[ "$comparison_rows" -eq "$EXPECTED_SENTENCES" ]] \
    || die "expected $EXPECTED_SENTENCES comparison rows; found $comparison_rows"

[[ "$rule_rows" -eq "$EXPECTED_EXECUTED_RULES" ]] \
    || die "expected $EXPECTED_EXECUTED_RULES executed-rule rows; found $rule_rows"

python3 - \
    "$COMPARISON" \
    "$SUMMARY" \
    "$DATASET_SUMMARY" \
    "$EXPECTED_SENTENCES" <<'PY'
import csv
import sys
from collections import Counter
from pathlib import Path

comparison_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
dataset_summary_path = Path(sys.argv[3])
expected = int(sys.argv[4])

with comparison_path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream, delimiter="\t"))

required = {"sentence_id", "dataset", "struct_status", "result", "details"}
if not rows or not required.issubset(rows[0]):
    raise SystemExit(f"invalid comparison-report columns in {comparison_path}")

if len(rows) != expected:
    raise SystemExit(f"expected {expected} comparison rows; found {len(rows)}")

ids = [row["sentence_id"] for row in rows]
if len(set(ids)) != expected:
    raise SystemExit("comparison report contains duplicate/missing sentence IDs")

def counts_for(selected):
    c = Counter(row["result"] for row in selected)
    return (
        c["EXACT_MATCH"],
        c["TRACE_EQUIVALENT"],
        c["STRUCTURAL_DIFFERENCE"],
        len(selected),
    )

statuses = [s for s in ("DONE", "REVIEW") if any(r["struct_status"] == s for r in rows)]
statuses.extend(sorted({r["struct_status"] for r in rows} - set(statuses)))

summary_lines = [
    "struct_status\texact\ttrace_equivalent\tstructural_difference\ttotal"
]
for status in [*statuses, "TOTAL"]:
    selected = rows if status == "TOTAL" else [
        r for r in rows if r["struct_status"] == status
    ]
    summary_lines.append(
        "\t".join(map(str, (status, *counts_for(selected))))
    )

summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

dataset_lines = [
    "dataset\tstruct_status\texact\ttrace_equivalent\tstructural_difference\ttotal"
]
datasets = sorted({row["dataset"] for row in rows})
for dataset in datasets:
    for status in statuses:
        selected = [
            r for r in rows
            if r["dataset"] == dataset and r["struct_status"] == status
        ]
        if selected:
            dataset_lines.append(
                "\t".join(map(str, (dataset, status, *counts_for(selected))))
            )

dataset_summary_path.write_text(
    "\n".join(dataset_lines) + "\n",
    encoding="utf-8",
)

print("\nAdjudicated parser-A comparison summary:")
print(summary_path.read_text(encoding="utf-8"), end="")
print("By dataset × status:")
print(dataset_summary_path.read_text(encoding="utf-8"), end="")
PY

sha256sum \
    "$RULES_A" \
    "$DEFINITIONS" \
    "$GOLD" \
    "$INPUT" \
    "$OUTPUT" \
    "$COMPARISON" \
    "$DIFF" \
    "$RULE_LOG" \
    "$SUMMARY" \
    "$DATASET_SUMMARY" \
    "$CONSOLE_LOG" \
    > "$HASHES"

printf '\nAdjudicated parser-A run completed successfully.\n'
printf '  Emulator exit status: %s\n' "$runner_status"
printf '  Executed rules: %s (TBP rules 77 and 122 skipped)\n' "$rule_rows"
printf '  Compared sentences: %s\n' "$comparison_rows"
printf '  Run directory: %s\n' "$RUN_DIR"
printf '  Adjudicated gold: %s\n' "$GOLD"
printf '  Derived POS input: %s\n' "$INPUT"
printf '  Output: %s\n' "$OUTPUT"
printf '  Comparison: %s\n' "$COMPARISON"
printf '  Structural diff: %s\n' "$DIFF"
printf '  Rule log: %s\n' "$RULE_LOG"
printf '  Summary: %s\n' "$SUMMARY"
printf '  Dataset summary: %s\n' "$DATASET_SUMMARY"
printf '  Input hashes: %s\n' "$INPUT_HASHES"
printf '  Provenance hashes: %s\n' "$HASHES"
