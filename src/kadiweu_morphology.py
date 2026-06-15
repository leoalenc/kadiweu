#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilities for Kadiwéu morphology used by the converter ecosystem.

This module centralizes small pieces of reusable linguistic knowledge that
should not be hard-coded in the conversion logic.

Current scope
-------------
- Deictic/numeral-classifier roots used in nG- demonstrative/pronominal forms.
- Generation of standard and reduced/non-standard nG- forms.
- Diagnostic inspection of generated mappings.

Linguistic note
---------------
For forms such as:

    niGida
    naGajo

the vowel after G is the gender marker:

    i = masculine
    a = feminine

The initial vowel after n may be absent in non-standard/source spelling:

    niGida -> nGida
    naGajo -> nGajo

The reduced spelling therefore suppresses only the first copied vowel, not the
gender-marking vowel after G.
"""

from __future__ import annotations

from pprint import pprint
from typing import Dict, Iterable, Mapping, MutableMapping, Optional


DEICTIC_ROOT_GLOSSES: Dict[str, Dict[str, str]] = {
    "da": {
        "gloss_1": "standing",
        "gloss_2": "vertically extended",
    },
    "ni": {
        "gloss_1": "sitting",
        "gloss_2": "non-extended",
    },
    "na": {
        "gloss_1": "coming",
        "gloss_2": "approaching",
    },
    "di": {
        "gloss_1": "lying",
        "gloss_2": "horizontally extended",
    },
    "jo": {
        "gloss": "going away",
    },
    "ca": {
        "gloss_1": "absent",
        "gloss_2": "out of sight",
        "source_form": "ka",
    },
}


GENDER_VOWELS: Dict[str, str] = {
    "a": "Fem",
    "i": "Masc",
}



def pluralize_ng_form(singular_form: str) -> str:
    """
    Build the plural form of an nG- demonstrative.

    Griffiths (2002):
        niGidi -> niGidiwa
        niGini -> niGiniwa
        niGina -> niGinoa
        niGijo -> niGijoa
        niGida -> niGidoa
    """
    if singular_form.endswith("i"):
        return singular_form + "wa"

    if singular_form.endswith("a"):
        return singular_form[:-1] + "oa"

    if singular_form.endswith("o"):
        return singular_form + "a"

    return singular_form + "wa"

def build_ng_deictic_form_map(
    roots: Optional[Mapping[str, Mapping[str, str]]] = None,
    gender_vowels: Optional[Mapping[str, str]] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Build standard and reduced nG- deictic forms.

    Standard form:
        n + V + G + V + root

    Reduced/non-standard form:
        n + G + V + root

    where V is the gender vowel:
        a = feminine
        i = masculine

    Examples:
        niGida -> nGida
        naGajo -> nGajo

    Returns
    -------
    dict
        A dictionary keyed by the reduced/non-standard spelling. Each value
        contains the corresponding standard form, gender, deictic root, and
        classifier/root gloss information.
    """
    roots = roots or DEICTIC_ROOT_GLOSSES
    gender_vowels = gender_vowels or GENDER_VOWELS

    out: Dict[str, Dict[str, str]] = {}

    for root, gloss_info in roots.items():
        for vowel, gender in gender_vowels.items():
            standard_form = f"n{vowel}G{vowel}{root}"
            reduced_form = f"nG{vowel}{root}"
            plural_form = pluralize_ng_form(standard_form)
            reduced_plural_form = pluralize_ng_form(reduced_form)

            out[reduced_form] = {
                "standard_form": standard_form,
                "standard_lemma": standard_form,
                "upos": "DET",
                "xpos": "D",
                "feats": f"Gender={gender}|Number=Sing",
                "gender": gender,
                "number": "Sing",
                "deictic_root": root,
                **dict(gloss_info),
            }

            out[reduced_plural_form] = {
                "standard_form": plural_form,
                "standard_lemma": standard_form,
                "upos": "DET",
                "xpos": "D",
                "feats": "Gender=Masc|Number=Plur",
                "gender": "Masc",
                "number": "Plur",
                "deictic_root": root,
                **dict(gloss_info),
            }

            out[plural_form] = {
                "standard_form": plural_form,
                "standard_lemma": standard_form,
                "upos": "DET",
                "xpos": "D",
                "feats": "Gender=Masc|Number=Plur",
                "gender": "Masc",
                "number": "Plur",
                "deictic_root": root,
                **dict(gloss_info),
        }

    return out


def build_form_corrections_from_ng_deictics(
    ng_map: Optional[Mapping[str, Mapping[str, str]]] = None,
) -> Dict[str, str]:
    """
    Build a simple typo-correction table from the rich nG- deictic mapping.

    This is suitable for feeding converter logic such as:

        lookup_form = FORM_CORRECTIONS.get(surface_form, surface_form)

    The richer metadata should still be kept for documentation and review.
    """
    ng_map = ng_map or build_ng_deictic_form_map()

    return {
        reduced_form: info["standard_form"]
        for reduced_form, info in ng_map.items()
    }


def describe_ng_deictic_form(
    form: str,
    ng_map: Optional[Mapping[str, Mapping[str, str]]] = None,
) -> Optional[Dict[str, str]]:
    """
    Return metadata for a reduced/non-standard nG- form, if known.
    """
    ng_map = ng_map or build_ng_deictic_form_map()
    item = ng_map.get(form)
    return dict(item) if item is not None else None

def correct_ng_deictic_form(form: str) -> Optional[dict]:
    """
    Return correction metadata for reduced nG- deictic forms.

    Example:
        nGida -> niGida
        nGajo -> naGajo
    """
    ng_map = build_ng_deictic_form_map()
    return ng_map.get(form)

def get_standard_form_correction(form: str) -> Optional[dict]:
    """
    Return correction metadata for known morphology-based spelling variants.
    """
    ng_info = correct_ng_deictic_form(form)
    if ng_info is not None:
        return ng_info

    return None

def test_ng_deictic_forms() -> None:
    """
    Print the generated nG- deictic mapping for manual inspection.

    Run:

        python3 kadiweu_morphology.py

    or import and call:

        from kadiweu_morphology import test_ng_deictic_forms
        test_ng_deictic_forms()
    """
    ng_map = build_ng_deictic_form_map()

    print("Generated reduced/non-standard nG- forms:")
    print()

    for reduced_form in sorted(ng_map):
        info = ng_map[reduced_form]
        print(
            f"{reduced_form:8s} -> {info['standard_form']:8s} "
            f"gender={info['gender']:4s} "
            f"root={info['deictic_root']:2s} "
            f"gloss={format_gloss(info)}"
        )

    print()
    print("Simple form_corrections table:")
    pprint(build_form_corrections_from_ng_deictics(ng_map), sort_dicts=True)


def format_gloss(info: Mapping[str, str]) -> str:
    """
    Format one gloss dictionary for compact display.
    """
    if "gloss" in info:
        return info["gloss"]

    glosses = []
    for key in ("gloss_1", "gloss_2"):
        value = info.get(key)
        if value:
            glosses.append(value)

    return " / ".join(glosses)


if __name__ == "__main__":
    test_ng_deictic_forms()
