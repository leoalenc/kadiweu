# run_toy_parser.sh

## NAME

`run_toy_parser.sh` — run and evaluate a CorpusSearch toy grammar for any language.

## SYNOPSIS

```text
run_toy_parser.sh --rules FILE --input FILE --gold FILE [OPTIONS] [all|LAST_RULE]
```

## DESCRIPTION

Runs all numbered rules, or stops after `LAST_RULE`, inclusive. Compares the generated trees with the supplied gold (reference) trees. Input and gold must have unique, matching sentence IDs in the same order. There are no fixed corpus hashes, language labels, or sentence counts.

This is a separate, general-purpose wrapper based on `run_kadiweu_toy_parser.sh`. The original script remains available for the frozen Kadiwéu experiment.

## REQUIREMENTS

Bash, Python 3 compatible with the project scripts, standard Unix utilities, and a working CorpusSearch installation with Java. Install the wrapper in the project's `src/`, alongside `run_kadiweu_parser_rules.py` and its dependencies.

Optional displays use `kadiweu_psd_tree.py` and `kadiweu_constituency.py`. These existing dependency filenames are retained; they do not impose a Kadiwéu output prefix. PDF, SVG, and PNG require Graphviz (`dot`); combined PDFs also require `pdfunite` (`poppler-utils` on Ubuntu). Annotated PSD and DOT do not require Graphviz. Annotated PSD requires metadata comments preceding the trees.

## OPTIONS

| Option | Meaning |
|---|---|
| `-r`, `--rules FILE` | Numbered rule file; required. |
| `-i`, `--input FILE` | Flat POS corpus; required. |
| `-g`, `--gold FILE` | Gold PSD corpus; required. |
| `-o`, `--output-dir DIR` | Destination directory. |
| `--name NAME` | Override the output basename, before `-through-rule-N`. Use letters, digits, underscores, dots, and hyphens; start with a letter, digit, or underscore. |
| `--runner FILE` | Override the Python parser runner. |
| `--corpussearch COMMAND` | CorpusSearch executable name or path, without additional arguments. |
| `--tree-format FORMAT` | Additional `psd`, `pdf`, `svg`, `png`, or `dot` output; repeat for multiple formats. |
| `--pdf-layout LAYOUT` | `separate` (default), `combined`, or `both`; requires PDF output. |
| `--tree-style STYLE` | `ascii` (default) or `unicode` for annotated PSD. |
| `--tree-script FILE` | Override the display/export script. |
| `-h`, `--help` | Print usage and exit. |

Long options accept `--option=value` as well as `--option value`. Omitted `all|LAST_RULE` means `all`.

## EXAMPLE

From `tests/corpussearch-toy-parser/`:

```bash
bash ../../src/run_toy_parser.sh \
  --rules russian_toy_parser_rules.txt \
  --input russian-toy-parser.pos \
  --gold russian-toy-parser.gold.psd \
  --tree-format pdf --pdf-layout combined all
```

Use the corresponding English, Terena, or other filenames for another language. Supply `--name russian-np-exercise` to choose an explicit experiment name.

## FILES

By default, outputs go to `data/generated/constituency/corpussearch-toy-parser/` under the parent of the script's directory. `TOY_PARSER_ROOT` overrides that project root; `--output-dir` overrides the destination directly.

The output basename comes from the POS filename, removing trailing `.txt` and then `.pos`. When the rules filename matches the conventional stem (`russian_toy_parser_rules.txt` for `russian-toy-parser.pos`), it is not repeated. Other rules filenames add a label to distinguish variants. `--name` overrides this automatic basename.

For the example above with four rules:

```text
russian-toy-parser-through-rule-4.psd
russian-toy-parser-through-rule-4-comparison.tsv
russian-toy-parser-through-rule-4-trees.pdf
```

Other outputs include `-summary.tsv`, `.diff`, `-run.tsv`, `-console.log`, and `-hashes.txt`. Intermediate parser files are retained in a unique run directory. Optional annotated PSD uses `.with-trees.psd`; individual graphics use `-trees/000001.FORMAT`, in record order.

Repeated runs overwrite corresponding outputs. Older, unrequested exports are retained but excluded from a new combined PDF. Displays always show the generated analyses, including parsing errors.

## ENVIRONMENT AND EXIT STATUS

`RULES`, `INPUT`, `GOLD`, `RUNNER`, and `CORPUSSEARCH` may supply defaults; corresponding CLI options take precedence. `TOY_PARSER_ROOT` affects the default output directory, not helper-script lookup. The helpers default to the wrapper's directory.

Exit **0** means successful execution, including runs with structural differences from gold. Inspect the comparison report for accuracy. Explicit validation failures return **2**; other command failures may return another nonzero status. Rendering failures preserve the ordinary parser output.
