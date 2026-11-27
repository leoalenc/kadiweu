#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract *et* stative-verb entries and listed forms from the TBP JSON lexicon.

Uses the existing ``KadiweuLexicon`` reader from
``kadiweu_lexicon_explorer.py``. It selects entries whose first morpheme is
``et`` tagged ``v`` (rather than every word that happens to begin with et),
then exports headwords, variants, morpheme analyses, and conjugation forms.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from kadiweu_lexicon_explorer import KadiweuLexicon  # existing project utility


def is_et_stative_entry(entry: dict[str, Any]) -> bool:
    morphemes = entry.get("morphemes")
    if not isinstance(morphemes, list) or not morphemes:
        return False
    first = morphemes[0] if isinstance(morphemes[0], dict) else {}
    return str(first.get("name", "")).casefold() == "et" and str(first.get("tag", "")).casefold() == "v"


def extract(path: Path) -> dict[str, Any]:
    lexicon = KadiweuLexicon(path)
    # Reuse the explorer's tag index/filter, then retain only the morphologically
    # identified stative-verb entries. This includes incomplete and TODO records.
    candidates: dict[str, dict[str, Any]] = {}
    for tag in ("VB", "VBI", "VBT", "VBAPL", "VBTAPL"):
        for entry in lexicon.search_by_tag(tag):
            if not is_et_stative_entry(entry):
                continue
            uid = str(entry.get("uid") or entry.get("name") or id(entry))
            record = {
                "form": str(entry.get("name", "")),
                "entry_name": str(entry.get("name", "")),
                "tag": entry.get("tag"),
                "grammar": entry.get("grammar"),
                "definition": entry.get("definition"),
                "senses": entry.get("senses", []),
                "morphemes": entry.get("morphemes", []),
                "variants": entry.get("variants", []),
                "conjugations": entry.get("conjugations", []),
                "lexicon_status": entry.get("status"),
                "lexicon": entry.get("lexicon"),
                "uid": entry.get("uid"),
                "copyright": entry.get("copyright"),
                "review_status": "source_entry",
            }
            candidates[uid] = record

    records: list[dict[str, Any]] = []
    for entry in candidates.values():
        records.append({"record_type": "headword", **entry})
        variants = entry.get("variants")
        if isinstance(variants, list):
            for variant in variants:
                if isinstance(variant, str):
                    form = variant
                    metadata: dict[str, Any] = {}
                elif isinstance(variant, dict):
                    form = variant.get("name") or variant.get("form") or variant.get("value")
                    metadata = variant
                else:
                    continue
                if form:
                    records.append({
                        "record_type": "variant", "form": str(form),
                        "entry_name": entry["entry_name"], "entry_uid": entry["uid"],
                        "variant_metadata": metadata, "morphemes": entry["morphemes"],
                        "review_status": "source_variant",
                    })
        paradigms = entry.get("conjugations")
        if isinstance(paradigms, list):
            for pi, paradigm in enumerate(paradigms):
                values = paradigm.get("values", []) if isinstance(paradigm, dict) else []
                if not isinstance(values, list):
                    continue
                for vi, value in enumerate(values):
                    if value:
                        records.append({
                            "record_type": "conjugation_form", "form": str(value),
                            "entry_name": entry["entry_name"], "entry_uid": entry["uid"],
                            "paradigm_index": pi, "form_index": vi,
                            "transitivity": paradigm.get("transitivity") if isinstance(paradigm, dict) else None,
                            "paradigm_values": values,
                            # The entry segmentation belongs to its headword. Do
                            # not copy it to every paradigm form: e.g. etee is
                            # independently listed with a pronoun analysis and
                            # as a classifier form under etini.
                            "review_status": "paradigm_form",
                        })
    records.sort(key=lambda r: (str(r.get("form", "")).casefold(), r.get("record_type", "")))
    return {
        "schema_version": 1,
        "source": str(path),
        "extractor": "KadiweuLexicon from kadiweu_lexicon_explorer.py",
        "entry_count": len(candidates),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lexicon", type=Path, help="TBP-exported lexicon-kadiweu.json")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.lexicon.is_file():
        parser.error(f"lexicon file not found: {args.lexicon}")
    data = extract(args.lexicon)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {data['entry_count']} entries and {len(data['records'])} form records", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
