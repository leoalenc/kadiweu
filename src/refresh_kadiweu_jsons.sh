#!/usr/bin/env bash

# Refresh the JSON and PSD files used by the Kadiwéu UD conversion pipeline.
#
# For each of the three Tycho Brahe Platform documents, this script:
#
# 1. identifies the newest downloaded JSON export by its stable document UID;
# 2. finds the corresponding PSD export by validating all JSON sentences whose
#    status is DONE against all PSD trees, in their original order;
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

# Validate the complete ordered alignment between a Tycho Brahe JSON export
# and a PSD export.
#
# Tycho Brahe PSD exports contain all and only JSON sentences whose
# sentence-level status is DONE, preserving their relative order.
#
# The comparison uses:
#
#   JSON: the v values of non-empty tokens in each DONE sentence
#   PSD:  the terminal values in each constituency tree
#
# Orthographic G and ǥ are treated as equivalent, and matching is
# case-insensitive. Empty-category terminals beginning with "*" are ignored.
validate_json_psd_alignment() {
  local json_src="$1"
  local psd_src="$2"
  local report_errors="${3:-yes}"

  python3 - "$json_src" "$psd_src" "$report_errors" <<'PY_ALIGNMENT'
import json
import re
import sys

json_path = sys.argv[1]
psd_path = sys.argv[2]
report_errors = sys.argv[3] == "yes"


def fail(message):
    if report_errors:
        print(message, file=sys.stderr)
    raise SystemExit(1)


def normalize_token(token):
    return token.replace("ǥ", "G").casefold()


def iter_sentence_objects(obj):
    if isinstance(obj, dict):
        text = obj.get("text")
        struct = obj.get("struct")

        if (
            isinstance(text, str)
            and isinstance(struct, dict)
            and isinstance(struct.get("tokens"), list)
        ):
            yield obj
            return

        for value in obj.values():
            yield from iter_sentence_objects(value)

    elif isinstance(obj, list):
        for value in obj:
            yield from iter_sentence_objects(value)


def json_token_values(sentence):
    tokens = []

    for token in sentence["struct"]["tokens"]:
        value = token.get("v")

        if (
            isinstance(value, str)
            and value
            and not token.get("ec", False)
      ):
            tokens.append(value)

    return tokens


def extract_psd_trees(content):
    trees = []
    start = None
    depth = 0

    for index, char in enumerate(content):
        if char == "(":
            if depth == 0:
                start = index
            depth += 1

        elif char == ")":
            if depth == 0:
                fail(
                    f"ERROR: unmatched closing parenthesis in PSD: "
                    f"{psd_path}"
                )

            depth -= 1

            if depth == 0 and start is not None:
                trees.append(content[start:index + 1])
                start = None

    if depth != 0:
        fail(f"ERROR: unbalanced tree in PSD: {psd_path}")

    if not trees:
        fail(f"ERROR: no trees found in PSD: {psd_path}")

    return trees


def psd_terminal_values(tree):
    terminals = re.findall(
        r"\([^()\s]+\s+([^()\s]+)\)",
        tree,
    )

    return [
        token
        for token in terminals
        if not token.startswith("*")
    ]


with open(json_path, encoding="utf-8") as stream:
    data = json.load(stream)

sentences = list(iter_sentence_objects(data))

done_sentences = [
    (position, sentence)
    for position, sentence in enumerate(sentences, start=1)
    if sentence.get("status") == "DONE"
]

if not done_sentences:
    fail(
        f"ERROR: no sentence with status DONE found in JSON: "
        f"{json_path}"
    )

with open(psd_path, encoding="utf-8") as stream:
    psd_content = stream.read()

psd_trees = extract_psd_trees(psd_content)

if len(done_sentences) != len(psd_trees):
    fail(
        "\n".join(
            [
                "ERROR: JSON/PSD sentence-count mismatch",
                f"  JSON:            {json_path}",
                f"  PSD:             {psd_path}",
                f"  JSON DONE:       {len(done_sentences)}",
                f"  PSD trees:       {len(psd_trees)}",
            ]
        )
    )

for tree_number, ((json_position, sentence), tree) in enumerate(
    zip(done_sentences, psd_trees),
    start=1,
):
    json_tokens = json_token_values(sentence)
    psd_tokens = psd_terminal_values(tree)

    normalized_json = [
        normalize_token(token)
        for token in json_tokens
    ]
    normalized_psd = [
        normalize_token(token)
        for token in psd_tokens
    ]

    if normalized_json != normalized_psd:
        sentence_uid = sentence.get("uid", "<missing>")

        fail(
            "\n".join(
                [
                    "ERROR: JSON/PSD token alignment mismatch",
                    f"  JSON:            {json_path}",
                    f"  PSD:             {psd_path}",
                    f"  PSD tree:        {tree_number}",
                    f"  JSON position:   {json_position}",
                    f"  Sentence UID:    {sentence_uid}",
                    f"  Status:          {sentence.get('status')}",
                    f"  JSON tokens:     {' '.join(json_tokens)}",
                    f"  PSD terminals:   {' '.join(psd_tokens)}",
                ]
            )
        )

raise SystemExit(0)
PY_ALIGNMENT
}


# PSD exports do not contain document UIDs, and their generated filenames are
# unrelated to the JSON filenames. Retain only PSD files whose complete ordered
# tree sequence matches all DONE sentences in the JSON.
find_psd_for_json() {
  local json_src="$1"
  local base="$2"
  local candidates=()
  local psd_files=()
  local psd
  local newest_psd

  shopt -s nullglob
  psd_files=("$DOWNLOAD_DIR"/*.psd "$DOWNLOAD_DIR"/*.PSD)
  shopt -u nullglob

  if [[ "${#psd_files[@]}" -eq 0 ]]; then
    echo "ERROR: no PSD files found in $DOWNLOAD_DIR" >&2
    exit 1
  fi

  for psd in "${psd_files[@]}"; do
    if validate_json_psd_alignment "$json_src" "$psd" no; then
      candidates+=("$psd")
    fi
  done

  if [[ "${#candidates[@]}" -eq 0 ]]; then
    echo "ERROR: no PSD export completely matches the DONE sentences of $base" >&2
    echo "  JSON: $json_src" >&2
    echo >&2
    echo "Detailed comparison with the newest available PSD:" >&2

    newest_psd="$(ls -t "${psd_files[@]}" | head -n 1)"
    validate_json_psd_alignment "$json_src" "$newest_psd" yes || true

    exit 1
  fi

  if [[ "${#candidates[@]}" -gt 1 ]]; then
    {
      echo "Found ${#candidates[@]} fully matching PSD exports for corpus $base:"
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
PSD exports contain all and only JSON sentences whose sentence-level
\`status\` is \`DONE\`, preserving their relative order. The script therefore
compares the token \`v\` values of every \`DONE\` JSON sentence with the
terminal sequence of the corresponding PSD tree. Matching is case-insensitive,
treats \`G\` and \`ǥ\` as equivalent, and ignores empty-category terminals.
Both the sentence counts and every ordered token sequence must agree. If
several PSD downloads match completely, the newest one is selected and the
alternatives are reported.

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
