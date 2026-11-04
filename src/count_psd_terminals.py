#!/usr/bin/env python3
"""Count overt word and punctuation terminals in CorpusSearch PSD files.

Uses ``iter_psd_records`` from the accompanying ``kadiweu_constituency.py``
module, so the PSD syntax and trace conventions are interpreted consistently
with the project's exporter.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kadiweu_constituency import TreeConstructionError, iter_psd_records


def count_file(path: Path) -> tuple[int, int, int, int]:
    """Return sentence count, word count, punctuation count, skipped traces."""
    sentences = words = punctuation = traces = 0

    for record in iter_psd_records(path):
        sentences += 1
        for token in record.tree.tokens:
            # Trace terminals are represented in some trees, but are not overt
            # terminal words and therefore are excluded from these totals.
            if token.empty_category:
                traces += 1
            elif token.tag == "PUNC":
                punctuation += 1
            else:
                words += 1

    return sentences, words, punctuation, traces


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count overt word and PUNC terminals separately in one or more "
            "CorpusSearch PSD files. Empty-category traces are excluded."
        )
    )
    parser.add_argument("psd_files", nargs="+", type=Path, metavar="PSD")
    args = parser.parse_args()

    rows: list[tuple[str, int, int, int, int]] = []
    try:
        for path in args.psd_files:
            sentences, words, punctuation, traces = count_file(path)
            rows.append((path.name, sentences, words, punctuation, traces))
    except (OSError, UnicodeError, TreeConstructionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    widths = [max(len(header), *(len(str(row[i])) for row in rows))
              for i, header in enumerate(("File", "Sentences", "Words", "Punctuation", "Traces excluded"))]
    headers = ("File", "Sentences", "Words", "Punctuation", "Traces excluded")
    print("  ".join(header.ljust(widths[i]) for i, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)))

    totals = ("TOTAL", *(sum(row[i] for row in rows) for i in range(1, 5)))
    print("  ".join(str(value).ljust(widths[i]) for i, value in enumerate(totals)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
