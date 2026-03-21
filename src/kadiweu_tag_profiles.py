#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate tag profiles from the Kadiwéu pedagogical grammar JSON.

Purpose
-------
This script helps you understand the annotation system before designing a
UD conversion pipeline. It computes frequency profiles for:

1. source token tags
2. token forms by source tag
3. split tags
4. split tag sequences
5. chunk labels
6. source tag x chunk label
7. source tag x split tag sequence

Output
------
By default, it prints summaries to stdout.

Optionally, it writes TSV files into an output directory, one file per profile:
- source_tag_counts.tsv
- token_form_by_source_tag.tsv
- split_tag_counts.tsv
- split_tag_sequence_counts.tsv
- chunk_label_counts.tsv
- source_tag_x_chunk.tsv
- source_tag_x_splitseq.tsv

Usage
-----
Basic:
    python3 kadiweu_tag_profiles.py gramatica-pedagogica.json

Write TSV profiles:
    python3 kadiweu_tag_profiles.py gramatica-pedagogica.json --outdir profiles

Only first 50 sentences:
    python3 kadiweu_tag_profiles.py gramatica-pedagogica.json --limit 50 --outdir profiles

Only one sentence:
    python3 kadiweu_tag_profiles.py gramatica-pedagogica.json --uid SOME-UID

Filter by text substring:
    python3 kadiweu_tag_profiles.py gramatica-pedagogica.json --text-contains ipegitege
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


def safe_get(d: Any, *path: str, default=None):
    """Safely descend nested dicts."""
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def is_sentence_object(obj: Any) -> bool:
    """
    Heuristic for recognizing a sentence object.
    We expect:
      - text
      - struct with at least one of tokens/chunks/conllu
    """
    if not isinstance(obj, dict):
        return False
    text = obj.get("text")
    struct = obj.get("struct")
    if not isinstance(text, str):
        return False
    if not isinstance(struct, dict):
        return False
    return any(k in struct for k in ("tokens", "chunks", "conllu"))


def walk_collect_sentences(
    obj: Any,
    path: str = "$",
    inherited_meta: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Recursively traverse the JSON and collect sentence-like objects.
    """
    if inherited_meta is None:
        inherited_meta = {}

    out: List[Dict[str, Any]] = []

    if isinstance(obj, dict):
        local_meta = dict(inherited_meta)

        for key in ("uid", "id", "title", "name", "label"):
            if key in obj and key not in local_meta:
                local_meta[key] = obj[key]

        if is_sentence_object(obj):
            out.append(
                {
                    "path": path,
                    "container_meta": local_meta,
                    "sentence": obj,
                }
            )

        for key, value in obj.items():
            out.extend(walk_collect_sentences(value, f"{path}.{key}", local_meta))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            out.extend(walk_collect_sentences(item, f"{path}[{i}]", inherited_meta))

    return out


def filter_sentences(
    sentences: List[Dict[str, Any]],
    uid: Optional[str] = None,
    text_contains: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter sentence records by UID or substring in text."""
    out = sentences

    if uid is not None:
        out = [r for r in out if safe_get(r, "sentence", "uid") == uid]

    if text_contains is not None:
        needle = text_contains.lower()
        out = [
            r
            for r in out
            if isinstance(safe_get(r, "sentence", "text"), str)
            and needle in safe_get(r, "sentence", "text").lower()
        ]

    return out


def build_chunk_membership(
    tokens: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
) -> Dict[int, List[str]]:
    """
    Build a mapping from token position p to all chunk labels that include it.

    Chunks use span fields i/f and a label t. We treat spans as inclusive.
    """
    membership: Dict[int, List[str]] = {}

    positions = []
    for tok in tokens:
        p = tok.get("p")
        if isinstance(p, int):
            positions.append(p)
            membership.setdefault(p, [])

    for ch in chunks:
        if not isinstance(ch, dict):
            continue

        start = ch.get("i")
        end = ch.get("f")
        label = ch.get("t")
        level = ch.get("l")

        if not isinstance(start, int) or not isinstance(end, int) or label is None:
            continue

        full_label = str(label)
        if level is not None:
            full_label = f"{full_label}[l={level}]"

        for p in positions:
            if start <= p <= end:
                membership[p].append(full_label)

    return membership


def split_tag_sequence(token: Dict[str, Any]) -> str:
    """
    Return the sequence of split tags for a token, e.g. 'Erg|v|Apl'.
    Empty string if no splits exist.
    """
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return ""

    tags = []
    for s in splits:
        if isinstance(s, dict):
            tags.append(str(s.get("t", "")))
    return "|".join(tags)


def compute_profiles(sentence_records: List[Dict[str, Any]]) -> Dict[str, Counter]:
    """
    Compute all counters of interest.
    """
    counters = {
        "source_tag_counts": Counter(),
        "token_form_by_source_tag": Counter(),
        "split_tag_counts": Counter(),
        "split_tag_sequence_counts": Counter(),
        "chunk_label_counts": Counter(),
        "source_tag_x_chunk": Counter(),
        "source_tag_x_splitseq": Counter(),
    }

    for rec in sentence_records:
        sentence = rec["sentence"]
        struct = sentence.get("struct", {}) if isinstance(sentence.get("struct"), dict) else {}

        tokens = struct.get("tokens", [])
        chunks = struct.get("chunks", [])

        if not isinstance(tokens, list):
            tokens = []
        if not isinstance(chunks, list):
            chunks = []

        chunk_membership = build_chunk_membership(tokens, chunks)

        for tok in tokens:
            if not isinstance(tok, dict):
                continue

            tag = str(tok.get("t", ""))
            form = str(tok.get("v", ""))
            p = tok.get("p")

            counters["source_tag_counts"][tag] += 1
            counters["token_form_by_source_tag"][(tag, form)] += 1

            seq = split_tag_sequence(tok)
            if seq:
                counters["split_tag_sequence_counts"][seq] += 1
                counters["source_tag_x_splitseq"][(tag, seq)] += 1

            splits = tok.get("splits", [])
            if isinstance(splits, list):
                for s in splits:
                    if isinstance(s, dict):
                        split_tag = str(s.get("t", ""))
                        counters["split_tag_counts"][split_tag] += 1

            token_chunks = chunk_membership.get(p, []) if isinstance(p, int) else []
            for ch in token_chunks:
                counters["chunk_label_counts"][ch] += 1
                counters["source_tag_x_chunk"][(tag, ch)] += 1

    return counters


def print_counter(title: str, counter: Counter, limit: int = 50) -> None:
    """Pretty-print the top entries of a Counter."""
    print("=" * 80)
    print(title)
    print("=" * 80)
    if not counter:
        print("<empty>")
        print()
        return

    for i, (key, count) in enumerate(counter.most_common(limit), start=1):
        print(f"{i:>4}  {key!r}  ->  {count}")
    print()


def write_counter_tsv(
    path: Path,
    counter: Counter,
    key_headers: List[str],
) -> None:
    """
    Write a counter to TSV. Supports either scalar keys or tuple keys.
    """
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")

        writer.writerow(key_headers + ["count"])

        for key, count in counter.most_common():
            if isinstance(key, tuple):
                row = list(key) + [count]
            else:
                row = [key, count]
            writer.writerow(row)


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate tag profiles from the Kadiwéu pedagogical grammar JSON."
    )
    p.add_argument("json_file", help="Input JSON file")
    p.add_argument(
        "--outdir",
        default=None,
        help="Optional directory where TSV profile files will be written.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N matching sentences.",
    )
    p.add_argument(
        "--uid",
        default=None,
        help="Only process the sentence with this UID.",
    )
    p.add_argument(
        "--text-contains",
        default=None,
        help="Only process sentences whose text contains this substring.",
    )
    p.add_argument(
        "--top",
        type=int,
        default=50,
        help="How many top items to print per profile (default: 50).",
    )
    return p


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    args = build_argparser().parse_args()

    json_path = Path(args.json_file)
    if not json_path.is_file():
        print(f"ERROR: file not found: {json_path}", file=sys.stderr)
        return 1

    try:
        data = load_json(json_path)

        sentence_records = walk_collect_sentences(data)
        sentence_records = filter_sentences(
            sentence_records,
            uid=args.uid,
            text_contains=args.text_contains,
        )

        if args.limit is not None:
            sentence_records = sentence_records[:args.limit]

        if not sentence_records:
            print("No matching sentences found.", file=sys.stderr)
            return 2

        profiles = compute_profiles(sentence_records)

        print(f"Processed {len(sentence_records)} sentence(s).\n")

        print_counter("Source tag counts", profiles["source_tag_counts"], limit=args.top)
        print_counter("Token form by source tag", profiles["token_form_by_source_tag"], limit=args.top)
        print_counter("Split tag counts", profiles["split_tag_counts"], limit=args.top)
        print_counter("Split tag sequence counts", profiles["split_tag_sequence_counts"], limit=args.top)
        print_counter("Chunk label counts", profiles["chunk_label_counts"], limit=args.top)
        print_counter("Source tag x chunk label", profiles["source_tag_x_chunk"], limit=args.top)
        print_counter("Source tag x split tag sequence", profiles["source_tag_x_splitseq"], limit=args.top)

        if args.outdir:
            outdir = Path(args.outdir)
            outdir.mkdir(parents=True, exist_ok=True)

            write_counter_tsv(
                outdir / "source_tag_counts.tsv",
                profiles["source_tag_counts"],
                ["source_tag"],
            )
            write_counter_tsv(
                outdir / "token_form_by_source_tag.tsv",
                profiles["token_form_by_source_tag"],
                ["source_tag", "token_form"],
            )
            write_counter_tsv(
                outdir / "split_tag_counts.tsv",
                profiles["split_tag_counts"],
                ["split_tag"],
            )
            write_counter_tsv(
                outdir / "split_tag_sequence_counts.tsv",
                profiles["split_tag_sequence_counts"],
                ["split_tag_sequence"],
            )
            write_counter_tsv(
                outdir / "chunk_label_counts.tsv",
                profiles["chunk_label_counts"],
                ["chunk_label"],
            )
            write_counter_tsv(
                outdir / "source_tag_x_chunk.tsv",
                profiles["source_tag_x_chunk"],
                ["source_tag", "chunk_label"],
            )
            write_counter_tsv(
                outdir / "source_tag_x_splitseq.tsv",
                profiles["source_tag_x_splitseq"],
                ["source_tag", "split_tag_sequence"],
            )

            print(f"TSV profiles written to: {outdir}", file=sys.stderr)

        return 0

    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())