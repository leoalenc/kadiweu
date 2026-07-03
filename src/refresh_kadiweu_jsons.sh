#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/kadiweu}"
DATA="$REPO/data"
DOWNLOAD_DIR="${1:-$HOME/Downloads}"
INSPECT="$REPO/src/inspect_kadiweu_json.py"
BACKUP="$DATA/backup-json-$(date +%Y%m%d-%H%M%S)"

declare -A UID_TO_BASE=(
  ["28eeb8a0-d923-4d75-aebe-599aadddfbbb"]="ped-gramm"
  ["ffef8450-e302-4882-8306-e5998d31f584"]="hil-data"
  ["9d0f60a9-8c32-44c0-ac68-0b5d5b993db8"]="van-data"
)

mkdir -p "$DATA" "$BACKUP"

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

  # If old and new dumps both match, use the most recently modified one.
  printf '%s\n' "${matches[@]}" | xargs -r ls -t | head -n 1
}

process_one() {
  local src="$1"
  local base="$2"

  local json="$DATA/$base.json"
  local txt="$DATA/$base.txt"
  local jsonl="$DATA/$base.jsonl"

  echo "Processing $base:"
  echo "  source: $src"
  echo "  target: $json"

  for f in "$json" "$txt" "$jsonl"; do
    [[ -e "$f" ]] && cp -a "$f" "$BACKUP/"
  done

  cp "$src" "$json"
  sed -i 's/ǥ/G/g' "$json"

  "$INSPECT" "$json" --jsonl-out "$jsonl" > "$txt"
}

for uid in "${!UID_TO_BASE[@]}"; do
  base="${UID_TO_BASE[$uid]}"
  src="$(find_json_for_uid "$uid")"
  process_one "$src" "$base"
done

echo
echo "Done. Backups are in:"
echo "  $BACKUP"