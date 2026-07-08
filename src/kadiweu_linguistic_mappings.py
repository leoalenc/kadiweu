#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linguistic mapping layer for the Kadiwéu Tycho Brahe JSON -> UD converter.

This module centralizes language-specific and notation-specific knowledge:
- layered override resources;
- Tycho Brahe tag -> UD UPOS mappings;
- lemma inference from morphemic splits;
- UD FEATS inference from source token tags and morpheme tags;
- normalization of recurrent Tycho Brahe morpheme-tag variants;
- distribution of split-derived features across MWT components;
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


# ---------------------------------------------------------------------
# Tycho Brahe morpheme tag normalization and feature mapping
# ---------------------------------------------------------------------

# Canonicalize recurrent spelling/case variants in split-level tags.
# This table is intentionally restricted to morpheme/split tags, not
# source token tags. For example, token-level M is still handled by
# the UPOS map, while split-level M is a masculine gender marker.
SPLIT_TAG_ALIASES: Dict[str, str] = {
    "M": "Masc",
    "Masc": "Masc",
    "masc": "Masc",
    "F": "Fem",
    "Fem": "Fem",
    "fem": "Fem",
    "Plu": "Plur",
    "Pl": "Plur",
    "pl": "Plur",
    "Sg": "Sing",
    "sg": "Sing",
    "Sing": "Sing",
    "sing": "Sing",
    "Neg": "Neg",
    "NEG": "Neg",
    "neg": "Neg",
    "Inv": "Inv",
    "inv": "Inv",
    "Coll": "Tot",
    "coll": "Tot",
    "Apl": "Apl",
    "APL": "Apl",
    "PFV": "PFV",
    "Pfv": "PFV",
    "Imperf": "Imperf",
    "IMPERF": "Imperf",
    "imperf": "Imperf",
    "Erg": "Erg",
    "ERG": "Erg",
    "erg": "Erg",
        "Abs": "Abs",
    "ABS": "Abs",
    "abs": "Abs",

    # Demonstrative / anaphoric split tags.
    # In the current data, Anf behaves like the demonstrative/anaphoric
    # prefix found in forms such as niGijo, naGani, niGida, etc.
    "Dem": "Dem",
    "DEM": "Dem",
    "dem": "Dem",
    "Anf": "Dem",
    "ANF": "Dem",
    "anf": "Dem",

    # Relative/pronominal split tags.
    "Wpro": "Wpro",
    "WPRO": "Wpro",
    "wpro": "Wpro",
    "Pro": "Pro",
    "PRO": "Pro",
    "pro": "Pro",

    # Nominal morphology.
    "Dim": "Dim",
    "DIM": "Dim",
    "dim": "Dim",
    "Cla": "Cla",
    "CLA": "Cla",
    "cla": "Cla",

    # Applicative/oblique person marking variants.
    "OBL": "OBL",
    "Obl": "OBL",
    "obl": "OBL",

    # Nominalization variants. Keep these as Der for now; do not
    # generate UD FEATS directly from them yet.
    "Nmlz": "Der",
    "NMLZ": "Der",
    "nmlz": "Der",
}

# Direct split-tag -> UD FEATS mappings. Context-sensitive mappings such
# as Abs with gloss-br=1 are handled in features_from_split().
SPLIT_TAG_TO_FEATS: Dict[str, List[str]] = {
    "Masc": ["Gender=Masc"],
    "Fem": ["Gender=Fem"],
    "Plur": ["Number=Plur"],
    "Sing": ["Number=Sing"],
    "Tot": [], # TODO: "Tot" is a totaltative marker, but UD does not have a standard feature for it.
    "Neg": ["Polarity=Neg"],
    "Inv": ["Voice=Inv"],
    "Apl": ["Voice=Appl"],
    "PFV": ["Aspect=Perf"],
    "Imperf": ["Aspect=Imp"],

    # Strong productive mappings from split tags.
    # Lexical/contextual refinements remain the job of the override resources.
    "Dem": ["PronType=Dem"],
    "Wpro": ["PronType=Rel"],
    "Dim": ["Degree=Dim"],
}

# Split-derived features in @-style MWTs must be assigned to the component
# that realizes the corresponding grammatical information. NEG-targeted
# features attach to the negative particle; VERB-targeted features attach
# to the verbal component. None means the feature may remain on ordinary
# non-MWT tokens.
SPLIT_TAG_FEATURE_TARGET: Dict[str, str] = {
    "Neg": "NEG",
    "Inv": "VERB",
    "Apl": "VERB",
    "PFV": "VERB",
    "Imperf": "VERB",
        "Abs": "VERB",
    "Erg": "VERB",
    "OBL": "VERB",
    "v": "VERB",

    # These should attach to the nominal/pronominal component in MWTs
    # such as C+D and C+DAPL, not to the complementizer component.
    "Dem": "NOMINAL",
    "Wpro": "NOMINAL",
    "Pro": "NOMINAL",
    "Dim": "NOMINAL",
    "Gnr": "NOMINAL",
    "Cla": "NOMINAL",
}

VERBAL_SOURCE_TAGS = {"VB", "VBI", "VBT", "VBAPL", "VBTAPL", "AUX", "T"}
NEGATIVE_SOURCE_TAGS = {"NEG", "ADVNEG", "CNEG"}


def canonicalize_split_tag(tag: Any) -> str:
    """Return the canonical spelling of a Tycho Brahe split/morpheme tag."""
    raw = str(tag).strip()
    return SPLIT_TAG_ALIASES.get(raw, raw)


def normalize_split_tags(token: Dict[str, Any]) -> List[str]:
    """Return canonicalized source morpheme/split tags as strings."""
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return []
    tags: List[str] = []
    for split in splits:
        if isinstance(split, dict):
            tag = split.get("t")
            if tag:
                tags.append(canonicalize_split_tag(tag))
    return tags


def _target_for_component(component_tag: str, component_upos: Optional[str]) -> str:
    """Classify an emitted token/component for MWT feature distribution.

    This is mainly relevant for @-style MWTs such as C+D, C+DAPL,
    NEG+VB, and NEG+VBAPL. The split analysis may be stored on the
    first source token, but features must be assigned only to the
    component that realizes them.
    """
    if component_tag in NEGATIVE_SOURCE_TAGS or component_upos == "PART":
        return "NEG"
    if component_tag in VERBAL_SOURCE_TAGS or component_upos in {"VERB", "AUX"}:
        return "VERB"
    if component_upos in {"NOUN", "PROPN", "PRON", "DET", "ADJ", "NUM"}:
        return "NOMINAL"
    return component_tag


def _feature_applies_to_component(
    split_tag: str,
    component_tag: str,
    component_upos: Optional[str],
    *,
    restrict_to_mwt_component: bool,
) -> bool:
    """Return whether a split-derived feature belongs on this emitted token."""
    if not restrict_to_mwt_component:
        return True

    target = SPLIT_TAG_FEATURE_TARGET.get(split_tag)
    if target is None:
        return True

    return _target_for_component(component_tag, component_upos) == target

def _split_gloss(split: Dict[str, Any], key: str = "gloss-br") -> Optional[str]:
    """Return a normalized split gloss string, if present."""
    gloss = safe_get(split, "attributes", key, default=None)
    if gloss is None:
        return None
    value = str(gloss).strip()
    return value or None


def _person_from_gloss(gloss: Optional[str]) -> Optional[str]:
    """Extract person from common Tycho gloss values such as 1, 1s, 1SG, 3M."""
    if not gloss:
        return None
    value = gloss.strip()
    if value and value[0] in {"1", "2", "3"}:
        return value[0]
    return None


def _is_singular_gloss(gloss: Optional[str]) -> bool:
    """Return True for glosses that explicitly encode singular."""
    if not gloss:
        return False
    return gloss.lower() in {"1s", "1sg", "2s", "2sg", "3s", "3sg"}


def _gender_from_gloss(gloss: Optional[str]) -> Optional[str]:
    """Extract UD gender from recurrent Tycho gloss values."""
    if not gloss:
        return None
    value = gloss.strip()
    if value in {"M", "Masc", "masc", "MASC"} or "MASC" in value.upper():
        return "Masc"
    if value in {"F", "Fem", "fem", "FEM"} or "FEM" in value.upper():
        return "Fem"
    return None


def features_from_split(split: Dict[str, Any]) -> List[str]:
    """Map one Tycho Brahe split/morpheme analysis to UD FEATS.

    This function should encode productive split-level morphology only.
    Lexical gender, context-dependent UPOS decisions, and corrections for
    incomplete or wrong Tycho annotations remain in the override resources.
    """
    split_tag = canonicalize_split_tag(split.get("t", ""))
    features: List[str] = list(SPLIT_TAG_TO_FEATS.get(split_tag, []))

    gloss_br = _split_gloss(split, "gloss-br")
    gloss = _split_gloss(split, "gloss")
    gloss_for_gender = gloss_br or gloss

    # Absolutive agreement on verbal predicates.
    person = _person_from_gloss(gloss_br)
    if split_tag == "Abs" and person is not None:
        features.append(f"Person={person}")

    # Ergative agreement on verbal predicates.
    if split_tag == "Erg" and person is not None:
        features.append(f"Person[erg]={person}")

    # Possessor person on possessed nouns.
    if split_tag == "Gen" and person is not None:
        features.append(f"Person[psor]={person}")
        if _is_singular_gloss(gloss_br):
            features.append("Number[psor]=Sing")
    elif split_tag in {"1POSS", "2POSS", "3POSS"}:
        features.append(f"Person[psor]={split_tag[0]}")

    # Gender is often encoded by the generic Gnr split tag and the actual
    # gender value is stored in gloss-br/gloss.
    gender = _gender_from_gloss(gloss_for_gender)
    if split_tag == "Gnr" and gender is not None:
        features.append(f"Gender={gender}")

    # Cla is not as general as Gnr, but it occurs in nominal classifiers such
    # as iwaalo = iwaa + lo, where the gloss identifies feminine gender.
    if split_tag == "Cla" and gender is not None:
        features.append(f"Gender={gender}")

    # Applicative agreement. Keep this conservative: derive object person and
    # gender only when the gloss explicitly encodes them.
    if split_tag == "Apl":
        obj_person = _person_from_gloss(gloss_br)
        if obj_person is not None:
            features.append(f"Person[obj]={obj_person}")

        obj_gender = _gender_from_gloss(gloss_br)
        if obj_gender is not None:
            features.append(f"Gender[obj]={obj_gender}")

    # OBL occurs in applicative-like verbal forms with object/oblique person
    # information, e.g. gloss-br=2 in ipegitaGagi.
    if split_tag == "OBL":
        obj_person = _person_from_gloss(gloss_br)
        if obj_person is not None:
            features.append(f"Person[obj]={obj_person}")
        if _is_singular_gloss(gloss_br):
            features.append("Number[obj]=Sing")

    # Independent personal-pronoun split, e.g. ee with gloss-br=1SG.
    if split_tag == "Pro":
        features.append("PronType=Prs")
        pro_person = _person_from_gloss(gloss_br)
        if pro_person is not None:
            features.append(f"Person={pro_person}")
        if _is_singular_gloss(gloss_br):
            features.append("Number=Sing")

    return features


def split_derived_feats(
    token: Dict[str, Any],
    component_tag: str,
    component_upos: Optional[str],
    *,
    restrict_to_mwt_component: bool = False,
) -> List[str]:
    """Return UD FEATS inferred from split tags for one emitted token."""
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return []

    features: List[str] = []
    for split in splits:
        if not isinstance(split, dict):
            continue
        split_tag = canonicalize_split_tag(split.get("t", ""))
        if not _feature_applies_to_component(
            split_tag,
            component_tag,
            component_upos,
            restrict_to_mwt_component=restrict_to_mwt_component,
        ):
            continue
        features.extend(features_from_split(split))

    return features


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
    feature_source_token: Optional[Dict[str, Any]] = None,
    restrict_split_feats_to_component: bool = False,
) -> str:
    """Infer UD FEATS from source tag, morpheme tags, and override resources.

    feature_source_token is normally tok. In @-style MWTs, however, the
    complete split analysis may be stored on the first source token only
    (e.g. aG@ in NEG+VB). In that case, the converter can pass the MWT
    source token as feature_source_token while tag/upos identify the emitted
    component that should receive the compatible features.
    """
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
        source_token = feature_source_token if feature_source_token is not None else tok
        feats.extend(
            split_derived_feats(
                source_token,
                tag,
                upos,
                restrict_to_mwt_component=restrict_split_feats_to_component,
            )
        )

        # Keep previous token-tag heuristics for compatibility when the
        # source token has no corresponding split analysis.
        split_tags = normalize_split_tags(source_token)

        if tag == "T":
            if "PFV" in split_tags and "Aspect=Perf" not in feats:
                feats.append("Aspect=Perf")
            if "Imperf" in split_tags and "Aspect=Imp" not in feats:
                feats.append("Aspect=Imp")

        if tag == "NEG" and "Polarity=Neg" not in feats:
            feats.append("Polarity=Neg")

        if tag == "VBAPL" and "Voice=Appl" not in feats:
            feats.append("Voice=Appl")
        
        # Kadiwéu finite verbal predicates are often identifiable by verbal
        # split morphology even when Mood/VerbForm are not explicitly encoded
        # in the source. Gold-derived overrides already learn these features
        # for many forms; this fallback improves coverage for new or unseen
        # forms without replacing lexical overrides.
        if upos in {"VERB", "AUX"}:
            if any(t in split_tags for t in {"v", "Erg", "Abs", "Inv", "Apl", "OBL"}):
                if "VerbForm=Fin" not in feats:
                    feats.append("VerbForm=Fin")
                if "Mood=Ind" not in feats:
                    feats.append("Mood=Ind")

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
