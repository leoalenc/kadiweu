#!/usr/bin/env bash

# Abort on:
#   - any command returning a non-zero status (-e)
#   - use of an undefined variable (-u)
#   - failure of any command in a pipeline (-o pipefail)
set -euo pipefail

# CoNLL-U file to test.
#
# If a file path is supplied as the first argument, use it.
# Otherwise fall back to a default test file.
#
# Examples:
#   tests/test_dapl_overrides.sh
#   tests/test_dapl_overrides.sh ../data/treebank/draft-van.TEST19.conllu
OUT="${1:-../data/treebank/draft-van.conllu}"

# ------------------------------------------------------------------
# Regression test: anitaGa
#
# Ensure that DAPL form anitaGa is analyzed as:
#   UPOS = DET
#   XPOS = DAPL
#
# This protects the manual override:
#   anitaGa\tDAPL -> DET
# ------------------------------------------------------------------
grep -P '\tanitaGa\tanitaGa\tDET\tDAPL\tGender=Fem\|Number=Sing\|PronType=Dem\t' "$OUT" >/dev/null

# ------------------------------------------------------------------
# Regression test: initaGa
#
# Ensure that DAPL form initaGa is analyzed as:
#   UPOS = PRON
#   XPOS = DAPL
#
# This protects the learned override:
#   initaGa\tDAPL -> PRON
# ------------------------------------------------------------------
grep -P '\tinitaGa\tinitaGa\tPRON\tDAPL\tGender=Masc\|Number=Sing\|PronType=Dem\t' "$OUT" >/dev/null

# ------------------------------------------------------------------
# Full UD validation
#
# Ensures that:
#   - no DAPL forms revert to UPOS=X
#   - no feature-upos-not-permitted errors occur
#   - the file remains valid according to the kbc language profile
# ------------------------------------------------------------------
validate.py --lang=kbc --max-err=0 "$OUT" >/dev/null

echo "PASS: DAPL regression tests succeeded for $OUT"