#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolidate dictionary and lexicon evidence into converter morphology JSON.

The output keeps source evidence and competing analyses instead of flattening
everything into the converter's general form-feature override table.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOTS = {
    "da": {"value": "Standing", "meaning": "standing / vertically extended"},
    "ni": {"value": "Sitting", "meaning": "sitting / non-extended"},
    "na": {"value": "Coming", "meaning": "coming / approaching"},
    "di": {"value": "Lying", "meaning": "lying / horizontally extended"},
    "jo": {"value": "Going", "meaning": "going away"},
    "ca": {"value": "Absent", "meaning": "absent / out of sight", "source_form": "ka"},
}


def canonical(form: Any) -> str:
    s = str(form or "").strip().translate(str.maketrans({"ǥ": "g", "Ɠ": "g", "ɡ": "g"})).casefold()
    return re.sub(r"\s+", "", s)


def read_records(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("records", []) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"Expected a JSON object with a records list: {path}")
    return [r for r in rows if isinstance(r, dict)]


def analysis_from_morphemes(record: dict[str, Any]) -> dict[str, Any] | None:
    morphs = record.get("morphemes")
    if not isinstance(morphs, list):
        return None
    features: dict[str, str] = {}
    segments = []
    root = None
    pronoun = None
    gender = None
    for morph in morphs:
        if not isinstance(morph, dict):
            continue
        name, tag = str(morph.get("name", "")), str(morph.get("tag", ""))
        segments.append({"form": name, "tag": tag})
        gloss = str((morph.get("attributes") or {}).get("gloss-br", "")).casefold()
        if tag.casefold() == "ncl":
            root = name.casefold()
        elif tag.casefold() == "gnr":
            gender = "Fem" if name.casefold() == "a" or "fem" in gloss else "Masc" if name.casefold() == "i" or "masc" in gloss else None
        elif tag.casefold() == "pro":
            pronoun = name.casefold()
    if root in ROOTS:
        features["NumClass"] = ROOTS[root]["value"]
    if gender:
        features["Gender"] = gender
    if pronoun in {"ee", "eeyo", "akaami", "akami", "oko"}:
        features["Person"] = "2" if pronoun in {"akaami", "akami"} else "1"
        features["Number"] = "Plur" if pronoun == "oko" else "Sing"
    if not segments:
        return None
    return {
        "segments": segments,
        "features": features,
        "analysis_type": "incorporated_classifier" if root in ROOTS else "incorporated_personal_pronoun" if pronoun else "morphological",
        "evidence": record.get("source", record.get("record_type", "source morpheme analysis")),
        "review_status": "attested_segmentation",
    }


def consolidate(griffiths: list[dict[str, Any]], lexicon: list[dict[str, Any]]) -> dict[str, Any]:
    by_form: dict[str, dict[str, Any]] = defaultdict(lambda: {"forms": [], "analyses": [], "sources": []})
    for source_name, rows in (("Griffiths 2002", griffiths), ("TBP JSON lexicon", lexicon)):
        for row in rows:
            form = str(row.get("form") or row.get("entry_name") or "").strip()
            if not form:
                continue
            key = canonical(form)
            bucket = by_form[key]
            if form not in bucket["forms"]:
                bucket["forms"].append(form)
            provenance = {"source": source_name}
            for k in ("source_file", "page_in_extracted_text", "context", "entry_name", "entry_uid", "uid", "tag", "grammar", "definition", "lexicon_status", "record_type", "review_status", "paradigm_index", "form_index"):
                if row.get(k) is not None:
                    provenance[k] = row[k]
            if provenance not in bucket["sources"]:
                bucket["sources"].append(provenance)
            # Only headwords and listed variants carry a direct segmentation.
            # Conjugation tables list surface forms, not necessarily analyses;
            # inheriting the headword's morphemes creates false homographic
            # analyses (notably etee as both a pronoun and a classifier form).
            analysis = analysis_from_morphemes(row) if row.get("record_type") in {"headword", "variant"} else None
            if analysis and analysis not in bucket["analyses"]:
                bucket["analyses"].append(analysis)

    forms = {}
    for key, value in sorted(by_form.items()):
        analyses = value["analyses"]
        features_set = {tuple(sorted(a.get("features", {}).items())) for a in analyses if a.get("features")}
        status = "attested_analysis" if len(features_set) == 1 and features_set else "needs_review" if len(features_set) > 1 else "form_only"
        forms[key] = {**value, "status": status}

    return {
        "schema_version": 1,
        "feature_values": ROOTS,
        "d_element_templates": {
            "gender_vowels": {"i": "Masc", "a": "Fem"},
            "classifier_roots": sorted(ROOTS),
            "forms": ["gender-vowel + root", "nG + gender-vowel + root", "reduced nG + gender-vowel + root"],
        },
        "et_verb_templates": {
            "classifier_agreement": "et + gender vowel + Ncl root",
            "personal_pronouns": {
                "ee": {"Person": "1", "Number": "Sing"},
                "eeyo": {"Person": "1", "Number": "Sing"},
                "akaami": {"Person": "2", "Number": "Sing"},
                "akami": {"Person": "2", "Number": "Sing", "status": "orthographic_variant_to_review"},
                "oko": {"Person": "1", "Number": "Plur"},
            },
        },
        "forms": forms,
        "provenance_note": "Source evidence is retained. Unsegmented dictionary/conjugation forms are not treated as confirmed analyses unless a productive fallback recognizes them.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--griffiths", type=Path, help="JSON output from extract_griffiths_et_forms.py")
    p.add_argument("--lexicon", type=Path, help="JSON output from extract_et_forms_from_lexicon.py")
    p.add_argument("-o", "--output", type=Path, required=True)
    args = p.parse_args()
    data = consolidate(read_records(args.griffiths), read_records(args.lexicon))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(data['forms'])} distinct normalized forms to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
