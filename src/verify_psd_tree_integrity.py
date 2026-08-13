#!/usr/bin/env python3
"""Verify that enriched PSD files preserve their source TBP trees.

Metadata comments, (ID ...) subtrees, and formatting whitespace are ignored.
Everything else—including tree order, labels, terminals, capitalization,
G versus ǥ, traces, and empty categories—is compared strictly.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union


Tree = Union[str, List["Tree"]]


class PsdError(ValueError):
    """Raised when a PSD file is malformed or cannot be verified safely."""


@dataclass(frozen=True)
class ParsedPsd:
    path: Path
    trees: Tuple[Tree, ...]
    canonical_trees: Tuple[str, ...]
    sha256: str


def remove_comments(text: str, path: Path) -> str:
    """Remove C-style comments, rejecting nesting and unterminated comments."""
    output: List[str] = []
    index = 0
    while index < len(text):
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end == -1:
                raise PsdError(f"unterminated comment in {path}")
            if text.find("/*", index + 2, end) != -1:
                raise PsdError(f"nested comment in {path}")
            output.append(" ")
            index = end + 2
        elif text.startswith("*/", index):
            raise PsdError(f"unmatched comment terminator in {path}")
        else:
            output.append(text[index])
            index += 1
    return "".join(output)


def tokenize(text: str, path: Path) -> List[str]:
    tokens: List[str] = []
    atom: List[str] = []

    def finish_atom() -> None:
        if atom:
            tokens.append("".join(atom))
            atom.clear()

    for character in remove_comments(text, path):
        if character in "()":
            finish_atom()
            tokens.append(character)
        elif character.isspace():
            finish_atom()
        else:
            atom.append(character)
    finish_atom()
    return tokens


def parse_psd(path: Path) -> Tuple[Tree, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise PsdError(f"cannot read {path}: {error}") from error

    tokens = tokenize(text, path)
    position = 0

    def parse_tree() -> Tree:
        nonlocal position
        if position >= len(tokens) or tokens[position] != "(":
            found = "end of file" if position >= len(tokens) else repr(tokens[position])
            raise PsdError(f"expected '(' in {path}; found {found}")
        position += 1
        children: List[Tree] = []
        while position < len(tokens) and tokens[position] != ")":
            if tokens[position] == "(":
                children.append(parse_tree())
            else:
                children.append(tokens[position])
                position += 1
        if position >= len(tokens):
            raise PsdError(f"unclosed parenthesis in {path}")
        position += 1
        return children

    trees: List[Tree] = []
    while position < len(tokens):
        if tokens[position] != "(":
            raise PsdError(
                f"unexpected top-level token {tokens[position]!r} in {path}"
            )
        trees.append(parse_tree())
    if not trees:
        raise PsdError(f"no trees found in {path}")
    return tuple(trees)


def remove_id_subtrees(tree: Tree) -> Optional[Tree]:
    """Return a copy without subtrees whose first child is the atom ID."""
    if isinstance(tree, str):
        return tree
    if tree and tree[0] == "ID":
        return None
    result: List[Tree] = []
    for child in tree:
        retained = remove_id_subtrees(child)
        if retained is not None:
            result.append(retained)
    return result


def canonicalize(tree: Tree) -> str:
    if isinstance(tree, str):
        return tree
    return "(" + " ".join(canonicalize(child) for child in tree) + ")"


def load(path: Path) -> ParsedPsd:
    trees = tuple(remove_id_subtrees(tree) for tree in parse_psd(path))
    if any(tree is None for tree in trees):
        raise PsdError(f"top-level ID tree found in {path}")
    retained = tuple(tree for tree in trees if tree is not None)
    canonical = tuple(canonicalize(tree) for tree in retained)
    digest = hashlib.sha256("\n".join(canonical).encode("utf-8")).hexdigest()
    return ParsedPsd(path, retained, canonical, digest)


def shortened(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def compare(source_path: Path, enriched_path: Path) -> bool:
    source = load(source_path)
    enriched = load(enriched_path)

    print(f"Source:    {source.path}")
    print(f"Enriched:  {enriched.path}")
    print(f"Trees:     {len(source.trees)} / {len(enriched.trees)}")

    if len(source.trees) != len(enriched.trees):
        print("Result:    DIFFERENT (tree-count mismatch)")
        print(f"Source SHA-256:    {source.sha256}")
        print(f"Enriched SHA-256:  {enriched.sha256}")
        return False

    for index, (source_tree, enriched_tree) in enumerate(
        zip(source.canonical_trees, enriched.canonical_trees), start=1
    ):
        if source_tree != enriched_tree:
            print(f"Result:    DIFFERENT (first mismatch at tree {index})")
            print(f"Source tree:    {shortened(source_tree)}")
            print(f"Enriched tree:  {shortened(enriched_tree)}")
            print(f"Source SHA-256:    {source.sha256}")
            print(f"Enriched SHA-256:  {enriched.sha256}")
            return False

    print("Result:    IDENTICAL after removing comments, IDs, and formatting")
    print(f"SHA-256:   {source.sha256}")
    return True


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare source TBP PSD files with enriched stable-name PSD files. "
            "Supply paths in SOURCE ENRICHED pairs."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        metavar="PSD",
        help="SOURCE ENRICHED pairs; multiple pairs may be supplied",
    )
    arguments = parser.parse_args()
    if len(arguments.paths) % 2:
        parser.error("paths must be supplied in SOURCE ENRICHED pairs")
    return arguments


def main() -> int:
    arguments = parse_arguments()
    pairs = list(zip(arguments.paths[::2], arguments.paths[1::2]))
    all_identical = True
    try:
        for pair_number, (source, enriched) in enumerate(pairs, start=1):
            if pair_number > 1:
                print()
            if not compare(source, enriched):
                all_identical = False
    except PsdError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print()
    if all_identical:
        print(f"PASS: all {len(pairs)} PSD pair(s) preserve the source trees")
        return 0
    print("FAIL: one or more PSD pairs differ", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
