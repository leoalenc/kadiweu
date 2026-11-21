#!/usr/bin/env python3
"""Plot the development history of kadiweu_json_to_conllu.py from its TSV.

Example:
    python plot_converter_history.py converter_history.tsv \
        -o converter_history_evolution.pdf

The script also writes a PNG preview alongside the PDF.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if not rows:
        raise SystemExit(f"No data rows found in {path}")
    rows.sort(key=lambda row: datetime.fromisoformat(row["date"]))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tsv", type=Path, help="history TSV produced by converter_history_stats.py")
    parser.add_argument("-o", "--output", type=Path, default=Path("converter_history_evolution.pdf"),
                        help="output PDF path (default: converter_history_evolution.pdf)")
    args = parser.parse_args()
    rows = load_rows(args.tsv)

    dates = [datetime.fromisoformat(row["date"]) for row in rows]
    sloc = [int(row["sloc"]) for row in rows]
    lloc = [int(row["lloc"]) for row in rows]
    functions = [int(row["function_count"]) for row in rows]
    mean_cc = [float(row["mean_complexity"]) for row in rows]
    max_cc = [int(row["max_complexity"]) for row in rows]

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10})
    fig, axes = plt.subplots(3, 1, figsize=(8.2, 7.4), sharex=True,
                             gridspec_kw={"height_ratios": [1.25, 0.8, 1.0]})
    fig.subplots_adjust(left=0.12, right=0.97, top=0.91, bottom=0.12, hspace=0.16)
    fig.suptitle(r"Evolution of the main Kadiwéu converter script", x=0.12, ha="left",
                 fontsize=14, fontweight="semibold")

    ax = axes[0]
    ax.plot(dates, sloc, color="#176B87", linewidth=2.2, marker="o", markersize=3.5,
            label="SLOC (Radon)")
    ax.plot(dates, lloc, color="#E07A32", linewidth=1.8, marker=".", markersize=4,
            linestyle="--", label="LLOC (Radon)")
    ax.set_ylabel("Lines")
    ax.set_title("Code size", loc="left", pad=5)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    ax.annotate(f"{sloc[0]:,} SLOC", (dates[0], sloc[0]), xytext=(6, 7),
                textcoords="offset points", fontsize=8, color="#176B87")
    ax.annotate(f"{sloc[-1]:,} SLOC", (dates[-1], sloc[-1]), xytext=(-7, 8),
                textcoords="offset points", ha="right", fontsize=8, color="#176B87")

    ax = axes[1]
    ax.plot(dates, functions, color="#5B7F35", linewidth=2, marker="o", markersize=3.5)
    ax.set_ylabel("Functions\nand methods")
    ax.set_title("Number of functions and methods", loc="left", pad=5)

    ax = axes[2]
    ax.plot(dates, max_cc, color="#9B3A62", linewidth=2.1, marker="o", markersize=3.5,
            label="Maximum function complexity")
    ax.plot(dates, mean_cc, color="#6A5D9B", linewidth=1.8, marker=".", markersize=4,
            linestyle="--", label="Mean function complexity")
    ax.set_ylabel("Cyclomatic\ncomplexity")
    ax.set_title("Cyclomatic complexity", loc="left", pad=5)
    ax.legend(frameon=False, loc="upper left")
    ax.set_xlabel("Commit date")

    for ax in axes:
        ax.grid(axis="y", color="#D9DEE3", linewidth=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.margins(x=0.025)
    axes[-1].xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=8))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.text(0.12, 0.035,
             "Metrics describe kadiweu_json_to_conllu.py only; each point is a commit that changed the file.",
             fontsize=8, color="#555555")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight")
    png_path = args.output.with_suffix(".png")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    print(f"Wrote {args.output}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
