#!/usr/bin/env python3
"""Find complete lexicon records that may belong to a lexical paradigm.

This tool does not assume that every form occurs as a record name. It can:
  * match one or more seed forms against record names;
  * search names for one or more supplied stem/allomorph strings;
  * find seed forms inside nominalParadigms/conjugations fields;
  * optionally follow related-entry UID links.

Stem matches are candidates, not proof of paradigm membership. Review the
printed report before treating the extracted records as one paradigm.
"""

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path


PARADIGM_FIELDS = ("nominalParadigms", "conjugations")


def norm(text: str) -> str:
    """Normalize Unicode and the spelling alternation G ~ ǥ."""
    return unicodedata.normalize("NFC", text).replace("ǥ", "G")


def strings_in(value):
    """Yield all strings nested in a JSON value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from strings_in(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from strings_in(nested)


def stored_forms(field, value):
    """Yield form values only, excluding paradigm metadata such as transitivity."""
    if field in ("nominalParadigms", "conjugations"):
        groups = value if isinstance(value, list) else [value]
        for group in groups:
            if isinstance(group, dict) and "values" in group:
                yield from strings_in(group["values"])
            elif isinstance(group, list):
                yield from strings_in(group)
    else:
        yield from strings_in(value)


def meaning_text(record):
    """Collect definition/gloss text for the optional meaning filter."""
    pieces = []
    for key in ("definition", "attributes", "senses"):
        pieces.extend(strings_in(record.get(key)))
    return " ".join(pieces).casefold()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("lexicon", type=Path, help="Lexicon JSON file")
    ap.add_argument(
        "--seed", nargs="+", required=True,
        help="Known form(s), e.g. yacilo; a seed may occur inside a paradigm field",
    )
    ap.add_argument(
        "--stem", nargs="*", default=[],
        help="Known stem spelling(s) or allomorph(s) to search for in record names",
    )
    ap.add_argument(
        "--meaning-contains",
        help="Optional substring filter for definitions/glosses, e.g. cabeça",
    )
    ap.add_argument(
        "--match-mode", choices=("any", "all"), default="any",
        help=(
            "Combine discovery criteria with OR ('any', default) or use the "
            "previous stricter stem/seed AND meaning behavior ('all')."
        ),
    )
    ap.add_argument(
        "--follow-related", action="store_true",
        help="Also include records explicitly referenced through related.entry UIDs",
    )
    ap.add_argument(
        "--output", type=Path, default=Path("paradigm_candidates.json"),
        help="Output JSON file (default: paradigm_candidates.json)",
    )
    ap.add_argument(
        "--tsv-output", type=Path,
        help="TSV report path (default: same path as --output with a .tsv suffix)",
    )
    args = ap.parse_args()

    records = json.loads(args.lexicon.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        ap.error("The input JSON must contain a list of records.")

    seed_keys = {norm(s) for s in args.seed}
    stem_keys = {norm(s) for s in args.stem if s}
    uid_to_index = {
        rec["uid"]: i for i, rec in enumerate(records)
        if isinstance(rec.get("uid"), str)
    }
    reasons = {}

    def add(i, reason):
        reasons.setdefault(i, set()).add(reason)

    # Exact form matches, including G/ǥ spelling variants.
    for i, rec in enumerate(records):
        name = rec.get("name")
        if isinstance(name, str) and norm(name) in seed_keys:
            add(i, "seed-name")

        # Stem matching is deliberately reported as candidate evidence.
        if isinstance(name, str):
            nname = norm(name)
            for stem in stem_keys:
                if stem in nname:
                    add(i, f"name-contains-stem:{stem}")

        # Some forms are listed in a paradigm field, not as record names.
        for field in PARADIGM_FIELDS:
            if field not in rec:
                continue
            for form in stored_forms(field, rec[field]):
                if norm(form) in seed_keys:
                    add(i, f"seed-in-{field}")
                for stem in stem_keys:
                    if stem in norm(form):
                        add(i, f"{field}-contains-stem:{stem}")

        # A plural or variant spelling may be stored outside the main paradigm
        # fields. Treat these as candidate evidence too.
        for field in ("plurals", "variants", "variantList"):
            for form in stored_forms(field, rec.get(field)):
                if norm(form) in seed_keys:
                    add(i, f"seed-in-{field}")
                for stem in stem_keys:
                    if stem in norm(form):
                        add(i, f"{field}-contains-stem:{stem}")

        if args.meaning_contains and args.meaning_contains.casefold() in meaning_text(rec):
            add(i, f"definition-or-gloss-contains:{args.meaning_contains}")

    # Optional explicit link traversal. Kept opt-in because related links can
    # point to semantically related records rather than paradigm members.
    if args.follow_related:
        queue = list(reasons)
        seen = set(queue)
        while queue:
            i = queue.pop()
            for link in records[i].get("related") or []:
                if not isinstance(link, dict):
                    continue
                target = uid_to_index.get(link.get("entry"))
                if target is not None:
                    add(target, f"related-from:{records[i].get('name', i)}")
                    if target not in seen:
                        seen.add(target)
                        queue.append(target)

    selected = sorted(reasons)
    if args.match_mode == "all" and args.meaning_contains:
        # Strict mode: require a seed/stem signal and a matching definition.
        meaning_reason = f"definition-or-gloss-contains:{args.meaning_contains}"
        selected = [
            i for i in selected
            if meaning_reason in reasons[i]
            and any(
                reason == "seed-name"
                or reason.startswith("name-contains-stem:")
                or reason.startswith("seed-in-")
                or "-contains-stem:" in reason
                for reason in reasons[i]
            )
        ]

    if not selected:
        ap.error(
            "No records matched. Check the spelling, add known stem allomorphs "
            "with --stem, or remove --meaning-contains."
        )

    # Complete source records are preserved; only JSON whitespace is changed.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps([records[i] for i in selected], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Build the TSV from the JSON just written, so both outputs describe the
    # same selected source records. Each row is a record name or a value stored
    # in a field that can contain paradigm forms.
    generated_records = json.loads(args.output.read_text(encoding="utf-8"))
    tsv_path = args.tsv_output or args.output.with_suffix(".tsv")
    tsv_path.parent.mkdir(parents=True, exist_ok=True)
    form_fields = ("nominalParadigms", "conjugations", "plurals", "variants", "variantList")

    with tsv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow((
            "candidate_form_or_value",
            "occurrence_type",
            "source_record_name",
            "source_record_uid",
            "source_field",
            "inclusion_reasons",
        ))
        for record in generated_records:
            record_name = record.get("name", "")
            uid = record.get("uid", "")
            row_reasons = set()
            for i, original in enumerate(records):
                if original.get("uid") == uid:
                    row_reasons.update(reasons.get(i, set()))
                    break

            writer.writerow((
                record_name,
                "record_name",
                record_name,
                uid,
                "name",
                "; ".join(sorted(row_reasons)),
            ))

            for field in form_fields:
                for value in stored_forms(field, record.get(field)):
                    # The current lexicon contains nominalParadigms placeholders
                    # such as teste1...teste6; report actual stored forms only.
                    if field == "nominalParadigms" and re.fullmatch(
                        r"(?:teste|test)\d+", value.strip(), flags=re.IGNORECASE
                    ):
                        continue
                    value_reasons = {f"stored_in_field:{field}"}
                    if norm(value) in seed_keys:
                        value_reasons.add("exact_seed_form_occurs_in_record")
                    for stem in stem_keys:
                        if stem in norm(value):
                            value_reasons.add(f"form_value_contains_stem:{stem}")
                    if args.meaning_contains and args.meaning_contains.casefold() in meaning_text(record):
                        value_reasons.add(
                            f"source_record_definition-or-gloss-contains:{args.meaning_contains}"
                        )
                    # Record selection reasons explain why this form's parent
                    # record was included; field reason explains where the
                    # candidate value itself was found.
                    for i, original in enumerate(records):
                        if original.get("uid") == uid:
                            value_reasons.update(
                                f"source_record:{reason}" for reason in reasons.get(i, set())
                            )
                            break
                    writer.writerow((
                        value,
                        "inside_record",
                        record_name,
                        uid,
                        field,
                        "; ".join(sorted(value_reasons)),
                    ))

    print(f"Found {len(selected)} candidate record(s):")
    for i in selected:
        print(f"  {records[i].get('name', '<unnamed>')}: {', '.join(sorted(reasons[i]))}")
    print(f"Full records written to: {args.output}")
    print(f"Candidate-form TSV written to: {tsv_path}")
    print("Review candidates: a matching criterion identifies candidates; it does not by itself establish paradigm membership.")


if __name__ == "__main__":
    main()
