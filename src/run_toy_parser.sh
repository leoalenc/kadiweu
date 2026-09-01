#!/usr/bin/env bash
# Run a CorpusSearch toy-parser experiment for any language.

set -euo pipefail

usage() {
    cat >&2 <<EOF
Usage: ${0##*/} --rules FILE --input FILE --gold FILE [OPTIONS] [all|LAST_RULE]

Run every rule (all, the default), or stop after LAST_RULE, inclusive.
Input and gold must contain the same sentence IDs in the same order.

Options:
  -r, --rules FILE   numbered parser rules (required)
  -i, --input FILE   flat POS input (required)
  -g, --gold FILE    reference PSD trees (required)
  -o, --output-dir DIR
                    output directory (default: project data/generated/constituency/corpussearch-toy-parser)
  --name NAME       output basename before -through-rule-N; no directory components
  --runner FILE     parser runner (default: beside this script)
  --corpussearch COMMAND
                    CorpusSearch executable (default: corpussearch)
  --tree-format FORMAT
                    additional tree output: psd, pdf, svg, png, or dot
                    repeat to generate several formats; disabled by default
                    psd: tree displays inside metadata comments
                    graphics: one numbered file per sentence, with metadata
  --pdf-layout LAYOUT
                    separate (default), combined, or both; requires --tree-format pdf
                    combined: one multipage PDF in PSD record order
                    both: retain individual PDFs and the combined PDF
                    combined/both require pdfunite (Ubuntu: poppler-utils)
  --tree-style STYLE
                    text-tree style for annotated PSD: ascii (default), unicode
  --tree-script FILE
                    path to kadiweu_psd_tree.py (default: beside this script)
  -h, --help         show this help

Example (from tests/corpussearch-toy-parser):
  bash ../../src/${0##*/} --rules russian_toy_parser_rules.txt \\
    --input russian-toy-parser.pos --gold russian-toy-parser.gold.psd \\
    --tree-format pdf --pdf-layout combined all

The ordinary PSD and existing reports are always generated as before.
Additional files use the same output directory and run prefix:
  PREFIX-trees.pdf (combined PDF)
  PREFIX.with-trees.psd
  PREFIX-trees/000001.pdf, 000002.pdf, ... (in PSD record order)
Graphical output requires kadiweu_constituency.py and Graphviz (except DOT).
Annotated PSD requires kadiweu_constituency.py but not Graphviz.
EOF
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${TOY_PARSER_ROOT:-$(dirname -- "$SCRIPT_DIR")}"
SRC_DIR="$SCRIPT_DIR"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency/corpussearch-toy-parser"
RULES="${RULES:-}"
INPUT="${INPUT:-}"
GOLD="${GOLD:-}"
OUTPUT_NAME=""
requested_run="all"
run_argument_seen=false
TREE_FORMATS=()
PDF_LAYOUT="separate"
pdf_layout_seen=false
TREE_STYLE="ascii"
TREE_SCRIPT="$SRC_DIR/kadiweu_psd_tree.py"

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
        -i|--input)
            [[ "$#" -ge 2 ]] || die "$1 requires a file path"
            INPUT="$2"
            shift 2
            ;;
        --input=*)
            INPUT="${1#*=}"
            [[ -n "$INPUT" ]] || die "--input requires a nonempty file path"
            shift
            ;;
        -g|--gold)
            [[ "$#" -ge 2 ]] || die "$1 requires a file path"
            GOLD="$2"
            shift 2
            ;;
        --gold=*)
            GOLD="${1#*=}"
            [[ -n "$GOLD" ]] || die "--gold requires a nonempty file path"
            shift
            ;;
        -o|--output-dir|--output-dir=*|--name|--name=*|--runner|--runner=*|--corpussearch|--corpussearch=*|--pdf-layout|--pdf-layout=*|--tree-format|--tree-style|--tree-script|--tree-format=*|--tree-style=*|--tree-script=*)
            option="${1%%=*}"
            if [[ "$1" == *=* ]]; then
                value="${1#*=}"
                shift
            else
                [[ "$#" -ge 2 ]] || die "$1 requires a value"
                value="$2"
                shift 2
            fi
            [[ -n "$value" && "$value" != --* ]] || die "$option requires a value"
            case "$option" in
                -o|--output-dir) OUT_DIR="$value" ;;
                --name) OUTPUT_NAME="$value" ;;
                --runner) RUNNER="$value" ;;
                --corpussearch) CORPUSSEARCH="$value" ;;
                --tree-format)
                    case "$value" in
                        psd|pdf|svg|png|dot) ;;
                        *) die "unsupported tree format: $value (use psd, pdf, svg, png, or dot)" ;;
                    esac
                    # Ignore repeats of the same format.
                    if [[ " ${TREE_FORMATS[*]-} " != *" $value "* ]]; then
                        TREE_FORMATS+=("$value")
                    fi
                    ;;
                --pdf-layout)
                    case "$value" in
                        separate|combined|both) PDF_LAYOUT="$value" ;;
                        *) die "unsupported PDF layout: $value (use separate, combined, or both)" ;;
                    esac
                    pdf_layout_seen=true
                    ;;
                --tree-style)
                    case "$value" in
                        ascii|unicode) TREE_STYLE="$value" ;;
                        *) die "unsupported tree style: $value (use ascii or unicode)" ;;
                    esac
                    ;;
                --tree-script) TREE_SCRIPT="$value" ;;
            esac
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

if [[ "$pdf_layout_seen" == true && " ${TREE_FORMATS[*]-} " != *" pdf "* ]]; then
    die "--pdf-layout requires --tree-format pdf"
fi

[[ -n "$RULES" ]] || die "--rules FILE is required"
[[ -n "$INPUT" ]] || die "--input FILE is required"
[[ -n "$GOLD" ]] || die "--gold FILE is required"
if [[ -n "$OUTPUT_NAME" ]]; then
    [[ "$OUTPUT_NAME" =~ ^[[:alnum:]_][[:alnum:]_.-]*$ ]] \
        || die "--name must start with a letter, digit, or underscore and contain only letters, digits, underscores, dots, or hyphens"
fi

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
CORPUSSEARCH="${CORPUSSEARCH:-corpussearch}"

rules_filename="${RULES##*/}"
rules_stem="${rules_filename%.*}"
rules_label="$(printf '%s' "$rules_stem" | tr -cs '[:alnum:]_.-' '-')"
[[ -n "$rules_label" ]] || rules_label="rules"

input_filename="${INPUT##*/}"
input_stem="${input_filename%.txt}"
input_stem="${input_stem%.pos}"
input_stem="$(printf '%s' "$input_stem" | tr -cs '[:alnum:]_.-' '-')"
[[ -n "$input_stem" ]] || input_stem="toy-parser"
if [[ -z "$OUTPUT_NAME" ]]; then
    OUTPUT_NAME="$input_stem"
    # Avoid repeating the language for the conventional matching rules file.
    if [[ "$rules_stem" != "${input_stem//-/_}_rules" ]]; then
        OUTPUT_NAME+="-$rules_label"
    fi
fi
ARTIFACT_PREFIX="$OUT_DIR/$OUTPUT_NAME-through-rule-$STOP_AFTER_RULE"
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

for command_name in python3 sha256sum awk mktemp tee; do
    command -v "$command_name" >/dev/null 2>&1 \
        || die "required command not found: $command_name"
done
command -v "$CORPUSSEARCH" >/dev/null 2>&1 \
    || die "CorpusSearch command not found: $CORPUSSEARCH"

for required in "$RUNNER" "$RULES" "$INPUT" "$GOLD"; do
    require_file "$required"
done

# Check optional rendering dependencies before the potentially long parser run.
if [[ "${#TREE_FORMATS[@]}" -gt 0 ]]; then
    if [[ "$PDF_LAYOUT" != separate ]]; then
        command -v pdfunite >/dev/null 2>&1 \
            || die "combined PDF output requires pdfunite (Ubuntu: sudo apt install poppler-utils)"
    fi
    require_file "$TREE_SCRIPT"
    python3 "$TREE_SCRIPT" --help >/dev/null \
        || die "cannot load tree script and its kadiweu_constituency.py dependency: $TREE_SCRIPT"
    for tree_format in "${TREE_FORMATS[@]}"; do
        case "$tree_format" in
            pdf|svg|png)
                command -v dot >/dev/null 2>&1 || die "Graphviz dot is required for $tree_format output"
                ;;
        esac
    done
fi

printf 'Rules: %s\nInput: %s\nGold: %s\n' "$RULES" "$INPUT" "$GOLD"
# Read IDs independently of line breaks; ignore metadata comments.
if ! EXPECTED_SENTENCE_COUNT="$(python3 - "$INPUT" "$GOLD" <<'PYIDS'
import re
import sys
from pathlib import Path

def ids(path):
    text = Path(path).read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    values = re.findall(r"\(\s*ID\s+([^\s()]+)\s*\)", text)
    if not values:
        raise SystemExit(f"no (ID ...) records found in {path}")
    if len(set(values)) != len(values):
        raise SystemExit(f"duplicate sentence IDs in {path}")
    return values

source, gold = map(ids, sys.argv[1:])
if source != gold:
    raise SystemExit("input/gold sentence IDs differ in count, identity, or order")
print(len(gold))
PYIDS
)"; then
    die "input/gold alignment validation failed"
fi
printf 'Aligned records: %s\n' "$EXPECTED_SENTENCE_COUNT"
readonly EXPECTED_SENTENCE_COUNT

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
pipeline_status=("${PIPESTATUS[@]}")
runner_status=${pipeline_status[0]}
set -e

[[ "${pipeline_status[1]}" -eq 0 ]] || die "cannot write console log: $CONSOLE_LOG"

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
[[ "$comparison_rows" -eq "$EXPECTED_SENTENCE_COUNT" ]] \
    || die "expected $EXPECTED_SENTENCE_COUNT comparison rows; found $comparison_rows"
[[ "$rule_rows" -eq "$EXPECTED_EXECUTED_RULES" ]] \
    || die "expected $EXPECTED_EXECUTED_RULES executed-rule rows; found $rule_rows"

python3 - "$COMPARISON" "$SUMMARY" "$EXPECTED_SENTENCE_COUNT" "$STOP_AFTER_RULE" <<'PY'
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
    raise SystemExit(f"comparison report does not contain {expected} unique IDs")

status_counts = Counter(row["struct_status"] for row in rows)
counts = Counter(row["result"] for row in rows)
status_label = (
    next(iter(status_counts))
    if len(status_counts) == 1
    else "+".join(f"{status}={count}" for status, count in sorted(status_counts.items()))
)
lines = [
    "struct_status\texact\ttrace_equivalent\tstructural_difference\ttotal",
    "\t".join(map(str, (
        status_label,
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

printf '\nParsing and comparison through rule %s completed.\n' "$STOP_AFTER_RULE"
printf '  Emulator exit status: %s\n' "$runner_status"
printf '  Executed rules: %s\n' "$rule_rows"
printf '  Compared sentences: %s\n' "$comparison_rows"
printf '  Run directory: %s\n' "$RUN_DIR"
printf '  Output: %s\n' "$OUTPUT"
printf '  Comparison: %s\n' "$COMPARISON"
printf '  Structural diff: %s\n' "$DIFF"
printf '  Rule log: %s\n' "$RULE_LOG"
printf '  Summary: %s\n' "$SUMMARY"
printf '  Provenance hashes: %s\n' "$HASHES"

# Render the parser output, never the gold trees. Comparison differences (runner
# status 1) are valid results and therefore also receive requested tree displays.
if [[ "${#TREE_FORMATS[@]}" -gt 0 ]]; then
    # Remove only temporary files created by this invocation, even on failure.
    pdf_temp_dir=""
    trap 'if [[ -n "$pdf_temp_dir" ]]; then rm -rf -- "$pdf_temp_dir"; fi' EXIT
    sha256sum "$TREE_SCRIPT" >> "$HASHES"
    for tree_format in "${TREE_FORMATS[@]}"; do
        if [[ "$tree_format" == psd ]]; then
            tree_output="$ARTIFACT_PREFIX.with-trees.psd"
            python3 "$TREE_SCRIPT" inject "$OUTPUT" \
                --style "$TREE_STYLE" -o "$tree_output" \
                || die "annotated PSD generation failed; ordinary parser output remains at $OUTPUT"
            sha256sum "$tree_output" >> "$HASHES"
            printf '  Annotated PSD: %s\n' "$tree_output"
        else
            tree_dir="$ARTIFACT_PREFIX-trees"
            if [[ "$tree_format" == pdf && "$PDF_LAYOUT" != separate ]]; then
                pdf_temp_dir="$(mktemp -d "$ARTIFACT_PREFIX-pdf-XXXXXXXX")"
                if [[ "$PDF_LAYOUT" == combined ]]; then
                    tree_dir="$pdf_temp_dir"
                fi
            fi
            mkdir -p "$tree_dir"
            pdf_pages=()
            for ((tree_number=1; tree_number<=EXPECTED_SENTENCE_COUNT; tree_number++)); do
                printf -v tree_output '%s/%06d.%s' "$tree_dir" "$tree_number" "$tree_format"
                python3 "$TREE_SCRIPT" export "$OUTPUT" --number "$tree_number" \
                    --format "$tree_format" --comments -o "$tree_output" \
                    || die "tree $tree_number export failed; ordinary parser output remains at $OUTPUT"
                if [[ "$tree_format" == pdf ]]; then
                    pdf_pages+=("$tree_output")
                fi
                if [[ "$tree_format" != pdf || "$PDF_LAYOUT" != combined ]]; then
                    sha256sum "$tree_output" >> "$HASHES"
                fi
            done
            if [[ "$tree_format" == pdf && "$PDF_LAYOUT" != separate ]]; then
                # Explicit array excludes stale PDFs and preserves numeric record order.
                # Merge first, then atomically replace any previous combined output.
                combined_pdf="$ARTIFACT_PREFIX-trees.pdf"
                pdfunite "${pdf_pages[@]}" "$pdf_temp_dir/combined.pdf" \
                    || die "PDF consolidation failed; ordinary parser output remains at $OUTPUT"
                mv -- "$pdf_temp_dir/combined.pdf" "$combined_pdf"
                sha256sum "$combined_pdf" >> "$HASHES"
                printf '  Combined PDF: %s\n' "$combined_pdf"
                rm -rf -- "$pdf_temp_dir"
                pdf_temp_dir=""
            fi
            if [[ "$tree_format" == pdf && "$PDF_LAYOUT" == combined ]]; then
                continue
            fi
            printf '  Graphical trees (%s): %s\n' "$tree_format" "$tree_dir"
        fi
    done
fi

printf 'Toy-parser experiment completed successfully.\n'
