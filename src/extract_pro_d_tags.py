#!/usr/bin/env python3
"""Inventory PRO forms and check whether the same forms are also tagged D.

The script reads CorpusSearch PSD files whose sentence records consist of a
metadata comment followed by a tree. It emits one TSV row for each combination
of normalized form, corpus tag (PRO or D), and provenance (DONE or REVIEW).
Only forms attested at least once with the tag PRO are included.
"""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Sequence, Tuple


COMMENT_RE = re.compile(r"/\*(.*?)\*/", re.DOTALL)
FIELD_RE = re.compile(r"^\s*([A-Za-z_]+)\s*=\s*(.*?)\s*$", re.MULTILINE)
LEAF_RE = re.compile(r"\(([^\s()]+)\s+([^()\s]+)\)")


def normalize_form(form: str) -> str:
    """Remove CorpusSearch token-boundary markers and fold case."""
    return form.replace("@", "").casefold()


def provenance_from_path(path: Path) -> str:
    name = path.name.lower()
    if ".review." in name:
        return "REVIEW"
    if ".done." in name:
        return "DONE"
    return ""


def iter_records(path: Path) -> Iterable[Tuple[Dict[str, str], str]]:
    text = path.read_text(encoding="utf-8")
    comments = list(COMMENT_RE.finditer(text))
    for index, match in enumerate(comments):
        tree_end = comments[index + 1].start() if index + 1 < len(comments) else len(text)
        metadata = dict(FIELD_RE.findall(match.group(1)))
        yield metadata, text[match.end():tree_end]


def collect(paths: Sequence[Path]) -> Tuple[
    DefaultDict[str, List[Tuple[str, str, str, str]]],
    DefaultDict[Tuple[str, str, str], List[Tuple[str, str]]],
]:
    pro_forms: DefaultDict[str, List[Tuple[str, str, str, str]]] = defaultdict(list)
    occurrences: DefaultDict[Tuple[str, str, str], List[Tuple[str, str]]] = defaultdict(list)

    for path in paths:
        file_provenance = provenance_from_path(path)
        for metadata, tree in iter_records(path):
            provenance = metadata.get("status", file_provenance).upper()
            sentence_id_match = re.search(r"\(ID\s+([^()\s]+)\)", tree)
            sentence_id = sentence_id_match.group(1) if sentence_id_match else ""
            for tag, surface in LEAF_RE.findall(tree):
                if tag not in {"PRO", "D"}:
                    continue
                normalized = normalize_form(surface)
                occurrences[(normalized, tag, provenance)].append((surface, sentence_id))
                if tag == "PRO":
                    pro_forms[normalized].append((surface, sentence_id, provenance, path.name))

    return pro_forms, occurrences


def write_table(paths: Sequence[Path], output: Path) -> None:
    pro_forms, occurrences = collect(paths)
    fieldnames = [
        "normalized_form",
        "surface_forms",
        "corpus_tag",
        "provenance",
        "token_count",
        "sentence_ids",
        "also_tagged_D",
        "D_token_count_total",
        "D_sentence_ids",
    ]

    rows = []
    for normalized in sorted(pro_forms):
        d_items = [
            item
            for (form, tag, _provenance), values in occurrences.items()
            if form == normalized and tag == "D"
            for item in values
        ]
        d_ids = sorted({sentence_id for _, sentence_id in d_items if sentence_id})
        relevant_keys = sorted(
            key for key in occurrences
            if key[0] == normalized and key[1] in {"PRO", "D"}
        )
        for _, tag, provenance in relevant_keys:
            items = occurrences[(normalized, tag, provenance)]
            rows.append({
                "normalized_form": normalized,
                "surface_forms": "; ".join(sorted({surface for surface, _ in items})),
                "corpus_tag": tag,
                "provenance": provenance,
                "token_count": len(items),
                "sentence_ids": "; ".join(sorted({sid for _, sid in items if sid})),
                "also_tagged_D": "yes" if d_items else "no",
                "D_token_count_total": len(d_items),
                "D_sentence_ids": "; ".join(d_ids),
            })

    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("psd_files", nargs="+", type=Path, help="CorpusSearch PSD files")
    parser.add_argument("-o", "--output", required=True, type=Path, help="Output TSV path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_table(args.psd_files, args.output)


if __name__ == "__main__":
    main()
