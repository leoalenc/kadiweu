#!/usr/bin/env python3
"""Tests for gold/constituency dependency comparison."""

from __future__ import annotations

import tempfile
import textwrap
import unittest
import csv
import io
from pathlib import Path

from kadiweu_constituency import PsdRecord, tree_from_psd_record
from kadiweu_constituency import iter_psd_records
from compare_constituency_ud_dependencies import (
    DEFAULT_RELATIONS,
    align_tokens,
    comparison_rows,
    iter_conllu_sentences,
)


RELATIONS = {"nmod:poss", "det", "mark", "acl:relcl", "nsubj"}


def psd_record(tree_text: str, sent_id: str, sent_uid: str) -> PsdRecord:
    tree, corpussearch_id = tree_from_psd_record(
        f"({tree_text} (ID {sent_id}))", metadata={"uid": sent_uid, "status": "DONE"}
    )
    return PsdRecord(tree, {"uid": sent_uid, "status": "DONE"}, corpussearch_id)


def conllu_sentence(text: str):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "fixture.conllu"
        path.write_text(textwrap.dedent(text).strip() + "\n\n", encoding="utf-8")
        return list(iter_conllu_sentences(path))[0]


class NewRulesReferenceTests(unittest.TestCase):
    def test_attested_reference_comparison_and_known_disagreements(self):
        fixtures = Path(__file__).parent / "fixtures"
        rows = list(comparison_rows(list(iter_psd_records(fixtures / "complement_rules.psd")),
                                   list(iter_conllu_sentences(fixtures / "complement_rules.conllu")),
                                   set(DEFAULT_RELATIONS)))
        self.assertIn("parataxis", DEFAULT_RELATIONS)
        self.assertFalse(any(r["comparison"] == "GOLD_ONLY" for r in rows))
        mismatches = {(r["sent_id"], r["comparison"]) for r in rows if r["comparison"] != "MATCH"}
        self.assertEqual(mismatches, {("hil-data,0.17", "DEPREL_MISMATCH"),
                                     ("hil-data,0.18", "DEPREL_MISMATCH")})
        self.assertTrue(any(r["deprel"] == "parataxis" and r["comparison"] == "MATCH" for r in rows))


class ConlluParsingTests(unittest.TestCase):
    def test_mwt_range_rows_are_ignored(self):
        sentence = conllu_sentence(
            """
# sent_id = ped-gramm-7
# sent_uid = e553e02e-0d33-4fed-8f6a-b7cf5c9cf9c9
1\tliGeladi\tGeladi\tNOUN\tN$\t_\t4\tnsubj\t_\t_
2\tMaria\tmaria\tPROPN\tNPR\t_\t1\tnmod:poss\t_\t_
3-4\taGipegetege\t_\t_\t_\t_\t_\t_\t_\t_
3\taG\taG\tPART\tNEG\t_\t4\tadvmod\t_\t_
4\tipegetege\tpegi\tVERB\tVBAPL\t_\t0\troot\t_\t_
            """
        )
        self.assertEqual([token.id for token in sentence.tokens], [1, 2, 3, 4])


class ComparisonTests(unittest.TestCase):
    def test_match_ane_relative_hil_039(self):
        uid = "38f73c1c-ddfb-4153-9310-d24214cd68e7"
        record = psd_record(
            "(IP-MAT (NP (D NaGani) (N wetiGa) "
            "(CP-REL (WNP-1 (WPRO ane)) "
            "(IP-SUB (NP-TRACE (-NONE- *T*-1)) (VB iwaGadi)))) "
            "(VBAPL eniteloco) (NP-APL (N$ iGonagi)))",
            "hil-data,0.39",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = hil-data-39
# sent_uid = {uid}
1\tNaGani\t_\tDET\tD\t_\t2\tdet\t_\t_
2\twetiGa\t_\tNOUN\tN\t_\t5\tnsubj\t_\t_
3\tane\t_\tPRON\tWPRO\tPronType=Rel\t4\tnsubj\t_\t_
4\tiwaGadi\t_\tVERB\tVB\t_\t2\tacl:relcl\t_\t_
5\teniteloco\t_\tVERB\tVBAPL\t_\t0\troot\t_\t_
6\tiGonagi\t_\tNOUN\tN$\t_\t5\tobj\t_\t_
            """
        )
        rows = list(comparison_rows([record], [gold], RELATIONS))
        by_dependent = {row["gold_dependent"]: row for row in rows}
        self.assertEqual(by_dependent["ane"]["comparison"], "MATCH")
        self.assertEqual(by_dependent["iwaGadi"]["comparison"], "MATCH")
        self.assertEqual(by_dependent["wetiGa"]["comparison"], "MATCH")

    def test_match_me_relative_ped_025(self):
        uid = "a4d33655-fe74-4df2-8d5e-b3c88fba5fd1"
        record = psd_record(
            "(IP-MAT (NP (N$ iGeladi)) (VB idei) "
            "(NP (N naigi) "
            "(CP-me (C me) (IP-SUB (NP (N napioi))))))",
            "ped-gramm,0.25",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = ped-gramm-25
# sent_uid = {uid}
1\tiGeladi\t_\tNOUN\tN$\t_\t2\tnsubj\t_\t_
2\tidei\t_\tVERB\tVB\t_\t0\troot\t_\t_
3\tnaigi\t_\tNOUN\tN\t_\t2\tobj\t_\t_
4\tme\t_\tSCONJ\tC\t_\t5\tmark\t_\t_
5\tnapioi\t_\tNOUN\tN\t_\t3\tacl:relcl\t_\t_
            """
        )
        rows = list(comparison_rows([record], [gold], RELATIONS))
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["comparison"] for r in rows], ["MATCH", "MATCH", "MATCH"])

    def test_attested_match_hil_003(self):
        uid = "39f34955-a828-47d7-808d-b3b3565b42d6"
        record = psd_record(
            "(IP-MAT (NP-SBJ (N$ LotaGa) (NP (N$ Ganioxoa))) "
            "(NP-PRD (N$ libinienaGa)))",
            "hil-data,0.3",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = hil-data-3
# sent_uid = {uid}
1\tLotaGa\t_\tNOUN\tN$\t_\t3\tnsubj\t_\t_
2\tGanioxoa\t_\tNOUN\tN$\t_\t1\tnmod:poss\t_\t_
3\tlibinienaGa\t_\tNOUN\tN$\t_\t0\troot\t_\t_
4\t.\t.\tPUNCT\tPUNC\t_\t3\tpunct\t_\t_
            """
        )
        rows = list(comparison_rows([record], [gold], RELATIONS))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["comparison"], "MATCH")
        self.assertEqual(rows[0]["token_alignment"], "FINAL_PUNCT_IGNORED")

    def test_attested_head_mismatch_hil_044(self):
        uid = "83fdcd4c-338f-4a9f-8545-da8539e67e9d"
        record = psd_record(
            "(IP-MAT (NP-1 (D NiGidiwa) (NP (N noGojedi)) "
            "(N$ lixagotaGaGa)) (NEG aG@) (VBU @dakake) "
            "(NP (NP-GEN (-NONE- *T*-1)) (N$ loojedi)))",
            "hil-data,0.44",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = hil-data-44
# sent_uid = {uid}
1\tNiGidiwa\t_\tDET\tD\t_\t2\tdet\t_\t_
2\tnoGojedi\t_\tNOUN\tN\t_\t3\tnmod:poss\t_\t_
3\tlixagotaGaGa\t_\tNOUN\tN$\t_\t5\tdislocated\t_\t_
4\taG\t_\tPART\tNEG\t_\t5\tadvmod\t_\t_
5\tdakake\t_\tVERB\tVBU\t_\t0\troot\t_\t_
6\tloojedi\t_\tNOUN\tN$\t_\t5\tnsubj\t_\t_
7\t.\t.\tPUNCT\tPUNC\t_\t5\tpunct\t_\t_
            """
        )
        rows = list(comparison_rows([record], [gold], RELATIONS))
        by_dependent = {row["gold_dependent"]: row for row in rows}
        self.assertEqual(by_dependent["NiGidiwa"]["comparison"], "HEAD_MISMATCH")
        self.assertEqual(by_dependent["noGojedi"]["comparison"], "MATCH")

    def test_match_nonpossessive_determiner_hil_009(self):
        uid = "0ca977cd-2edf-45d9-b958-068648aebef9"
        record = psd_record(
            "(IP-MAT (NP (D NiGida) (N niwenigi)) (VB etadi) (NP (N weiigi)))",
            "hil-data,0.9",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = hil-data-9
# sent_uid = {uid}
1\tNiGida\t_\tDET\tD\t_\t2\tdet\t_\t_
2\tniwenigi\t_\tNOUN\tN\t_\t3\tnsubj\t_\t_
3\tetadi\t_\tVERB\tVB\t_\t0\troot\t_\t_
4\tweiigi\t_\tNOUN\tN\t_\t3\tobj\t_\t_
            """
        )
        rows = list(comparison_rows([record], [gold], RELATIONS))
        self.assertEqual(rows[0]["comparison"], "MATCH")

    def test_match_complementizer_hil_025(self):
        uid = "24a9e039-79d0-4026-8824-0d061c2b21ee"
        record = psd_record(
            "(IP-MAT (NP-SBJ (D naGana)) "
            "(CP-me (Q eliodi) (C me@) (IP-SUB (VB @ninitibeci))))",
            "hil-data,0.25",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = hil-data-25
# sent_uid = {uid}
1\tnaGana\t_\tPRON\tD\t_\t4\tnsubj\t_\t_
2\teliodi\t_\tADV\tQ\t_\t4\tadvmod\t_\t_
3\tme\t_\tSCONJ\tC\t_\t4\tmark\t_\t_
4\tninitibeci\t_\tVERB\tVB\t_\t0\troot\t_\t_
            """
        )
        rows = list(comparison_rows([record], [gold], RELATIONS))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["comparison"], "MATCH")

    def test_match_q_and_mark_with_nominal_ip_van_010(self):
        uid = "0c38eab8-c6b0-4f02-bf05-27ea6285fe70"
        record = psd_record(
            "(CP-me (Q eliodi) (C me) "
            "(IP-SUB (NP (N$ libinienigi))))",
            "van-data,0.10",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = van-data-10
# sent_uid = {uid}
1\teliodi\t_\tDET\tQ\t_\t3\tdet\t_\t_
2\tme\t_\tSCONJ\tC\t_\t3\tmark\t_\t_
3\tlibinienigi\t_\tNOUN\tN$\t_\t0\troot\t_\t_
            """
        )
        rows = list(comparison_rows([record], [gold], RELATIONS))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["comparison"] == "MATCH" for row in rows))

    def test_match_dapl_and_mark_van_014(self):
        uid = "2386b5b5-57d0-4a1f-86c2-73f67561744c"
        record = psd_record(
            "(CP-me (C me@) "
            "(IP-SUB (NP (DAPL @anitaGa) (N niwatece))))",
            "van-data,0.14",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = van-data-14
# sent_uid = {uid}
1\tme\t_\tSCONJ\tC\t_\t3\tmark\t_\t_
2\tanitaGa\t_\tDET\tDAPL\t_\t3\tdet\t_\t_
3\tniwatece\t_\tNOUN\tN\t_\t0\troot\t_\t_
            """
        )
        rows = list(comparison_rows([record], [gold], RELATIONS))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["comparison"] == "MATCH" for row in rows))

    def test_tree_sentence_absent_from_gold(self):
        uid = "39f34955-a828-47d7-808d-b3b3565b42d6"
        record = psd_record(
            "(IP-MAT (NP-SBJ (N$ LotaGa) (NP (N$ Ganioxoa))) "
            "(NP-PRD (N$ libinienaGa)))",
            "hil-data,0.3",
            uid,
        )
        rows = list(comparison_rows([record], [], RELATIONS))
        self.assertEqual(rows[0]["comparison"], "NO_GOLD_SENTENCE")

    def test_count_mismatch_rejects_alignment(self):
        uid = "39f34955-a828-47d7-808d-b3b3565b42d6"
        record = psd_record(
            "(IP-MAT (NP-SBJ (N$ LotaGa) (NP (N$ Ganioxoa))) "
            "(NP-PRD (N$ libinienaGa)))",
            "hil-data,0.3",
            uid,
        )
        gold = conllu_sentence(
            f"""
# sent_id = hil-data-3
# sent_uid = {uid}
1\tLotaGa\t_\tNOUN\tN$\t_\t0\troot\t_\t_
2\tGanioxoa\t_\tNOUN\tN$\t_\t1\tnmod:poss\t_\t_
            """
        )
        alignment = align_tokens(record, gold)
        self.assertEqual(alignment.status, "ERROR")
        self.assertIn("TOKEN_COUNT_MISMATCH", alignment.error)


class ClauseComparisonTests(unittest.TestCase):
    def test_root_zero_matches_and_serializes(self):
        from kadiweu_constituency_dependencies import write_tsv
        from compare_constituency_ud_dependencies import write_comparison
        record = psd_record("(IP-MAT (NP (N$ libiniena)))", "hil-data,0.28",
                            "fab37d81-bb9b-4e20-a8f5-3b3969ee86d1")
        gold = conllu_sentence("# sent_id = hil-data-28\n# sent_uid = "
                               + record.tree.sentence_uid + "\n"
                               "1\tlibiniena\t_\tNOUN\tN$\t_\t0\troot\t_\t_")
        rows = list(comparison_rows([record], [gold], set(DEFAULT_RELATIONS)))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["comparison"], "MATCH")
        self.assertEqual((rows[0]["head"], rows[0]["gold_head"]), ("ROOT", "ROOT"))
        for writer, data in [(write_tsv, [record]), (write_comparison, rows)]:
            output = io.StringIO()
            writer(data, output)
            row = list(csv.DictReader(io.StringIO(output.getvalue()), delimiter="\t"))[0]
            self.assertEqual((row["head_position"], row["head"]), ("0", "ROOT"))

    def test_attested_coordination_matches_reviewed_ped_049(self):
        # Source: DONE ped-gramm,0.49 and reviewed kbc_unicamp-ud-test(2).
        record = psd_record(
            "(IP-MAT (IP-MAT (NP (N$ Niwatece)) (VB iwaGadi)) "
            "(CONJP (CONJ codaa) (IP-MAT (NEG aG@) (VBU @dakake) "
            "(NP (N$ loojedi)))) (PUNC .))", "ped-gramm,0.49",
            "eeb42af3-fe5a-4b7d-97ea-b381ab589860")
        gold = conllu_sentence("""
# sent_id = ped-gramm-49
# sent_uid = eeb42af3-fe5a-4b7d-97ea-b381ab589860
1\tNiwatece\twatece\tNOUN\tN$\t_\t2\tnsubj\t_\t_
2\tiwaGadi\twaaGadi\tVERB\tVB\t_\t0\troot\t_\t_
3\tcodaa\tcodaa\tCCONJ\tCONJ\t_\t5\tcc\t_\t_
4-5\tadakake\t_\t_\t_\t_\t_\t_\t_\t_
4\taG\taG\tPART\tNEG\t_\t5\tadvmod\t_\t_
5\tdakake\takake\tVERB\tVBU\t_\t2\tconj\t_\t_
6\tloojedi\toojedi\tNOUN\tN$\t_\t5\tnsubj\t_\t_
7\t.\t.\tPUNCT\tPUNCT\t_\t2\tpunct\t_\t_
        """)
        rows = list(comparison_rows([record], [gold], set(DEFAULT_RELATIONS)))
        self.assertEqual([r["comparison"] for r in rows],
                         ["MATCH"] * 7)
        filtered = list(comparison_rows([record], [gold], {"root", "conj", "cc"}))
        self.assertEqual(len(filtered), 3)
        self.assertTrue(all(r["comparison"] == "MATCH" for r in filtered))

    def test_root_with_missing_reference(self):
        record = psd_record("(IP-MAT (NP (N$ libiniena)))", "hil-data,0.28", "missing")
        rows = list(comparison_rows([record], [], {"root"}))
        self.assertEqual(rows[0]["comparison"], "NO_GOLD_SENTENCE")
        self.assertEqual(rows[0]["head"], "ROOT")

    def test_root_reference_head_mismatch(self):
        # Artificial negative reference; not a proposed linguistic annotation.
        record = psd_record("(IP-MAT (NP (N placeholder)))", "negative", "negative")
        gold = conllu_sentence("# sent_uid = negative\n"
                               "1\tplaceholder\t_\tNOUN\tN\t_\t1\troot\t_\t_")
        self.assertEqual(list(comparison_rows([record], [gold], {"root"}))[0]["comparison"],
                         "HEAD_MISMATCH")

    def test_root_with_trace_positions_and_final_punctuation(self):
        # Mechanical perturbation: trace adds a source position, not a UD word.
        record = psd_record("(IP-MAT (NP-TRACE (-NONE- *T*-1)) (VB placeholder))",
                            "negative", "negative")
        gold = conllu_sentence("# sent_uid = negative\n"
                               "1\tplaceholder\t_\tVERB\tVB\t_\t0\troot\t_\t_\n"
                               "2\t.\t_\tPUNCT\tPUNC\t_\t1\tpunct\t_\t_")
        rows = list(comparison_rows([record], [gold], {"root"}))
        self.assertEqual(rows[0]["dependent_position"], 2)
        self.assertEqual(rows[0]["gold_dependent_id"], 1)
        self.assertEqual(rows[0]["comparison"], "MATCH")
        self.assertEqual(rows[0]["token_alignment"], "FINAL_PUNCT_IGNORED")




# Exact supplied DONE records and updated reference sentences, not generated gold.
RAISING_REFERENCE_FIXTURES = {
  "hil-data,0.5": [
    "e349508c-4d86-48b8-9918-057988755e77",
    "(\n  (IP-MAT\n    (NP-1\n      (N Etogo)\n      (CP-REL\n        (WNP-2\n          (WPRO ane@)\n        )\n        (IP-SUB\n          (NP-TRACE\n            (-NONE- *T*-2)\n          )\n          (VB @iwaGadi)\n        )\n      )\n    )\n    (NEG aG@)\n    (VBU @dakake)\n    (NP\n      (NP-GEN\n        (-NONE- *T*-1)\n      )\n      (N$ lojedi)\n    )\n  )\n  (ID hil-data,0.5)\n)",
    "# sent_id = hil-data-5\n# sent_uid = e349508c-4d86-48b8-9918-057988755e77\n# text = Etogo aneiwaGadi adakake lojedi.\n# text_orig = Etogo aneiwaGadi adakake lojedi\n# text_por_orig = A pesada canoa está barata .\n# text_por = A pesada canoa está barata.\n1\tEtogo\tetogo\tNOUN\tN\tGender=Fem|Number=Sing\t5\tdislocated\t_\tTokenRange=0:5\n2-3\taneiwaGadi\t_\t_\t_\t_\t_\t_\t_\tTokenRange=6:16\n2\tane\tane\tPRON\tWPRO\tPronType=Rel\t3\tnsubj\t_\t_\n3\tiwaGadi\twaaGadi\tVERB\tVB\tMood=Ind|Person=3|VerbForm=Fin\t1\tacl:relcl\t_\tStandardForm=iwaaGadi\n4-5\tadakake\t_\t_\t_\t_\t_\t_\t_\tTokenRange=17:24\n4\taG\taG\tPART\tNEG\tPolarity=Neg\t5\tadvmod\t_\t_\n5\tdakake\takake\tVERB\tVB\tMood=Ind|Person=3|VerbForm=Fin|Voice=Inv\t0\troot\t_\t_\n6\tlojedi\toojedi\tNOUN\tN$\tGender=Masc|Number=Sing|Person[psor]=3\t5\tnsubj\t_\tStandardForm=loojedi|SpaceAfter=No|TokenRange=25:31\n7\t.\t.\tPUNCT\tPUNCT\t_\t5\tpunct\t_\tSpaceAfter=No|TokenRange=31:32"
  ],
  "hil-data,0.6": [
    "1d10c633-e74d-4e27-ac23-6b6b2dde9647",
    "(\n  (IP-MAT\n    (NP-1\n      (N Etogo)\n      (CP-REL\n        (WNP-2\n          (WPRO ane)\n        )\n        (IP-SUB\n          (NP-TRACE\n            (-NONE- *T*-2)\n          )\n          (VB iwaGadi)\n        )\n      )\n    )\n    (NEG aG@)\n    (VBU @dakake)\n    (NP\n      (NP-GEN\n        (-NONE- *T*-1)\n      )\n      (N$ loojedi)\n    )\n  )\n  (ID hil-data,0.6)\n)",
    "# sent_id = hil-data-6\n# sent_uid = 1d10c633-e74d-4e27-ac23-6b6b2dde9647\n# text = Etogo ane iwaGadi adakake loojedi.\n# text_orig = Etogo ane iwaGadi adakake loojedi\n# text_por_orig = A canoa pesada é barata .\n# text_por = A canoa pesada é barata.\n1\tEtogo\tetogo\tNOUN\tN\tGender=Fem|Number=Sing\t5\tdislocated\t_\tTokenRange=0:5\n2\tane\tane\tPRON\tWPRO\tPronType=Rel\t3\tnsubj\t_\tTokenRange=6:9\n3\tiwaGadi\twaaGadi\tVERB\tVB\tMood=Ind|Person=3|VerbForm=Fin\t1\tacl:relcl\t_\tStandardForm=iwaaGadi|TokenRange=10:17\n4-5\tadakake\t_\t_\t_\t_\t_\t_\t_\tTokenRange=18:25\n4\taG\taG\tPART\tNEG\tPolarity=Neg\t5\tadvmod\t_\t_\n5\tdakake\takake\tVERB\tVB\tMood=Ind|Person=3|VerbForm=Fin|Voice=Inv\t0\troot\t_\t_\n6\tloojedi\toojedi\tNOUN\tN$\tGender=Masc|Number=Sing|Person[psor]=3\t5\tnsubj\t_\tSpaceAfter=No|TokenRange=26:33\n7\t.\t.\tPUNCT\tPUNCT\t_\t5\tpunct\t_\tSpaceAfter=No|TokenRange=33:34"
  ],
  "hil-data,0.9": [
    "0ca977cd-2edf-45d9-b958-068648aebef9",
    "(\n  (IP-MAT\n    (NP-1\n      (D NiGida)\n      (N niwenigi)\n    )\n    (CP-me\n      (Q eliodi)\n      (C me)\n      (IP-SUB\n        (VBU dakake)\n        (NP\n          (NP-GEN\n            (-NONE- *T*-1)\n          )\n          (N$ loojedi)\n        )\n      )\n    )\n  )\n  (ID hil-data,0.9)\n)",
    "# sent_id = hil-data-9\n# sent_uid = 0ca977cd-2edf-45d9-b958-068648aebef9\n# text = NiGida niwenigi eliodi me dakake loojedi.\n# text_orig = NiGida niwenigi eliodi me dakake loojedi\n# text_por_orig = Aquela comida é muito cara .\n# text_por = Aquela comida é muito cara.\n1\tNiGida\tniGida\tDET\tD\tGender=Masc|Number=Sing|PronType=Dem\t2\tdet\t_\tTokenRange=0:6\n2\tniwenigi\tenigi\tNOUN\tN$\tGender=Masc|Number=Sing\t5\tdislocated\t_\tTokenRange=7:15\n3\teliodi\teliodi\tADV\tQ\t_\t5\tadvmod\t_\tTokenRange=16:22\n4\tme\tme\tSCONJ\tC\t_\t5\tmark\t_\tTokenRange=23:25\n5\tdakake\takake\tVERB\tVB\tMood=Ind|Person=3|VerbForm=Fin|Voice=Inv\t0\troot\t_\tTokenRange=26:32\n6\tloojedi\tloojedi\tNOUN\tN$\tGender=Masc|Number=Sing|Person[psor]=3\t5\tnsubj\t_\tSpaceAfter=No|TokenRange=33:40\n7\t.\t.\tPUNCT\tPUNCT\t_\t5\tpunct\t_\tSpaceAfter=No|TokenRange=40:41"
  ],
  "hil-data,0.44": [
    "83fdcd4c-338f-4a9f-8545-da8539e67e9d",
    "(\n  (IP-MAT\n    (NP-1\n      (D NiGidiwa)\n      (NP\n        (N noGojedi)\n      )\n      (N$ lixagotaGaGa)\n    )\n    (NEG aG@)\n    (VBU @dakake)\n    (NP\n      (NP-GEN\n        (-NONE- *T*-1)\n      )\n      (N$ loojedi)\n    )\n  )\n  (ID hil-data,0.44)\n)",
    "# sent_id = hil-data-44\n# sent_uid = 83fdcd4c-338f-4a9f-8545-da8539e67e9d\n# text = NiGidiwa noGojedi lixagotaGaGa adakake loojedi.\n# text_orig = NiGidiwa noGojedi lixagotaGaGa adakake loojedi\n# text_por_orig = Estes peixes vermelhos estão baratos .\n# text_por = Estes peixes vermelhos estão baratos.\n1\tNiGidiwa\tniGidi\tDET\tD\tGender=Masc|Number=Plur|PronType=Dem\t3\tdet\t_\tStandardForm=niGidiwa|TokenRange=0:8\n2\tnoGojedi\tnoGojegi\tNOUN\tN\tGender=Masc|Number=Plur\t3\tnmod:poss\t_\tTokenRange=9:17\n3\tlixagotaGaGa\tixagodi\tNOUN\tN$\tNumber=Plur\t5\tdislocated\t_\tTokenRange=18:30\n4-5\tadakake\t_\t_\t_\t_\t_\t_\t_\tTokenRange=31:38\n4\taG\taG\tPART\tNEG\tPolarity=Neg\t5\tadvmod\t_\t_\n5\tdakake\takake\tVERB\tVBU\tMood=Ind|Person=3|VerbForm=Fin|Voice=Inv\t0\troot\t_\t_\n6\tloojedi\toojedi\tNOUN\tN$\tGender=Masc|Number=Sing|Person[psor]=3\t5\tnsubj\t_\tSpaceAfter=No|TokenRange=39:46\n7\t.\t.\tPUNCT\tPUNCT\t_\t5\tpunct\t_\tSpaceAfter=No|TokenRange=46:47"
  ],
  "van-data,0.12": [
    "a1e15803-1e5e-481f-8137-a84beac6cbcc",
    "(\n  (IP-MAT\n    (NP-1\n      (D niGida)\n      (N niwenigi)\n    )\n    (CP-me\n      (Q daGaxa)\n      (C me)\n      (IP-SUB\n        (VBU dakake)\n        (NP\n          (NP-GEN\n            (-NONE- *T*-1)\n          )\n          (N$ loojedi)\n        )\n      )\n    )\n  )\n  (ID van-data,0.12)\n)",
    "# sent_id = van-data-12\n# sent_uid = a1e15803-1e5e-481f-8137-a84beac6cbcc\n# text = niGida niwenigi daGaxa me dakake loojedi.\n# text_orig = niGida niwenigi daGaxa me dakake loojedi\n# text_por_orig = aquela comida é muito cara\n# text_por = aquela comida é muito cara.\n1\tniGida\tniGida\tDET\tD\tGender=Masc|Number=Sing|PronType=Dem\t2\tdet\t_\tTokenRange=0:6\n2\tniwenigi\twenigi\tNOUN\tN$\tGender=Masc|Number=Sing\t5\tdislocated\t_\tTokenRange=7:15\n3\tdaGaxa\tdaGaxa\tADV\tQ\t_\t5\tadvmod\t_\tTokenRange=16:22\n4\tme\tme\tSCONJ\tC\t_\t5\tmark\t_\tTokenRange=23:25\n5\tdakake\takake\tVERB\tVB\tMood=Ind|Person=3|VerbForm=Fin|Voice=Inv\t0\troot\t_\tTokenRange=26:32\n6\tloojedi\toojedi\tNOUN\tN$\tGender=Masc|Number=Sing|Person[psor]=3\t5\tnsubj\t_\tSpaceAfter=No|TokenRange=33:40\n7\t.\t.\tPUNCT\tPUNCT\t_\t5\tpunct\t_\tSpaceAfter=No|TokenRange=40:41"
  ],
  "van-data,0.47": [
    "fad6e8d3-1e9f-451c-aaa7-fd28aecfd967",
    "(\n  (IP-MAT\n    (NP-1\n      (D idiwa)\n      (NP\n        (N noGojedi)\n      )\n      (N$ lixagotaGaGa)\n    )\n    (NEG aG@)\n    (VBU @dakake)\n    (NP\n      (NP-GEN\n        (-NONE- *T*-1)\n      )\n      (N$ loojedi)\n    )\n  )\n  (ID van-data,0.47)\n)",
    "# sent_id = van-data-47\n# sent_uid = fad6e8d3-1e9f-451c-aaa7-fd28aecfd967\n# text = idiwa noGojedi lixagotaGaGa adakake loojedi.\n# text_orig = idiwa noGojedi lixagotaGaGa adakake loojedi\n# text_por_orig = estes peixes vermelhos estão baratos\n# text_por = estes peixes vermelhos estão baratos.\n1\tidiwa\tidi\tDET\tD\tGender=Masc|Number=Plur|PronType=Dem\t3\tdet\t_\tTokenRange=0:5\n2\tnoGojedi\tnoGojegi\tNOUN\tN\tGender=Masc|Number=Plur\t3\tnmod:poss\t_\tTokenRange=6:14\n3\tlixagotaGaGa\tixagodi\tNOUN\tN$\tNumber=Plur\t5\tdislocated\t_\tTokenRange=15:27\n4-5\tadakake\t_\t_\t_\t_\t_\t_\t_\tTokenRange=28:35\n4\taG\taG\tPART\tNEG\tPolarity=Neg\t5\tadvmod\t_\t_\n5\tdakake\takake\tVERB\tVBU\tMood=Ind|Person=3|VerbForm=Fin|Voice=Inv\t0\troot\t_\t_\n6\tloojedi\toojedi\tNOUN\tN$\tGender=Masc|Number=Sing|Person[psor]=3\t5\tnsubj\t_\tSpaceAfter=No|TokenRange=36:43\n7\t.\t.\tPUNCT\tPUNCT\t_\t6\tpunct\t_\tSpaceAfter=No|TokenRange=43:44"
  ]
}

class RaisingReferenceTests(unittest.TestCase):
    def test_all_six_reviewed_raising_chains(self):
        from kadiweu_constituency_dependencies import infer_dependencies
        for sent_id, (uid, raw, gold_text) in RAISING_REFERENCE_FIXTURES.items():
            with self.subTest(sentence=sent_id):
                tree, csid = tree_from_psd_record(raw, metadata={"uid": uid, "status": "DONE"})
                record = PsdRecord(tree, {"uid": uid, "status": "DONE"}, csid)
                assignments = infer_dependencies(tree)
                raised = [a for a in assignments if a.rule == "possessor-raising-trace"]
                self.assertEqual(len(raised), 1)
                rows = list(comparison_rows([record], [conllu_sentence(gold_text)], {"dislocated", "nsubj"}))
                self.assertTrue(rows)
                self.assertTrue(all(r["comparison"] == "MATCH" for r in rows), rows)


if __name__ == "__main__":
    unittest.main()
