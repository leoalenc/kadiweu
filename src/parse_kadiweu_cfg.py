#!/usr/bin/env python3
"""Parse a POS-tagged Kadiwéu sentence with an induced NLTK CFG.

The --sentence value may be a whitespace-separated sequence of word/POS
tokens (for example, ``Etogo/N``), optionally ending in untagged punctuation,
or a whitespace-separated sequence of POS tags. Only POS tags are sent to the
CFG; tagged words are returned under POS preterminals. Trees are printed in
NLTK bracketed (LISP) format by default, or as ASCII or Unicode tree drawings
with ``--format``.
In batch mode, ``--output`` writes all generated parses as CorpusSearch-style
PSD records with sentence metadata and a parse number.

Requires NLTK (``python -m pip install nltk``).
"""

import argparse
import csv
import re
import string
import sys
from itertools import islice
from pathlib import Path

from nltk import CFG
from nltk.grammar import Nonterminal
from nltk.parse import ChartParser
from nltk.tree import Tree
from induce_kadiweu_cfg import iter_records, normalized_label
from kadiweu_constituency import (
    ConstituentNode,
    ConstituencyTree,
    TokenNode,
    render_tree_text,
)


def sentence_to_tags(sentence, punctuation_tag=None):
    """Return CFG tags and optional word forms from the input sentence."""
    tags = []
    words = []
    raw_tokens = sentence.split()
    if not raw_tokens:
        raise ValueError("the input sentence contains no tokens")

    tagged_tokens = ["/" in token for token in raw_tokens]
    if not any(tagged_tokens):
        # Bare input is interpreted as a POS-tag sequence.
        return raw_tokens, None

    for token in raw_tokens:
        if "/" in token:
            word, tag = token.rsplit("/", 1)
            if not word:
                raise ValueError(f"token has an empty word form: {token!r}")
            if not tag:
                raise ValueError(f"token has an empty POS tag: {token!r}")
            tags.append(tag)
            words.append(word)
        else:
            if all(char in string.punctuation for char in token):
                if not punctuation_tag:
                    raise ValueError(
                        "cannot infer the tag for untagged punctuation; "
                        "use --punct-tag to specify it"
                    )
                tags.append(punctuation_tag)
                words.append(token)
            else:
                raise ValueError(
                    "untagged token {!r} is not punctuation; use word/POS "
                    "tokens throughout".format(token)
                )
    return tags, words


def insert_preterminals(tree, tags, words):
    """Turn each POS terminal into a preterminal over its aligned word form."""
    if len(tree.leaves()) != len(words):
        raise ValueError(
            "parse leaf count ({}) does not match input word count ({})".format(
                len(tree.leaves()), len(words)
            )
        )
    if len(tags) != len(words):
        raise ValueError("POS-tag count does not match input word count")
    positions = [tree.leaf_treeposition(index) for index in range(len(words))]
    for position, tag, word in zip(positions, tags, words):
        tree[position] = Tree(tag, [word])


def tree_word_pos_sequence(tree):
    """Return overt (word, POS) pairs from a flat or full PSD tree."""
    return [
        (str(node[0]), str(node.label()))
        for node in tree.subtrees()
        if len(node) == 1
        and isinstance(node[0], str)
        and node.label() != "-NONE-"
    ]


def gold_cfg_signature(tree):
    """Normalize a gold tree like CFG induction: remove traces and words."""
    def visit(node):
        label = node.label()
        if label == "-NONE-":
            return None
        if len(node) == 1 and isinstance(node[0], str):
            return ("T", normalized_label(label))
        rhs = tuple(
            symbol
            for child in node
            if (symbol := visit(child)) is not None
        )
        return ("N", normalized_label(label), rhs)

    return visit(tree)


def parse_cfg_signature(tree):
    """Normalize a CFG parse, abstracting away its ROOT wrapper."""
    if tree.label() == "ROOT" and len(tree) == 1:
        tree = tree[0]

    def visit(node):
        if not isinstance(node, Tree):
            return ("T", normalized_label(node))
        rhs = tuple(visit(child) for child in node)
        return ("N", normalized_label(node.label()), rhs)

    return visit(tree)


def format_psd_tree(tree, indent=2):
    """Format an NLTK tree as an indented parenthesized PSD tree."""
    prefix = " " * indent
    if len(tree) == 1 and isinstance(tree[0], str):
        return f"{prefix}({tree.label()} {tree[0]})"

    lines = [f"{prefix}({tree.label()}"]
    for child in tree:
        if isinstance(child, Tree):
            lines.append(format_psd_tree(child, indent + 2))
        else:
            lines.append(f"{' ' * (indent + 2)}{child}")
    lines.append(f"{prefix})")
    return "\n".join(lines)


def format_psd_record(metadata, corpus_id, parse_number, tree):
    """Return one numbered parse in the project's CorpusSearch PSD style."""
    metadata_lines = []
    for key in ("sentence", "uid", "status", "text", "text_por"):
        value = metadata.get(key)
        if value:
            value = " ".join(str(value).split()).replace("*/", "* /")
            metadata_lines.append(f"{key} = {value}")
    metadata_lines.append(f"parse_number = {parse_number}")

    lines = ["/*", *metadata_lines, "*/", "(", format_psd_tree(tree)]
    if corpus_id:
        lines.append(f"  (ID {corpus_id})")
    lines.append(")")
    return "\n".join(lines)


def to_constituency_tree(tree):
    """Adapt an NLTK Tree for the project's shared tree text renderer."""
    tokens = []
    leaf_count = 0

    def convert(node, level=0, parent=None):
        nonlocal leaf_count

        if not isinstance(node, Tree):
            # A bare POS terminal (when input consists only of tags) is shown
            # as a leaf label. Tagged word input instead uses TokenNode below.
            leaf_count += 1
            return ConstituentNode(
                label=str(node),
                start=leaf_count,
                end=leaf_count,
                level=level,
                parent=parent,
            )

        if len(node) == 1 and not isinstance(node[0], Tree):
            leaf_count += 1
            token = TokenNode(
                position=leaf_count,
                form=str(node[0]),
                tag=str(node.label()),
                level=level,
                parent=parent,
            )
            tokens.append(token)
            return token

        start = leaf_count + 1
        constituent = ConstituentNode(
            label=str(node.label()),
            start=start,
            end=start - 1,
            level=level,
            parent=parent,
        )
        for child in node:
            constituent.children.append(convert(child, level + 1, constituent))
        constituent.end = leaf_count
        return constituent

    root = convert(tree)
    if not isinstance(root, ConstituentNode):
        raise ValueError("the parse tree has no constituent root")
    return ConstituencyTree(roots=[root], tokens=tokens)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Parse a Kadiwéu sentence using an induced CFG whose terminals "
            "are POS tags."
        )
    )
    parser.add_argument(
        "-g",
        "--grammar",
        required=True,
        type=Path,
        help="path to the induced NLTK CFG file",
    )
    parser.add_argument(
        "-s",
        "--sentence",
        help=(
            "quoted word/POS sentence (final punctuation may be untagged) "
            "or a POS-tag sequence"
        ),
    )
    parser.add_argument(
        "--flat-trees",
        type=Path,
        metavar="FILE",
        help="batch-parse a PSD file containing flat POS-tagged trees",
    )
    parser.add_argument(
        "--status",
        default="DONE",
        help="status selected with --flat-trees (default: DONE)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        metavar="TSV",
        help="write per-sentence batch results to this TSV file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="PSD",
        help="write generated batch parses to this PSD file",
    )
    parser.add_argument(
        "--gold-trees",
        type=Path,
        metavar="FILE",
        help="full gold PSD file for exact/trace-partial parse comparison",
    )
    parser.add_argument(
        "--start",
        default="ROOT",
        help="grammar start symbol (default: ROOT)",
    )
    parser.add_argument(
        "--punct-tag",
        help="POS tag to assign to untagged punctuation (inferred when unique)",
    )
    parser.add_argument(
        "--max-parses",
        type=int,
        default=5,
        help="maximum number of parses to print (default: 5)",
    )
    parser.add_argument(
        "-n",
        "--number",
        action="store_true",
        help="print only the total number of parses (ignores --max-parses)",
    )
    parser.add_argument(
        "--format",
        choices=("lisp", "ascii", "unicode"),
        default="lisp",
        help=("tree output format: NLTK LISP, ASCII, or Unicode "
              "(default: lisp)"),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print diagnostics and parse headings",
    )
    parser.add_argument(
        "--trees-only",
        action="store_true",
        help="suppress diagnostics (legacy option; also the default)",
    )
    return parser


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    if bool(args.sentence) == bool(args.flat_trees):
        print("error: specify exactly one of --sentence or --flat-trees", file=sys.stderr)
        return 2
    if (args.report or args.gold_trees or args.output) and not args.flat_trees:
        print(
            "error: --report, --gold-trees, and --output require --flat-trees",
            file=sys.stderr,
        )
        return 2
    if args.flat_trees and not args.flat_trees.is_file():
        print(f"error: flat-tree file not found: {args.flat_trees}", file=sys.stderr)
        return 2
    if args.gold_trees and not args.gold_trees.is_file():
        print(f"error: gold-tree file not found: {args.gold_trees}", file=sys.stderr)
        return 2
    if not args.number and args.max_parses < 1:
        print("error: --max-parses must be at least 1", file=sys.stderr)
        return 2
    if not args.grammar.is_file():
        print(f"error: grammar file not found: {args.grammar}", file=sys.stderr)
        return 2

    try:
        parsed_grammar = CFG.fromstring(args.grammar.read_text(encoding="utf-8"))
        start_symbol = Nonterminal(args.start)
        productions = parsed_grammar.productions()
        if not any(production.lhs() == start_symbol for production in productions):
            raise ValueError(
                "the grammar has no productions for start symbol {!r}; "
                "regenerate it with the updated induce_kadiweu_cfg.py or "
                "pass the correct symbol with --start".format(args.start)
            )
        # CFG.fromstring normally adopts the LHS of the first production as
        # the start symbol. Set it explicitly so older grammars whose rules
        # are alphabetically ordered still parse from ROOT.
        grammar = CFG(start_symbol, productions)
        terminals = {
            symbol
            for production in productions
            for symbol in production.rhs()
            if isinstance(symbol, str)
        }
        punctuation_tag = args.punct_tag
        if punctuation_tag and punctuation_tag not in terminals:
            raise ValueError(
                "punctuation tag {!r} is not a terminal in the grammar".format(
                    punctuation_tag
                )
            )
        if punctuation_tag is None:
            candidates = [tag for tag in ("PUNC", "PUNCT") if tag in terminals]
            if len(candidates) == 1:
                punctuation_tag = candidates[0]
        if args.flat_trees:
            flat_records = list(iter_records(args.flat_trees))
            selected = [
                (metadata, tree)
                for metadata, tree, _ in flat_records
                if metadata.get("status", "").upper() == args.status.upper()
            ]
            if not selected:
                raise ValueError(
                    f"no records with status {args.status!r} in {args.flat_trees}"
                )
        else:
            tags, words = sentence_to_tags(args.sentence, punctuation_tag)
            grammar.check_coverage(tags)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser = ChartParser(grammar)
    verbose = args.verbose and not args.trees_only

    if args.flat_trees:
        gold_by_uid = {}
        gold_by_id = {}
        try:
            if args.gold_trees:
                for metadata, tree, _ in iter_records(args.gold_trees):
                    if metadata.get("status", "").upper() != args.status.upper():
                        continue
                    if metadata.get("uid"):
                        gold_by_uid[metadata["uid"]] = (metadata, tree)
                    if metadata.get("corpus_id"):
                        gold_by_id[metadata["corpus_id"]] = (metadata, tree)

            rows = []
            psd_records = []
            parsed_sentences = 0
            total_parses = 0
            aligned_gold = 0
            exact_sentences = 0
            partial_sentences = 0
            for metadata, flat_tree in selected:
                sequence = tree_word_pos_sequence(flat_tree)
                words = [word for word, _ in sequence]
                tags = [tag for _, tag in sequence]
                parse_count = 0
                exact_numbers = []
                partial_numbers = []
                note = ""
                try:
                    grammar.check_coverage(tags)
                    parses = parser.parse(tags)
                    gold_record = (
                        gold_by_uid.get(metadata.get("uid"))
                        or gold_by_id.get(metadata.get("corpus_id"))
                    ) if args.gold_trees else None
                    gold_signature = None
                    gold_has_traces = False
                    if gold_record:
                        gold_metadata, gold_tree = gold_record
                        gold_sequence = tree_word_pos_sequence(gold_tree)
                        if sequence == gold_sequence:
                            aligned_gold += 1
                            gold_signature = gold_cfg_signature(gold_tree)
                            gold_has_traces = any(
                                node.label() == "-NONE-"
                                for node in gold_tree.subtrees()
                            )
                        else:
                            note = "gold_yield_mismatch"

                    for parse_number, parse_tree in enumerate(parses, start=1):
                        parse_count = parse_number
                        if args.output:
                            output_tree = parse_tree.copy(deep=True)
                            insert_preterminals(output_tree, tags, words)
                            psd_records.append(
                                format_psd_record(
                                    metadata,
                                    metadata.get("corpus_id", ""),
                                    parse_number,
                                    output_tree,
                                )
                            )
                        if gold_signature is not None and parse_cfg_signature(parse_tree) == gold_signature:
                            if gold_has_traces:
                                partial_numbers.append(parse_number)
                            else:
                                exact_numbers.append(parse_number)
                    parsed_sentences += int(parse_count > 0)
                except ValueError as exc:
                    note = str(exc)
                    gold_record = None
                    gold_signature = None
                    parse_count = 0
                total_parses += parse_count

                row = {
                    "sentence": metadata.get("sentence", ""),
                    "corpussearch_id": metadata.get("corpus_id", ""),
                    "uid": metadata.get("uid", ""),
                    "tokens": len(sequence),
                    "parse_count": parse_count,
                    "parse_found": "yes" if parse_count else "no",
                    "exact_match_parse_numbers": ",".join(map(str, exact_numbers)),
                    "partial_trace_match_parse_numbers": ",".join(map(str, partial_numbers)),
                    "gold_match": "",
                    "note": note,
                }
                if args.gold_trees:
                    if not gold_record:
                        row["gold_match"] = "missing_gold"
                    elif gold_signature is None:
                        row["gold_match"] = "yield_mismatch"
                    elif exact_numbers:
                        row["gold_match"] = "exact"
                        exact_sentences += 1
                    elif partial_numbers:
                        row["gold_match"] = "partial_trace"
                        partial_sentences += 1
                    else:
                        row["gold_match"] = "no_match"
                rows.append(row)

            if args.report:
                fieldnames = [
                    "sentence", "corpussearch_id", "uid", "tokens", "parse_count",
                    "parse_found", "exact_match_parse_numbers",
                    "partial_trace_match_parse_numbers", "gold_match", "note",
                ]
                with args.report.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(
                        stream, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
                    )
                    writer.writeheader()
                    writer.writerows(rows)
            if args.output:
                args.output.write_text(
                    "\n\n".join(psd_records) + ("\n" if psd_records else ""),
                    encoding="utf-8",
                )
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        print(
            f"Selected {len(selected)} {args.status.upper()} records; "
            f"parsed {parsed_sentences}; failed {len(selected) - parsed_sentences}; "
            f"total parses {total_parses}."
        )
        if args.gold_trees:
            print(
                f"Gold yields aligned: {aligned_gold}; exact matches: "
                f"{exact_sentences}; partial trace matches: {partial_sentences}."
            )
        if args.report:
            print(f"Per-sentence report: {args.report}")
        if args.output:
            print(f"Parse trees: {args.output} ({len(psd_records)} records)")
        return 0

    if args.number:
        # Count every parse without retaining or modifying the parse trees.
        if verbose:
            print("POS sequence:", " ".join(tags))
            print("Grammar start symbol:", grammar.start())
        count = sum(1 for _ in parser.parse(tags))
        print(f"Number of parse trees: {count}" if verbose else count)
        return 0

    if verbose:
        print("POS sequence:", " ".join(tags))
        print("Grammar start symbol:", grammar.start())

    # NLTK parse trees can share mutable subtrees. Copy each result as it is
    # yielded so inserting word forms into one parse cannot affect another.
    parses = [
        tree.copy(deep=True)
        for tree in islice(parser.parse(tags), args.max_parses)
    ]

    if not parses:
        if verbose:
            print("No parse found.")
        return 1

    if verbose:
        print("Showing up to {} parse(s):".format(args.max_parses))
    for index, tree in enumerate(parses, 1):
        if words is not None:
            insert_preterminals(tree, tags, words)
        if index > 1:
            print()
        if verbose:
            print("Parse {}:".format(index))
        if args.format == "lisp":
            print(tree)
        else:
            adapted_tree = to_constituency_tree(tree)
            print(render_tree_text(adapted_tree, style=args.format))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
