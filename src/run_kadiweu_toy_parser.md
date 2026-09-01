# run_kadiweu_toy_parser.sh

## NAME

`run_kadiweu_toy_parser.sh` — run the Kadiwéu toy parser, compare its trees with reference trees, and optionally render them.

## SYNOPSIS

```text
./run_kadiweu_toy_parser.sh [OPTIONS] [all | LAST_RULE]
```

Brackets indicate optional arguments; `|` means “or”. Do not type these symbols.

## DESCRIPTION

Applies numbered parsing rules to a flat POS input and compares the resulting constituency trees with a **gold** file (reference analyses). The default experiment uses three rules and six sentences marked `DONE`.

`all`, also the default when omitted, runs every rule in the selected rule file. A positive integer runs through that rule, inclusive: `2` runs rules 1 and 2. The requested rule must exist.

Every run produces a bracketed PSD file and comparison reports. Optional displays show the **parser's output**, including incorrect analyses, rather than the gold trees. This allows students to inspect how the rules construct constituents and where they fail.

## REQUIREMENTS

- Bash; invoke the script directly or with `bash`, not `sh`.
- Python 3 compatible with the project's Python scripts.
- A working `corpussearch` command and its Java runtime.
- Standard Unix utilities, including `awk`, `sha256sum`, `mktemp`, `tee`, and `tr`.
- The project runner, `src/run_kadiweu_parser_rules.py`, with its dependencies.
- Rules, POS input, and matching gold PSD files.

Optional tree output also requires `src/kadiweu_psd_tree.py` and its dependency `kadiweu_constituency.py`. Annotated PSD input must have a metadata comment for each tree.

PDF, SVG, and PNG require Graphviz (`dot`). Combined PDFs also require `pdfunite`. On Ubuntu, install these optional system packages with:

```bash
sudo apt install graphviz poppler-utils
```

Annotated PSD and DOT output do not require Graphviz.

## OPTIONS

Long options accepting a value support both `--option VALUE` and `--option=VALUE`.

| Option | Meaning |
|---|---|
| `-r FILE`, `--rules FILE` | Use an alternative numbered rule file. |
| `-i FILE`, `--input FILE` | Use an alternative flat POS input. |
| `-g FILE`, `--gold FILE` | Use an alternative gold PSD file. Supply matching input and gold sentences, with corresponding IDs and order. |
| `--tree-format FORMAT` | Add `psd`, `pdf`, `svg`, `png`, or `dot` output. Repeat for multiple formats. No extra displays by default. |
| `--pdf-layout LAYOUT` | Choose `separate` (default), `combined`, or `both`. Requires `--tree-format pdf`. |
| `--tree-style STYLE` | Choose `ascii` (default) or `unicode` for displays inside the additional PSD file. |
| `--tree-script FILE` | Use a different path to `kadiweu_psd_tree.py`. |
| `-h`, `--help` | Print usage and exit. |

`--tree-format psd` adds text-tree displays inside metadata comments without changing the bracketed analyses. Graphical exports include metadata. `separate` writes one PDF per sentence; `combined` writes one multipage PDF in sentence order; `both` writes both forms. SVG, PNG, and DOT remain separate files per sentence.

## EXAMPLES

Run from the project's `src/` directory. If necessary, enable execution once:

```bash
chmod +x run_kadiweu_toy_parser.sh
```

Run the complete default experiment, then inspect the result after just rule 1:

```bash
./run_kadiweu_toy_parser.sh
./run_kadiweu_toy_parser.sh 1
```

Try modified rules saved in another file:

```bash
./run_kadiweu_toy_parser.sh --rules my_rules.txt all
```

Produce an annotated PSD and a single PDF containing every tree:

```bash
./run_kadiweu_toy_parser.sh \
  --tree-format psd --tree-format pdf --pdf-layout combined all
```

Keep both individual and combined PDFs after rule 2:

```bash
./run_kadiweu_toy_parser.sh --tree-format pdf --pdf-layout both 2
```

Use another aligned corpus:

```bash
./run_kadiweu_toy_parser.sh --input example.pos --gold example.gold.psd all
```

## FILES

The project root defaults to `~/kadiweu`. Default inputs are under `tests/corpussearch-toy-parser/`:

- `kadiweu_toy_parser_rules.txt`
- `kadiweu-toy-parser.pos`
- `kadiweu-toy-parser.gold.psd`

Outputs go to `data/generated/constituency/corpussearch-toy-parser/` under that root. There is no output-directory option.

For default inputs, `PREFIX` below is `kadiweu-toy-parser-through-rule-N`, where `N` is the last rule executed. Alternative input and rule filenames add labels to the prefix.

| Output | Contents |
|---|---|
| `PREFIX.psd` | Parser-generated bracketed trees. |
| `PREFIX-comparison.tsv` | Sentence-by-sentence comparison with gold. |
| `PREFIX-summary.tsv` | Counts of exact matches, trace-equivalent analyses, and structural differences. |
| `PREFIX.diff` | Structural differences. |
| `PREFIX-run.tsv` | Rule execution log. |
| `PREFIX-console.log` | Runner console output. |
| `PREFIX-hashes.txt` | SHA-256 checksums of inputs and generated artifacts. |
| `PREFIX.with-trees.psd` | Optional PSD with text-tree displays. |
| `PREFIX-trees/000001.FORMAT` | Optional individual exports, numbered by record order. |
| `PREFIX-trees.pdf` | Optional combined PDF. |

Intermediate parser files are retained in a uniquely named run directory. Repeating a run with the same prefix overwrites corresponding output files. Unrequested older exports are not removed; combined PDFs include only the current run's pages.

## ENVIRONMENT

| Variable | Default / purpose |
|---|---|
| `KADIWEU_ROOT` | Project root; defaults to `$HOME/kadiweu`. It is not inferred from the script's location. |
| `RULES`, `INPUT`, `GOLD` | Override default input paths; corresponding command-line options take precedence. |
| `RUNNER` | Runner path; defaults to `$KADIWEU_ROOT/src/run_kadiweu_parser_rules.py`. |
| `CORPUSSEARCH` | Executable name or path; defaults to `corpussearch`. |

For a project elsewhere:

```bash
KADIWEU_ROOT=/path/to/kadiweu ./run_kadiweu_toy_parser.sh all
```

## EXIT STATUS AND DIAGNOSTICS

**0** indicates successful completion, even when trees differ from gold. Inspect the comparison report to assess parsing accuracy. The displayed emulator status `1` means structural differences were found; it is not a wrapper failure.

Explicit configuration and validation errors return **2**; other command failures may produce another nonzero status.

A default-file hash mismatch means a frozen experiment file has changed. For exercises, save edited rules under a new filename and select it with `--rules`. Missing optional rendering dependencies are checked before parsing starts. If rendering subsequently fails, the ordinary parser output remains available.

## SEE ALSO

`run_kadiweu_parser_rules.py`, `kadiweu_psd_tree.py`, `dot(1)`, `pdfunite(1)`.
