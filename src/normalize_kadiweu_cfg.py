#!/usr/bin/env python3
"""Factor sentence-final PUNC out of root-category productions in a CFG.

For each category directly selected by ROOT, this script removes productions
whose final symbol is the terminal PUNC, retains the corresponding versions
without PUNC, and adds ROOT -> CATEGORY PUNC. This is appropriate when those
final PUNC symbols are sentence-final. A CFG file alone does not encode whether
the same category is used in root and embedded positions, so inspect the
affected categories if embedded final punctuation must be preserved.

The input and output files use NLTK CFG notation. NLTK is required.
"""

import argparse
import sys
from pathlib import Path

from nltk import CFG, Production
from nltk.grammar import Nonterminal


def unique_in_order(items):
    result = []
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def rhs_sort_key(rhs):
    return tuple(
        (0, symbol.symbol()) if isinstance(symbol, Nonterminal)
        else (1, str(symbol))
        for symbol in rhs
    )


def format_production(production):
    rhs = []
    for symbol in production.rhs():
        if isinstance(symbol, Nonterminal):
            rhs.append(symbol.symbol())
        else:
            rhs.append(repr(symbol))
    return "{} -> {}".format(production.lhs().symbol(), " ".join(rhs))


def normalize_grammar(grammar, start_name="ROOT", punctuation_tag="PUNC"):
    """Return normalized productions and basic transformation statistics."""
    start = Nonterminal(start_name)
    punctuation = punctuation_tag
    productions = list(grammar.productions())
    if not any(production.lhs() == start for production in productions):
        raise ValueError("no productions found for start symbol {!r}".format(start_name))

    root_productions = [p for p in productions if p.lhs() == start]
    root_categories = []
    existing_root_punct = set()
    for production in root_productions:
        rhs = production.rhs()
        if len(rhs) == 1 and isinstance(rhs[0], Nonterminal):
            root_categories.append(rhs[0])
        elif (len(rhs) == 2 and isinstance(rhs[0], Nonterminal)
              and rhs[1] == punctuation):
            root_categories.append(rhs[0])
            existing_root_punct.add(rhs[0])
    root_categories = unique_in_order(root_categories)
    if not root_categories:
        raise ValueError(
            "expected ROOT productions of the form ROOT -> CATEGORY"
        )

    transformed = []
    removed_punctuation_variants = 0
    categories_with_punc = set()

    for category in root_categories:
        category_rules = [p for p in productions if p.lhs() == category]
        for production in category_rules:
            rhs = production.rhs()
            if rhs and rhs[-1] == punctuation:
                categories_with_punc.add(category)
                rhs = rhs[:-1]
                transformed.append(Production(category, rhs))
                removed_punctuation_variants += 1
            else:
                transformed.append(production)

    # Keep all grammar rules whose LHS is not a direct ROOT category, along
    # with ROOT's existing rules. Add the sentence-final punctuation options.
    root_categories_set = set(root_categories)
    for production in productions:
        if production.lhs() == start:
            transformed.append(production)
        elif production.lhs() not in root_categories_set:
            transformed.append(production)

    added_root_rules = 0
    for category in root_categories:
        if category in categories_with_punc and category not in existing_root_punct:
            transformed.append(Production(start, (category, punctuation)))
            added_root_rules += 1

    transformed = unique_in_order(transformed)
    stats = {
        "categories": sorted(c.symbol() for c in categories_with_punc),
        "removed_punctuation_variants": removed_punctuation_variants,
        "added_root_punctuation_rules": added_root_rules,
    }
    return transformed, stats


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Move final PUNC alternatives from ROOT-selected categories to ROOT."
        )
    )
    parser.add_argument("-i", "--input", required=True, type=Path,
                        help="input NLTK CFG file")
    parser.add_argument("-o", "--output", required=True, type=Path,
                        help="path for the normalized CFG file")
    parser.add_argument("--start-symbol", default="ROOT",
                        help="CFG start symbol (default: ROOT)")
    parser.add_argument("--punct-tag", default="PUNC",
                        help="terminal to factor at sentence end (default: PUNC)")
    return parser


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    if not args.input.is_file():
        print("error: input grammar not found: {}".format(args.input), file=sys.stderr)
        return 2

    try:
        grammar = CFG.fromstring(args.input.read_text(encoding="utf-8"))
        productions, stats = normalize_grammar(
            grammar,
            start_name=args.start_symbol,
            punctuation_tag=args.punct_tag,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        start = Nonterminal(args.start_symbol)
        productions.sort(
            key=lambda p: (
                0 if p.lhs() == start else 1,
                p.lhs().symbol(),
                rhs_sort_key(p.rhs()),
            )
        )
        with args.output.open("w", encoding="utf-8", newline="\n") as output:
            output.write("# CFG normalized to factor sentence-final punctuation\n")
            output.write("# Start symbol: {}\n".format(args.start_symbol))
            output.write("# Categories with final PUNC factored: {}\n".format(
                ", ".join(stats["categories"])
            ))
            for production in productions:
                output.write(format_production(production) + "\n")
    except (OSError, UnicodeError, ValueError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2

    print("Normalized grammar written to {}".format(args.output))
    print("Categories normalized: {}".format(", ".join(stats["categories"])))
    print("Final-PUNC productions factored: {}".format(
        stats["removed_punctuation_variants"]
    ))
    print("ROOT punctuation alternatives added: {}".format(
        stats["added_root_punctuation_rules"]
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
