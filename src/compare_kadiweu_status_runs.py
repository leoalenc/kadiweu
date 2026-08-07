#!/usr/bin/env python3
"""Compare two sentence-status reports produced by kadiweu_status_stats.py.

Rows are matched by ``(dataset, sentence_uid)``.  The program distinguishes
status transitions among shared sentences from sentences added in B or removed
since A, so a larger aggregate DONE count is not mistaken for annotation
progress.

Example
-------
    python3 compare_kadiweu_status_runs.py \
        data/reports/status/A/sentence_status_individual.tsv \
        data/reports/status/B/sentence_status_individual.tsv \
        --label-a A --label-b B \
        --outdir data/reports/status/A-to-B
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


REQUIRED_COLUMNS = {
    "sentence_number",
    "sentence_uid",
    "dataset",
    "constituency_status",
}
MISSING_UID_VALUES = {"", "MISSING"}


@dataclass(frozen=True)
class SentenceRow:
    sentence_number: str
    sentence_uid: str
    dataset: str
    status: str
    source_line: int

    @property
    def key(self) -> tuple[str, str]:
        return self.dataset, self.sentence_uid


@dataclass(frozen=True)
class ComparisonRow:
    dataset: str
    sentence_uid: str
    sentence_number_a: str
    sentence_number_b: str
    status_a: str
    status_b: str
    change_class: str


@dataclass(frozen=True)
class IntegrityIssue:
    state: str
    source_line: int
    dataset: str
    sentence_uid: str
    issue: str
    detail: str


def normalize_status(value: str, uppercase: bool) -> str:
    value = value.strip()
    return value.upper() if uppercase else value


def read_run(path: Path, *, uppercase: bool) -> list[SentenceRow]:
    """Read and validate the structure of one individual-status TSV."""

    if not path.is_file():
        raise FileNotFoundError(f"file not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty TSV or missing header")
        missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames))
        if missing:
            raise ValueError(
                f"{path}: missing required column(s): {', '.join(missing)}"
            )
        rows = []
        for line_number, record in enumerate(reader, start=2):
            rows.append(
                SentenceRow(
                    sentence_number=record["sentence_number"].strip(),
                    sentence_uid=record["sentence_uid"].strip(),
                    dataset=record["dataset"].strip(),
                    status=normalize_status(
                        record["constituency_status"], uppercase
                    ),
                    source_line=line_number,
                )
            )
    return rows


def index_rows(
    rows: Iterable[SentenceRow], state: str
) -> tuple[dict[tuple[str, str], SentenceRow], list[IntegrityIssue]]:
    """Return unique, usable rows and all identity/data-integrity issues."""

    grouped: dict[tuple[str, str], list[SentenceRow]] = defaultdict(list)
    issues: list[IntegrityIssue] = []
    for row in rows:
        if not row.dataset:
            issues.append(
                IntegrityIssue(
                    state, row.source_line, row.dataset, row.sentence_uid,
                    "MISSING_DATASET", "row excluded from comparison",
                )
            )
            continue
        if row.sentence_uid.upper() in MISSING_UID_VALUES:
            issues.append(
                IntegrityIssue(
                    state, row.source_line, row.dataset, row.sentence_uid,
                    "MISSING_UID", "row excluded from comparison",
                )
            )
            continue
        if not row.status:
            issues.append(
                IntegrityIssue(
                    state, row.source_line, row.dataset, row.sentence_uid,
                    "MISSING_STATUS", "row excluded from comparison",
                )
            )
            continue
        grouped[row.key].append(row)

    index: dict[tuple[str, str], SentenceRow] = {}
    for key, candidates in grouped.items():
        if len(candidates) == 1:
            index[key] = candidates[0]
            continue
        lines = ", ".join(str(row.source_line) for row in candidates)
        for row in candidates:
            issues.append(
                IntegrityIssue(
                    state, row.source_line, row.dataset, row.sentence_uid,
                    "DUPLICATE_KEY",
                    f"key occurs on lines {lines}; all occurrences excluded",
                )
            )
    return index, issues


def classify_change(status_a: str, status_b: str) -> str:
    if not status_a:
        return "ADDED"
    if not status_b:
        return "REMOVED"
    if status_a == status_b:
        return "UNCHANGED"
    if status_a.upper() == "REVIEW" and status_b.upper() == "DONE":
        return "IMPROVEMENT"
    if status_a.upper() == "DONE" and status_b.upper() == "REVIEW":
        return "REGRESSION"
    return "STATUS_CHANGE"


def compare_runs(
    index_a: dict[tuple[str, str], SentenceRow],
    index_b: dict[tuple[str, str], SentenceRow],
) -> list[ComparisonRow]:
    rows = []
    for dataset, uid in sorted(set(index_a) | set(index_b)):
        row_a = index_a.get((dataset, uid))
        row_b = index_b.get((dataset, uid))
        status_a = row_a.status if row_a else ""
        status_b = row_b.status if row_b else ""
        rows.append(
            ComparisonRow(
                dataset=dataset,
                sentence_uid=uid,
                sentence_number_a=row_a.sentence_number if row_a else "",
                sentence_number_b=row_b.sentence_number if row_b else "",
                status_a=status_a,
                status_b=status_b,
                change_class=classify_change(status_a, status_b),
            )
        )
    return rows


def safe_label(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-.")
    return slug or "state"


def write_comparison(rows: Sequence[ComparisonRow], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow([
            "dataset", "sentence_uid", "sentence_number_A", "sentence_number_B",
            "status_A", "status_B", "change_class",
        ])
        for row in rows:
            writer.writerow([
                row.dataset, row.sentence_uid, row.sentence_number_a,
                row.sentence_number_b, row.status_a, row.status_b,
                row.change_class,
            ])


def write_statistics(rows: Sequence[ComparisonRow], path: Path) -> None:
    counts: Counter[tuple[str, str, str, str]] = Counter()
    for row in rows:
        counts[(row.dataset, row.status_a, row.status_b, row.change_class)] += 1
        counts[("ALL", row.status_a, row.status_b, row.change_class)] += 1
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(["dataset", "status_A", "status_B", "change_class", "count"])
        for key in sorted(counts, key=lambda item: (item[0] == "ALL", item)):
            writer.writerow([*key, counts[key]])


def write_integrity(issues: Sequence[IntegrityIssue], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow([
            "state", "source_line", "dataset", "sentence_uid", "issue", "detail"
        ])
        for issue in issues:
            writer.writerow([
                issue.state, issue.source_line, issue.dataset, issue.sentence_uid,
                issue.issue, issue.detail,
            ])


def done_counts(rows: Sequence[ComparisonRow], side: str) -> tuple[int, int]:
    statuses = [row.status_a if side == "a" else row.status_b for row in rows]
    present = [status for status in statuses if status]
    return sum(status.upper() == "DONE" for status in present), len(present)


def markdown_uid_list(rows: Sequence[ComparisonRow], change: str) -> list[str]:
    selected = [row for row in rows if row.change_class == change]
    if not selected:
        return ["- None."]
    return [
        f"- `{row.dataset}`, `{row.sentence_uid}`: "
        f"`{row.status_a or 'absent'}` → `{row.status_b or 'absent'}`"
        for row in selected
    ]


def write_summary(
    rows: Sequence[ComparisonRow],
    issues: Sequence[IntegrityIssue],
    path: Path,
    *,
    label_a: str,
    label_b: str,
    percentage_digits: int,
    source_a: Path,
    source_b: Path,
) -> None:
    classes = Counter(row.change_class for row in rows)
    shared = [row for row in rows if row.status_a and row.status_b]
    shared_done_a = sum(row.status_a.upper() == "DONE" for row in shared)
    shared_done_b = sum(row.status_b.upper() == "DONE" for row in shared)
    shared_total = len(shared)
    rate_a = 100 * shared_done_a / shared_total if shared_total else 0.0
    rate_b = 100 * shared_done_b / shared_total if shared_total else 0.0
    done_a, total_a = done_counts(rows, "a")
    done_b, total_b = done_counts(rows, "b")
    added_done = sum(
        row.change_class == "ADDED" and row.status_b.upper() == "DONE"
        for row in rows
    )
    removed_done = sum(
        row.change_class == "REMOVED" and row.status_a.upper() == "DONE"
        for row in rows
    )
    datasets = sorted({row.dataset for row in rows})

    lines = [
        f"# Sentence-status comparison: {label_a} → {label_b}", "",
        "Sentences are matched by `(dataset, sentence_uid)`. Rows with missing or "
        "duplicate identities are excluded and reported as integrity issues.", "",
        "## Headline results", "",
        "| Measure | Count |", "|---|---:|",
        f"| Shared sentences | {shared_total} |",
        f"| REVIEW → DONE (improvements) | {classes['IMPROVEMENT']} |",
        f"| DONE → REVIEW (regressions) | {classes['REGRESSION']} |",
        f"| Net progress among shared sentences | {classes['IMPROVEMENT'] - classes['REGRESSION']:+d} |",
        f"| Added sentences | {classes['ADDED']} |",
        f"| Removed sentences | {classes['REMOVED']} |",
        f"| Other status changes | {classes['STATUS_CHANGE']} |",
        f"| Integrity issues | {len(issues)} |", "",
        "## DONE accounting", "",
        "| Measure | State A | State B | Change |", "|---|---:|---:|---:|",
        f"| DONE sentences (all present rows) | {done_a}/{total_a} | {done_b}/{total_b} | {done_b - done_a:+d} |",
        f"| DONE among shared sentences | {shared_done_a}/{shared_total} | {shared_done_b}/{shared_total} | {shared_done_b - shared_done_a:+d} |",
        f"| DONE rate among shared sentences | {rate_a:.{percentage_digits}f}% | {rate_b:.{percentage_digits}f}% | {rate_b - rate_a:+.{percentage_digits}f} pp |",
        "", f"Added DONE sentences: **{added_done}**. Removed DONE sentences: **{removed_done}**.",
        "", "## Results by dataset", "",
        "| Dataset | Shared | Improvements | Regressions | Net progress | Added | Removed |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for dataset in datasets:
        subset = [row for row in rows if row.dataset == dataset]
        count = Counter(row.change_class for row in subset)
        shared_dataset = sum(row.status_a != "" and row.status_b != "" for row in subset)
        markdown_dataset = dataset.replace("|", "\\|")
        lines.append(
            f"| {markdown_dataset} | {shared_dataset} | "
            f"{count['IMPROVEMENT']} | {count['REGRESSION']} | "
            f"{count['IMPROVEMENT'] - count['REGRESSION']:+d} | "
            f"{count['ADDED']} | {count['REMOVED']} |"
        )
    lines.extend(["", "## Improved sentences", ""])
    lines.extend(markdown_uid_list(rows, "IMPROVEMENT"))
    lines.extend(["", "## Regressed sentences", ""])
    lines.extend(markdown_uid_list(rows, "REGRESSION"))
    lines.extend([
        "", "## Sources", "",
        f"- **{label_a}:** `{source_a}`", f"- **{label_b}:** `{source_b}`", "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare two sentence_status_individual.tsv runs by stable UID."
    )
    parser.add_argument("run_a", type=Path, metavar="RUN_A_TSV")
    parser.add_argument("run_b", type=Path, metavar="RUN_B_TSV")
    parser.add_argument("--label-a", default="A", help="display label for state A")
    parser.add_argument("--label-b", default="B", help="display label for state B")
    parser.add_argument("--outdir", type=Path, default=Path("data/reports/status/A-to-B"))
    parser.add_argument(
        "--normalize-status", action="store_true",
        help="convert statuses to uppercase before comparison",
    )
    parser.add_argument(
        "--strict-integrity", action="store_true",
        help="fail instead of generating comparisons when identities are invalid",
    )
    parser.add_argument("--percentage-digits", type=int, default=2, metavar="N")
    return parser


def run(args: argparse.Namespace) -> list[Path]:
    if args.percentage_digits < 0:
        raise ValueError("--percentage-digits must be zero or greater")
    rows_a = read_run(args.run_a, uppercase=args.normalize_status)
    rows_b = read_run(args.run_b, uppercase=args.normalize_status)
    index_a, issues_a = index_rows(rows_a, args.label_a)
    index_b, issues_b = index_rows(rows_b, args.label_b)
    issues = issues_a + issues_b
    if issues and args.strict_integrity:
        raise ValueError(
            f"found {len(issues)} integrity issue(s); rerun without "
            "--strict-integrity to report them and compare valid rows"
        )
    comparisons = compare_runs(index_a, index_b)
    args.outdir.mkdir(parents=True, exist_ok=True)
    stem = f"sentence_status_{safe_label(args.label_a)}_to_{safe_label(args.label_b)}"
    outputs = [
        args.outdir / f"{stem}.tsv",
        args.outdir / f"{stem}_statistics.tsv",
        args.outdir / f"{stem}_summary.md",
        args.outdir / f"{stem}_integrity.tsv",
    ]
    write_comparison(comparisons, outputs[0])
    write_statistics(comparisons, outputs[1])
    write_summary(
        comparisons, issues, outputs[2], label_a=args.label_a,
        label_b=args.label_b, percentage_digits=args.percentage_digits,
        source_a=args.run_a, source_b=args.run_b,
    )
    write_integrity(issues, outputs[3])
    return outputs


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    try:
        outputs = run(args)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for output in outputs:
        print(f"Wrote {output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
