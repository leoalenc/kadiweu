#!/usr/bin/env bash
# Apply unchanged Kadiwéu Parser C rules to seven tagged Kadiwéu/Nheengatu test sentences.
# Install in ~/kadiweu/src and run with bash run_nheengatu_sentence_parser_C.sh.
# Environment overrides: KADIWEU_ROOT, RUNNER, RULES_C, DEFINITIONS_C,
# CORPUSSEARCH, OUT_DIR. Gold uses the shared Kadiwéu-style NP structure.
set -euo pipefail

# Match run_kadiweu_parser_full_test_C_250926_1055.sh resources.
readonly EXPECTED_RULES_SHA256="1d3291204215014851b0ae9f2e7888faa2361b0c6f022f73485ad2811b556a4a"
readonly EXPECTED_DEFINITIONS_SHA256="46b3e1fb5512747d4c20aa5bdcf600af6ac6a6d6b639d9debe2155470a050222"
readonly EXPECTED_EXECUTED_RULES=175

PROJECT_ROOT="${KADIWEU_ROOT:-$HOME/kadiweu}"
RUNNER="${RUNNER:-$PROJECT_ROOT/src/run_kadiweu_parser_rules.py}"
RULES_C="${RULES_C:-/home/leonel/Dropbox/projects/2025/post-doc/parser/Kadiw-u-250926-1055.compat.json}"
DEFINITIONS_C="${DEFINITIONS_C:-$HOME/Dropbox/projects/2025/post-doc/parser/kadiweu_parser_definitions_070726.txt}"
CORPUSSEARCH="${CORPUSSEARCH:-corpussearch}"
OUT_DIR="${OUT_DIR:-$PROJECT_ROOT/data/generated/constituency}"

die() { printf 'ERROR: %s\n' "$*" >&2; exit 2; }
for cmd in python3 sha256sum mktemp tee; do
    command -v "$cmd" >/dev/null 2>&1 || die "required command not found: $cmd"
done
command -v "$CORPUSSEARCH" >/dev/null 2>&1 \
    || die "CorpusSearch command not found: $CORPUSSEARCH"
for path in "$RUNNER" "$RULES_C" "$DEFINITIONS_C"; do
    [[ -f "$path" ]] || die "required file not found: $path"
done

# Resource overrides must still identify the same frozen Parser C version.
actual_sha256() {
    python3 - "$1" <<'HASH_PY'
import hashlib
import sys
from pathlib import Path
print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
HASH_PY
}
rules_hash="$(actual_sha256 "$RULES_C")"
definitions_hash="$(actual_sha256 "$DEFINITIONS_C")"
[[ "$rules_hash" == "$EXPECTED_RULES_SHA256" ]] \
    || die "rules C hash mismatch: expected $EXPECTED_RULES_SHA256; found $rules_hash"
[[ "$definitions_hash" == "$EXPECTED_DEFINITIONS_SHA256" ]] \
    || die "definitions C hash mismatch: expected $EXPECTED_DEFINITIONS_SHA256; found $definitions_hash"
printf 'Parser C 250926-1055 rules and definitions hashes: OK\n'

# Use absolute paths before the emulator enters its working directory.
RUNNER="$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$RUNNER")"
RULES_C="$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$RULES_C")"
DEFINITIONS_C="$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$DEFINITIONS_C")"
CORPUSSEARCH="$(command -v "$CORPUSSEARCH")"
CORPUSSEARCH="$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$CORPUSSEARCH")"
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"
# Separate directories preserve repeated experiments and intermediate stages.
EXPERIMENT_DIR="$(mktemp -d "$OUT_DIR/nheengatu-sentence-C-XXXXXXXX")"
INPUT="$EXPERIMENT_DIR/nheengatu-sentence.pos"
OUTPUT="$EXPERIMENT_DIR/nheengatu-sentence-C.psd"
GOLD="$EXPERIMENT_DIR/nheengatu-sentence.gold.psd"
COMPARISON="$EXPERIMENT_DIR/comparison.tsv"
DIFF="$EXPERIMENT_DIR/structural.diff"
RULE_LOG="$EXPERIMENT_DIR/rules.tsv"
CONSOLE_LOG="$EXPERIMENT_DIR/console.log"
RUN_DIR="$(mktemp -d "$EXPERIMENT_DIR/work-XXXXXXXX")"

# The quoted heredoc preserves N$ literally. The input is a flat tree:
# POS tags are preterminals; the emulator must build the phrase structure.
cat > "$INPUT" <<'POS'
((IP-MAT
  (N Mɨcura)
  (N$ raɨíra)
  (VB oiumẽndári)
  (N cinimũ)
  (PUNCT .))
 (ID nheengatu-test,0.1))

((IP-MAT
  (D Niǥidoa)
  (N waca)
  (N$ lotiidi)
  (VB dapicoǥo))
 (ID kadiweu-test,0.1))

((IP-MAT
  (D Niǥidoa)
  (N waca)
  (N$ lotiidi)
  (VB dapicoǥo)
  (PUNCT .))
 (ID kadiweu-test,0.2))

((IP-MAT
  (D Kwá)
  (N mɨcura)
  (N$ raɨíra)
  (VB oiumẽndári)
  (N cinimũ)
  (PUNCT .))
 (ID nheengatu-test,0.2))

((IP-MAT
  (D kwá)
  (N mɨcura)
  (N$ raɨíra)
  (VB oiumẽndári)
  (PUNCT .))
 (ID nheengatu-test,0.3))

((IP-MAT
  (D Kwá)
  (N mɨcura)
  (N$ raɨíra)
  (VB oiumẽndári)
  (PUNCT .))
 (ID nheengatu-test,0.4))

((IP-MAT
  (D Kwá)
  (N mɨcura)
  (N$ raɨíra)
  (VB oiumẽndári))
 (ID nheengatu-test,0.5))
POS

# Constructed gold hypothesis: nested possessor NP precedes possessed N$.
# Plain NP labels follow the DONE Kadiwéu analogue
# niGidowa waca lotiidi dapikoGo (ped-gramm,0.55).
# The original sentence plus six added variants have unique IDs.
# Outer NP contains D (when supplied), possessor NP, and possessed N$.
# No unexpressed object, punctuation, or empty category is inserted.
cat > "$GOLD" <<'GOLD_PSD'
((IP-MAT
  (NP
    (NP (N Mɨcura))
    (N$ raɨíra))
  (VB oiumẽndári)
  (NP (N cinimũ))
  (PUNCT .))
 (ID nheengatu-test,0.1))

((IP-MAT
  (NP (D Niǥidoa) (NP (N waca)) (N$ lotiidi))
  (VB dapicoǥo))
 (ID kadiweu-test,0.1))

((IP-MAT
  (NP (D Niǥidoa) (NP (N waca)) (N$ lotiidi))
  (VB dapicoǥo)
  (PUNCT .))
 (ID kadiweu-test,0.2))

((IP-MAT
  (NP (D Kwá) (NP (N mɨcura)) (N$ raɨíra))
  (VB oiumẽndári)
  (NP (N cinimũ))
  (PUNCT .))
 (ID nheengatu-test,0.2))

((IP-MAT
  (NP (D kwá) (NP (N mɨcura)) (N$ raɨíra))
  (VB oiumẽndári)
  (PUNCT .))
 (ID nheengatu-test,0.3))

((IP-MAT
  (NP (D Kwá) (NP (N mɨcura)) (N$ raɨíra))
  (VB oiumẽndári)
  (PUNCT .))
 (ID nheengatu-test,0.4))

((IP-MAT
  (NP (D Kwá) (NP (N mɨcura)) (N$ raɨíra))
  (VB oiumẽndári))
 (ID nheengatu-test,0.5))
GOLD_PSD

# Record actual resources rather than requiring the full-test frozen hashes.
# This permits explicit RULES_C/DEFINITIONS_C overrides for later experiments.
sha256sum "$RUNNER" "$RULES_C" "$DEFINITIONS_C" "$INPUT" "$GOLD" \
    > "$EXPERIMENT_DIR/input-hashes.txt"
printf 'Experiment: %s\nInput:\n' "$EXPERIMENT_DIR"
cat "$INPUT"

set +e
python3 -u "$RUNNER" "$RULES_C" "$INPUT" \
    --definitions "$DEFINITIONS_C" \
    --corpussearch "$CORPUSSEARCH" \
    --output "$OUTPUT" \
    --expected "$GOLD" \
    --comparison-report "$COMPARISON" \
    --diff "$DIFF" \
    --work-dir "$RUN_DIR" \
    --keep-intermediate \
    --log "$RULE_LOG" \
    2>&1 | tee "$CONSOLE_LOG"
pipeline_status=("${PIPESTATUS[@]}")
set -e
runner_status="${pipeline_status[0]}"
[[ "${pipeline_status[1]}" -eq 0 ]] || die "could not write console log"
case "$runner_status" in
    0) printf 'Comparison completed without structural differences.\n' ;;
    1) printf 'Comparison completed; structural differences found.\n' ;;
    *) die "emulator exited with status $runner_status; inspect $CONSOLE_LOG and $RUN_DIR" ;;
esac
[[ -s "$OUTPUT" ]] || die "emulator produced no parse: $OUTPUT"
[[ -f "$RULE_LOG" ]] || die "emulator produced no rule log: $RULE_LOG"
rule_rows="$(python3 - "$RULE_LOG" <<'COUNT_PY'
import csv
import sys
with open(sys.argv[1], encoding="utf-8", newline="") as stream:
    reader = csv.reader(stream, delimiter="\t")
    next(reader, None)
    print(sum(1 for row in reader if row))
COUNT_PY
)"
[[ "$rule_rows" -eq "$EXPECTED_EXECUTED_RULES" ]] \
    || die "expected $EXPECTED_EXECUTED_RULES executed-rule rows; found $rule_rows"
printf 'Executed rules: %s\n' "$rule_rows"
for path in "$COMPARISON" "$DIFF"; do
    [[ -f "$path" ]] || die "missing comparison artifact: $path"
done
sha256sum "$OUTPUT" "$RULE_LOG" "$CONSOLE_LOG" "$COMPARISON" "$DIFF" \
    > "$EXPERIMENT_DIR/output-hashes.txt"
printf '\nGenerated parses (inspect their structures):\n'
cat "$OUTPUT"
printf '\nParse: %s\nRule log: %s\nIntermediate trees: %s\n' \
    "$OUTPUT" "$RULE_LOG" "$RUN_DIR"
printf '\nGold: %s\nComparison: %s\nStructural diff: %s\n' "$GOLD" "$COMPARISON" "$DIFF"
cat "$COMPARISON"
# Like the full-test wrapper, a completed comparison returns success even when
# differences exist. The comparison TSV records the sentence-level result.
printf 'Gold is a constructed analysis for this experiment.\n' 
