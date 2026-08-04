# Updating the DONE and REVIEW CorpusSearch files

## Purpose

`update_corpussearch_psd.sh` regenerates the CorpusSearch (`.psd`) versions of all sentences whose `struct_status` is `DONE` or `REVIEW` in the three current Kadiwéu JSON datasets. It replaces six repeated invocations of `kadiweu_constituency.py` with one reproducible command.

The generated files are:

- `data/generated/constituency/hil-data.done.psd`
- `data/generated/constituency/hil-data.review.psd`
- `data/generated/constituency/ped-gramm.done.psd`
- `data/generated/constituency/ped-gramm.review.psd`
- `data/generated/constituency/van-data.done.psd`
- `data/generated/constituency/van-data.review.psd`

## Location

Place both `update_corpussearch_psd.sh` and this documentation file in the repository's `src/` directory, beside `kadiweu_constituency.py`.

The script determines the repository root from its own location. It can therefore be invoked from any working directory and does not depend on the repository being installed specifically as `~/kadiweu`.

## Prerequisites

Before running the script:

- the current Tycho exports must already have been refreshed as `data/hil-data.json`, `data/ped-gramm.json`, and `data/van-data.json`;
- `src/kadiweu_constituency.py` must be executable;
- each sentence to be exported must have the intended `struct_status` in its source JSON.

If needed, make both programs executable:

```bash
chmod +x src/kadiweu_constituency.py src/update_corpussearch_psd.sh
```

## Usage

From the repository root:

```bash
./src/update_corpussearch_psd.sh
```

From `src/`:

```bash
./update_corpussearch_psd.sh
```

No arguments are required. The script creates `data/generated/constituency/` if it does not yet exist.

## Pipeline position

Run this script after refreshing the three source JSON files and after making any corrections to constituency conversion in `kadiweu_constituency.py`. The JSON files remain the authoritative inputs; the `.psd` files are generated CorpusSearch views used for queries, structural experiments, reports, and local tree revisions that may later be implemented manually in the Tycho GUI.

The script exports statuses separately rather than combining them. This preserves the distinction between approved `DONE` analyses and `REVIEW` analyses that still require inspection or correction.

## Safety and failure behavior

The six generated `.psd` files are outputs, not hand-edited source files. Running the script updates the existing versions, so manual changes made directly in those files may be lost. CorpusSearch revision experiments should be written to different output files.

The script checks that the converter is executable and that all three JSON inputs exist before generation begins. It stops on the first failed converter invocation, unset variable, or pipeline error. After every invocation, it also checks that the expected `.psd` file exists and is not empty.

Because the script stops at the first error, files generated earlier in the same run may already have been updated. Correct the reported problem and run the script again to regenerate the complete set consistently.

## Equivalent converter command

For each dataset and status, the script runs the equivalent of:

```bash
./kadiweu_constituency.py \
    ../data/hil-data.json \
    --all \
    --status DONE \
    --format corpussearch \
    --output-dir ../data/generated/constituency/
```

The dataset varies over `hil-data`, `ped-gramm`, and `van-data`; the status varies over `DONE` and `REVIEW`. Output filenames are assigned by `kadiweu_constituency.py`, using lowercase status names such as `.done.psd` and `.review.psd`.
