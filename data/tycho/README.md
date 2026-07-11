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
| `ped-gramm` | `28eeb8a0-d923-4d75-aebe-599aadddfbbb` | `6a515ffa2ed8e12ea325e239.json` | `6a51600d2ed8e12ea325e23a.psd` | `json/6a515ffa2ed8e12ea325e239.json` | `psd/6a51600d2ed8e12ea325e23a.psd` | `../ped-gramm.json` | `../ped-gramm.psd` |
| `hil-data` | `ffef8450-e302-4882-8306-e5998d31f584` | `6a515fda2ed8e12ea325e237.json` | `6a515feb2ed8e12ea325e238.psd` | `json/6a515fda2ed8e12ea325e237.json` | `psd/6a515feb2ed8e12ea325e238.psd` | `../hil-data.json` | `../hil-data.psd` |
| `van-data` | `9d0f60a9-8c32-44c0-ac68-0b5d5b993db8` | `6a51601f2ed8e12ea325e23b.json` | `6a5160262ed8e12ea325e23c.psd` | `json/6a51601f2ed8e12ea325e23b.json` | `psd/6a5160262ed8e12ea325e23c.psd` | `../van-data.json` | `../van-data.psd` |

## Pairing JSON and PSD exports

A JSON export is identified by the stable document UID stored in its content.
The corresponding PSD file does not contain that UID, and Tycho Brahe assigns
new, unrelated opaque filenames whenever JSON and PSD files are downloaded.
The script therefore extracts the first sentence from the JSON and the terminal
sequence of the first PSD tree, normalizes both, and compares them. Matching is
case-insensitive, treats `G` and `ǥ` as equivalent, and ignores tree labels,
parentheses, and whitespace differences. If several PSD downloads match, the
newest one is selected and the alternatives are reported.

## Normalization

The archived files are untouched originals. Normalization is applied only to
the canonical working copies:

- canonical JSON: `ǥ` → `G`;
- canonical PSD: `G` → `ǥ`.

Generated: 2026-07-10T23:21:13-03:00
