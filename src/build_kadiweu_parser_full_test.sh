#!/usr/bin/env bash
# Build the fixed 206-sentence gold/POS pair used by the full parser test.

set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

source_dir="$SCRIPT_DIR/../data/generated/constituency"
runner="$SCRIPT_DIR/run_kadiweu_parser_rules.py"
output_prefix=""
expected_count=206
force=0

usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Build kadiweu-parser-full-test.gold.psd and
kadiweu-parser-full-test.pos from the six DONE/REVIEW CorpusSearch PSD exports, then
validate their counts and ID inventories before publishing them.

Options:
  --source-dir DIR       Directory containing the six source PSD files
                         (default: ../data/generated/constituency relative
                         to this script)
  --runner FILE          Parser runner with extraction support
                         (default: run_kadiweu_parser_rules.py beside this script)
  --output-prefix PATH   Output path without .gold.psd or .pos suffix
                         (default: SOURCE_DIR/kadiweu-parser-full-test)
  --expected-count N     Required number of unique records (default: 206)
  --force                Replace existing output files
  -h, --help             Show this help text
EOF
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

while (($#)); do
    case $1 in
        --source-dir)
            (($# >= 2)) || die "--source-dir requires a value"
            source_dir=$2
            shift 2
            ;;
        --runner)
            (($# >= 2)) || die "--runner requires a value"
            runner=$2
            shift 2
            ;;
        --output-prefix)
            (($# >= 2)) || die "--output-prefix requires a value"
            output_prefix=$2
            shift 2
            ;;
        --expected-count)
            (($# >= 2)) || die "--expected-count requires a value"
            expected_count=$2
            shift 2
            ;;
        --force)
            force=1
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

[[ $expected_count =~ ^[1-9][0-9]*$ ]] || \
    die "--expected-count must be a positive integer"
[[ -d $source_dir ]] || die "source directory not found: $source_dir"
[[ -f $runner ]] || die "runner not found: $runner"

if [[ -z $output_prefix ]]; then
    output_prefix="$source_dir/kadiweu-parser-full-test"
fi

source_files=(
    "$source_dir/hil-data.done.corpussearch.psd"
    "$source_dir/hil-data.review.corpussearch.psd"
    "$source_dir/ped-gramm.done.corpussearch.psd"
    "$source_dir/ped-gramm.review.corpussearch.psd"
    "$source_dir/van-data.done.corpussearch.psd"
    "$source_dir/van-data.review.corpussearch.psd"
)

for path in "${source_files[@]}"; do
    [[ -f $path ]] || die "required source file not found: $path"
done

bare_trace_re='^[[:space:]]+[*][^[:space:]()]*[*]-[0-9]+[[:space:]]*$'
wrapped_trace_re='[(]-NONE-[[:space:]]+[*][^[:space:]()]*[*]-[0-9]+'
any_trace_re='[*][^[:space:]()]*[*]-[0-9]+'

if grep -nEH "$bare_trace_re" "${source_files[@]}" >&2; then
    die "bare traces found in CorpusSearch source files; expected (-NONE- *T*-N)"
fi

source_trace_count=$(awk -v re="$wrapped_trace_re" '$0 ~ re { count++ } END { print count + 0 }' \
    "${source_files[@]}")

gold_output="$output_prefix.gold.psd"
pos_output="$output_prefix.pos"

if ((force == 0)); then
    [[ ! -e $gold_output ]] || \
        die "output already exists: $gold_output (use --force to replace it)"
    [[ ! -e $pos_output ]] || \
        die "output already exists: $pos_output (use --force to replace it)"
fi

mkdir -p -- "$(dirname -- "$output_prefix")"

tmp_base_dir="$source_dir/tmp"
mkdir -p -- "$tmp_base_dir"
tmp_dir=$(mktemp -d "$tmp_base_dir/kadiweu-full-test.XXXXXXXX")
cleanup() {
    rm -rf -- "$tmp_dir"
}
trap cleanup EXIT

extract_ids() {
    sed -n 's/.*(ID[[:space:]]\+\([^()[:space:]]\+\)[[:space:]]*).*/\1/p' "$@"
}

ids_file="$tmp_dir/all.ids"
extract_ids "${source_files[@]}" > "$ids_file"

record_count=$(wc -l < "$ids_file")
((record_count == expected_count)) || \
    die "found $record_count ID records; expected $expected_count"

duplicates_file="$tmp_dir/duplicate.ids"
sort "$ids_file" | uniq -d > "$duplicates_file"
if [[ -s $duplicates_file ]]; then
    printf 'ERROR: duplicate sentence IDs found:\n' >&2
    sed 's/^/  /' "$duplicates_file" >&2
    exit 1
fi

id_args=()
while IFS= read -r sentence_id; do
    [[ -n $sentence_id ]] || die "encountered an empty sentence ID"
    id_args+=(--sentence-id "$sentence_id")
done < "$ids_file"

tmp_gold="$tmp_dir/full.gold.psd"
tmp_pos="$tmp_dir/full.pos"

python3 "$runner" \
    --extract-from "${source_files[@]}" \
    "${id_args[@]}" \
    --gold-output "$tmp_gold" \
    --pos-output "$tmp_pos"

for generated in "$tmp_gold" "$tmp_pos"; do
    generated_count=$(extract_ids "$generated" | wc -l)
    ((generated_count == expected_count)) || \
        die "$generated contains $generated_count IDs; expected $expected_count"
done

extract_ids "$tmp_gold" | sort > "$tmp_dir/gold.ids"
extract_ids "$tmp_pos" | sort > "$tmp_dir/pos.ids"
cmp -s "$tmp_dir/gold.ids" "$tmp_dir/pos.ids" || \
    die "generated gold and POS files have different ID inventories"
cmp -s "$tmp_dir/gold.ids" <(sort "$ids_file") || \
    die "generated files do not preserve the complete source ID inventory"

if grep -nE "$bare_trace_re" "$tmp_gold" >&2; then
    die "generated gold file contains bare traces"
fi

gold_trace_count=$(awk -v re="$wrapped_trace_re" '$0 ~ re { count++ } END { print count + 0 }' \
    "$tmp_gold")
((gold_trace_count == source_trace_count)) || \
    die "generated gold contains $gold_trace_count wrapped traces; sources contain $source_trace_count"

if grep -nE "$any_trace_re" "$tmp_pos" >&2; then
    die "generated POS file contains traces; parser input must be trace-free"
fi

mv -f -- "$tmp_gold" "$gold_output"
mv -f -- "$tmp_pos" "$pos_output"

printf 'Built the fixed full-corpus test pair (%d records):\n' "$record_count"
printf '  preserved %d CorpusSearch-format traces in gold; POS is trace-free\n' \
    "$gold_trace_count"
printf '  %s\n' "$gold_output" "$pos_output"
