#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate tag profiles from one or more Kadiwéu Tycho Brahe JSON dumps.

Purpose
-------
This script helps you understand the source annotation system before designing
or revising the UD conversion pipeline. It computes frequency profiles for:

1. source token tags
2. token forms by source tag
3. split tags
4. split tag sequences
5. gloss-br values
6. split tag x gloss-br
7. chunk labels
8. source tag x chunk label
9. source tag x split tag sequence

It now supports the current canonical JSON dump names used in the repository:

    data/ped-gramm.json
    data/hil-data.json
    data/van-data.json

The script infers a stable source_id from each input filename, for example:

    ped-gramm.json -> ped-gramm
    hil-data.json  -> hil-data
    van-data.json  -> van-data

Output
------
By default, it prints combined summaries to stdout.

Optionally, it writes TSV files into an output directory, including both
combined profiles and source-aware profiles:

Combined profiles:
- source_tag_counts.tsv
- token_form_by_source_tag.tsv
- split_tag_counts.tsv
- split_tag_sequence_counts.tsv
- gloss_br_counts.tsv
- split_tag_x_gloss_br.tsv
- chunk_label_counts.tsv
- source_tag_x_chunk.tsv
- source_tag_x_splitseq.tsv

Source-aware profiles:
- source_id_x_source_tag.tsv
- source_id_x_token_form_by_source_tag.tsv
- source_id_x_split_tag.tsv
- source_id_x_split_tag_sequence.tsv
- source_id_x_gloss_br.tsv
- source_id_x_split_tag_x_gloss_br.tsv
- source_id_x_chunk_label.tsv
- source_id_x_source_tag_x_chunk.tsv
- source_id_x_source_tag_x_splitseq.tsv

Usage
-----
Run from the repository root:

    python3 src/kadiweu_tag_profiles.py \
      data/ped-gramm.json \
      data/hil-data.json \
      data/van-data.json

Run from src/:

    python3 kadiweu_tag_profiles.py \
      ../data/ped-gramm.json \
      ../data/hil-data.json \
      ../data/van-data.json

Write TSV profiles:

    python3 src/kadiweu_tag_profiles.py \
      data/ped-gramm.json data/hil-data.json data/van-data.json \
      --outdir data/tag_profiles

Only first 50 matching sentences per selected source:

    python3 src/kadiweu_tag_profiles.py data/*.json --limit 50

Only one sentence:

    python3 src/kadiweu_tag_profiles.py data/*.json --uid SOME-UID

Filter by text substring:

    python3 src/kadiweu_tag_profiles.py data/*.json --text-contains ipegitege

Filter by source_id:

    python3 src/kadiweu_tag_profiles.py data/*.json --source-id ped-gramm

If you want to process only the current canonical dumps and you are running from
the repository root, you can use:

    python3 src/kadiweu_tag_profiles.py \
      data/ped-gramm.json data/hil-data.json data/van-data.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


CANONICAL_SOURCE_IDS = {"ped-gramm", "hil-data", "van-data"}


def safe_get(d: Any, *path: str, default=None):
    """Safely descend nested dicts."""
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def infer_source_id(path: Path) -> str:
    """
    Infer a stable source_id from an input JSON filename.

    Examples
    --------
    ped-gramm.json -> ped-gramm
    hil-data.json  -> hil-data
    van-data.json  -> van-data
    """
    return path.stem


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
    """Recursively traverse the JSON and collect sentence-like objects."""
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
    source_ids: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """Filter sentence records by source_id, UID, or substring in text."""
    out = sentences

    if source_ids:
        wanted = set(source_ids)
        out = [r for r in out if r.get("source_id") in wanted]

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
    """Return the sequence of split tags for a token, e.g. 'Erg|v|Apl'."""
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return ""

    tags = []
    for s in splits:
        if isinstance(s, dict):
            tags.append(str(s.get("t", "")))
    return "|".join(tags)


def _stringify_gloss_value(value: Any) -> str:
    """Return a stable string representation for one gloss value."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _extract_gloss_value(obj: Dict[str, Any]) -> str:
    """
    Extract a gloss value from a token or split object.

    The Tycho Brahe JSON is not fully uniform across dumps and export dates.
    Glosses may occur as either:

    - attributes: {"gloss-br": "..."}
    - attributes: {"gloss": "..."}
    - attributes: [{"gloss-br": "..."}, {"gloss": "..."}]
    - directly on the object as gloss-br/gloss, in older or normalized exports

    Prefer gloss-br when available, but fall back to gloss. If multiple values
    are present in an attributes list, join them with ' | ' so information is
    not silently dropped.
    """
    values: List[str] = []

    def add(value: Any) -> None:
        text = _stringify_gloss_value(value)
        if text:
            values.append(text)

    attrs = obj.get("attributes")

    if isinstance(attrs, dict):
        add(attrs.get("gloss-br"))
        if not values:
            add(attrs.get("gloss"))
    elif isinstance(attrs, list):
        # First collect all Brazilian Portuguese glosses, then fall back to
        # generic glosses only if no gloss-br value was found.
        for attr in attrs:
            if isinstance(attr, dict):
                add(attr.get("gloss-br"))
        if not values:
            for attr in attrs:
                if isinstance(attr, dict):
                    add(attr.get("gloss"))

    if not values:
        add(obj.get("gloss-br"))
    if not values:
        add(obj.get("gloss"))

    # Preserve order but remove duplicates.
    deduped = list(dict.fromkeys(values))
    return " | ".join(deduped)


def token_gloss_br(token: Dict[str, Any]) -> str:
    """Return a token-level gloss value, preferably gloss-br, or an empty string."""
    return _extract_gloss_value(token)


def split_gloss_br(split: Dict[str, Any]) -> str:
    """Return a split-level gloss value, preferably gloss-br, or an empty string."""
    return _extract_gloss_value(split)


def empty_profiles() -> Dict[str, Counter]:
    """Create all counters used by this script."""
    return {
        "source_tag_counts": Counter(),
        "token_form_by_source_tag": Counter(),
        "split_tag_counts": Counter(),
        "split_tag_sequence_counts": Counter(),
        "gloss_br_counts": Counter(),
        "split_tag_x_gloss_br": Counter(),
        "chunk_label_counts": Counter(),
        "source_tag_x_chunk": Counter(),
        "source_tag_x_splitseq": Counter(),
        "source_id_x_source_tag": Counter(),
        "source_id_x_token_form_by_source_tag": Counter(),
        "source_id_x_split_tag": Counter(),
        "source_id_x_split_tag_sequence": Counter(),
        "source_id_x_gloss_br": Counter(),
        "source_id_x_split_tag_x_gloss_br": Counter(),
        "source_id_x_chunk_label": Counter(),
        "source_id_x_source_tag_x_chunk": Counter(),
        "source_id_x_source_tag_x_splitseq": Counter(),
    }


def compute_profiles(sentence_records: List[Dict[str, Any]]) -> Dict[str, Counter]:
    """Compute combined and source-aware counters."""
    counters = empty_profiles()

    for rec in sentence_records:
        source_id = str(rec.get("source_id", ""))
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
            counters["source_id_x_source_tag"][(source_id, tag)] += 1
            counters["source_id_x_token_form_by_source_tag"][(source_id, tag, form)] += 1

            gloss = token_gloss_br(tok)
            if gloss:
                counters["gloss_br_counts"][gloss] += 1
                counters["source_id_x_gloss_br"][(source_id, gloss)] += 1

            seq = split_tag_sequence(tok)
            if seq:
                counters["split_tag_sequence_counts"][seq] += 1
                counters["source_tag_x_splitseq"][(tag, seq)] += 1
                counters["source_id_x_split_tag_sequence"][(source_id, seq)] += 1
                counters["source_id_x_source_tag_x_splitseq"][(source_id, tag, seq)] += 1

            splits = tok.get("splits", [])
            if isinstance(splits, list):
                for s in splits:
                    if isinstance(s, dict):
                        split_tag = str(s.get("t", ""))
                        counters["split_tag_counts"][split_tag] += 1
                        counters["source_id_x_split_tag"][(source_id, split_tag)] += 1

                        gloss = split_gloss_br(s)
                        if gloss:
                            counters["gloss_br_counts"][gloss] += 1
                            counters["source_id_x_gloss_br"][(source_id, gloss)] += 1
                            counters["split_tag_x_gloss_br"][(split_tag, gloss)] += 1
                            counters["source_id_x_split_tag_x_gloss_br"][(source_id, split_tag, gloss)] += 1

            token_chunks = chunk_membership.get(p, []) if isinstance(p, int) else []
            for ch in token_chunks:
                counters["chunk_label_counts"][ch] += 1
                counters["source_tag_x_chunk"][(tag, ch)] += 1
                counters["source_id_x_chunk_label"][(source_id, ch)] += 1
                counters["source_id_x_source_tag_x_chunk"][(source_id, tag, ch)] += 1

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
    """Write a counter to TSV. Supports scalar keys and tuple keys."""
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(key_headers + ["count"])

        for key, count in counter.most_common():
            if isinstance(key, tuple):
                row = list(key) + [count]
            else:
                row = [key, count]
            writer.writerow(row)


def write_profiles(outdir: Path, profiles: Dict[str, Counter]) -> None:
    """Write all combined and source-aware profile tables."""
    outdir.mkdir(parents=True, exist_ok=True)

    write_counter_tsv(outdir / "source_tag_counts.tsv", profiles["source_tag_counts"], ["source_tag"])
    write_counter_tsv(outdir / "token_form_by_source_tag.tsv", profiles["token_form_by_source_tag"], ["source_tag", "token_form"])
    write_counter_tsv(outdir / "split_tag_counts.tsv", profiles["split_tag_counts"], ["split_tag"])
    write_counter_tsv(outdir / "split_tag_sequence_counts.tsv", profiles["split_tag_sequence_counts"], ["split_tag_sequence"])
    write_counter_tsv(outdir / "gloss_br_counts.tsv", profiles["gloss_br_counts"], ["gloss_br"])
    write_counter_tsv(outdir / "split_tag_x_gloss_br.tsv", profiles["split_tag_x_gloss_br"], ["split_tag", "gloss_br"])
    write_counter_tsv(outdir / "chunk_label_counts.tsv", profiles["chunk_label_counts"], ["chunk_label"])
    write_counter_tsv(outdir / "source_tag_x_chunk.tsv", profiles["source_tag_x_chunk"], ["source_tag", "chunk_label"])
    write_counter_tsv(outdir / "source_tag_x_splitseq.tsv", profiles["source_tag_x_splitseq"], ["source_tag", "split_tag_sequence"])

    write_counter_tsv(outdir / "source_id_x_source_tag.tsv", profiles["source_id_x_source_tag"], ["source_id", "source_tag"])
    write_counter_tsv(outdir / "source_id_x_token_form_by_source_tag.tsv", profiles["source_id_x_token_form_by_source_tag"], ["source_id", "source_tag", "token_form"])
    write_counter_tsv(outdir / "source_id_x_split_tag.tsv", profiles["source_id_x_split_tag"], ["source_id", "split_tag"])
    write_counter_tsv(outdir / "source_id_x_split_tag_sequence.tsv", profiles["source_id_x_split_tag_sequence"], ["source_id", "split_tag_sequence"])
    write_counter_tsv(outdir / "source_id_x_gloss_br.tsv", profiles["source_id_x_gloss_br"], ["source_id", "gloss_br"])
    write_counter_tsv(outdir / "source_id_x_split_tag_x_gloss_br.tsv", profiles["source_id_x_split_tag_x_gloss_br"], ["source_id", "split_tag", "gloss_br"])
    write_counter_tsv(outdir / "source_id_x_chunk_label.tsv", profiles["source_id_x_chunk_label"], ["source_id", "chunk_label"])
    write_counter_tsv(outdir / "source_id_x_source_tag_x_chunk.tsv", profiles["source_id_x_source_tag_x_chunk"], ["source_id", "source_tag", "chunk_label"])
    write_counter_tsv(outdir / "source_id_x_source_tag_x_splitseq.tsv", profiles["source_id_x_source_tag_x_splitseq"], ["source_id", "source_tag", "split_tag_sequence"])


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate tag profiles from one or more Kadiwéu Tycho Brahe JSON dumps."
    )
    p.add_argument(
        "json_files",
        nargs="+",
        help="Input JSON file(s), e.g. data/ped-gramm.json data/hil-data.json data/van-data.json.",
    )
    p.add_argument(
        "--outdir",
        default=None,
        help="Optional directory where TSV profile files will be written.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N matching sentences per selected source.",
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
        "--source-id",
        action="append",
        default=None,
        help=(
            "Only process this inferred source_id. Can be repeated. "
            "Typical values: ped-gramm, hil-data, van-data."
        ),
    )
    p.add_argument(
        "--top",
        type=int,
        default=50,
        help="How many top items to print per profile (default: 50).",
    )
    p.add_argument(
        "--skip-source-aware-print",
        action="store_true",
        help="Print only combined profiles to stdout; source-aware TSVs are still written when --outdir is used.",
    )
    return p


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_sentence_records(json_paths: Sequence[Path]) -> Tuple[List[Dict[str, Any]], Counter]:
    """Load sentence records from all input files and annotate each with source_id."""
    records: List[Dict[str, Any]] = []
    source_sentence_counts: Counter = Counter()

    for json_path in json_paths:
        data = load_json(json_path)
        source_id = infer_source_id(json_path)
        source_records = walk_collect_sentences(data)

        for rec in source_records:
            rec["source_id"] = source_id
            rec["source_path"] = str(json_path)

        records.extend(source_records)
        source_sentence_counts[source_id] += len(source_records)

    return records, source_sentence_counts


def apply_limit_per_source(records: List[Dict[str, Any]], limit: Optional[int]) -> List[Dict[str, Any]]:
    """Apply --limit independently to each source_id."""
    if limit is None:
        return records

    seen: Counter = Counter()
    limited: List[Dict[str, Any]] = []

    for rec in records:
        source_id = str(rec.get("source_id", ""))
        if seen[source_id] >= limit:
            continue
        limited.append(rec)
        seen[source_id] += 1

    return limited


def main() -> int:
    args = build_argparser().parse_args()

    json_paths = [Path(p) for p in args.json_files]
    missing = [p for p in json_paths if not p.is_file()]
    if missing:
        for path in missing:
            print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1

    try:
        sentence_records, source_sentence_counts = load_sentence_records(json_paths)
        sentence_records = filter_sentences(
            sentence_records,
            uid=args.uid,
            text_contains=args.text_contains,
            source_ids=args.source_id,
        )
        sentence_records = apply_limit_per_source(sentence_records, args.limit)

        if not sentence_records:
            print("No matching sentences found.", file=sys.stderr)
            return 2

        profiles = compute_profiles(sentence_records)
        processed_by_source = Counter(str(rec.get("source_id", "")) for rec in sentence_records)

        print(f"Input JSON file(s): {len(json_paths)}")
        print(f"Processed {len(sentence_records)} sentence(s).")
        print("Processed sentences by source_id:")
        for source_id, count in sorted(processed_by_source.items()):
            total = source_sentence_counts.get(source_id, 0)
            print(f"  {source_id}: {count} / {total}")
        print()

        print_counter("Source tag counts", profiles["source_tag_counts"], limit=args.top)
        print_counter("Token form by source tag", profiles["token_form_by_source_tag"], limit=args.top)
        print_counter("Split tag counts", profiles["split_tag_counts"], limit=args.top)
        print_counter("Split tag sequence counts", profiles["split_tag_sequence_counts"], limit=args.top)
        print_counter("gloss-br value counts", profiles["gloss_br_counts"], limit=args.top)
        print_counter("Split tag x gloss-br", profiles["split_tag_x_gloss_br"], limit=args.top)
        print_counter("Chunk label counts", profiles["chunk_label_counts"], limit=args.top)
        print_counter("Source tag x chunk label", profiles["source_tag_x_chunk"], limit=args.top)
        print_counter("Source tag x split tag sequence", profiles["source_tag_x_splitseq"], limit=args.top)

        if not args.skip_source_aware_print:
            print_counter("Source ID x source tag", profiles["source_id_x_source_tag"], limit=args.top)
            print_counter("Source ID x split tag", profiles["source_id_x_split_tag"], limit=args.top)
            print_counter("Source ID x gloss-br", profiles["source_id_x_gloss_br"], limit=args.top)
            print_counter("Source ID x split tag x gloss-br", profiles["source_id_x_split_tag_x_gloss_br"], limit=args.top)
            print_counter("Source ID x chunk label", profiles["source_id_x_chunk_label"], limit=args.top)

        if args.outdir:
            outdir = Path(args.outdir)
            write_profiles(outdir, profiles)
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
