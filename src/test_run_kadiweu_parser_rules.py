import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).with_name("run_kadiweu_parser_rules.py")
SPEC = importlib.util.spec_from_file_location("runner", RUNNER)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def record(sentence_id, status, tree):
    return (
        f"/*\nstatus = {status}\n*/\n"
        f"( {tree} (ID {sentence_id}) )\n"
    )


class TransitionComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        path = self.directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_reports_every_changed_sentence_and_omits_unchanged(self):
        reference = self.write(
            "reference.psd",
            record("hil-data,0.1", "DONE", "(IP-MAT (N a))")
            + record("hil-data,0.2", "DONE", "(IP-MAT (NP-1 (N b)) (NP-TRACE *T*-1))")
            + record("van-data,0.3", "REVIEW", "(CP (N c))"),
        )
        accepted = self.write(
            "accepted.psd",
            record("hil-data,0.1", "DONE", "(IP-MAT (N a))")
            + record("hil-data,0.2", "DONE", "(IP-MAT (NP-7 (N b)) (NP-TRACE *T*-7))")
            + record("van-data,0.3", "REVIEW", "(IP-MAT (N c))"),
        )
        candidate = self.write(
            "candidate.psd",
            record("hil-data,0.1", "DONE", "(IP-MAT (N a))")
            + record("hil-data,0.2", "DONE", "(IP-MAT (NP-9 (N b)) (NP-TRACE (-NONE- *T*-9)))")
            + record("van-data,0.3", "REVIEW", "(CP (N c))"),
        )

        results = runner.classify_transitions(accepted, candidate, reference)

        self.assertEqual(
            [item.sentence_id for item in results],
            ["hil-data,0.2", "van-data,0.3"],
        )
        trace, improvement = results
        self.assertEqual(trace.output_change_classification, runner.TRACE_EQUIVALENT)
        self.assertEqual(trace.transition, "TRACE_EQUIVALENT -> TRACE_EQUIVALENT")
        self.assertEqual(
            improvement.transition,
            "STRUCTURAL_DIFFERENCE -> EXACT_MATCH",
        )
        self.assertIn("provisional until manual adjudication", improvement.details)

    def test_reports_missing_candidate_sentence(self):
        reference = self.write(
            "reference.psd",
            record("ped-gramm,0.1", "DONE", "(IP-MAT (N a))"),
        )
        accepted = self.write(
            "accepted.psd",
            record("ped-gramm,0.1", "DONE", "(IP-MAT (N a))"),
        )
        candidate = self.write("candidate.psd", "")

        results = runner.classify_transitions(accepted, candidate, reference)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].sentence_id, "ped-gramm,0.1")
        self.assertEqual(results[0].candidate_classification, runner.STRUCTURAL_DIFFERENCE)
        self.assertEqual(results[0].output_change_classification, runner.STRUCTURAL_DIFFERENCE)

    def test_writes_stable_tsv_schema(self):
        reference = self.write(
            "reference.psd",
            record("hil-data,0.1", "DONE", "(IP-MAT (N a))"),
        )
        accepted = self.write(
            "accepted.psd",
            record("hil-data,0.1", "DONE", "(IP-MAT (N x))"),
        )
        candidate = self.write(
            "candidate.psd",
            record("hil-data,0.1", "DONE", "(IP-MAT (N a))"),
        )
        report = self.directory / "transitions.tsv"

        runner.compare_accepted_to_candidate(accepted, candidate, reference, report)

        with report.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["accepted_classification"], runner.STRUCTURAL_DIFFERENCE)
        self.assertEqual(rows[0]["candidate_classification"], runner.EXACT_MATCH)
        self.assertEqual(rows[0]["output_change_classification"], runner.STRUCTURAL_DIFFERENCE)


if __name__ == "__main__":
    unittest.main()
