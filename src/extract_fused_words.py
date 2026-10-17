#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract fused-word occurrences and frequency summary for KadGramPed data.

The script processes the three current corpus exports (ped-gramm, hil-data,
van-data), keeps only DONE sentences, reads fused-word links and composite
tags from each JSON, and uses the matching constituency PSD to recover the
original sentence numbering.

Run from ~/kadiweu/src:
    python3 extract_kadgramped_fused_words.py

Defaults:
    JSON:   ~/kadiweu/data/{ped-gramm,hil-data,van-data}.json
    PSD:    ~/kadiweu/data/generated/constituency/*.done.psd
    output: ~/kadiweu/data/reports/fused-words/

For another checkout or uploaded files, use --data-dir, --psd-dir, and
--out-dir. PSD names may include a suffix such as .done(4).psd.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CORPORA = ("ped-gramm", "hil-data", "van-data")
ID_RE = re.compile(r"\(ID\s+([^\s)]+)\s*\)")


def collect_sentences(obj: Any) -> list[dict[str, Any]]:
    """Collect sentence objects in document order from a Tycho JSON export."""
    out: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if (isinstance(value.get("text"), str)
                    and isinstance(value.get("struct"), dict)
                    and isinstance(value["struct"].get("tokens"), list)):
                out.append(value)
                return
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(obj)
    return out


def find_psd(psd_dir: Path, corpus: str) -> Path:
    exact = psd_dir / f"{corpus}.done.psd"
    if exact.is_file():
        return exact
    candidates = sorted(psd_dir.glob(f"{corpus}.done*.psd"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(f"No {corpus}.done*.psd found in {psd_dir}")
    raise ValueError(f"More than one {corpus}.done*.psd found in {psd_dir}: {candidates}")


def sentence_ids(psd_path: Path, corpus: str) -> dict[int, str]:
    """Map original sentence ordinal to its short numeric suffix (e.g. 0.7)."""
    ids = ID_RE.findall(psd_path.read_text(encoding="utf-8"))
    out: dict[int, str] = {}
    for sid in ids:
        if not sid.startswith(corpus + ","):
            raise ValueError(f"Unexpected sentence ID {sid!r} in {psd_path}")
        suffix = sid.split(",", 1)[1]
        try:
            ordinal = int(suffix.rsplit(".", 1)[1])
        except (IndexError, ValueError) as exc:
            raise ValueError(f"Cannot derive ordinal from sentence ID {sid!r}") from exc
        if ordinal in out:
            raise ValueError(f"Duplicate sentence ordinal {ordinal} in {psd_path}")
        out[ordinal] = suffix
    return out


def fused_groups(tokens: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """Return (surface form, composite tag, split-off components) per token."""
    groups: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = []
    for token in tokens:
        ref = token.get("split")
        if not isinstance(ref, dict) or not isinstance(ref.get("idx"), int):
            continue
        if ref["idx"] == 0:
            groups.append((str(ref.get("v", "")), ref, [token]))
        elif groups:
            # Only the idx=0 record stores composite form/tag; following
            # records in this split sequence carry their index and surface.
            groups[-1][2].append(token)

    found: list[tuple[str, str, str]] = []
    for surface, composite, members in groups:
        by_idx: dict[int, dict[str, Any]] = {}
        for token in members:
            idx = token.get("split", {}).get("idx")
            if isinstance(idx, int):
                by_idx.setdefault(idx, token)
        if not surface or len(by_idx) < 2:
            continue
        components = " ".join(str(by_idx[i].get("v", "")) for i in sorted(by_idx))
        found.append((surface, str(composite.get("t", "")), components))
    return found


def extract_corpus(corpus: str, json_path: Path, psd_path: Path) -> tuple[list[dict[str, str]], int]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    sentences = collect_sentences(data)
    id_by_ordinal = sentence_ids(psd_path, corpus)
    occurrences: list[dict[str, str]] = []
    done_count = 0
    for ordinal, sentence in enumerate(sentences, start=1):
        if str(sentence.get("status", "")).upper() != "DONE":
            continue
        done_count += 1
        # The DONE PSD can be an earlier partial snapshot. Original sentence
        # ordinals stay stable, so use the PSD ID when present, and otherwise
        # reconstruct its suffix from the document ordinal.
        sent_id = id_by_ordinal.get(ordinal, f"0.{ordinal}")
        tokens = sentence.get("struct", {}).get("tokens", [])
        for surface, tag, components in fused_groups(tokens):
            occurrences.append({
                "corpus": corpus,
                "fused word": surface,
                "sentence id": sent_id,
                "components": components,
                "composite tag": tag,
            })
    return occurrences, done_count


def write_tsv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    default_data = Path.home() / "kadiweu/data"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=default_data,
                        help="directory containing the three JSON files")
    parser.add_argument("--psd-dir", type=Path, default=default_data / "generated/constituency",
                        help="directory containing each corpus's DONE PSD")
    parser.add_argument("--out-dir", type=Path,
                        default=default_data / "reports/fused-words",
                        help="directory for the occurrence and summary TSV files")
    args = parser.parse_args()

    try:
        occurrences: list[dict[str, str]] = []
        done_counts: dict[str, int] = {}
        for corpus in CORPORA:
            json_path = args.data_dir / f"{corpus}.json"
            if not json_path.is_file():
                raise FileNotFoundError(f"Missing JSON file: {json_path}")
            psd_path = find_psd(args.psd_dir, corpus)
            corpus_rows, done_count = extract_corpus(corpus, json_path, psd_path)
            occurrences.extend(corpus_rows)
            done_counts[corpus] = done_count

        # Keep each occurrence traceable without repeating the corpus prefix
        # inside sentence IDs. The corpus name is a separate column.
        occurrence_columns = ["corpus", "fused word", "sentence id", "components", "composite tag"]
        occurrences.sort(key=lambda r: (CORPORA.index(r["corpus"]), int(r["sentence id"].rsplit(".", 1)[-1])))

        counts = Counter((r["fused word"], r["composite tag"], r["components"]) for r in occurrences)
        summary = [
            {"fused word": fused, "composite tag": tag, "components": components, "frequency": str(freq)}
            for (fused, tag, components), freq in sorted(counts.items(), key=lambda item: (item[0][0].casefold(), item[0][1], item[0][2]))
        ]
        args.out_dir.mkdir(parents=True, exist_ok=True)
        occurrence_path = args.out_dir / "fused-words-occurrences.tsv"
        summary_path = args.out_dir / "fused-words-summary.tsv"
        write_tsv(occurrence_path, occurrences, occurrence_columns)
        write_tsv(summary_path, summary, ["fused word", "composite tag", "components", "frequency"])

        print("DONE sentences: " + ", ".join(f"{c}={done_counts[c]}" for c in CORPORA), file=sys.stderr)
        print(f"Fused-word occurrences: {len(occurrences)}; summary types: {len(summary)}", file=sys.stderr)
        print(f"Occurrences TSV: {occurrence_path}\nSummary TSV: {summary_path}", file=sys.stderr)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
