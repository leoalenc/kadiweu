# Kadiwéu converter pipeline: Halstead and complexity summary

## Coverage

- Files with Halstead metrics: **42**
- Functions with Halstead metrics: **638**
- Functions matched with cyclomatic complexity: **633**
- Functions not matched with cyclomatic complexity: **5**
- Ambiguous function-name matches (CC withheld): **5**

## Halstead summary over functions

| Metric | Mean | Median | Maximum / total |
| --- | --- | --- | --- |
| Volume | 65.89 | 13.93 | 3 795.22 |
| Difficulty | 1.47 | 1.00 | 15.69 |
| Effort | 377.41 | 15.51 | 59 557.73 |
| Bugs | 0.0220 | 0.0046 | total=14.01; max=1.2651 |

## Files ranked by Halstead effort

| File | Volume | Difficulty | Effort | Bugs |
| --- | --- | --- | --- | --- |
| kadiweu_json_to_conllu.py | 8 488.54 | 14.17 | 120 316.34 | 2.8295 |
| kadiweu_constituency.py | 6 015.74 | 13.78 | 82 884.62 | 2.0052 |
| kadiweu_constituency_dependencies.py | 9 202.09 | 7.91 | 72 769.58 | 3.0674 |
| run_kadiweu_parser_rules.py | 6 280.12 | 11.31 | 71 029.20 | 2.0934 |
| compare_grammyep_kadiweu.py | 2 412.04 | 12.75 | 30 745.83 | 0.8040 |
| compare_kadiweu_conllu_versions.py | 2 380.42 | 11.74 | 27 942.41 | 0.7935 |
| update_overrides_from_gold.py | 2 463.19 | 10.33 | 25 452.94 | 0.8211 |
| make_kadiweu_parser_transition_report.py | 1 804.59 | 12.03 | 21 708.58 | 0.6015 |
| kadiweu_lexicon_explorer.py | 2 869.95 | 7.52 | 21 595.58 | 0.9566 |
| check_kadiweu_json_consistency.py | 1 874.75 | 9.42 | 17 664.28 | 0.6249 |
| kadiweu_linguistic_mappings.py | 2 433.76 | 6.89 | 16 771.12 | 0.8113 |
| kadiweu_tag_profiles.py | 1 718.82 | 9.48 | 16 297.28 | 0.5729 |
| refresh_kadiweu_narratives.py | 1 541.24 | 7.84 | 12 079.98 | 0.5137 |
| create_kadiweu_parser_compat.py | 1 311.91 | 8.54 | 11 203.75 | 0.4373 |
| import_nheengatu_tbp.py | 1 404.06 | 7.36 | 10 331.76 | 0.4680 |
| compare_conllu_drafts_to_gold.py | 1 114.28 | 8.91 | 9 925.35 | 0.3714 |
| compare_kadiweu_status_runs.py | 1 218.27 | 7.99 | 9 733.50 | 0.4061 |
| kadiweu_token_ranges.py | 1 177.66 | 7.65 | 9 010.36 | 0.3926 |
| compare_constituency_ud_dependencies.py | 1 086.80 | 8.20 | 8 914.53 | 0.3623 |
| kadiweu_psd_tree.py | 989.64 | 8.99 | 8 900.02 | 0.3299 |
| verify_psd_tree_integrity.py | 738.92 | 10.76 | 7 949.81 | 0.2463 |
| inventory_tbp_annotations.py | 1 316.91 | 5.83 | 7 671.91 | 0.4390 |
| kadiweu_status_stats.py | 1 040.25 | 7.37 | 7 669.10 | 0.3468 |
| induce_kadiweu_ud_mappings.py | 919.28 | 8.17 | 7 514.10 | 0.3064 |
| kadiweu_lexicon_stats.py | 714.09 | 9.79 | 6 989.58 | 0.2380 |
| parse-sentence.py | 858.86 | 6.47 | 5 553.56 | 0.2863 |
| plot_kadiweu_done_history.py | 837.58 | 6.15 | 5 152.24 | 0.2792 |
| inspect_kadiweu_json.py | 781.67 | 6.39 | 4 994.63 | 0.2606 |
| kadiweu_annotation_coverage.py | 985.48 | 4.46 | 4 395.01 | 0.3285 |
| extract_new_done_sentences.py | 810.82 | 5.41 | 4 388.99 | 0.2703 |
| kadiweu_json_to_token_table.py | 703.86 | 4.77 | 3 359.32 | 0.2346 |
| extract_paradigm.py | 671.94 | 4.79 | 3 216.49 | 0.2240 |
| kadiweu_empty_categories.py | 463.96 | 6.81 | 3 159.36 | 0.1547 |
| kadiweu_prediction_bridge.py | 596.60 | 5.15 | 3 074.76 | 0.1989 |
| extract_fused_words.py | 427.82 | 5.22 | 2 234.17 | 0.1426 |
| compare_conllu_drafts_to_gold_done.py | 201.78 | 4.88 | 983.66 | 0.0673 |
| extract_pro_d_tags.py | 204.04 | 3.65 | 745.17 | 0.0680 |
| kadiweu_morphology.py | 182.68 | 3.41 | 622.77 | 0.0609 |
| compare_A_B_overlap.py | 176.42 | 2.74 | 482.83 | 0.0588 |
| kadiweu_normalization.py | 101.02 | 3.75 | 378.84 | 0.0337 |
| test_run_kadiweu_parser_rules.py | 137.55 | 2.00 | 275.10 | 0.0458 |
| kadiweu_converter_config.py | 0.00 | 0.00 | 0.00 | 0.0000 |

## Top functions by Halstead effort

| Function | File | Line | CC | CC rank | Volume | Difficulty | Effort | Bugs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| convert_sentence | kadiweu_json_to_conllu.py | 693 | 176 | F | 3 795.22 | 15.69 | 59 557.73 | 1.2651 |
| main | compare_kadiweu_conllu_versions.py | 338 | 80 | F | 1 341.09 | 14.42 | 19 341.07 | 0.4470 |
| argument_assignments | kadiweu_constituency_dependencies.py | 425 | 73 | F | 1 572.02 | 8.58 | 13 487.04 | 0.5240 |
| main | compare_grammyep_kadiweu.py | 295 | 72 | F | 952.46 | 9.80 | 9 334.06 | 0.3175 |
| learn_overrides | update_overrides_from_gold.py | 448 | 51 | F | 761.81 | 10.23 | 7 795.30 | 0.2539 |
| run | refresh_kadiweu_narratives.py | 109 | 42 | F | 1 002.30 | 5.80 | 5 816.17 | 0.3341 |
| analyze | check_kadiweu_json_consistency.py | 266 | 96 | F | 911.63 | 5.29 | 4 823.02 | 0.3039 |
| tree_for | import_nheengatu_tbp.py | 32 | 22 | D | 574.08 | 7.26 | 4 165.15 | 0.1914 |
| tree_from_sentence | kadiweu_constituency.py | 794 | 38 | E | 396.46 | 9.93 | 3 937.25 | 0.1322 |
| main | make_kadiweu_parser_transition_report.py | 476 | 32 | E | 461.03 | 8.25 | 3 803.50 | 0.1537 |
| possessor_raising_assignments | kadiweu_constituency_dependencies.py | 376 | 37 | E | 717.13 | 5.23 | 3 747.56 | 0.2390 |
| main | run_kadiweu_parser_rules.py | 1457 | 41 | F | 524.96 | 6.82 | 3 577.72 | 0.1750 |
| complement_and_adjunct_assignments | kadiweu_constituency_dependencies.py | 329 | 34 | E | 545.63 | 6.08 | 3 316.56 | 0.1819 |
| infer_feats | kadiweu_linguistic_mappings.py | 569 | 34 | E | 505.47 | 6.15 | 3 110.57 | 0.1685 |
| main | extract_paradigm.py | 63 | 61 | F | 581.21 | 4.91 | 2 851.23 | 0.1937 |
| tree_from_psd_record | kadiweu_constituency.py | 469 | 14 | C | 521.24 | 5.33 | 2 779.95 | 0.1737 |
| comparison_rows | compare_constituency_ud_dependencies.py | 257 | 39 | E | 325.00 | 8.22 | 2 670.65 | 0.1083 |
| main | parse-sentence.py | 74 | 34 | E | 416.13 | 6.30 | 2 623.66 | 0.1387 |
| analyze | kadiweu_lexicon_stats.py | 59 | 31 | E | 353.60 | 7.10 | 2 509.41 | 0.1179 |
| infer_ud_upos | kadiweu_lexicon_explorer.py | 417 | 36 | E | 433.96 | 5.56 | 2 412.32 | 0.1447 |

## Top functions by Halstead volume

| Function | File | Line | CC | CC rank | Volume | Difficulty | Effort | Bugs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| convert_sentence | kadiweu_json_to_conllu.py | 693 | 176 | F | 3 795.22 | 15.69 | 59 557.73 | 1.2651 |
| argument_assignments | kadiweu_constituency_dependencies.py | 425 | 73 | F | 1 572.02 | 8.58 | 13 487.04 | 0.5240 |
| main | compare_kadiweu_conllu_versions.py | 338 | 80 | F | 1 341.09 | 14.42 | 19 341.07 | 0.4470 |
| run | refresh_kadiweu_narratives.py | 109 | 42 | F | 1 002.30 | 5.80 | 5 816.17 | 0.3341 |
| main | compare_grammyep_kadiweu.py | 295 | 72 | F | 952.46 | 9.80 | 9 334.06 | 0.3175 |
| analyze | check_kadiweu_json_consistency.py | 266 | 96 | F | 911.63 | 5.29 | 4 823.02 | 0.3039 |
| learn_overrides | update_overrides_from_gold.py | 448 | 51 | F | 761.81 | 10.23 | 7 795.30 | 0.2539 |
| possessor_raising_assignments | kadiweu_constituency_dependencies.py | 376 | 37 | E | 717.13 | 5.23 | 3 747.56 | 0.2390 |
| main | extract_paradigm.py | 63 | 61 | F | 581.21 | 4.91 | 2 851.23 | 0.1937 |
| tree_for | import_nheengatu_tbp.py | 32 | 22 | D | 574.08 | 7.26 | 4 165.15 | 0.1914 |
| inspect_sentence | inventory_tbp_annotations.py | 90 | 45 | F | 547.09 | 3.51 | 1 919.96 | 0.1824 |
| complement_and_adjunct_assignments | kadiweu_constituency_dependencies.py | 329 | 34 | E | 545.63 | 6.08 | 3 316.56 | 0.1819 |
| main | import_nheengatu_tbp.py | 86 | 25 | D | 534.28 | 3.54 | 1 891.34 | 0.1781 |
| main | run_kadiweu_parser_rules.py | 1457 | 41 | F | 524.96 | 6.82 | 3 577.72 | 0.1750 |
| tree_from_psd_record | kadiweu_constituency.py | 469 | 14 | C | 521.24 | 5.33 | 2 779.95 | 0.1737 |
| parse_json_rules | run_kadiweu_parser_rules.py | 226 | 29 | D | 511.05 | 3.71 | 1 898.18 | 0.1703 |
| infer_feats | kadiweu_linguistic_mappings.py | 569 | 34 | E | 505.47 | 6.15 | 3 110.57 | 0.1685 |
| main | make_kadiweu_parser_transition_report.py | 476 | 32 | E | 461.03 | 8.25 | 3 803.50 | 0.1537 |
| infer_ud_upos | kadiweu_lexicon_explorer.py | 417 | 36 | E | 433.96 | 5.56 | 2 412.32 | 0.1447 |
| main | induce_kadiweu_ud_mappings.py | 235 | 27 | D | 430.33 | 5.06 | 2 178.55 | 0.1434 |

## Top functions by cyclomatic complexity, with Halstead metrics

| Function | File | Line | CC | CC rank | Volume | Difficulty | Effort | Bugs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| convert_sentence | kadiweu_json_to_conllu.py | 693 | 176 | F | 3 795.22 | 15.69 | 59 557.73 | 1.2651 |
| analyze | check_kadiweu_json_consistency.py | 266 | 96 | F | 911.63 | 5.29 | 4 823.02 | 0.3039 |
| main | compare_kadiweu_conllu_versions.py | 338 | 80 | F | 1 341.09 | 14.42 | 19 341.07 | 0.4470 |
| argument_assignments | kadiweu_constituency_dependencies.py | 425 | 73 | F | 1 572.02 | 8.58 | 13 487.04 | 0.5240 |
| main | compare_grammyep_kadiweu.py | 295 | 72 | F | 952.46 | 9.80 | 9 334.06 | 0.3175 |
| main | extract_paradigm.py | 63 | 61 | F | 581.21 | 4.91 | 2 851.23 | 0.1937 |
| learn_overrides | update_overrides_from_gold.py | 448 | 51 | F | 761.81 | 10.23 | 7 795.30 | 0.2539 |
| inspect_sentence | inventory_tbp_annotations.py | 90 | 45 | F | 547.09 | 3.51 | 1 919.96 | 0.1824 |
| run | refresh_kadiweu_narratives.py | 109 | 42 | F | 1 002.30 | 5.80 | 5 816.17 | 0.3341 |
| main | run_kadiweu_parser_rules.py | 1457 | 41 | F | 524.96 | 6.82 | 3 577.72 | 0.1750 |
| ud_head | kadiweu_constituency_dependencies.py | 176 | 40 | E | 361.89 | 3.97 | 1 436.92 | 0.1206 |
| comparison_rows | compare_constituency_ud_dependencies.py | 257 | 39 | E | 325.00 | 8.22 | 2 670.65 | 0.1083 |
| tree_from_sentence | kadiweu_constituency.py | 794 | 38 | E | 396.46 | 9.93 | 3 937.25 | 0.1322 |
| possessor_raising_assignments | kadiweu_constituency_dependencies.py | 376 | 37 | E | 717.13 | 5.23 | 3 747.56 | 0.2390 |
| infer_ud_upos | kadiweu_lexicon_explorer.py | 417 | 36 | E | 433.96 | 5.56 | 2 412.32 | 0.1447 |
| complement_and_adjunct_assignments | kadiweu_constituency_dependencies.py | 329 | 34 | E | 545.63 | 6.08 | 3 316.56 | 0.1819 |
| infer_feats | kadiweu_linguistic_mappings.py | 569 | 34 | E | 505.47 | 6.15 | 3 110.57 | 0.1685 |
| main | parse-sentence.py | 74 | 34 | E | 416.13 | 6.30 | 2 623.66 | 0.1387 |
| main | make_kadiweu_parser_transition_report.py | 476 | 32 | E | 461.03 | 8.25 | 3 803.50 | 0.1537 |
| analyze | kadiweu_lexicon_stats.py | 59 | 31 | E | 353.60 | 7.10 | 2 509.41 | 0.1179 |

## Compact publication table: top functions by Halstead effort

| Function | File | CC | CC rank | Halstead volume | Halstead effort |
| --- | --- | --- | --- | --- | --- |
| convert_sentence | kadiweu_json_to_conllu.py | 176 | F | 3 795.22 | 59 557.73 |
| main | compare_kadiweu_conllu_versions.py | 80 | F | 1 341.09 | 19 341.07 |
| argument_assignments | kadiweu_constituency_dependencies.py | 73 | F | 1 572.02 | 13 487.04 |
| main | compare_grammyep_kadiweu.py | 72 | F | 952.46 | 9 334.06 |
| learn_overrides | update_overrides_from_gold.py | 51 | F | 761.81 | 7 795.30 |
| run | refresh_kadiweu_narratives.py | 42 | F | 1 002.30 | 5 816.17 |
| analyze | check_kadiweu_json_consistency.py | 96 | F | 911.63 | 4 823.02 |
| tree_for | import_nheengatu_tbp.py | 22 | D | 574.08 | 4 165.15 |
| tree_from_sentence | kadiweu_constituency.py | 38 | E | 396.46 | 3 937.25 |
| main | make_kadiweu_parser_transition_report.py | 32 | E | 461.03 | 3 803.50 |
