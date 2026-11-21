#!/usr/bin/env python3
"""Parse a POS-tagged Kadiwéu sentence with an induced NLTK CFG.

The --sentence value may be a whitespace-separated sequence of word/POS
tokens (for example, ``Etogo/N``), optionally ending in untagged punctuation,
or a whitespace-separated sequence of POS tags. Only POS tags are sent to the
CFG; tagged words are returned under POS preterminals in NLTK bracketed-tree
format.

Requires NLTK (``python -m pip install nltk``).
"""

import argparse
import string
import sys
from itertools import islice
from pathlib import Path

from nltk import CFG
from nltk.grammar import Nonterminal
from nltk.parse import ChartParser
from nltk.tree import Tree


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
        required=True,
        help=(
            "quoted word/POS sentence (final punctuation may be untagged) "
            "or a POS-tag sequence"
        ),
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
        "--trees-only",
        action="store_true",
        help="print only bracketed parse trees, without diagnostic text",
    )
    return parser


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
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
        tags, words = sentence_to_tags(args.sentence, punctuation_tag)
        grammar.check_coverage(tags)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser = ChartParser(grammar)

    if args.number:
        # Count every parse without retaining or modifying the parse trees.
        print(sum(1 for _ in parser.parse(tags)))
        return 0

    if not args.trees_only:
        print("POS sequence:", " ".join(tags))
        print("Grammar start symbol:", grammar.start())

    # NLTK parse trees can share mutable subtrees. Copy each result as it is
    # yielded so inserting word forms into one parse cannot affect another.
    parses = [
        tree.copy(deep=True)
        for tree in islice(parser.parse(tags), args.max_parses)
    ]

    if not parses:
        print("No parse found.")
        return 1

    if not args.trees_only:
        print("Showing up to {} parse(s):".format(args.max_parses))
    for index, tree in enumerate(parses, 1):
        if words is not None:
            insert_preterminals(tree, tags, words)
        if not args.trees_only:
            print("\nParse {}:".format(index))
        print(tree)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
