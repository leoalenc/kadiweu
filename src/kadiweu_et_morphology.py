#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Morphological analysis and feature enrichment for Kadiwéu D-elements and *et*.

The module is shared by the JSON-to-CoNLL-U converter and the CoNLL-U
enrichment CLI at the bottom of this file. Its order of evidence is:

1. explicit TBP split analysis (especially ``Ncl`` and ``Gnr``);
2. reviewed analyses in ``data/resources/kadiweu_et_morphology.json``;
3. conservative productive templates for D-elements and ``et`` forms.

It adds missing features without replacing other inferred or overridden
features. ``NumClass`` is routed to a determiner/pronoun component or to the
verb that hosts an incorporated D-element. Personal-pronoun incorporation in
``et`` verbs contributes person/number features but does not itself imply
``NumClass``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT_INFO: Dict[str, Dict[str, str]] = {
    "da": {"NumClass": "Standing", "meaning": "standing / vertically extended"},
    "ni": {"NumClass": "Sitting", "meaning": "sitting / non-extended"},
    "na": {"NumClass": "Coming", "meaning": "coming / approaching"},
    "di": {"NumClass": "Lying", "meaning": "lying / horizontally extended"},
    "jo": {"NumClass": "Going", "meaning": "going away"},
    "ca": {"NumClass": "Absent", "meaning": "absent / out of sight"},
}
GENDER = {"i": "Masc", "a": "Fem"}
ROOT_TO_FEATURE = {root: data["NumClass"] for root, data in ROOT_INFO.items()}
ET_UPOS = {"VERB", "AUX"}
D_UPOS = {"DET", "PRON"}
D_XPOS = {"D", "DAPL", "PRO$", "PRO", "NPRO", "$PRO"}
PRONOUNS = {
    "ee": {"Person": "1", "Number": "Sing"},
    "eeyo": {"Person": "1", "Number": "Sing"},
    "akaami": {"Person": "2", "Number": "Sing"},
    "akami": {"Person": "2", "Number": "Sing"},
    "oko": {"Person": "1", "Number": "Plur"},
}
DEFAULT_INVENTORY = Path(__file__).resolve().parent.parent / "data" / "resources" / "kadiweu_et_morphology.json"


def normalize_form(form: Any) -> str:
    """Normalize orthographic G/ǥ variants and case for morphology lookup."""
    return str(form or "").strip().translate(str.maketrans({"ǥ": "g", "Ɠ": "g", "ɡ": "g"})).casefold()


@lru_cache(maxsize=8)
def _load_inventory_cached(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Cannot load Kadiwéu et morphology resource %s: %s" % (path, exc)) from exc
    return data if isinstance(data, dict) else {}


def load_inventory(path: Optional[Path] = None) -> dict[str, Any]:
    return _load_inventory_cached(str(path or DEFAULT_INVENTORY))


def _split_list(token: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(token, dict):
        return []
    splits = token.get("splits")
    return [x for x in splits if isinstance(x, dict)] if isinstance(splits, list) else []


def _root_from_split(value: Any) -> Optional[str]:
    root = normalize_form(value)
    return root if root in ROOT_TO_FEATURE else None


def _gender_from_split(splits: list[dict[str, Any]]) -> Optional[str]:
    for split in splits:
        if normalize_form(split.get("t")) != "gnr":
            continue
        value = normalize_form(split.get("v"))
        gloss = normalize_form((split.get("attributes") or {}).get("gloss-br", ""))
        if value in GENDER:
            return GENDER[value]
        if "fem" in gloss or gloss == "f":
            return "Fem"
        if "masc" in gloss or gloss == "m":
            return "Masc"
    return None


def _person_from_gloss(gloss: Any) -> Tuple[Optional[str], Optional[str]]:
    value = normalize_form(gloss)
    match = re.search(r"(?<!\d)([123])\s*(?:s|sg|sing)?\b", value)
    if not match:
        return None, None
    number = "Plur" if re.search(r"(?:pl|plural|plur)", value) else "Sing" if re.search(r"(?:sg|sing|\b[123]s\b)", value) else None
    return match.group(1), number


def _pluralize_d_form(form: str, root: str) -> str:
    if root.endswith("i"):
        return form + "wa"
    if root.endswith("a"):
        return form[:-1] + "oa"
    if root.endswith("o"):
        return form + "a"
    return form + "wa"


def _parse_d_element(form: str) -> Optional[dict[str, str]]:
    """Recognize a D-series form from its final gender-vowel + classifier root.

    The surface suffix is checked against the attested singular/plural
    alternations. Requiring a D/PRON tag at the call site prevents the same
    string ending in a noun or unrelated verb from receiving NumClass.
    """
    text = normalize_form(form)
    # Also permit the optional nG anaphoric/demonstrative prefix.
    candidates = {text}
    for initial in ("ni", "na", "ngi", "nga"):
        if text.startswith(initial) and len(text) > len(initial):
            candidates.add(text[len(initial):])
    for candidate in candidates:
        for root, info in ROOT_INFO.items():
            for vowel, gender in GENDER.items():
                base_tail = vowel + root
                variants = {base_tail, _pluralize_d_form(base_tail, root)}
                # A copied-gender nG prefix can remain in reduced source forms;
                # after stripping it, the remaining stem must still match.
                if any(candidate.endswith(variant) for variant in variants):
                    return {"NumClass": info["NumClass"], "Gender": gender, "root": root}
    return None


def _parse_et_classifier(form: str) -> Optional[dict[str, str]]:
    text = normalize_form(form)
    if not text.startswith("et"):
        return None
    stem = text[2:]
    for root, info in ROOT_INFO.items():
        for vowel, gender in GENDER.items():
            base = vowel + root
            variants = {base, _pluralize_d_form(base, root)}
            if stem in variants:
                return {"NumClass": info["NumClass"], "Gender": gender, "root": root, "incorporation": "D-element"}
    return None


def _et_pronoun_analysis(form: str) -> Optional[dict[str, str]]:
    text = normalize_form(form)
    if not text.startswith("et"):
        return None
    suffix = text[2:]
    # The TBP lexicon lists variants such as etakami/etakaami and forms with
    # the productive 2PL suffix. The suffix is recorded separately from the
    # incorporated pronoun so it does not get mistaken for a classifier.
    plural_suffix = "tiwaji"
    has_plural_suffix = suffix.endswith(plural_suffix)
    if has_plural_suffix:
        suffix = suffix[:-len(plural_suffix)]
    pronoun = PRONOUNS.get(suffix)
    if not pronoun:
        return None
    out = dict(pronoun)
    if has_plural_suffix:
        out["Number"] = "Plur"
    out["incorporation"] = "personal-pronoun"
    return out


def _registered_analysis(form: str, inventory: dict[str, Any]) -> list[dict[str, Any]]:
    forms = inventory.get("forms", {})
    if not isinstance(forms, dict):
        return []
    record = forms.get(normalize_form(form))
    if not isinstance(record, dict):
        return []
    analyses = record.get("analyses", [])
    return [x for x in analyses if isinstance(x, dict)] if isinstance(analyses, list) else []


def analyze_token(
    form: str,
    lemma: str = "",
    upos: str = "",
    xpos: str = "",
    source_token: Optional[dict[str, Any]] = None,
    feature_source_token: Optional[dict[str, Any]] = None,
    inventory: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Return analysis metadata/features without modifying an input token."""
    resource = inventory if inventory is not None else load_inventory()
    source = feature_source_token if feature_source_token is not None else source_token
    splits = _split_list(source)
    upos_upper, xpos_upper = str(upos).upper(), str(xpos).upper()
    features: dict[str, str] = {}
    roots = []
    for split in splits:
        if normalize_form(split.get("t")) == "ncl":
            root = _root_from_split(split.get("v"))
            if root:
                roots.append(root)
    if roots and upos_upper in D_UPOS | ET_UPOS:
        features["NumClass"] = ROOT_TO_FEATURE[roots[-1]]
    gender = _gender_from_split(splits)
    if gender:
        features["Gender"] = gender

    lemma_is_et = normalize_form(lemma) == "et"
    et_form_match = _parse_et_classifier(form) or _et_pronoun_analysis(form)
    is_et_verb = upos_upper in ET_UPOS and (lemma_is_et or et_form_match is not None)

    if is_et_verb:
        # A complete source segmentation has priority over raw-form fallback.
        if not roots:
            et_class = _parse_et_classifier(form)
            if et_class:
                features.setdefault("NumClass", et_class["NumClass"])
                features.setdefault("Gender", et_class["Gender"])
        pronoun_splits = [s for s in splits if normalize_form(s.get("t")) == "pro"]
        if pronoun_splits:
            gloss = (pronoun_splits[-1].get("attributes") or {}).get("gloss-br", "")
            person, number = _person_from_gloss(gloss)
            if person:
                features.setdefault("Person", person)
            if number:
                features.setdefault("Number", number)
            suffix_info = _et_pronoun_analysis(form)
            if suffix_info:
                for key in ("Person", "Number"):
                    if key in suffix_info:
                        features.setdefault(key, suffix_info[key])
        elif not roots:
            pronoun_info = _et_pronoun_analysis(form)
            if pronoun_info:
                features.setdefault("Person", pronoun_info["Person"])
                features.setdefault("Number", pronoun_info["Number"])

        # Analyses exported from the lexicon can resolve a non-template form.
        for analysis in _registered_analysis(form, resource):
            raw_features = analysis.get("features", {})
            if isinstance(raw_features, dict):
                for key, value in raw_features.items():
                    if key in {"NumClass", "Gender", "Person", "Number"} and value:
                        features.setdefault(key, str(value))

    elif upos_upper in D_UPOS or xpos_upper in D_XPOS:
        # Split evidence is strongest; otherwise use the D-series form shape.
        if not roots:
            d_analysis = _parse_d_element(form)
            if d_analysis:
                features.setdefault("NumClass", d_analysis["NumClass"])
                features.setdefault("Gender", d_analysis["Gender"])
        for analysis in _registered_analysis(form, resource):
            raw_features = analysis.get("features", {})
            if isinstance(raw_features, dict) and raw_features.get("NumClass"):
                features.setdefault("NumClass", str(raw_features["NumClass"]))

    return {
        "is_et_verb": is_et_verb,
        "incorporation": "D-element" if "NumClass" in features and is_et_verb else "personal-pronoun" if is_et_verb and "Person" in features else None,
        "features": features,
        "roots": roots,
    }


def add_features(
    existing_feats: str,
    form: str,
    lemma: str = "",
    upos: str = "",
    xpos: str = "",
    source_token: Optional[dict[str, Any]] = None,
    feature_source_token: Optional[dict[str, Any]] = None,
    inventory: Optional[dict[str, Any]] = None,
) -> str:
    """Add morphology features while preserving every pre-existing feature."""
    parsed: dict[str, str] = {}
    if existing_feats and existing_feats != "_":
        for item in existing_feats.split("|"):
            if "=" in item:
                key, value = item.split("=", 1)
                parsed[key] = value
    analysis = analyze_token(form, lemma, upos, xpos, source_token, feature_source_token, inventory)
    for key, value in analysis["features"].items():
        parsed.setdefault(key, value)
    return "|".join("%s=%s" % item for item in sorted(parsed.items())) if parsed else "_"


def _parse_kv_field(value: str) -> dict[str, str]:
    if not value or value == "_":
        return {}
    result = {}
    for item in value.split("|"):
        if "=" in item:
            key, val = item.split("=", 1)
            result[key] = val
    return result


def enrich_conllu_text(text: str, inventory: Optional[dict[str, Any]] = None) -> tuple[str, dict[str, int]]:
    """Move tentative NumClass from MISC and infer missing features in CoNLL-U.

    Multiword-token range rows are left alone; their syntactic component rows
    receive features. Any old ``MISC NumClass`` is removed, including on nouns;
    it is copied into FEATS only for DET/PRON/VERB/AUX rows.
    """
    counts = {"rows_seen": 0, "numclass_added": 0, "numclass_moved": 0, "numclass_removed_from_misc": 0, "et_rows_enriched": 0}
    output_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        bare = line.rstrip("\r\n")
        newline = line[len(bare):]
        if not bare or bare.startswith("#"):
            output_lines.append(line)
            continue
        cols = bare.split("\t")
        if len(cols) != 10 or not re.fullmatch(r"\d+", cols[0]):
            output_lines.append(line)
            continue
        counts["rows_seen"] += 1
        misc = _parse_kv_field(cols[9])
        misc_numclass = misc.pop("NumClass", None)
        if misc_numclass is not None:
            counts["numclass_removed_from_misc"] += 1
        target = cols[3] in (D_UPOS | ET_UPOS)
        original = cols[5]
        if misc_numclass and target:
            feats = _parse_kv_field(original)
            if "NumClass" not in feats:
                feats["NumClass"] = misc_numclass
                counts["numclass_moved"] += 1
            original = "|".join("%s=%s" % item for item in sorted(feats.items())) if feats else "_"
        cols[5] = add_features(original, cols[1], cols[2], cols[3], cols[4], inventory=inventory)
        after_feats = _parse_kv_field(cols[5])
        before_feats = _parse_kv_field(original)
        if "NumClass" not in before_feats and "NumClass" in after_feats:
            counts["numclass_added"] += 1
        if cols[3] in ET_UPOS and analyze_token(cols[1], cols[2], cols[3], cols[4], inventory=inventory)["is_et_verb"]:
            counts["et_rows_enriched"] += 1
        cols[9] = "|".join("%s=%s" % item for item in sorted(misc.items())) if misc else "_"
        output_lines.append("\t".join(cols) + newline)
    return "".join(output_lines), counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich CoNLL-U with NumClass and *et* incorporation features")
    parser.add_argument("conllu", type=Path, help="Input CoNLL-U")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Write enriched copy here")
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    args = parser.parse_args()
    if not args.conllu.is_file():
        parser.error("CoNLL-U file not found: %s" % args.conllu)
    text = args.conllu.read_text(encoding="utf-8")
    inventory = load_inventory(args.inventory)
    result, counts = enrich_conllu_text(text, inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print("Wrote %s; %s" % (args.output, ", ".join("%s=%s" % x for x in counts.items())), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
