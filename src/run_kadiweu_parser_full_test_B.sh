#!/usr/bin/env bash
# Run parser version B over the frozen 206-sentence test and compare it with A.

set -euo pipefail

readonly EXPECTED_RULES_SHA256="45f957f9d99c06b3bfff358ef666556a3b56f254958cb87ddd1b0900f4c7e0af"
readonly EXPECTED_DEFINITIONS_SHA256="46b3e1fb5512747d4c20aa5bdcf600af6ac6a6d6b639d9debe2155470a050222"
readonly EXPECTED_SENTENCES=206
readonly EXPECTED_EXECUTED_RULES=168

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
SRC_DIR="$PROJECT_ROOT/src"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency"
RUNNER="${RUNNER:-$SRC_DIR/run_kadiweu_parser_rules.py}"
RULES_B="${RULES_B:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_070826.corpussearch.txt}"
DEFINITIONS_B="${DEFINITIONS_B:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_070726.txt}"
CORPUSSEARCH="${CORPUSSEARCH:-corpussearch}"

INPUT="$OUT_DIR/kadiweu-parser-full-test.pos"
GOLD="$OUT_DIR/kadiweu-parser-full-test.gold.psd"
INPUT_HASHES="$OUT_DIR/kadiweu-parser-full-test-input-hashes.txt"
A_COMPARISON="$OUT_DIR/kadiweu-parser-full-test-A-comparison.tsv"
OUTPUT="$OUT_DIR/kadiweu-parser-full-test-B.psd"
COMPARISON="$OUT_DIR/kadiweu-parser-full-test-B-comparison.tsv"
DIFF="$OUT_DIR/kadiweu-parser-full-test-B.diff"
RULE_LOG="$OUT_DIR/kadiweu-parser-full-test-B-run.tsv"
SUMMARY="$OUT_DIR/kadiweu-parser-full-test-B-summary.tsv"
TRANSITIONS="$OUT_DIR/kadiweu-parser-full-test-A-to-B-transitions.tsv"
TRANSITION_SUMMARY="$OUT_DIR/kadiweu-parser-full-test-A-to-B-summary.tsv"
HASHES="$OUT_DIR/kadiweu-parser-full-test-B-hashes.txt"
CONSOLE_LOG="$OUT_DIR/kadiweu-parser-full-test-B-console.log"

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

for required in "$RUNNER" "$RULES_B" "$DEFINITIONS_B" "$INPUT" "$GOLD" \
    "$INPUT_HASHES" "$A_COMPARISON"; do
    require_file "$required"
done

printf 'Verifying frozen full-test inputs...\n'
(
    cd "$OUT_DIR"
    sha256sum -c "$(basename "$INPUT_HASHES")"
) || die "the frozen full-test inputs do not match their recorded hashes"

rules_hash="$(actual_sha256 "$RULES_B")"
definitions_hash="$(actual_sha256 "$DEFINITIONS_B")"
[[ "$rules_hash" == "$EXPECTED_RULES_SHA256" ]] \
    || die "rules B hash mismatch: expected $EXPECTED_RULES_SHA256; found $rules_hash"
[[ "$definitions_hash" == "$EXPECTED_DEFINITIONS_SHA256" ]] \
    || die "definitions B hash mismatch: expected $EXPECTED_DEFINITIONS_SHA256; found $definitions_hash"
printf 'Rules B and definitions B hashes: OK\n'

# mktemp creates the new, empty work directory required by the emulator.
RUN_DIR="$(mktemp -d "$OUT_DIR/kadiweu-parser-full-test-B-run-XXXXXXXX")"
printf 'Intermediate run directory: %s\n' "$RUN_DIR"

set +e
python3 -u "$RUNNER" \
    "$RULES_B" \
    "$INPUT" \
    --definitions "$DEFINITIONS_B" \
    --corpussearch "$CORPUSSEARCH" \
    --skip-rule 30 \
    --skip-rule 78 \
    --skip-rule 123 \
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
    0) printf 'Emulator completed with no structural differences against gold.\n' ;;
    1) printf 'Emulator completed; structural differences against gold were found.\n' ;;
    2) die "emulator execution/configuration failure; see $CONSOLE_LOG and $RUN_DIR" ;;
    *) die "unexpected emulator exit status $runner_status; see $CONSOLE_LOG" ;;
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

python3 - "$A_COMPARISON" "$COMPARISON" "$SUMMARY" "$TRANSITIONS" \
    "$TRANSITION_SUMMARY" "$EXPECTED_SENTENCES" <<'PY'
import csv
import sys
from collections import Counter
from pathlib import Path

a_path, b_path, summary_path, transitions_path, transition_summary_path = map(Path, sys.argv[1:6])
expected = int(sys.argv[6])

def load(path):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    required = {"sentence_id", "dataset", "struct_status", "result", "details"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit(f"invalid comparison-report columns in {path}")
    ids = [row["sentence_id"] for row in rows]
    if len(rows) != expected or len(set(ids)) != expected:
        raise SystemExit(f"{path} must contain {expected} rows with unique sentence IDs")
    return {row["sentence_id"]: row for row in rows}

def print_table(headers, rows, numeric_columns):
    """Print aligned columns while leaving the saved TSV representation intact."""
    text_rows = [[str(value) for value in row] for row in rows]
    widths = [
        max(len(headers[column]), *(len(row[column]) for row in text_rows))
        for column in range(len(headers))
    ]
    formats = [
        f"{{:>{width}}}" if column in numeric_columns else f"{{:<{width}}}"
        for column, width in enumerate(widths)
    ]
    print("  ".join(formats[column].format(header)
                    for column, header in enumerate(headers)))
    for row in text_rows:
        print("  ".join(formats[column].format(value)
                        for column, value in enumerate(row)))

a = load(a_path)
b = load(b_path)
if set(a) != set(b):
    raise SystemExit("A and B comparison reports contain different sentence IDs")
for sid in a:
    if a[sid]["struct_status"] != b[sid]["struct_status"]:
        raise SystemExit(f"struct_status differs between A and B for {sid}")

result_order = ("EXACT_MATCH", "TRACE_EQUIVALENT", "STRUCTURAL_DIFFERENCE")
statuses = ("DONE", "REVIEW", "TOTAL")

# B-versus-gold summary.
summary_headers = (
    "struct_status", "exact", "trace_equivalent", "structural_difference", "total"
)
summary_rows = []
for status in statuses:
    rows = list(b.values()) if status == "TOTAL" else [r for r in b.values() if r["struct_status"] == status]
    counts = Counter(r["result"] for r in rows)
    summary_rows.append((
        status, counts[result_order[0]], counts[result_order[1]], counts[result_order[2]], len(rows)
    ))
with summary_path.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(summary_headers)
    writer.writerows(summary_rows)

# Sentence-level A-to-B transitions.
transition_fields = (
    "sentence_id", "dataset", "struct_status", "result_A", "result_B", "classification"
)
transition_rows = []
structural = "STRUCTURAL_DIFFERENCE"
for sid in sorted(a):
    ar, br = a[sid], b[sid]
    if ar["result"] == structural and br["result"] != structural:
        classification = "IMPROVEMENT"
    elif ar["result"] != structural and br["result"] == structural:
        classification = "REGRESSION"
    elif ar["result"] == structural and br["result"] == structural:
        classification = "PERSISTENT_STRUCTURAL"
    elif ar["result"] != br["result"]:
        classification = "STRUCTURALLY_NEUTRAL_CHANGE"
    else:
        classification = "UNCHANGED"
    transition_rows.append({
        "sentence_id": sid,
        "dataset": ar["dataset"],
        "struct_status": ar["struct_status"],
        "result_A": ar["result"],
        "result_B": br["result"],
        "classification": classification,
    })

with transitions_path.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=transition_fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(transition_rows)

transition_summary_headers = (
    "struct_status", "A_structural", "B_structural", "improvements",
    "regressions", "persistent", "net_improvement", "total"
)
transition_summary_rows = []
for status in statuses:
    selected = transition_rows if status == "TOTAL" else [r for r in transition_rows if r["struct_status"] == status]
    classes = Counter(r["classification"] for r in selected)
    a_structural = sum(r["result_A"] == structural for r in selected)
    b_structural = sum(r["result_B"] == structural for r in selected)
    improvements = classes["IMPROVEMENT"]
    regressions = classes["REGRESSION"]
    transition_summary_rows.append((
        status, a_structural, b_structural, improvements, regressions,
        classes["PERSISTENT_STRUCTURAL"], improvements - regressions, len(selected)
    ))
with transition_summary_path.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(transition_summary_headers)
    writer.writerows(transition_summary_rows)

print("\nParser B comparison with gold:")
print_table(summary_headers, summary_rows, numeric_columns={1, 2, 3, 4})
print("\nParser A to B structural transitions:")
print_table(
    transition_summary_headers,
    transition_summary_rows,
    numeric_columns={1, 2, 3, 4, 5, 6, 7},
)

done_regressions = [r["sentence_id"] for r in transition_rows
                    if r["struct_status"] == "DONE" and r["classification"] == "REGRESSION"]
done_improvements = [r["sentence_id"] for r in transition_rows
                     if r["struct_status"] == "DONE" and r["classification"] == "IMPROVEMENT"]
print("DONE improvements:", ", ".join(done_improvements) or "none")
print("DONE regressions:", ", ".join(done_regressions) or "none")
PY

sha256sum \
    "$RULES_B" "$DEFINITIONS_B" "$INPUT" "$GOLD" "$A_COMPARISON" \
    "$OUTPUT" "$COMPARISON" "$DIFF" "$RULE_LOG" "$SUMMARY" \
    "$TRANSITIONS" "$TRANSITION_SUMMARY" "$CONSOLE_LOG" \
    > "$HASHES"

printf '\nParser B experiment completed successfully.\n'
printf '  Emulator exit status: %s\n' "$runner_status"
printf '  Executed rules: %s (TBP Rule 30 [nbar10], Rule 78 [ip-xp], and Rule 123 [CP-D] skipped)\n' "$rule_rows"
printf '  Compared sentences: %s\n' "$comparison_rows"
printf '  Run directory: %s\n' "$RUN_DIR"
printf '  Output: %s\n' "$OUTPUT"
printf '  Comparison with gold: %s\n' "$COMPARISON"
printf '  Structural diff: %s\n' "$DIFF"
printf '  Rule log: %s\n' "$RULE_LOG"
printf '  B summary: %s\n' "$SUMMARY"
printf '  A-to-B transitions: %s\n' "$TRANSITIONS"
printf '  A-to-B summary: %s\n' "$TRANSITION_SUMMARY"
printf '  Provenance hashes: %s\n' "$HASHES"
