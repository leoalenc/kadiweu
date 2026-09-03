#!/usr/bin/env python3
"""Tests using only structures and terminals attested in DONE sentences."""

from __future__ import annotations

import unittest
from pathlib import Path
from kadiweu_constituency import iter_psd_records

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
    # Historical subtree tests assert local rules; sentence roots are tested
    # separately below with the complete, unfiltered assignment list.
    return [
        (a.dependent_position, a.head_position, a.deprel, a.rule)
        for a in infer_dependencies(parse_tree(tree_text, sent_id))
        if a.deprel != "root"
    ]


class ComplementRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = {r.corpussearch_id: r for r in iter_psd_records(
            Path(__file__).parent / "fixtures" / "complement_rules.psd")}

    def edges(self, sent_id):
        tree = self.records[sent_id].tree
        forms = {t.position: t.form.replace("@", "") for t in tree.tokens}
        return {(forms[a.dependent_position], forms.get(a.head_position, "ROOT"), a.deprel)
                for a in infer_dependencies(tree)}

    def test_six_attested_nominal_cp_objects(self):
        for sid, dep, head in [("hil-data,0.10", "niwatece", "idei"),
                               ("hil-data,0.60", "akiidi", "idei"),
                               ("van-data,0.19", "initaGa", "idei"),
                               ("van-data,0.20", "anitaGa", "idei"),
                               ("van-data,0.50", "anitaGa", "etee"),
                               ("van-data,0.51", "initaGa", "etee")]:
            with self.subTest(sentence=sid):
                self.assertIn((dep, head, "obj"), self.edges(sid))
                self.assertIn(("me", dep, "mark"), self.edges(sid))

    def test_attested_ee_subject_and_object(self):
        edges = self.edges("hil-data,0.12")
        self.assertIn(("ee", "Te", "nsubj"), edges)
        self.assertIn(("nigotaGa", "Te", "obj"), edges)

    def test_attested_parataxis_and_local_arguments(self):
        edges = self.edges("van-data,0.8")
        self.assertIn(("noxilece", "iwaGadi", "parataxis"), edges)
        self.assertIn(("lojetedi", "noxilece", "obj"), edges)
        self.assertIn(("niwatece", "iwaGadi", "nsubj"), edges)
        self.assertEqual([e for e in edges if e[2] == "root"], [("iwaGadi", "ROOT", "root")])

    def test_attested_dagaxa_contexts(self):
        self.assertIn(("daGaxa", "dakake", "advmod"), self.edges("van-data,0.12"))
        self.assertIn(("daGaxa", "ninitibeci", "advmod"), self.edges("van-data,0.24"))

    def test_attested_ina_heuristic(self):
        self.assertIn(("ina", "eteyo", "obj"), self.edges("van-data,0.49"))

    def test_determiner_heuristic_known_reference_disagreements(self):
        # Regression evidence, NOT an assertion that the gold nsubj is wrong.
        for sid in ("hil-data,0.17", "hil-data,0.18"):
            with self.subTest(sentence=sid):
                self.assertTrue(any(e[2] == "obj" for e in self.edges(sid)))

    def test_synthetic_guards(self):
        # Explicit English placeholders: these are structural negative tests,
        # not purported Kadiweu examples or additional DONE attestations.
        cases = [
            ("(IP-MAT (VBU verb) (NP (D determiner)))", "obj"),
            ("(IP-MAT (VBAPL verb) (NP (D determiner)))", "obj"),
            ("(IP-MAT (VB verb) (NP-SBJ (D determiner)))", "obj"),
            ("(IP-MAT (VB verb) (NP (PRO unknown)) (NP (N noun)))", "nsubj"),
            ("(IP-MAT (VB verb) (CP-me (C marker) (IP-SUB (VB embedded))))", "obj"),
            ("(IP-MAT (CP-me (C marker) (IP-SUB (NP (N noun)))))", "obj"),
            ("(IP-MAT (VB verb) (NP (N noun) (CP-me (C marker) (IP-SUB (NP (N other))))))", "obj"),
            ("(IP-MAT (VB verb) (IP-ADV (C marker) (VB other)))", "parataxis"),
            ("(IP-MAT (VB verb) (CONJ coordinator) (IP-ADV (VB other)))", "parataxis"),
            ("(IP-MAT (VB verb) (ADVP (ADV unknown)))", "advmod"),
            ("(IP-MAT (VB verb) (NP-TRACE (-NONE- *T*-1)) (NP (D determiner)))", "obj"),
            ("(IP-MAT (VB verb) (CP-me (C marker) (IP-SUB (NP (N first)) (NP (N second)))))", "obj"),
            ("(IP-MAT (VB verb) (CP-me (C marker) (IP-SUB (NP (N first)))) (CP-me (C marker) (IP-SUB (NP (N second)))))", "obj"),
        ]
        for source, forbidden in cases:
            with self.subTest(source=source):
                self.assertFalse(any(a.deprel == forbidden for a in infer_dependencies(parse_tree(source, "synthetic"))))

    def test_no_second_object_from_determiner_heuristic(self):
        tree = parse_tree("(IP-MAT (VB verb) (NP (D determiner)) (CP-me (C marker) (IP-SUB (NP (N noun)))))", "synthetic")
        assignments = infer_dependencies(tree)
        self.assertEqual(sum(a.deprel == "obj" for a in assignments), 1)
        self.assertFalse(any(a.dependent_position == 2 for a in assignments))

    def test_vbu_inside_ip_adv_retains_subject_rule(self):
        # Structural contrast to the attested VB case; English placeholders.
        tree = parse_tree("(IP-MAT (VB outer) (IP-ADV (VBU inner) (NP (N nominal))))", "synthetic")
        edges = {(a.dependent_position, a.head_position, a.deprel) for a in infer_dependencies(tree)}
        self.assertIn((3, 2, "nsubj"), edges)
        self.assertNotIn((3, 2, "obj"), edges)


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
        self.assertEqual(actual, [(1, 3, "advmod", "eliodi-verbal-modifier"),
                                  (2, 3, "mark", MARK_RULE)])

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


PED_049 = """(IP-MAT
  (IP-MAT (NP (N$ Niwatece)) (VB iwaGadi))
  (CONJP (CONJ codaa)
    (IP-MAT (NEG aG@) (VBU @dakake) (NP (N$ loojedi))))
  (PUNC .))"""


class ClauseStructureTests(unittest.TestCase):
    def edges(self, text, sent_id="synthetic-negative"):
        tree = parse_tree(text, sent_id)
        return {(a.dependent_position, a.head_position, a.deprel)
                for a in infer_dependencies(tree)}

    def test_coordination_ped_049(self):
        self.assertEqual(self.edges(PED_049, "ped-gramm,0.49"), {
            (2, 0, "root"), (3, 5, "cc"), (5, 2, "conj"),
            (4, 5, "advmod"), (7, 2, "punct"), (1, 2, "nsubj"), (6, 5, "nsubj")})

    def test_single_nominal_matrix_hil_028_029(self):
        for number, word in [(28, "libiniena"), (29, "libinienigi")]:
            with self.subTest(number=number):
                self.assertEqual(self.edges(f"(IP-MAT (NP (N$ {word})))",
                                           f"hil-data,0.{number}"), {(1, 0, "root")})

    def test_single_np_with_punctuation_hil_032(self):
        self.assertEqual(self.edges("(IP-MAT (NP (N Ninitibigiwaji)) (PUNC .))",
                                    "hil-data,0.32"), {(1, 0, "root"), (2, 1, "punct")})

    def test_predicate_and_subject_hil_003(self):
        self.assertEqual(self.edges("(IP-MAT (NP-SBJ (N$ LotaGa) (NP (N$ Ganioxoa))) "
                                    "(NP-PRD (N$ libinienaGa)))", "hil-data,0.3"),
                         {(1, 3, "nsubj"), (2, 1, "nmod:poss"), (3, 0, "root")})

    def test_cp_me_matrix_predicate_hil_025(self):
        self.assertEqual(self.edges("(IP-MAT (NP-SBJ (D naGana)) "
                                    "(CP-me (Q eliodi) (C me@) (IP-SUB (VB @ninitibeci))))",
                                    "hil-data,0.25"),
                         {(1, 4, "nsubj"), (2, 4, "advmod"), (3, 4, "mark"), (4, 0, "root")})

    def test_cp_d_sentence_root_van_056_057(self):
        for number, word in [(56, "jipegitege"), (57, "jipegitegi")]:
            with self.subTest(number=number):
                self.assertEqual(self.edges("(CP-D (NEG aG@) (NP (D @ica)) "
                                           f"(C daGa) (IP-SUB (VBAPL {word})))",
                                           f"van-data,0.{number}"),
                                 {(3, 4, "mark"), (4, 0, "root")})

    def test_verbless_capl_predicate_van_072(self):
        text = "(IP-MAT (NP (D ijowa) (N$ leonigipi) (NP (N iwaalo))) "
        text += "(CP (NP (D idi)) (CAPL metaGa)))"
        self.assertEqual(self.edges(text, "van-data,0.72"), {
            (1, 2, "det"), (2, 4, "nsubj"), (3, 2, "nmod:poss"),
            (4, 0, "root"), (5, 4, "mark")})

    # Deliberately artificial structures below test abstention/mechanics,
    # not additional Kadiwéu constructions or lexical attestations.
    def test_no_root_for_ambiguous_single_np(self):
        self.assertEqual(self.edges("(IP-MAT (NP (N first) (N second)))"), set())

    def test_no_root_for_two_verbs(self):
        self.assertEqual(self.edges("(IP-MAT (VB first) (VB second))"), set())

    def test_no_root_for_multiple_predicates(self):
        self.assertEqual(self.edges("(IP-MAT (NP-PRD (N first)) (NP-PRD (N second)))"), set())

    def test_ambiguous_np_not_discarded_when_resolving_ip_sub(self):
        tree = parse_tree("(IP-SUB (NP (N first)) (NP (N second) (N third)))", "negative")
        self.assertIsNone(ud_head(tree.root))

    def test_no_mark_for_capl_without_np(self):
        self.assertEqual(self.edges("(CP (CAPL marker))"), set())

    def test_no_capl_fallback_with_two_nps(self):
        self.assertEqual(self.edges("(CP (NP (D first)) (NP (D second)) (CAPL marker))"), set())

    def test_no_capl_fallback_with_overt_verb(self):
        self.assertEqual(self.edges("(CP (NP (D first)) (CAPL marker) (VB verb))"), set())

    def test_single_np_subject_default(self):
        self.assertEqual(self.edges("(IP-MAT (NP (N noun)) (VB verb))"),
                         {(2, 0, "root"), (1, 2, "nsubj")})

    def test_nested_coordination_keeps_local_edges(self):
        text = "(IP-MAT (IP-MAT (VB first)) (CONJP (CONJ and) "
        text += "(IP-MAT (IP-MAT (VB second)) (CONJP (CONJ and) (IP-MAT (VB third))))))"
        self.assertEqual(self.edges(text), {(1, 0, "root"), (2, 3, "cc"),
                                          (3, 1, "conj"), (4, 5, "cc"), (5, 3, "conj")})

    def test_malformed_coordination_does_not_pick_first(self):
        self.assertEqual(self.edges("(IP-MAT (IP-MAT (VB first)) "
                                    "(CONJP (CONJ and) (CONJ or) (IP-MAT (VB second))))"), set())

    def test_embedded_ip_mat_does_not_get_root(self):
        self.assertEqual(self.edges("(IP-MAT (VB outer) (CP-OTHER (IP-MAT (VB inner))))"),
                         {(1, 0, "root")})

    def test_empty_trace_never_becomes_root(self):
        self.assertEqual(self.edges("(IP-MAT (NP-TRACE (-NONE- *T*-1)))"), set())

    def test_modifier_rules_apply_inside_second_conjunct(self):
        text = "(IP-MAT (IP-MAT (VB first)) (CONJP (CONJ and) "
        text += "(IP-MAT (NP-SBJ (D the) (N noun)) (NP-PRD (N predicate)))))"
        self.assertEqual(self.edges(text), {(1, 0, "root"), (2, 5, "cc"),
                                          (3, 4, "det"), (4, 5, "nsubj"), (5, 1, "conj")})


class ArgumentAndRaisingTests(unittest.TestCase):
    # Attested minimal complete raising example: DONE ped-gramm,0.58.
    RAISING = "(IP-MAT (NP-1 (N etogo)) (NEG aG@) (VBU @dakake) " \
              "(NP (NP-GEN (-NONE- *T*-1)) (N$ lojedi)))"

    def assignments(self, text):
        return infer_dependencies(parse_tree(text, "test"))

    def test_raising_ped_058(self):
        aa = self.assignments(self.RAISING)
        self.assertEqual({(a.dependent_position, a.head_position, a.deprel) for a in aa},
                         {(1, 3, "dislocated"), (2, 3, "advmod"), (3, 0, "root"), (5, 3, "nsubj")})
        self.assertEqual(next(a.rule for a in aa if a.deprel == "nsubj"), "unaccusative-subject")

    def test_cross_cp_raising_hil_009(self):
        text = "(IP-MAT (NP-1 (D NiGida) (N niwenigi)) (CP-me (Q eliodi) "
        text += "(C me) (IP-SUB (VBU dakake) (NP (NP-GEN (-NONE- *T*-1)) (N$ loojedi)))))"
        aa = self.assignments(text)
        self.assertIn((2, 5, "dislocated"), [(a.dependent_position,a.head_position,a.deprel) for a in aa])
        self.assertIn((7, 5, "nsubj"), [(a.dependent_position,a.head_position,a.deprel) for a in aa])
        self.assertEqual(sum(a.deprel == "nsubj" for a in aa), 1)

    def test_relative_and_genitive_traces_hil_005(self):
        text = "(IP-MAT (NP-1 (N Etogo) (CP-REL (WNP-2 (WPRO ane@)) "
        text += "(IP-SUB (NP-TRACE (-NONE- *T*-2)) (VB @iwaGadi)))) "
        text += "(NEG aG@) (VBU @dakake) (NP (NP-GEN (-NONE- *T*-1)) (N$ lojedi)))"
        edges = {(a.dependent_position,a.head_position,a.deprel) for a in self.assignments(text)}
        self.assertTrue({(1,6,"dislocated"),(2,4,"nsubj"),(4,1,"acl:relcl"),(8,6,"nsubj")} <= edges)
        self.assertFalse(any(d in {3,7} or h in {3,7} for d,h,_ in edges))

    def test_svo_ped_002(self):
        aa = self.assignments("(IP-MAT (NP (D ajo) (N$ liwatece)) (VB etadi) (NP (N weiigi)))")
        self.assertTrue({(2,3,"nsubj"),(4,3,"obj")} <=
                        {(a.dependent_position,a.head_position,a.deprel) for a in aa})

    # Explicitly artificial structural boundary tests; no claimed attestations.
    def test_vbu_never_uses_svo_object_default(self):
        aa = self.assignments("(IP-MAT (NP (N first)) (VBU predicate) (NP (N second)))")
        self.assertFalse(any(a.deprel in {"obj","nsubj"} for a in aa))

    def test_apl_not_promoted_to_subject(self):
        aa = self.assignments("(IP-MAT (VBAPL predicate) (NP-APL (N argument)))")
        self.assertEqual([(a.deprel,a.rule) for a in aa if a.dependent_position == 2],
                         [("obj","applicative-argument")])

    def test_single_subject_plus_apl(self):
        aa = self.assignments("(IP-MAT (NP (N subject)) (VBAPL predicate) (NP-APL (N applied)))")
        self.assertTrue({(1,2,"nsubj"),(3,2,"obj")} <=
                        {(a.dependent_position,a.head_position,a.deprel) for a in aa})

    def test_ambiguous_np_blocks_single_argument_guess(self):
        aa = self.assignments("(IP-MAT (NP (N one) (N two)) (VB verb) (NP (N three)))")
        self.assertFalse(any(a.deprel in {"nsubj","obj"} for a in aa))

    def test_mismatched_genitive_index_abstains(self):
        aa = self.assignments(self.RAISING.replace('*T*-1','*T*-2'))
        self.assertFalse(any(a.deprel == "dislocated" for a in aa))
        self.assertFalse(any(a.dependent_position == 1 for a in aa))

    def test_duplicate_antecedents_abstain(self):
        aa = self.assignments(self.RAISING.replace('(NEG aG@)', '(NP-1 (N duplicate)) (NEG aG@)'))
        self.assertFalse(any(a.deprel == "dislocated" for a in aa))

    def test_duplicate_traces_abstain(self):
        aa = self.assignments(self.RAISING.replace('(N$ lojedi)', '(NP-GEN (-NONE- *T*-1)) (N$ lojedi)'))
        self.assertFalse(any(a.deprel == "dislocated" for a in aa))

    def test_nonpossessive_head_abstains(self):
        aa = self.assignments(self.RAISING.replace('(N$ lojedi)', '(N placeholder)'))
        self.assertFalse(any(a.deprel == "dislocated" for a in aa))

    def test_unrelated_clause_index_not_reused(self):
        text = "(IP-MAT (IP-MAT (NP-1 (N first)) (VB predicate)) "
        text += "(CONJP (CONJ and) (IP-MAT (VBU other) (NP (NP-GEN (-NONE- *T*-1)) (N$ possessed)))))"
        self.assertFalse(any(a.deprel == "dislocated" for a in self.assignments(text)))

    def test_unknown_q_not_generalized(self):
        aa = self.assignments("(CP-me (Q unknown) (C marker) (IP-SUB (VB verb)))")
        self.assertFalse(any(a.deprel == "advmod" for a in aa))


if __name__ == "__main__":
    unittest.main()
