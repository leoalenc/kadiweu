#!/usr/bin/env python3
"""Run exported Tycho Brahe parser rules sequentially with CorpusSearch.

The input is a CorpusSearch-readable ``.pos`` file whose records contain a
flat sequence of POS preterminals inside ``IP-MAT``.  Every numbered rule from
the Tycho Brahe text export is written to a separate query file and applied to
the preceding rule's output.  Diagnostics go to stderr; final trees may be
written to a PSD file and/or printed to stdout.

The program can also extract selected records from gold PSD files, derive the
corresponding flat POS input, and compare parsed output with a gold PSD file.
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


class RunnerError(RuntimeError):
    """Raised for malformed input, rule failure, or CorpusSearch failure."""


@dataclass(frozen=True)
class Rule:
    original_number: int
    name: str
    body: str

    def query_text(self, execution_number: int) -> str:
        return (
            "/*\n"
            f"Execution rule: {execution_number}\n"
            f"Original TBP rule: {self.original_number}\n"
            f"Name: {self.name}\n"
            "*/\n\n"
            f"{self.body.rstrip()}\n"
        )


@dataclass(frozen=True)
class Record:
    comment: str
    tree: str
    sentence_id: str

    def render(self) -> str:
        prefix = self.comment.rstrip()
        return (prefix + "\n" if prefix else "") + self.tree.strip() + "\n"


RULE_HEADER = re.compile(r"(?m)^(\d+):\s*([^\r\n]+)\s*$")
ID_RE = re.compile(r"\(ID\s+([^()\s]+)\s*\)")
ATOM_RE = re.compile(r"[^()\s]+")


def parse_rules(path: Path) -> list[Rule]:
    text = path.read_text(encoding="utf-8")
    matches = list(RULE_HEADER.finditer(text))
    if not matches:
        raise RunnerError(f"no numbered rules found in {path}")
    rules: list[Rule] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        if not re.search(r"(?m)^\s*node\s*:", body):
            raise RunnerError(f"rule {match.group(1)} has no node declaration")
        if not re.search(r"(?m)^\s*query\s*:", body):
            raise RunnerError(f"rule {match.group(1)} has no query declaration")
        rules.append(Rule(int(match.group(1)), match.group(2).strip(), body))
    numbers = [rule.original_number for rule in rules]
    if len(numbers) != len(set(numbers)):
        raise RunnerError("duplicate original rule numbers")
    return rules

def parse_corpussearch_results(text: str) -> list[Record]:
    """Extract ID-bearing trees from a CorpusSearch report."""
    records: list[Record] = []
    seen_ids: set[str] = set()
    cursor = 0

    while cursor < len(text):
        start = text.find("(", cursor)
        if start < 0:
            break

        try:
            end = _balanced_tree_end(text, start)
        except RunnerError:
            cursor = start + 1
            continue

        tree = text[start:end]
        ids = ID_RE.findall(tree)

        if len(ids) == 1:
            sentence_id = ids[0]
            if sentence_id in seen_ids:
                raise RunnerError(
                    "CorpusSearch returned duplicate transformed record "
                    f"for {sentence_id}"
                )
            seen_ids.add(sentence_id)
            records.append(Record("", tree, sentence_id))

        cursor = end

    return records

def merge_transformed_records(
    current_records: Sequence[Record],
    transformed_records: Sequence[Record],
) -> tuple[list[Record], int]:
    """Replace transformed records by ID and retain all nonmatches."""
    current_ids = {record.sentence_id for record in current_records}

    if len(current_ids) != len(current_records):
        raise RunnerError("the current corpus contains duplicate IDs")

    replacements: dict[str, Record] = {}

    for record in transformed_records:
        sentence_id = record.sentence_id

        if sentence_id not in current_ids:
            raise RunnerError(
                "CorpusSearch returned an ID absent from its input: "
                f"{sentence_id}"
            )
        if sentence_id in replacements:
            raise RunnerError(
                f"CorpusSearch returned duplicate ID {sentence_id}"
            )

        replacements[sentence_id] = record

    merged: list[Record] = []

    for original in current_records:
        replacement = replacements.get(original.sentence_id)

        if replacement is None:
            merged.append(original)
        else:
            # Retain the original project metadata comment.
            merged.append(
                Record(
                    comment=original.comment,
                    tree=replacement.tree,
                    sentence_id=original.sentence_id,
                )
            )

    return merged, len(replacements)

def _balanced_tree_end(text: str, start: int) -> int:
    depth = 0
    for position in range(start, len(text)):
        char = text[position]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return position + 1
            if depth < 0:
                break
    raise RunnerError(f"unbalanced tree beginning at character {start}")


def parse_records(text: str) -> list[Record]:
    records: list[Record] = []
    cursor = 0
    pending_comment = ""
    while cursor < len(text):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text):
            break
        if text.startswith("/*", cursor):
            end = text.find("*/", cursor + 2)
            if end < 0:
                raise RunnerError("unterminated block comment")
            pending_comment = text[cursor:end + 2]
            cursor = end + 2
            continue
        if text[cursor] != "(":
            line = text.count("\n", 0, cursor) + 1
            raise RunnerError(f"unexpected content at line {line}")
        end = _balanced_tree_end(text, cursor)
        tree = text[cursor:end]
        ids = ID_RE.findall(tree)
        if len(ids) != 1:
            raise RunnerError(f"record must contain exactly one ID; found {ids!r}")
        records.append(Record(pending_comment, tree, ids[0]))
        pending_comment = ""
        cursor = end
    if pending_comment:
        raise RunnerError("metadata comment is not followed by a tree")
    return records


def read_records(path: Path) -> list[Record]:
    return parse_records(path.read_text(encoding="utf-8"))


def _sexpr_tokens(tree: str) -> list[str]:
    return re.findall(r"\(|\)|[^()\s]+", tree)


def parse_sexpr(tree: str):
    tokens = _sexpr_tokens(tree)
    position = 0

    def parse():
        nonlocal position
        if position >= len(tokens) or tokens[position] != "(":
            raise RunnerError("expected '('")
        position += 1
        values = []
        while position < len(tokens) and tokens[position] != ")":
            if tokens[position] == "(":
                values.append(parse())
            else:
                values.append(tokens[position])
                position += 1
        if position >= len(tokens):
            raise RunnerError("unclosed parenthesis")
        position += 1
        return values

    value = parse()
    if position != len(tokens):
        raise RunnerError("content follows outer tree")
    return value


def terminal_pairs(record: Record) -> list[tuple[str, str]]:
    """Return overt ``(form, POS)`` pairs from a parsed PSD record."""
    root = parse_sexpr(record.tree)
    pairs: list[tuple[str, str]] = []

    def visit(node) -> None:
        if not isinstance(node, list) or not node:
            return
        if len(node) == 2 and all(isinstance(item, str) for item in node):
            tag, form = node
            if tag not in {"ID", "-NONE-"}:
                pairs.append((form, tag))
            return
        for child in node[1:] if isinstance(node[0], str) else node:
            visit(child)

    visit(root)
    return pairs


def record_to_pos(record: Record, indent: int = 2) -> Record:
    """Flatten a gold record to the input assumed by the downloaded rules."""
    pairs = terminal_pairs(record)
    if not pairs:
        raise RunnerError(f"{record.sentence_id} has no overt terminals")
    lines = ["(", " " * indent + "(IP-MAT"]
    for form, tag in pairs:
        lines.append(" " * (indent * 2) + f"({tag} {form})")
    lines.extend([
        " " * indent + ")",
        " " * indent + f"(ID {record.sentence_id})",
        ")",
    ])
    return Record(record.comment, "\n".join(lines), record.sentence_id)


def write_records(path: Path, records: Iterable[Record]) -> None:
    rendered = "\n".join(record.render().rstrip() for record in records) + "\n"
    path.write_text(rendered, encoding="utf-8")


def select_records(paths: Sequence[Path], sentence_ids: Sequence[str]) -> list[Record]:
    wanted = set(sentence_ids)
    found: dict[str, Record] = {}
    for path in paths:
        for record in read_records(path):
            if record.sentence_id in wanted:
                if record.sentence_id in found:
                    raise RunnerError(f"duplicate selected ID {record.sentence_id}")
                found[record.sentence_id] = record
    missing = [sentence_id for sentence_id in sentence_ids if sentence_id not in found]
    if missing:
        raise RunnerError("selected IDs not found: " + ", ".join(missing))
    return [found[sentence_id] for sentence_id in sentence_ids]


def corpussearch_output(query_path: Path) -> Path:
    """Return the output file created by CorpusSearch for a query."""
    candidates = [
        query_path.with_suffix(".out"),
        Path(str(query_path) + ".out"),
    ]
    existing = [path for path in candidates if path.is_file()]

    if len(existing) == 1:
        return existing[0]

    if not existing:
        raise RunnerError(
            f"CorpusSearch created no output for query {query_path}"
        )

    raise RunnerError(
        f"CorpusSearch created multiple possible outputs for {query_path}: "
        + ", ".join(str(path) for path in existing)
    )

def run_rules(
    rules: Sequence[Rule], input_path: Path, corpussearch: str,
    work_dir: Path, keep_intermediate: bool, log_path: Path | None,
) -> Path:
    input_path = input_path.resolve()
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    if any(work_dir.iterdir()):
        raise RunnerError(
            f"work directory is not empty: {work_dir}; "
            "select a new or empty directory"
        )

    query_dir = work_dir / "queries"
    query_dir.mkdir(exist_ok=True)
    current = work_dir / "000-input.pos"
    shutil.copyfile(input_path, current)
    log_lines = ["execution\toriginal_tbp\tname\tstatus"]
    for execution, rule in enumerate(rules, start=1):
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", rule.name).strip("-") or "rule"
        query = query_dir / f"{execution:03d}-tbp-{rule.original_number:03d}-{safe_name}.q"
        query.write_text(rule.query_text(execution), encoding="utf-8")
        print(f"[{execution:03d}/{len(rules):03d}] TBP {rule.original_number}: {rule.name}", file=sys.stderr)
        expected_output = query.with_suffix(".out")
        if expected_output.exists():
            expected_output.unlink()
        completed = subprocess.run(
            [
                corpussearch,
                str(query.resolve()),
                str(current.resolve()),
            ],
            cwd=work_dir,
            stdin=subprocess.DEVNULL,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        transcript = completed.stdout or ""
        transcript_path = (
            work_dir
            / f"{execution:03d}-tbp-"
                f"{rule.original_number:03d}-{safe_name}.log"
        )
        transcript_path.write_text(transcript, encoding="utf-8")
        if completed.returncode != 0 or re.search(r"(?im)^\s*(ERROR|FATAL)", transcript):
            (work_dir / f"{execution:03d}-failure.log").write_text(transcript, encoding="utf-8")
            raise RunnerError(
                f"CorpusSearch failed at execution rule {execution} "
                f"(original TBP {rule.original_number}: {rule.name}); "
                f"see {work_dir / f'{execution:03d}-failure.log'}"
            )
        produced = corpussearch_output(query)

        current_records = read_records(current)
        result_text = produced.read_text(encoding="utf-8", errors="replace")
        transformed_records = parse_corpussearch_results(result_text)

        merged_records, changed_count = merge_transformed_records(
        current_records,
        transformed_records,
        )

        next_path = (
            work_dir
        /   f"{execution:03d}-tbp-"
            f"{rule.original_number:03d}-{safe_name}.psd"
        )
        write_records(next_path, merged_records)

        if len(merged_records) != len(current_records):
            raise RunnerError(
                f"rule {execution} changed the corpus size from "
                f"{len(current_records)} to {len(merged_records)}"
            )

        log_lines.append(
            f"{execution}\t{rule.original_number}\t"
            f"{rule.name}\tOK\t{changed_count}"
        )

        if not keep_intermediate and current.name != "000-input.pos":
            current.unlink()

        if not keep_intermediate:
            produced.unlink()

        current = next_path
        if not keep_intermediate and current.name != "000-input.pos":
            current.unlink()
        current = next_path
        log_lines = [
            "execution\toriginal_tbp\tname\tstatus\ttransformed_records"
        ]
    if log_path:
        log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return current


def normalized_records(path: Path) -> dict[str, str]:
    normalized: dict[str, str] = {}

    for record in read_records(path):
        if record.sentence_id in normalized:
            raise RunnerError(
                f"duplicate ID in {path}: {record.sentence_id}"
            )
        normalized[record.sentence_id] = " ".join(
            _sexpr_tokens(record.tree)
        )

    return normalized


def compare_psd(actual_path: Path, expected_path: Path, diff_path: Path | None) -> bool:
    actual = normalized_records(actual_path)
    expected = normalized_records(expected_path)
    ok = actual == expected
    if ok:
        print(f"PASS: all {len(expected)} trees are structurally identical", file=sys.stderr)
        return True
    lines: list[str] = []
    for sentence_id in sorted(set(actual) | set(expected)):
        if actual.get(sentence_id) == expected.get(sentence_id):
            continue
        lines.extend(difflib.unified_diff(
            [expected.get(sentence_id, "<missing>") + "\n"],
            [actual.get(sentence_id, "<missing>") + "\n"],
            fromfile=f"expected/{sentence_id}", tofile=f"actual/{sentence_id}",
        ))
    diff = "".join(lines)
    if diff_path:
        diff_path.write_text(diff, encoding="utf-8")
        print(f"FAIL: tree differences written to {diff_path}", file=sys.stderr)
    else:
        sys.stderr.write(diff)
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rules", type=Path, nargs="?", help="downloaded numbered TBP rule file")
    parser.add_argument("input", type=Path, nargs="?", help="flat CorpusSearch .pos input")
    parser.add_argument("--corpussearch", default="corpussearch", help="CorpusSearch command (default: corpussearch)")
    parser.add_argument("--output", type=Path, help="write final CorpusSearch PSD here")
    parser.add_argument("--print-parses", action="store_true", help="print final PSD to stdout")
    parser.add_argument("--work-dir", type=Path, help="directory for queries and execution files")
    parser.add_argument("--keep-intermediate", action="store_true")
    parser.add_argument("--log", type=Path, help="write TSV execution manifest")
    parser.add_argument("--expected", type=Path, help="compare final trees with this gold PSD")
    parser.add_argument("--diff", type=Path, help="write structural comparison diff here")
    parser.add_argument("--extract-from", type=Path, nargs="+", metavar="PSD", help="extract records from PSD files instead of running rules")
    parser.add_argument("--sentence-id", action="append", default=[], help="ID to extract; repeat in desired order")
    parser.add_argument("--gold-output", type=Path, help="write extracted gold PSD")
    parser.add_argument("--pos-output", type=Path, help="write POS input derived from extracted trees")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.extract_from:
            if not args.sentence_id or not args.gold_output or not args.pos_output:
                raise RunnerError("extraction requires --sentence-id, --gold-output, and --pos-output")
            records = select_records(args.extract_from, args.sentence_id)
            write_records(args.gold_output, records)
            write_records(args.pos_output, (record_to_pos(record) for record in records))
            print(f"wrote {len(records)} gold records to {args.gold_output}", file=sys.stderr)
            print(f"wrote {len(records)} POS records to {args.pos_output}", file=sys.stderr)
            return 0
        if not args.rules or not args.input:
            raise RunnerError("RULES and INPUT are required unless --extract-from is used")
        if not args.output and not args.print_parses and not args.expected:
            raise RunnerError("request at least one of --output, --print-parses, or --expected")
        rules = parse_rules(args.rules)
        if args.work_dir:
            work_dir = args.work_dir
            temporary = None
        else:
            temporary = tempfile.TemporaryDirectory(prefix="kadiweu-parser-")
            work_dir = Path(temporary.name)
        final_path = run_rules(rules, args.input, args.corpussearch, work_dir, args.keep_intermediate, args.log)
        final_text = final_path.read_text(encoding="utf-8")
        if args.output:
            args.output.write_text(final_text, encoding="utf-8")
        if args.print_parses:
            sys.stdout.write(final_text)
        comparison_ok = True
        if args.expected:
            comparison_ok = compare_psd(final_path, args.expected, args.diff)
        if temporary is not None:
            temporary.cleanup()
        return 0 if comparison_ok else 1
    except (OSError, RunnerError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
