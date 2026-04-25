#!/bin/bash

KADIWEU_DIR=~/kadiweu
TEST="${KADIWEU_DIR}/data/treebank/draft-hil-refactoring-repository-normalization.vdt.conllu"

awk -F '\t' '
  NF == 10 && $2 == "." && ($4 != "PUNCT" || $5 != "PUNCT") {
    print FNR ":" $0
    bad=1
  }
  END {
    if (bad) {
      print "FAIL: bad punctuation"
      exit 1
    }
  }
' "$TEST"

awk -F '\t' '
  NF == 10 && $4 == "PUNCT" && $5 == "PUNCT" && $8 != "punct" {
    print FNR ":" $0
    bad=1
  }
  END {
    if (bad) {
      print "FAIL: bad deprel"
      exit 1
    }
  }
' "$TEST"