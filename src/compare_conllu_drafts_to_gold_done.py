#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Compare CoNLL-U drafts against only sentences marked DONE in gold.

The CoNLL-U parsing, UID alignment, token comparison, scoring, and report/CSV
writers are imported from ``compare_conllu_drafts_to_gold.py``. Drafts are not
filtered by their own review metadata: the DONE sentence inventory comes from
gold, and matching is by ``sent_uid``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from compare_conllu_drafts_to_gold import (
    compare_draft,
    index_gold_by_uid,
    make_markdown_report,
    parse_conllu,
    write_mismatch_csv,
    write_summary_csv,
)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare one or more draft CoNLL-U files against gold sentences "
            "whose ud_review_status is DONE."
        )
    )
    parser.add_argument("gold", type=Path, help="Gold CoNLL-U file.")
    parser.add_argument("drafts", type=Path, nargs="+", help="One or more draft files.")
    parser.add_argument(
        "--json",
        dest="json_paths",
        action="append",
        required=True,
        type=Path,
        help=(
            "TBP JSON source file used to identify DONE sentences. Repeat once "
            "for each source document."
        ),
    )
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path.")
    parser.add_argument("--csv-out", type=Path, help="Optional CSV summary path.")
    parser.add_argument(
        "--mismatch-csv-out",
        type=Path,
        help="Optional CSV path for token-count/token-ID mismatch details.",
    )
    return parser.parse_args(argv)


def load_done_uids(json_paths: Sequence[Path]):
    """Read the current DONE sentence UIDs and their source-file provenance."""
    done_uids = {}
    done_counts = {}
    for json_path in json_paths:
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read JSON source {json_path}: {exc}") from exc

        source_count = 0
        for page in data.get("pages", []):
            for sentence in page.get("sentences", []):
                if sentence.get("status") != "DONE":
                    continue
                source_count += 1
                uid = sentence.get("uid")
                if not uid:
                    raise ValueError(
                        f"DONE sentence without uid in {json_path} "
                        f"(page {page.get('order', '?')})"
                    )
                if uid in done_uids:
                    raise ValueError(
                        f"Duplicate DONE sentence UID {uid} in "
                        f"{done_uids[uid]} and {json_path}"
                    )
                done_uids[uid] = json_path.name
        done_counts[json_path.name] = source_count
    return done_uids, done_counts


def write_coverage_report(
    report: str,
    all_gold_sentences,
    json_done_uids,
    json_done_counts,
    gold_done_index,
    draft_paths: Sequence[Path],
) -> str:
    """Append JSON-DONE/gold intersection and per-draft coverage details."""
    lines = [report.rstrip(), "", "## DONE-sentence inventory and coverage", ""]
    lines.append(f"- Gold sentences read: {len(all_gold_sentences)}")
    lines.append(f"- JSON DONE sentences: {len(json_done_uids)}")
    for source_name, count in json_done_counts.items():
        lines.append(f"  - `{source_name}`: {count}")
    lines.append(f"- JSON DONE UIDs present in gold: {len(gold_done_index)}")
    missing_from_gold = sorted(set(json_done_uids) - set(
        sent.sent_uid for sent in all_gold_sentences if sent.sent_uid
    ))
    lines.append(f"- JSON DONE UIDs absent from gold: {len(missing_from_gold)}")
    if missing_from_gold:
        lines.append("- DONE sentences absent from gold: " + ", ".join(
            f"`{uid}` ({json_done_uids[uid]})" for uid in missing_from_gold
        ))

    for draft_path in draft_paths:
        draft_sentences = parse_conllu(draft_path)
        draft_uids = [s.sent_uid for s in draft_sentences if s.sent_uid]
        draft_uid_set = set(draft_uids)
        missing = sorted(
            (uid for uid in gold_done_index if uid not in draft_uid_set),
            key=lambda uid: gold_done_index[uid].sent_id,
        )
        unique_draft_uids = set(draft_uids)
        outside_done = unique_draft_uids - set(gold_done_index)
        lines.append("")
        lines.append(f"### `{draft_path.name}`")
        lines.append("")
        lines.append(f"- Draft sentences read: {len(draft_sentences)}")
        lines.append(f"- Draft UIDs matched to DONE gold: {len(set(gold_done_index) & unique_draft_uids)}")
        lines.append(f"- Draft UIDs outside the DONE gold inventory (excluded): {len(outside_done)}")
        lines.append(f"- DONE gold UIDs missing from the draft: {len(missing)}")
        if missing:
            lines.append("- Missing DONE gold sentences: " + ", ".join(
                f"`{gold_done_index[uid].sent_id}` ({uid})" for uid in missing
            ))

    lines.append("")
    lines.append(
        "DONE status is taken from the current TBP JSON sentence records, not from "
        "optional `ud_review_status` comments in CoNLL-U. JSON DONE sentences are "
        "intersected with the gold inventory by `sent_uid`; only that intersection "
        "enters the scores."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    try:
        all_gold_sentences = parse_conllu(args.gold)
        json_done_uids, json_done_counts = load_done_uids(args.json_paths)
        all_gold_index = index_gold_by_uid(all_gold_sentences)
        gold_done_index = {
            uid: sent for uid, sent in all_gold_index.items() if uid in json_done_uids
        }
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not gold_done_index:
        print(
            "ERROR: no JSON DONE sentence UIDs were found in the gold file.",
            file=sys.stderr,
        )
        return 2

    stats_list = []
    for draft_path in args.drafts:
        try:
            stats_list.append(
                compare_draft(gold_done_index, len(gold_done_index), draft_path)
            )
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    report = make_markdown_report(stats_list)
    report = report.replace(
        "# CoNLL-U draft accuracy against gold",
        "# CoNLL-U draft accuracy against DONE gold sentences",
        1,
    )
    report = write_coverage_report(
        report,
        all_gold_sentences,
        json_done_uids,
        json_done_counts,
        gold_done_index,
        args.drafts,
    )
    print(report)

    for output_path in (args.markdown_out, args.csv_out, args.mismatch_csv_out):
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.markdown_out:
        args.markdown_out.write_text(report, encoding="utf-8")
        print(f"Wrote Markdown report: {args.markdown_out}", file=sys.stderr)
    if args.csv_out:
        write_summary_csv(stats_list, args.csv_out)
        print(f"Wrote CSV summary: {args.csv_out}", file=sys.stderr)
    if args.mismatch_csv_out:
        write_mismatch_csv(stats_list, args.mismatch_csv_out)
        print(f"Wrote mismatch CSV: {args.mismatch_csv_out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
