#!/usr/bin/env python3
"""Tests for gold/constituency dependency comparison."""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from kadiweu_constituency import PsdRecord, tree_from_psd_record
from compare_constituency_ud_dependencies import (
    align_tokens,
    comparison_rows,
    iter_conllu_sentences,
)


RELATIONS = {"nmod:poss", "det", "mark"}


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
        self.assertEqual(len(rows), 1)
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
        self.assertEqual(len(rows), 1)
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


if __name__ == "__main__":
    unittest.main()
