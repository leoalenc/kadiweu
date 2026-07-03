#!/usr/bin/env bash

# Refresh the three JSON dumps used by the Kadiwéu UD conversion pipeline.
#
# This script automates the ingestion of newly downloaded JSON dumps from the
# Tycho Brahe Platform for the documents that make up the "Corpus Kadiwéu —
# Gramática Pedagógica".
#
# It identifies each downloaded JSON dump by a stable document/container UID,
# copies the newest matching dump into the repository's data/ directory under
# the canonical filename expected by the conversion pipeline, normalizes the
# character "ǥ" to "G", and regenerates the corresponding .txt and .jsonl
# inspection files with inspect_kadiweu_json.py.
#
# Canonical output files:
#
#   data/ped-gramm.json
#   data/ped-gramm.txt
#   data/ped-gramm.jsonl
#
#   data/hil-data.json
#   data/hil-data.txt
#   data/hil-data.jsonl
#
#   data/van-data.json
#   data/van-data.txt
#   data/van-data.jsonl
#
# The script also appends one provenance record per imported document to:
#
#   data/import-json-history.tsv
#
# The provenance log records:
#
#   - import timestamp
#   - canonical target name
#   - original downloaded filename
#   - original source path
#   - source file size in bytes
#   - document UID used for matching
#   - sentence count extracted from the generated .txt file
#   - SHA-256 checksum of the downloaded source file
#
# Usage:
#
#   ./refresh_kadiweu_jsons.sh ~/Downloads
#
# If no download directory is supplied, the script defaults to:
#
#   ~/Downloads
#
# Recommended location:
#
#   kadiweu/src/refresh_kadiweu_jsons.sh
#
# The script assumes that inspect_kadiweu_json.py is also in kadiweu/src/.
#
# Notes:
#
# - Repository history is handled by Git. This script does not create backup
#   folders by default.
# - If more than one downloaded JSON matches the same UID, the newest file by
#   modification time is selected.
# - Diagnostic messages about multiple matches are printed to stderr so that
#   command substitution captures only the selected file path.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

DATA="$REPO/data"
DOWNLOAD_DIR="${1:-$HOME/Downloads}"
INSPECT="$REPO/src/inspect_kadiweu_json.py"
LOG="$DATA/import-json-history.tsv"

# Stable document/container UIDs used to identify the three source documents.
declare -A UID_TO_BASE=(
  ["28eeb8a0-d923-4d75-aebe-599aadddfbbb"]="ped-gramm"
  ["ffef8450-e302-4882-8306-e5998d31f584"]="hil-data"
  ["9d0f60a9-8c32-44c0-ac68-0b5d5b993db8"]="van-data"
)

mkdir -p "$DATA"

[[ -x "$INSPECT" ]] || {
  echo "ERROR: not executable: $INSPECT" >&2
  exit 1
}

# Initialize the provenance log if this is the first import.
if [[ ! -f "$LOG" ]]; then
  printf "timestamp\ttarget\tsource_file\tsource_path\tsize_bytes\tdocument_uid\tsentences\tsha256\n" > "$LOG"
fi

# Find the newest downloaded JSON file containing a given document UID.
find_json_for_uid() {
  local uid="$1"
  local matches=()

  mapfile -t matches < <(
    grep -El "$uid" "$DOWNLOAD_DIR"/*.json 2>/dev/null || true
  )

  if [[ "${#matches[@]}" -eq 0 ]]; then
    echo "ERROR: no JSON file found for UID $uid" >&2
    exit 1
  fi

  if [[ "${#matches[@]}" -gt 1 ]]; then
    {
      echo "Found ${#matches[@]} matching dumps for UID $uid:"
      ls -lh -t "${matches[@]}"
      echo "Using newest."
      echo
  }   >&2
fi

  ls -t "${matches[@]}" | head -n 1
}

# Extract the sentence count from inspect_kadiweu_json.py output.
sentence_count_from_txt() {
  local txt="$1"
  grep -Eo '^Found [0-9]+ matching sentence\(s\)\.' "$txt" \
    | awk '{print $2}' \
    | head -n 1
}

# Copy, normalize, regenerate derived files, and log provenance.
process_one() {
  local src="$1"
  local base="$2"
  local uid="$3"

  local json="$DATA/$base.json"
  local txt="$DATA/$base.txt"
  local jsonl="$DATA/$base.jsonl"

  local timestamp
  local size
  local sha
  local sentences

  timestamp="$(date --iso-8601=seconds)"
  size="$(stat -c '%s' "$src")"
  sha="$(sha256sum "$src" | awk '{print $1}')"

  cp "$src" "$json"
  sed -i 's/ǥ/G/g' "$json"

  "$INSPECT" "$json" --jsonl-out "$jsonl" > "$txt"
  sentences="$(sentence_count_from_txt "$txt")"

  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$timestamp" \
    "$base" \
    "$(basename "$src")" \
    "$src" \
    "$size" \
    "$uid" \
    "${sentences:-NA}" \
    "$sha" >> "$LOG"

  echo "============================================================"
  echo "Corpus:        $base"
  echo "Source file:   $(basename "$src")"
  echo "Source path:   $src"
  echo "Installed as:  data/$base.json"
  echo "Document UID:  $uid"
  echo "Sentences:     ${sentences:-NA}"
  echo "Size:          $size bytes"
  echo "SHA-256:       $sha"
  echo
  echo "Actions:"
  echo "  copied JSON dump"
  echo "  normalized ǥ -> G"
  echo "  generated data/$base.txt"
  echo "  generated data/$base.jsonl"
  echo "  appended provenance to data/import-json-history.tsv"
  echo "============================================================"
  echo
}

# Process all known source documents.
for uid in "${!UID_TO_BASE[@]}"; do
for uid in "${!UID_TO_BASE[@]}"; do
  base="${UID_TO_BASE[$uid]}"
  src="$(find_json_for_uid "$uid")"
  process_one "$src" "$base" "$uid"
done

echo "Done."
echo "Provenance log:"
echo "  $LOG"

echo
echo "Git status:"
git -C "$REPO" status --short -- data