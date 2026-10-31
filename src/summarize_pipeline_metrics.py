#!/usr/bin/env python3
"""
Summarize publication-oriented metrics from pipeline_publication_metrics.py JSON output.

This script reads the JSON report produced by pipeline_publication_metrics.py and
creates a second-level summary focused on Halstead metrics and their relation to
cyclomatic complexity. It does not recompute metrics from source code.

Typical use:

    summarize_pipeline_metrics.py \
        pipeline_publication_metrics.edt.json \
        --top 20 \
        --publication-top 10 \
        --markdown-out pipeline_metrics_tables.md \
        --json-out pipeline_metrics_summary.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

JsonDict = Dict[str, Any]

HALSTEAD_KEYS = ("volume", "difficulty", "effort", "bugs")


def fmt_float(value: Any, digits: int = 2) -> str:
    """Format a number for human-readable tables."""
    if value is None:
        return "NA"
    try:
        return f"{float(value):,.{digits}f}".replace(",", " ")
    except Exception:
        return str(value)


def fmt_int(value: Any) -> str:
    """Format an integer with spaces as thousands separators."""
    if value is None:
        return "NA"
    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return str(value)


def short_file(path: str) -> str:
    """Return a compact filename for display."""
    return Path(path).name


def load_report(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_nested(report: JsonDict, *keys: str) -> Any:
    current: Any = report
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def collect_halstead_files(report: JsonDict) -> List[JsonDict]:
    """Collect file-level Halstead totals."""
    raw = get_nested(report, "software_metrics", "radon_hal", "raw") or {}
    rows: List[JsonDict] = []

    for file_path, data in raw.items():
        if not isinstance(data, dict):
            continue
        total = data.get("total") or {}
        if not isinstance(total, dict):
            continue
        row = {"file": file_path, "file_short": short_file(file_path)}
        row.update({key: total.get(key) for key in total})
        rows.append(row)

    return rows


def collect_halstead_functions(report: JsonDict) -> List[JsonDict]:
    """Collect function-level Halstead metrics."""
    raw = get_nested(report, "software_metrics", "radon_hal", "raw") or {}
    rows: List[JsonDict] = []

    for file_path, data in raw.items():
        if not isinstance(data, dict):
            continue
        functions = data.get("functions") or {}
        if not isinstance(functions, dict):
            continue

        for func_name, metrics in functions.items():
            if not isinstance(metrics, dict):
                continue
            row = {
                "file": file_path,
                "file_short": short_file(file_path),
                "name": func_name,
            }
            row.update({key: metrics.get(key) for key in metrics})
            rows.append(row)

    return rows


def collect_cc_functions(report: JsonDict) -> List[JsonDict]:
    """Collect function/method cyclomatic-complexity entries.

    Radon cc JSON contains both class records and individual method/function records.
    This function keeps only function/method entries and ignores class aggregate rows.
    """
    raw = get_nested(report, "software_metrics", "radon_cc", "raw") or {}
    rows: List[JsonDict] = []

    for file_path, items in raw.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("type") not in {"function", "method"}:
                continue
            rows.append(
                {
                    "file": file_path,
                    "file_short": short_file(file_path),
                    "name": item.get("name"),
                    "lineno": item.get("lineno"),
                    "endline": item.get("endline"),
                    "type": item.get("type"),
                    "classname": item.get("classname"),
                    "cc": item.get("complexity"),
                    "cc_rank": item.get("rank"),
                }
            )
    return rows


def build_cc_index(cc_rows: List[JsonDict]) -> Dict[Tuple[str, str], List[JsonDict]]:
    """Index CC rows by (file, function name).

    Halstead function records do not include line numbers, so file + function name is
    the safest common key. The value is a list because names such as property getters
    may occur more than once.
    """
    index: Dict[Tuple[str, str], List[JsonDict]] = {}
    for row in cc_rows:
        key = (row.get("file"), row.get("name"))
        index.setdefault(key, []).append(row)
    return index


def attach_cc_to_halstead(hal_rows: List[JsonDict], cc_rows: List[JsonDict]) -> List[JsonDict]:
    """Attach CC only when (file, name) identifies exactly one CC record.

    Radon's Halstead function data have no line numbers. Duplicate function names
    cannot be disambiguated reliably, so their CC fields remain unavailable.
    """
    cc_index = build_cc_index(cc_rows)
    enriched: List[JsonDict] = []

    for row in hal_rows:
        out = dict(row)
        matches = cc_index.get((row.get("file"), row.get("name")), [])
        out.update({
            "cc": None,
            "cc_rank": None,
            "lineno": None,
            "endline": None,
            "cc_type": None,
            "classname": None,
            "cc_match_count": len(matches),
            "cc_match_status": "ambiguous" if len(matches) > 1 else ("missing" if not matches else "unique"),
        })
        if len(matches) == 1:
            match = matches[0]
            out.update({
                "cc": match.get("cc"),
                "cc_rank": match.get("cc_rank"),
                "lineno": match.get("lineno"),
                "endline": match.get("endline"),
                "cc_type": match.get("type"),
                "classname": match.get("classname"),
            })
        enriched.append(out)

    return enriched

def numeric_values(rows: Iterable[JsonDict], key: str, *, positive_only: bool = False) -> List[float]:
    values: List[float] = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)):
            if positive_only and value <= 0:
                continue
            values.append(float(value))
    return values


def summarize_metric(rows: List[JsonDict], key: str, *, positive_only: bool = False) -> JsonDict:
    values = numeric_values(rows, key, positive_only=positive_only)
    if not values:
        return {"count": 0, "mean": None, "median": None, "maximum": None, "minimum": None, "total": None}
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "maximum": max(values),
        "minimum": min(values),
        "total": sum(values),
    }


def top_rows(rows: List[JsonDict], key: str, limit: int) -> List[JsonDict]:
    return sorted(rows, key=lambda row: row.get(key) or 0, reverse=True)[:limit]


def rank_map(rows: List[JsonDict], key: str) -> Dict[Tuple[str, str], int]:
    ranked = sorted(rows, key=lambda row: row.get(key) or 0, reverse=True)
    return {(row.get("file"), row.get("name")): i + 1 for i, row in enumerate(ranked)}


def add_rank_comparisons(rows: List[JsonDict]) -> List[JsonDict]:
    effort_rank = rank_map(rows, "effort")
    volume_rank = rank_map(rows, "volume")
    cc_rank = rank_map([r for r in rows if r.get("cc") is not None], "cc")

    out: List[JsonDict] = []
    for row in rows:
        key = (row.get("file"), row.get("name"))
        new_row = dict(row)
        new_row["halstead_effort_rank"] = effort_rank.get(key)
        new_row["halstead_volume_rank"] = volume_rank.get(key)
        new_row["cc_numeric_rank"] = cc_rank.get(key)
        out.append(new_row)
    return out


def markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    def cell(value: Any) -> str:
        text = str(value)
        return text.replace("|", "\\|").replace("\n", " ")

    lines = []
    lines.append("| " + " | ".join(cell(h) for h in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(lines)


def halstead_summary_table(summary: JsonDict) -> str:
    rows = []
    for key in ["volume", "difficulty", "effort"]:
        s = summary["function_halstead_summary"].get(key, {})
        rows.append(
            [
                key.capitalize(),
                fmt_float(s.get("mean")),
                fmt_float(s.get("median")),
                fmt_float(s.get("maximum")),
            ]
        )

    bugs = summary["function_halstead_summary"].get("bugs", {})
    rows.append(
        [
            "Bugs",
            fmt_float(bugs.get("mean"), 4),
            fmt_float(bugs.get("median"), 4),
            f"total={fmt_float(bugs.get('total'), 2)}; max={fmt_float(bugs.get('maximum'), 4)}",
        ]
    )

    return markdown_table(["Metric", "Mean", "Median", "Maximum / total"], rows)


def function_table(rows: List[JsonDict], limit: int) -> str:
    table_rows: List[List[Any]] = []
    for row in rows[:limit]:
        name = row.get("name") or ""
        file_name = row.get("file_short") or ""
        line = row.get("lineno") or ""
        table_rows.append(
            [
                name,
                file_name,
                line,
                fmt_int(row.get("cc")) if row.get("cc") is not None else "NA",
                row.get("cc_rank") or "NA",
                fmt_float(row.get("volume")),
                fmt_float(row.get("difficulty")),
                fmt_float(row.get("effort")),
                fmt_float(row.get("bugs"), 4),
            ]
        )
    return markdown_table(
        ["Function", "File", "Line", "CC", "CC rank", "Volume", "Difficulty", "Effort", "Bugs"],
        table_rows,
    )


def compact_publication_table(rows: List[JsonDict], limit: int) -> str:
    table_rows: List[List[Any]] = []
    for row in rows[:limit]:
        table_rows.append(
            [
                row.get("name") or "",
                row.get("file_short") or "",
                fmt_int(row.get("cc")) if row.get("cc") is not None else "NA",
                row.get("cc_rank") or "NA",
                fmt_float(row.get("volume")),
                fmt_float(row.get("effort")),
            ]
        )
    return markdown_table(
        ["Function", "File", "CC", "CC rank", "Halstead volume", "Halstead effort"],
        table_rows,
    )


def file_halstead_table(rows: List[JsonDict]) -> str:
    ranked = top_rows(rows, "effort", len(rows))
    table_rows = [
        [
            row.get("file_short"),
            fmt_float(row.get("volume")),
            fmt_float(row.get("difficulty")),
            fmt_float(row.get("effort")),
            fmt_float(row.get("bugs"), 4),
        ]
        for row in ranked
    ]
    return markdown_table(["File", "Volume", "Difficulty", "Effort", "Bugs"], table_rows)


def build_summary(report: JsonDict, top_n: int, publication_top: int) -> JsonDict:
    hal_files = collect_halstead_files(report)
    hal_functions = collect_halstead_functions(report)
    cc_functions = collect_cc_functions(report)
    enriched = attach_cc_to_halstead(hal_functions, cc_functions)
    enriched = add_rank_comparisons(enriched)

    function_summary = {
        key: summarize_metric(enriched, key, positive_only=False) for key in HALSTEAD_KEYS
    }
    function_summary_positive = {
        key: summarize_metric(enriched, key, positive_only=True) for key in HALSTEAD_KEYS
    }
    file_summary = {key: summarize_metric(hal_files, key, positive_only=False) for key in HALSTEAD_KEYS}

    top_by_effort = top_rows(enriched, "effort", top_n)
    top_by_volume = top_rows(enriched, "volume", top_n)
    top_by_cc = top_rows([r for r in enriched if r.get("cc") is not None], "cc", top_n)
    top_files_by_effort = top_rows(hal_files, "effort", len(hal_files))

    report_metadata = report.get("metadata", {})

    return {
        "metadata": {
            "source_report": report_metadata.get("json_out"),
            "generated_at_original": report_metadata.get("generated_at"),
            "top_n": top_n,
            "publication_top": publication_top,
        },
        "counts": {
            "halstead_files": len(hal_files),
            "halstead_functions": len(hal_functions),
            "cc_functions_matched": sum(1 for row in enriched if row.get("cc") is not None),
            "cc_functions_unmatched": sum(1 for row in enriched if row.get("cc") is None),
            "cc_functions_ambiguous": sum(1 for row in enriched if row.get("cc_match_status") == "ambiguous"),
            "cc_functions_missing": sum(1 for row in enriched if row.get("cc_match_status") == "missing"),
        },
        "file_halstead_summary": file_summary,
        "function_halstead_summary": function_summary,
        "function_halstead_summary_positive_only": function_summary_positive,
        "top_files_by_halstead_effort": top_files_by_effort,
        "top_functions_by_halstead_effort": top_by_effort,
        "top_functions_by_halstead_volume": top_by_volume,
        "top_functions_by_cyclomatic_complexity": top_by_cc,
        "publication_table_top_by_effort": top_by_effort[:publication_top],
    }


def make_markdown(summary: JsonDict) -> str:
    lines: List[str] = []
    lines.append("# Kadiwéu converter pipeline: Halstead and complexity summary")
    lines.append("")
    counts = summary["counts"]
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- Files with Halstead metrics: **{fmt_int(counts.get('halstead_files'))}**")
    lines.append(f"- Functions with Halstead metrics: **{fmt_int(counts.get('halstead_functions'))}**")
    lines.append(f"- Functions matched with cyclomatic complexity: **{fmt_int(counts.get('cc_functions_matched'))}**")
    lines.append(f"- Functions not matched with cyclomatic complexity: **{fmt_int(counts.get('cc_functions_unmatched'))}**")
    lines.append(f"- Ambiguous function-name matches (CC withheld): **{fmt_int(counts.get('cc_functions_ambiguous'))}**")
    lines.append("")

    lines.append("## Halstead summary over functions")
    lines.append("")
    lines.append(halstead_summary_table(summary))
    lines.append("")

    lines.append("## Files ranked by Halstead effort")
    lines.append("")
    lines.append(file_halstead_table(summary["top_files_by_halstead_effort"]))
    lines.append("")

    lines.append("## Top functions by Halstead effort")
    lines.append("")
    lines.append(function_table(summary["top_functions_by_halstead_effort"], len(summary["top_functions_by_halstead_effort"])))
    lines.append("")

    lines.append("## Top functions by Halstead volume")
    lines.append("")
    lines.append(function_table(summary["top_functions_by_halstead_volume"], len(summary["top_functions_by_halstead_volume"])))
    lines.append("")

    lines.append("## Top functions by cyclomatic complexity, with Halstead metrics")
    lines.append("")
    lines.append(function_table(summary["top_functions_by_cyclomatic_complexity"], len(summary["top_functions_by_cyclomatic_complexity"])))
    lines.append("")

    lines.append("## Compact publication table: top functions by Halstead effort")
    lines.append("")
    lines.append(compact_publication_table(summary["publication_table_top_by_effort"], len(summary["publication_table_top_by_effort"])))
    lines.append("")

    return "\n".join(lines)


def print_console_summary(summary: JsonDict) -> None:
    print("# Halstead and complexity summary")
    print()
    counts = summary["counts"]
    print("## Coverage")
    print(f"Files with Halstead metrics: {fmt_int(counts.get('halstead_files'))}")
    print(f"Functions with Halstead metrics: {fmt_int(counts.get('halstead_functions'))}")
    print(f"Functions matched with CC: {fmt_int(counts.get('cc_functions_matched'))}")
    print(f"Functions not matched with CC: {fmt_int(counts.get('cc_functions_unmatched'))}")
    print(f"Ambiguous function-name matches (CC withheld): {fmt_int(counts.get('cc_functions_ambiguous'))}")
    print()

    print("## Halstead summary over functions")
    s = summary["function_halstead_summary"]
    for key in ["volume", "difficulty", "effort"]:
        item = s[key]
        print(
            f"{key.capitalize()}: mean={fmt_float(item.get('mean'))}; "
            f"median={fmt_float(item.get('median'))}; max={fmt_float(item.get('maximum'))}"
        )
    bugs = s["bugs"]
    print(
        f"Bugs: total={fmt_float(bugs.get('total'), 2)}; "
        f"mean={fmt_float(bugs.get('mean'), 4)}; max={fmt_float(bugs.get('maximum'), 4)}"
    )
    print()

    print("## Top 20 functions by Halstead effort")
    print(function_table(summary["top_functions_by_halstead_effort"], len(summary["top_functions_by_halstead_effort"])))
    print()

    print("## Top 20 functions by Halstead volume")
    print(function_table(summary["top_functions_by_halstead_volume"], len(summary["top_functions_by_halstead_volume"])))
    print()

    print("## Top functions by cyclomatic complexity, with Halstead metrics")
    print(function_table(summary["top_functions_by_cyclomatic_complexity"], len(summary["top_functions_by_cyclomatic_complexity"])))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize Halstead and cyclomatic-complexity metrics from a pipeline metrics JSON report."
    )
    parser.add_argument("report_json", help="JSON report produced by pipeline_publication_metrics.py")
    parser.add_argument("--top", type=int, default=20, help="Number of top functions to report. Default: 20")
    parser.add_argument(
        "--publication-top",
        type=int,
        default=10,
        help="Number of functions in compact publication table. Default: 10",
    )
    parser.add_argument(
        "--markdown-out",
        default=None,
        help="Optional Markdown output file for publication-ready tables.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional JSON output file with the computed summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_path = Path(args.report_json).expanduser().resolve()
    report = load_report(report_path)
    summary = build_summary(report, top_n=args.top, publication_top=args.publication_top)

    print_console_summary(summary)

    if args.json_out:
        json_path = Path(args.json_out).expanduser().resolve()
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print()
        print(f"JSON summary written to: {json_path}")

    if args.markdown_out:
        md_path = Path(args.markdown_out).expanduser().resolve()
        md_path.write_text(make_markdown(summary), encoding="utf-8")
        print(f"Markdown tables written to: {md_path}")


if __name__ == "__main__":
    main()
