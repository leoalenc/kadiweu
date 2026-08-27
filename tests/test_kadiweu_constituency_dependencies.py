#!/usr/bin/env python3
"""Tests for certain constituency-derived Kadiwéu dependencies."""

from __future__ import annotations

import unittest

from kadiweu_constituency import tree_from_psd_record
from kadiweu_constituency_dependencies import (
    DETERMINER_RULE,
    POSSESSOR_RULE,
    infer_dependencies,
    lexical_head,
)


def parse_tree(tree_text: str):
    tree, _ = tree_from_psd_record(f"({tree_text} (ID test,0.1))")
    return tree


def assignment_tuples(tree_text: str):
    return [
        (a.dependent_position, a.head_position, a.deprel, a.rule)
        for a in infer_dependencies(parse_tree(tree_text))
    ]


class LexicalHeadTests(unittest.TestCase):
    def test_determiner_can_be_sole_np_head(self):
        tree = parse_tree("(NP (D idi))")
        self.assertEqual(lexical_head(tree.root).form, "idi")

    def test_pronoun_can_be_sole_np_head(self):
        tree = parse_tree("(NP (PRO jema))")
        self.assertEqual(lexical_head(tree.root).form, "jema")

    def test_simple_d_n_np_is_headed_by_n(self):
        tree = parse_tree("(NP (D idi) (N niweiigi))")
        self.assertEqual(lexical_head(tree.root).form, "niweiigi")

    def test_ambiguous_np_has_no_guessed_head(self):
        tree = parse_tree("(NP (N one) (N two))")
        self.assertIsNone(lexical_head(tree.root))


class PossessiveNPTests(unittest.TestCase):
    def test_possessum_precedes_possessor(self):
        actual = assignment_tuples(
            "(NP-SBJ (N$ LotaGa) (NP (N$ Ganioxoa)))"
        )
        self.assertEqual(actual, [(2, 1, "nmod:poss", POSSESSOR_RULE)])

    def test_possessor_precedes_possessum(self):
        actual = assignment_tuples(
            "(NP-APL (NP (N niweiigi)) (N$ nigotaGa))"
        )
        self.assertEqual(actual, [(1, 2, "nmod:poss", POSSESSOR_RULE)])

    def test_determiner_with_possessum_possessor_order(self):
        actual = assignment_tuples(
            "(NP (D ijo) (N$ ligetedi) (NP (N$ liwigo)))"
        )
        self.assertEqual(
            actual,
            [
                (1, 2, "det", DETERMINER_RULE),
                (3, 2, "nmod:poss", POSSESSOR_RULE),
            ],
        )

    def test_determiner_with_possessor_possessum_order(self):
        actual = assignment_tuples(
            "(NP (D NiGidoa) (NP (N waca)) (N$ lotiidi))"
        )
        self.assertEqual(
            actual,
            [
                (1, 3, "det", DETERMINER_RULE),
                (2, 3, "nmod:poss", POSSESSOR_RULE),
            ],
        )

    def test_determiner_can_head_possessor_np(self):
        actual = assignment_tuples("(NP (N$ LotaGa) (NP (D idi)))")
        self.assertEqual(actual, [(2, 1, "nmod:poss", POSSESSOR_RULE)])

    def test_recursive_possession(self):
        actual = assignment_tuples(
            "(NP (N$ outer) (NP (N$ inner) (NP (PRO possessor))))"
        )
        self.assertEqual(
            actual,
            [
                (2, 1, "nmod:poss", POSSESSOR_RULE),
                (3, 2, "nmod:poss", POSSESSOR_RULE),
            ],
        )

    def test_two_np_daughters_are_left_unresolved(self):
        actual = assignment_tuples(
            "(NP (NP (N first)) (N$ head) (NP (N second)))"
        )
        self.assertEqual(actual, [])

    def test_two_possessum_candidates_are_left_unresolved(self):
        actual = assignment_tuples("(NP (N$ one) (NP (N poss)) (N$ two))")
        self.assertEqual(actual, [])

    def test_additional_unrecognized_daughter_is_left_unresolved(self):
        actual = assignment_tuples(
            "(NP (Q two) (N$ head) (NP (N possessor)))"
        )
        self.assertEqual(actual, [])

    def test_relative_clause_is_not_mistaken_for_possessor(self):
        actual = assignment_tuples(
            "(NP (N head) (CP-REL (IP-SUB (VB predicate))))"
        )
        self.assertEqual(actual, [])


if __name__ == "__main__":
    unittest.main()
