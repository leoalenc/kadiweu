#!/usr/bin/env python3
"""Compute reproducible inventory and duplication statistics for the Kadiwéu lexicon.

Usage:
    python3 kadiweu_lexicon_stats.py ../data/lexicon-kadiweu.json
    python3 kadiweu_lexicon_stats.py ../data/lexicon-kadiweu.json --reports stats_reports

The script is intentionally standalone. It reads the source JSON without
modifying it and writes a JSON summary to stdout. With --reports, it also
writes TSV files listing repeated exact names and entries with morpheme data.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


# These fields identify records or record history rather than lexical content.
# They are ignored only for the optional "same content apart from IDs/history"
# comparison; the source JSON itself is never changed.
IDENTITY_AND_AUDIT_FIELDS = {
    "_id", "uid", "createdAt", "createdBy", "modifiedAt", "modifiedBy",
}


def canonical(value: Any) -> str:
    """Stable JSON representation for comparing field values."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def populated(value: Any) -> bool:
    """Whether a JSON field contains meaningful nonempty data."""
    return value is not None and value != "" and value != [] and value != {}


def meanings_signature(entry: dict[str, Any]) -> str:
    """Compare definitions and sense lists together, preserving their content."""
    return canonical({"definition": entry.get("definition"), "senses": entry.get("senses")})


def analyze(entries: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing_name = 0
    for entry in entries:
        name = entry.get("name")
        if isinstance(name, str) and name != "":
            # Exact string comparison: case, diacritics, whitespace, and
            # characters such as G/g/ǥ are preserved.
            by_name[name].append(entry)
        else:
            missing_name += 1

    repeated = {name: group for name, group in by_name.items() if len(group) > 1}
    entries_in_repeated_groups = sum(len(group) for group in repeated.values())
    excess_entries = sum(len(group) - 1 for group in repeated.values())

    groups_with_multiple_tags = 0
    groups_with_multiple_meaning_signatures = 0
    groups_with_multiple_tag_and_meaning_combinations = 0
    groups_with_redundant_content_records = 0
    total_redundant_content_pairs = 0

    for group in repeated.values():
        tags = {canonical(entry.get("tag")) for entry in group}
        meanings = {meanings_signature(entry) for entry in group}
        tag_meaning_pairs = {
            canonical({"tag": entry.get("tag"), "meanings": json.loads(meanings_signature(entry))})
            for entry in group
        }
        if len(tags) > 1:
            groups_with_multiple_tags += 1
        if len(meanings) > 1:
            groups_with_multiple_meaning_signatures += 1
        if len(tag_meaning_pairs) > 1:
            groups_with_multiple_tag_and_meaning_combinations += 1

        content_records = [
            canonical({k: v for k, v in entry.items() if k not in IDENTITY_AND_AUDIT_FIELDS})
            for entry in group
        ]
        counts: dict[str, int] = defaultdict(int)
        for record in content_records:
            counts[record] += 1
        pair_count = sum(n * (n - 1) // 2 for n in counts.values())
        if pair_count:
            groups_with_redundant_content_records += 1
            total_redundant_content_pairs += pair_count

    with_morpheme_field = sum("morphemes" in entry for entry in entries)
    with_populated_morphemes = sum(populated(entry.get("morphemes")) for entry in entries)

    summary = {
        "source_entry_count": len(entries),
        "entries_with_nonempty_name": sum(len(group) for group in by_name.values()),
        "entries_missing_or_empty_name": missing_name,
        "distinct_exact_name_strings": len(by_name),
        "repeated_exact_name_strings": len(repeated),
        "entries_in_repeated_name_groups": entries_in_repeated_groups,
        "extra_entries_beyond_one_per_name": excess_entries,
        "repeated_name_groups_with_multiple_tags": groups_with_multiple_tags,
        "repeated_name_groups_with_multiple_definition_or_sense_signatures": groups_with_multiple_meaning_signatures,
        "repeated_name_groups_with_multiple_tag_and_meaning_combinations": groups_with_multiple_tag_and_meaning_combinations,
        "repeated_name_groups_with_redundant_content_records": groups_with_redundant_content_records,
        "redundant_content_record_pairs": total_redundant_content_pairs,
        "entries_with_morphemes_field": with_morpheme_field,
        "entries_with_nonempty_morphemes": with_populated_morphemes,
        "entries_with_empty_or_null_morphemes": with_morpheme_field - with_populated_morphemes,
    }
    return summary, repeated


def write_reports(report_dir: Path, repeated: dict[str, list[dict[str, Any]]], entries: list[dict[str, Any]]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    with (report_dir / "repeated_names.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["name", "group_size", "uid", "tag", "grammar", "definition", "senses", "status"])
        for name in sorted(repeated):
            for entry in repeated[name]:
                writer.writerow([
                    name,
                    len(repeated[name]),
                    entry.get("uid", ""),
                    entry.get("tag", ""),
                    entry.get("grammar", ""),
                    entry.get("definition", ""),
                    canonical(entry.get("senses")),
                    entry.get("status", ""),
                ])

    with (report_dir / "morpheme_entries.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["name", "uid", "tag", "definition", "morphemes"])
        for entry in entries:
            if populated(entry.get("morphemes")):
                writer.writerow([
                    entry.get("name", ""), entry.get("uid", ""), entry.get("tag", ""),
                    entry.get("definition", ""), canonical(entry.get("morphemes")),
                ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path, help="Path to lexicon-kadiweu.json")
    parser.add_argument("--reports", type=Path, help="Optional directory for detailed TSV reports")
    args = parser.parse_args()

    with args.json_path.open("r", encoding="utf-8") as f:
        entries = json.load(f)
    if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
        parser.error("the JSON root must be a list of entry objects")

    summary, repeated = analyze(entries)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.reports:
        write_reports(args.reports, repeated, entries)
        print(f"\nDetailed TSV reports written to: {args.reports}")


if __name__ == "__main__":
    main()
