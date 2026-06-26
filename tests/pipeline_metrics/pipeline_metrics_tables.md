# Kadiwéu converter pipeline: Halstead and complexity summary

## Coverage

- Files with Halstead metrics: **14**
- Functions with Halstead metrics: **248**
- Functions matched with cyclomatic complexity: **248**
- Functions not matched with cyclomatic complexity: **0**

## Halstead summary over functions

| Metric | Mean | Median | Maximum / total |
| --- | --- | --- | --- |
| Volume | 53.49 | 11.61 | 3 366.81 |
| Difficulty | 1.30 | 0.50 | 16.30 |
| Effort | 402.92 | 6.97 | 54 874.05 |
| Bugs | 0.0178 | 0.0039 | total=4.42; max=1.1223 |

## Files ranked by Halstead effort

| File | Volume | Difficulty | Effort | Bugs |
| --- | --- | --- | --- | --- |
| kadiweu_json_to_conllu.py | 8 879.75 | 13.96 | 123 946.53 | 2.9599 |
| update_overrides_from_gold.py | 2 416.24 | 10.21 | 24 675.40 | 0.8054 |
| kadiweu_lexicon_explorer.py | 2 869.95 | 7.52 | 21 595.58 | 0.9566 |
| compare_kadiweu_conllu_versions.py | 1 946.12 | 9.59 | 18 663.65 | 0.6487 |
| check_kadiweu_json_consistency.py | 1 804.65 | 9.48 | 17 102.49 | 0.6015 |
| kadiweu_token_ranges.py | 1 177.66 | 7.65 | 9 010.36 | 0.3926 |
| kadiweu_tag_profiles.py | 883.70 | 7.54 | 6 665.62 | 0.2946 |
| inspect_kadiweu_json.py | 584.17 | 6.21 | 3 629.42 | 0.1947 |
| kadiweu_json_to_token_table.py | 703.86 | 4.77 | 3 359.32 | 0.2346 |
| kadiweu_empty_categories.py | 463.96 | 6.81 | 3 159.36 | 0.1547 |
| induce_kadiweu_ud_mappings.py | 612.82 | 5.03 | 3 083.27 | 0.2043 |
| kadiweu_morphology.py | 182.68 | 3.41 | 622.77 | 0.0609 |
| kadiweu_normalization.py | 101.02 | 3.75 | 378.84 | 0.0337 |
| kadiweu_converter_config.py | 0.00 | 0.00 | 0.00 | 0.0000 |

## Top functions by Halstead effort

| Function | File | Line | CC | CC rank | Volume | Difficulty | Effort | Bugs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| convert_sentence | kadiweu_json_to_conllu.py | 1016 | 154 | F | 3 366.81 | 16.30 | 54 874.05 | 1.1223 |
| main | compare_kadiweu_conllu_versions.py | 331 | 62 | F | 980.69 | 10.97 | 10 753.72 | 0.3269 |
| learn_overrides | update_overrides_from_gold.py | 394 | 51 | F | 761.81 | 10.23 | 7 795.30 | 0.2539 |
| analyze | check_kadiweu_json_consistency.py | 250 | 94 | F | 887.58 | 5.31 | 4 715.26 | 0.2959 |
| infer_feats | kadiweu_json_to_conllu.py | 712 | 36 | E | 412.53 | 6.06 | 2 500.19 | 0.1375 |
| infer_ud_upos | kadiweu_lexicon_explorer.py | 417 | 36 | E | 433.96 | 5.56 | 2 412.32 | 0.1447 |
| apply_spaceafter_from_text | kadiweu_json_to_conllu.py | 256 | 13 | C | 262.33 | 6.86 | 1 798.84 | 0.0874 |
| main | induce_kadiweu_ud_mappings.py | 144 | 16 | C | 273.99 | 3.71 | 1 017.67 | 0.0913 |
| build_text_from_rows | kadiweu_json_to_conllu.py | 904 | 11 | C | 182.84 | 5.06 | 925.61 | 0.0609 |
| choose_nominal_attachment_target | kadiweu_json_to_conllu.py | 599 | 8 | B | 121.01 | 6.33 | 766.42 | 0.0403 |
| pick_root_index | kadiweu_json_to_conllu.py | 559 | 23 | D | 178.81 | 3.42 | 611.73 | 0.0596 |
| main | kadiweu_lexicon_explorer.py | 823 | 21 | D | 183.48 | 2.80 | 513.73 | 0.0612 |
| build_space_aware_token_ranges | kadiweu_json_to_conllu.py | 394 | 6 | B | 127.44 | 3.57 | 455.14 | 0.0425 |
| resolve_empty_categories | kadiweu_empty_categories.py | 115 | 18 | C | 178.81 | 2.50 | 447.03 | 0.0596 |
| collect_mwt_group | kadiweu_json_to_conllu.py | 641 | 7 | B | 112.37 | 3.64 | 409.35 | 0.0375 |
| align_forms_to_text | kadiweu_token_ranges.py | 258 | 6 | B | 96.00 | 3.64 | 349.09 | 0.0320 |
| filter_entries | kadiweu_lexicon_explorer.py | 378 | 10 | B | 155.59 | 2.12 | 329.48 | 0.0519 |
| check_sentence | kadiweu_token_ranges.py | 395 | 9 | B | 85.84 | 3.82 | 327.74 | 0.0286 |
| best_known_split_profile | check_kadiweu_json_consistency.py | 210 | 10 | B | 68.11 | 4.29 | 291.92 | 0.0227 |
| search_by_pos_semantics | kadiweu_lexicon_explorer.py | 321 | 16 | C | 95.91 | 2.88 | 276.66 | 0.0320 |

## Top functions by Halstead volume

| Function | File | Line | CC | CC rank | Volume | Difficulty | Effort | Bugs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| convert_sentence | kadiweu_json_to_conllu.py | 1016 | 154 | F | 3 366.81 | 16.30 | 54 874.05 | 1.1223 |
| main | compare_kadiweu_conllu_versions.py | 331 | 62 | F | 980.69 | 10.97 | 10 753.72 | 0.3269 |
| analyze | check_kadiweu_json_consistency.py | 250 | 94 | F | 887.58 | 5.31 | 4 715.26 | 0.2959 |
| learn_overrides | update_overrides_from_gold.py | 394 | 51 | F | 761.81 | 10.23 | 7 795.30 | 0.2539 |
| infer_ud_upos | kadiweu_lexicon_explorer.py | 417 | 36 | E | 433.96 | 5.56 | 2 412.32 | 0.1447 |
| infer_feats | kadiweu_json_to_conllu.py | 712 | 36 | E | 412.53 | 6.06 | 2 500.19 | 0.1375 |
| main | induce_kadiweu_ud_mappings.py | 144 | 16 | C | 273.99 | 3.71 | 1 017.67 | 0.0913 |
| apply_spaceafter_from_text | kadiweu_json_to_conllu.py | 256 | 13 | C | 262.33 | 6.86 | 1 798.84 | 0.0874 |
| main | kadiweu_lexicon_explorer.py | 823 | 21 | D | 183.48 | 2.80 | 513.73 | 0.0612 |
| build_text_from_rows | kadiweu_json_to_conllu.py | 904 | 11 | C | 182.84 | 5.06 | 925.61 | 0.0609 |
| resolve_empty_categories | kadiweu_empty_categories.py | 115 | 18 | C | 178.81 | 2.50 | 447.03 | 0.0596 |
| pick_root_index | kadiweu_json_to_conllu.py | 559 | 23 | D | 178.81 | 3.42 | 611.73 | 0.0596 |
| filter_entries | kadiweu_lexicon_explorer.py | 378 | 10 | B | 155.59 | 2.12 | 329.48 | 0.0519 |
| build_space_aware_token_ranges | kadiweu_json_to_conllu.py | 394 | 6 | B | 127.44 | 3.57 | 455.14 | 0.0425 |
| choose_nominal_attachment_target | kadiweu_json_to_conllu.py | 599 | 8 | B | 121.01 | 6.33 | 766.42 | 0.0403 |
| collect_mwt_group | kadiweu_json_to_conllu.py | 641 | 7 | B | 112.37 | 3.64 | 409.35 | 0.0375 |
| main | kadiweu_tag_profiles.py | 344 | 7 | B | 109.39 | 2.25 | 246.13 | 0.0365 |
| compute_profiles | kadiweu_tag_profiles.py | 209 | 13 | C | 99.91 | 1.55 | 154.41 | 0.0333 |
| ud_notes | kadiweu_lexicon_explorer.py | 537 | 10 | B | 98.10 | 2.46 | 241.47 | 0.0327 |
| align_forms_to_text | kadiweu_token_ranges.py | 258 | 6 | B | 96.00 | 3.64 | 349.09 | 0.0320 |

## Top functions by cyclomatic complexity, with Halstead metrics

| Function | File | Line | CC | CC rank | Volume | Difficulty | Effort | Bugs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| convert_sentence | kadiweu_json_to_conllu.py | 1016 | 154 | F | 3 366.81 | 16.30 | 54 874.05 | 1.1223 |
| analyze | check_kadiweu_json_consistency.py | 250 | 94 | F | 887.58 | 5.31 | 4 715.26 | 0.2959 |
| main | compare_kadiweu_conllu_versions.py | 331 | 62 | F | 980.69 | 10.97 | 10 753.72 | 0.3269 |
| learn_overrides | update_overrides_from_gold.py | 394 | 51 | F | 761.81 | 10.23 | 7 795.30 | 0.2539 |
| infer_ud_upos | kadiweu_lexicon_explorer.py | 417 | 36 | E | 433.96 | 5.56 | 2 412.32 | 0.1447 |
| infer_feats | kadiweu_json_to_conllu.py | 712 | 36 | E | 412.53 | 6.06 | 2 500.19 | 0.1375 |
| _extract_field_values | kadiweu_lexicon_explorer.py | 647 | 25 | D | 25.27 | 1.20 | 30.32 | 0.0084 |
| stats | kadiweu_lexicon_explorer.py | 603 | 23 | D | 0.00 | 0.00 | 0.00 | 0.0000 |
| pick_root_index | kadiweu_json_to_conllu.py | 559 | 23 | D | 178.81 | 3.42 | 611.73 | 0.0596 |
| main | kadiweu_lexicon_explorer.py | 823 | 21 | D | 183.48 | 2.80 | 513.73 | 0.0612 |
| print_sentence_summary | inspect_kadiweu_json.py | 239 | 19 | C | 68.00 | 3.30 | 224.40 | 0.0227 |
| resolve_empty_categories | kadiweu_empty_categories.py | 115 | 18 | C | 178.81 | 2.50 | 447.03 | 0.0596 |
| sentence_to_rows | kadiweu_json_to_token_table.py | 235 | 17 | C | 64.73 | 2.00 | 129.45 | 0.0216 |
| search_by_pos_semantics | kadiweu_lexicon_explorer.py | 321 | 16 | C | 95.91 | 2.88 | 276.66 | 0.0320 |
| main | induce_kadiweu_ud_mappings.py | 144 | 16 | C | 273.99 | 3.71 | 1 017.67 | 0.0913 |
| pretty_entry | kadiweu_lexicon_explorer.py | 726 | 14 | C | 27.00 | 1.00 | 27.00 | 0.0090 |
| compute_profiles | kadiweu_tag_profiles.py | 209 | 13 | C | 99.91 | 1.55 | 154.41 | 0.0333 |
| apply_spaceafter_from_text | kadiweu_json_to_conllu.py | 256 | 13 | C | 262.33 | 6.86 | 1 798.84 | 0.0874 |
| parse_conllu | update_overrides_from_gold.py | 102 | 12 | C | 76.15 | 2.60 | 197.98 | 0.0254 |
| normalize_feats | compare_kadiweu_conllu_versions.py | 138 | 12 | C | 48.43 | 2.57 | 124.54 | 0.0161 |

## Compact publication table: top functions by Halstead effort

| Function | File | CC | CC rank | Halstead volume | Halstead effort |
| --- | --- | --- | --- | --- | --- |
| convert_sentence | kadiweu_json_to_conllu.py | 154 | F | 3 366.81 | 54 874.05 |
| main | compare_kadiweu_conllu_versions.py | 62 | F | 980.69 | 10 753.72 |
| learn_overrides | update_overrides_from_gold.py | 51 | F | 761.81 | 7 795.30 |
| analyze | check_kadiweu_json_consistency.py | 94 | F | 887.58 | 4 715.26 |
| infer_feats | kadiweu_json_to_conllu.py | 36 | E | 412.53 | 2 500.19 |
| infer_ud_upos | kadiweu_lexicon_explorer.py | 36 | E | 433.96 | 2 412.32 |
| apply_spaceafter_from_text | kadiweu_json_to_conllu.py | 13 | C | 262.33 | 1 798.84 |
| main | induce_kadiweu_ud_mappings.py | 16 | C | 273.99 | 1 017.67 |
| build_text_from_rows | kadiweu_json_to_conllu.py | 11 | C | 182.84 | 925.61 |
| choose_nominal_attachment_target | kadiweu_json_to_conllu.py | 8 | B | 121.01 | 766.42 |
