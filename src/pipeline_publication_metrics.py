#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compute publication-oriented metrics for the Kadiwéu Tycho Brahe -> UD
converter pipeline.

Hybrid strategy:
1. Primary Python software metrics: radon raw, cc, mi, and hal.
2. AST-based logical-structure metrics.
3. Cross-check software-size metrics: cloc.
4. Project-specific linguistic-resource metrics: explicit JSON files only.

The script intentionally does NOT compute CoNLL-U treebank statistics, because
UD already provides standard Perl scripts for those figures.

Typical use from repository root:

    python3 pipeline_publication_metrics.py \
        --src src \
        --json-resource data/resources/kadiweu_default_overrides.json \
        --json-resource data/resources/gold_derived_overrides.json \
        --json-resource data/resources/kadiweu_manual_overrides.json \
        --json-resource data/resources/lexicon-kadiweu.json \
        --json-out pipeline_publication_metrics.json

Recommended external tools:

    sudo apt install cloc
    pip install radon

The script still runs if these tools are not installed, but the corresponding
sections of the report are marked as unavailable.
"""

from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

def collect_python_files(src: Path, exclude_dirs, exclude_files=()):
    """Select Python sources, excluding named directories and relative filenames."""
    excluded_dirs = set(exclude_dirs)
    excluded_files = {Path(name).as_posix() for name in exclude_files}
    return sorted(
        str(path)
        for path in src.rglob("*.py")
        if not any(part in excluded_dirs for part in path.relative_to(src).parts[:-1])
        and path.name not in excluded_files
        and path.relative_to(src).as_posix() not in excluded_files
    )
    

def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def run_command(command: Sequence[str]) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            list(command),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "command": list(command),
            "returncode": None,
            "stdout": "",
            "stderr": "command not found",
        }

    return {
        "available": True,
        "command": list(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_cloc(src: Path, exclude_dirs: list[str], exclude_files=()) -> Dict[str, Any]:
    """Cross-check precisely the Python files supplied to Radon.

    Passing explicit filenames avoids cloc's independent directory traversal and
    language/file inclusion rules changing the comparison population.
    """
    if shutil.which("cloc") is None:
        return {"available": False, "reason": "cloc not found in PATH", "raw": None, "summary": {}}

    files = sorted(collect_python_files(src, exclude_dirs, exclude_files))
    if not files:
        return {"available": False, "reason": "no Python files selected", "raw": None, "summary": {}}

    result = run_command(["cloc", "--json", "--force-lang=Python", *files])
    if result["returncode"] != 0:
        return {
            "available": False,
            "reason": "cloc failed",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    try:
        raw = json.loads(result["stdout"])
    except json.JSONDecodeError as e:
        return {
            "available": False,
            "reason": f"could not parse cloc JSON: {e}",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    total = raw.get("SUM", {})
    python = raw.get("Python", {})
    if python.get("nFiles", 0) != len(files):
        return {
            "available": False,
            "reason": f"cloc counted {python.get('nFiles', 0)} of {len(files)} selected Python files",
            "raw": raw,
            "summary": {},
        }

    return {
        "available": True,
        "tool": "cloc",
        "selected_python_files": files,
        "raw": raw,
        "summary": {
            "python_files": python.get("nFiles", 0),
            "python_blank_lines": python.get("blank", 0),
            "python_comment_lines": python.get("comment", 0),
            "python_code_lines_sloc": python.get("code", 0),
            "all_files": total.get("nFiles", 0),
            "all_blank_lines": total.get("blank", 0),
            "all_comment_lines": total.get("comment", 0),
            "all_code_lines": total.get("code", 0),
        },
    }

def run_radon_raw(src: Path, exclude_dirs: list[str], exclude_files=()) -> Dict[str, Any]:
    if shutil.which("radon") is None:
        return {"available": False, "reason": "radon not found in PATH", "raw": None, "summary": {}}

    files = collect_python_files(src, exclude_dirs, exclude_files)
    result = run_command(["radon", "raw", "-j", *files])

    if result["returncode"] != 0:
        return {
            "available": False,
            "reason": "radon raw failed",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    try:
        raw = json.loads(result["stdout"])
    except json.JSONDecodeError as e:
        return {
            "available": False,
            "reason": f"could not parse radon raw JSON: {e}",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    totals = {
        "files": len(raw),
        "loc": 0,
        "lloc": 0,
        "sloc": 0,
        "comments": 0,
        "multi": 0,
        "blank": 0,
        "single_comments": 0,
    }

    for item in raw.values():
        for key in totals:
            if key != "files":
                totals[key] += int(item.get(key, 0))

    return {
        "available": True,
        "tool": "radon raw",
        "raw": raw,
        "summary": totals,
    }

def run_radon_hal(src: Path, exclude_dirs: list[str], exclude_files=()) -> Dict[str, Any]:
    if shutil.which("radon") is None:
        return {"available": False, "reason": "radon not found in PATH", "raw": None, "summary": {}}

    files = collect_python_files(src, exclude_dirs, exclude_files)
    result = run_command(["radon", "hal", "-j", *files])

    if result["returncode"] != 0:
        return {
            "available": False,
            "reason": "radon hal failed",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    try:
        raw = json.loads(result["stdout"])
    except json.JSONDecodeError as e:
        return {
            "available": False,
            "reason": f"could not parse radon hal JSON: {e}",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    return {
        "available": True,
        "tool": "radon hal",
        "raw": raw,
        "summary": {
            "files": len(raw),
            "note": "Halstead metrics are stored per file in raw output.",
        },
    }

def run_radon_cc(src: Path, exclude_dirs: list[str], exclude_files=()) -> Dict[str, Any]:
    if shutil.which("radon") is None:
        return {"available": False, "reason": "radon not found in PATH", "raw": None, "summary": {}}

    files = collect_python_files(src, exclude_dirs, exclude_files)
    result = run_command(
    ["radon", "cc", "-j", "-s", *files]
)
    if result["returncode"] != 0:
        return {
            "available": False,
            "reason": "radon cc failed",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    try:
        raw = json.loads(result["stdout"])
    except json.JSONDecodeError as e:
        return {
            "available": False,
            "reason": f"could not parse radon cc JSON: {e}",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    blocks: List[Dict[str, Any]] = []
    for file_path, entries in raw.items():
        for entry in entries:
            item = dict(entry)
            item["file"] = file_path
            blocks.append(item)

    functions = [b for b in blocks if b.get("type") in {"function", "method"}]
    classes = [b for b in blocks if b.get("type") == "class"]

    total_cc = sum(int(b.get("complexity", 0)) for b in functions)
    max_cc = max((int(b.get("complexity", 0)) for b in functions), default=0)
    avg_cc = round(total_cc / len(functions), 3) if functions else 0.0

    top = sorted(functions, key=lambda b: int(b.get("complexity", 0)), reverse=True)[:25]

    rank_counts: Dict[str, int] = {}
    for b in functions:
        rank = str(b.get("rank", "NA"))
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    return {
        "available": True,
        "tool": "radon cc",
        "raw": raw,
        "summary": {
            "functions_and_methods": len(functions),
            "classes": len(classes),
            "total_cyclomatic_complexity": total_cc,
            "average_cyclomatic_complexity_per_function": avg_cc,
            "maximum_cyclomatic_complexity": max_cc,
            "rank_counts": rank_counts,
            "top_complex_functions": top,
        },
    }


def run_radon_mi(src: Path, exclude_dirs: list[str], exclude_files=()) -> Dict[str, Any]:
    if shutil.which("radon") is None:
        return {"available": False, "reason": "radon not found in PATH", "raw": None, "summary": {}}

    files = collect_python_files(src, exclude_dirs, exclude_files)
    result = run_command(
    ["radon", "mi", "-j", "-s", *files]
)
    if result["returncode"] != 0:
        return {
            "available": False,
            "reason": "radon mi failed",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    try:
        raw = json.loads(result["stdout"])
    except json.JSONDecodeError as e:
        return {
            "available": False,
            "reason": f"could not parse radon mi JSON: {e}",
            "raw_command_result": result,
            "raw": None,
            "summary": {},
        }

    values = []
    for file_path, item in raw.items():
        if isinstance(item, dict) and "mi" in item:
            values.append({"file": file_path, "maintainability_index": item.get("mi"), "rank": item.get("rank")})

    numeric = [float(v["maintainability_index"]) for v in values if isinstance(v.get("maintainability_index"), (int, float))]

    rank_counts: Dict[str, int] = {}
    for v in values:
        rank = str(v.get("rank", "NA"))
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    return {
        "available": True,
        "tool": "radon mi",
        "raw": raw,
        "summary": {
            "files": len(values),
            "average_maintainability_index": round(sum(numeric) / len(numeric), 3) if numeric else None,
            "minimum_maintainability_index": round(min(numeric), 3) if numeric else None,
            "maximum_maintainability_index": round(max(numeric), 3) if numeric else None,
            "rank_counts": rank_counts,
            "files_by_maintainability": sorted(values, key=lambda x: float(x.get("maintainability_index") or 0)),
        },
    }


def count_python_ast_objects(
    src: Path,
    exclude_dirs: list[str],
    exclude_files=()
) -> Dict[str, Any]:
    files: List[Dict[str, Any]] = []
    total_logical_loc = 0
    total_functions = 0
    total_classes = 0

    for selected_path in collect_python_files(src, exclude_dirs, exclude_files):
        path = Path(selected_path)

        rel = str(path.relative_to(src))
        text = read_text(path)

        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as e:
            files.append({"path": rel, "parse_error": f"{e.__class__.__name__}: {e}", "logical_loc": 0, "functions": 0, "classes": 0})
            continue

        logical_loc = sum(1 for node in ast.walk(tree) if isinstance(node, ast.stmt))
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))

        total_logical_loc += logical_loc
        total_functions += functions
        total_classes += classes

        files.append({"path": rel, "parse_error": None, "logical_loc": logical_loc, "functions": functions, "classes": classes})

    return {
        "summary": {
            "python_files": len(files),
            "logical_loc_ast_statements": total_logical_loc,
            "functions_and_methods_ast": total_functions,
            "classes_ast": total_classes,
        },
        "files": files,
    }


def is_sentence_like_object(obj: Any) -> bool:
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("text"), str)
        and isinstance(obj.get("struct"), dict)
        and any(k in obj["struct"] for k in ("tokens", "chunks", "conllu"))
    )


def walk_json(obj: Any) -> Iterable[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk_json(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk_json(value)


def count_leaf_values(obj: Any) -> int:
    if isinstance(obj, dict):
        if not obj:
            return 0
        return sum(count_leaf_values(v) for v in obj.values())
    if isinstance(obj, list):
        return len(obj)
    return 1


def analyze_json_resource(path: Path) -> Dict[str, Any]:
    text = read_text(path)
    physical_lines = len(text.splitlines())
    blank_lines = sum(1 for line in text.splitlines() if not line.strip())

    result: Dict[str, Any] = {
        "path": str(path),
        "physical_lines": physical_lines,
        "blank_lines": blank_lines,
        "parse_error": None,
        "top_level_type": None,
        "top_level_items": None,
        "sentence_like_objects": 0,
        "lexicon_entries_heuristic": 0,
        "override_rules_heuristic": 0,
    }

    try:
        obj = json.loads(text)
    except Exception as e:
        result["parse_error"] = f"{e.__class__.__name__}: {e}"
        return result

    result["top_level_type"] = type(obj).__name__
    result["top_level_items"] = len(obj) if isinstance(obj, (list, dict)) else 1
    result["sentence_like_objects"] = sum(1 for item in walk_json(obj) if is_sentence_like_object(item))

    lower_name = path.name.lower()
    if isinstance(obj, list) and ("lexicon" in lower_name or "lex" in lower_name):
        result["lexicon_entries_heuristic"] = len(obj)

    if "override" in lower_name:
        result["override_rules_heuristic"] = count_leaf_values(obj)

    return result


def summarize_json_resources(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "files": len(resources),
        "physical_lines": sum(int(r.get("physical_lines") or 0) for r in resources),
        "blank_lines": sum(int(r.get("blank_lines") or 0) for r in resources),
        "sentence_like_objects": sum(int(r.get("sentence_like_objects") or 0) for r in resources),
        "lexicon_entries_heuristic": sum(int(r.get("lexicon_entries_heuristic") or 0) for r in resources),
        "override_rules_heuristic": sum(int(r.get("override_rules_heuristic") or 0) for r in resources),
        "parse_errors": [r for r in resources if r.get("parse_error")],
    }


def format_int(value: Any) -> str:
    if value is None:
        return "NA"
    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return str(value)


def print_human_report(report: Dict[str, Any]) -> None:
    print("# Kadiwéu converter pipeline metrics")
    print()
    print(f"Generated at: {report['metadata']['generated_at']}")
    print(f"Source directory: {report['metadata']['src']}")
    print(f"JSON report: {report['metadata']['json_out']}")
    print()

    raw = report["software_metrics"]["radon_raw"]
    ast_metrics = report["software_metrics"]["python_ast"]
    radon_cc = report["software_metrics"]["radon_cc"]
    radon_mi = report["software_metrics"]["radon_mi"]
    radon_hal = report["software_metrics"]["radon_hal"]
    cloc = report["software_metrics"]["cloc_crosscheck"]
    json_summary = report["linguistic_resources"]["summary"]

    print("## Software size: Radon raw metrics")
    if raw.get("available"):
        s = raw["summary"]
        print(f"Python files: {format_int(s.get('files'))}")
        print(f"Physical LOC: {format_int(s.get('loc'))}")
        print(f"SLOC: {format_int(s.get('sloc'))}")
        print(f"Logical LOC: {format_int(s.get('lloc'))}")
        print(f"Comment lines: {format_int(s.get('comments'))}")
        print(f"Blank lines: {format_int(s.get('blank'))}")
    else:
        print(f"radon raw unavailable: {raw.get('reason')}")
        print()
    
    print()

    print("## AST-based logical structure")
    s = ast_metrics["summary"]
    print(f"AST statement count: {format_int(s.get('logical_loc_ast_statements'))}")
    print(f"AST functions/methods: {format_int(s.get('functions_and_methods_ast'))}")
    print(f"AST classes: {format_int(s.get('classes_ast'))}")
    print()

    print("## Software structure and complexity")
    if radon_cc.get("available"):
        s = radon_cc["summary"]
        print(f"Functions/methods: {format_int(s.get('functions_and_methods'))}")
        print(f"Classes: {format_int(s.get('classes'))}")
        print(f"Total cyclomatic complexity: {format_int(s.get('total_cyclomatic_complexity'))}")
        print(f"Average cyclomatic complexity per function: {s.get('average_cyclomatic_complexity_per_function')}")
        print(f"Maximum cyclomatic complexity: {format_int(s.get('maximum_cyclomatic_complexity'))}")
        print(f"Cyclomatic-complexity ranks: {s.get('rank_counts')}")
    else:
        print(f"radon cc unavailable: {radon_cc.get('reason')}")
        s = ast_metrics["summary"]
        print(f"Functions/methods, AST fallback: {format_int(s.get('functions_and_methods_ast'))}")
        print(f"Classes, AST fallback: {format_int(s.get('classes_ast'))}")

    if radon_mi.get("available"):
        s = radon_mi["summary"]
        print(f"Average maintainability index: {s.get('average_maintainability_index')}")
        print(f"Minimum maintainability index: {s.get('minimum_maintainability_index')}")
        print(f"Maintainability ranks: {s.get('rank_counts')}")
    else:
        print(f"radon mi unavailable: {radon_mi.get('reason')}")
    print()

    if radon_cc.get("available") and radon_cc["summary"].get("top_complex_functions"):
        print("## Most complex functions")
        for item in radon_cc["summary"]["top_complex_functions"][:10]:
            print(f"- CC={item.get('complexity'):>3} {item.get('file')}:{item.get('lineno')} {item.get('name')} [{item.get('rank')}]")
        print()
    
    print("## Halstead metrics")
    if radon_hal.get("available"):
        print(f"Files with Halstead metrics: {format_int(radon_hal['summary'].get('files'))}")
        print("Full Halstead metrics are stored in the JSON report.")
    else:
        print(f"radon hal unavailable: {radon_hal.get('reason')}")
    print()

    print("## Explicitly included JSON linguistic resources")
    print(f"JSON files: {format_int(json_summary.get('files'))}")
    print(f"JSON physical lines: {format_int(json_summary.get('physical_lines'))}")
    print(f"Sentence-like Tycho Brahe objects: {format_int(json_summary.get('sentence_like_objects'))}")
    print(f"Lexicon entries, heuristic: {format_int(json_summary.get('lexicon_entries_heuristic'))}")
    print(f"Override rules, heuristic: {format_int(json_summary.get('override_rules_heuristic'))}")

    print()
    print("## Cross-check: cloc")
    if cloc.get("available"):
        s = cloc["summary"]
        print(f"Python files: {format_int(s.get('python_files'))}")
        print(f"Python SLOC: {format_int(s.get('python_code_lines_sloc'))}")
        print(f"Python comment lines: {format_int(s.get('python_comment_lines'))}")
        print(f"Python blank lines: {format_int(s.get('python_blank_lines'))}")
    else:
        print(f"cloc unavailable: {cloc.get('reason')}")

    if json_summary.get("parse_errors"):
        print()
        print("JSON files with parse errors:")
        for item in json_summary["parse_errors"]:
            print(f"- {item['path']}: {item['parse_error']}")


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    src = Path(args.src).expanduser().resolve()
    json_out = Path(args.json_out).expanduser().resolve()
    json_paths = [Path(p).expanduser().resolve() for p in args.json_resource]

    json_resource_metrics = [analyze_json_resource(path) for path in json_paths]

    return {
        "metadata": {
            "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "script": Path(__file__).name,
            "python_version": sys.version,
            "src": str(src),
            "json_resources": [str(p) for p in json_paths],
            "excluded_files": args.exclude_file,
            "json_out": str(json_out),
            "external_tools": {"cloc": shutil.which("cloc"), "radon": shutil.which("radon")},
            "notes": [
                "CoNLL-U statistics are intentionally not computed here; use the standard UD Perl scripts.",
                "Only JSON resources explicitly supplied with --json-resource are included.",
                "The tests directory is not analyzed unless it is inside --src.",
            ],
        },
        "software_metrics": {
            "radon_raw": run_radon_raw(src, args.exclude_dir, args.exclude_file),
            "radon_cc": run_radon_cc(src, args.exclude_dir, args.exclude_file),
            "radon_mi": run_radon_mi(src, args.exclude_dir, args.exclude_file),
            "radon_hal": run_radon_hal(src, args.exclude_dir, args.exclude_file),
            "python_ast": count_python_ast_objects(src, args.exclude_dir, args.exclude_file),
            "cloc_crosscheck": run_cloc(src, args.exclude_dir, args.exclude_file),
        },
        "linguistic_resources": {"summary": summarize_json_resources(json_resource_metrics), "files": json_resource_metrics},
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute publication-oriented metrics for the Kadiwéu converter pipeline."
    )
    parser.add_argument("--src", default="src", help="Directory containing Python source scripts. Default: src")
    parser.add_argument(
        "--json-resource",
        action="append",
        default=[],
        help="JSON linguistic resource to include. Repeat once per file. No JSON file is included implicitly.",
    )
    parser.add_argument("--json-out", default="pipeline_publication_metrics.json", help="Output JSON report path.")

    parser.add_argument(
    "--exclude-dir",
    action="append",
    default=["attic", "__pycache__"],
    help="Directory name to exclude from Python source analysis. Can be repeated.",
    )

    parser.add_argument(
        "--exclude-file", action="append", default=[],
        help="Python filename or path relative to --src to exclude; repeatable.",
    )
    return parser.parse_args(argv)

    


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    report = build_report(args)

    json_out = Path(args.json_out).expanduser().resolve()
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print_human_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
