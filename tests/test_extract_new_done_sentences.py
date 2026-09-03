"""Synthetic English fixtures test selection, not Kadiweu linguistic rules."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import extract_new_done_sentences as extractor


def block(uid, sid="sample", extra=""):
    return "# sent_id = {}\n# sent_uid = {}\n{}1\tplaceholder\t_\tNOUN\tN\t_\t0\troot\t_\t_\n".format(sid, uid, extra)


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reference = self.write("gold.conllu", block("old", "old"))
        self.draft = self.write("draft.conllu", block("old", "renumbered") + "\n" + block("new") + "\n" + block("review", "review"))
        self.source = self.write("source.json", json.dumps({"pages": [{"sentences": [
            {"uid": "old", "status": "DONE"}, {"uid": "new", "status": "DONE"},
            {"uid": "review", "status": "REVIEW"}]}]}))
        self.output = self.root / "review/new.conllu"

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def args(self):
        return ["--drafts", str(self.draft), "--reference", str(self.reference),
                "--json", str(self.source), "--output", str(self.output)]

    def run_cli(self, extra=None):
        with contextlib.redirect_stderr(io.StringIO()):
            return extractor.main(self.args() + (extra or []))

    def test_uid_membership_and_review_exclusion(self):
        selected, counts = extractor.select_sentences([self.draft], self.reference, [self.source])
        self.assertEqual(selected, [block("new")])
        self.assertEqual(counts["already_in_reference"], 1)
        self.assertEqual(counts["not_done"], 1)

    def test_copy_verbatim_comments_mwt_and_empty_nodes(self):
        content = block("new", extra="# text = placeholder\n# note = preserve me\n") + "2-3\tcompound\t_\t_\t_\t_\t_\t_\t_\t_\n2.1\tempty\t_\t_\t_\t_\t_\t_\t_\t_\n"
        self.draft.write_text(content, encoding="utf-8")
        self.assertEqual(self.run_cli(), 0)
        self.assertEqual(self.output.read_text(), content + "\n")

    def test_never_overwrite_review_file(self):
        self.assertEqual(self.run_cli(), 0)
        self.output.write_text("manually revised")
        self.assertEqual(self.run_cli(), 1)
        self.assertEqual(self.output.read_text(), "manually revised")

    def test_dry_run_and_inputs_unchanged(self):
        before = [p.read_bytes() for p in (self.draft, self.reference, self.source)]
        self.assertEqual(self.run_cli(["--dry-run"]), 0)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.run_cli(), 0)
        self.assertEqual(before, [p.read_bytes() for p in (self.draft, self.reference, self.source)])

    def test_duplicate_draft_uid_fails(self):
        self.draft.write_text(block("new") + "\n" + block("new"))
        self.assertEqual(self.run_cli(), 1)
        self.assertFalse(self.output.exists())

    def test_missing_reference_uid_fails(self):
        self.reference.write_text("# sent_id = old\n1\tword\n")
        self.assertEqual(self.run_cli(), 1)

    def test_sentence_id_collision_fails(self):
        self.draft.write_text(block("new", "old"))
        self.assertEqual(self.run_cli(), 1)

    def test_unknown_source_uid_excluded(self):
        self.draft.write_text(block("unknown"))
        selected, counts = extractor.select_sentences([self.draft], self.reference, [self.source])
        self.assertEqual(selected, [])
        self.assertEqual(counts["missing_source_uid"], 1)

    def test_duplicate_json_uid_fails(self):
        with self.assertRaises(ValueError):
            extractor.source_statuses([self.source, self.source])

    def test_reference_cannot_be_output(self):
        self.output = self.reference
        self.assertEqual(self.run_cli(), 1)

    def test_multiple_drafts_preserve_order(self):
        second = self.write("second.conllu", block("old", "old"))
        self.draft.write_text(block("new"))
        selected, _ = extractor.select_sentences([self.draft, second], self.reference, [self.source])
        self.assertEqual(selected, [block("new")])
