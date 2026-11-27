#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract reviewable *et*-verb candidates from Griffiths' dictionary.

Accepts a searchable PDF (converted with ``pdftotext -layout``) or an already
extracted UTF-8 text file. The source dictionary's two-column layout and OCR
make automatic headword classification unsafe, so this emits short contexts
and marks every result as a candidate for review; it does not assign UD tags.

Usage:
    python3 extract_griffiths_et_forms.py Griffiths-2002.pdf -o griffiths-et.json
    python3 extract_griffiths_et_forms.py Griffiths-2002.txt -o griffiths-et.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

WORD = re.compile(r"(?<![\w])et[\wǥƓɡ'’:-]*", re.IGNORECASE)
VERB_CUES = re.compile(
    r"\b(v|vi|vt|loc|estado|estar|est[aã]o?|fica(?:r)?|aqui|a[ií]|l[aá]|"
    r"em p[eé]|sentad[oa]|deitad[oa])\b",
    re.IGNORECASE,
)


def read_source(path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        return path.read_text(encoding="utf-8", errors="replace")
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("pdftotext is required for PDF input; provide a .txt export instead") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr or "pdftotext failed") from exc
    return result.stdout


def extract(text: str, source: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    page_starts = [0]
    page_starts.extend(m.end() for m in re.finditer("\f", text))
    for match in WORD.finditer(text):
        form = match.group(0).strip("-:;,.()[]{}")
        if len(form) < 4:
            continue
        left = max(0, match.start() - 180)
        right = min(len(text), match.end() + 220)
        context = re.sub(r"\s+", " ", text[left:right]).strip()
        page = max(i for i, start in enumerate(page_starts) if start <= match.start()) + 1
        key = (form.casefold(), context)
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "form": form,
            "source": "Griffiths 2002 dictionary",
            "source_file": source,
            "page_in_extracted_text": page,
            "context": context,
            "verb_cue_found": bool(VERB_CUES.search(context)),
            "review_status": "candidate",
        })
    return {
        "schema_version": 1,
        "source": "Griffiths 2002, Dicionário da língua Kadiwéu",
        "extraction_note": "Regex candidates with context; verify headword, sense, and page against the scan.",
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Searchable PDF or pdftotext UTF-8 output")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f"source file not found: {args.source}")
    try:
        data = extract(read_source(args.source), str(args.source))
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(data['records'])} *et*-initial candidates to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
