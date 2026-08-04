#!/usr/bin/env bash

# Regenerate the CorpusSearch PSD files for the DONE and REVIEW sentences in
# each KadiwÃ©u source dataset.

set -Eeuo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(CDPATH= cd -- "${script_dir}/.." && pwd)"
converter="${script_dir}/kadiweu_constituency.py"
data_dir="${repo_dir}/data"
output_dir="${data_dir}/generated/constituency"

datasets=(
    "hil-data"
    "ped-gramm"
    "van-data"
)

statuses=(
    "DONE"
    "REVIEW"
)

if [[ ! -x "${converter}" ]]; then
    printf 'Error: converter is missing or not executable: %s\n' "${converter}" >&2
    exit 1
fi

for dataset in "${datasets[@]}"; do
    input="${data_dir}/${dataset}.json"
    if [[ ! -f "${input}" ]]; then
        printf 'Error: input file not found: %s\n' "${input}" >&2
        exit 1
    fi
done

mkdir -p -- "${output_dir}"

for dataset in "${datasets[@]}"; do
    input="${data_dir}/${dataset}.json"

    for status in "${statuses[@]}"; do
        expected_output="${output_dir}/${dataset}.${status,,}.psd"
        printf 'Generating %s\n' "${expected_output}"

        "${converter}" \
            "${input}" \
            --all \
            --status "${status}" \
            --format corpussearch \
            --output-dir "${output_dir}"

        if [[ ! -s "${expected_output}" ]]; then
            printf 'Error: expected output was not created or is empty: %s\n' \
                "${expected_output}" >&2
            exit 1
        fi
    done
done

printf 'Updated six CorpusSearch files in %s\n' "${output_dir}"