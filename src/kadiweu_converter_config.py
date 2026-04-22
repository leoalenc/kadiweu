"""Configuration constants for the Kadiwéu JSON -> CoNLL-U converter.

Purpose
-------
Keep relatively stable converter configuration out of the main conversion
script so that the converter logic remains easier to maintain.

This module is intended for:
- source-tag -> UD UPOS mappings
- other stable, code-adjacent configuration constants

More frequently edited linguistic resources such as lemma overrides,
feature overrides, and PronType overrides should live in external JSON files.
"""

from __future__ import annotations

UPOS_MAP = {
    "VB": "VERB",
    "VBAPL": "VERB",
    "VBT": "VERB",
    "VBTAPL": "VERB",
    "VBI": "VERB",
    "N": "NOUN",
    "N$": "NOUN",
    "NAPL": "NOUN",
    "NPR": "PROPN",
    "D": "DET",
    "Q": "DET",
    "PRO": "PRON",
    "PRO$": "PRON",
    "WPRO": "PRON",
    "WADV": "ADV",
    "ADV": "ADV",
    "ADJ": "ADJ",
    "NEG": "PART",
    "C": "SCONJ",
    "CT": "SCONJ",
    "CONJ": "CCONJ",
    "T": "AUX",
    "PUNCT": "PUNCT",
}
