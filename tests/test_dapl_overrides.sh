#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-../data/treebank/draft-van.conllu}"

grep -P '\tanitaGa\tanitaGa\tDET\tDAPL\tGender=Fem\|Number=Sing\|PronType=Dem\t' "$OUT" >/dev/null
grep -P '\tinitaGa\tinitaGa\tPRON\tDAPL\tGender=Masc\|Number=Sing\|PronType=Dem\t' "$OUT" >/dev/null

validate.py --lang=kbc --max-err=0 "$OUT" >/dev/null