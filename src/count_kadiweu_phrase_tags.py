#!/usr/bin/env python3
"""Count phrase-level labels and functional tags in DONE CorpusSearch PSDs.

The input PSD files should contain the DONE sentences (as in the supplied
*.done.corpussearch.psd files). Phrase nodes are identified structurally: a
node is phrase-level when it has at least one child node. Numeric suffixes
such as NP-1 are treated as coindexation, not as functional tags.

Usage:
  python3 count_kadiweu_phrase_tags.py FILE.psd [FILE.psd ...] [-o REPORT_DIR]

Writes phrase_label_counts.tsv and category_functional_tag_proportions.tsv.
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
from pathlib import Path
from typing import Iterator, List, Union

Tree = List[Union[str, "Tree"]]
TOKEN_RE = re.compile(r"\(|\)|[^\s()]+")
NUMERIC_SUFFIX = re.compile(r"-\d+$")


def parse_trees(text: str, source: str) -> Iterator[Tree]:
    """Yield top-level S-expressions, rejecting unbalanced input."""
    # Parentheses may occur in the free-text headers, not just in the trees.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    tokens = TOKEN_RE.findall(text)
    stack: List[Tree] = []
    roots: List[Tree] = []
    for token in tokens:
        if token == "(":
            node: Tree = []
            if stack:
                stack[-1].append(node)
            else:
                roots.append(node)
            stack.append(node)
        elif token == ")":
            if not stack:
                raise ValueError(f"{source}: unexpected closing parenthesis")
            stack.pop()
        elif stack:
            stack[-1].append(token)
        # Ignore any non-parenthesized text outside trees.
    if stack:
        raise ValueError(f"{source}: unclosed parenthesis")
    yield from roots


def phrase_labels(node: Tree) -> Iterator[str]:
    """Yield labels on nodes that dominate at least one constituent node."""
    if not node:
        return
    if not isinstance(node[0], str):
        for item in node:
            if isinstance(item, list):
                yield from phrase_labels(item)
        return
    label = node[0]
    children = [item for item in node[1:] if isinstance(item, list)]
    if children:
        yield label
    for child in children:
        yield from phrase_labels(child)


def split_label(label: str) -> tuple[str, str]:
    """Return category and functional tag; indices and CP-me are not tags."""
    # In CP-me, "-me" identifies the complementizer heading the CP; it is
    # part of the phrase label, not a functional tag. The exact label is
    # retained in phrase_label_counts.tsv, while this mapping pools it with CP
    # for the functional-tag proportions.
    if label == "CP-me":
        return "CP", ""
    match = NUMERIC_SUFFIX.search(label)
    if match:
        return label[:match.start()], ""
    if "-" in label:
        category, tag = label.split("-", 1)
        return category, tag
    return label, ""


def write_tsv(path: Path, header: list[str], rows: list[tuple]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("psd", nargs="+", type=Path, help="DONE CorpusSearch PSD file(s)")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    labels: collections.Counter[str] = collections.Counter()
    sources: collections.Counter[str] = collections.Counter()
    for path in args.psd:
        text = path.read_text(encoding="utf-8")
        n_sentences = 0
        for tree in parse_trees(text, str(path)):
            n_sentences += 1
            labels.update(phrase_labels(tree))
        sources[path.name] = n_sentences

    category_totals: collections.Counter[str] = collections.Counter()
    category_tagged: collections.Counter[str] = collections.Counter()
    category_tag_counts: collections.Counter[tuple[str, str]] = collections.Counter()
    tag_totals: collections.Counter[str] = collections.Counter()
    for label, count in labels.items():
        category, tag = split_label(label)
        category_totals[category] += count
        if tag:
            category_tagged[category] += count
            category_tag_counts[(category, tag)] += count
            tag_totals[tag] += count

    args.output_dir.mkdir(parents=True, exist_ok=True)
    # One file contains exact-label counts plus totals pooled by functional tag.
    rows = []
    for label, count in sorted(labels.items(), key=lambda pair: (split_label(pair[0]), pair[0])):
        category, tag = split_label(label)
        rows.append(("phrase_label", label, category, tag or "_", count))
    for tag, count in sorted(tag_totals.items()):
        rows.append(("functional_tag_total", "_", "_", tag, count))
    write_tsv(
        args.output_dir / "phrase_label_counts.tsv",
        ["record_type", "phrase_label", "category", "functional_tag", "count"],
        rows,
    )

    proportion_rows = []
    for category in sorted(category_totals):
        total = category_totals[category]
        tagged = category_tagged[category]
        proportion_rows.append(
            (category, total, tagged, total - tagged, f"{100 * tagged / total:.2f}")
        )
    write_tsv(
        args.output_dir / "category_functional_tag_proportions.tsv",
        ["category", "phrase_count", "functional_tagged_count", "untagged_count", "tagged_percent"],
        proportion_rows,
    )

    sentence_total = sum(sources.values())
    print(f"Read {sentence_total} sentences from {len(sources)} file(s).")
    for name, count in sources.items():
        print(f"  {name}: {count} sentences")
    print(f"Counted {sum(labels.values())} phrase nodes across {len(labels)} distinct labels.")
    print(f"Wrote {args.output_dir / 'phrase_label_counts.tsv'}")
    print(f"Wrote {args.output_dir / 'category_functional_tag_proportions.tsv'}")


if __name__ == "__main__":
    main()
