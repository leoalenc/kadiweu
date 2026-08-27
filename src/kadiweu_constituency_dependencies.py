#!/usr/bin/env python3
"""Infer certain UD dependencies from Kadiwéu constituency trees.

This module is intentionally partial.  A rule emits an assignment only when
the constituency configuration determines both the dependency head and the
relation.  Unresolved terminals are left for later rules or for the existing
JSON-to-CoNLL-U converter.

First implemented regularity
----------------------------
Possessive NPs license both orders::

    NP -> (D) N$ NP
    NP -> (D) NP N$

The immediate N$ is the possessum and the head of the outer NP.  The lexical
head of the immediate NP daughter is the possessor and depends on the
possessum as ``nmod:poss``.  An immediate D, when present, depends on the same
head as ``det``.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence, TextIO

from kadiweu_constituency import (
    ConstituencyTree,
    ConstituentNode,
    PsdRecord,
    TokenNode,
    TreeNode,
    iter_psd_records,
)


POSSESSOR_RULE = "possessive-np-possessor"
DETERMINER_RULE = "possessive-np-determiner"


@dataclass(frozen=True, slots=True)
class DependencyAssignment:
    """One certain dependency expressed in source-token positions."""

    dependent_position: int
    head_position: int
    deprel: str
    rule: str


class DependencyConflictError(ValueError):
    """Raised when certain rules disagree about a terminal's dependency."""


def is_np(node: TreeNode) -> bool:
    """Return whether *node* is an overt NP projection.

    Functional NP labels are accepted, but trace projections are not possible
    possessors for the first rule.
    """

    return (
        isinstance(node, ConstituentNode)
        and (node.label == "NP" or node.label.startswith("NP-"))
        and node.label != "NP-TRACE"
    )


def lexical_head(node: TreeNode) -> TokenNode | None:
    """Return a conservatively identifiable lexical head.

    This is deliberately not a general Kadiwéu head-finding algorithm.  It
    covers only the configurations needed by the first dependency rule:

    * a terminal is its own head;
    * a possessive NP's unique immediate N$ is its head;
    * in a simple NP, a unique immediate N/N$/NPR/PRO is its head;
    * D is the head when it is the sole terminal realization of an NP;
    * a unary phrasal projection inherits its daughter's head.

    Ambiguity returns ``None`` rather than selecting by linear position.
    """

    if isinstance(node, TokenNode):
        return None if node.empty_category else node
    if not is_np(node):
        return None

    overt_tokens = [
        child
        for child in node.children
        if isinstance(child, TokenNode) and not child.empty_category
    ]
    np_children = [child for child in node.children if is_np(child)]
    possessums = [token for token in overt_tokens if token.tag == "N$"]

    # The two licensed possessive orders share this order-independent head.
    if len(possessums) == 1 and len(np_children) == 1:
        permitted_ids = {id(possessums[0]), id(np_children[0])}
        permitted_ids.update(id(token) for token in overt_tokens if token.tag == "D")
        if all(
            id(child) in permitted_ids
            for child in node.children
        ):
            return possessums[0]

    lexical = [
        token for token in overt_tokens
        if token.tag in {"N", "N$", "NPR", "PRO"}
    ]
    if len(lexical) == 1 and all(
        child is lexical[0]
        or (isinstance(child, TokenNode) and child.tag == "D")
        for child in node.children
    ):
        return lexical[0]

    if len(overt_tokens) == 1 and overt_tokens[0].tag in {"D", "PRO"}:
        return overt_tokens[0]

    if not overt_tokens and len(np_children) == 1 and len(node.children) == 1:
        return lexical_head(np_children[0])
    return None


def possessive_np_assignments(node: ConstituentNode) -> list[DependencyAssignment]:
    """Infer dependencies for one unambiguous possessive NP.

    Daughter order is immaterial.  The rule rejects additional daughters,
    multiple N$ heads, multiple NP daughters, and possessors whose lexical
    head cannot be established conservatively.
    """

    if not is_np(node):
        return []

    possessums = [
        child
        for child in node.children
        if isinstance(child, TokenNode)
        and not child.empty_category
        and child.tag == "N$"
    ]
    possessors = [child for child in node.children if is_np(child)]
    determiners = [
        child
        for child in node.children
        if isinstance(child, TokenNode)
        and not child.empty_category
        and child.tag == "D"
    ]

    if len(possessums) != 1 or len(possessors) != 1 or len(determiners) > 1:
        return []

    permitted_ids = {
        id(possessums[0]),
        id(possessors[0]),
        *(id(determiner) for determiner in determiners),
    }
    if any(id(child) not in permitted_ids for child in node.children):
        return []

    possessor_head = lexical_head(possessors[0])
    if possessor_head is None:
        return []
    possessum = possessums[0]

    assignments = [
        DependencyAssignment(
            dependent_position=possessor_head.position,
            head_position=possessum.position,
            deprel="nmod:poss",
            rule=POSSESSOR_RULE,
        )
    ]
    assignments.extend(
        DependencyAssignment(
            dependent_position=determiner.position,
            head_position=possessum.position,
            deprel="det",
            rule=DETERMINER_RULE,
        )
        for determiner in determiners
    )
    return assignments


def _add_assignment(
    assignments: dict[int, DependencyAssignment],
    assignment: DependencyAssignment,
) -> None:
    previous = assignments.get(assignment.dependent_position)
    if previous is None:
        assignments[assignment.dependent_position] = assignment
        return
    if (
        previous.head_position != assignment.head_position
        or previous.deprel != assignment.deprel
    ):
        raise DependencyConflictError(
            f"token {assignment.dependent_position}: {previous.rule} proposed "
            f"head={previous.head_position}, deprel={previous.deprel}; "
            f"{assignment.rule} proposed head={assignment.head_position}, "
            f"deprel={assignment.deprel}"
        )


def infer_dependencies(tree: ConstituencyTree) -> list[DependencyAssignment]:
    """Return all certain assignments currently licensed for *tree*."""

    by_dependent: dict[int, DependencyAssignment] = {}
    for node in tree.walk():
        if not isinstance(node, ConstituentNode):
            continue
        for assignment in possessive_np_assignments(node):
            _add_assignment(by_dependent, assignment)
    return [by_dependent[position] for position in sorted(by_dependent)]


def iter_psd_assignments(
    records: Iterable[PsdRecord],
) -> Iterator[tuple[PsdRecord, DependencyAssignment]]:
    """Yield record/assignment pairs for an iterable of PSD records."""

    for record in records:
        for assignment in infer_dependencies(record.tree):
            yield record, assignment


def write_tsv(records: Iterable[PsdRecord], stream: TextIO) -> None:
    """Write an auditable table of certain assignments."""

    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ["sent_id", "dependent_position", "dependent", "head_position", "head", "deprel", "rule"]
    )
    for record, assignment in iter_psd_assignments(records):
        by_position = {token.position: token for token in record.tree.tokens}
        writer.writerow(
            [
                record.corpussearch_id or "",
                assignment.dependent_position,
                by_position[assignment.dependent_position].form,
                assignment.head_position,
                by_position[assignment.head_position].form,
                assignment.deprel,
                assignment.rule,
            ]
        )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report certain UD dependencies inferred from Kadiwéu PSD trees."
    )
    parser.add_argument("psd", type=Path, help="CorpusSearch/Penn PSD input")
    parser.add_argument("-o", "--output", type=Path, help="TSV output; default: stdout")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    records = iter_psd_records(args.psd)
    if args.output is None:
        write_tsv(records, sys.stdout)
    else:
        with args.output.open("w", encoding="utf-8", newline="") as stream:
            write_tsv(records, stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
