#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Tuple

LOOKUP_CHAR_MAP = str.maketrans({
    "ǥ": "g",   # future-proof
    "Ɠ": "G",
    "ɡ": "g",
})

def normalize_form_for_lookup(form: str) -> str:
    """
    Normalize a token form for override matching and lexicon lookup.

    Current policy:
    - strip surrounding whitespace
    - map a few orthographic variants to a common lookup space
    - lowercase only the first character

    Examples:
        NaGajo -> naGajo
        naGajo -> naGajo
        Naǥajo -> naGajo
    """
    if form is None:
        return ""
    form = str(form).strip().translate(LOOKUP_CHAR_MAP)
    if not form:
        return ""
    return form[:1].lower() + form[1:]

def get_surface_and_lookup_form(form: str) -> Tuple[str, str]:
    surface_form = form or ""
    lookup_form = normalize_form_for_lookup(surface_form)
    return surface_form, lookup_form

def canonicalize_override_map(raw_map: dict, label: str = "override") -> dict:
    cooked = {}
    for key, value in raw_map.items():
        if isinstance(key, tuple) and key:
            norm_key = (normalize_form_for_lookup(key[0]), *key[1:])
        else:
            norm_key = normalize_form_for_lookup(key)

        if norm_key in cooked and cooked[norm_key] != value:
            raise ValueError(
                f"Conflicting {label} entries after normalization: "
                f"{key!r} -> {norm_key!r}"
            )
        cooked[norm_key] = value
    return cooked
