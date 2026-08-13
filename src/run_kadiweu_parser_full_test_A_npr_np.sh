#!/usr/bin/env bash
# Run the controlled full-corpus NPR-possessor experiment:
# accepted parser A = kadiweu_parser_300726.pdt.txt output
# candidate A+NPR = the same parser plus TBP rule 171 (np-wrap-sister-npr-test)
#
# Experimental controls:
#   - frozen 206-sentence POS input and gold PSD
#   - kadiweu_parser_definitions_050726.txt
#   - TBP rules 77 and 122 skipped
#   - accepted A output produced by run_kadiweu_parser_full_test_A.sh
#
# The candidate is evaluated:
#   1. against the frozen gold reference; and
#   2. directly against the accepted A output, producing an impact/transition TSV.

set -euo pipefail

readonly EXPECTED_RULES_SHA256="aae745826f1ee4e174f5eb3a5584b9ff01a19604f92bae48d54073a5ce073b82"
readonly EXPECTED_DEFINITIONS_SHA256="67765202a6721f4d2e269cbb5564cb4a676027a6218af05ef8f457f999d734ff"
readonly EXPECTED_SENTENCES=206
readonly EXPECTED_EXECUTED_RULES=169

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
SRC_DIR="$PROJECT_ROOT/src"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency"

RUNNER="${RUNNER:-$SRC_DIR/run_kadiweu_parser_rules.py}"
RULES_NPR="${RULES_NPR:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.pdt.npr-np-test.txt}"
DEFINITIONS="${DEFINITIONS:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_050726.txt}"
CORPUSSEARCH="${CORPUSSEARCH:-corpussearch}"

INPUT="$OUT_DIR/kadiweu-parser-full-test.pos"
GOLD="$OUT_DIR/kadiweu-parser-full-test.gold.psd"
INPUT_HASHES="$OUT_DIR/kadiweu-parser-full-test-input-hashes.txt"

# Freshly reproduced accepted parser-A output.
ACCEPTED_OUTPUT="$OUT_DIR/kadiweu-parser-full-test-A.psd"

# Candidate A+NPR artifacts.
OUTPUT="$OUT_DIR/kadiweu-parser-full-test-A-npr-np.psd"
COMPARISON="$OUT_DIR/kadiweu-parser-full-test-A-npr-np-comparison.tsv"
DIFF="$OUT_DIR/kadiweu-parser-full-test-A-npr-np.diff"
RULE_LOG="$OUT_DIR/kadiweu-parser-full-test-A-npr-np-run.tsv"
SUMMARY="$OUT_DIR/kadiweu-parser-full-test-A-npr-np-summary.tsv"
TRANSITIONS="$OUT_DIR/kadiweu-parser-full-test-A-to-A-npr-np-transitions.tsv"
TRANSITION_SUMMARY="$OUT_DIR/kadiweu-parser-full-test-A-to-A-npr-np-summary.tsv"
HASHES="$OUT_DIR/kadiweu-parser-full-test-A-npr-np-hashes.txt"
CONSOLE_LOG="$OUT_DIR/kadiweu-parser-full-test-A-npr-np-console.log"

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
    "$INPUT" \
    "$GOLD" \
    "$INPUT_HASHES" \
    "$ACCEPTED_OUTPUT"
do
    require_file "$required"
done

printf 'Verifying frozen full-test inputs...\n'
(
    cd "$OUT_DIR"
    sha256sum -c "$(basename "$INPUT_HASHES")"
) || die "the frozen full-test inputs do not match their recorded hashes"

rules_hash="$(actual_sha256 "$RULES_NPR")"
definitions_hash="$(actual_sha256 "$DEFINITIONS")"

[[ "$rules_hash" == "$EXPECTED_RULES_SHA256" ]] \
    || die "A+NPR rules hash mismatch: expected $EXPECTED_RULES_SHA256; found $rules_hash"

[[ "$definitions_hash" == "$EXPECTED_DEFINITIONS_SHA256" ]] \
    || die "definitions hash mismatch: expected $EXPECTED_DEFINITIONS_SHA256; found $definitions_hash"

printf 'A+NPR rules and definitions hashes: OK\n'

# mktemp creates the new, empty work directory required by the emulator.
RUN_DIR="$(mktemp -d "$OUT_DIR/kadiweu-parser-full-test-A-npr-np-run-XXXXXXXX")"
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
        printf 'Emulator completed with no structural differences against gold.\n'
        ;;
    1)
        printf 'Emulator completed; structural differences against gold were found.\n'
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

# Build:
#   1. candidate-versus-gold summary; and
#   2. direct A-to-A+NPR transition summary.
python3 - \
    "$COMPARISON" \
    "$TRANSITIONS" \
    "$SUMMARY" \
    "$TRANSITION_SUMMARY" \
    "$EXPECTED_SENTENCES" <<'PY'
import csv
import sys
from collections import Counter
from pathlib import Path

comparison_path = Path(sys.argv[1])
transitions_path = Path(sys.argv[2])
summary_path = Path(sys.argv[3])
transition_summary_path = Path(sys.argv[4])
expected = int(sys.argv[5])

RESULT_ORDER = (
    "EXACT_MATCH",
    "TRACE_EQUIVALENT",
    "STRUCTURAL_DIFFERENCE",
)

with comparison_path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream, delimiter="\t"))

required = {
    "sentence_id",
    "dataset",
    "struct_status",
    "result",
    "details",
}
if not rows or not required.issubset(rows[0]):
    raise SystemExit(
        f"invalid comparison-report columns in {comparison_path}"
    )

if len(rows) != expected:
    raise SystemExit(
        f"expected {expected} comparison rows; found {len(rows)}"
    )

ids = [row["sentence_id"] for row in rows]
if len(set(ids)) != expected:
    raise SystemExit(
        "comparison report does not contain the expected number of unique IDs"
    )

statuses = [
    status
    for status in ("DONE", "REVIEW")
    if any(row["struct_status"] == status for row in rows)
]
statuses.extend(
    sorted(
        {row["struct_status"] for row in rows}
        - set(statuses)
    )
)

summary_lines = [
    "struct_status\texact\ttrace_equivalent\tstructural_difference\ttotal"
]

for status in [*statuses, "TOTAL"]:
    selected = (
        rows
        if status == "TOTAL"
        else [
            row
            for row in rows
            if row["struct_status"] == status
        ]
    )
    counts = Counter(row["result"] for row in selected)
    summary_lines.append(
        "\t".join(
            map(
                str,
                (
                    status,
                    counts["EXACT_MATCH"],
                    counts["TRACE_EQUIVALENT"],
                    counts["STRUCTURAL_DIFFERENCE"],
                    len(selected),
                ),
            )
        )
    )

summary_path.write_text(
    "\n".join(summary_lines) + "\n",
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

# A header-only transition report is valid if rule 171 changes no sentence.
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

transition_lines = [
    "struct_status\ttransition\tcount"
]

transition_statuses = [
    status
    for status in ("DONE", "REVIEW")
    if any(row["struct_status"] == status for row in transitions)
]
transition_statuses.extend(
    sorted(
        {row["struct_status"] for row in transitions}
        - set(transition_statuses)
    )
)

for status in transition_statuses:
    selected = [
        row
        for row in transitions
        if row["struct_status"] == status
    ]
    counts = Counter(row["transition"] for row in selected)
    for transition, count in sorted(counts.items()):
        transition_lines.append(
            f"{status}\t{transition}\t{count}"
        )

total_counts = Counter(
    row["transition"]
    for row in transitions
)
for transition, count in sorted(total_counts.items()):
    transition_lines.append(
        f"TOTAL\t{transition}\t{count}"
    )

transition_lines.append(
    f"TOTAL\tALL_CHANGED_SENTENCES\t{len(transitions)}"
)

transition_summary_path.write_text(
    "\n".join(transition_lines) + "\n",
    encoding="utf-8",
)

print("\nA+NPR comparison against gold:")
print(summary_path.read_text(encoding="utf-8"), end="")

print("A -> A+NPR transition summary:")
print(
    transition_summary_path.read_text(encoding="utf-8"),
    end="",
)
PY

require_file "$SUMMARY"
require_file "$TRANSITION_SUMMARY"

sha256sum \
    "$RULES_NPR" \
    "$DEFINITIONS" \
    "$INPUT" \
    "$GOLD" \
    "$ACCEPTED_OUTPUT" \
    "$OUTPUT" \
    "$COMPARISON" \
    "$DIFF" \
    "$RULE_LOG" \
    "$SUMMARY" \
    "$TRANSITIONS" \
    "$TRANSITION_SUMMARY" \
    "$CONSOLE_LOG" \
    > "$HASHES"

printf '\nA+NPR full-test experiment completed successfully.\n'
printf '  Emulator exit status: %s\n' "$runner_status"
printf '  Executed rules: %s (TBP rules 77 and 122 skipped; rule 171 added)\n' "$rule_rows"
printf '  Compared sentences: %s\n' "$comparison_rows"
printf '  Sentences changed from A: %s\n' "$transition_rows"
printf '  Run directory: %s\n' "$RUN_DIR"
printf '  Accepted A output: %s\n' "$ACCEPTED_OUTPUT"
printf '  Candidate output: %s\n' "$OUTPUT"
printf '  Candidate-vs-gold comparison: %s\n' "$COMPARISON"
printf '  Candidate structural diff: %s\n' "$DIFF"
printf '  Rule log: %s\n' "$RULE_LOG"
printf '  Candidate summary: %s\n' "$SUMMARY"
printf '  A-to-A+NPR transitions: %s\n' "$TRANSITIONS"
printf '  Transition summary: %s\n' "$TRANSITION_SUMMARY"
printf '  Console log: %s\n' "$CONSOLE_LOG"
printf '  Provenance hashes: %s\n' "$HASHES"
