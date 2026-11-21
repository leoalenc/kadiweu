#!/usr/bin/env python3
"""Induce a POS-terminal CFG from CorpusSearch-format Kadiwéu trees.

Each input path is a CorpusSearch PSD file. Only records marked ``DONE`` are
used. Overt preterminals are replaced by their POS labels as terminal symbols.
Coindexed category suffixes (for example, ``NP-1``) are removed from CFG
nonterminals. ``-NONE-`` trace subtrees are removed, leaving an epsilon rule
at any phrase node that consequently has no overt children. A TSV sidecar
preserves the source indices and tree positions for later trace postprocessing.

Requires NLTK (``python -m pip install nltk``).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator, Tuple

from nltk.tree import Tree


COINDEX_RE = re.compile(r"^(?P<label>.+)-(?P<index>\d+)$")
TRACE_RE = re.compile(r"^\*[^*]+\*-(?P<index>\d+)$")

# An RHS symbol is (kind, value), where kind is "T" for a POS terminal or
# "N" for a nonterminal. Keeping the distinction explicit matters because
# the same spelling can have different roles in a grammar.
Symbol = Tuple[str, str]
ProductionKey = Tuple[str, Tuple[Symbol, ...]]


def parse_metadata(block: str) -> dict[str, str]:
    return {
        key.strip(): value.strip()
        for key, value in re.findall(
            r"(?m)^\s*([\w-]+)\s*=\s*(.*?)\s*$", block
        )
    }


def extract_balanced_tree(text: str, offset: int, source: Path) -> tuple[str, int]:
    """Return the parenthesized CorpusSearch tree beginning at offset."""
    start = offset
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "(":
        raise ValueError(f"{source}: expected a tree after a metadata block")

    depth = 0
    for pos in range(start, len(text)):
        char = text[pos]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start : pos + 1], pos + 1
    raise ValueError(f"{source}: unbalanced parentheses in a tree")


def iter_records(path: Path) -> Iterator[tuple[dict[str, str], Tree, str]]:
    """Yield metadata, sentence tree, and the record's original wrapper."""
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"(?m)^\s*/\*", text))
    if not matches:
        raise ValueError(f"{path}: no CorpusSearch metadata records found")

    for match in matches:
        close = text.find("*/", match.end())
        if close < 0:
            raise ValueError(f"{path}: unterminated metadata block")
        metadata = parse_metadata(text[match.end() : close])
        wrapped_text, _ = extract_balanced_tree(text, close + 2, path)

        # CorpusSearch wraps the sentence tree and its (ID ...) node in an
        # unlabeled outer pair of parentheses. Give that wrapper a label so
        # NLTK can parse it, then select the sole non-ID child.
        body = wrapped_text[1:-1].strip()
        wrapper = Tree.fromstring(f"(CORPUSSEARCH {body})")
        sentence_trees = [
            child
            for child in wrapper
            if isinstance(child, Tree) and child.label() != "ID"
        ]
        if len(sentence_trees) != 1:
            raise ValueError(
                f"{path}: expected one sentence tree besides ID; "
                f"found {len(sentence_trees)}"
            )
        id_nodes = [
            child for child in wrapper if isinstance(child, Tree) and child.label() == "ID"
        ]
        if len(id_nodes) == 1 and len(id_nodes[0]) == 1:
            metadata["corpus_id"] = str(id_nodes[0][0])
        yield metadata, sentence_trees[0], wrapped_text


def normalized_label(label: str) -> str:
    """Remove only a final numeric coindexation suffix."""
    match = COINDEX_RE.fullmatch(label)
    return match.group("label") if match else label


def collect_productions(tree: Tree, counts: Counter[ProductionKey]) -> None:
    """Collect productions after replacing overt preterminals with POS tags."""

    def visit(node: Tree) -> Symbol | None:
        label = node.label()
        if label == "-NONE-":
            return None

        # An overt preterminal contributes its POS label as a terminal in its
        # parent's RHS; its word is deliberately absent from the grammar.
        if len(node) == 1 and isinstance(node[0], str):
            return ("T", normalized_label(label))

        rhs: list[Symbol] = []
        for child in node:
            if isinstance(child, str):
                raise ValueError(
                    f"unexpected bare leaf {child!r} under non-preterminal {label!r}"
                )
            symbol = visit(child)
            if symbol is not None:
                rhs.append(symbol)

        lhs = normalized_label(label)
        counts[(lhs, tuple(rhs))] += 1
        return ("N", lhs)

    if visit(tree) is None:
        raise ValueError("the sentence root was removed as an empty category")


def collect_trace_rows(
    path: Path, metadata: dict[str, str], tree: Tree
) -> list[dict[str, str]]:
    """Record indexed nodes and matching trace markers for later postprocessing."""
    indexed_nodes: dict[str, list[tuple[str, str]]] = {}
    trace_nodes: dict[str, list[tuple[str, str]]] = {}

    for position in tree.treepositions():
        node = tree[position]
        if isinstance(node, Tree):
            match = COINDEX_RE.fullmatch(node.label())
            if match:
                indexed_nodes.setdefault(match.group("index"), []).append(
                    (match.group("label"), ".".join(map(str, position)))
                )
        elif isinstance(node, str):
            match = TRACE_RE.fullmatch(node)
            if match:
                trace_position = ".".join(map(str, position))
                trace_nodes.setdefault(match.group("index"), []).append(
                    (node, trace_position)
                )

    rows: list[dict[str, str]] = []
    for index in sorted(set(indexed_nodes) | set(trace_nodes), key=lambda x: int(x)):
        antecedents = indexed_nodes.get(index, []) or [("", "")]
        traces = trace_nodes.get(index, []) or [("", "")]
        for category, antecedent_position in antecedents:
            for marker, trace_position in traces:
                rows.append(
                    {
                        "source_file": path.name,
                        "sentence_id": metadata.get(
                            "corpus_id", metadata.get("sentence", "")
                        ),
                        "uid": metadata.get("uid", ""),
                        "coindex": index,
                        "indexed_category": category,
                        "indexed_position": antecedent_position,
                        "trace_marker": marker,
                        "trace_position": trace_position,
                    }
                )
    return rows


def render_symbol(symbol: Symbol) -> str:
    kind, value = symbol
    if kind == "T":
        # POS terminals are quoted in NLTK CFG notation.
        return repr(value)
    return value


def write_outputs(
    cfg_path: Path,
    counts_path: Path,
    trace_path: Path,
    counts: Counter[ProductionKey],
    trace_rows: list[dict[str, str]],
    tree_count: int,
    start_symbol: str,
) -> None:
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    ordered = sorted(
        counts.items(),
        key=lambda item: (
            item[0][0],
            tuple((0 if kind == "N" else 1, value) for kind, value in item[0][1]),
        ),
    )
    with cfg_path.open("w", encoding="utf-8", newline="\n") as output:
        output.write("# POS-terminal CFG induced from DONE CorpusSearch trees\n")
        output.write(f"# Start symbol: {start_symbol}\n")
        output.write(f"# DONE trees: {tree_count}\n")
        by_lhs: dict[str, list[tuple[Symbol, ...]]] = {}
        for (lhs, rhs), _frequency in ordered:
            by_lhs.setdefault(lhs, []).append(rhs)
        for lhs, alternatives in by_lhs.items():
            rendered = [
                " ".join(render_symbol(symbol) for symbol in rhs)
                for rhs in alternatives
            ]
            output.write(f"{lhs} -> {' | '.join(rendered)}\n")

    with counts_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(("lhs", "rhs", "frequency"))
        for (lhs, rhs), frequency in ordered:
            rendered_rhs = " ".join(render_symbol(symbol) for symbol in rhs)
            writer.writerow((lhs, rendered_rhs or "<epsilon>", frequency))

    with trace_path.open("w", encoding="utf-8", newline="") as output:
        fieldnames = (
            "source_file",
            "sentence_id",
            "uid",
            "coindex",
            "indexed_category",
            "indexed_position",
            "trace_marker",
            "trace_position",
        )
        writer = csv.DictWriter(
            output, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(trace_rows)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Induce a CFG whose terminals are POS tags from one or more "
            "CorpusSearch-format treebank files. Only DONE records are used."
        )
    )
    parser.add_argument(
        "treebanks",
        nargs="+",
        type=Path,
        metavar="TREEBANK",
        help="path to a CorpusSearch PSD file; supply one or more files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("kadiweu-pos.cfg"),
        help="output CFG path (default: kadiweu-pos.cfg)",
    )
    parser.add_argument(
        "--counts",
        type=Path,
        help="rule-frequency TSV path (default: OUTPUT.counts.tsv)",
    )
    parser.add_argument(
        "--trace-map",
        type=Path,
        help="trace/coindex TSV path (default: OUTPUT.traces.tsv)",
    )
    parser.add_argument(
        "--start",
        default="ROOT",
        help="synthetic grammar start symbol (default: ROOT)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    counts: Counter[ProductionKey] = Counter()
    trace_rows: list[dict[str, str]] = []
    done_count = 0
    skipped_count = 0

    for path in args.treebanks:
        if not path.is_file():
            print(f"error: input file not found: {path}", file=sys.stderr)
            return 2
        try:
            for metadata, tree, _wrapped in iter_records(path):
                if metadata.get("status", "").upper() != "DONE":
                    skipped_count += 1
                    continue
                if tree.label() == args.start:
                    raise ValueError(
                        f"{path}: sentence {metadata.get('sentence', '?')} already "
                        f"uses the synthetic start symbol {args.start!r}"
                    )
                # Treebanks may have multiple sentence-root categories (for
                # example IP-MAT and CP-D). A synthetic start symbol makes all
                # of them available to the same parser.
                counts[(args.start, (("N", tree.label()),))] += 1
                collect_productions(tree, counts)
                trace_rows.extend(collect_trace_rows(path, metadata, tree))
                done_count += 1
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    if done_count == 0:
        print("error: no DONE trees were found", file=sys.stderr)
        return 2

    counts_path = args.counts or args.output.with_suffix(".counts.tsv")
    trace_path = args.trace_map or args.output.with_suffix(".traces.tsv")
    try:
        write_outputs(
            args.output,
            counts_path,
            trace_path,
            counts,
            trace_rows,
            done_count,
            args.start,
        )
    except OSError as exc:
        print(f"error: could not write output: {exc}", file=sys.stderr)
        return 2

    print(f"DONE trees: {done_count}; skipped non-DONE records: {skipped_count}")
    print(f"Distinct productions: {len(counts)}")
    print(f"CFG: {args.output}")
    print(f"Rule frequencies: {counts_path}")
    print(f"Trace/coindex map: {trace_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
