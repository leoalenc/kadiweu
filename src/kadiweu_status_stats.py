#!/usr/bin/env python3
"""Statistics for constituency-tree statuses in Tycho Brahe JSON exports.

The program reads the sentence-level ``status`` field used for constituency
annotation. Status values are discovered dynamically: values other than
``DONE`` and ``REVIEW`` require no code changes. Missing or blank values are
reported explicitly.

Examples
--------
Generate TSV and Markdown tables:

    python3 kadiweu_status_stats.py \
        data/ped-gramm.json data/hil-data.json data/van-data.json \
        --outdir data/reports/status

Also generate per-corpus pie charts and a comparative 100% stacked bar chart:

    python3 kadiweu_status_stats.py \
        data/ped-gramm.json data/hil-data.json data/van-data.json \
        --outdir data/reports/status \
        --chart pie --chart stacked-bar --chart-format svg --show

Assign stable corpus labels independently of filenames:

    python3 kadiweu_status_stats.py \
        --corpus ped-gramm=data/ped-gramm.json \
        --corpus hil-data=data/hil-data.json \
        --corpus van-data=data/van-data.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_MISSING_LABEL = "MISSING"
DEFAULT_OUTDIR = Path("data/reports/status")

# Known statuses retain the same color in every figure. Additional statuses
# receive colors deterministically from matplotlib's tab20 palette.
KNOWN_STATUS_COLORS = {
    "DONE": "#2E7D32",
    "REVIEW": "#F9A825",
    "TODO": "#757575",
    "AUTO": "#1976D2",
    "IN_PROGRESS": "#7B1FA2",
    DEFAULT_MISSING_LABEL: "#C62828",
}


@dataclass(frozen=True)
class CorpusSpec:
    """A display name paired with a JSON input path."""

    name: str
    path: Path


@dataclass(frozen=True)
class StatusRow:
    """One tidy-table row."""

    corpus: str
    constituency_status: str
    count: int
    percentage: float
    total: int


def is_sentence_object(obj: Any) -> bool:
    """Return whether *obj* resembles a Tycho Brahe sentence object.

    This intentionally follows the heuristic used by
    ``kadiweu_tag_profiles.py``: a sentence has textual content and a ``struct``
    mapping containing tokens, chunks, or a CoNLL-U representation.
    """

    if not isinstance(obj, dict):
        return False
    if not isinstance(obj.get("text"), str):
        return False
    struct = obj.get("struct")
    return isinstance(struct, dict) and any(
        key in struct for key in ("tokens", "chunks", "conllu")
    )


def walk_sentences(obj: Any) -> Iterable[dict[str, Any]]:
    """Yield sentence objects recursively in source order."""

    if isinstance(obj, dict):
        if is_sentence_object(obj):
            yield obj
            # Sentence-internal structures cannot contain another sentence.
            return
        for value in obj.values():
            yield from walk_sentences(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk_sentences(value)


def load_sentences(path: Path) -> list[dict[str, Any]]:
    """Load *path* and return its sentence objects in source order."""

    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    return list(walk_sentences(data))


def normalize_status(
    raw_status: Any,
    *,
    missing_label: str = DEFAULT_MISSING_LABEL,
    uppercase: bool = False,
) -> str:
    """Convert a raw sentence status to its report label."""

    if raw_status is None:
        return missing_label
    status = str(raw_status).strip()
    if not status:
        return missing_label
    return status.upper() if uppercase else status


def is_missing_status(raw_status: Any) -> bool:
    """Return whether a raw status is absent or blank."""

    return raw_status is None or not str(raw_status).strip()


def count_statuses(
    sentences: Iterable[Mapping[str, Any]],
    *,
    status_field: str = "status",
    missing_label: str = DEFAULT_MISSING_LABEL,
    uppercase: bool = False,
) -> Counter[str]:
    """Count dynamically discovered constituency-tree status values."""

    return Counter(
        normalize_status(
            sentence.get(status_field),
            missing_label=missing_label,
            uppercase=uppercase,
        )
        for sentence in sentences
    )


def build_rows(
    counts_by_corpus: Mapping[str, Counter[str]],
    *,
    combined: bool = True,
    combined_label: str = "ALL",
) -> list[StatusRow]:
    """Build tidy rows with percentages computed within each corpus."""

    report_counts: OrderedDict[str, Counter[str]] = OrderedDict(
        (name, Counter(counts)) for name, counts in counts_by_corpus.items()
    )
    if combined:
        aggregate: Counter[str] = Counter()
        for counts in counts_by_corpus.values():
            aggregate.update(counts)
        report_counts[combined_label] = aggregate

    # Preserve corpus order while giving every corpus the same status order.
    statuses = sorted(
        {status for counts in report_counts.values() for status in counts},
        key=status_sort_key,
    )

    rows: list[StatusRow] = []
    for corpus, counts in report_counts.items():
        total = sum(counts.values())
        for status in statuses:
            count = counts.get(status, 0)
            percentage = (100.0 * count / total) if total else 0.0
            rows.append(StatusRow(corpus, status, count, percentage, total))
    return rows


def status_sort_key(status: str) -> tuple[int, str]:
    """Sort common workflow statuses first and all others alphabetically."""

    preferred = {
        "DONE": 0,
        "REVIEW": 1,
        "IN_PROGRESS": 2,
        "TODO": 3,
        "AUTO": 4,
        DEFAULT_MISSING_LABEL: 99,
    }
    return preferred.get(status.upper(), 50), status.casefold()


def write_delimited(
    rows: Sequence[StatusRow],
    path: Path,
    *,
    delimiter: str,
    percentage_digits: int,
) -> None:
    """Write a tidy TSV or CSV report."""

    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter=delimiter)
        writer.writerow(
            ["corpus", "constituency_status", "count", "percentage", "total"]
        )
        for row in rows:
            writer.writerow(
                [
                    row.corpus,
                    row.constituency_status,
                    row.count,
                    f"{row.percentage:.{percentage_digits}f}",
                    row.total,
                ]
            )


def write_markdown(
    rows: Sequence[StatusRow],
    path: Path,
    *,
    percentage_digits: int,
    source_paths: Sequence[CorpusSpec],
) -> None:
    """Write a human-readable Markdown report."""

    lines = [
        "# Constituency-tree sentence status statistics",
        "",
        "The status is read from the sentence-level `status` field in each "
        "Tycho Brahe JSON export.",
        "",
        "| Corpus | Constituency status | Count | Percentage | Total |",
        "|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {escape_markdown(row.corpus)} "
            f"| {escape_markdown(row.constituency_status)} "
            f"| {row.count} "
            f"| {row.percentage:.{percentage_digits}f}% "
            f"| {row.total} |"
        )

    lines.extend(["", "## Sources", ""])
    for spec in source_paths:
        lines.append(f"- `{spec.name}`: `{spec.path}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def escape_markdown(value: str) -> str:
    """Escape table-breaking characters."""

    return value.replace("\\", "\\\\").replace("|", "\\|")


def print_table(rows: Sequence[StatusRow], percentage_digits: int) -> None:
    """Print a compact aligned table to stdout."""

    headers = ("corpus", "constituency_status", "count", "percentage", "total")
    values = [
        (
            row.corpus,
            row.constituency_status,
            str(row.count),
            f"{row.percentage:.{percentage_digits}f}%",
            str(row.total),
        )
        for row in rows
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in values))
        for index in range(len(headers))
    ]
    print(
        f"{headers[0]:<{widths[0]}}  {headers[1]:<{widths[1]}}  "
        f"{headers[2]:>{widths[2]}}  {headers[3]:>{widths[3]}}  "
        f"{headers[4]:>{widths[4]}}"
    )
    print("  ".join("-" * width for width in widths))
    for row in values:
        print(
            f"{row[0]:<{widths[0]}}  {row[1]:<{widths[1]}}  "
            f"{row[2]:>{widths[2]}}  {row[3]:>{widths[3]}}  "
            f"{row[4]:>{widths[4]}}"
        )


def slugify(value: str) -> str:
    """Return a filesystem-safe chart-name component."""

    slug = re.sub(r"[^\w.-]+", "-", value.strip(), flags=re.UNICODE)
    return slug.strip("-_.") or "corpus"


def get_status_colors(statuses: Sequence[str]) -> dict[str, Any]:
    """Return stable colors for known and newly encountered statuses."""

    import matplotlib.pyplot as plt

    colors: dict[str, Any] = {}
    unknown = [
        status
        for status in statuses
        if status.upper() not in KNOWN_STATUS_COLORS
    ]
    palette = plt.get_cmap("tab20")
    unknown_colors = {
        status: palette(index % palette.N) for index, status in enumerate(unknown)
    }
    for status in statuses:
        colors[status] = KNOWN_STATUS_COLORS.get(
            status.upper(), unknown_colors.get(status)
        )
    return colors


def plot_pies(
    counts_by_corpus: Mapping[str, Counter[str]],
    *,
    outdir: Path,
    formats: Sequence[str],
    percentage_digits: int,
) -> list[Path]:
    """Create one pie chart per corpus."""

    import matplotlib.pyplot as plt

    statuses = sorted(
        {status for counts in counts_by_corpus.values() for status in counts},
        key=status_sort_key,
    )
    colors = get_status_colors(statuses)
    outputs: list[Path] = []

    for corpus, counts in counts_by_corpus.items():
        present = [status for status in statuses if counts.get(status, 0)]
        values = [counts[status] for status in present]
        total = sum(values)
        labels = [
            f"{status} (n={counts[status]})"
            for status in present
        ]

        figure, axis = plt.subplots(figsize=(7.2, 5.4), constrained_layout=True)
        axis.pie(
            values,
            labels=labels,
            colors=[colors[status] for status in present],
            autopct=lambda pct: f"{pct:.{percentage_digits}f}%",
            startangle=90,
            counterclock=False,
            wedgeprops={"edgecolor": "white", "linewidth": 1},
        )
        axis.set_title(f"Constituency-tree status: {corpus} (N={total})")

        for chart_format in formats:
            output = outdir / f"sentence_status_{slugify(corpus)}_pie.{chart_format}"
            figure.savefig(output, dpi=300 if chart_format == "png" else None)
            outputs.append(output)
        plt.close(figure)

    return outputs


def plot_stacked_bar(
    counts_by_corpus: Mapping[str, Counter[str]],
    *,
    outdir: Path,
    formats: Sequence[str],
) -> list[Path]:
    """Create a 100% stacked bar chart comparing corpora."""

    import matplotlib.pyplot as plt

    corpora = list(counts_by_corpus)
    statuses = sorted(
        {status for counts in counts_by_corpus.values() for status in counts},
        key=status_sort_key,
    )
    colors = get_status_colors(statuses)
    totals = [sum(counts_by_corpus[corpus].values()) for corpus in corpora]
    bottoms = [0.0] * len(corpora)

    width = max(7.2, 1.25 * len(corpora) + 3)
    figure, axis = plt.subplots(figsize=(width, 5.4), constrained_layout=True)
    for status in statuses:
        percentages = [
            (
                100.0 * counts_by_corpus[corpus].get(status, 0) / total
                if total
                else 0.0
            )
            for corpus, total in zip(corpora, totals)
        ]
        axis.bar(
            corpora,
            percentages,
            bottom=bottoms,
            label=status,
            color=colors[status],
            edgecolor="white",
            linewidth=0.8,
        )
        bottoms = [
            bottom + percentage
            for bottom, percentage in zip(bottoms, percentages)
        ]

    axis.set_ylim(0, 100)
    axis.set_ylabel("Sentences (%)")
    axis.set_title("Constituency-tree status by corpus")
    axis.legend(title="Status", bbox_to_anchor=(1.02, 1), loc="upper left")
    axis.spines[["top", "right"]].set_visible(False)

    outputs: list[Path] = []
    for chart_format in formats:
        output = outdir / f"sentence_status_stacked_bar.{chart_format}"
        figure.savefig(output, dpi=300 if chart_format == "png" else None)
        outputs.append(output)
    plt.close(figure)
    return outputs


def parse_corpus_assignment(value: str) -> CorpusSpec:
    """Parse ``NAME=PATH`` used by ``--corpus``."""

    name, separator, path_string = value.partition("=")
    if not separator or not name.strip() or not path_string.strip():
        raise argparse.ArgumentTypeError(
            "--corpus must have the form NAME=PATH"
        )
    return CorpusSpec(name.strip(), Path(path_string))


def resolve_corpora(
    json_files: Sequence[Path],
    assignments: Sequence[CorpusSpec],
) -> list[CorpusSpec]:
    """Resolve positional paths and explicit corpus assignments."""

    specs = [CorpusSpec(path.stem, path) for path in json_files]
    specs.extend(assignments)
    if not specs:
        raise ValueError("provide at least one JSON file or --corpus NAME=PATH")

    names = [spec.name for spec in specs]
    duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
    if duplicates:
        raise ValueError(
            "duplicate corpus name(s): " + ", ".join(duplicates)
            + "; use --corpus NAME=PATH to assign unique names"
        )
    return specs


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compute statistics for sentence-level constituency-tree statuses "
            "in Tycho Brahe JSON exports."
        )
    )
    parser.add_argument(
        "json_files",
        metavar="JSON",
        type=Path,
        nargs="*",
        help="one or more Tycho Brahe JSON exports",
    )
    parser.add_argument(
        "--corpus",
        action="append",
        default=[],
        type=parse_corpus_assignment,
        metavar="NAME=PATH",
        help="add a JSON input with an explicit corpus label (repeatable)",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=DEFAULT_OUTDIR,
        help=f"output directory (default: {DEFAULT_OUTDIR})",
    )
    parser.add_argument(
        "--status-field",
        default="status",
        help=(
            "sentence field containing the constituency-tree status "
            "(default: status)"
        ),
    )
    parser.add_argument(
        "--missing-label",
        default=DEFAULT_MISSING_LABEL,
        help=f"label for missing or blank statuses (default: {DEFAULT_MISSING_LABEL})",
    )
    parser.add_argument(
        "--normalize-status",
        action="store_true",
        help="strip statuses and convert them to uppercase",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail if a sentence has a missing or blank status",
    )
    parser.add_argument(
        "--table-format",
        action="append",
        choices=("tsv", "csv", "markdown"),
        dest="table_formats",
        help=(
            "table format to generate (repeatable; defaults to tsv and markdown)"
        ),
    )
    parser.add_argument(
        "--chart",
        action="append",
        choices=("pie", "stacked-bar"),
        default=[],
        help="chart type to generate (repeatable; charts are optional)",
    )
    parser.add_argument(
        "--chart-format",
        action="append",
        choices=("png", "svg"),
        dest="chart_formats",
        help="chart file format (repeatable; default: png)",
    )
    parser.add_argument(
        "--percentage-digits",
        type=int,
        default=2,
        metavar="N",
        help="decimal places in percentages (default: 2)",
    )
    parser.add_argument(
        "--no-combined",
        action="store_true",
        help="omit the combined ALL distribution from tables",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="print the table to standard output",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.percentage_digits < 0:
        raise ValueError("--percentage-digits must be zero or greater")
    if not args.missing_label.strip():
        raise ValueError("--missing-label cannot be empty")


def run(args: argparse.Namespace) -> tuple[list[StatusRow], list[Path]]:
    """Execute the report and return its rows and generated paths."""

    validate_args(args)
    corpora = resolve_corpora(args.json_files, args.corpus)
    counts_by_corpus: OrderedDict[str, Counter[str]] = OrderedDict()

    for spec in corpora:
        if not spec.path.is_file():
            raise FileNotFoundError(f"file not found: {spec.path}")
        sentences = load_sentences(spec.path)
        if not sentences:
            raise ValueError(f"no sentence objects found: {spec.path}")
        missing_count = sum(
            is_missing_status(sentence.get(args.status_field))
            for sentence in sentences
        )
        counts = count_statuses(
            sentences,
            status_field=args.status_field,
            missing_label=args.missing_label,
            uppercase=args.normalize_status,
        )
        if args.strict and missing_count:
            raise ValueError(
                f"{spec.path}: {missing_count} sentence(s) have "
                f"no non-blank {args.status_field!r} value"
            )
        counts_by_corpus[spec.name] = counts

    rows = build_rows(
        counts_by_corpus,
        combined=not args.no_combined,
    )
    args.outdir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    table_formats = args.table_formats or ["tsv", "markdown"]

    for table_format in dict.fromkeys(table_formats):
        if table_format == "tsv":
            output = args.outdir / "sentence_status_statistics.tsv"
            write_delimited(
                rows,
                output,
                delimiter="\t",
                percentage_digits=args.percentage_digits,
            )
        elif table_format == "csv":
            output = args.outdir / "sentence_status_statistics.csv"
            write_delimited(
                rows,
                output,
                delimiter=",",
                percentage_digits=args.percentage_digits,
            )
        else:
            output = args.outdir / "sentence_status_summary.md"
            write_markdown(
                rows,
                output,
                percentage_digits=args.percentage_digits,
                source_paths=corpora,
            )
        generated.append(output)

    chart_formats = list(dict.fromkeys(args.chart_formats or ["png"]))
    charts = list(dict.fromkeys(args.chart))
    if charts:
        try:
            import matplotlib

            matplotlib.use("Agg")
        except ImportError as error:
            raise RuntimeError(
                "chart generation requires matplotlib; install it or omit --chart"
            ) from error

    if "pie" in charts:
        generated.extend(
            plot_pies(
                counts_by_corpus,
                outdir=args.outdir,
                formats=chart_formats,
                percentage_digits=args.percentage_digits,
            )
        )
    if "stacked-bar" in charts:
        generated.extend(
            plot_stacked_bar(
                counts_by_corpus,
                outdir=args.outdir,
                formats=chart_formats,
            )
        )

    if args.show:
        print_table(rows, args.percentage_digits)
    return rows, generated


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)
    try:
        _rows, generated = run(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        f"Processed {len(resolve_corpora(args.json_files, args.corpus))} "
        f"corpus file(s).",
        file=sys.stderr,
    )
    for path in generated:
        print(f"Wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
