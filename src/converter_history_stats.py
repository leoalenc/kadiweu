#!/usr/bin/env python3
"""Write a TSV time series for kadiweu_json_to_conllu.py in this repository.

Metrics are computed with Radon (``pip install radon``), so SLOC and LLOC
follow Radon's definitions. The output contains one row per commit in which
the target file changed, ordered from oldest to newest. Renames are followed.

Run from any directory inside the repository:
    python path/to/converter_history_stats.py -o converter_history.tsv

The target path is discovered from Git's tracked-file list by basename, so
the script continues to work if the converter is moved within the repository.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from pathlib import PurePosixPath


def git(repo: str, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", "-C", repo, *args], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def revisions(repo: str, target: str) -> list[tuple[str, str]]:
    raw = git(repo, "log", "--follow", "--format=%H%x09%cI", "--", target)
    rows = []
    for line in raw.decode().splitlines():
        if line:
            commit, date = line.split("\t", 1)
            rows.append((commit, date))
    return list(reversed(rows))


def path_at_revision(repo: str, commit: str, target: str) -> str:
    """Resolve the historical path, including commits before a rename."""
    names = git(repo, "show", "--format=", "--name-only", commit).decode().splitlines()
    candidates = [name for name in names if name and name.endswith(".py")]
    candidates.extend([target])
    for name in dict.fromkeys(candidates):
        probe = subprocess.run(
            ["git", "-C", repo, "cat-file", "-e", f"{commit}:{name}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if probe.returncode == 0 and PurePosixPath(name).name == PurePosixPath(target).name:
            return name
    # For a rename, git's name-only output usually includes the old path too.
    for name in dict.fromkeys(candidates):
        probe = subprocess.run(
            ["git", "-C", repo, "cat-file", "-e", f"{commit}:{name}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if probe.returncode == 0:
            return name
    raise RuntimeError(f"Could not locate {target!r} in commit {commit}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository directory (default: current directory)")
    parser.add_argument("-o", "--output", default="-", help="TSV output path (default: stdout)")
    args = parser.parse_args()

    repo = git(args.repo, "rev-parse", "--show-toplevel").decode().strip()
    target_name = "kadiweu_json_to_conllu.py"
    tracked = git(repo, "ls-files", "--", f"*{target_name}").decode().splitlines()
    target_matches = [path for path in tracked if PurePosixPath(path).name == target_name]
    # When launched from src/, prefer the converter next to the script. This
    # also handles repositories that retain another tracked copy elsewhere.
    cwd_candidate = os.path.relpath(os.path.join(os.getcwd(), target_name), repo)
    if cwd_candidate in target_matches:
        target_matches = [cwd_candidate]
    if len(target_matches) != 1:
        parser.error(
            f"Expected one tracked {target_name!r} in {repo!r}; found {len(target_matches)} "
            f"after preferring the current directory. Candidates: {', '.join(target_matches)}"
        )
    target = target_matches[0]

    try:
        from radon.complexity import cc_visit
        from radon.raw import analyze
    except ImportError:
        parser.error("Radon is required; install it with: python -m pip install radon")

    history = revisions(repo, target)
    if not history:
        parser.error(f"No commits found for {target!r} in {repo!r}")

    fields = [
        "commit", "date", "file", "total_lines", "blank_lines", "comment_lines",
        "multi_lines", "sloc", "lloc", "function_count", "mean_complexity",
        "max_complexity", "max_complexity_function",
    ]
    output = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8", newline="")
    try:
        writer = csv.DictWriter(output, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for commit, date in history:
            path = path_at_revision(repo, commit, target)
            source = git(repo, "show", f"{commit}:{path}").decode("utf-8", "replace")
            raw = analyze(source)
            blocks = cc_visit(source)
            complexities = [(block.name, block.complexity) for block in blocks]
            mean_cc = sum(score for _, score in complexities) / len(complexities) if complexities else 0
            max_name, max_cc = max(complexities, key=lambda item: item[1]) if complexities else ("", 0)
            writer.writerow({
                "commit": commit,
                "date": date,
                "file": path,
                "total_lines": raw.loc,
                "blank_lines": raw.blank,
                "comment_lines": raw.comments,
                "multi_lines": raw.multi,
                "sloc": raw.sloc,
                "lloc": raw.lloc,
                "function_count": len(complexities),
                "mean_complexity": f"{mean_cc:.2f}",
                "max_complexity": max_cc,
                "max_complexity_function": max_name,
            })
    finally:
        if output is not sys.stdout:
            output.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
