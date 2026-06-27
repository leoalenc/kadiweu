# Manifest

This directory preserves the frozen evaluation snapshot used for the
abstract submitted to the **Texto Livre** special issue on **IA and
Linguistics**.

**Repository:** https://github.com/leoalenc/kadiweu

This is **not** the official Universal Dependencies repository. It is
the public development repository for the Kadiwéu UD conversion pipeline
and also contains the evolving development version of
`kbc_unicamp-ud-test.conllu`, which is periodically synchronized with
the development branch of **UD_Kadiweu-Unicamp**.

## Directory structure

``` text
ia-linguistics-abstract/
  README.md
  MANIFEST.md
  drafts/
  gold/
  metadata/
  reports/
```

## Frozen draft CoNLL-U files

`drafts/draft-all.conllu` --- Concatenated draft CoNLL-U file containing
the converter output for all three source documents.

`drafts/draft-ped-gramm.conllu` --- Draft CoNLL-U output for the
`ped-gramm` source document.

`drafts/draft-hil.conllu` --- Draft CoNLL-U output for the `hil-data`
source document.

`drafts/draft-van.conllu` --- Draft CoNLL-U output for the `van-data`
source document.

## Frozen gold treebank

`gold/kbc_unicamp-ud-test.conllu` --- Gold-standard CoNLL-U treebank
used as the evaluation reference for this snapshot.

## Reports

`reports/conllu_drafts_vs_gold_all.md`,
`reports/conllu_drafts_vs_gold_all.csv`,
`reports/conllu_token_mismatches_all.csv` --- Evaluation reports
comparing `draft-all.conllu` against the frozen gold treebank.

`reports/conllu_drafts_vs_gold.md`, `reports/conllu_drafts_vs_gold.csv`,
`reports/conllu_token_mismatches.csv` --- Evaluation reports comparing
the individual draft treebanks against the frozen gold treebank.

## Metadata

`metadata/README.md` --- Overview of the metadata directory and the role
of each file.

`metadata/commands.sh` --- Commands used to generate the draft treebanks
and comparison reports.

`metadata/environment.txt` --- Software and system environment
information (Python version, operating system, Git version, etc.).

`metadata/git-commit.txt` --- Git commit hash identifying the exact
revision of the repository from which this snapshot was produced. This
file provides the primary link between the frozen evaluation snapshot
and the repository history. It should be created immediately after
committing the snapshot.

`metadata/notes.md` --- Human-readable notes describing the purpose of
the snapshot, its relation to the associated publication, and any
additional information needed for interpretation or reproduction.

## Reproducibility note

The files in this directory constitute a frozen evaluation snapshot
corresponding to the results reported in the Texto Livre abstract.
Together with the Git commit recorded in `metadata/git-commit.txt`, they
allow the exact evaluation to be reproduced even if subsequent
development modifies the converter, source JSON files, override
resources, draft CoNLL-U files, or the gold treebank.
