#!/usr/bin/env python3
"""Create a PDF-friendly Markdown report of DONE parser transitions.

The report includes every DONE improvement and regression found in a parser
transition TSV, with the corresponding BEFORE and AFTER PSD trees in both
LISP and graphical form. When a gold PSD is supplied, the report also includes
DONE persistent structural cases with GOLD, BEFORE, and AFTER trees.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence


@dataclass(frozen=True)
class PsdRecord:
    sentence_id: str
    metadata: dict[str, str]
    expression: list[object]
    tree: list[object]


TOKEN_RE = re.compile(r"\(|\)|[^\s()]+")
COMMENT_RE = re.compile(r"/\*(.*?)\*/", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract DONE improvements and regressions from a transition TSV "
            "and create a Markdown report with BEFORE/AFTER PSD trees. With "
            "--gold-psd, also include persistent structural cases."
        )
    )
    parser.add_argument("transitions", type=Path, help="parser transition TSV")
    parser.add_argument("before_psd", type=Path, help="BEFORE parser PSD")
    parser.add_argument("after_psd", type=Path, help="AFTER parser PSD")
    parser.add_argument(
        "--gold-psd",
        type=Path,
        help=(
            "gold PSD; when supplied, add DONE persistent structural cases "
            "with GOLD, BEFORE, and AFTER trees"
        ),
    )
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="output Markdown file"
    )
    parser.add_argument("--before-label", help="display label, e.g. A")
    parser.add_argument("--after-label", help="display label, e.g. C")
    parser.add_argument(
        "--gold-label", default="GOLD", help="gold-tree display label (default: GOLD)"
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        help="tree-image directory (default: OUTPUT stem plus .assets)",
    )
    parser.add_argument(
        "--image-format",
        choices=("svg", "png", "pdf"),
        default="svg",
        help="Graphviz output format (default: svg)",
    )
    parser.add_argument(
        "--title", default="DONE Parser Transition Report"
    )
    return parser.parse_args()


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"ERROR: {message}")


def require_file(path: Path) -> None:
    if not path.is_file():
        fail(f"required file not found: {path}")


def parse_metadata(comment: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in comment.splitlines():
        match = re.match(r"\s*([^=]+?)\s*=\s*(.*?)\s*$", line)
        if match:
            metadata[match.group(1).strip()] = match.group(2).strip()
    return metadata


def balanced_expression(text: str, start: int) -> tuple[str, int]:
    opening = text.find("(", start)
    if opening < 0:
        fail("PSD comment is not followed by a parenthesized tree")
    depth = 0
    for position in range(opening, len(text)):
        character = text[position]
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return text[opening : position + 1], position + 1
            if depth < 0:
                break
    fail(f"unbalanced PSD expression beginning at byte {opening}")


def parse_sexpression(source: str) -> list[object]:
    tokens = TOKEN_RE.findall(source)
    stack: list[list[object]] = []
    root: list[object] | None = None
    for token in tokens:
        if token == "(":
            node: list[object] = []
            if stack:
                stack[-1].append(node)
            else:
                if root is not None:
                    fail("multiple top-level expressions in one PSD record")
                root = node
            stack.append(node)
        elif token == ")":
            if not stack:
                fail("unexpected closing parenthesis in PSD record")
            stack.pop()
        else:
            if not stack:
                fail(f"token outside a PSD expression: {token}")
            stack[-1].append(token)
    if stack or root is None:
        fail("unbalanced or empty PSD expression")
    return root


def direct_id(expression: list[object]) -> str | None:
    for child in expression:
        if (
            isinstance(child, list)
            and len(child) >= 2
            and child[0] == "ID"
            and isinstance(child[1], str)
        ):
            return child[1]
    return None


def tree_from_record(expression: list[object]) -> list[object]:
    # CorpusSearch records normally wrap TREE and (ID id) in an outer list.
    if direct_id(expression) is not None:
        for child in expression:
            if isinstance(child, list) and child and child[0] != "ID":
                return child
    # Also accept an unwrapped tree when its ID is nested or supplied elsewhere.
    return expression


def nested_id(node: list[object]) -> str | None:
    found = direct_id(node)
    if found is not None:
        return found
    for child in node:
        if isinstance(child, list):
            found = nested_id(child)
            if found is not None:
                return found
    return None


def read_psd(path: Path) -> dict[str, PsdRecord]:
    text = path.read_text(encoding="utf-8")
    records: dict[str, PsdRecord] = {}
    comments = list(COMMENT_RE.finditer(text))
    if not comments:
        fail(f"no /* ... */ sentence records found in {path}")
    for comment_match in comments:
        source, _ = balanced_expression(text, comment_match.end())
        expression = parse_sexpression(source)
        metadata = parse_metadata(comment_match.group(1))
        sentence_id = nested_id(expression) or metadata.get("id")
        if not sentence_id:
            fail(f"record after byte {comment_match.end()} in {path} has no ID")
        if sentence_id in records:
            fail(f"duplicate sentence ID {sentence_id!r} in {path}")
        records[sentence_id] = PsdRecord(
            sentence_id=sentence_id,
            metadata=metadata,
            expression=expression,
            tree=tree_from_record(expression),
        )
    return records


def pretty_sexpression(node: object, indent: int = 0) -> str:
    padding = " " * indent
    if isinstance(node, str):
        return padding + node
    if not node:
        return padding + "()"
    if all(isinstance(item, str) for item in node):
        return padding + "(" + " ".join(node) + ")"
    prefix: list[str] = []
    first_child = 0
    for first_child, item in enumerate(node):
        if isinstance(item, list):
            break
        prefix.append(item)
    else:
        first_child = len(node)
    lines = [padding + "(" + " ".join(prefix)]
    for child in node[first_child:]:
        lines.append(pretty_sexpression(child, indent + 2))
    lines[-1] += ")"
    return "\n".join(lines)


def dot_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def tree_to_dot(tree: list[object]) -> str:
    lines = [
        "digraph tree {",
        "  graph [rankdir=TB, bgcolor=white, margin=0.08, nodesep=0.22, ranksep=0.34];",
        '  node [fontname="DejaVu Sans", fontsize=11, color="#4b5563"];',
        '  edge [color="#9ca3af", penwidth=1.1, arrowsize=0];',
    ]
    counter = 0

    def add_node(node: object) -> str:
        nonlocal counter
        node_id = f"n{counter}"
        counter += 1
        if isinstance(node, str):
            lines.append(
                f"  {node_id} [label={dot_quote(node)}, shape=plaintext, "
                'fontname="DejaVu Sans Bold", fontcolor="#111827"];'
            )
            return node_id
        label = str(node[0]) if node and isinstance(node[0], str) else ""
        lines.append(
            f"  {node_id} [label={dot_quote(label)}, shape=box, style=rounded, "
            'height=0.25, margin="0.07,0.04", color="#6b7280"];'
        )
        for child in node[1:] if label else node:
            child_id = add_node(child)
            lines.append(f"  {node_id} -> {child_id};")
        return node_id

    add_node(tree)
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_tree(tree: list[object], destination: Path, image_format: str) -> None:
    command = ["dot", f"-T{image_format}", "-o", str(destination)]
    completed = subprocess.run(
        command,
        input=tree_to_dot(tree),
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if completed.returncode:
        fail(f"Graphviz failed for {destination}: {completed.stderr.strip()}")


def infer_result_columns(fieldnames: Sequence[str]) -> tuple[str, str, str, str]:
    result_columns = [name for name in fieldnames if name.startswith("result_")]
    if len(result_columns) != 2:
        fail(
            "transition TSV must contain exactly two result_* columns; found "
            + ", ".join(result_columns)
        )
    before_column, after_column = result_columns
    prefix = "result_"
    return (
        before_column,
        after_column,
        before_column[len(prefix) :],
        after_column[len(prefix) :],
    )


def transition_kind(value: str) -> str | None:
    normalized = value.strip().upper()
    if normalized.endswith("PERSISTENT_STRUCTURAL"):
        return "persistent"
    if normalized.endswith("IMPROVEMENT"):
        return "improvement"
    if normalized.endswith("REGRESSION"):
        return "regression"
    return None


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def safe_stem(sentence_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", sentence_id).strip("-") or "sentence"


def relative_link(target: Path, markdown_path: Path) -> str:
    import os

    return Path(os.path.relpath(target, markdown_path.parent)).as_posix()


def metadata_value(before: PsdRecord, after: PsdRecord, key: str) -> str:
    return after.metadata.get(key) or before.metadata.get(key) or ""


def append_transition(
    output: list[str],
    row: dict[str, str],
    before: PsdRecord,
    after: PsdRecord,
    before_column: str,
    after_column: str,
    before_label: str,
    after_label: str,
    assets_dir: Path,
    markdown_path: Path,
    image_format: str,
) -> None:
    sentence_id = row["sentence_id"]
    stem = safe_stem(sentence_id)
    before_image = assets_dir / f"{stem}.before.{image_format}"
    after_image = assets_dir / f"{stem}.after.{image_format}"
    render_tree(before.tree, before_image, image_format)
    render_tree(after.tree, after_image, image_format)

    output.extend(
        [
            '<div style="page-break-before: always;"></div>',
            "",
            f"### {markdown_escape(sentence_id)}",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Dataset | {markdown_escape(row.get('dataset', ''))} |",
            f"| Status | {markdown_escape(row.get('struct_status', ''))} |",
            f"| Text | {markdown_escape(metadata_value(before, after, 'text'))} |",
            f"| Portuguese | {markdown_escape(metadata_value(before, after, 'text_por'))} |",
            f"| {markdown_escape(before_label)} result | {markdown_escape(row[before_column])} |",
            f"| {markdown_escape(after_label)} result | {markdown_escape(row[after_column])} |",
            "",
            f"#### BEFORE — parser {markdown_escape(before_label)} — LISP",
            "",
            "```lisp",
            pretty_sexpression(before.expression),
            "```",
            "",
            f"#### BEFORE — parser {markdown_escape(before_label)} — graphical tree",
            "",
            f"![BEFORE tree for {markdown_escape(sentence_id)}]({relative_link(before_image, markdown_path)})",
            "",
            f"#### AFTER — parser {markdown_escape(after_label)} — LISP",
            "",
            "```lisp",
            pretty_sexpression(after.expression),
            "```",
            "",
            f"#### AFTER — parser {markdown_escape(after_label)} — graphical tree",
            "",
            f"![AFTER tree for {markdown_escape(sentence_id)}]({relative_link(after_image, markdown_path)})",
            "",
        ]
    )


def append_tree_representation(
    output: list[str],
    record: PsdRecord,
    role: str,
    label: str,
    image: Path,
    sentence_id: str,
    markdown_path: Path,
    image_format: str,
) -> None:
    render_tree(record.tree, image, image_format)
    escaped_role = markdown_escape(role)
    escaped_label = markdown_escape(label)
    escaped_id = markdown_escape(sentence_id)
    output.extend(
        [
            f"#### {escaped_role} — {escaped_label} — LISP",
            "",
            "```lisp",
            pretty_sexpression(record.expression),
            "```",
            "",
            f"#### {escaped_role} — {escaped_label} — graphical tree",
            "",
            f"![{escaped_role} tree for {escaped_id}]({relative_link(image, markdown_path)})",
            "",
        ]
    )


def append_persistent_transition(
    output: list[str],
    row: dict[str, str],
    gold: PsdRecord,
    before: PsdRecord,
    after: PsdRecord,
    before_column: str,
    after_column: str,
    gold_label: str,
    before_label: str,
    after_label: str,
    assets_dir: Path,
    markdown_path: Path,
    image_format: str,
) -> None:
    sentence_id = row["sentence_id"]
    stem = safe_stem(sentence_id)
    output.extend(
        [
            '<div style="page-break-before: always;"></div>',
            "",
            f"### {markdown_escape(sentence_id)}",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Dataset | {markdown_escape(row.get('dataset', ''))} |",
            f"| Status | {markdown_escape(row.get('struct_status', ''))} |",
            f"| Text | {markdown_escape(metadata_value(before, after, 'text'))} |",
            f"| Portuguese | {markdown_escape(metadata_value(before, after, 'text_por'))} |",
            f"| {markdown_escape(before_label)} result | {markdown_escape(row[before_column])} |",
            f"| {markdown_escape(after_label)} result | {markdown_escape(row[after_column])} |",
            "",
        ]
    )
    append_tree_representation(
        output,
        gold,
        "REFERENCE",
        gold_label,
        assets_dir / f"{stem}.gold.{image_format}",
        sentence_id,
        markdown_path,
        image_format,
    )
    append_tree_representation(
        output,
        before,
        "BEFORE",
        f"parser {before_label}",
        assets_dir / f"{stem}.before.{image_format}",
        sentence_id,
        markdown_path,
        image_format,
    )
    append_tree_representation(
        output,
        after,
        "AFTER",
        f"parser {after_label}",
        assets_dir / f"{stem}.after.{image_format}",
        sentence_id,
        markdown_path,
        image_format,
    )


def main() -> int:
    args = parse_args()
    required_paths = [args.transitions, args.before_psd, args.after_psd]
    if args.gold_psd is not None:
        required_paths.append(args.gold_psd)
    for path in required_paths:
        require_file(path)
    if shutil.which("dot") is None:
        fail("Graphviz 'dot' was not found; install the graphviz package")

    with args.transitions.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not reader.fieldnames:
            fail(f"empty transition TSV: {args.transitions}")
        required = {"sentence_id", "struct_status", "classification"}
        missing = required - set(reader.fieldnames)
        if missing:
            fail("transition TSV lacks column(s): " + ", ".join(sorted(missing)))
        before_column, after_column, inferred_before, inferred_after = infer_result_columns(
            reader.fieldnames
        )
        rows = list(reader)

    before_label = args.before_label or inferred_before
    after_label = args.after_label or inferred_after
    selected: dict[str, list[dict[str, str]]] = {
        "improvement": [],
        "regression": [],
        "persistent": [],
    }
    for row in rows:
        if row["struct_status"].strip().upper() != "DONE":
            continue
        kind = transition_kind(row["classification"])
        if kind in ("improvement", "regression"):
            selected[kind].append(row)
        elif kind == "persistent" and args.gold_psd is not None:
            selected[kind].append(row)

    before_records = read_psd(args.before_psd)
    after_records = read_psd(args.after_psd)
    gold_records = read_psd(args.gold_psd) if args.gold_psd is not None else {}
    selected_ids = {
        row["sentence_id"] for group in selected.values() for row in group
    }
    for sentence_id in sorted(selected_ids):
        if sentence_id not in before_records:
            fail(f"sentence {sentence_id!r} is missing from BEFORE PSD")
        if sentence_id not in after_records:
            fail(f"sentence {sentence_id!r} is missing from AFTER PSD")
        if args.gold_psd is not None and sentence_id not in gold_records:
            fail(f"sentence {sentence_id!r} is missing from GOLD PSD")

    output_path = args.output.expanduser().resolve()
    assets_dir = (
        args.assets_dir.expanduser().resolve()
        if args.assets_dir
        else output_path.with_name(output_path.stem + ".assets")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    if args.gold_psd is None:
        introduction = (
            f"This document compares parser {before_label} (BEFORE) with parser "
            f"{after_label} (AFTER) for DONE sentences whose classification changed. "
            "It contains every improvement and regression recorded in the transition "
            "TSV, with both parser trees shown in LISP and graphical formats for human inspection."
        )
    else:
        introduction = (
            f"This document compares parser {before_label} (BEFORE) with parser "
            f"{after_label} (AFTER) for DONE sentences. It contains every improvement, "
            "regression, and persistent structural case recorded in the transition TSV. "
            "Improvement and regression sections show both parser trees; the persistent "
            "section shows the gold reference together with both parser trees. All trees "
            "are provided in LISP and graphical formats for human inspection."
        )

    markdown = [
        "---",
        f'title: "{args.title.replace(chr(34), chr(39))}"',
        "geometry: margin=20mm",
        "fontsize: 10pt",
        "---",
        "",
        "# 1. Introduction",
        "",
        introduction,
        "",
        f"**DONE improvements:** {len(selected['improvement'])}.  ",
        f"**DONE regressions:** {len(selected['regression'])}.",
        "",
        "# 2. DONE improvements",
        "",
    ]
    if not selected["improvement"]:
        markdown.extend(["No DONE improvements were recorded.", ""])
    for row in selected["improvement"]:
        append_transition(
            markdown,
            row,
            before_records[row["sentence_id"]],
            after_records[row["sentence_id"]],
            before_column,
            after_column,
            before_label,
            after_label,
            assets_dir,
            output_path,
            args.image_format,
        )

    markdown.extend(["# 3. DONE regressions", ""])
    if not selected["regression"]:
        markdown.extend(["No DONE regressions were recorded.", ""])
    for row in selected["regression"]:
        append_transition(
            markdown,
            row,
            before_records[row["sentence_id"]],
            after_records[row["sentence_id"]],
            before_column,
            after_column,
            before_label,
            after_label,
            assets_dir,
            output_path,
            args.image_format,
        )

    if args.gold_psd is not None:
        markdown.extend(
            [
                "# 4. DONE persistent structural cases",
                "",
                (
                    "In these cases, both parsers remain structurally different from "
                    "the gold tree. The A and C outputs may nevertheless be identical "
                    "to or different from one another."
                ),
                "",
            ]
        )
        if not selected["persistent"]:
            markdown.extend(["No DONE persistent structural cases were recorded.", ""])
        for row in selected["persistent"]:
            append_persistent_transition(
                markdown,
                row,
                gold_records[row["sentence_id"]],
                before_records[row["sentence_id"]],
                after_records[row["sentence_id"]],
                before_column,
                after_column,
                args.gold_label,
                before_label,
                after_label,
                assets_dir,
                output_path,
                args.image_format,
            )

    output_path.write_text("\n".join(markdown).rstrip() + "\n", encoding="utf-8")
    print(f"DONE improvements: {len(selected['improvement'])}")
    print(f"DONE regressions: {len(selected['regression'])}")
    if args.gold_psd is not None:
        print(f"DONE persistent structural cases: {len(selected['persistent'])}")
    print(f"Markdown report: {output_path}")
    print(f"Tree images: {assets_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
