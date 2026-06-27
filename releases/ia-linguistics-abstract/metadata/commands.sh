#!/usr/bin/env bash

# Comparison of combined draft against the gold treebank

./compare_conllu_drafts_to_gold.py \
../releases/ia-linguistics-abstract/gold/kbc_unicamp-ud-test.conllu \
../releases/ia-linguistics-abstract/drafts/draft-all.conllu \
--markdown-out ../releases/ia-linguistics-abstract/reports/conllu_drafts_vs_gold_all.md \
--csv-out ../releases/ia-linguistics-abstract/reports/conllu_drafts_vs_gold_all.csv \
--mismatch-csv-out ../releases/ia-linguistics-abstract/reports/conllu_token_mismatches_all.csv


# Comparison of individual draft treebanks

./compare_conllu_drafts_to_gold.py \
../releases/ia-linguistics-abstract/gold/kbc_unicamp-ud-test.conllu \
../releases/ia-linguistics-abstract/drafts/draft-ped-gramm.conllu \
../releases/ia-linguistics-abstract/drafts/draft-hil.conllu \
../releases/ia-linguistics-abstract/drafts/draft-van.conllu \
--markdown-out ../releases/ia-linguistics-abstract/reports/conllu_drafts_vs_gold.md \
--csv-out ../releases/ia-linguistics-abstract/reports/conllu_drafts_vs_gold.csv \
--mismatch-csv-out ../releases/ia-linguistics-abstract/reports/conllu_token_mismatches.csv