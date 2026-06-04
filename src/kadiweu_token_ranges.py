#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities for assigning, checking, and repairing CoNLL-U TokenRange values.

The module treats the CoNLL-U `# text = ...` line as the source of truth.
It is intended for the Kadiwéu converter/treebank workflow, but the code is
not Kadiwéu-specific.

Main use cases
--------------
1. During conversion, after rows have been emitted:

    from kadiweu_token_ranges import assign_token_ranges_to_emitted_rows
    assign_token_ranges_to_emitted_rows(emitted_rows, text)

2. Check an existing treebank:

    python3 kadiweu_token_ranges.py check input.conllu

3. Write a corrected copy:

    python3 kadiweu_token_ranges.py fix input.conllu -o corrected.conllu

4. Correct a file in place:

    python3 kadiweu_token_ranges.py fix input.conllu --in-place

Policy
------
- TokenRange is assigned to visible surface rows: ordinary token rows, MWT rows,
  and punctuation rows.
- TokenRange is removed from MWT component rows because they do not correspond
  to a contiguous substring of `# text` independently from the MWT surface form.
- SpaceAfter=No may be recomputed from `# text` for visible surface rows.
- SpaceAfter=No is removed from MWT component rows.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TOKEN_RANGE_RE = re.compile(r"^TokenRange=(\d+):(\d+)$")
TOKEN_RANGE_SEARCH_RE = re.compile(r"(?:^|\|)TokenRange=(\d+):(\d+)(?:\||$)")


@dataclasses.dataclass
class TokenRangeIssue:
    sent_id: str
    row_id: str
    form: str
    kind: str
    expected: Optional[str]
    found: Optional[str]

    def format(self) -> str:
        exp = self.expected if self.expected is not None else "_"
        got = self.found if self.found is not None else "_"
        return f"{self.sent_id}\t{self.row_id}\t{self.form}\t{self.kind}\texpected={exp}\tfound={got}"


@dataclasses.dataclass
class ConlluRow:
    line_index: int
    fields: List[str]

    @property
    def id(self) -> str:
        return self.fields[0]

    @property
    def form(self) -> str:
        return self.fields[1]

    @property
    def misc(self) -> str:
        return self.fields[9]

    @misc.setter
    def misc(self, value: str) -> None:
        self.fields[9] = value or "_"

    def serialize(self) -> str:
        return "\t".join(self.fields)


@dataclasses.dataclass
class SentenceBlock:
    lines: List[str]
    sent_id: str
    text: str
    rows: List[ConlluRow]


# ---------------------------------------------------------------------------
# MISC helpers
# ---------------------------------------------------------------------------


def parse_misc(misc: str) -> List[str]:
    if not misc or misc == "_":
        return []
    return [item for item in misc.split("|") if item and item != "_"]


def join_misc(items: Sequence[str]) -> str:
    clean = [item for item in items if item and item != "_"]
    return "|".join(clean) if clean else "_"


def get_misc_value(misc: str, key: str) -> Optional[str]:
    prefix = key + "="
    for item in parse_misc(misc):
        if item.startswith(prefix):
            return item[len(prefix):]
    return None


def remove_misc_key(misc: str, key: str) -> str:
    prefix = key + "="
    return join_misc([item for item in parse_misc(misc) if not item.startswith(prefix)])


def set_misc_key(misc: str, key: str, value: str) -> str:
    prefix = key + "="
    replaced = False
    out: List[str] = []
    for item in parse_misc(misc):
        if item.startswith(prefix):
            if not replaced:
                out.append(prefix + value)
                replaced = True
        else:
            out.append(item)
    if not replaced:
        out.append(prefix + value)
    return join_misc(out)


def ensure_flag(misc: str, flag: str) -> str:
    items = parse_misc(misc)
    if flag not in items:
        items.insert(0, flag)
    return join_misc(items)


def remove_flag(misc: str, flag: str) -> str:
    return join_misc([item for item in parse_misc(misc) if item != flag])


def get_token_range(misc: str) -> Optional[str]:
    value = get_misc_value(misc, "TokenRange")
    if value and re.match(r"^\d+:\d+$", value):
        return value
    return None


# ---------------------------------------------------------------------------
# ID and block helpers
# ---------------------------------------------------------------------------


def is_int_id(row_id: str) -> bool:
    return row_id.isdigit()


def is_mwt_id(row_id: str) -> bool:
    return bool(re.match(r"^\d+-\d+$", row_id))


def is_empty_node_id(row_id: str) -> bool:
    return bool(re.match(r"^\d+\.\d+$", row_id))


def mwt_span(row_id: str) -> Optional[Tuple[int, int]]:
    if not is_mwt_id(row_id):
        return None
    a, b = row_id.split("-", 1)
    return int(a), int(b)


def parse_conllu_blocks(conllu_text: str) -> List[SentenceBlock]:
    blocks: List[SentenceBlock] = []
    raw_blocks = re.split(r"\n\s*\n", conllu_text.strip()) if conllu_text.strip() else []

    for raw in raw_blocks:
        lines = raw.splitlines()
        sent_id = "<unknown>"
        text = ""
        rows: List[ConlluRow] = []

        for i, line in enumerate(lines):
            if line.startswith("# sent_id ="):
                sent_id = line.split("=", 1)[1].strip()
            elif line.startswith("# text ="):
                text = line.split("=", 1)[1].strip()
            elif line and not line.startswith("#"):
                fields = line.split("\t")
                if len(fields) == 10:
                    rows.append(ConlluRow(i, fields))

        blocks.append(SentenceBlock(lines=lines, sent_id=sent_id, text=text, rows=rows))

    return blocks


def serialize_blocks(blocks: Sequence[SentenceBlock]) -> str:
    out: List[str] = []
    for block in blocks:
        lines = list(block.lines)
        for row in block.rows:
            lines[row.line_index] = row.serialize()
        out.append("\n".join(lines))
    return "\n\n".join(out) + ("\n" if out else "")


# ---------------------------------------------------------------------------
# Alignment and TokenRange assignment
# ---------------------------------------------------------------------------


def mwt_component_ids(rows: Sequence[ConlluRow]) -> set[int]:
    component_ids: set[int] = set()
    for row in rows:
        span = mwt_span(row.id)
        if span is None:
            continue
        start, end = span
        component_ids.update(range(start, end + 1))
    return component_ids


def visible_surface_rows(rows: Sequence[ConlluRow]) -> List[ConlluRow]:
    """Return rows that should be aligned against `# text`."""
    components = mwt_component_ids(rows)
    visible: List[ConlluRow] = []

    for row in rows:
        if is_empty_node_id(row.id):
            continue
        if is_mwt_id(row.id):
            visible.append(row)
            continue
        if is_int_id(row.id) and int(row.id) in components:
            continue
        visible.append(row)

    return visible


def align_forms_to_text(text: str, forms: Sequence[str]) -> List[Tuple[int, int]]:
    """
    Align visible token forms to the sentence text and return character offsets.

    Offsets are Python-style half-open ranges: start inclusive, end exclusive.
    """
    ranges: List[Tuple[int, int]] = []
    cursor = 0
    n = len(text)

    for form in forms:
        while cursor < n and text[cursor].isspace():
            cursor += 1

        if text.startswith(form, cursor):
            start = cursor
            end = cursor + len(form)
            ranges.append((start, end))
            cursor = end
            continue

        # Conservative fallback: search after cursor. This handles duplicated
        # whitespace but still avoids matching an earlier occurrence.
        found = text.find(form, cursor)
        if found >= 0:
            start = found
            end = found + len(form)
            ranges.append((start, end))
            cursor = end
            continue

        context = text[max(0, cursor - 20): min(n, cursor + 40)]
        raise ValueError(
            f"Cannot align form {form!r} at or after offset {cursor} in text {text!r}. "
            f"Nearby context: {context!r}"
        )

    return ranges


def expected_ranges_for_rows(rows: Sequence[ConlluRow], text: str) -> Dict[str, str]:
    visible = visible_surface_rows(rows)
    ranges = align_forms_to_text(text, [row.form for row in visible])
    return {
        row.id: f"{start}:{end}"
        for row, (start, end) in zip(visible, ranges)
    }


def _next_visible_starts_immediately(text: str, token_end: int) -> bool:
    return token_end < len(text) and not text[token_end].isspace()


def assign_token_ranges_to_rows(
    rows: Sequence[ConlluRow],
    text: str,
    *,
    recompute_spaceafter: bool = True,
    remove_ranges_from_mwt_components: bool = True,
) -> None:
    """Mutate parsed CoNLL-U rows by assigning correct TokenRange values."""
    visible = visible_surface_rows(rows)
    ranges = align_forms_to_text(text, [row.form for row in visible])
    expected_by_id = {
        row.id: (start, end)
        for row, (start, end) in zip(visible, ranges)
    }
    components = mwt_component_ids(rows)

    for row in rows:
        if row.id in expected_by_id:
            start, end = expected_by_id[row.id]
            row.misc = set_misc_key(row.misc, "TokenRange", f"{start}:{end}")
            if recompute_spaceafter:
                # Keep the project style: final punctuation carries SpaceAfter=No.
                # For ordinary final words, remove it because there is no following
                # token to separate.
                if _next_visible_starts_immediately(text, end) or (end == len(text) and row.form in {".", "!", "?", "..."}):
                    row.misc = ensure_flag(row.misc, "SpaceAfter=No")
                else:
                    row.misc = remove_flag(row.misc, "SpaceAfter=No")
            continue

        if is_int_id(row.id) and int(row.id) in components:
            if remove_ranges_from_mwt_components:
                row.misc = remove_misc_key(row.misc, "TokenRange")
            # UD validator rejects SpaceAfter=No on MWT component rows.
            row.misc = remove_flag(row.misc, "SpaceAfter=No")


def assign_token_ranges_to_emitted_rows(
    emitted_rows: List[Dict[str, str]],
    text: str,
    *,
    recompute_spaceafter: bool = True,
    remove_ranges_from_mwt_components: bool = True,
) -> None:
    """
    Mutate converter-style row dictionaries in place.

    Expected keys are at least `id`, `form`, and `misc`. This is the function to
    call inside `kadiweu_json_to_conllu.py` after MWT rows and final punctuation
    have been emitted.
    """
    parsed = [
        ConlluRow(
            line_index=i,
            fields=[
                row.get("id", "_"),
                row.get("form", "_"),
                row.get("lemma", "_"),
                row.get("upos", "_"),
                row.get("xpos", "_"),
                row.get("feats", "_"),
                row.get("head", "_"),
                row.get("deprel", "_"),
                row.get("deps", "_"),
                row.get("misc", "_"),
            ],
        )
        for i, row in enumerate(emitted_rows)
    ]
    assign_token_ranges_to_rows(
        parsed,
        text,
        recompute_spaceafter=recompute_spaceafter,
        remove_ranges_from_mwt_components=remove_ranges_from_mwt_components,
    )
    for source, fixed in zip(emitted_rows, parsed):
        source["misc"] = fixed.misc


# ---------------------------------------------------------------------------
# Checking and fixing complete CoNLL-U text
# ---------------------------------------------------------------------------


def check_sentence(block: SentenceBlock) -> List[TokenRangeIssue]:
    issues: List[TokenRangeIssue] = []
    if not block.text:
        return issues

    expected = expected_ranges_for_rows(block.rows, block.text)
    components = mwt_component_ids(block.rows)

    for row in block.rows:
        found = get_token_range(row.misc)
        if row.id in expected:
            exp = expected[row.id]
            if found is None:
                issues.append(TokenRangeIssue(block.sent_id, row.id, row.form, "missing", exp, None))
            elif found != exp:
                issues.append(TokenRangeIssue(block.sent_id, row.id, row.form, "incorrect", exp, found))
        elif is_int_id(row.id) and int(row.id) in components and found is not None:
            issues.append(TokenRangeIssue(block.sent_id, row.id, row.form, "component-has-tokenrange", None, found))

    return issues


def check_conllu_text(conllu_text: str) -> List[TokenRangeIssue]:
    issues: List[TokenRangeIssue] = []
    for block in parse_conllu_blocks(conllu_text):
        issues.extend(check_sentence(block))
    return issues


def fix_conllu_text(
    conllu_text: str,
    *,
    recompute_spaceafter: bool = True,
    remove_ranges_from_mwt_components: bool = True,
) -> Tuple[str, List[TokenRangeIssue]]:
    blocks = parse_conllu_blocks(conllu_text)
    before: List[TokenRangeIssue] = []

    for block in blocks:
        before.extend(check_sentence(block))
        if block.text:
            assign_token_ranges_to_rows(
                block.rows,
                block.text,
                recompute_spaceafter=recompute_spaceafter,
                remove_ranges_from_mwt_components=remove_ranges_from_mwt_components,
            )

    return serialize_blocks(blocks), before


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assign, check, and repair CoNLL-U TokenRange values using # text as ground truth."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="report missing/incorrect TokenRange values")
    p_check.add_argument("input", type=Path)

    p_fix = sub.add_parser("fix", help="write a corrected CoNLL-U file")
    p_fix.add_argument("input", type=Path)
    p_fix.add_argument("-o", "--output", type=Path)
    p_fix.add_argument("--in-place", action="store_true", help="overwrite the input file")
    p_fix.add_argument(
        "--keep-spaceafter",
        action="store_true",
        help="do not recompute SpaceAfter=No from # text",
    )
    p_fix.add_argument(
        "--keep-component-tokenranges",
        action="store_true",
        help="do not remove TokenRange from MWT component rows",
    )

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    data = args.input.read_text(encoding="utf-8")

    if args.command == "check":
        issues = check_conllu_text(data)
        for issue in issues:
            print(issue.format())
        print(f"TokenRange issues: {len(issues)}", file=sys.stderr)
        return 1 if issues else 0

    if args.command == "fix":
        fixed, issues = fix_conllu_text(
            data,
            recompute_spaceafter=not args.keep_spaceafter,
            remove_ranges_from_mwt_components=not args.keep_component_tokenranges,
        )
        if args.in_place:
            args.input.write_text(fixed, encoding="utf-8")
        else:
            if args.output is None:
                raise SystemExit("fix requires -o/--output unless --in-place is used")
            args.output.write_text(fixed, encoding="utf-8")
        for issue in issues:
            print(issue.format(), file=sys.stderr)
        print(f"Corrected TokenRange issues: {len(issues)}", file=sys.stderr)
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
