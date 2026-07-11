#!/usr/bin/env bash

# Refresh the JSON and PSD files used by the Kadiwéu UD conversion pipeline.
#
# For each of the three Tycho Brahe Platform documents, this script:
#
# 1. identifies the newest downloaded JSON export by its stable document UID;
# 2. finds the corresponding PSD export by comparing normalized first sentences;
# 3. creates canonical JSON and PSD files directly under data/;
# 4. normalizes canonical JSON files from "ǥ" to "G";
# 5. normalizes canonical PSD files from "G" to "ǥ";
# 6. regenerates the corresponding .txt and .jsonl inspection files;
# 7. moves the original downloaded JSON and PSD files to data/tycho/json/ and
#    data/tycho/psd/, respectively;
# 8. writes data/tycho/README.md explaining the source and canonical names; and
# 9. appends provenance records to data/import-json-history.tsv.
#
# Canonical files:
#
#   data/ped-gramm.json       data/ped-gramm.psd
#   data/hil-data.json        data/hil-data.psd
#   data/van-data.json        data/van-data.psd
#
# Archived original exports:
#
#   data/tycho/json/<downloaded-name>.json
#   data/tycho/psd/<downloaded-name>.psd
#
# Usage:
#
#   ./refresh_kadiweu_jsons.sh ~/Downloads
#
# If no download directory is supplied, ~/Downloads is used.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

DATA="$REPO/data"
DOWNLOAD_DIR="${1:-$HOME/Downloads}"
INSPECT="$REPO/src/inspect_kadiweu_json.py"
LOG="$DATA/import-json-history.tsv"
TYCHO_DIR="$DATA/tycho"
TYCHO_JSON_DIR="$TYCHO_DIR/json"
TYCHO_PSD_DIR="$TYCHO_DIR/psd"
TYCHO_README="$TYCHO_DIR/README.md"

# Stable document/container UIDs and canonical repository names.
declare -A UID_TO_BASE=(
  ["28eeb8a0-d923-4d75-aebe-599aadddfbbb"]="ped-gramm"
  ["ffef8450-e302-4882-8306-e5998d31f584"]="hil-data"
  ["9d0f60a9-8c32-44c0-ac68-0b5d5b993db8"]="van-data"
)

# Explicit order keeps processing and README output deterministic.
UID_ORDER=(
  "28eeb8a0-d923-4d75-aebe-599aadddfbbb"
  "ffef8450-e302-4882-8306-e5998d31f584"
  "9d0f60a9-8c32-44c0-ac68-0b5d5b993db8"
)

mkdir -p "$DATA" "$TYCHO_JSON_DIR" "$TYCHO_PSD_DIR"

[[ -d "$DOWNLOAD_DIR" ]] || {
  echo "ERROR: download directory not found: $DOWNLOAD_DIR" >&2
  exit 1
}

[[ -x "$INSPECT" ]] || {
  echo "ERROR: not executable: $INSPECT" >&2
  exit 1
}

if [[ ! -f "$LOG" ]]; then
  printf "timestamp\ttarget\tsource_file\tsource_path\tsize_bytes\tdocument_uid\tsentences\tsha256\n" > "$LOG"
fi

find_json_for_uid() {
  local uid="$1"
  local matches=()

  mapfile -t matches < <(
    grep -El "$uid" "$DOWNLOAD_DIR"/*.json 2>/dev/null || true
  )

  if [[ "${#matches[@]}" -eq 0 ]]; then
    echo "ERROR: no JSON file found for UID $uid in $DOWNLOAD_DIR" >&2
    exit 1
  fi

  if [[ "${#matches[@]}" -gt 1 ]]; then
    {
      echo "Found ${#matches[@]} matching JSON exports for UID $uid:"
      ls -lh -t "${matches[@]}"
      echo "Using newest."
      echo
    } >&2
  fi

  ls -t "${matches[@]}" | head -n 1
}

# Normalize a sentence signature for content-based JSON/PSD matching.
# Orthographic G and ǥ are treated as equivalent, matching is case-insensitive,
# and runs of whitespace are collapsed.
normalize_sentence_signature() {
  python3 -c 'import re, sys
text = sys.stdin.read().replace("ǥ", "G")
text = re.sub(r"\s+", " ", text).strip().casefold()
print(text)'
}

# Extract the first sentence text from a Tycho Brahe JSON export.
json_first_sentence_signature() {
  local json_src="$1"

  python3 - "$json_src" <<'PY_JSON'
import json
import re
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as stream:
    data = json.load(stream)

def find_first_sentence(obj):
    if isinstance(obj, dict):
        text = obj.get("text")
        struct = obj.get("struct")
        if isinstance(text, str) and isinstance(struct, dict):
            if any(key in struct for key in ("tokens", "chunks", "conllu")):
                return text
        for value in obj.values():
            result = find_first_sentence(value)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for value in obj:
            result = find_first_sentence(value)
            if result is not None:
                return result
    return None

text = find_first_sentence(data)
if text is None:
    raise SystemExit(f"ERROR: could not find a sentence object in JSON: {path}")

text = text.replace("ǥ", "G")
text = re.sub(r"\s+", " ", text).strip().casefold()
print(text)
PY_JSON
}

# Extract terminals from the first balanced Penn-style tree in a PSD file.
# Preterminal labels such as D, N$, VB, and punctuation tags are discarded.
psd_first_sentence_signature() {
  local psd_src="$1"

  python3 - "$psd_src" <<'PY_PSD'
import re
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as stream:
    content = stream.read()

start = content.find("(")
if start < 0:
    raise SystemExit(f"ERROR: no tree found in PSD: {path}")

depth = 0
end = None
for index in range(start, len(content)):
    char = content[index]
    if char == "(":
        depth += 1
    elif char == ")":
        depth -= 1
        if depth == 0:
            end = index + 1
            break

if end is None:
    raise SystemExit(f"ERROR: unbalanced first tree in PSD: {path}")

first_tree = content[start:end]
terminals = re.findall(r"\([^()\s]+\s+([^()\s]+)\)", first_tree)
if not terminals:
    raise SystemExit(f"ERROR: no terminals found in first PSD tree: {path}")

# Empty-category terminals do not represent words in the surface sentence.
terminals = [token for token in terminals if not token.startswith("*")]
text = " ".join(terminals).replace("ǥ", "G")
text = re.sub(r"\s+", " ", text).strip().casefold()
print(text)
PY_PSD
}

# PSD exports do not contain document UIDs and their generated filenames are
# unrelated to the JSON filenames. Match them by the normalized first sentence.
find_psd_for_json() {
  local json_src="$1"
  local base="$2"
  local json_signature psd_signature
  local candidates=()
  local psd_files=()
  local psd

  json_signature="$(json_first_sentence_signature "$json_src")"

  shopt -s nullglob
  psd_files=("$DOWNLOAD_DIR"/*.psd "$DOWNLOAD_DIR"/*.PSD)
  shopt -u nullglob

  if [[ "${#psd_files[@]}" -eq 0 ]]; then
    echo "ERROR: no PSD files found in $DOWNLOAD_DIR" >&2
    exit 1
  fi

  for psd in "${psd_files[@]}"; do
    psd_signature="$(psd_first_sentence_signature "$psd")"
    if [[ "$psd_signature" == "$json_signature" ]]; then
      candidates+=("$psd")
    fi
  done

  if [[ "${#candidates[@]}" -eq 0 ]]; then
    echo "ERROR: no PSD first sentence matches the JSON corpus $base" >&2
    echo "  JSON: $json_src" >&2
    echo "  Normalized first sentence: $json_signature" >&2
    exit 1
  fi

  if [[ "${#candidates[@]}" -gt 1 ]]; then
    {
      echo "Found ${#candidates[@]} matching PSD exports for corpus $base:"
      ls -lh -t "${candidates[@]}"
      echo "Using newest."
      echo
    } >&2
  fi

  ls -t "${candidates[@]}" | head -n 1
}

sentence_count_from_txt() {
  local txt="$1"

  grep -Eo '^Found [0-9]+ matching sentence\(s\)\.' "$txt" \
    | awk '{print $2}' \
    | head -n 1
}

# Return a destination that does not overwrite a previously archived export.
archive_destination() {
  local src="$1"
  local destination_dir="$2"
  local filename stem extension stamp destination

  filename="$(basename "$src")"
  destination="$destination_dir/$filename"

  if [[ -e "$destination" ]]; then
    stem="${filename%.*}"
    extension="${filename##*.}"
    stamp="$(date '+%Y%m%d-%H%M%S')"
    destination="$destination_dir/$stem.$stamp.$extension"
  fi

  printf '%s\n' "$destination"
}

# Data used to generate the README after all three imports succeed.
declare -A IMPORTED_JSON_NAME=()
declare -A IMPORTED_PSD_NAME=()
declare -A ARCHIVED_JSON_NAME=()
declare -A ARCHIVED_PSD_NAME=()
declare -A USED_PSD_PATH=()

process_one() {
  local json_src="$1"
  local psd_src="$2"
  local base="$3"
  local uid="$4"

  local json="$DATA/$base.json"
  local psd="$DATA/$base.psd"
  local txt="$DATA/$base.txt"
  local jsonl="$DATA/$base.jsonl"

  local timestamp json_size json_sha sentences
  local original_json_path original_psd_path
  local archived_json archived_psd

  timestamp="$(date --iso-8601=seconds)"
  json_size="$(stat -c '%s' "$json_src")"
  json_sha="$(sha256sum "$json_src" | awk '{print $1}')"
  original_json_path="$json_src"
  original_psd_path="$psd_src"

  # Create canonical working copies before moving either downloaded source.
  cp "$json_src" "$json"
  sed -i 's/ǥ/G/g' "$json"

  cp "$psd_src" "$psd"
  sed -i 's/G/ǥ/g' "$psd"

  "$INSPECT" "$json" --source-id "$base" --jsonl-out "$jsonl" > "$txt"
  sentences="$(sentence_count_from_txt "$txt")"

  archived_json="$(archive_destination "$json_src" "$TYCHO_JSON_DIR")"
  archived_psd="$(archive_destination "$psd_src" "$TYCHO_PSD_DIR")"

  # Move both original exports only after canonical and derived outputs succeed.
  mv "$json_src" "$archived_json"
  mv "$psd_src" "$archived_psd"

  IMPORTED_JSON_NAME["$base"]="$(basename "$original_json_path")"
  IMPORTED_PSD_NAME["$base"]="$(basename "$original_psd_path")"
  ARCHIVED_JSON_NAME["$base"]="$(basename "$archived_json")"
  ARCHIVED_PSD_NAME["$base"]="$(basename "$archived_psd")"

  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$timestamp" "$base" "$(basename "$original_json_path")" \
    "$original_json_path" "$json_size" "$uid" "${sentences:-NA}" \
    "$json_sha" >> "$LOG"

  echo "============================================================"
  echo "Corpus:             $base"
  echo "JSON source:        $(basename "$original_json_path")"
  echo "PSD source:         $(basename "$original_psd_path")"
  echo "Canonical JSON:     data/$base.json"
  echo "Canonical PSD:      data/$base.psd"
  echo "Archived JSON:      ${archived_json#"$REPO/"}"
  echo "Archived PSD:       ${archived_psd#"$REPO/"}"
  echo "Document UID:       $uid"
  echo "Sentences:          ${sentences:-NA}"
  echo "JSON size:          $json_size bytes"
  echo "JSON SHA-256:       $json_sha"
  echo
  echo "Actions:"
  echo "  created and normalized data/$base.json (ǥ -> G)"
  echo "  created and normalized data/$base.psd (G -> ǥ)"
  echo "  generated data/$base.txt"
  echo "  generated data/$base.jsonl"
  echo "  moved original JSON to ${archived_json#"$REPO/"}"
  echo "  moved original PSD to ${archived_psd#"$REPO/"}"
  echo "  appended JSON provenance to data/import-json-history.tsv"
  echo "============================================================"
  echo
}

write_tycho_readme() {
  local generated_at uid base

  generated_at="$(date --iso-8601=seconds)"

  cat > "$TYCHO_README" <<EOF_README
# Tycho Brahe Platform source exports

This directory stores the **original downloaded exports** from the Tycho Brahe
Platform after they have been processed by
\`src/refresh_kadiweu_jsons.sh\`.

## Directory names

- \`json/\`: original JSON exports downloaded from the platform.
- \`psd/\`: original Penn-style constituency tree files downloaded from the
  platform.

The short parent name \`tycho\` identifies the external source. The format names
\`json\` and \`psd\` make the two archive directories compact and unambiguous
within this repository.

## Naming policy

Downloaded files retain their opaque Tycho Brahe export names in this archive.
The processing script creates stable, human-readable canonical names directly
under \`data/\`:

| Canonical base | Document UID | Downloaded JSON | Downloaded PSD | Archived JSON | Archived PSD | Canonical JSON | Canonical PSD |
|---|---|---|---|---|---|---|---|
EOF_README

  for uid in "${UID_ORDER[@]}"; do
    base="${UID_TO_BASE[$uid]}"
    printf '| `%s` | `%s` | `%s` | `%s` | `json/%s` | `psd/%s` | `../%s.json` | `../%s.psd` |\n' \
      "$base" "$uid" \
      "${IMPORTED_JSON_NAME[$base]}" "${IMPORTED_PSD_NAME[$base]}" \
      "${ARCHIVED_JSON_NAME[$base]}" "${ARCHIVED_PSD_NAME[$base]}" \
      "$base" "$base" >> "$TYCHO_README"
  done

  cat >> "$TYCHO_README" <<EOF_README

## Pairing JSON and PSD exports

A JSON export is identified by the stable document UID stored in its content.
The corresponding PSD file does not contain that UID, and Tycho Brahe assigns
new, unrelated opaque filenames whenever JSON and PSD files are downloaded.
The script therefore extracts the first sentence from the JSON and the terminal
sequence of the first PSD tree, normalizes both, and compares them. Matching is
case-insensitive, treats \`G\` and \`ǥ\` as equivalent, and ignores tree labels,
parentheses, and whitespace differences. If several PSD downloads match, the
newest one is selected and the alternatives are reported.

## Normalization

The archived files are untouched originals. Normalization is applied only to
the canonical working copies:

- canonical JSON: \`ǥ\` → \`G\`;
- canonical PSD: \`G\` → \`ǥ\`.

Generated: $generated_at
EOF_README
}

for uid in "${UID_ORDER[@]}"; do
  base="${UID_TO_BASE[$uid]}"
  json_src="$(find_json_for_uid "$uid")"
  psd_src="$(find_psd_for_json "$json_src" "$base")"

  if [[ -n "${USED_PSD_PATH[$psd_src]:-}" ]]; then
    echo "ERROR: PSD selected for more than one corpus: $psd_src" >&2
    echo "  First corpus: ${USED_PSD_PATH[$psd_src]}" >&2
    echo "  Second corpus: $base" >&2
    exit 1
  fi
  USED_PSD_PATH["$psd_src"]="$base"

  process_one "$json_src" "$psd_src" "$base" "$uid"
done

ALL_TXT="$DATA/kadiweu-all.txt"
ALL_JSONL="$DATA/kadiweu-all.jsonl"

"$INSPECT" \
  "$DATA/ped-gramm.json" \
  "$DATA/hil-data.json" \
  "$DATA/van-data.json" \
  --source-id ped-gramm \
  --source-id hil-data \
  --source-id van-data \
  --jsonl-out "$ALL_JSONL" \
  --summary-only > "$ALL_TXT"

write_tycho_readme

echo "Generated consolidated inspection files:"
echo "  data/kadiweu-all.txt"
echo "  data/kadiweu-all.jsonl"
echo
echo "Archived Tycho Brahe exports:"
echo "  data/tycho/json/"
echo "  data/tycho/psd/"
echo
echo "Archive documentation:"
echo "  data/tycho/README.md"
echo
echo "Done."
echo "Provenance log:"
echo "  $LOG"
echo
echo "Git status:"
git -C "$REPO" status --short -- data
