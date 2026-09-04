#!/usr/bin/env python3
"""Inspect and annotate Kadiwéu CorpusSearch/Penn PSD constituency trees.

This is the PSD-facing command-line companion to ``kadiweu_constituency.py``.
It deliberately keeps rendering in the library module so JSON-derived and
PSD-derived trees share the same tree object and the same text and Graphviz
renderers.

Examples
--------
Show the fifth PSD record in a terminal::

    python3 kadiweu_psd_tree.py show data/example.psd 5

Show the third REVIEW record::

    python3 kadiweu_psd_tree.py show data/example.psd --status REVIEW 3

Show a tree by CorpusSearch ID::

    python3 kadiweu_psd_tree.py show data/example.psd --id hil-data,0.5

Create a review copy with an ASCII tree in every metadata comment::

    python3 kadiweu_psd_tree.py inject data/example.psd \\
        -o data/example.with-trees.psd --style ascii

Annotate only REVIEW records::

    python3 kadiweu_psd_tree.py inject data/example.psd \\
        -o data/example.review-trees.psd --status REVIEW

Export one PSD tree as a printable PDF (Graphviz required)::

    python3 kadiweu_psd_tree.py export data/example.psd \\
        --id van-data,0.43 --format pdf -o van-data-0.43.pdf

The ``inject`` operation does not reserialize the Lisp tree. It modifies only
the preceding ``/* ... */`` metadata comment, so the parse itself and its trace
notation remain byte-for-byte unchanged.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence

from kadiweu_constituency import (
    PsdRecord,
    TreeConstructionError,
    iter_psd_records,
    render_tree_graphviz,
    render_tree_text,
)

BEGIN_RE = re.compile(r"^tree_display_begin\s*=.*$", re.MULTILINE)
TREE_BLOCK_RE = re.compile(
    r"\ntree_display_begin\s*=.*?\ntree_display_end\s*=\s*true\s*\n?",
    re.DOTALL,
)


def select_records(
    records: Sequence[PsdRecord],
    *,
    numbers: Sequence[int] | None = None,
    uids: Sequence[str] | None = None,
    ids: Sequence[str] | None = None,
    statuses: Sequence[str] | None = None,
) -> list[tuple[int, PsdRecord]]:
    """Select records, applying status before ordinal NUMBER selection.

    NUMBER/--number is 1-based within the status-filtered set. Thus
    ``--status REVIEW 3`` means the third REVIEW record. Without --status,
    NUMBER refers to file order.
    """
    indexed = list(enumerate(records, start=1))
    wanted_statuses = set(statuses or ())
    if wanted_statuses:
        indexed = [
            (absolute_number, record)
            for absolute_number, record in indexed
            if record.tree.status in wanted_statuses
        ]

    wanted_uids = set(uids or ())
    wanted_ids = set(ids or ())
    if wanted_uids or wanted_ids:
        indexed = [
            (absolute_number, record)
            for absolute_number, record in indexed
            if record.tree.sentence_uid in wanted_uids
            or record.corpussearch_id in wanted_ids
        ]

    if numbers:
        selected = []
        for n in numbers:
            if n < 1 or n > len(indexed):
                raise ValueError(
                    f"record number {n} is outside the current selection "
                    f"(1..{len(indexed)})"
                )
            selected.append(indexed[n - 1])
        return selected

    return indexed


def render_record(record: PsdRecord, *, style: str, show_spans: bool, show_positions: bool) -> str:
    """Render one record with a compact human-readable heading."""
    heading = []
    if record.tree.sentence_number is not None:
        heading.append(f"sentence = {record.tree.sentence_number}")
    if record.corpussearch_id:
        heading.append(f"id = {record.corpussearch_id}")
    if record.tree.sentence_uid:
        heading.append(f"uid = {record.tree.sentence_uid}")
    if record.tree.status:
        heading.append(f"status = {record.tree.status}")
    if record.tree.text:
        heading.append(f"text = {record.tree.text}")
    if record.tree.text_por:
        heading.append(f"text_por = {record.tree.text_por}")
    tree = render_tree_text(
        record.tree,
        style=style,
        show_spans=show_spans,
        show_positions=show_positions,
    )
    return "\n".join(f"# {line}" for line in heading) + "\n" + tree


def tree_comment_block(record: PsdRecord, *, style: str, show_spans: bool, show_positions: bool) -> str:
    """Return the idempotent tree-display block inserted in a PSD comment."""
    tree = render_tree_text(
        record.tree,
        style=style,
        show_spans=show_spans,
        show_positions=show_positions,
    )
    return f"tree_display_begin = {style}\n{tree}\ntree_display_end = true"


def update_comment(comment: str, block: str) -> str:
    """Add or replace our generated tree block inside one ``/* ... */`` comment."""
    if not comment.startswith("/*") or not comment.endswith("*/"):
        raise TreeConstructionError("expected a complete PSD block comment")
    body = comment[2:-2]
    body = TREE_BLOCK_RE.sub("\n", body).rstrip()
    if body:
        body += "\n"
    body += block + "\n"
    return "/*" + body + "*/"


def inject_tree_comments(
    text: str,
    records: Sequence[PsdRecord],
    selected_ordinals: set[int],
    *,
    style: str,
    show_spans: bool,
    show_positions: bool,
) -> str:
    """Inject displays while preserving every syntactic record verbatim."""
    # Locate comments that immediately precede top-level records. The parser and
    # this replacement pass advance through the same record order.
    pieces: list[str] = []
    cursor = 0
    scan = 0
    ordinal = 0
    n = len(text)

    while scan < n:
        comment_start = text.find("/*", scan)
        record_start = text.find("(", scan)
        if record_start < 0:
            break
        if comment_start >= 0 and comment_start < record_start:
            comment_end = text.find("*/", comment_start + 2)
            if comment_end < 0:
                raise TreeConstructionError("unclosed block comment")
            after_comment = comment_end + 2
            candidate_record = text.find("(", after_comment)
            if candidate_record < 0:
                break
            # Only regard this as the record metadata comment if no other
            # non-whitespace material occurs before the record.
            if text[after_comment:candidate_record].strip():
                scan = after_comment
                continue
            ordinal += 1
            if ordinal > len(records):
                raise TreeConstructionError("record/comment count mismatch")
            if ordinal in selected_ordinals:
                record = records[ordinal - 1]
                block = tree_comment_block(
                    record,
                    style=style,
                    show_spans=show_spans,
                    show_positions=show_positions,
                )
                replacement = update_comment(text[comment_start:after_comment], block)
                pieces.append(text[cursor:comment_start])
                pieces.append(replacement)
                cursor = after_comment
            scan = candidate_record + 1
        else:
            # A record without a metadata comment is allowed for display, but
            # injection intentionally does not invent a new comment here.
            scan = record_start + 1

    pieces.append(text[cursor:])
    if ordinal != len(records):
        # Project PSDs currently have one metadata comment per record. Refuse a
        # silent partial rewrite if that invariant changes.
        raise TreeConstructionError(
            f"found {len(records)} PSD records but {ordinal} metadata comments"
        )
    return "".join(pieces)


def add_selectors(parser: argparse.ArgumentParser) -> None:
    # Use repeatable single-value options rather than nargs="+".  A greedy
    # nargs option placed before FILE consumes the file name as another value,
    # making natural commands such as ``show --uid UID FILE.psd`` fail with
    # "the following arguments are required: FILE".
    parser.add_argument(
        "--number", type=int, action="append", metavar="N",
        help=("1-based record number within the current selection; repeat "
              "--number to select more than one"),
    )
    parser.add_argument(
        "--uid", action="append", metavar="UID",
        help="sentence UID; repeat --uid to select more than one",
    )
    parser.add_argument(
        "--id", dest="ids", action="append", metavar="ID",
        help="CorpusSearch ID, e.g. van-data,0.38; repeat --id to select more than one",
    )
    parser.add_argument(
        "--status", dest="statuses", action="append", metavar="STATUS",
        help="filter by status, e.g. REVIEW or DONE; repeat --status for more than one",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect and annotate Kadiwéu CorpusSearch/Penn PSD constituency trees.",
        epilog=("Use `%(prog)s show --help`, `%(prog)s inject --help`, or "
                "`%(prog)s export --help` for command-specific examples."),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser(
        "show",
        help="display selected PSD trees in the terminal",
        description=("Display PSD constituency trees as readable text. NUMBER is 1-based. "
                     "When --status is present, NUMBER is counted within that filtered set."),
        epilog="""examples:
  %(prog)s FILE.psd 2
      Show the second record in the file.

  %(prog)s FILE.psd --status REVIEW 3
      Show the third REVIEW record.

  %(prog)s FILE.psd --status REVIEW --number 3
      Equivalent explicit form.

  %(prog)s FILE.psd --id hil-data,0.5
      Select by CorpusSearch ID.

  %(prog)s --uid 5739aca1-95fc-4584-9550-d7bd73c3c361 FILE.psd
      Select by UID with the option before the file path.

  %(prog)s FILE.psd --uid UID1 --uid UID2
      Select more than one UID by repeating the option.

  %(prog)s FILE.psd --status REVIEW
      Show all REVIEW records.

  %(prog)s FILE.psd 2 --style ascii
      Render the second record using portable ASCII.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    show.add_argument("psd_file", type=Path, metavar="FILE")
    show.add_argument("positional_number", type=int, nargs="?", metavar="NUMBER",
                      help="1-based record number; after --status filtering if supplied")
    add_selectors(show)
    show.add_argument("--style", choices=("unicode", "ascii"), default="unicode")
    show.add_argument("--show-spans", action="store_true", help="show constituent token spans")
    show.add_argument("--show-positions", action="store_true", help="show token positions")

    inject = sub.add_parser(
        "inject",
        help="insert text trees into existing PSD metadata comments",
        description=("Insert rendered trees into PSD metadata comments without reserializing "
                     "or otherwise changing the Lisp parse."),
        epilog="""examples:
  %(prog)s FILE.psd -o FILE.with-trees.psd
      Inject ASCII displays into all records.

  %(prog)s FILE.psd -o review.psd --status REVIEW
      Inject displays only into REVIEW records.

  %(prog)s FILE.psd -o one.psd --status REVIEW --number 3
      Inject a display only into the third REVIEW record.

  %(prog)s FILE.psd --in-place --status REVIEW
      Modify the input file itself. Use deliberately.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    inject.add_argument("psd_file", type=Path, metavar="FILE")
    add_selectors(inject)
    inject.add_argument("--style", choices=("unicode", "ascii"), default="ascii")
    inject.add_argument("--show-spans", action="store_true", help="show constituent token spans")
    inject.add_argument("--show-positions", action="store_true", help="show token positions")
    destination = inject.add_mutually_exclusive_group(required=True)
    destination.add_argument("-o", "--output", type=Path, help="write annotated copy to this file")
    destination.add_argument("--in-place", action="store_true",
                             help="replace the input file atomically (destructive)")

    export = sub.add_parser(
        "export",
        help="export one PSD tree graphically with Graphviz",
        description=("Export one selected PSD constituency tree as PDF, PNG, SVG, "
                     "or Graphviz DOT. PDF is the default."),
        epilog="""examples:
  %(prog)s FILE.psd --id van-data,0.43 -o van-data-0.43.pdf
      Export one tree to printable PDF.

  %(prog)s FILE.psd --status REVIEW 3 --format png -o review-3.png
      Export the third REVIEW tree as PNG.

  %(prog)s FILE.psd --id van-data,0.43 --format dot -o tree.dot
      Write DOT source without invoking Graphviz.

  %(prog)s FILE.psd --id van-data,0.43 --comments -o tree.pdf
      Print the PSD metadata comment above the graphical tree.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    export.add_argument("psd_file", type=Path, metavar="FILE")
    export.add_argument("positional_number", type=int, nargs="?", metavar="NUMBER",
                        help="1-based record number; after --status filtering if supplied")
    add_selectors(export)
    export.add_argument(
        "--format", choices=("pdf", "png", "svg", "dot"), default="pdf",
        help="graphical output format (default: pdf)",
    )
    export.add_argument("-o", "--output", type=Path, required=True,
                        help="output file")
    export.add_argument(
        "--no-boxes", action="store_true",
        help="draw constituent labels without enclosing boxes",
    )
    export.add_argument(
        "--comments", action="store_true",
        help="print everything inside the PSD /* ... */ comment above the tree",
    )
    export.add_argument(
        "--dot-command", default="dot", metavar="COMMAND",
        help="Graphviz dot executable (default: dot)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        records = list(iter_psd_records(args.psd_file))
        numbers = args.number
        if args.command in {"show", "export"} and args.positional_number is not None:
            if args.number:
                raise ValueError("use either positional NUMBER or --number, not both")
            numbers = [args.positional_number]
        selected = select_records(
            records,
            numbers=numbers,
            uids=args.uid,
            ids=args.ids,
            statuses=args.statuses,
        )
        if not selected:
            raise ValueError("selection contains no PSD trees")

        if args.command == "show":
            for i, (_, record) in enumerate(selected):
                if i:
                    print()
                print(render_record(
                    record,
                    style=args.style,
                    show_spans=args.show_spans,
                    show_positions=args.show_positions,
                ))
            return 0

        if args.command == "export":
            if len(selected) != 1:
                raise ValueError(
                    f"export requires exactly one PSD tree; selection contains {len(selected)}"
                )
            render_tree_graphviz(
                selected[0][1].tree,
                args.output,
                output_format=args.format,
                no_boxes=args.no_boxes,
                dot_command=args.dot_command,
                comments=(
                    selected[0][1].raw_comment[2:-2]
                    if args.comments and selected[0][1].raw_comment is not None
                    else None
                ),
            )
            print(args.output)
            return 0

        original = args.psd_file.read_text(encoding="utf-8")
        output_text = inject_tree_comments(
            original,
            records,
            {number for number, _ in selected},
            style=args.style,
            show_spans=args.show_spans,
            show_positions=args.show_positions,
        )
        if args.in_place:
            temp = args.psd_file.with_name(args.psd_file.name + ".tmp-treeview")
            with temp.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(output_text)
            os.replace(temp, args.psd_file)
            print(args.psd_file)
        else:
            if args.output.resolve() == args.psd_file.resolve():
                raise ValueError("use --in-place to replace the input file")
            with args.output.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(output_text)
            print(args.output)
        return 0
    except (OSError, TreeConstructionError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
