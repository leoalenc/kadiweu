#!/usr/bin/env python3
"""Infer certain UD dependencies from Kadiwéu constituency trees.

This module is intentionally partial.  A rule emits an assignment only when
the constituency configuration determines both the dependency head and the
relation.  Unresolved terminals are left for later rules or for the existing
JSON-to-CoNLL-U converter.

Implemented regularities
------------------------
Nominal projections treat ``N``, possessively inflected ``N$``, and proper
``NPR`` as members of the same head-selection class.  Immediate ``D``,
``DAPL``, and ``Q`` modifiers are licensed with the empirically attested
common-noun tags ``N`` and ``N$``::

    NP -> ... D/DAPL/Q ... N/N$ ...

Each modifier depends on the nominal head as ``det``.  When no overt noun is
present, a sole D, DAPL, or PRO represents the NP and does not license a
``det`` assignment.

Possessive NPs license both orders::

    NP -> (D) N$ NP
    NP -> (D) NP N$

The immediate N$ is the possessum and the head of the outer NP.  The lexical
head of the immediate NP daughter is the possessor and depends on the
possessum as ``nmod:poss``.

For a functional CP headed by an immediate C with an ``IP-SUB`` complement,
UD promotes the content-word head of ``IP-SUB`` and attaches C to it as
``mark``.  CP-relative structures without an immediate C are deliberately
left for a later rule.  An immediate Q modifier of CP-me attaches as ``det``
when the promoted content-word head is nominal.
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
DETERMINER_RULE = "nominal-np-determiner"
MARK_RULE = "complementizer-mark"

NP_HEAD_TAGS = frozenset({"N", "N$", "NPR"})
ELLIPTICAL_NP_HEAD_TAGS = frozenset({"D", "DAPL", "PRO"})
NOMINAL_MODIFIER_TAGS = frozenset({"D", "DAPL", "Q"})
DET_MODIFIABLE_NOUN_TAGS = frozenset({"N", "N$"})
VERBAL_HEAD_TAGS = frozenset({"VB", "VBU", "VBAPL"})


@dataclass(frozen=True)
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


def is_ip_sub(node: TreeNode) -> bool:
    """Return whether *node* is a subordinate IP projection."""

    return isinstance(node, ConstituentNode) and (
        node.label == "IP-SUB" or node.label.startswith("IP-SUB-")
    )


def lexical_head(node: TreeNode) -> TokenNode | None:
    """Return a conservatively identifiable lexical head.

    This is deliberately not a general Kadiwéu head-finding algorithm.  It
    covers only the configurations needed by the first dependency rule:

    * a terminal is its own head;
    * an NP's unique immediate N/N$/NPR is its head;
    * D, DAPL, or PRO is the head when it is the sole terminal realization
      of an NP;
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
    nominal_heads = [token for token in overt_tokens if token.tag in NP_HEAD_TAGS]

    # X-bar generalization: a unique immediately dominated noun heads NP,
    # independently of its position and of phrasal dependents/modifiers.
    if len(nominal_heads) == 1:
        return nominal_heads[0]

    if (
        len(overt_tokens) == 1
        and overt_tokens[0].tag in ELLIPTICAL_NP_HEAD_TAGS
    ):
        return overt_tokens[0]

    if not overt_tokens and len(np_children) == 1 and len(node.children) == 1:
        return lexical_head(np_children[0])
    return None


def ud_head(node: TreeNode) -> TokenNode | None:
    """Return a conservatively identifiable UD content-word head.

    Unlike ``lexical_head``, this function implements functional-head reversal
    for the currently supported IP-SUB configurations.
    """

    if isinstance(node, TokenNode):
        return None if node.empty_category else node
    if is_np(node):
        return lexical_head(node)
    if not is_ip_sub(node):
        return None

    verbal_heads = [
        child
        for child in node.children
        if isinstance(child, TokenNode)
        and not child.empty_category
        and child.tag in VERBAL_HEAD_TAGS
    ]
    if len(verbal_heads) == 1:
        return verbal_heads[0]
    if verbal_heads:
        return None

    np_heads = [
        head
        for child in node.children
        if is_np(child)
        for head in [lexical_head(child)]
        if head is not None
    ]
    if len(np_heads) == 1:
        return np_heads[0]
    return None


def nominal_determiner_assignments(
    node: ConstituentNode,
) -> list[DependencyAssignment]:
    """Attach immediate D/DAPL/Q modifiers to a common-noun NP head.

    NPR participates in NP head selection but is excluded here because the
    DONE data do not establish D as a modifier of a proper noun in Kadiwéu.
    """

    if not is_np(node):
        return []
    modifiers = [
        child
        for child in node.children
        if isinstance(child, TokenNode)
        and not child.empty_category
        and child.tag in NOMINAL_MODIFIER_TAGS
    ]
    head = lexical_head(node)
    if (
        not modifiers
        or head is None
        or head.tag not in DET_MODIFIABLE_NOUN_TAGS
    ):
        return []
    return [
        DependencyAssignment(
            dependent_position=modifier.position,
            head_position=head.position,
            deprel="det",
            rule=DETERMINER_RULE,
        )
        for modifier in modifiers
    ]


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
    modifiers = [
        child
        for child in node.children
        if isinstance(child, TokenNode)
        and not child.empty_category
        and child.tag in NOMINAL_MODIFIER_TAGS
    ]

    if len(possessums) != 1 or len(possessors) != 1:
        return []

    permitted_ids = {
        id(possessums[0]),
        id(possessors[0]),
        *(id(modifier) for modifier in modifiers),
    }
    if any(id(child) not in permitted_ids for child in node.children):
        return []

    possessor_head = lexical_head(possessors[0])
    if possessor_head is None:
        return []
    possessum = possessums[0]

    return [
        DependencyAssignment(
            dependent_position=possessor_head.position,
            head_position=possessum.position,
            deprel="nmod:poss",
            rule=POSSESSOR_RULE,
        )
    ]


def complementizer_assignments(
    node: ConstituentNode,
) -> list[DependencyAssignment]:
    """Apply UD functional-head reversal to an unambiguous C + IP-SUB CP."""

    # CP-REL is excluded: its relative element requires a separate UD
    # analysis and is not licensed as ``mark`` by this rule.
    if node.label not in {"CP-me", "CP-D"}:
        return []
    complementizers = [
        child
        for child in node.children
        if isinstance(child, TokenNode)
        and not child.empty_category
        and child.tag == "C"
    ]
    complements = [child for child in node.children if is_ip_sub(child)]
    if len(complementizers) != 1 or len(complements) != 1:
        return []
    complement_head = ud_head(complements[0])
    if complement_head is None:
        return []
    return [
        DependencyAssignment(
            dependent_position=complementizers[0].position,
            head_position=complement_head.position,
            deprel="mark",
            rule=MARK_RULE,
        )
    ]


def cp_modifier_assignments(
    node: ConstituentNode,
) -> list[DependencyAssignment]:
    """Attach an immediate CP-me Q to a promoted nominal IP-SUB head."""

    if node.label != "CP-me":
        return []
    modifiers = [
        child
        for child in node.children
        if isinstance(child, TokenNode)
        and not child.empty_category
        and child.tag == "Q"
    ]
    complements = [child for child in node.children if is_ip_sub(child)]
    if not modifiers or len(complements) != 1:
        return []
    complement_head = ud_head(complements[0])
    if (
        complement_head is None
        or complement_head.tag not in DET_MODIFIABLE_NOUN_TAGS
    ):
        return []
    return [
        DependencyAssignment(
            dependent_position=modifier.position,
            head_position=complement_head.position,
            deprel="det",
            rule=DETERMINER_RULE,
        )
        for modifier in modifiers
    ]


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
        for assignment in nominal_determiner_assignments(node):
            _add_assignment(by_dependent, assignment)
        for assignment in possessive_np_assignments(node):
            _add_assignment(by_dependent, assignment)
        for assignment in complementizer_assignments(node):
            _add_assignment(by_dependent, assignment)
        for assignment in cp_modifier_assignments(node):
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
