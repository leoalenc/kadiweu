#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Inspect the structure of a Kadiwéu Tycho Brahe JSON source document in a way that is useful
for later conversion to UD CoNLL-U. 

The repository uses stable source identifiers for the three current Tycho Brahe
source documents:

- ped-gramm
- hil-data
- van-data

The corresponding JSON files are expected to be named ped-gramm.json,
hil-data.json, and van-data.json.


What this script does
---------------------
- Loads the JSON file.
- Walks recursively through the structure and collects all sentence-like objects.
- Prints, for each sentence:
  * sentence UID
  * text
  * translations
  * struct.conllu scaffold
  * struct.tokens with:
      - position p
      - surface form v
      - source tag t
      - level l
      - gloss-br (if present)
      - split/splits information
  * struct.chunks
- Optionally limits output to the first N sentences.
- Optionally outputs JSONL records for downstream scripting.

Usage
-----
Basic inspection:
    python3 inspect_kadiweu_json.py ped-gramm.json

Inspect only first 10 sentences:
    python3 inspect_kadiweu_json.py ped-gramm.json --limit 10

Inspect one sentence by UID:
    python3 inspect_kadiweu_json.py ped-gramm.json --uid e553e02e-0d33-4fed-8f6a-b7cf5c9cf9c9

Write normalized JSONL:
    python3 inspect_kadiweu_json.py ped-gramm.json --jsonl-out ped-gramm.jsonl

Usage examples with the other JSON files
    python3 inspect_kadiweu_json.py data/ped-gramm.json
    python3 inspect_kadiweu_json.py data/hil-data.json --summary-only
    python3 inspect_kadiweu_json.py data/van-data.json --limit 10
    python3 inspect_kadiweu_json.py data/ped-gramm.json --jsonl-out data/ped-gramm.jsonl
    python3 inspect_kadiweu_json.py data/hil-data.json --jsonl-out data/hil-data.jsonl
    python3 inspect_kadiweu_json.py data/van-data.json --jsonl-out data/van-data.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def safe_get(d: Any, *path: str, default=None):
    """Safely descend nested dicts."""
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def compact_json(obj: Any) -> str:
    """Compact JSON rendering for inline display."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=False)


def token_gloss(token: Dict[str, Any]) -> Optional[str]:
    """Return token-level gloss if present."""
    return safe_get(token, "attributes", "gloss-br")


def split_gloss(split: Dict[str, Any]) -> Optional[str]:
    """Return split-level gloss if present."""
    return safe_get(split, "attributes", "gloss-br")


def is_sentence_object(obj: Any) -> bool:
    """
    Heuristic for recognizing a sentence object in this JSON.
    We expect:
      - text
      - translations (often)
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

    We keep a lightweight inherited metadata dictionary with container UIDs and labels
    when possible, so later you can see where a sentence came from.
    """
    if inherited_meta is None:
        inherited_meta = {}

    out: List[Dict[str, Any]] = []

    if isinstance(obj, dict):
        local_meta = dict(inherited_meta)

        # Keep useful container metadata if present
        for key in ("uid", "id", "title", "name", "label", "content", "contents"):
            if key in obj and key not in local_meta:
                local_meta[key] = obj[key]

        if is_sentence_object(obj):
            record = {
                "path": path,
                "container_meta": local_meta,
                "sentence": obj,
            }
            out.append(record)

        for key, value in obj.items():
            child_path = f"{path}.{key}"
            out.extend(walk_collect_sentences(value, child_path, local_meta))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            out.extend(walk_collect_sentences(item, child_path, inherited_meta))

    return out


def normalize_conllu_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize minimal proto-CoNLL-U entry."""
    return {
        "id": entry.get("id"),
        "form": entry.get("form"),
        "misc": entry.get("misc"),
    }


def normalize_split(split: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one split object."""
    return {
        "v": split.get("v"),
        "t": split.get("t"),
        "gloss_br": split_gloss(split),
        "fn": split.get("fn"),
        "idx": split.get("idx"),
    }


def normalize_token(token: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize token object into a stable inspection schema."""
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        splits = []

    return {
        "p": token.get("p"),
        "v": token.get("v"),
        "t": token.get("t"),
        "l": token.get("l"),
        "gloss_br": token_gloss(token),
        "split": token.get("split"),
        "splits": [normalize_split(s) for s in splits if isinstance(s, dict)],
    }


def normalize_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize chunk object."""
    return {
        "i": chunk.get("i"),
        "f": chunk.get("f"),
        "t": chunk.get("t"),
        "l": chunk.get("l"),
    }


def normalize_sentence(record: Dict[str, Any], ordinal: int) -> Dict[str, Any]:
    """Produce a normalized sentence record suitable for inspection or JSONL output."""
    sentence = record["sentence"]
    struct = sentence.get("struct", {}) if isinstance(sentence.get("struct"), dict) else {}

    tokens = struct.get("tokens", [])
    chunks = struct.get("chunks", [])
    conllu = struct.get("conllu", [])

    if not isinstance(tokens, list):
        tokens = []
    if not isinstance(chunks, list):
        chunks = []
    if not isinstance(conllu, list):
        conllu = []

    return {
        "ordinal": ordinal,
        "path": record["path"],
        "container_meta": record.get("container_meta", {}),
        "uid": sentence.get("uid"),
        "text": sentence.get("text"),
        "translations": sentence.get("translations", {}),
        "visible": struct.get("visible"),
        "tokens": [normalize_token(t) for t in tokens if isinstance(t, dict)],
        "chunks": [normalize_chunk(c) for c in chunks if isinstance(c, dict)],
        "conllu": [normalize_conllu_entry(c) for c in conllu if isinstance(c, dict)],
    }


def print_header(title: str) -> None:
    print("=" * 80)
    print(title)
    print("=" * 80)


def render_container_meta_value(key: str, value: Any, mode: str) -> str:
    """Render container_meta values for human-readable text output."""
    if key in {"content", "contents"}:
        if mode == "ellipsis":
            return "..."
        if mode == "none":
            return "<omitted>"

    if isinstance(value, (dict, list)):
        return compact_json(value)
    return str(value)


def print_sentence_summary(s: Dict[str, Any], container_meta_mode: str = "ellipsis") -> None:
    """Pretty-print one normalized sentence record."""
    print_header(f"Sentence {s['ordinal']}")

    print(f"path: {s['path']}")
    print(f"uid: {s.get('uid')}")
    print(f"text: {s.get('text')}")
    print(f"visible: {s.get('visible')}")

    container_meta = s.get("container_meta", {})
    if container_meta:
        print("container_meta:")
        for k in sorted(container_meta):
            value = render_container_meta_value(k, container_meta[k], container_meta_mode)
            print(f"  {k}: {value}")

    translations = s.get("translations") or {}
    print("translations:")
    if translations:
        for lang, value in translations.items():
            print(f"  {lang}: {value}")
    else:
        print("  <none>")

    print("\nproto-conllu:")
    conllu = s.get("conllu", [])
    if conllu:
        for row in conllu:
            print(
                "  id={id!s:<4} form={form!r:<20} misc={misc}".format(
                    id=row.get("id"),
                    form=row.get("form"),
                    misc=row.get("misc"),
                )
            )
    else:
        print("  <none>")

    print("\nchunks:")
    chunks = s.get("chunks", [])
    if chunks:
        for ch in chunks:
            print(
                "  span={i}-{f} type={t} level={l}".format(
                    i=ch.get("i"),
                    f=ch.get("f"),
                    t=ch.get("t"),
                    l=ch.get("l"),
                )
            )
    else:
        print("  <none>")

    print("\ntokens:")
    tokens = s.get("tokens", [])
    if not tokens:
        print("  <none>")
        return

    for tok in tokens:
        print(
            "  p={p!s:<3} v={v!r:<18} t={t!r:<12} l={l!s:<3} gloss-br={g!r}".format(
                p=tok.get("p"),
                v=tok.get("v"),
                t=tok.get("t"),
                l=tok.get("l"),
                g=tok.get("gloss_br"),
            )
        )

        split_obj = tok.get("split")
        if split_obj is not None:
            print(f"      split: {compact_json(split_obj)}")

        splits = tok.get("splits", [])
        if splits:
            print("      splits:")
            for i, s in enumerate(splits, start=1):
                print(
                    "        [{i}] v={v!r:<12} t={t!r:<10} gloss-br={g!r} fn={fn!r} idx={idx!r}".format(
                        i=i,
                        v=s.get("v"),
                        t=s.get("t"),
                        g=s.get("gloss_br"),
                        fn=s.get("fn"),
                        idx=s.get("idx"),
                    )
                )

    print("\nconllu/token count check:")
    print(f"  tokens={len(tokens)}  proto-conllu={len(conllu)}")

    # Optional lightweight alignment by position/order
    if tokens and conllu:
        print("  order alignment:")
        n = min(len(tokens), len(conllu))
        for i in range(n):
            tok = tokens[i]
            row = conllu[i]
            print(
                "    token[{i}] p={p!s:<3} v={tv!r:<18}  <->  conllu[{i}] id={cid!r:<4} form={cf!r}".format(
                    i=i + 1,
                    p=tok.get("p"),
                    tv=tok.get("v"),
                    cid=row.get("id"),
                    cf=row.get("form"),
                )
            )
        if len(tokens) != len(conllu):
            print("    WARNING: token count and proto-conllu count differ.")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def write_jsonl(path: Path, normalized: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for rec in normalized:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Inspect sentence structure in one or more Kadiwéu Tycho Brahe "
            "JSON source documents."
        ),
        epilog="""Examples:
  python3 inspect_kadiweu_json.py data/ped-gramm.json --summary-only
  python3 inspect_kadiweu_json.py data/hil-data.json --limit 10
  python3 inspect_kadiweu_json.py data/van-data.json --jsonl-out data/van-data.jsonl
  python3 inspect_kadiweu_json.py data/ped-gramm.json data/hil-data.json data/van-data.json \\
      --source-id ped-gramm --source-id hil-data --source-id van-data \\
      --jsonl-out data/kadiweu-all.jsonl
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "json_file",
        nargs="+",
        help=(
            "Input Tycho Brahe JSON file(s), e.g. data/ped-gramm.json, "
            "data/hil-data.json, or data/van-data.json"
        ),
    )
    p.add_argument(
        "--source-id",
        action="append",
        default=None,
        help=(
            "Stable source identifier for an input JSON file, e.g. ped-gramm, "
            "hil-data, or van-data. May be supplied once per input file. "
            "If omitted, the input file stem is used."
        ),
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Print only the first N matching sentences",
    )
    p.add_argument(
        "--uid",
        default=None,
        help="Inspect only the sentence with this UID",
    )
    p.add_argument(
        "--text-contains",
        default=None,
        help="Inspect only sentences whose text contains this substring",
    )
    p.add_argument(
        "--jsonl-out",
        default=None,
        help="Write normalized sentence records to a JSONL file",
    )
    p.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print sentence list (ordinal, uid, text), not full details",
    )
    p.add_argument(
        "--container-meta-mode",
        choices=("ellipsis", "full", "none"),
        default="ellipsis",
        help=(
            "How to print container_meta content/contents in the text output: "
            "ellipsis (default) prints '...', full prints the full value, "
            "and none prints '<omitted>'."
        ),
    )
    return p


def attach_source_metadata(
    records: List[Dict[str, Any]],
    source_id: str,
    source_file: Path,
) -> List[Dict[str, Any]]:
    """Attach stable source metadata to raw sentence records."""
    source_file_str = str(source_file)

    for record in records:
        record["source_id"] = source_id
        record["source_file"] = source_file_str

    return records


def main() -> int:
    args = build_argparser().parse_args()

    json_paths = [Path(path) for path in args.json_file]

    if args.source_id is not None and len(args.source_id) != len(json_paths):
        print(
            "ERROR: --source-id must be supplied exactly once per input JSON file "
            f"({len(args.source_id)} source-id value(s) for "
            f"{len(json_paths)} file(s)).",
            file=sys.stderr,
        )
        return 1

    source_ids = args.source_id or [path.stem for path in json_paths]

    raw_sentences: List[Dict[str, Any]] = []

    for json_path, source_id in zip(json_paths, source_ids):
        if not json_path.is_file():
            print(f"ERROR: file not found: {json_path}", file=sys.stderr)
            return 1

        data = load_json(json_path)
        records = walk_collect_sentences(data)
        records = attach_source_metadata(records, source_id, json_path)
        raw_sentences.extend(records)

    if not raw_sentences:
        print("No sentence-like objects found.", file=sys.stderr)
        return 2

    raw_sentences = filter_sentences(
        raw_sentences,
        uid=args.uid,
        text_contains=args.text_contains,
    )

    if args.limit is not None:
        raw_sentences = raw_sentences[: args.limit]

    normalized = []

    for i, rec in enumerate(raw_sentences, start=1):
        norm = normalize_sentence(rec, ordinal=i)
        norm["source_id"] = rec.get("source_id")
        norm["source_file"] = rec.get("source_file")
        normalized.append(norm)

    print(f"Found {len(normalized)} matching sentence(s).")

    if args.summary_only:
        for s in normalized:
            print(
                "{ord:>4}  source={source:<10} uid={uid}  text={text}".format(
                    ord=s["ordinal"],
                    source=s.get("source_id") or "",
                    uid=s.get("uid"),
                    text=s.get("text"),
                )
            )
    else:
        for s in normalized:
            print_sentence_summary(s, container_meta_mode=args.container_meta_mode)
            print()

    if args.jsonl_out:
        write_jsonl(Path(args.jsonl_out), normalized)
        print(f"Wrote JSONL to: {args.jsonl_out}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())