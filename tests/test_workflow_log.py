from pathlib import Path
import tempfile
import unittest

from src.parser import build_result
from src.file_handler import read_text_files_from_folder
from src.workflow_log import (
    apply_routing_review_flag,
    append_run_log,
    assess_routing_confidence,
    build_document_hash,
    build_processing_id,
    find_duplicate_hashes,
)


class WorkflowLogTests(unittest.TestCase):
    def test_duplicate_hashes_detect_repeated_documents(self):
        documents = [
            ("first.txt", "The maintenance team reported a fault."),
            ("second.txt", "The maintenance team reported a fault."),
            ("third.txt", "The meeting discussed a process improvement."),
        ]

        duplicate_hashes = find_duplicate_hashes(documents)

        self.assertIn(build_document_hash(documents[0][1]), duplicate_hashes)
        self.assertNotIn(build_document_hash(documents[2][1]), duplicate_hashes)

    def test_routing_confidence_and_run_log(self):
        text = (
            "The maintenance team reported repeated faults in the conveyor sensor system. "
            "Engineering should review the fault logs before the next production cycle."
        )
        result = build_result(text, summary=text)
        result.update(
            {
                "file_name": "maintenance.txt",
                "document_hash": build_document_hash(text),
                "processing_id": build_processing_id("maintenance.txt", build_document_hash(text)),
                "duplicate": False,
                "routing": assess_routing_confidence(result),
                "preferred_model": "T5",
                "processing_latency_ms": 12.3,
            }
        )

        with tempfile.TemporaryDirectory() as directory:
            log_path = append_run_log([result], Path(directory) / "triage_run_log.csv")

            content = log_path.read_text(encoding="utf-8")
            self.assertIn("maintenance.txt", content)
            self.assertIn("routing_confidence", content)
            self.assertEqual(result["routing"]["overall"], "High")

    def test_low_routing_confidence_adds_review_reason(self):
        result = build_result("This is a short unclear note with no owner.", summary="Unclear note.")
        result["routing"] = assess_routing_confidence(result)

        apply_routing_review_flag(result)

        self.assertEqual(result["routing"]["overall"], "Low")
        self.assertTrue(result["human_review"]["review_required"])
        self.assertIn("Low routing confidence", result["human_review"]["reasons"])

    def test_batch_reader_accepts_text_markdown_and_email_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "ticket.txt").write_text("Maintenance should inspect the unit.", encoding="utf-8")
            (base / "note.md").write_text("## Meeting\nThe team should prepare a proposal.", encoding="utf-8")
            (base / "message.eml").write_text("Subject: Update\nPlease review by Friday.", encoding="utf-8")
            (base / "ignore.pdf").write_text("not supported here", encoding="utf-8")

            documents = read_text_files_from_folder(base)

            names = {file_name for file_name, _text in documents}
            self.assertEqual(names, {"ticket.txt", "note.md", "message.eml"})


if __name__ == "__main__":
    unittest.main()
