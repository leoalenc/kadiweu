# Kadiwéu TBP refresh and parser C evaluation pipeline

`run_kadiweu_parser_C_refresh_pipeline.sh` performs the complete sequence needed
to test a new TBP parser C publication against refreshed Kadiwéu data. It replaces
the individual refresh, conversion, hashing, parser A, compatibility-generation,
and parser C commands previously run by hand.

## What the pipeline does

In order, the script:

1. refreshes the canonical `ped-gramm`, `hil-data`, and `van-data` resources from
   downloaded TBP JSON and PSD exports;
2. regenerates the corresponding TXT and JSONL inspection resources as part of
   the refresh;
3. regenerates the six CorpusSearch-compatible DONE/REVIEW PSD files;
4. rebuilds the 206-sentence full-test gold and POS pair;
5. recreates and verifies the full-test input-hash manifest;
6. reruns parser A against the refreshed gold reference;
7. archives the newest complete `Kadiw-u*.txt`/`Kadiw-u*.json` rules pair and
   creates the compatibility JSON and dated parser C runner;
8. runs parser C and generates its comparison, diff, summary, transition, log,
   and provenance files; and
9. prints an authoritative DONE-only accuracy and A-to-C transition summary;
10. generates the illustrated DONE-only A-to-C transition report in Markdown;
    and
11. converts that report to PDF with Pandoc and WeasyPrint.

The dependency chain is:

```text
TBP document JSON/PSD exports
  -> canonical JSON/PSD/TXT/JSONL resources
  -> six DONE/REVIEW CorpusSearch PSD files
  -> full-test gold/POS and hash manifest
  -> refreshed parser A baseline
  -> parser C evaluation

TBP Kadiw-u TXT/JSON rules + histórico.txt
  -> archived dated rules
  -> compatibility JSON and dated C runner
  -> parser C evaluation
```

## Requirements

The project is expected at `~/kadiweu` unless `KADIWEU_ROOT` or
`--project-root` specifies another location. The following project scripts must
already be present and executable under `src/`:

```text
refresh_kadiweu_jsons.sh
update_corpussearch_psd.sh
build_kadiweu_parser_full_test.sh
run_kadiweu_parser_full_test_A.sh
create_kadiweu_parser_compat.py
run_kadiweu_parser_rules.py
make_kadiweu_parser_transition_report.py
```

CorpusSearch must be available as `corpussearch` on `PATH` when the A and C
runners execute. PDF production additionally requires `pandoc` and
`weasyprint` on `PATH`.

For a complete default run, the downloads directory must contain fresh JSON and
PSD exports for all three TBP documents and a complete same-stem parser-rule
pair, for example:

```text
Kadiw-u (2).txt
Kadiw-u (2).json
```

The compatibility generator selects the newest complete pair by modification
time. A lone JSON or TXT file is ignored.

## Normal use

Make the script executable after copying it to `~/kadiweu/src/`:

```bash
chmod +x ~/kadiweu/src/run_kadiweu_parser_C_refresh_pipeline.sh
```

Run the complete pipeline:

```bash
cd ~/kadiweu
src/run_kadiweu_parser_C_refresh_pipeline.sh \
  --history "$HOME/Dropbox/projects/2025/post-doc/parser/histórico.txt"
```

The displayed history path is already the default, so the shortest invocation is:

```bash
cd ~/kadiweu
src/run_kadiweu_parser_C_refresh_pipeline.sh
```

## Options

```text
--project-root DIR   Repository root
--downloads-dir DIR  Directory containing the downloaded TBP exports
--history FILE       TBP parser histórico.txt
--skip-refresh       Do not import new canonical JSON/PSD resources
--runner FILE        Reuse an existing dated parser C runner
-h, --help           Show command-line help
```

If the canonical JSON resources have already been refreshed but all derived
files must be rebuilt, use:

```bash
src/run_kadiweu_parser_C_refresh_pipeline.sh --skip-refresh
```

To evaluate with an already generated C runner, avoiding a collision when the
same TBP parser publication has already been archived, use:

```bash
src/run_kadiweu_parser_C_refresh_pipeline.sh \
  --skip-refresh \
  --runner src/run_kadiweu_parser_full_test_C_250926_1055.sh
```

## Hash handling

`build_kadiweu_parser_full_test.sh --force` replaces the gold and POS files but
does not update `kadiweu-parser-full-test-input-hashes.txt`. The orchestration
script therefore recreates the manifest atomically with the new files and
immediately checks it with `sha256sum -c`.

The dated parser C runner separately verifies the pinned rules and definitions
hashes, the expected number of comparison rows, and the expected number of
executed rules.

## Why parser A is rerun

Parser C produces A-to-C transition tables using
`kadiweu-parser-full-test-A-comparison.tsv`. After the gold reference changes,
the previous A comparison is stale. The pipeline consequently reruns parser A
before parser C so both versions are compared against exactly the same refreshed
reference.

## DONE and REVIEW interpretation

Only DONE sentences constitute an authoritative evaluation reference.

For DONE sentences:

- `EXACT_MATCH` and `TRACE_EQUIVALENT` count as acceptable analyses;
- `STRUCTURAL_DIFFERENCE` counts as an error;
- A-to-C changes may be described as corrections, regressions, or persistent
  structural problems.

REVIEW trees are provisional and are generally not correct. Their transitions
must not be interpreted as improvements or regressions. They may be reported
only as descriptive agreement changes. For this reason, the final summary
printed by the orchestration script reports accuracy and improvements/regressions
only for DONE sentences.

## Transition report and PDF

After parser C finishes, the pipeline passes the A-to-C transition table and
the A, C, and gold PSD files to
`make_kadiweu_parser_transition_report.py`. The report generator selects DONE
sentences and includes corrections, new structural differences, and persistent
structural differences. REVIEW sentences are not treated as improvements or
regressions.

The runner timestamp determines the output names. For example, runner
`run_kadiweu_parser_full_test_C_250926_1055.sh` produces:

```text
kadiweu-parser-full-test-A-to-C-250926-1055-DONE-review-svg.md
kadiweu-parser-full-test-A-to-C-250926-1055-DONE-review.pdf
```

SVG images are used in the intermediate Markdown because they render reliably
and remain sharp in the PDF. Pandoc performs the conversion with
`--pdf-engine=weasyprint` from inside the output directory so that the relative
image paths resolve correctly.

## Principal outputs

The generated evaluation files are stored under
`data/generated/constituency/`, including:

```text
kadiweu-parser-full-test.gold.psd
kadiweu-parser-full-test.pos
kadiweu-parser-full-test-input-hashes.txt
kadiweu-parser-full-test-A-comparison.tsv
kadiweu-parser-full-test-C.psd
kadiweu-parser-full-test-C-comparison.tsv
kadiweu-parser-full-test-C.diff
kadiweu-parser-full-test-C-run.tsv
kadiweu-parser-full-test-C-summary.tsv
kadiweu-parser-full-test-A-to-C-transitions.tsv
kadiweu-parser-full-test-A-to-C-summary.tsv
kadiweu-parser-full-test-C-hashes.txt
kadiweu-parser-full-test-C-console.log
kadiweu-parser-full-test-A-to-C-DDMMYY-HHMM-DONE-review-svg.md
kadiweu-parser-full-test-A-to-C-DDMMYY-HHMM-DONE-review.pdf
```

The original TBP document exports are archived under `data/tycho/`. Original
dated parser-rule exports and the generated compatibility JSON are stored under
`~/Dropbox/projects/2025/post-doc/parser/` by default.

## Failure behavior

The orchestration script uses strict shell error handling and stops when a
required file, executable, command, count, or hash check fails. Parser C may
internally report `FAIL` and emulator status `1` when structural differences
against gold are found; its dated wrapper handles that expected comparison
outcome and still completes successfully. Status `2` indicates an execution or
configuration failure and stops the pipeline.
