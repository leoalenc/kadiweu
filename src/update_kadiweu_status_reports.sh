#!/usr/bin/env bash
# Create and compare a Kadiweu annotation-status snapshot, then update history.

set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
STATE=""
PREVIOUS_STATE=""
COMMIT_REPORTS=0
SHOW_PLOT=0

usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Update Kadiweu DONE/REVIEW statistics and historical plots.

Options:
  --project-root DIR  Repository root (default: \$KADIWEU_ROOT or ~/kadiweu)
  --state LETTER      New snapshot label (default: next unused A-Z label)
  --previous LETTER   Snapshot to compare against (default: latest earlier label)
  --commit            Commit the new snapshot/comparison before plotting
  --show              Open/show the final history plot when supported
  -h, --help          Show this help

The history plot is derived from committed snapshots. Use --commit when the
new snapshot must appear in done_history.tsv and done_history.svg immediately.
EOF
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

announce() {
    printf '\n[%s] %s\n' "$1" "$2"
}

while (($#)); do
    case $1 in
        --project-root)
            (($# >= 2)) || die "--project-root requires a value"
            PROJECT_ROOT=$2
            shift 2
            ;;
        --state)
            (($# >= 2)) || die "--state requires a value"
            STATE=${2^^}
            shift 2
            ;;
        --previous)
            (($# >= 2)) || die "--previous requires a value"
            PREVIOUS_STATE=${2^^}
            shift 2
            ;;
        --commit)
            COMMIT_REPORTS=1
            shift
            ;;
        --show)
            SHOW_PLOT=1
            shift
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
SRC_DIR="$PROJECT_ROOT/src"
STATUS_DIR="$PROJECT_ROOT/data/reports/status"
STATS="$SRC_DIR/kadiweu_status_stats.py"
COMPARE="$SRC_DIR/compare_kadiweu_status_runs.py"
PLOT="$SRC_DIR/plot_kadiweu_done_history.py"

for command_name in python3 git realpath sort find sed; do
    command -v "$command_name" >/dev/null 2>&1 \
        || die "required command not found: $command_name"
done
for required_file in "$STATS" "$COMPARE" "$PLOT"; do
    [[ -f $required_file ]] || die "required script not found: $required_file"
done
for corpus in ped-gramm hil-data van-data; do
    [[ -f $PROJECT_ROOT/data/$corpus.json ]] \
        || die "canonical JSON not found: $PROJECT_ROOT/data/$corpus.json"
done
mkdir -p "$STATUS_DIR"

mapfile -t existing_states < <(
    find "$STATUS_DIR" -mindepth 1 -maxdepth 1 -type d \
        -printf '%f\n' | sed -n '/^[A-Z]$/p' | sort
)

if [[ -z $STATE ]]; then
    for candidate in {A..Z}; do
        if [[ ! -d $STATUS_DIR/$candidate ]]; then
            STATE=$candidate
            break
        fi
    done
    [[ -n $STATE ]] || die 'all snapshot labels A-Z are already in use'
fi
[[ $STATE =~ ^[A-Z]$ ]] || die "--state must be one letter from A to Z: $STATE"
[[ ! -e $STATUS_DIR/$STATE ]] \
    || die "snapshot already exists: $STATUS_DIR/$STATE"

if [[ -z $PREVIOUS_STATE && ${#existing_states[@]} -gt 0 ]]; then
    for candidate in "${existing_states[@]}"; do
        [[ $candidate < $STATE ]] && PREVIOUS_STATE=$candidate
    done
fi
if [[ -n $PREVIOUS_STATE ]]; then
    [[ $PREVIOUS_STATE =~ ^[A-Z]$ ]] \
        || die "--previous must be one letter from A to Z: $PREVIOUS_STATE"
    [[ -f $STATUS_DIR/$PREVIOUS_STATE/sentence_status_individual.tsv ]] \
        || die "previous snapshot TSV not found for state $PREVIOUS_STATE"
fi

announce 1 "Generating status snapshot $STATE"
python3 "$STATS" \
    --corpus "ped-gramm=$PROJECT_ROOT/data/ped-gramm.json" \
    --corpus "hil-data=$PROJECT_ROOT/data/hil-data.json" \
    --corpus "van-data=$PROJECT_ROOT/data/van-data.json" \
    --outdir "$STATUS_DIR/$STATE" \
    --normalize-status \
    --strict \
    --chart pie \
    --chart stacked-bar \
    --chart-format png \
    --chart-format svg \
    --show

COMPARE_DIR=""
if [[ -n $PREVIOUS_STATE ]]; then
    COMPARE_DIR="$STATUS_DIR/$PREVIOUS_STATE-to-$STATE"
    announce 2 "Comparing status snapshots $PREVIOUS_STATE and $STATE"
    python3 "$COMPARE" \
        "$STATUS_DIR/$PREVIOUS_STATE/sentence_status_individual.tsv" \
        "$STATUS_DIR/$STATE/sentence_status_individual.tsv" \
        --label-a "$PREVIOUS_STATE" \
        --label-b "$STATE" \
        --outdir "$COMPARE_DIR" \
        --normalize-status \
        --strict-integrity
else
    announce 2 'No earlier snapshot found; skipping the two-run comparison'
fi

if ((COMMIT_REPORTS)); then
    announce 3 'Committing the new status reports'
    git -C "$PROJECT_ROOT" add -- "$STATUS_DIR/$STATE"
    if [[ -n $COMPARE_DIR ]]; then
        git -C "$PROJECT_ROOT" add -- "$COMPARE_DIR"
    fi
    git -C "$PROJECT_ROOT" diff --cached --quiet -- \
        "$STATUS_DIR/$STATE" ${COMPARE_DIR:+"$COMPARE_DIR"} \
        && die 'the generated status reports contain no staged changes'
    git -C "$PROJECT_ROOT" commit -m "Add Kadiweu status snapshot $STATE"
else
    announce 3 'Leaving the generated status reports uncommitted'
    printf 'To include snapshot %s in Git-based history, rerun with --commit or commit:\n' "$STATE"
    printf '  git -C %q add -- %q' "$PROJECT_ROOT" "$STATUS_DIR/$STATE"
    [[ -z $COMPARE_DIR ]] || printf ' %q' "$COMPARE_DIR"
    printf '\n  git -C %q commit -m %q\n' \
        "$PROJECT_ROOT" "Add Kadiweu status snapshot $STATE"
fi

announce 4 'Regenerating the committed DONE/REVIEW history table and plot'
plot_args=()
((SHOW_PLOT)) && plot_args+=(--show)
python3 "$PLOT" "${plot_args[@]}"

printf '\nStatus update completed successfully.\n'
printf 'New snapshot: %s\n' "$STATUS_DIR/$STATE"
[[ -z $COMPARE_DIR ]] || printf 'Comparison:   %s\n' "$COMPARE_DIR"
printf 'History TSV:  %s\n' "$STATUS_DIR/done_history.tsv"
printf 'History plot: %s\n' "$STATUS_DIR/done_history.svg"
if ((COMMIT_REPORTS == 0)); then
    printf 'NOTE: snapshot %s will enter the historical plot only after it is committed.\n' "$STATE"
fi
