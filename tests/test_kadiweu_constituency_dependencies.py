#!/usr/bin/env python3
"""Tests using only structures and terminals attested in DONE sentences."""

from __future__ import annotations

import unittest

from kadiweu_constituency import tree_from_psd_record
from kadiweu_constituency_dependencies import (
    DETERMINER_RULE,
    MARK_RULE,
    POSSESSOR_RULE,
    RELATIVE_CLAUSE_RULE,
    RELATIVE_PRONOUN_RULE,
    infer_dependencies,
    lexical_head,
    ud_head,
)


def parse_tree(tree_text: str, sent_id: str):
    """Parse a literal subtree copied from the named DONE sentence."""
    tree, _ = tree_from_psd_record(f"({tree_text} (ID {sent_id}))")
    return tree


def assignment_tuples(tree_text: str, sent_id: str):
    return [
        (a.dependent_position, a.head_position, a.deprel, a.rule)
        for a in infer_dependencies(parse_tree(tree_text, sent_id))
    ]


class LexicalHeadTests(unittest.TestCase):
    def test_determiner_can_be_sole_np_head_hil_017(self):
        tree = parse_tree("(NP (D naGada))", "hil-data,0.17")
        self.assertEqual(lexical_head(tree.root).form, "naGada")

    def test_pronoun_can_be_sole_np_head_hil_012(self):
        tree = parse_tree("(NP (PRO ee))", "hil-data,0.12")
        self.assertEqual(lexical_head(tree.root).form, "ee")

    def test_d_n_np_is_headed_by_n_hil_009(self):
        tree = parse_tree(
            "(NP (D NiGida) (N niwenigi))",
            "hil-data,0.9",
        )
        self.assertEqual(lexical_head(tree.root).form, "niwenigi")

    def test_proper_noun_heads_np_hil_060(self):
        tree = parse_tree("(NP (NPR Maria))", "hil-data,0.60")
        self.assertEqual(lexical_head(tree.root).form, "Maria")

    def test_noun_heads_np_with_relative_clause_hil_005(self):
        tree = parse_tree(
            "(NP (N Etogo) (CP-REL (WNP-1 (WPRO ane@)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-1)) (VB @iwaGadi))))",
            "hil-data,0.5",
        )
        self.assertEqual(lexical_head(tree.root).form, "Etogo")

    def test_two_nominal_head_candidates_are_ambiguous(self):
        # Negative robustness test: uppercase forms are metavariables, not
        # purported Kadiwéu words.
        tree = parse_tree(
            "(NP (N NOUN_ONE) (N NOUN_TWO))",
            "negative-test,0.1",
        )
        self.assertIsNone(lexical_head(tree.root))


class PossessiveNPTests(unittest.TestCase):
    def test_possessum_precedes_possessor_hil_003(self):
        actual = assignment_tuples(
            "(NP-SBJ (N$ LotaGa) (NP (N$ Ganioxoa)))",
            "hil-data,0.3",
        )
        self.assertEqual(actual, [(2, 1, "nmod:poss", POSSESSOR_RULE)])

    def test_possessor_precedes_possessum_ped_047(self):
        actual = assignment_tuples(
            "(NP-APL (NP (N niweiigi)) (N$ nigotaGa))",
            "ped-gramm,0.47",
        )
        self.assertEqual(actual, [(1, 2, "nmod:poss", POSSESSOR_RULE)])

    def test_determiner_possessum_possessor_van_031(self):
        actual = assignment_tuples(
            "(NP-SBJ (D ica) (N$ liwigo) (NP (N niganigawanigi)))",
            "van-data,0.31",
        )
        self.assertEqual(
            actual,
            [
                (1, 2, "det", DETERMINER_RULE),
                (3, 2, "nmod:poss", POSSESSOR_RULE),
            ],
        )

    def test_determiner_possessor_possessum_hil_041(self):
        actual = assignment_tuples(
            "(NP (D NiGidoa) (NP (N waca)) (N$ lotiidi))",
            "hil-data,0.41",
        )
        self.assertEqual(
            actual,
            [
                (1, 3, "det", DETERMINER_RULE),
                (2, 3, "nmod:poss", POSSESSOR_RULE),
            ],
        )

    def test_two_np_daughters_are_unresolved_hil_043(self):
        actual = assignment_tuples(
            "(NP-SBJ (D niGidiwa) (NP (N okokodi)) "
            "(N$ ligetedi) (NP (N$ liwigo)))",
            "hil-data,0.43",
        )
        # Possession is unresolved, but the immediate D and unique N$ still
        # establish a certain determiner dependency.
        self.assertEqual(actual, [(1, 3, "det", DETERMINER_RULE)])

    def test_q_modifier_with_possession_van_071(self):
        actual = assignment_tuples(
            "(NP-SBJ (Q idiwa) (N$ leonigipi) (NP (NPR Maria)))",
            "van-data,0.71",
        )
        self.assertEqual(
            actual,
            [
                (1, 2, "det", DETERMINER_RULE),
                (3, 2, "nmod:poss", POSSESSOR_RULE),
            ],
        )

    def test_relative_clause_is_not_a_possessor_hil_005(self):
        actual = assignment_tuples(
            "(NP (N Etogo) (CP-REL (WNP-1 (WPRO ane@)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-1)) (VB @iwaGadi))))",
            "hil-data,0.5",
        )
        self.assertNotIn("nmod:poss", [assignment[2] for assignment in actual])

    def test_two_possessum_candidates_are_unresolved(self):
        # Negative robustness test: uppercase forms are metavariables, not
        # purported Kadiwéu words.
        actual = assignment_tuples(
            "(NP (N$ POSSESSUM_ONE) (NP (N POSSESSOR)) "
            "(N$ POSSESSUM_TWO))",
            "negative-test,0.2",
        )
        self.assertEqual(actual, [])

    def test_determiner_only_np_can_be_a_possessor(self):
        # Prospective compositional test.  The components are attested in DONE:
        # (N$ LotaGa) in hil-data,0.3 and (NP (D naGada)) in hil-data,0.17.
        actual = assignment_tuples(
            "(NP (N$ LotaGa) (NP (D naGada)))",
            "prospective-test,0.1",
        )
        self.assertEqual(actual, [(2, 1, "nmod:poss", POSSESSOR_RULE)])

    def test_recursive_possession(self):
        # Prospective compositional test.  LotaGa and Ganioxoa occur in the
        # possessive NP in hil-data,0.3; (NP (PRO ee)) occurs in hil-data,0.12.
        actual = assignment_tuples(
            "(NP (N$ LotaGa) (NP (N$ Ganioxoa) (NP (PRO ee))))",
            "prospective-test,0.2",
        )
        self.assertEqual(
            actual,
            [
                (2, 1, "nmod:poss", POSSESSOR_RULE),
                (3, 2, "nmod:poss", POSSESSOR_RULE),
            ],
        )


class GeneralDeterminerTests(unittest.TestCase):
    def test_nonpossessive_determiner_hil_009(self):
        actual = assignment_tuples(
            "(NP (D NiGida) (N niwenigi))",
            "hil-data,0.9",
        )
        self.assertEqual(actual, [(1, 2, "det", DETERMINER_RULE)])

    def test_nonpossessive_determiner_hil_060(self):
        actual = assignment_tuples(
            "(NP (D @idi) (N akiidi))",
            "hil-data,0.60",
        )
        self.assertEqual(actual, [(1, 2, "det", DETERMINER_RULE)])

    def test_determiner_only_np_does_not_license_det_hil_017(self):
        actual = assignment_tuples("(NP (D naGada))", "hil-data,0.17")
        self.assertEqual(actual, [])

    def test_determiner_plus_proper_noun_is_not_generalized(self):
        # Negative prospective test: uppercase forms are category
        # metavariables, not purported Kadiwéu words.
        actual = assignment_tuples(
            "(NP (D DETERMINER) (NPR PROPER_NOUN))",
            "negative-test,0.3",
        )
        self.assertEqual(actual, [])

    def test_dapl_modifies_overt_noun_van_014(self):
        actual = assignment_tuples(
            "(NP (DAPL @anitaGa) (N niwatece))",
            "van-data,0.14",
        )
        self.assertEqual(actual, [(1, 2, "det", DETERMINER_RULE)])

    def test_q_and_d_both_modify_np_head_van_030(self):
        actual = assignment_tuples(
            "(NP-PRD (Q @ica) (D digoida) (N$ liGeladi))",
            "van-data,0.30",
        )
        self.assertEqual(
            actual,
            [
                (1, 3, "det", DETERMINER_RULE),
                (2, 3, "det", DETERMINER_RULE),
            ],
        )

    def test_dapl_only_np_does_not_license_det_van_019(self):
        actual = assignment_tuples(
            "(NP (DAPL @initaGa))",
            "van-data,0.19",
        )
        self.assertEqual(actual, [])


class FunctionalHeadTests(unittest.TestCase):
    def test_ip_sub_with_nominal_predicate_hil_007(self):
        tree = parse_tree(
            "(IP-SUB (NP (N$ libinienigi)))",
            "hil-data,0.7",
        )
        self.assertEqual(ud_head(tree.root).form, "libinienigi")

    def test_ip_sub_with_verbal_predicate_hil_025(self):
        tree = parse_tree(
            "(IP-SUB (VB @ninitibeci))",
            "hil-data,0.25",
        )
        self.assertEqual(ud_head(tree.root).form, "@ninitibeci")

    def test_complementizer_marks_nominal_predicate_hil_060(self):
        actual = assignment_tuples(
            "(CP-me (C me@) (IP-SUB (NP (D @idi) (N akiidi))))",
            "hil-data,0.60",
        )
        self.assertEqual(
            actual,
            [
                (1, 3, "mark", MARK_RULE),
                (2, 3, "det", DETERMINER_RULE),
            ],
        )

    def test_complementizer_marks_verbal_predicate_hil_025(self):
        actual = assignment_tuples(
            "(CP-me (Q eliodi) (C me@) (IP-SUB (VB @ninitibeci)))",
            "hil-data,0.25",
        )
        self.assertEqual(actual, [(2, 3, "mark", MARK_RULE)])

    def test_q_modifies_ip_sub_head_van_010(self):
        actual = assignment_tuples(
            "(CP-me (Q eliodi) (C me) "
            "(IP-SUB (NP (N$ libinienigi))))",
            "van-data,0.10",
        )
        self.assertEqual(
            actual,
            [
                (1, 3, "det", DETERMINER_RULE),
                (2, 3, "mark", MARK_RULE),
            ],
        )

    def test_complementizer_marks_sole_dapl_van_019(self):
        actual = assignment_tuples(
            "(CP-me (C me@) (IP-SUB (NP (DAPL @initaGa))))",
            "van-data,0.19",
        )
        self.assertEqual(actual, [(1, 2, "mark", MARK_RULE)])

    def test_relative_c_instead_of_wpro_is_unresolved(self):
        actual = assignment_tuples(
            "(CP-REL (WNP-1 (C ane@)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-1)) (VB @iwaGadi)))",
            "negative-test,0.4",
        )
        self.assertEqual(actual, [])


class RelativeClauseTests(unittest.TestCase):
    def test_ane_subject_relative_hil_039(self):
        actual = assignment_tuples(
            "(NP (D NaGani) (N wetiGa) "
            "(CP-REL (WNP-1 (WPRO ane)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-1)) (VB iwaGadi))))",
            "hil-data,0.39",
        )
        self.assertEqual(
            actual,
            [
                (1, 2, "det", DETERMINER_RULE),
                (3, 5, "nsubj", RELATIVE_PRONOUN_RULE),
                (5, 2, "acl:relcl", RELATIVE_CLAUSE_RULE),
            ],
        )

    def test_fused_ane_subject_relative_hil_005(self):
        actual = assignment_tuples(
            "(NP (N Etogo) (CP-REL (WNP-2 (WPRO ane@)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-2)) (VB @iwaGadi))))",
            "hil-data,0.5",
        )
        self.assertEqual(
            actual,
            [
                (2, 4, "nsubj", RELATIVE_PRONOUN_RULE),
                (4, 1, "acl:relcl", RELATIVE_CLAUSE_RULE),
            ],
        )

    def test_ane_with_nominal_predicate_ped_024(self):
        actual = assignment_tuples(
            "(NP (N naigi) (CP-REL (WNP-1 (WPRO ane@)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-1)) "
            "(NP (N @napioi)))))",
            "ped-gramm,0.24",
        )
        self.assertEqual(
            actual,
            [
                (2, 4, "nsubj", RELATIVE_PRONOUN_RULE),
                (4, 1, "acl:relcl", RELATIVE_CLAUSE_RULE),
            ],
        )

    def test_me_restrictive_relative_ped_025(self):
        actual = assignment_tuples(
            "(NP (N naigi) "
            "(CP-me (C me) (IP-SUB (NP (N napioi)))))",
            "ped-gramm,0.25",
        )
        self.assertEqual(
            actual,
            [
                (2, 3, "mark", MARK_RULE),
                (3, 1, "acl:relcl", RELATIVE_CLAUSE_RULE),
            ],
        )

    def test_clause_level_me_is_not_relative_hil_007(self):
        actual = assignment_tuples(
            "(IP-MAT (NP-SBJ (N$ Gawenigi)) "
            "(CP-me (Q eliodi) (C me) "
            "(IP-SUB (NP (N$ libinienigi)))))",
            "hil-data,0.7",
        )
        self.assertNotIn("acl:relcl", [assignment[2] for assignment in actual])

    def test_mismatched_ane_trace_is_unresolved(self):
        actual = assignment_tuples(
            "(NP (N Etogo) (CP-REL (WNP-1 (WPRO ane)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-2)) (VB iwaGadi))))",
            "negative-test,0.5",
        )
        self.assertEqual(actual, [])

    def test_free_relative_is_unresolved(self):
        actual = assignment_tuples(
            "(NP (CP-FRL (WNP-1 (WPRO ane)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-1)) (VB iwaGadi))))",
            "negative-test,0.6",
        )
        self.assertEqual(actual, [])


if __name__ == "__main__":
    unittest.main()
