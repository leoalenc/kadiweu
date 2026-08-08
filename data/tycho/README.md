# Tycho Brahe Platform source exports

This directory stores the **original downloaded exports** from the Tycho Brahe
Platform after they have been processed by
`src/refresh_kadiweu_jsons.sh`.

The exports come from three documents belonging to the Tycho Brahe corpus
*$TYCHO_CORPUS_TITLE*. The document titles are the human-readable titles
currently shown on the platform; the repository document identifiers remain
stable if those titles change.

For a durable explanation of the corpus–document relationship and the history
of the `ped-gramm` identifier, see `../README.md`.

## Directory names

- `json/`: original JSON exports downloaded from the platform.
- `psd/`: original Penn-style constituency tree files downloaded from the
  platform.

The short parent name `tycho` identifies the external source. The format names
`json` and `psd` make the two archive directories compact and unambiguous
within this repository.

## Naming policy

Downloaded files retain their opaque Tycho Brahe export names in this archive.
The processing script creates stable, human-readable canonical names directly
under `data/`:

| Repository document identifier | Tycho Brahe document title | Document UID | Downloaded JSON | Downloaded PSD | Archived JSON | Archived PSD | Canonical JSON | Canonical PSD |
|---|---|---|---|---|---|---|---|---|
| `ped-gramm` | Dados para a gramática do sintagma nominal | `28eeb8a0-d923-4d75-aebe-599aadddfbbb` | `6a760d805ed58a65b62497bc.json` | `6a760d895ed58a65b62497bd.psd` | `json/6a760d805ed58a65b62497bc.json` | `psd/6a760d895ed58a65b62497bd.psd` | `../ped-gramm.json` | `../ped-gramm.psd` |
| `hil-data` | dados do Hilário abril de 2026 | `ffef8450-e302-4882-8306-e5998d31f584` | `6a7608755ed58a65b62497ba.json` | `6a76087c5ed58a65b62497bb.psd` | `json/6a7608755ed58a65b62497ba.json` | `psd/6a76087c5ed58a65b62497bb.psd` | `../hil-data.json` | `../hil-data.psd` |
| `van-data` | Vanda dados | `9d0f60a9-8c32-44c0-ac68-0b5d5b993db8` | `6a7608115ed58a65b62497b8.json` | `6a7608185ed58a65b62497b9.psd` | `json/6a7608115ed58a65b62497b8.json` | `psd/6a7608185ed58a65b62497b9.psd` | `../van-data.json` | `../van-data.psd` |

## Pairing JSON and PSD exports

A JSON export is identified by the stable document UID stored in its content.
The corresponding PSD file does not contain that UID, and Tycho Brahe assigns
new, unrelated opaque filenames whenever JSON and PSD files are downloaded.
PSD exports contain all and only JSON sentences whose sentence-level
`status` is `DONE`, preserving their relative order. The script therefore
compares the token `v` values of every `DONE` JSON sentence with the
terminal sequence of the corresponding PSD tree. Matching is case-insensitive,
treats `G` and `ǥ` as equivalent, and ignores empty-category terminals.
Both the sentence counts and every ordered token sequence must agree. If
several PSD downloads match completely, the newest one is selected and the
alternatives are reported.

## Normalization

The archived files are untouched originals. Normalization is applied only to
the canonical working copies:

- canonical JSON: `ǥ` → `G`;
- canonical PSD: `G` → `ǥ`.

Generated: 2026-08-07T19:18:37-03:00
