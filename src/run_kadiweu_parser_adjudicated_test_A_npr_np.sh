#!/usr/bin/env bash
# Run A+NPR against the same adjudicated Kadiwéu test set used for parser A.
#
# Candidate:
#   kadiweu_parser_300726.pdt.npr-np-test.txt
#   = original compatible parser A + rule 171 np-wrap-sister-npr-test
#
# The script compares:
#   1. A+NPR vs adjudicated gold; and
#   2. adjudicated parser-A output vs A+NPR output.
#
# It does NOT overwrite any kadiweu-parser-full-test-* artifact.

set -euo pipefail

readonly EXPECTED_GOLD_SHA256="a0409cfb8f4acd1b2610db2135b8ee8855b5bd7bb35b592982cb9384ac096985"
readonly EXPECTED_RULES_SHA256="aae745826f1ee4e174f5eb3a5584b9ff01a19604f92bae48d54073a5ce073b82"
readonly EXPECTED_DEFINITIONS_SHA256="67765202a6721f4d2e269cbb5564cb4a676027a6218af05ef8f457f999d734ff"
readonly EXPECTED_SENTENCES=182
readonly EXPECTED_DONE=170
readonly EXPECTED_REVIEW=12
readonly EXPECTED_EXECUTED_RULES=169

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
SRC_DIR="$PROJECT_ROOT/src"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency"

RUNNER="${RUNNER:-$SRC_DIR/run_kadiweu_parser_rules.py}"
RULES_NPR="${RULES_NPR:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.pdt.npr-np-test.txt}"
DEFINITIONS="${DEFINITIONS:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_050726.txt}"
CORPUSSEARCH="${CORPUSSEARCH:-corpussearch}"

GOLD="${ADJUDICATED_GOLD:-$OUT_DIR/kadiweu-parser-adjudicated-test.gold.psd}"
INPUT="$OUT_DIR/kadiweu-parser-adjudicated-test.pos"
INPUT_HASHES="$OUT_DIR/kadiweu-parser-adjudicated-test-input-hashes.txt"

ACCEPTED_OUTPUT="$OUT_DIR/kadiweu-parser-adjudicated-test-A.psd"
ACCEPTED_COMPARISON="$OUT_DIR/kadiweu-parser-adjudicated-test-A-comparison.tsv"

OUTPUT="$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np.psd"
COMPARISON="$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np-comparison.tsv"
DIFF="$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np.diff"
RULE_LOG="$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np-run.tsv"
SUMMARY="$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np-summary.tsv"
DATASET_SUMMARY="$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np-dataset-summary.tsv"
TRANSITIONS="$OUT_DIR/kadiweu-parser-adjudicated-test-A-to-A-npr-np-transitions.tsv"
TRANSITION_SUMMARY="$OUT_DIR/kadiweu-parser-adjudicated-test-A-to-A-npr-np-summary.tsv"
HASHES="$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np-hashes.txt"
CONSOLE_LOG="$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np-console.log"

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

for required in \
    "$RUNNER" \
    "$RULES_NPR" \
    "$DEFINITIONS" \
    "$GOLD" \
    "$INPUT" \
    "$INPUT_HASHES" \
    "$ACCEPTED_OUTPUT" \
    "$ACCEPTED_COMPARISON"
do
    require_file "$required"
done

printf 'Verifying adjudicated experiment inputs...\n'

gold_hash="$(actual_sha256 "$GOLD")"
rules_hash="$(actual_sha256 "$RULES_NPR")"
definitions_hash="$(actual_sha256 "$DEFINITIONS")"

[[ "$gold_hash" == "$EXPECTED_GOLD_SHA256" ]] \
    || die "adjudicated gold hash mismatch: expected $EXPECTED_GOLD_SHA256; found $gold_hash"

[[ "$rules_hash" == "$EXPECTED_RULES_SHA256" ]] \
    || die "A+NPR rules hash mismatch: expected $EXPECTED_RULES_SHA256; found $rules_hash"

[[ "$definitions_hash" == "$EXPECTED_DEFINITIONS_SHA256" ]] \
    || die "definitions hash mismatch: expected $EXPECTED_DEFINITIONS_SHA256; found $definitions_hash"

(
    cd "$OUT_DIR"
    sha256sum -c "$(basename "$INPUT_HASHES")"
) || die "adjudicated gold/POS no longer match the hashes recorded by the A run"

printf 'Adjudicated gold/POS, A+NPR rules, and definitions: OK\n'

# Confirm that gold, POS, accepted A output, and accepted A comparison all
# contain exactly the same 182 sentence IDs.
python3 - \
    "$RUNNER" \
    "$GOLD" \
    "$INPUT" \
    "$ACCEPTED_OUTPUT" \
    "$ACCEPTED_COMPARISON" \
    "$EXPECTED_SENTENCES" \
    "$EXPECTED_DONE" \
    "$EXPECTED_REVIEW" <<'PY'
import csv
import importlib.util
import sys
from collections import Counter
from pathlib import Path

runner_path = Path(sys.argv[1])
gold_path = Path(sys.argv[2])
pos_path = Path(sys.argv[3])
accepted_path = Path(sys.argv[4])
accepted_comparison_path = Path(sys.argv[5])
expected = int(sys.argv[6])
expected_done = int(sys.argv[7])
expected_review = int(sys.argv[8])

spec = importlib.util.spec_from_file_location("kadiweu_runner", runner_path)
if spec is None or spec.loader is None:
    raise SystemExit(f"cannot load runner module from {runner_path}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

gold_records = module.read_records(gold_path)
pos_records = module.read_records(pos_path)
accepted_records = module.read_records(accepted_path)

for label, records in (
    ("gold", gold_records),
    ("POS", pos_records),
    ("accepted A output", accepted_records),
):
    if len(records) != expected:
        raise SystemExit(
            f"{label} must contain {expected} records; found {len(records)}"
        )
    ids = [record.sentence_id for record in records]
    if len(set(ids)) != expected:
        raise SystemExit(f"{label} contains duplicate sentence IDs")

gold_ids = [record.sentence_id for record in gold_records]
if [record.sentence_id for record in pos_records] != gold_ids:
    raise SystemExit("POS IDs/order differ from adjudicated gold")
if [record.sentence_id for record in accepted_records] != gold_ids:
    raise SystemExit("accepted A output IDs/order differ from adjudicated gold")

statuses = Counter(module.record_status(record) for record in gold_records)
if statuses["DONE"] != expected_done or statuses["REVIEW"] != expected_review:
    raise SystemExit(
        "unexpected adjudicated status counts: "
        f"DONE={statuses['DONE']} REVIEW={statuses['REVIEW']}"
    )

with accepted_comparison_path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream, delimiter="\t"))

if len(rows) != expected:
    raise SystemExit(
        f"accepted A comparison must contain {expected} rows; found {len(rows)}"
    )

comparison_ids = [row["sentence_id"] for row in rows]

if len(set(comparison_ids)) != expected:
    raise SystemExit(
        "accepted A comparison contains duplicate sentence IDs"
    )

if set(comparison_ids) != set(gold_ids):
    missing = sorted(set(gold_ids) - set(comparison_ids))
    extra = sorted(set(comparison_ids) - set(gold_ids))
    raise SystemExit(
        "accepted A comparison and adjudicated gold contain different "
        f"sentence IDs; missing={missing}; extra={extra}"
    )

print(
    f"Validated common adjudicated population: {expected} records "
    f"(DONE={statuses['DONE']}, REVIEW={statuses['REVIEW']})"
)
PY

RUN_DIR="$(mktemp -d "$OUT_DIR/kadiweu-parser-adjudicated-test-A-npr-np-run-XXXXXXXX")"
printf 'Intermediate run directory: %s\n' "$RUN_DIR"

set +e
python3 -u "$RUNNER" \
    "$RULES_NPR" \
    "$INPUT" \
    --definitions "$DEFINITIONS" \
    --corpussearch "$CORPUSSEARCH" \
    --skip-rule 77 \
    --skip-rule 122 \
    --output "$OUTPUT" \
    --expected "$GOLD" \
    --comparison-report "$COMPARISON" \
    --diff "$DIFF" \
    --accepted-output "$ACCEPTED_OUTPUT" \
    --transition-report "$TRANSITIONS" \
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

for artifact in \
    "$OUTPUT" \
    "$COMPARISON" \
    "$DIFF" \
    "$RULE_LOG" \
    "$TRANSITIONS" \
    "$CONSOLE_LOG"
do
    require_file "$artifact"
done

comparison_rows="$(awk 'END {print NR - 1}' "$COMPARISON")"
rule_rows="$(awk 'END {print NR - 1}' "$RULE_LOG")"
transition_rows="$(awk 'END {print NR - 1}' "$TRANSITIONS")"

[[ "$comparison_rows" -eq "$EXPECTED_SENTENCES" ]] \
    || die "expected $EXPECTED_SENTENCES comparison rows; found $comparison_rows"

[[ "$rule_rows" -eq "$EXPECTED_EXECUTED_RULES" ]] \
    || die "expected $EXPECTED_EXECUTED_RULES executed-rule rows; found $rule_rows"

python3 - \
    "$COMPARISON" \
    "$TRANSITIONS" \
    "$SUMMARY" \
    "$DATASET_SUMMARY" \
    "$TRANSITION_SUMMARY" \
    "$EXPECTED_SENTENCES" <<'PY'
import csv
import sys
from collections import Counter
from pathlib import Path

comparison_path = Path(sys.argv[1])
transitions_path = Path(sys.argv[2])
summary_path = Path(sys.argv[3])
dataset_summary_path = Path(sys.argv[4])
transition_summary_path = Path(sys.argv[5])
expected = int(sys.argv[6])

with comparison_path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream, delimiter="\t"))

required = {"sentence_id", "dataset", "struct_status", "result", "details"}
if not rows or not required.issubset(rows[0]):
    raise SystemExit(f"invalid comparison-report columns in {comparison_path}")
if len(rows) != expected:
    raise SystemExit(f"expected {expected} comparison rows; found {len(rows)}")
ids = [row["sentence_id"] for row in rows]
if len(set(ids)) != expected:
    raise SystemExit("candidate comparison contains duplicate/missing IDs")

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
for dataset in sorted({row["dataset"] for row in rows}):
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

with transitions_path.open(encoding="utf-8", newline="") as stream:
    transitions = list(csv.DictReader(stream, delimiter="\t"))

transition_required = {
    "sentence_id",
    "dataset",
    "struct_status",
    "accepted_classification",
    "candidate_classification",
    "output_change_classification",
    "transition",
    "details",
}

if transitions:
    if not transition_required.issubset(transitions[0]):
        raise SystemExit(
            f"invalid transition-report columns in {transitions_path}"
        )
else:
    with transitions_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        header = next(reader, [])
    if not transition_required.issubset(set(header)):
        raise SystemExit(
            f"invalid transition-report header in {transitions_path}"
        )

transition_lines = ["struct_status\ttransition\tcount"]

transition_statuses = [
    s for s in ("DONE", "REVIEW")
    if any(r["struct_status"] == s for r in transitions)
]
transition_statuses.extend(
    sorted({r["struct_status"] for r in transitions} - set(transition_statuses))
)

for status in transition_statuses:
    selected = [r for r in transitions if r["struct_status"] == status]
    counts = Counter(r["transition"] for r in selected)
    for transition, count in sorted(counts.items()):
        transition_lines.append(f"{status}\t{transition}\t{count}")

total_counts = Counter(r["transition"] for r in transitions)
for transition, count in sorted(total_counts.items()):
    transition_lines.append(f"TOTAL\t{transition}\t{count}")

transition_lines.append(
    f"TOTAL\tALL_CHANGED_SENTENCES\t{len(transitions)}"
)

transition_summary_path.write_text(
    "\n".join(transition_lines) + "\n",
    encoding="utf-8",
)

print("\nAdjudicated A+NPR comparison against gold:")
print(summary_path.read_text(encoding="utf-8"), end="")
print("By dataset × status:")
print(dataset_summary_path.read_text(encoding="utf-8"), end="")
print("Adjudicated A -> A+NPR transition summary:")
print(transition_summary_path.read_text(encoding="utf-8"), end="")
PY

sha256sum \
    "$RULES_NPR" \
    "$DEFINITIONS" \
    "$GOLD" \
    "$INPUT" \
    "$ACCEPTED_OUTPUT" \
    "$ACCEPTED_COMPARISON" \
    "$OUTPUT" \
    "$COMPARISON" \
    "$DIFF" \
    "$RULE_LOG" \
    "$SUMMARY" \
    "$DATASET_SUMMARY" \
    "$TRANSITIONS" \
    "$TRANSITION_SUMMARY" \
    "$CONSOLE_LOG" \
    > "$HASHES"

printf '\nAdjudicated A+NPR experiment completed successfully.\n'
printf '  Emulator exit status: %s\n' "$runner_status"
printf '  Executed rules: %s (TBP rules 77 and 122 skipped; rule 171 added)\n' "$rule_rows"
printf '  Compared sentences: %s\n' "$comparison_rows"
printf '  Sentences changed from adjudicated A: %s\n' "$transition_rows"
printf '  Run directory: %s\n' "$RUN_DIR"
printf '  Adjudicated gold: %s\n' "$GOLD"
printf '  POS input: %s\n' "$INPUT"
printf '  Accepted adjudicated A output: %s\n' "$ACCEPTED_OUTPUT"
printf '  Candidate output: %s\n' "$OUTPUT"
printf '  Candidate-vs-gold comparison: %s\n' "$COMPARISON"
printf '  Candidate structural diff: %s\n' "$DIFF"
printf '  Rule log: %s\n' "$RULE_LOG"
printf '  Candidate summary: %s\n' "$SUMMARY"
printf '  Dataset summary: %s\n' "$DATASET_SUMMARY"
printf '  A-to-A+NPR transitions: %s\n' "$TRANSITIONS"
printf '  Transition summary: %s\n' "$TRANSITION_SUMMARY"
printf '  Console log: %s\n' "$CONSOLE_LOG"
printf '  Provenance hashes: %s\n' "$HASHES"
