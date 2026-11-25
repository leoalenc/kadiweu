#!/usr/bin/env python3
"""Restore attested Kadiwéu trace notation in CFG-generated PSD parses.

The input is a CorpusSearch-style PSD file produced by
``parse_kadiweu_cfg.py --output``. The script restores the empty-category
patterns found in DONE trees:

* subject gaps in CP-REL clauses introduced by the relative pronoun *ane*;
* empty NP-GEN possessor positions linked to the sentence's initial NP.

The artificial CFG ROOT node is removed. Input metadata and sentence IDs are
preserved, and each parse remains a separate PSD record.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from nltk.tree import Tree

from induce_kadiweu_cfg import iter_records


INDEX_SUFFIX_RE = re.compile(r"^(?P<label>.+)-(?P<index>\d+)$")


def descendants(node: Tree, label: str | None = None):
    """Yield constituent nodes in preorder, optionally filtering by label."""
    for subtree in node.subtrees():
        if label is None or subtree.label() == label:
            yield subtree


def is_overt_np(node) -> bool:
    return (
        isinstance(node, Tree)
        and node.label().startswith("NP")
        and node.label() not in {"NP-TRACE", "NP-GEN"}
        and any(isinstance(leaf, str) and not leaf.startswith("*")
                for leaf in node.leaves())
    )


def set_coindex(node: Tree, index: int) -> None:
    """Add a numeric coindex, rejecting conflicting existing indices."""
    match = INDEX_SUFFIX_RE.fullmatch(node.label())
    if match:
        if int(match.group("index")) != index:
            raise ValueError(
                f"{node.label()} already has a different coindex than {index}"
            )
        return
    node.set_label(f"{node.label()}-{index}")


def empty_projection_nodes(tree: Tree, label: str) -> list[Tree]:
    return [node for node in descendants(tree, label) if len(node) == 0]


def matrix_ip(tree: Tree) -> Tree | None:
    """Return the first IP-MAT node, below ROOT if present."""
    if tree.label() == "ROOT" and len(tree) == 1 and isinstance(tree[0], Tree):
        tree = tree[0]
    if tree.label() == "IP-MAT":
        return tree
    return next(descendants(tree, "IP-MAT"), None)


def first_matrix_np(matrix: Tree) -> Tree | None:
    """Find the first overt NP daughter of IP-MAT, as in the DONE patterns."""
    return next((child for child in matrix if is_overt_np(child)), None)


def relative_ane_gaps(tree: Tree) -> list[tuple[Tree, Tree]]:
    """Return (WNP, empty NP-TRACE) pairs in attested ane relatives."""
    pairs = []
    for cp in descendants(tree, "CP-REL"):
        wnps = list(descendants(cp, "WNP"))
        ips = list(descendants(cp, "IP-SUB"))
        if len(wnps) != 1 or len(ips) != 1:
            continue
        wpros = [node for node in descendants(wnps[0], "WPRO")
                 if len(node) == 1 and isinstance(node[0], str)]
        if len(wpros) != 1:
            continue
        pronoun = wpros[0][0].casefold().rstrip("@")
        if pronoun != "ane":
            continue
        # In DONE trees the subject gap is an immediate, empty IP-SUB daughter.
        gaps = [child for child in ips[0]
                if isinstance(child, Tree)
                and child.label() == "NP-TRACE"
                and len(child) == 0]
        if len(gaps) == 1:
            pairs.append((wnps[0], gaps[0]))
    return pairs


def restore_tree(tree: Tree) -> tuple[Tree, int, int, list[str]]:
    """Restore traces and coindices; return tree, counts, and diagnostics."""
    if tree.label() == "ROOT" and len(tree) == 1 and isinstance(tree[0], Tree):
        tree = tree[0]

    warnings = []
    genitive_gaps = empty_projection_nodes(tree, "NP-GEN")
    relative_pairs = relative_ane_gaps(tree)
    restored_genitives = 0
    restored_relatives = 0

    if genitive_gaps:
        matrix = matrix_ip(tree)
        antecedent = first_matrix_np(matrix) if matrix is not None else None
        if antecedent is None:
            warnings.append("NP-GEN gap has no overt initial NP in IP-MAT")
        elif len(genitive_gaps) > 1:
            warnings.append(
                f"found {len(genitive_gaps)} empty NP-GEN nodes; DONE data has at most one"
            )
        else:
            try:
                set_coindex(antecedent, 1)
                genitive_gaps[0].append(Tree("-NONE-", ["*T*-1"]))
                restored_genitives = 1
            except ValueError as exc:
                warnings.append(str(exc))

    # DONE examples with both movements use index 1 for the moved possessor
    # and index 2 for the relative pronoun; relative-only examples use 1.
    next_index = 2 if restored_genitives else 1
    for wnp, gap in relative_pairs:
        try:
            set_coindex(wnp, next_index)
            gap.append(Tree("-NONE-", [f"*T*-{next_index}"]))
            restored_relatives += 1
            next_index += 1
        except ValueError as exc:
            warnings.append(str(exc))

    return tree, restored_relatives, restored_genitives, warnings


def format_tree(tree: Tree, indent: int = 2) -> str:
    """Render an NLTK tree in the project's indented PSD style."""
    margin = " " * indent
    if len(tree) == 0:
        return f"{margin}({tree.label()})"
    if len(tree) == 1 and isinstance(tree[0], str):
        return f"{margin}({tree.label()} {tree[0]})"

    lines = [f"{margin}({tree.label()}"]
    for child in tree:
        if isinstance(child, Tree):
            lines.append(format_tree(child, indent + 2))
        else:
            lines.append(f"{' ' * (indent + 2)}{child}")
    lines.append(f"{margin})")
    return "\n".join(lines)


def metadata_comment(
    metadata: dict[str, str], parse_number: int
) -> tuple[str, str | None]:
    fields = dict(metadata)
    corpus_id = fields.pop("corpus_id", None)
    fields.setdefault("parse_number", str(parse_number))
    lines = []
    for key, value in fields.items():
        normalized = " ".join(str(value).split()).replace("*/", "* /")
        lines.append(f"{key} = {normalized}")
    return "/*\n" + "\n".join(lines) + "\n*/", corpus_id


def format_record(metadata: dict[str, str], tree: Tree, parse_number: int) -> str:
    comment, corpus_id = metadata_comment(metadata, parse_number)
    if not corpus_id:
        raise ValueError("PSD record is missing its (ID ...) value")
    return "\n".join((
        comment,
        "(",
        format_tree(tree),
        f"  (ID {corpus_id})",
        ")",
    ))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Restore the attested relative-pronoun and possessor traces in "
            "CFG-generated CorpusSearch PSD parses."
        )
    )
    parser.add_argument("-i", "--input", required=True, type=Path,
                        help="PSD file generated by parse_kadiweu_cfg.py")
    parser.add_argument("-o", "--output", required=True, type=Path,
                        help="new PSD file with restored traces")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if not args.input.is_file():
        print(f"error: input PSD not found: {args.input}", file=sys.stderr)
        return 2
    if args.input.resolve() == args.output.resolve():
        print("error: --output must be a different file from --input", file=sys.stderr)
        return 2

    try:
        records = list(iter_records(args.input))
        output_records = []
        total_relative = 0
        total_genitive = 0
        warnings = []
        for record_number, (metadata, tree, _wrapped) in enumerate(records, start=1):
            tree, relative_count, genitive_count, record_warnings = restore_tree(tree)
            total_relative += relative_count
            total_genitive += genitive_count
            if record_warnings:
                identifier = metadata.get("corpus_id", f"record {record_number}")
                warnings.extend(f"{identifier}: {message}" for message in record_warnings)
            parse_number = int(metadata.get("parse_number", record_number))
            output_records.append(format_record(metadata, tree, parse_number))
        args.output.write_text(
            "\n\n".join(output_records) + ("\n" if output_records else ""),
            encoding="utf-8",
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"Wrote {len(output_records)} PSD records to {args.output}; restored "
        f"{total_relative} relative-clause trace(s) and "
        f"{total_genitive} NP-GEN possessor trace(s)."
    )
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
