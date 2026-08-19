#!/usr/bin/env bash
# Run the Kadiweu toy parser through rule 1, rule 2, or all three rules.

set -euo pipefail

readonly EXPECTED_RULES_SHA256="f3f23696e7f47e3b3df681af94c5ba2bd3d51b277047dc8f9426026fbf695282"
readonly EXPECTED_INPUT_SHA256="30bb0817699d6d839ac5c7547a698915dcf55c7cc4af6e981f86daaaca6bfb5b"
readonly EXPECTED_GOLD_SHA256="f23053f856cb3b9061f4828821108590d1c399b443e08004cece733a70b2df03"
readonly EXPECTED_SENTENCES=6
readonly EXPECTED_DONE_SENTENCES=6
readonly EXPECTED_REVIEW_SENTENCES=0

usage() {
    cat >&2 <<EOF
Usage: ${0##*/} [--rules FILE] [all|LAST_RULE]

Run the toy parser through LAST_RULE:
  ${0##*/}                         run all rules from the default file
  ${0##*/} all                     run all rules from the default file
  ${0##*/} 2                       run rules 1 and 2 from the default file
  ${0##*/} 1                       run only rule 1 from the default file
  ${0##*/} --rules FILE all        run all rules from FILE
  ${0##*/} --rules FILE 2          run rules 1 and 2 from FILE

Options:
  -r, --rules FILE   use an alternative toy-parser rule file
  -h, --help         show this help
EOF
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
SRC_DIR="$PROJECT_ROOT/src"
TEST_DIR="$PROJECT_ROOT/tests/corpussearch-toy-parser"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency/corpussearch-toy-parser"
DEFAULT_RULES="$TEST_DIR/kadiweu_toy_parser_rules.txt"

RULES="${RULES:-$DEFAULT_RULES}"
requested_run="all"
run_argument_seen=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -r|--rules)
            [[ "$#" -ge 2 ]] || die "$1 requires a file path"
            RULES="$2"
            shift 2
            ;;
        --rules=*)
            RULES="${1#*=}"
            [[ -n "$RULES" ]] || die "--rules requires a nonempty file path"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        all)
            [[ "$run_argument_seen" == false ]] \
                || die "only one of all or LAST_RULE may be supplied"
            requested_run="$1"
            run_argument_seen=true
            shift
            ;;
        *)
            if [[ "$1" =~ ^[1-9][0-9]*$ ]]; then
                [[ "$run_argument_seen" == false ]] \
                    || die "only one of all or LAST_RULE may be supplied"
                requested_run="$1"
                run_argument_seen=true
                shift
            else
                usage
                die "unrecognized argument: $1"
            fi
            ;;
    esac
done

[[ -f "$RULES" ]] || die "rule file not found: $RULES"
last_available_rule="$(awk -F: '/^[0-9]+:/ {number = $1} END {print number}' "$RULES")"
[[ "$last_available_rule" =~ ^[1-9][0-9]*$ ]] \
    || die "no numbered rules found in: $RULES"

if [[ "$requested_run" == "all" ]]; then
    STOP_AFTER_RULE="$last_available_rule"
else
    STOP_AFTER_RULE="$requested_run"
fi
[[ "$STOP_AFTER_RULE" =~ ^[1-9][0-9]*$ ]] || {
    usage
    die "LAST_RULE must be a positive integer or all; found: $requested_run"
}
readonly STOP_AFTER_RULE

RUNNER="${RUNNER:-$SRC_DIR/run_kadiweu_parser_rules.py}"
INPUT="${INPUT:-$TEST_DIR/kadiweu-toy-parser.pos}"
GOLD="${GOLD:-$TEST_DIR/kadiweu-toy-parser.gold.psd}"
CORPUSSEARCH="${CORPUSSEARCH:-corpussearch}"

rules_filename="${RULES##*/}"
rules_stem="${rules_filename%.*}"
rules_label="$(printf '%s' "$rules_stem" | tr -cs '[:alnum:]_.-' '-')"
[[ -n "$rules_label" ]] || rules_label="rules"

if [[ "$RULES" == "$DEFAULT_RULES" ]]; then
    ARTIFACT_PREFIX="$OUT_DIR/kadiweu-toy-parser-through-rule-$STOP_AFTER_RULE"
else
    ARTIFACT_PREFIX="$OUT_DIR/kadiweu-toy-parser-$rules_label-through-rule-$STOP_AFTER_RULE"
fi
OUTPUT="$ARTIFACT_PREFIX.psd"
COMPARISON="$ARTIFACT_PREFIX-comparison.tsv"
DIFF="$ARTIFACT_PREFIX.diff"
RULE_LOG="$ARTIFACT_PREFIX-run.tsv"
SUMMARY="$ARTIFACT_PREFIX-summary.tsv"
HASHES="$ARTIFACT_PREFIX-hashes.txt"
CONSOLE_LOG="$ARTIFACT_PREFIX-console.log"

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

for required in "$RUNNER" "$RULES" "$INPUT" "$GOLD"; do
    require_file "$required"
done

rules_hash="$(actual_sha256 "$RULES")"
if [[ "$RULES" == "$DEFAULT_RULES" ]]; then
    [[ "$rules_hash" == "$EXPECTED_RULES_SHA256" ]] \
        || die "default toy-parser rules hash mismatch"
    printf 'Default toy-parser rules hash: OK\n'
else
    printf 'Experimental rules: %s\n' "$RULES"
    printf 'Experimental rules SHA-256: %s\n' "$rules_hash"
fi
[[ "$(actual_sha256 "$INPUT")" == "$EXPECTED_INPUT_SHA256" ]] \
    || die "toy-parser POS input hash mismatch"
[[ "$(actual_sha256 "$GOLD")" == "$EXPECTED_GOLD_SHA256" ]] \
    || die "toy-parser gold hash mismatch"
printf 'Toy-parser POS input and gold hashes: OK\n'

if ! EXPECTED_EXECUTED_RULES="$(
    python3 - "$RULES" "$STOP_AFTER_RULE" <<'PY'
import re
import sys
from pathlib import Path

rules_path = Path(sys.argv[1])
stop_after = int(sys.argv[2])
numbers = [
    int(match.group(1))
    for match in re.finditer(r"(?m)^(\d+):", rules_path.read_text(encoding="utf-8"))
]

if stop_after not in numbers:
    raise SystemExit(f"rule {stop_after} is absent from {rules_path}")

print(sum(number <= stop_after for number in numbers))
PY
)"; then
    die "cannot determine the executed-rule count through rule $STOP_AFTER_RULE"
fi
readonly EXPECTED_EXECUTED_RULES

mkdir -p "$OUT_DIR"
RUN_DIR="$(mktemp -d "$ARTIFACT_PREFIX-run-XXXXXXXX")"
printf 'Intermediate run directory: %s\n' "$RUN_DIR"

set +e
python3 -u "$RUNNER" \
    "$RULES" \
    "$INPUT" \
    --corpussearch "$CORPUSSEARCH" \
    --stop-after-rule "$STOP_AFTER_RULE" \
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

for artifact in "$OUTPUT" "$COMPARISON" "$DIFF" "$RULE_LOG" "$CONSOLE_LOG"; do
    require_file "$artifact"
done

comparison_rows="$(awk 'END {print NR - 1}' "$COMPARISON")"
rule_rows="$(awk 'END {print NR - 1}' "$RULE_LOG")"
[[ "$comparison_rows" -eq "$EXPECTED_SENTENCES" ]] \
    || die "expected $EXPECTED_SENTENCES comparison rows; found $comparison_rows"
[[ "$rule_rows" -eq "$EXPECTED_EXECUTED_RULES" ]] \
    || die "expected $EXPECTED_EXECUTED_RULES executed-rule rows; found $rule_rows"

python3 - "$COMPARISON" "$SUMMARY" "$EXPECTED_SENTENCES" "$STOP_AFTER_RULE" <<'PY'
import csv
import sys
from collections import Counter
from pathlib import Path

comparison = Path(sys.argv[1])
summary = Path(sys.argv[2])
expected = int(sys.argv[3])
stop_after_rule = int(sys.argv[4])

with comparison.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream, delimiter="\t"))

required = {"sentence_id", "struct_status", "result"}
if not rows or not required.issubset(rows[0]):
    raise SystemExit(f"invalid comparison-report columns in {comparison}")
if len(rows) != expected:
    raise SystemExit(f"expected {expected} comparison rows; found {len(rows)}")
if len({row["sentence_id"] for row in rows}) != expected:
    raise SystemExit("comparison report does not contain six unique IDs")
if any(row["struct_status"] != "DONE" for row in rows):
    raise SystemExit("all toy-suite records must have status DONE")

counts = Counter(row["result"] for row in rows)
lines = [
    "struct_status\texact\ttrace_equivalent\tstructural_difference\ttotal",
    "\t".join(map(str, (
        "DONE",
        counts["EXACT_MATCH"],
        counts["TRACE_EQUIVALENT"],
        counts["STRUCTURAL_DIFFERENCE"],
        len(rows),
    ))),
]
summary.write_text("\n".join(lines) + "\n", encoding="utf-8")

table = [line.split("\t") for line in lines]
widths = [max(len(row[column]) for row in table) for column in range(len(table[0]))]

print(f"\nToy parser through rule {stop_after_rule} comparison summary:")
for row_number, row in enumerate(table):
    formatted = [row[0].ljust(widths[0])]
    formatted.extend(
        value.ljust(widths[column]) if row_number == 0 else value.rjust(widths[column])
        for column, value in enumerate(row[1:], start=1)
    )
    print("  ".join(formatted))
PY

sha256sum \
    "$RULES" \
    "$INPUT" \
    "$GOLD" \
    "$OUTPUT" \
    "$COMPARISON" \
    "$DIFF" \
    "$RULE_LOG" \
    "$SUMMARY" \
    "$CONSOLE_LOG" \
    > "$HASHES"

printf '\nToy parser through rule %s completed successfully.\n' "$STOP_AFTER_RULE"
printf '  Emulator exit status: %s\n' "$runner_status"
printf '  Executed rules: %s\n' "$rule_rows"
printf '  Compared sentences: %s (DONE=%s; REVIEW=%s)\n' \
    "$comparison_rows" "$EXPECTED_DONE_SENTENCES" "$EXPECTED_REVIEW_SENTENCES"
printf '  Run directory: %s\n' "$RUN_DIR"
printf '  Output: %s\n' "$OUTPUT"
printf '  Comparison: %s\n' "$COMPARISON"
printf '  Structural diff: %s\n' "$DIFF"
printf '  Rule log: %s\n' "$RULE_LOG"
printf '  Summary: %s\n' "$SUMMARY"
printf '  Provenance hashes: %s\n' "$HASHES"
