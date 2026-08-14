#!/usr/bin/env bash
# Compare Parser A0 (compatibility-and-lexicon baseline) with Parser A.

set -euo pipefail

readonly EXPECTED_SENTENCES=206
readonly EXPECTED_DONE_SENTENCES=174
readonly EXPECTED_REVIEW_SENTENCES=32

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency"

A0_COMPARISON="${A0_COMPARISON:-$OUT_DIR/kadiweu-parser-full-test-A0-comparison.tsv}"
A_COMPARISON="${A_COMPARISON:-$OUT_DIR/kadiweu-parser-full-test-A-comparison.tsv}"
A0_HASHES="${A0_HASHES:-$OUT_DIR/kadiweu-parser-full-test-A0-hashes.txt}"
A_HASHES="${A_HASHES:-$OUT_DIR/kadiweu-parser-full-test-A-hashes.txt}"
TRANSITIONS="$OUT_DIR/kadiweu-parser-full-test-A0-to-A-transitions.tsv"
SUMMARY="$OUT_DIR/kadiweu-parser-full-test-A0-to-A-summary.tsv"
HASHES="$OUT_DIR/kadiweu-parser-full-test-A0-to-A-hashes.txt"

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

require_file() {
    [[ -f "$1" ]] || die "required file not found: $1"
}

for command_name in python3 sha256sum; do
    command -v "$command_name" >/dev/null 2>&1 \
        || die "required command not found: $command_name"
done

for required in "$A0_COMPARISON" "$A_COMPARISON" "$A0_HASHES" "$A_HASHES"; do
    require_file "$required"
done

printf 'Verifying Parser A0 run artifacts...\n'
sha256sum -c "$A0_HASHES" || die "Parser A0 artifacts do not match their recorded hashes"

printf 'Verifying Parser A run artifacts...\n'
sha256sum -c "$A_HASHES" || die "Parser A artifacts do not match their recorded hashes"

python3 - "$A0_COMPARISON" "$A_COMPARISON" "$TRANSITIONS" "$SUMMARY" \
    "$EXPECTED_SENTENCES" "$EXPECTED_DONE_SENTENCES" "$EXPECTED_REVIEW_SENTENCES" <<'PY'
import csv
import sys
from collections import Counter
from pathlib import Path

a0_path, a_path, transitions_path, summary_path = map(Path, sys.argv[1:5])
expected = int(sys.argv[5])
expected_done = int(sys.argv[6])
expected_review = int(sys.argv[7])

RESULTS = {"EXACT_MATCH", "TRACE_EQUIVALENT", "STRUCTURAL_DIFFERENCE"}
STRUCTURAL = "STRUCTURAL_DIFFERENCE"


def load(path):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    required = {"sentence_id", "dataset", "struct_status", "result", "details"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit(f"invalid comparison-report columns in {path}")
    ids = [row["sentence_id"] for row in rows]
    if len(rows) != expected or len(set(ids)) != expected:
        raise SystemExit(f"{path} must contain {expected} rows with unique sentence IDs")
    unknown = sorted({row["result"] for row in rows} - RESULTS)
    if unknown:
        raise SystemExit(f"unknown result value(s) in {path}: {', '.join(unknown)}")
    counts = Counter(row["struct_status"] for row in rows)
    if counts["DONE"] != expected_done or counts["REVIEW"] != expected_review:
        raise SystemExit(
            f"{path} must contain DONE={expected_done} and REVIEW={expected_review}; "
            f"found DONE={counts['DONE']} and REVIEW={counts['REVIEW']}"
        )
    return rows, {row["sentence_id"]: row for row in rows}


def print_table(headers, rows, numeric_columns):
    text_rows = [[str(value) for value in row] for row in rows]
    widths = [
        max(len(headers[column]), *(len(row[column]) for row in text_rows))
        for column in range(len(headers))
    ]
    for row_number, row in enumerate([list(headers), *text_rows]):
        cells = []
        for column, value in enumerate(row):
            if row_number and column in numeric_columns:
                cells.append(value.rjust(widths[column]))
            else:
                cells.append(value.ljust(widths[column]))
        print("  ".join(cells))


a0_rows, a0 = load(a0_path)
a_rows, a = load(a_path)
if set(a0) != set(a):
    missing_from_a = sorted(set(a0) - set(a))
    missing_from_a0 = sorted(set(a) - set(a0))
    raise SystemExit(
        "A0 and A contain different sentence IDs; "
        f"missing from A={missing_from_a}; missing from A0={missing_from_a0}"
    )

for sid in a0:
    for field in ("dataset", "struct_status"):
        if a0[sid][field] != a[sid][field]:
            raise SystemExit(f"{field} differs between A0 and A for {sid}")

transition_fields = (
    "sentence_id", "dataset", "struct_status", "result_A0", "result_A",
    "coverage_classification", "details_changed"
)
transition_rows = []
for baseline_row in a0_rows:
    sid = baseline_row["sentence_id"]
    candidate_row = a[sid]
    baseline_result = baseline_row["result"]
    candidate_result = candidate_row["result"]
    if baseline_result == STRUCTURAL and candidate_result != STRUCTURAL:
        classification = "COVERAGE_IMPROVEMENT"
    elif baseline_result != STRUCTURAL and candidate_result == STRUCTURAL:
        classification = "COVERAGE_REGRESSION"
    elif baseline_result == STRUCTURAL and candidate_result == STRUCTURAL:
        classification = "PERSISTENT_STRUCTURAL"
    elif baseline_result != candidate_result:
        classification = "TRACE_ONLY_CHANGE"
    else:
        classification = "NO_RESULT_CATEGORY_CHANGE"
    transition_rows.append({
        "sentence_id": sid,
        "dataset": baseline_row["dataset"],
        "struct_status": baseline_row["struct_status"],
        "result_A0": baseline_result,
        "result_A": candidate_result,
        "coverage_classification": classification,
        "details_changed": "YES" if baseline_row["details"] != candidate_row["details"] else "NO",
    })

with transitions_path.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=transition_fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(transition_rows)

summary_headers = (
    "struct_status", "A0_structural", "A_structural", "improvements",
    "regressions", "persistent", "trace_only", "net_improvement", "total"
)
summary_rows = []
for status in ("DONE", "REVIEW", "TOTAL"):
    selected = transition_rows if status == "TOTAL" else [
        row for row in transition_rows if row["struct_status"] == status
    ]
    classes = Counter(row["coverage_classification"] for row in selected)
    improvements = classes["COVERAGE_IMPROVEMENT"]
    regressions = classes["COVERAGE_REGRESSION"]
    summary_rows.append((
        status,
        sum(row["result_A0"] == STRUCTURAL for row in selected),
        sum(row["result_A"] == STRUCTURAL for row in selected),
        improvements,
        regressions,
        classes["PERSISTENT_STRUCTURAL"],
        classes["TRACE_ONLY_CHANGE"],
        improvements - regressions,
        len(selected),
    ))

with summary_path.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(summary_headers)
    writer.writerows(summary_rows)

print("\nParser A0 to Parser A coverage transitions:")
print_table(summary_headers, summary_rows, numeric_columns=set(range(1, len(summary_headers))))

for status in ("DONE", "REVIEW"):
    improvements = [
        row["sentence_id"] for row in transition_rows
        if row["struct_status"] == status
        and row["coverage_classification"] == "COVERAGE_IMPROVEMENT"
    ]
    regressions = [
        row["sentence_id"] for row in transition_rows
        if row["struct_status"] == status
        and row["coverage_classification"] == "COVERAGE_REGRESSION"
    ]
    print(f"{status} coverage improvements:", ", ".join(improvements) or "none")
    print(f"{status} coverage regressions:", ", ".join(regressions) or "none")

print(
    "\nInterpret REVIEW transitions as candidates for manual adjudication, "
    "not as demonstrated linguistic improvements or regressions."
)
PY

sha256sum "$A0_COMPARISON" "$A_COMPARISON" "$TRANSITIONS" "$SUMMARY" > "$HASHES"

printf '\nA0-to-A comparison completed successfully.\n'
printf '  Sentence-level transitions: %s\n' "$TRANSITIONS"
printf '  Transition summary: %s\n' "$SUMMARY"
printf '  Provenance hashes: %s\n' "$HASHES"
