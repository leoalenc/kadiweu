"""Integration guarantees over all three committed source JSON documents."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import types
import unittest
from unittest.mock import patch

import kadiweu_json_to_conllu as converter
import kadiweu_prediction_bridge as bridge
from kadiweu_constituency_dependencies import DependencyAssignment

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "167801d60b5e2875dcebc08bb3523fd47539d4d5"


def convert(sentence, mode="done"):
    return converter.convert_sentence(sentence, 1, "test-", "document", "commit",
                                      "fixed timestamp", dependency_predictions=mode)


def nondependency_fields(output):
    return [line if line.startswith("#") else
            tuple(v for i, v in enumerate(line.split("\t")) if i not in (6, 7))
            for line in output.splitlines()]


class PredictionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sentences = [(name, i, s) for name in ("ped-gramm", "hil-data", "van-data")
                         for page in json.loads((ROOT / "data" / (name + ".json")).read_text())["pages"]
                         for i, s in enumerate(page["sentences"], 1)]

    def setUp(self):
        self.log = io.StringIO()
        self.stderr = contextlib.redirect_stderr(self.log)
        self.stderr.__enter__()
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def test_all_sources_preserve_other_fields_and_input(self):
        for name, i, sentence in self.sentences:
            with self.subTest(source=name, sentence=i):
                original = copy.deepcopy(sentence)
                legacy = convert(sentence, "off")
                updated = convert(sentence)
                self.assertEqual(nondependency_fields(legacy), nondependency_fields(updated))
                self.assertEqual(original, sentence)
                if sentence.get("status") != "DONE":
                    self.assertEqual(legacy, updated)
        self.assertNotIn("rejected", self.log.getvalue())
        self.assertNotIn("restored", self.log.getvalue())

    def test_off_matches_original_committed_converter(self):
        result = subprocess.run(["git", "show", BASELINE + ":src/kadiweu_json_to_conllu.py"],
                                cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            self.skipTest("baseline commit unavailable; fetch it for byte-for-byte regression test")
        baseline = types.ModuleType("baseline_converter")
        baseline.__file__ = converter.__file__
        exec(compile(result.stdout, converter.__file__, "exec"), baseline.__dict__)
        for name, i, sentence in self.sentences:
            with self.subTest(source=name, sentence=i):
                expected = baseline.convert_sentence(sentence, 1, "test-", "document", "commit", "fixed timestamp")
                self.assertEqual(expected, convert(sentence, "off"))

    def test_no_predictions_preserves_legacy(self):
        with patch.object(bridge, "predict", return_value=[]):
            for _, _, sentence in self.sentences:
                self.assertEqual(convert(sentence, "off"), convert(sentence))

    def test_all_accepted_predictions_survive_serialization(self):
        align = bridge.align_predictions
        for name, i, sentence in self.sentences:
            captured = []
            def capture(assignments, tokens):
                result = align(assignments, tokens)
                captured.append(result)
                return result
            with self.subTest(source=name, sentence=i), patch.object(bridge, "align_predictions", side_effect=capture):
                output = convert(sentence)
                rows = {int(c[0]): c for line in output.splitlines()
                        if not line.startswith("#") for c in [line.split("\t")]
                        if c[0].isdigit()}
                for mapping in captured:
                    for dep, (head, relation, _) in mapping.items():
                        self.assertEqual((int(rows[dep][6]), rows[dep][7]), (head, relation))
                if captured:
                    tokens = [types.SimpleNamespace(id=i, head=int(r[6]), deprel=r[7]) for i, r in rows.items()]
                    self.assertIsNone(bridge.graph_problem(tokens))

    def test_graph_failure_rolls_back_atomically(self):
        sentence = next(s for _, _, s in self.sentences if s.get("status") == "DONE")
        with patch.object(bridge, "graph_problem", return_value="test cycle"):
            self.assertEqual(convert(sentence, "off"), convert(sentence))
        self.assertIn("restored to legacy", self.log.getvalue())

    def test_bad_tree_falls_back_with_diagnostic(self):
        sentence = next(s for _, _, s in self.sentences if s.get("status") == "DONE")
        with patch.object(bridge, "predict", side_effect=ValueError("bad tree")):
            self.assertEqual(convert(sentence, "off"), convert(sentence))
        self.assertIn("tree rejected", self.log.getvalue())

    def test_missing_prediction_token_falls_back(self):
        sentence = next(s for _, _, s in self.sentences if s.get("status") == "DONE")
        with patch.object(bridge, "predict", return_value=[DependencyAssignment(99999, 0, "root", "test")]):
            self.assertEqual(convert(sentence, "off"), convert(sentence))
        self.assertIn("alignment rejected", self.log.getvalue())

    def test_cli_default_and_legacy_switch(self):
        self.assertEqual(converter.parse_args([]).dependency_predictions, "done")
        self.assertEqual(converter.parse_args(["--dependency-predictions", "off"]).dependency_predictions, "off")


class BridgeTests(unittest.TestCase):
    def token(self, source, tid, head=0, relation="dep", locked=False):
        token = converter.DraftToken(source, "placeholder", "placeholder", "NOUN", "N", "_", head=head, deprel=relation)
        token.id = tid
        token.locked_deprel = locked
        return token

    def test_trace_gap_maps_positions_to_word_ids(self):
        tokens = [self.token(1, 1), self.token(3, 2)]
        mapped = bridge.align_predictions([DependencyAssignment(3, 1, "obj", "test")], tokens)
        self.assertEqual(mapped[2], (1, "obj", "test"))

    def test_missing_head_and_duplicate_positions_rejected(self):
        for tokens in ([self.token(1, 1)], [self.token(1, 1), self.token(1, 2)]):
            with self.assertRaises(ValueError):
                bridge.align_predictions([DependencyAssignment(1, 3, "obj", "test")], tokens)

    def test_per_predicate_cleanup_preserves_locked_subjects(self):
        tokens = [self.token(1, 1, 2, "nsubj", True), self.token(3, 3, 4, "nsubj", True),
                  self.token(5, 5, 2, "nsubj")]
        bridge.demote_unlocked_duplicates(tokens)
        self.assertEqual([t.deprel for t in tokens], ["nsubj", "nsubj", "dep"])

    def test_cycle_and_root_validation(self):
        self.assertIsNotNone(bridge.graph_problem([self.token(1, 1, 2), self.token(2, 2, 1)]))
        self.assertIsNone(bridge.graph_problem([self.token(1, 1, 0, "root"), self.token(2, 2, 1)]))
