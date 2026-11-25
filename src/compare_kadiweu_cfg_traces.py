#!/usr/bin/env python3
"""Compare restored CFG parse trees with reference PSD trees.

Multiple actual parse records may share a sentence ID. This script compares
each with the single reference tree for that ID, ignoring a one-child
artificial ROOT wrapper and consistently renumbered coindices. Trace nodes,
trace positions, and the rest of the tree structure are preserved.

The PSD reader and coindex/trace normalizer are reused from
``run_kadiweu_parser_rules.py``.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from run_kadiweu_parser_rules import (
    RunnerError,
    parse_sexpr,
    read_records,
    trace_normalized_tree,
)

METADATA_RE = re.compile(r"(?im)^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*(.*?)\s*$")
PARSE_NUMBER_RE = re.compile(r"(?im)^\s*parse_number\s*=\s*(\d+)\s*$")


def metadata_fields(comment: str) -> dict[str, str]:
    """Read simple key=value fields from a CorpusSearch metadata comment."""
    return {key.lower(): value for key, value in METADATA_RE.findall(comment)}


def serialize_sexpr(node) -> str:
    """Serialize the nested-list representation returned by parse_sexpr."""
    if isinstance(node, list):
        return "(" + " ".join(serialize_sexpr(child) for child in node) + ")"
    return str(node)


def without_artificial_root(tree_text: str) -> str:
    """Remove ROOT only when it is a unary wrapper around the syntax tree."""
    root = parse_sexpr(tree_text)
    if not isinstance(root, list):
        return tree_text
    for index, child in enumerate(root):
        if (
            isinstance(child, list)
            and len(child) == 2
            and child[0] == "ROOT"
            and isinstance(child[1], list)
        ):
            root[index] = child[1]
    return serialize_sexpr(root)


def comparison_signature(tree_text: str) -> str:
    """Return the evaluator's trace-preserving, coindex-canonical signature."""
    return trace_normalized_tree(
        without_artificial_root(tree_text),
        collapse_empty_category_wrapper=False,
    )


def parse_number(record, fallback: int) -> str:
    match = PARSE_NUMBER_RE.search(record.comment)
    return match.group(1) if match else str(fallback)


def compare_files(parses_path: Path, reference_path: Path, report_path: Path) -> tuple[int, int, int]:
    """Write a sentence-level TSV and return (references, exact, parses)."""
    actual_records = read_records(parses_path)
    reference_records = read_records(reference_path)

    references = {}
    for record in reference_records:
        if record.sentence_id in references:
            raise RunnerError(
                f"duplicate reference ID {record.sentence_id!r} in {reference_path}"
            )
        references[record.sentence_id] = record

    actual_by_id = defaultdict(list)
    for record in actual_records:
        fallback_number = len(actual_by_id[record.sentence_id]) + 1
        actual_by_id[record.sentence_id].append(
            (parse_number(record, fallback_number), record)
        )

    fields = [
        "sentence",
        "corpussearch_id",
        "uid",
        "status",
        "parse_count",
        "exact_match_parse_numbers",
        "exact_match",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    exact_sentences = 0
    with report_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()

        for sentence_id, reference in references.items():
            ref_signature = comparison_signature(reference.tree)
            actuals = actual_by_id.get(sentence_id, [])
            matching_numbers = [
                number
                for number, record in actuals
                if comparison_signature(record.tree) == ref_signature
            ]
            exact_sentences += bool(matching_numbers)
            metadata = metadata_fields(reference.comment)
            writer.writerow({
                "sentence": metadata.get("sentence", ""),
                "corpussearch_id": sentence_id,
                "uid": metadata.get("uid", ""),
                "status": metadata.get("status", ""),
                "parse_count": len(actuals),
                "exact_match_parse_numbers": ",".join(matching_numbers),
                "exact_match": "yes" if matching_numbers else "no",
            })

    extra_ids = sorted(set(actual_by_id) - set(references))
    if extra_ids:
        print(
            "warning: parse records have IDs absent from the reference: "
            + ", ".join(extra_ids),
            file=sys.stderr,
        )
    return len(references), exact_sentences, len(actual_records)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare restored CFG PSD parses with one reference tree per "
            "sentence, allowing consistent coindex renumbering."
        )
    )
    parser.add_argument("--parses", required=True, type=Path,
                        help="PSD file containing one or more parses per sentence")
    parser.add_argument("--reference", required=True, type=Path,
                        help="reference PSD file with one tree per sentence")
    parser.add_argument("--report", required=True, type=Path,
                        help="output TSV path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    for path, label in ((args.parses, "parse"), (args.reference, "reference")):
        if not path.is_file():
            print(f"error: {label} PSD not found: {path}", file=sys.stderr)
            return 2
    if args.report.resolve() in {args.parses.resolve(), args.reference.resolve()}:
        print("error: --report must be different from the input files", file=sys.stderr)
        return 2

    try:
        references, exact_sentences, parse_count = compare_files(
            args.parses, args.reference, args.report
        )
    except (OSError, UnicodeError, RunnerError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"Compared {parse_count} parse records for {references} reference "
        f"sentences; exact structural matches (ROOT ignored, coindices "
        f"alpha-normalized): {exact_sentences}."
    )
    print(f"Per-sentence report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
