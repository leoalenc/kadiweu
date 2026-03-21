#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Normalize the Kadiwéu pedagogical grammar JSON into a flat token table.

Output:
- one row per sentence-token
- TSV by default, optionally CSV
- suitable for inspection, spreadsheet import, and rule design for UD conversion

Columns include:
- sentence metadata
- token metadata
- split morphemes and glosses
- chunk memberships
- proto-CoNLL-U scaffold fields

Usage
-----
Basic TSV to stdout:
    python3 kadiweu_json_to_token_table.py gramatica-pedagogica.json > tokens.tsv

Write TSV to file:
    python3 kadiweu_json_to_token_table.py gramatica-pedagogica.json --out tokens.tsv

Write CSV instead:
    python3 kadiweu_json_to_token_table.py gramatica-pedagogica.json --format csv --out tokens.csv

Only first 20 sentences:
    python3 kadiweu_json_to_token_table.py gramatica-pedagogica.json --limit 20 --out sample.tsv

Filter by sentence UID:
    python3 kadiweu_json_to_token_table.py gramatica-pedagogica.json --uid SOME-UID --out one.tsv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def safe_get(d: Any, *path: str, default=None):
    """Safely descend nested dicts."""
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def compact_json(obj: Any) -> str:
    """Compact JSON string for stable table cells."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=False)


def token_gloss(token: Dict[str, Any]) -> str:
    """Return token-level gloss if present."""
    return safe_get(token, "attributes", "gloss-br", default="") or ""


def split_gloss(split: Dict[str, Any]) -> str:
    """Return split-level gloss if present."""
    return safe_get(split, "attributes", "gloss-br", default="") or ""


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

    Keeps lightweight container metadata when available so you can later trace
    where the sentence came from.
    """
    if inherited_meta is None:
        inherited_meta = {}

    out: List[Dict[str, Any]] = []

    if isinstance(obj, dict):
        local_meta = dict(inherited_meta)

        # Preserve potentially useful container metadata
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

    Chunks in the JSON appear to use start/end span fields such as i and f,
    with a label t. We treat spans as inclusive. If a chunk lacks usable span
    data, it is ignored.
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


def index_proto_conllu(conllu_rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Index proto-CoNLL-U rows by 1-based order for lightweight alignment.

    This assumes the proto-conllu list is already ordered by token order,
    which seems to be the case in the uploaded JSON. If counts diverge,
    rows beyond the shorter side remain unmatched.
    """
    out: Dict[int, Dict[str, Any]] = {}
    for i, row in enumerate(conllu_rows, start=1):
        if isinstance(row, dict):
            out[i] = row
    return out


def normalize_split_list(token: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return normalized split records."""
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return []

    out = []
    for s in splits:
        if not isinstance(s, dict):
            continue
        out.append(
            {
                "v": s.get("v", ""),
                "t": s.get("t", ""),
                "gloss_br": split_gloss(s),
                "fn": s.get("fn", ""),
                "idx": s.get("idx", ""),
            }
        )
    return out


def sentence_to_rows(record: Dict[str, Any], sent_ordinal: int) -> List[Dict[str, Any]]:
    """Convert one sentence object into flat token rows."""
    sentence = record["sentence"]
    struct = sentence.get("struct", {}) if isinstance(sentence.get("struct"), dict) else {}

    tokens = struct.get("tokens", [])
    chunks = struct.get("chunks", [])
    conllu_rows = struct.get("conllu", [])

    if not isinstance(tokens, list):
        tokens = []
    if not isinstance(chunks, list):
        chunks = []
    if not isinstance(conllu_rows, list):
        conllu_rows = []

    chunk_membership = build_chunk_membership(tokens, chunks)
    conllu_index = index_proto_conllu(conllu_rows)

    sentence_uid = sentence.get("uid", "")
    sentence_text = sentence.get("text", "")
    translations = sentence.get("translations", {}) if isinstance(sentence.get("translations"), dict) else {}
    text_pt_br = translations.get("pt-br", "")
    visible = struct.get("visible", "")

    container_meta = record.get("container_meta", {})
    container_uid = container_meta.get("uid", "")
    container_id = container_meta.get("id", "")
    container_title = container_meta.get("title", "")
    path = record.get("path", "")

    rows: List[Dict[str, Any]] = []

    for row_ordinal, tok in enumerate(tokens, start=1):
        if not isinstance(tok, dict):
            continue

        p = tok.get("p", "")
        v = tok.get("v", "")
        t = tok.get("t", "")
        l = tok.get("l", "")
        gloss_br = token_gloss(tok)

        split_obj = tok.get("split", None)
        split_obj_json = compact_json(split_obj) if split_obj is not None else ""

        split_list = normalize_split_list(tok)
        split_count = len(split_list)

        split_forms = "|".join(str(s["v"]) for s in split_list)
        split_tags = "|".join(str(s["t"]) for s in split_list)
        split_glosses = "|".join(str(s["gloss_br"]) for s in split_list)
        split_fns = "|".join(str(s["fn"]) for s in split_list)
        split_idxs = "|".join(str(s["idx"]) for s in split_list)

        chunk_labels = chunk_membership.get(p, []) if isinstance(p, int) else []
        chunks_joined = "|".join(chunk_labels)

        proto = conllu_index.get(row_ordinal, {})
        proto_id = proto.get("id", "")
        proto_form = proto.get("form", "")
        proto_misc = compact_json(proto.get("misc")) if "misc" in proto else ""
        token_range = safe_get(proto, "misc", "TokenRange", default="") or ""

        rows.append(
            {
                # sentence-level metadata
                "sent_ordinal": sent_ordinal,
                "sent_uid": sentence_uid,
                "sent_text": sentence_text,
                "text_pt_br": text_pt_br,
                "visible": visible,
                "path": path,
                "container_uid": container_uid,
                "container_id": container_id,
                "container_title": container_title,

                # token-level source annotation
                "token_ordinal": row_ordinal,
                "token_p": p,
                "token_form": v,
                "token_tag_source": t,
                "token_level": l,
                "token_gloss_br": gloss_br,

                # split-level information flattened
                "split_obj_json": split_obj_json,
                "split_count": split_count,
                "split_forms": split_forms,
                "split_tags": split_tags,
                "split_glosses_br": split_glosses,
                "split_fns": split_fns,
                "split_idxs": split_idxs,

                # chunk membership
                "chunk_memberships": chunks_joined,

                # proto-CoNLL-U scaffold
                "proto_conllu_id": proto_id,
                "proto_conllu_form": proto_form,
                "proto_conllu_misc_json": proto_misc,
                "proto_token_range": token_range,
            }
        )

    return rows


def collect_rows(
    data: Any,
    uid: Optional[str] = None,
    text_contains: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Collect all flat token rows from the JSON."""
    sentence_records = walk_collect_sentences(data)
    sentence_records = filter_sentences(sentence_records, uid=uid, text_contains=text_contains)

    if limit is not None:
        sentence_records = sentence_records[:limit]

    all_rows: List[Dict[str, Any]] = []
    for sent_ordinal, record in enumerate(sentence_records, start=1):
        all_rows.extend(sentence_to_rows(record, sent_ordinal))

    return all_rows


def write_table(rows: List[Dict[str, Any]], out_path: Optional[Path], fmt: str) -> None:
    """Write the flat table as TSV or CSV."""
    if not rows:
        raise ValueError("No rows to write.")

    fieldnames = [
        "sent_ordinal",
        "sent_uid",
        "sent_text",
        "text_pt_br",
        "visible",
        "path",
        "container_uid",
        "container_id",
        "container_title",
        "token_ordinal",
        "token_p",
        "token_form",
        "token_tag_source",
        "token_level",
        "token_gloss_br",
        "split_obj_json",
        "split_count",
        "split_forms",
        "split_tags",
        "split_glosses_br",
        "split_fns",
        "split_idxs",
        "chunk_memberships",
        "proto_conllu_id",
        "proto_conllu_form",
        "proto_conllu_misc_json",
        "proto_token_range",
    ]

    delimiter = "\t" if fmt == "tsv" else ","

    if out_path is None:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Flatten the Kadiwéu pedagogical grammar JSON into a token table."
    )
    p.add_argument("json_file", help="Input JSON file")
    p.add_argument(
        "--out",
        default=None,
        help="Output file path. If omitted, writes to stdout.",
    )
    p.add_argument(
        "--format",
        choices=("tsv", "csv"),
        default="tsv",
        help="Output format (default: tsv).",
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
    return p


def main() -> int:
    args = build_argparser().parse_args()

    json_path = Path(args.json_file)
    if not json_path.is_file():
        print(f"ERROR: file not found: {json_path}", file=sys.stderr)
        return 1

    try:
        data = load_json(json_path)
        rows = collect_rows(
            data,
            uid=args.uid,
            text_contains=args.text_contains,
            limit=args.limit,
        )
        if not rows:
            print("No rows generated.", file=sys.stderr)
            return 2

        out_path = Path(args.out) if args.out else None
        write_table(rows, out_path, args.format)

        if out_path is not None:
            print(f"Wrote {len(rows)} rows to {out_path}", file=sys.stderr)

        return 0

    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())