# Toy grammars

Toy grammars used in **P_LL425A_2026S2 — Computational Linguistics**, Department of Linguistics, University of Campinas (Unicamp), Brazil, second semester of 2026.

## Contributors

| Language | Author |
|---|---|
| Kadiwéu | Leonel Figueiredo de Alencar |
| English | Gabriel Castelano Millas |
| Terena | Jennyffer Katielly de Almeida Santos |
| Russian | Lena Mironova |

The English, Terena, and Russian fragments were developed by the students credited above. The Kadiwéu fragment was developed by Leonel Figueiredo de Alencar, freely based on or inspired by the larger Kadiwéu parser by Filomena Sandalo and Charlotte Galves. It is an extreme simplification for pedagogical purposes, specifically teaching CorpusSearch.

## Files

Each experiment uses a rule file, a flat part-of-speech (POS) input, and a gold PSD file containing reference constituency trees.

| Experiment | Rules | POS input | Gold trees |
|---|---|---|---|
| Kadiwéu (default) | `kadiweu_toy_parser_rules.txt` | `kadiweu-toy-parser.pos` | `kadiweu-toy-parser.gold.psd` |
| Terena | `terena_toy_parser_rules_root.txt` | `terena-toy-parser.pos` | `terena-toy-parser.gold.psd` |
| English | `english_toy_parser_rules.txt` | `english-toy-parser.pos` | `english-toy-parser.gold.psd` |
| Russian | `russian_toy_parser_rules.txt` | `russian-toy-parser.pos` | `russian-toy-parser.gold.psd` |

Other Kadiwéu rule variants are also available in this directory.

## Filename conventions

The fragments use underscores for rule filenames and hyphens for corpus filenames:

| File type | Pattern |
|---|---|
| Rules | `LANGUAGE_toy_parser_rules.txt` |
| POS input | `LANGUAGE-toy-parser.pos` |
| Gold trees | `LANGUAGE-toy-parser.gold.psd` |

A descriptive suffix, such as `_root`, distinguishes rule variants. The Terena rules retain this suffix, as does one Kadiwéu variant. POS input and gold trees share the same stem.

## Usage

Run the following commands from `tests/corpussearch-toy-parser/`. The three student experiments use the language-neutral wrapper `run_toy_parser.sh`. Inputs stay in this directory; generated outputs go into `results/LANGUAGE/`, which the script creates if necessary.

Run the original frozen Kadiwéu experiment (the specialized wrapper defaults to a project at `~/kadiweu`; set `KADIWEU_ROOT` if needed):

```bash
bash ../../src/run_kadiweu_toy_parser.sh all
```

Run the Terena experiment:

```bash
bash ../../src/run_toy_parser.sh \
  --rules terena_toy_parser_rules_root.txt \
  --input terena-toy-parser.pos \
  --gold terena-toy-parser.gold.psd \
  --output-dir ./results/terena \
  --name terena-toy-parser all
```

The explicit name keeps filenames short despite the `_root` rule variant; it does not change the rules or analyses.

Run the English experiment:

```bash
bash ../../src/run_toy_parser.sh \
  --rules english_toy_parser_rules.txt \
  --input english-toy-parser.pos \
  --gold english-toy-parser.gold.psd \
  --output-dir ./results/english all
```

Run the Russian experiment and produce a single PDF with all resulting trees:

```bash
bash ../../src/run_toy_parser.sh \
  --rules russian_toy_parser_rules.txt \
  --input russian-toy-parser.pos \
  --gold russian-toy-parser.gold.psd \
  --output-dir ./results/russian \
  --tree-format pdf --pdf-layout combined all
```

Replace `all` with a rule number, such as `1`, to stop after that rule. Add `--tree-format pdf --pdf-layout combined` before `all` in the English or Terena command to generate a combined PDF. Omit these options to run without graphical output. Use `--pdf-layout both` to retain individual PDFs as well.

## Requirements and results

The runner requires Bash, Python 3, a working CorpusSearch installation with Java, and the project scripts. Graphical PDF output additionally requires `kadiweu_psd_tree.py`, `kadiweu_constituency.py`, and Graphviz. Consolidation requires `pdfunite` from `poppler-utils`.

The student commands above write trees and reports to `results/english/`, `results/terena/`, and `results/russian/` within this directory. Without `--output-dir`, the generic wrapper still writes to `data/generated/constituency/corpussearch-toy-parser/` under the project root. The option does not move older results. Repeating the same experiment overwrites corresponding outputs; use a different `--name` or output subdirectory to preserve a run. The input and gold files are not modified. A successful run can still contain parsing errors: inspect the comparison report and the generated trees.

See [the generic script manual](../../src/run_toy_parser.md) for all options, output filenames, environment variables, and exit statuses.

The [original Kadiwéu wrapper manual](../../src/run_kadiweu_toy_parser.md) documents the frozen experiment separately.
