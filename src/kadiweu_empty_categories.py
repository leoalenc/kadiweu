#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helpers for resolving Penn/Tycho-style empty categories before UD conversion.

At the moment this module handles:

- removal of empty-category tokens such as *T*
- local restructuring hints for relative clauses of the pattern:
      antecedent  REL  *T*  predicate
  which are converted in UD as:
      predicate -> acl:relcl (attached to antecedent)
      REL       -> nsubj     (attached to predicate)

The goal is not to perform full syntactic conversion here. This module is a
normalization layer that cleans the source representation and emits local
dependency hints for the main converter to use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import copy
import re
from typing import Any, Dict, List, Optional

EMPTY_FORM_RE = re.compile(r"^\*[^*]+\*$")

VERBAL_TAGS = {"VB", "VBAPL", "VBT", "VBTAPL", "VBI"}
PREDICATE_TAGS = VERBAL_TAGS | {"ADJ", "N", "N$", "NAPL"}
NOMINAL_TAGS = {"N", "N$", "NPR", "PRO", "PRO$"}
REL_TAGS = {"WPRO"}


@dataclass
class DependencyHint:
    source_pos: int
    deprel: str
    head_source_pos: Optional[int] = None
    note: str = ""


@dataclass
class EmptyCategoryResolution:
    tokens: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]
    dependency_hints: List[DependencyHint] = field(default_factory=list)
    removed_tokens: List[Dict[str, Any]] = field(default_factory=list)


def token_form(tok: Dict[str, Any]) -> str:
    return str(tok.get("v", "")).strip()


def token_tag(tok: Dict[str, Any]) -> str:
    return str(tok.get("t", "")).strip()


def token_pos(tok: Dict[str, Any]) -> Optional[int]:
    p = tok.get("p")
    return p if isinstance(p, int) else None


def is_empty_category_token(tok: Dict[str, Any]) -> bool:
    form = token_form(tok)
    if not form:
        return False
    if EMPTY_FORM_RE.match(form):
        return True
    # Be conservative: only treat bare T as empty when form itself is starred.
    return False


def is_relative_pronoun(tok: Dict[str, Any]) -> bool:
    tag = token_tag(tok)
    if tag in REL_TAGS:
        return True
    form = token_form(tok).lower()
    return form == "ane"


def is_predicate_candidate(tok: Dict[str, Any]) -> bool:
    return token_tag(tok) in PREDICATE_TAGS


def is_nominal_candidate(tok: Dict[str, Any]) -> bool:
    return token_tag(tok) in NOMINAL_TAGS


def _same_local_domain(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    pa = token_pos(a)
    pb = token_pos(b)
    if pa is None or pb is None:
        return False
    return abs(pa - pb) <= 4


def _nearest_previous(tokens: List[Dict[str, Any]], start_idx: int, pred) -> Optional[Dict[str, Any]]:
    for i in range(start_idx - 1, -1, -1):
        tok = tokens[i]
        if pred(tok):
            return tok
    return None


def _nearest_next(tokens: List[Dict[str, Any]], start_idx: int, pred) -> Optional[Dict[str, Any]]:
    for i in range(start_idx + 1, len(tokens)):
        tok = tokens[i]
        if pred(tok):
            return tok
    return None


def resolve_empty_categories(
    tokens: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
) -> EmptyCategoryResolution:
    """
    Return a cleaned token list plus local dependency hints.

    The token dictionaries are deep-copied so the caller can modify the result
    safely without mutating the original JSON object.
    """
    toks = [copy.deepcopy(tok) for tok in tokens if isinstance(tok, dict)]
    chs = [copy.deepcopy(ch) for ch in chunks if isinstance(ch, dict)]

    removed_tokens: List[Dict[str, Any]] = []
    hints: List[DependencyHint] = []

    # Detect local relative-clause patterns around empty traces before removal.
    for idx, tok in enumerate(toks):
        if not is_empty_category_token(tok):
            continue

        rel = _nearest_previous(toks, idx, is_relative_pronoun)
        pred = _nearest_next(toks, idx, is_predicate_candidate)

        if rel is None or pred is None:
            continue
        if not _same_local_domain(rel, tok) or not _same_local_domain(tok, pred):
            continue

        antecedent = _nearest_previous(
            toks,
            toks.index(rel),
            lambda x: (not is_empty_category_token(x)) and is_nominal_candidate(x),
        )
        if antecedent is None:
            continue

        rel_pos = token_pos(rel)
        pred_pos = token_pos(pred)
        ant_pos = token_pos(antecedent)
        if rel_pos is None or pred_pos is None or ant_pos is None:
            continue

        hints.append(
            DependencyHint(
                source_pos=pred_pos,
                deprel="acl:relcl",
                head_source_pos=ant_pos,
                note="relative-clause predicate recovered from empty trace",
            )
        )
        hints.append(
            DependencyHint(
                source_pos=rel_pos,
                deprel="nsubj",
                head_source_pos=pred_pos,
                note="relative pronoun promoted from trace context",
            )
        )

    cleaned_tokens: List[Dict[str, Any]] = []
    for tok in toks:
        if is_empty_category_token(tok):
            removed_tokens.append(tok)
            continue
        cleaned_tokens.append(tok)

    return EmptyCategoryResolution(
        tokens=cleaned_tokens,
        chunks=chs,
        dependency_hints=hints,
        removed_tokens=removed_tokens,
    )
