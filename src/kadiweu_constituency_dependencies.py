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
``mark``.  An immediate Q modifier of CP-me attaches as ``det`` when the
promoted content-word head is nominal.

Adnominal relative clauses promote the content-word head of ``IP-SUB`` and
attach it to the head of the containing NP as ``acl:relcl``.  In ``CP-REL``,
``WPRO ane`` is an overt relative pronoun rather than a marker: its WNP
coindex must match a unique ``*T*`` trace in ``IP-SUB``.  The subject-trace
configuration attested in DONE licenses ``ane`` as ``nsubj`` of the promoted
clause head.  In an adnominal ``CP-me``, the existing complementizer rule
attaches ``me`` to that same head as ``mark``.

Sentence heads are inherited from an overt verb, NP-PRD, CP-me predicate,
or a sole overt daughter (ignoring punctuation/empty projections). A
sentence-level CP-D promotes its IP-SUB head. The attested verbless
CP -> NP CAPL promotes the NP head and attaches CAPL as mark. Coordination
IP-MAT -> IP-MAT (CONJP CONJ IP-MAT)+ promotes the first conjunct; later
heads attach as conj and their coordinators as cc. Only the sentence-level
head receives HEAD=0/root. Labelled NP-SBJ, local IP negation, and immediate
sentence punctuation are supported. Clause-local argument defaults use VBU,
one-NP and NP-V-NP configurations after explicit labels and trace rules.
NP-APL maps provisionally to obj. Coindexed possessor raising through NP-GEN
maps to dislocated under the reference treebank's Basic UD convention.
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
RELATIVE_CLAUSE_RULE = "adnominal-relative-clause"
RELATIVE_PRONOUN_RULE = "relative-pronoun-trace"

NP_HEAD_TAGS = frozenset({"N", "N$", "NPR"})
ELLIPTICAL_NP_HEAD_TAGS = frozenset({"D", "DAPL", "PRO"})
NOMINAL_MODIFIER_TAGS = frozenset({"D", "DAPL", "Q"})
DET_MODIFIABLE_NOUN_TAGS = frozenset({"N", "N$"})
VERBAL_HEAD_TAGS = frozenset({"VB", "VBU", "VBAPL"})
APPLICATIVE_RELATION = "obj"  # Provisional project policy; retain rule provenance.


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


def _normalized_form(form: str) -> str:
    """Return a lexical form without TBP fusion-boundary markers."""

    return form.replace("@", "").casefold()


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

    This selects a head, not its external dependency. In particular, nested
    matrix clauses do not receive root here. Ambiguity is not resolved by
    discarding unresolved candidate phrases.
    """

    if isinstance(node, TokenNode):
        return None if node.empty_category else node
    if is_np(node):
        return lexical_head(node)
    if isinstance(node, ConstituentNode) and node.label in {"CP", "CP-me", "CP-D"}:
        complement = cp_complement(node)
        return ud_head(complement) if complement is not None else None
    if is_ip_mat(node):
        coordination = coordination_parts(node)
        if coordination is not None:
            return ud_head(coordination[0])
        verbs = [c for c in node.children if isinstance(c, TokenNode)
                 and not c.empty_category and c.tag in VERBAL_HEAD_TAGS]
        if verbs:
            return verbs[0] if len(verbs) == 1 else None
        predicates = [c for c in node.children if has_function(c, "NP", "PRD")]
        if predicates:
            return ud_head(predicates[0]) if len(predicates) == 1 else None
        cps = [c for c in node.children if isinstance(c, ConstituentNode)
               and (c.label == "CP-me" or verbless_capl_np(c) is not None)]
        if cps:
            return ud_head(cps[0]) if len(cps) == 1 else None
        children = overt_children(node)
        return ud_head(children[0]) if len(children) == 1 else None
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

    predicates = [c for c in node.children if has_function(c, "NP", "PRD")]
    candidates = predicates or [c for c in node.children if is_np(c)]
    if len(candidates) == 1:
        return lexical_head(candidates[0])
    return None


def has_function(node: TreeNode, category: str, function: str) -> bool:
    return (isinstance(node, ConstituentNode)
            and node.label.split("-")[0] == category
            and function in node.label.split("-")[1:])


def is_ip_mat(node: TreeNode) -> bool:
    return has_function(node, "IP", "MAT")


def overt_children(node: ConstituentNode) -> list[TreeNode]:
    """Ignore punctuation and wholly empty projections, not unresolved phrases."""
    return [c for c in node.children
            if not (isinstance(c, TokenNode) and c.tag in {"PUNC", "PUNCT", ".", ","})
            and any(isinstance(t, TokenNode) and not t.empty_category
                    for t in ([c] if isinstance(c, TokenNode) else c.walk()))]


def verbless_capl_np(node: TreeNode) -> ConstituentNode | None:
    """The attested CP -> NP CAPL construction; morphology adds no UD word."""
    if not isinstance(node, ConstituentNode) or node.label != "CP":
        return None
    children = overt_children(node)
    nps = [c for c in children if is_np(c)]
    markers = [c for c in children if isinstance(c, TokenNode) and c.tag == "CAPL"]
    if len(children) == 2 and len(nps) == len(markers) == 1:
        return nps[0]
    return None


def cp_complement(node: ConstituentNode) -> ConstituentNode | None:
    if node.label == "CP":
        return verbless_capl_np(node)
    if node.label not in {"CP-me", "CP-D"}:
        return None
    clauses = [c for c in node.children if is_ip_sub(c)]
    return clauses[0] if len(clauses) == 1 else None


def coordination_parts(
    node: ConstituentNode,
) -> tuple[ConstituentNode, list[tuple[TokenNode, ConstituentNode]]] | None:
    """Recognize IP-MAT -> IP-MAT (CONJP CONJ IP-MAT)+, locally."""
    if not is_ip_mat(node):
        return None
    children = overt_children(node)
    if len(children) < 2 or not is_ip_mat(children[0]):
        return None
    subsequent = []
    for wrapper in children[1:]:
        if not isinstance(wrapper, ConstituentNode) or wrapper.label != "CONJP":
            return None
        parts = overt_children(wrapper)
        clauses = [c for c in parts if is_ip_mat(c)]
        markers = [c for c in parts if isinstance(c, TokenNode) and c.tag == "CONJ"]
        if len(parts) != 2 or len(clauses) != 1 or len(markers) != 1:
            return None
        subsequent.append((markers[0], clauses[0]))
    return children[0], subsequent


def clause_assignments(node: ConstituentNode) -> list[DependencyAssignment]:
    """Local edges only: root is assigned separately, once per sentence.

    Bare verbal arguments are handled later by argument_assignments, after
    trace dependencies are established. This pass handles explicit structure.
    """
    result = []
    head = ud_head(node)
    if head is None:
        return result
    coordination = coordination_parts(node)
    if coordination is not None:
        for marker, clause in coordination[1]:
            other = ud_head(clause)
            if other is not None:
                result.extend([
                    DependencyAssignment(other.position, head.position, "conj", "clause-coordination"),
                    DependencyAssignment(marker.position, other.position, "cc", "clause-coordinator"),
                ])
    if is_ip_mat(node) or is_ip_sub(node):
        subjects = [c for c in node.children if has_function(c, "NP", "SBJ")]
        # van-data,0.72: require exactly NP + the attested verbless CP.
        children = overt_children(node)
        if (not subjects and is_ip_mat(node) and len(children) == 2
                and sum(verbless_capl_np(c) is not None for c in children) == 1):
            subjects = [c for c in children if is_np(c)]
        if len(subjects) == 1:
            subject = lexical_head(subjects[0])
            if subject is not None and subject.position != head.position:
                result.append(DependencyAssignment(subject.position, head.position,
                                                   "nsubj", "clause-subject"))
        for child in node.children:
            if isinstance(child, TokenNode) and not child.empty_category and child.tag == "NEG":
                result.append(DependencyAssignment(child.position, head.position,
                                                   "advmod", "clause-negation"))
    return result


def possessor_raising_assignments(tree: ConstituencyTree) -> list[DependencyAssignment]:
    """Attested Basic UD: raised NP -> predicate (dislocated).

    Match a unique overt NP-i and NP-GEN/*T*-i inside an N$ projection.
    Restrict to local VBU predication, allowing the attested intervening
    CP-me/IP-SUB. Do not emit the trace or an additional Basic UD possessor
    edge. Unknown, duplicate and nonlocal chains remain unresolved.
    """
    result = []
    for trace in tree.tokens:
        projection = trace.parent
        if (not trace.empty_category or trace.form != "*T*"
                or len(trace.coindex) != 1 or projection is None
                or projection.label != "NP-GEN" or len(projection.children) != 1):
            continue
        possessum_np = projection.parent
        if possessum_np is None or not is_np(possessum_np):
            continue
        possessum = lexical_head(possessum_np)
        clause = possessum_np.parent
        if (possessum is None or possessum.tag != "N$" or clause is None
                or not (is_ip_mat(clause) or is_ip_sub(clause))):
            continue
        predicate = ud_head(clause)
        if predicate is None or predicate.tag != "VBU":
            continue
        scope = clause
        if is_ip_sub(clause):
            cp = clause.parent
            if cp is None or cp.label != "CP-me" or cp.parent is None or not is_ip_mat(cp.parent):
                continue
            scope = cp.parent
        matching_traces = [t for t in scope.walk() if isinstance(t, TokenNode)
                           and t.empty_category and t.coindex == trace.coindex]
        candidates = [n for n in scope.walk() if is_np(n)
                      and n.coindex == trace.coindex and lexical_head(n) is not None]
        if len(matching_traces) != 1 or len(candidates) != 1:
            continue
        raised = candidates[0]
        raised_head = lexical_head(raised)
        if (raised.parent is not scope or raised is possessum_np
                or raised_head.position >= predicate.position
                or has_function(raised, "NP", "SBJ") or has_function(raised, "NP", "APL")):
            continue
        result.append(DependencyAssignment(raised_head.position, predicate.position,
                                          "dislocated", "possessor-raising-trace"))
    return result


def argument_assignments(
    node: ConstituentNode, established: dict[int, DependencyAssignment],
) -> list[DependencyAssignment]:
    """Clause-local defaults, subordinate to explicit labels and trace rules.

    Coindexed NPs and unclassified functional NPs are not bare arguments.
    VBU licenses a sole NP subject regardless of order, never an SVO object.
    Other verbal predicates use one-NP and strict NP-V-NP defaults. These
    defaults are provisional, not a general claim about Kadiwéu word order.
    """
    if not (is_ip_mat(node) or is_ip_sub(node)):
        return []
    predicate = ud_head(node)
    # Arguments belong to this immediate predicate, not a promoted CP head
    # or a verb found inside a different conjunct.
    if (predicate is None or predicate.tag not in VERBAL_HEAD_TAGS
            or predicate.parent is not node):
        return []
    result = []
    apls = [n for n in node.children if has_function(n, "NP", "APL")]
    objects = [a for a in established.values()
               if a.head_position == predicate.position and a.deprel == APPLICATIVE_RELATION]
    if len(apls) == 1 and not objects and predicate.tag != "VBU":
        head = lexical_head(apls[0])
        if head is not None and head.position not in established:
            result.append(DependencyAssignment(head.position, predicate.position,
                                              APPLICATIVE_RELATION, "applicative-argument"))
            objects = result[:]
    # Count unresolved bare NPs too: ambiguity must not turn two NPs into one.
    bare = [n for n in node.children if is_np(n) and n.label == "NP"
            and not n.coindex and any(isinstance(t, TokenNode) and not t.empty_category
                                      for t in n.walk())]
    heads = [lexical_head(n) for n in bare]
    if any(h is None for h in heads):
        return result
    heads = [h for h in heads if h.position not in established]
    subjects = [a for a in established.values()
                if a.head_position == predicate.position and a.deprel == "nsubj"]
    # A local subject label or movement gap blocks subject guessing even if
    # the corresponding lexical/relative resolution failed.
    subject_slot = bool(subjects) or any(
        has_function(n, "NP", "SBJ") or
        (isinstance(n, ConstituentNode) and n.label == "NP-TRACE")
        for n in node.children)
    if predicate.tag == "VBU":
        if len(heads) == 1 and not subject_slot and not apls:
            result.append(DependencyAssignment(heads[0].position, predicate.position,
                                              "nsubj", "unaccusative-subject"))
        return result
    if len(heads) == 1 and not subject_slot:
        result.append(DependencyAssignment(heads[0].position, predicate.position,
                                          "nsubj", "clause-single-np-subject"))
    elif (len(heads) == 2 and not subject_slot and not apls and not objects
          and heads[0].position < predicate.position < heads[1].position):
        result.extend([
            DependencyAssignment(heads[0].position, predicate.position, "nsubj", "clause-svo-subject"),
            DependencyAssignment(heads[1].position, predicate.position, "obj", "clause-svo-object"),
        ])
    elif (len(heads) == 1 and subjects and not apls and not objects
          and heads[0].position > predicate.position):
        result.append(DependencyAssignment(heads[0].position, predicate.position,
                                          "obj", "clause-postverbal-object"))
    return result


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
    """Promote IP-SUB, or the NP in the attested verbless CAPL construction."""

    # CP-REL is excluded: its relative element requires a separate UD
    # analysis and is not licensed as ``mark`` by this rule.
    if node.label not in {"CP-me", "CP-D", "CP"}:
        return []
    complementizers = [
        child
        for child in node.children
        if isinstance(child, TokenNode)
        and not child.empty_category
        and child.tag in {"C", "CAPL"}
    ]
    complement = cp_complement(node)
    if len(complementizers) != 1 or complement is None:
        return []
    complement_head = ud_head(complement)
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
    """Attach CP-me Q to a nominal head, or eliodi to a verbal head."""

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
    if complement_head is None:
        return []
    if complement_head.tag in VERBAL_HEAD_TAGS:
        # Only eliodi's agreed contextual mapping; do not generalize every Q.
        return [DependencyAssignment(m.position, complement_head.position,
                                     "advmod", "eliodi-verbal-modifier")
                for m in modifiers if _normalized_form(m.form) == "eliodi"]
    if complement_head.tag not in DET_MODIFIABLE_NOUN_TAGS:
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


def _unique_ip_sub(node: ConstituentNode) -> ConstituentNode | None:
    complements = [child for child in node.children if is_ip_sub(child)]
    return complements[0] if len(complements) == 1 else None


def _unique_relative_ane(
    node: ConstituentNode,
) -> tuple[TokenNode, tuple[int, ...]] | None:
    """Return the unique immediate WNP's ``ane`` and its coindex."""

    candidates: list[tuple[TokenNode, tuple[int, ...]]] = []
    for child in node.children:
        if not isinstance(child, ConstituentNode) or child.label != "WNP":
            continue
        relative_words = [
            descendant
            for descendant in child.walk()
            if isinstance(descendant, TokenNode)
            and not descendant.empty_category
            and descendant.tag == "WPRO"
            and _normalized_form(descendant.form) == "ane"
        ]
        if len(relative_words) == 1 and child.coindex:
            candidates.append((relative_words[0], child.coindex))
    return candidates[0] if len(candidates) == 1 else None


def _uniquely_coindexed_trace(
    clause: ConstituentNode,
    coindex: tuple[int, ...],
) -> TokenNode | None:
    traces = [
        descendant
        for descendant in clause.walk()
        if isinstance(descendant, TokenNode)
        and descendant.empty_category
        and descendant.form == "*T*"
        and descendant.coindex == coindex
    ]
    return traces[0] if len(traces) == 1 else None


def _attested_trace_relation(
    trace: TokenNode,
    clause: ConstituentNode,
    clause_head: TokenNode,
) -> str | None:
    """Return the role licensed by a currently attested trace configuration.

    All DONE ``ane`` relatives have an immediate, preverbal/prepredicative
    ``NP-TRACE`` daughter of IP-SUB and no overt subject projection.  This
    configuration realizes the relative pronoun as ``nsubj``.  Other trace
    positions remain unresolved until an authoritative example establishes
    their mapping; coindexation alone does not identify grammatical function.
    """

    projection = trace.parent
    if (
        projection is None
        or projection.label != "NP-TRACE"
        or projection.parent is not clause
        or trace.position >= clause_head.position
    ):
        return None
    overt_subjects = [
        child
        for child in clause.children
        if isinstance(child, ConstituentNode)
        and child.label.startswith("NP-SBJ")
        and lexical_head(child) is not None
    ]
    return None if overt_subjects else "nsubj"


def relative_clause_assignments(
    node: ConstituentNode,
) -> list[DependencyAssignment]:
    """Infer Basic UD dependencies for an unambiguous adnominal relative.

    ``CP-REL`` requires a unique coindexed ``WNP ... WPRO ane`` / ``*T*``
    chain.  ``CP-me`` requires an immediate ``C me``; its ``mark`` assignment
    is supplied by ``complementizer_assignments``.  Free relatives are outside
    this rule because they have no overt nominal antecedent.
    """

    if node.label not in {"CP-REL", "CP-me"}:
        return []
    parent = node.parent
    if parent is None or not is_np(parent):
        return []
    antecedent = lexical_head(parent)
    clause = _unique_ip_sub(node)
    if antecedent is None or clause is None:
        return []
    clause_head = ud_head(clause)
    if clause_head is None:
        return []

    clause_assignment = DependencyAssignment(
        dependent_position=clause_head.position,
        head_position=antecedent.position,
        deprel="acl:relcl",
        rule=RELATIVE_CLAUSE_RULE,
    )

    if node.label == "CP-me":
        markers = [
            child
            for child in node.children
            if isinstance(child, TokenNode)
            and not child.empty_category
            and child.tag == "C"
            and _normalized_form(child.form) == "me"
        ]
        return [clause_assignment] if len(markers) == 1 else []

    relative = _unique_relative_ane(node)
    if relative is None:
        return []
    ane, coindex = relative
    trace = _uniquely_coindexed_trace(clause, coindex)
    if trace is None:
        return []
    trace_relation = _attested_trace_relation(trace, clause, clause_head)
    if trace_relation is None:
        return []
    return [
        DependencyAssignment(
            dependent_position=ane.position,
            head_position=clause_head.position,
            deprel=trace_relation,
            rule=RELATIVE_PRONOUN_RULE,
        ),
        clause_assignment,
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
    if len(tree.roots) == 1:
        root = tree.root
        if is_ip_mat(root) or root.label in {"CP", "CP-me", "CP-D"}:
            head = ud_head(root)
            if head is not None:
                _add_assignment(by_dependent, DependencyAssignment(
                    head.position, 0, "root", "sentence-root"))
                for child in root.children:
                    if isinstance(child, TokenNode) and child.tag in {"PUNC", "PUNCT", ".", ","}:
                        _add_assignment(by_dependent, DependencyAssignment(
                            child.position, head.position, "punct", "sentence-punctuation"))
    for node in tree.walk():
        if not isinstance(node, ConstituentNode):
            continue
        for assignment in clause_assignments(node):
            _add_assignment(by_dependent, assignment)
        for assignment in nominal_determiner_assignments(node):
            _add_assignment(by_dependent, assignment)
        for assignment in possessive_np_assignments(node):
            _add_assignment(by_dependent, assignment)
        for assignment in complementizer_assignments(node):
            _add_assignment(by_dependent, assignment)
        for assignment in cp_modifier_assignments(node):
            _add_assignment(by_dependent, assignment)
        for assignment in relative_clause_assignments(node):
            _add_assignment(by_dependent, assignment)
    for assignment in possessor_raising_assignments(tree):
        _add_assignment(by_dependent, assignment)
    for node in tree.walk():
        if isinstance(node, ConstituentNode):
            for assignment in argument_assignments(node, by_dependent):
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
                "ROOT" if assignment.head_position == 0 else by_position[assignment.head_position].form,
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
