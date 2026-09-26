#!/usr/bin/env bash
# Refresh the Kadiweu TBP resources and evaluate a parser C publication.

set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
DOWNLOADS_DIR="$HOME/Downloads"
HISTORY_FILE="$HOME/Dropbox/projects/2025/post-doc/parser/histórico.txt"
EXISTING_C_RUNNER=""
SKIP_REFRESH=0

usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Run the complete Kadiweu TBP refresh and parser C evaluation pipeline.

Options:
  --project-root DIR   Repository root (default: \$KADIWEU_ROOT or ~/kadiweu)
  --downloads-dir DIR  Directory containing TBP exports (default: ~/Downloads)
  --history FILE       TBP parser histórico.txt (default: parser archive directory)
  --skip-refresh       Keep the current canonical JSON/PSD resources and start
                       by regenerating the six DONE/REVIEW CorpusSearch PSDs
  --runner FILE        Reuse an existing dated parser C runner instead of
                       creating one from the newest downloaded Kadiw-u pair
  -h, --help           Show this help

The default run expects fresh JSON and PSD exports for ped-gramm, hil-data,
and van-data, plus a complete Kadiw-u TXT/JSON parser-rule pair.
EOF
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

announce() {
    printf '\n[%s] %s\n' "$1" "$2"
}

require_file() {
    [[ -f $1 ]] || die "required file not found: $1"
}

require_executable() {
    [[ -x $1 ]] || die "required executable not found or not executable: $1"
}

while (($#)); do
    case $1 in
        --project-root)
            (($# >= 2)) || die "--project-root requires a value"
            PROJECT_ROOT=$2
            shift 2
            ;;
        --downloads-dir)
            (($# >= 2)) || die "--downloads-dir requires a value"
            DOWNLOADS_DIR=$2
            shift 2
            ;;
        --history)
            (($# >= 2)) || die "--history requires a value"
            HISTORY_FILE=$2
            shift 2
            ;;
        --skip-refresh)
            SKIP_REFRESH=1
            shift
            ;;
        --runner)
            (($# >= 2)) || die "--runner requires a value"
            EXISTING_C_RUNNER=$2
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1 (use --help)"
            ;;
    esac
done

PROJECT_ROOT=$(realpath -m "$PROJECT_ROOT")
DOWNLOADS_DIR=$(realpath -m "$DOWNLOADS_DIR")
HISTORY_FILE=$(realpath -m "$HISTORY_FILE")

SRC_DIR="$PROJECT_ROOT/src"
OUT_DIR="$PROJECT_ROOT/data/generated/constituency"
REFRESH="$SRC_DIR/refresh_kadiweu_jsons.sh"
UPDATE_PSD="$SRC_DIR/update_corpussearch_psd.sh"
BUILD_FULL_TEST="$SRC_DIR/build_kadiweu_parser_full_test.sh"
RUN_A="$SRC_DIR/run_kadiweu_parser_full_test_A.sh"
CREATE_COMPAT="$SRC_DIR/create_kadiweu_parser_compat.py"
INPUT="$OUT_DIR/kadiweu-parser-full-test.pos"
GOLD="$OUT_DIR/kadiweu-parser-full-test.gold.psd"
INPUT_HASHES="$OUT_DIR/kadiweu-parser-full-test-input-hashes.txt"
C_SUMMARY="$OUT_DIR/kadiweu-parser-full-test-C-summary.tsv"
TRANSITION_SUMMARY="$OUT_DIR/kadiweu-parser-full-test-A-to-C-summary.tsv"

for command_name in bash python3 sha256sum awk sed tee mktemp realpath; do
    command -v "$command_name" >/dev/null 2>&1 \
        || die "required command not found: $command_name"
done

[[ -d $PROJECT_ROOT ]] || die "project root not found: $PROJECT_ROOT"
[[ -d $DOWNLOADS_DIR ]] || die "downloads directory not found: $DOWNLOADS_DIR"
require_executable "$UPDATE_PSD"
require_executable "$BUILD_FULL_TEST"
require_executable "$RUN_A"

if ((SKIP_REFRESH == 0)); then
    require_executable "$REFRESH"
fi

if [[ -z $EXISTING_C_RUNNER ]]; then
    require_executable "$CREATE_COMPAT"
    require_file "$HISTORY_FILE"
else
    EXISTING_C_RUNNER=$(realpath -m "$EXISTING_C_RUNNER")
    require_executable "$EXISTING_C_RUNNER"
fi

printf 'Project root:  %s\n' "$PROJECT_ROOT"
printf 'Downloads:     %s\n' "$DOWNLOADS_DIR"
if [[ -z $EXISTING_C_RUNNER ]]; then
    printf 'Parser history: %s\n' "$HISTORY_FILE"
else
    printf 'Parser C runner: %s\n' "$EXISTING_C_RUNNER"
fi

if ((SKIP_REFRESH == 0)); then
    announce 1 'Refreshing canonical TBP JSON, PSD, TXT, and JSONL resources'
    "$REFRESH" "$DOWNLOADS_DIR"
else
    announce 1 'Skipping canonical TBP refresh by request'
fi

announce 2 'Regenerating the six DONE/REVIEW CorpusSearch PSD files'
"$UPDATE_PSD"

announce 3 'Rebuilding the 206-sentence full-test gold and POS pair'
"$BUILD_FULL_TEST" --force
require_file "$INPUT"
require_file "$GOLD"

announce 4 'Recording and verifying the refreshed full-test input hashes'
hash_tmp=$(mktemp "$OUT_DIR/.kadiweu-parser-full-test-input-hashes.XXXXXXXX")
cleanup_hash_tmp() {
    [[ ! -e ${hash_tmp:-} ]] || rm -f -- "$hash_tmp"
}
trap cleanup_hash_tmp EXIT
(
    cd "$OUT_DIR"
    sha256sum "$(basename "$INPUT")" "$(basename "$GOLD")"
) > "$hash_tmp"
mv -f -- "$hash_tmp" "$INPUT_HASHES"
(
    cd "$OUT_DIR"
    sha256sum -c "$(basename "$INPUT_HASHES")"
)

announce 5 'Rerunning parser A against the refreshed gold reference'
"$RUN_A"

if [[ -z $EXISTING_C_RUNNER ]]; then
    announce 6 'Archiving the newest parser rules and creating the dated C runner'
    compat_log=$(mktemp "${TMPDIR:-/tmp}/kadiweu-create-compat.XXXXXXXX")
    cleanup_compat_log() {
        [[ ! -e ${compat_log:-} ]] || rm -f -- "$compat_log"
    }
    trap 'cleanup_hash_tmp; cleanup_compat_log' EXIT

    "$CREATE_COMPAT" \
        --downloads-dir "$DOWNLOADS_DIR" \
        --history "$HISTORY_FILE" \
        | tee "$compat_log"

    C_RUNNER=$(sed -n 's/^Test runner: //p' "$compat_log" | tail -n 1)
    [[ -n $C_RUNNER ]] || die "compatibility generator did not report a test runner"
    C_RUNNER=$(realpath -m "$C_RUNNER")
    require_executable "$C_RUNNER"
else
    announce 6 'Using the requested existing parser C runner'
    C_RUNNER=$EXISTING_C_RUNNER
fi

announce 7 "Running parser C with ${C_RUNNER##*/}"
"$C_RUNNER"

require_file "$C_SUMMARY"
require_file "$TRANSITION_SUMMARY"

announce 8 'Authoritative DONE-only evaluation'
awk -F '\t' '
    NR == FNR && FNR == 1 {next}
    NR == FNR && $1 == "DONE" {
        acceptable = $2 + $3
        printf "Parser C versus gold (DONE only):\n"
        printf "  exact:                 %d\n", $2
        printf "  trace-equivalent:      %d\n", $3
        printf "  structural difference:%d\n", $4
        printf "  total:                 %d\n", $5
        printf "  accuracy:              %.2f%%\n", 100 * acceptable / $5
        next
    }
    NR != FNR && FNR == 1 {next}
    NR != FNR && $1 == "DONE" {
        printf "Parser A to C (DONE only):\n"
        printf "  A structural:          %d\n", $2
        printf "  C structural:          %d\n", $3
        printf "  corrected by C:        %d\n", $4
        printf "  new C differences:     %d\n", $5
        printf "  persistent:            %d\n", $6
        printf "  net reduction:         %d\n", $7
    }
' "$C_SUMMARY" "$TRANSITION_SUMMARY"

printf '\nREVIEW transitions are descriptive only and are not counted as improvements or regressions.\n'
printf 'Pipeline completed successfully.\n'
printf 'Parser C runner: %s\n' "$C_RUNNER"
printf 'Comparison TSV: %s\n' "$OUT_DIR/kadiweu-parser-full-test-C-comparison.tsv"
printf 'DONE summary:   %s\n' "$C_SUMMARY"

