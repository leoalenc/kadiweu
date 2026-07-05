#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linguistic mapping layer for the Kadiwéu Tycho Brahe JSON -> UD converter.

This module centralizes language-specific and notation-specific knowledge:
- layered override resources;
- Tycho Brahe tag -> UD UPOS mappings;
- lemma inference from morphemic splits;
- UD FEATS inference from source token tags and morpheme tags;
- PronType lookup hierarchy;
- known form corrections.

The main converter should keep algorithmic conversion logic hereafter: JSON walking,
MWT reconstruction, dependency induction, TokenRange/SpaceAfter handling, and CoNLL-U
serialization. It should call this module for linguistic interpretation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kadiweu_converter_config import UPOS_MAP
from kadiweu_morphology import get_standard_form_correction
from kadiweu_normalization import normalize_form_for_lookup, canonicalize_override_map

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_BASE_OVERRIDES_PATH = PROJECT_ROOT / "data" / "resources" / "kadiweu_default_overrides.json"
DEFAULT_GOLD_OVERRIDES_PATH = PROJECT_ROOT / "data" / "resources" / "gold_derived_overrides.json"
DEFAULT_MANUAL_OVERRIDES_PATH = PROJECT_ROOT / "data" / "resources" / "kadiweu_manual_overrides.json"

LEMMA_OVERRIDES: Dict[str, str] = {}
FORM_FEAT_OVERRIDES: Dict[str, str] = {}
PRONTYPE_OVERRIDES: Dict[Tuple[str, str], str] = {}
LEMMA_PRONTYPE_OVERRIDES: Dict[Tuple[str, str], str] = {}
TAG_TO_DEFAULT_PRONTYPE: Dict[Tuple[str, str], str] = {}
UPOS_OVERRIDES: Dict[Tuple[str, str], str] = {}
FORM_CORRECTIONS: Dict[str, Dict[str, str]] = {}
TAG_TO_UPOS: Dict[str, str] = {}
FORM_TO_UPOS: Dict[str, str] = {}
FORM_TO_XPOS: Dict[str, str] = {}


def safe_get(d: Any, *path: str, default=None):
    """Safely descend nested dictionaries."""
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def normalize_split_tags(token: Dict[str, Any]) -> List[str]:
    """Return source morpheme/split tags as strings, preserving current behavior."""
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return []
    tags: List[str] = []
    for split in splits:
        if isinstance(split, dict):
            tag = split.get("t")
            if tag:
                tags.append(str(tag))
    return tags


def load_override_resource(
    path: Path,
) -> Tuple[
    Dict[str, str],
    Dict[str, str],
    Dict[Tuple[str, str], str],
    Dict[Tuple[str, str], str],
    Dict[Tuple[str, str], str],
    Dict[Tuple[str, str], str],
    Dict[str, Dict[str, str]],
    Dict[str, str],
    Dict[str, str],
    Dict[str, str],
]:
    """Load one external override resource file."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    lemma_overrides = data.get("lemma_overrides", {})
    form_feat_overrides = data.get("form_feat_overrides", {})
    prontype_overrides = {
        tuple(k.split("\t")): v
        for k, v in data.get("prontype_overrides", {}).items()
    }
    lemma_prontype_overrides = {
        tuple(k.split("\t")): v
        for k, v in data.get("lemma_prontype_overrides", {}).items()
    }
    tag_to_default_prontype = {
        tuple(k.split("\t")): v
        for k, v in data.get("tag_to_default_prontype", {}).items()
    }
    upos_overrides = {
        tuple(k.split("\t")): v
        for k, v in data.get("upos_overrides", {}).items()
    }
    form_corrections = data.get("form_corrections", {})
    tag_to_upos = data.get("tag_to_upos", {})
    form_to_upos = data.get("form_to_upos", {})
    form_to_xpos = data.get("form_to_xpos", {})

    return (
        lemma_overrides,
        form_feat_overrides,
        prontype_overrides,
        lemma_prontype_overrides,
        tag_to_default_prontype,
        upos_overrides,
        form_corrections,
        tag_to_upos,
        form_to_upos,
        form_to_xpos,
    )


def configure_override_resources(overrides_path: Optional[Path] = None) -> None:
    """Configure active override resources by merging external JSON files."""
    global LEMMA_OVERRIDES
    global FORM_FEAT_OVERRIDES
    global PRONTYPE_OVERRIDES
    global LEMMA_PRONTYPE_OVERRIDES
    global TAG_TO_DEFAULT_PRONTYPE
    global UPOS_OVERRIDES
    global FORM_CORRECTIONS
    global TAG_TO_UPOS
    global FORM_TO_UPOS
    global FORM_TO_XPOS

    LEMMA_OVERRIDES = {}
    FORM_FEAT_OVERRIDES = {}
    PRONTYPE_OVERRIDES = {}
    LEMMA_PRONTYPE_OVERRIDES = {}
    TAG_TO_DEFAULT_PRONTYPE = {}
    UPOS_OVERRIDES = {}
    FORM_CORRECTIONS = {}
    TAG_TO_UPOS = {}
    FORM_TO_UPOS = {}
    FORM_TO_XPOS = {}

    candidate_paths = [
        DEFAULT_BASE_OVERRIDES_PATH,
        DEFAULT_GOLD_OVERRIDES_PATH,
        DEFAULT_MANUAL_OVERRIDES_PATH,
    ]

    if overrides_path is not None:
        if not overrides_path.exists():
            raise FileNotFoundError(f"Override resource not found: {overrides_path}")
        candidate_paths.append(overrides_path)

    print(DEFAULT_BASE_OVERRIDES_PATH, file=sys.stderr)
    print(DEFAULT_GOLD_OVERRIDES_PATH, file=sys.stderr)
    print(DEFAULT_MANUAL_OVERRIDES_PATH, file=sys.stderr)

    for path in candidate_paths:
        print(f"Loading override resource: {path}", file=sys.stderr)
        if path is None or not path.exists():
            continue

        (
            lemma_overrides,
            form_feat_overrides,
            prontype_overrides,
            lemma_prontype_overrides,
            tag_to_default_prontype,
            upos_overrides,
            form_corrections,
            tag_to_upos,
            form_to_upos,
            form_to_xpos,
        ) = load_override_resource(path)

        LEMMA_OVERRIDES.update(lemma_overrides)
        FORM_FEAT_OVERRIDES.update(form_feat_overrides)
        PRONTYPE_OVERRIDES.update(prontype_overrides)
        LEMMA_PRONTYPE_OVERRIDES.update(lemma_prontype_overrides)
        TAG_TO_DEFAULT_PRONTYPE.update(tag_to_default_prontype)
        UPOS_OVERRIDES.update(upos_overrides)
        FORM_CORRECTIONS.update(form_corrections)
        TAG_TO_UPOS.update(tag_to_upos)
        FORM_TO_UPOS.update(form_to_upos)
        FORM_TO_XPOS.update(form_to_xpos)

    LEMMA_OVERRIDES = canonicalize_override_map(LEMMA_OVERRIDES, "LEMMA_OVERRIDES")
    FORM_FEAT_OVERRIDES = canonicalize_override_map(FORM_FEAT_OVERRIDES, "FORM_FEAT_OVERRIDES")
    PRONTYPE_OVERRIDES = canonicalize_override_map(PRONTYPE_OVERRIDES, "PRONTYPE_OVERRIDES")
    LEMMA_PRONTYPE_OVERRIDES = canonicalize_override_map(
        LEMMA_PRONTYPE_OVERRIDES,
        "LEMMA_PRONTYPE_OVERRIDES",
    )
    TAG_TO_DEFAULT_PRONTYPE = canonicalize_override_map(
        TAG_TO_DEFAULT_PRONTYPE,
        "TAG_TO_DEFAULT_PRONTYPE",
    )
    UPOS_OVERRIDES = canonicalize_override_map(UPOS_OVERRIDES, "UPOS_OVERRIDES")
    FORM_TO_UPOS = canonicalize_override_map(FORM_TO_UPOS, "FORM_TO_UPOS")
    FORM_TO_XPOS = canonicalize_override_map(FORM_TO_XPOS, "FORM_TO_XPOS")


def infer_lemma(form: str, tok: Dict[str, Any]) -> str:
    """Infer lemma from overrides or lexical-looking split tags."""
    if form in LEMMA_OVERRIDES:
        return LEMMA_OVERRIDES[form]

    splits = tok.get("splits", [])
    if isinstance(splits, list):
        for split in splits:
            if not isinstance(split, dict):
                continue
            tag = str(split.get("t", ""))
            val = str(split.get("v", ""))
            if tag in {"v", "n"} and val:
                return val
        for split in reversed(splits):
            if not isinstance(split, dict):
                continue
            val = str(split.get("v", ""))
            if val:
                return val

    return form


def _candidate_forms(surface_form: Optional[str], lookup_form: str) -> List[str]:
    candidates: List[str] = []
    for form in (surface_form, lookup_form):
        for candidate in (form, normalize_form_for_lookup(form) if form else None):
            if candidate and candidate not in candidates:
                candidates.append(candidate)
    return candidates


def infer_feats(
    lookup_form: str,
    tag: str,
    tok: Dict[str, Any],
    upos: Optional[str] = None,
    surface_form: Optional[str] = None,
    lemma_override: Optional[str] = None,
) -> str:
    """Infer UD FEATS from source tag, morpheme tags, and override resources."""
    feats: List[str] = []
    candidate_forms = _candidate_forms(surface_form, lookup_form)

    override_feats = None
    for form in candidate_forms:
        if form in FORM_FEAT_OVERRIDES:
            override_feats = FORM_FEAT_OVERRIDES[form]
            break

    if override_feats is not None:
        if override_feats and override_feats != "_":
            feats.extend(override_feats.split("|"))
    else:
        splits = tok.get("splits", [])
        if not isinstance(splits, list):
            splits = []

        split_tags = normalize_split_tags(tok)

        if tag == "T":
            if "PFV" in split_tags:
                feats.append("Aspect=Perf")
            if "Imperf" in split_tags:
                feats.append("Aspect=Imp")

        if tag == "NEG":
            feats.append("Polarity=Neg")

        if tag == "VBAPL":
            feats.append("Voice=Appl")

        for split in splits:
            if not isinstance(split, dict):
                continue

            split_tag = str(split.get("t", ""))
            gloss_br = safe_get(split, "attributes", "gloss-br", default=None)
            gloss_br = str(gloss_br).strip() if gloss_br is not None else None

            if split_tag == "Gen" and gloss_br in {"1", "2", "3"}:
                feats.append(f"Person[psor]={gloss_br}")
            elif split_tag in {"1POSS", "2POSS", "3POSS"}:
                person = split_tag[0]
                feats.append(f"Person[psor]={person}")

    lemma = lemma_override if lemma_override is not None else infer_lemma(lookup_form, tok)

    pron_type = None
    for form in candidate_forms:
        pron_type = PRONTYPE_OVERRIDES.get((form, upos))
        if pron_type is not None:
            break

    if pron_type is None:
        pron_type = LEMMA_PRONTYPE_OVERRIDES.get((lemma, upos))

    if pron_type is None:
        pron_type = TAG_TO_DEFAULT_PRONTYPE.get((tag, upos))

    if pron_type and upos in {"DET", "PRON", "ADV"}:
        feats = [feat for feat in feats if not feat.startswith("PronType=")]
        feats.append(f"PronType={pron_type}")

    if upos != "ADV":
        feats = [feat for feat in feats if not feat.startswith("AdvType=")]

    return "|".join(sorted(set(feats))) if feats else "_"


def infer_upos(tag: str) -> str:
    """Infer UD UPOS from a source tag."""
    override = TAG_TO_UPOS.get(tag)
    if override is not None:
        return override
    return UPOS_MAP.get(tag, "X")


def upos_override_candidates(form: str, tag: str):
    forms: List[str] = []
    for candidate in (form, normalize_form_for_lookup(form) if form else None):
        if candidate and candidate not in forms:
            forms.append(candidate)
    for form in forms:
        yield (form, tag)


def infer_upos_for_form(form: str, tag: str) -> str:
    """Infer UPOS, allowing form+source-tag override resources."""
    for key in upos_override_candidates(form, tag):
        override = UPOS_OVERRIDES.get(key)
        if override is not None:
            return override
    return infer_upos(tag)


def apply_upos_override(form: str, tag: str, upos: str) -> str:
    """Apply a form+source-tag UPOS override to an already inferred UPOS."""
    for key in upos_override_candidates(form, tag):
        override = UPOS_OVERRIDES.get(key)
        if override is not None:
            return override
    return upos


def get_form_correction(form: str) -> Optional[Dict[str, str]]:
    """Return correction metadata for known non-canonical source forms."""
    manual = FORM_CORRECTIONS.get(form)
    if manual is not None:
        return dict(manual)
    return get_standard_form_correction(form)


# Keep current script behavior: default resources are loaded when imported.
configure_override_resources()
