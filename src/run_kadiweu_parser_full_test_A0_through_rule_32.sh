#!/usr/bin/env bash
# Run Parser A0 through rule 32 over the frozen full test.

set -euo pipefail

readonly EXPECTED_RULES_SHA256="0f1b403144a6b2ea7d08ae252341da3ba1c0bc93e937ae7c5d6180da32879752"
readonly EXPECTED_DEFINITIONS_SHA256="67765202a6721f4d2e269cbb5564cb4a676027a6218af05ef8f457f999d734ff"
readonly EXPECTED_SENTENCES=206
readonly EXPECTED_DONE_SENTENCES=174
readonly EXPECTED_REVIEW_SENTENCES=32
readonly STOP_AFTER_RULE=32
readonly EXPECTED_EXECUTED_RULES=32

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
SRC_DIR="$PROJECT_ROOT/src"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency"
RUNNER="${RUNNER:-$SRC_DIR/run_kadiweu_parser_rules.py}"
RULES_A0="${RULES_A0:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_300726.pdt-compat-lex-baseline.txt}"
DEFINITIONS="${DEFINITIONS:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_050726.txt}"
CORPUSSEARCH="${CORPUSSEARCH:-corpussearch}"

INPUT="$OUT_DIR/kadiweu-parser-full-test.pos"
GOLD="$OUT_DIR/kadiweu-parser-full-test.gold.psd"
INPUT_HASHES="$OUT_DIR/kadiweu-parser-full-test-input-hashes.txt"
OUTPUT="$OUT_DIR/kadiweu-parser-full-test-A0-through-rule-32.psd"
COMPARISON="$OUT_DIR/kadiweu-parser-full-test-A0-through-rule-32-comparison.tsv"
DIFF="$OUT_DIR/kadiweu-parser-full-test-A0-through-rule-32.diff"
RULE_LOG="$OUT_DIR/kadiweu-parser-full-test-A0-through-rule-32-run.tsv"
SUMMARY="$OUT_DIR/kadiweu-parser-full-test-A0-through-rule-32-summary.tsv"
HASHES="$OUT_DIR/kadiweu-parser-full-test-A0-through-rule-32-hashes.txt"
CONSOLE_LOG="$OUT_DIR/kadiweu-parser-full-test-A0-through-rule-32-console.log"

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

for required in "$RUNNER" "$RULES_A0" "$DEFINITIONS" "$INPUT" "$GOLD" "$INPUT_HASHES"; do
    require_file "$required"
done

printf 'Verifying frozen full-test inputs...\n'
(
    cd "$OUT_DIR"
    sha256sum -c "$(basename "$INPUT_HASHES")"
) || die "the frozen full-test inputs do not match their recorded hashes"

rules_hash="$(actual_sha256 "$RULES_A0")"
definitions_hash="$(actual_sha256 "$DEFINITIONS")"
[[ "$rules_hash" == "$EXPECTED_RULES_SHA256" ]] \
    || die "rules A0 hash mismatch: expected $EXPECTED_RULES_SHA256; found $rules_hash"
[[ "$definitions_hash" == "$EXPECTED_DEFINITIONS_SHA256" ]] \
    || die "definitions hash mismatch: expected $EXPECTED_DEFINITIONS_SHA256; found $definitions_hash"
printf 'Rules A0 and definitions hashes: OK\n'

# mktemp creates a new, empty directory, as required by the emulator.
RUN_DIR="$(mktemp -d "$OUT_DIR/kadiweu-parser-full-test-A0-through-rule-32-run-XXXXXXXX")"
printf 'Intermediate run directory: %s\n' "$RUN_DIR"

set +e
python3 -u "$RUNNER" \
    "$RULES_A0" \
    "$INPUT" \
    --definitions "$DEFINITIONS" \
    --corpussearch "$CORPUSSEARCH" \
    --skip-rule 77 \
    --skip-rule 122 \
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

python3 - "$COMPARISON" "$SUMMARY" "$EXPECTED_SENTENCES" "$EXPECTED_DONE_SENTENCES" "$EXPECTED_REVIEW_SENTENCES" <<'PY'
import csv
import sys
from collections import Counter
from pathlib import Path

comparison = Path(sys.argv[1])
summary = Path(sys.argv[2])
expected = int(sys.argv[3])
expected_done = int(sys.argv[4])
expected_review = int(sys.argv[5])

with comparison.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream, delimiter="\t"))

required = {"sentence_id", "dataset", "struct_status", "result", "details"}
if not rows or not required.issubset(rows[0]):
    raise SystemExit(f"invalid comparison-report columns in {comparison}")
if len(rows) != expected:
    raise SystemExit(f"expected {expected} comparison rows; found {len(rows)}")
ids = [row["sentence_id"] for row in rows]
if len(set(ids)) != expected:
    raise SystemExit("comparison report does not contain the expected number of unique IDs")

status_counts = Counter(row["struct_status"] for row in rows)
if status_counts["DONE"] != expected_done:
    raise SystemExit(f"expected {expected_done} DONE rows; found {status_counts['DONE']}")
if status_counts["REVIEW"] != expected_review:
    raise SystemExit(f"expected {expected_review} REVIEW rows; found {status_counts['REVIEW']}")

statuses = [status for status in ("DONE", "REVIEW") if any(r["struct_status"] == status for r in rows)]
statuses.extend(sorted({r["struct_status"] for r in rows} - set(statuses)))

lines = ["struct_status\texact\ttrace_equivalent\tstructural_difference\ttotal"]
for status in [*statuses, "TOTAL"]:
    selected = rows if status == "TOTAL" else [r for r in rows if r["struct_status"] == status]
    counts = Counter(r["result"] for r in selected)
    lines.append(
        "\t".join(
            map(str, (
                status,
                counts["EXACT_MATCH"],
                counts["TRACE_EQUIVALENT"],
                counts["STRUCTURAL_DIFFERENCE"],
                len(selected),
            ))
        )
    )

summary.write_text("\n".join(lines) + "\n", encoding="utf-8")

table = [line.split("\t") for line in lines]
widths = [max(len(row[column]) for row in table) for column in range(len(table[0]))]

print("\nParser A0 through rule 32 comparison summary:")
for row_number, row in enumerate(table):
    formatted = [row[0].ljust(widths[0])]
    formatted.extend(
        value.ljust(widths[column]) if row_number == 0 else value.rjust(widths[column])
        for column, value in enumerate(row[1:], start=1)
    )
    print("  ".join(formatted))
PY

sha256sum \
    "$RULES_A0" \
    "$DEFINITIONS" \
    "$INPUT" \
    "$GOLD" \
    "$OUTPUT" \
    "$COMPARISON" \
    "$DIFF" \
    "$RULE_LOG" \
    "$SUMMARY" \
    "$CONSOLE_LOG" \
    > "$HASHES"

printf '\nParser A0 through rule 32 full test completed successfully.\n'
printf '  Emulator exit status: %s\n' "$runner_status"
printf '  Executed rules: %s (stopped after rule %s; TBP rules 77 and 122 configured as skipped)\n' \
    "$rule_rows" "$STOP_AFTER_RULE"
printf '  Compared sentences: %s\n' "$comparison_rows"
printf '  Expected status totals: DONE=%s; REVIEW=%s\n' \
    "$EXPECTED_DONE_SENTENCES" "$EXPECTED_REVIEW_SENTENCES"
printf '  Run directory: %s\n' "$RUN_DIR"
printf '  Output: %s\n' "$OUTPUT"
printf '  Comparison: %s\n' "$COMPARISON"
printf '  Structural diff: %s\n' "$DIFF"
printf '  Rule log: %s\n' "$RULE_LOG"
printf '  Summary: %s\n' "$SUMMARY"
printf '  Provenance hashes: %s\n' "$HASHES"
