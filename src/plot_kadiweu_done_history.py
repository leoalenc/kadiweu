#!/usr/bin/env python3
"""Plot the total number of DONE sentences across committed TSV versions.

The script reads the Git history of a per-sentence status TSV without checking
out old revisions.  For every commit in which the file changed, it counts rows
whose status is DONE, writes a historical TSV, and creates a line chart.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


DEFAULT_FILE = "data/reports/status/sentence_status_individual.tsv"
DEFAULT_OUTPUT = "data/reports/status/done_history.svg"
DEFAULT_TABLE = "data/reports/status/done_history.tsv"
STATUS_COLUMNS = ("constituency_status", "status")


class HistoryError(RuntimeError):
    """An expected Git or TSV operation failed."""


@dataclass(frozen=True)
class HistoryPoint:
    commit: str
    short_commit: str
    committed_at: str
    date: str
    done: int
    total: int
    subject: str
    stage: str
    source_path: str


def run_git(repo: Path, arguments: Sequence[str]) -> str:
    command = ["git", "-C", str(repo), *arguments]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise HistoryError(f"Git command failed: {' '.join(command)}\n{detail}")
    return result.stdout


def find_repo(start: Path) -> Path:
    output = run_git(start, ["rev-parse", "--show-toplevel"])
    return Path(output.strip()).resolve()


def repo_relative_path(repo: Path, requested: Path) -> str:
    absolute = requested.resolve() if requested.is_absolute() else (Path.cwd() / requested).resolve()
    try:
        return absolute.relative_to(repo).as_posix()
    except ValueError as error:
        raise HistoryError(f"The tracked file must be inside the repository: {absolute}") from error


def commits_for_file(repo: Path, tracked_file: str) -> list[tuple[str, str, str, str]]:
    """Return commits and the file path valid at each commit.

    ``git log --follow`` crosses renames, but a blob still has to be requested
    from its pathname at that particular revision.  Therefore the name-status
    output is used to carry the pathname backwards across each rename.
    """
    marker = "@@KADIWEU_COMMIT@@"
    # %cI retains time and timezone, which keeps multiple commits on one date distinct.
    output = run_git(
        repo,
        [
            "log",
            "--follow",
            f"--format={marker}%H%x09%cI%x09%s",
            "--name-status",
            "--",
            tracked_file,
        ],
    )
    commits: list[tuple[str, str, str, str]] = []
    current_path = tracked_file
    pending: tuple[str, str, str] | None = None

    def finish_pending() -> None:
        nonlocal pending, current_path
        if pending is not None:
            commits.append((*pending, current_path))
            pending = None

    for line in output.splitlines():
        if not line.strip():
            continue
        if line.startswith(marker):
            finish_pending()
            parts = line[len(marker) :].split("\t", 2)
            if len(parts) != 3:
                raise HistoryError(f"Could not parse Git log line: {line!r}")
            pending = (parts[0], parts[1], parts[2])
            continue

        fields = line.split("\t")
        if fields[0].startswith("R") and len(fields) == 3:
            old_path, new_path = fields[1], fields[2]
            # At the rename commit the blob already has new_path.  Record that
            # commit first, then use old_path for all older revisions.
            if current_path == new_path:
                finish_pending()
                current_path = old_path

    finish_pending()
    if not commits:
        raise HistoryError(f"No committed versions found for {tracked_file}")
    return commits


def find_status_column(fieldnames: Sequence[str] | None) -> str:
    if not fieldnames:
        raise HistoryError("The TSV has no header row")
    normalized = {name.strip().lower(): name for name in fieldnames}
    for candidate in STATUS_COLUMNS:
        if candidate in normalized:
            return normalized[candidate]
    expected = " or ".join(repr(name) for name in STATUS_COLUMNS)
    raise HistoryError(
        f"The TSV has no {expected} column; columns found: {', '.join(fieldnames)}"
    )


def count_done(tsv_text: str, commit: str) -> tuple[int, int]:
    reader = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")
    status_column = find_status_column(reader.fieldnames)
    done = 0
    total = 0
    for line_number, row in enumerate(reader, start=2):
        if None in row:
            raise HistoryError(
                f"Malformed TSV row at {commit[:7]}:{line_number}: too many fields"
            )
        status = (row.get(status_column) or "").strip().upper()
        if not status:
            raise HistoryError(
                f"Empty {status_column!r} value at {commit[:7]}:{line_number}"
            )
        total += 1
        if status == "DONE":
            done += 1
    return done, total


def stage_from_path(path: str) -> str:
    """Use an A/B/C parent directory as the stage label when present."""
    parent = Path(path).parent.name
    return parent if parent in {"A", "B", "C"} else ""


def read_historical_files(
    repo: Path, commit: str, expected_path: str, tracked_file: str
) -> list[tuple[str, str, str]]:
    """Read one revision, expanding A/B/C JSON stages into separate snapshots.

    Each returned tuple contains ``(stage, contents, source_path)``.
    """
    try:
        contents = run_git(repo, ["show", f"{commit}:{expected_path}"])
        return [(stage_from_path(expected_path), contents, expected_path)]
    except HistoryError:
        pass

    basename = Path(tracked_file).name
    tree_paths = run_git(repo, ["ls-tree", "-r", "--name-only", commit]).splitlines()
    candidates = [path for path in tree_paths if Path(path).name == basename]

    if len(candidates) == 1:
        discovered_path = candidates[0]
        contents = run_git(repo, ["show", f"{commit}:{discovered_path}"])
        return [(stage_from_path(discovered_path), contents, discovered_path)]
    if not candidates:
        raise HistoryError(
            f"Could not find {basename} anywhere in the tree at {commit[:7]}."
        )

    staged = [(stage_from_path(path), path) for path in candidates]
    if all(stage for stage, _ in staged) and len({stage for stage, _ in staged}) == len(staged):
        changed_paths = set(
            run_git(
                repo,
                [
                    "diff-tree",
                    "--root",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    commit,
                ],
            ).splitlines()
        )
        changed_stages = [(stage, path) for stage, path in staged if path in changed_paths]
        # A/B/C are successive saved JSON stages. Files retained unchanged in
        # a later commit are not new observations and must not be plotted again.
        if changed_stages:
            staged = changed_stages
        results: list[tuple[str, str, str]] = []
        for stage, path in sorted(staged, key=lambda item: item[0]):
            contents = run_git(repo, ["show", f"{commit}:{path}"])
            results.append((stage, contents, path))
        return results

    formatted = ", ".join(candidates)
    raise HistoryError(
        f"More than one unlabelled historical file named {basename} exists at "
        f"{commit[:7]}: {formatted}."
    )


def collect_history(repo: Path, tracked_file: str) -> list[HistoryPoint]:
    # Git supplies commit groups newest first. Within a commit, stages remain
    # chronological (A, B, C), so reverse groups rather than individual points.
    groups: list[list[HistoryPoint]] = []
    for commit, committed_at, subject, historical_path in commits_for_file(repo, tracked_file):
        snapshots = read_historical_files(
            repo, commit, historical_path, tracked_file
        )
        group: list[HistoryPoint] = []
        for stage, contents, source_path in snapshots:
            done, total = count_done(contents, commit)
            group.append(
                HistoryPoint(
                    commit=commit,
                    short_commit=commit[:7],
                    committed_at=committed_at,
                    date=committed_at[:10],
                    done=done,
                    total=total,
                    subject=subject,
                    stage=stage,
                    source_path=source_path,
                )
            )
        groups.append(group)
    groups.reverse()
    return [point for group in groups for point in group]


def write_table(points: Sequence[HistoryPoint], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ("date", "committed_at", "commit", "stage", "done", "total", "source_path", "subject")
        )
        for point in points:
            writer.writerow(
                (
                    point.date,
                    point.committed_at,
                    point.commit,
                    point.stage,
                    point.done,
                    point.total,
                    point.source_path,
                    point.subject,
                )
            )


def plot_history(points: Sequence[HistoryPoint], output: Path, show: bool) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise HistoryError(
            "Plotting requires matplotlib. Install it with: python3 -m pip install matplotlib"
        ) from error

    positions = list(range(len(points)))
    counts = [point.done for point in points]
    labels = [
        f"{point.date}\n{point.short_commit}" + (f" · {point.stage}" if point.stage else "")
        for point in points
    ]

    figure_width = max(9, 1.25 * len(points))
    figure, axis = plt.subplots(figsize=(figure_width, 5.25))
    axis.plot(positions, counts, color="#276FBF", marker="o", linewidth=2.2, markersize=6)
    for position, count in zip(positions, counts):
        axis.annotate(
            str(count),
            (position, count),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    axis.set_title("Growth of DONE sentences")
    axis.set_xlabel("Committed version / stage")
    axis.set_ylabel("Number of DONE sentences")
    axis.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_xticks(positions, labels)
    axis.tick_params(axis="x", rotation=30)
    tick_step = 20
    upper_tick = max(tick_step, math.ceil(max(counts) / tick_step) * tick_step)
    axis.set_yticks(range(0, upper_tick + 1, tick_step))
    axis.set_ylim(0, upper_tick + max(4, upper_tick * 0.03))
    axis.margins(x=0.05)
    figure.tight_layout()

    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(figure)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plot the overall number of DONE sentences across committed versions "
            "of sentence_status_individual.tsv."
        )
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path(DEFAULT_FILE),
        help=f"tracked TSV file (default: {DEFAULT_FILE})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT),
        help=f"chart path; format follows its extension (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--table",
        type=Path,
        default=Path(DEFAULT_TABLE),
        help=f"historical TSV output (default: {DEFAULT_TABLE})",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        help="repository directory (default: detect from the current directory)",
    )
    parser.add_argument("--show", action="store_true", help="display the chart interactively")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        repo = find_repo((arguments.repo or Path.cwd()).resolve())
        tracked_file = repo_relative_path(repo, arguments.file)
        points = collect_history(repo, tracked_file)
        write_table(points, arguments.table)
        plot_history(points, arguments.output, arguments.show)
    except HistoryError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Processed {len(points)} committed version(s) of {tracked_file}.")
    print(f"Wrote {arguments.table}")
    print(f"Wrote {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
