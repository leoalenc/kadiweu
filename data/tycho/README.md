# Tycho Brahe Platform source exports

This directory stores the **original downloaded exports** from the Tycho Brahe
Platform after they have been processed by
`src/refresh_kadiweu_jsons.sh`.

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

| Canonical base | Document UID | Downloaded JSON | Downloaded PSD | Archived JSON | Archived PSD | Canonical JSON | Canonical PSD |
|---|---|---|---|---|---|---|---|
| `ped-gramm` | `28eeb8a0-d923-4d75-aebe-599aadddfbbb` | `6a63e5f1b431b1358862e302.json` | `6a63e5fab431b1358862e303.psd` | `json/6a63e5f1b431b1358862e302.json` | `psd/6a63e5fab431b1358862e303.psd` | `../ped-gramm.json` | `../ped-gramm.psd` |
| `hil-data` | `ffef8450-e302-4882-8306-e5998d31f584` | `6a63c4b7b431b1358862e2fe.json` | `6a63c4c4b431b1358862e2ff.psd` | `json/6a63c4b7b431b1358862e2fe.json` | `psd/6a63c4c4b431b1358862e2ff.psd` | `../hil-data.json` | `../hil-data.psd` |
| `van-data` | `9d0f60a9-8c32-44c0-ac68-0b5d5b993db8` | `6a63e614b431b1358862e304.json` | `6a63e61cb431b1358862e305.psd` | `json/6a63e614b431b1358862e304.json` | `psd/6a63e61cb431b1358862e305.psd` | `../van-data.json` | `../van-data.psd` |

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

Generated: 2026-07-24T19:24:58-03:00
