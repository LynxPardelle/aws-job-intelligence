import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from pypdf import PdfReader
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.application_package import prepare_application
from aji.connectors import parse_feed
from aji.matcher import SearchPolicy, match_job


FIXTURES = Path(__file__).parent / "fixtures"


def inputs():
    feed = json.loads((FIXTURES / "ashby.json").read_text("utf-8"))
    job = parse_feed("ashby", "acmeexample", "Acme Example", feed, "2026-10-13T14:00:00Z")[0]
    job = replace(job, mexico_eligibility="eligible")
    policy = SearchPolicy("fictional", ("python", "data"), ("senior",), ("remote",), 75000, "USD", 70)
    match = match_job(job, policy, "2026-10-13T15:00:00Z")
    profile = json.loads((FIXTURES / "verified_profile.json").read_text("utf-8"))
    return job, match, profile


class PackageTests(unittest.TestCase):
    def test_dry_run_writes_only_verified_claims_and_no_submission_record(self):
        job, match, profile = inputs()
        with tempfile.TemporaryDirectory() as directory:
            output = prepare_application(job, match, profile, Path(directory))
            names = {path.name for path in output.iterdir()}
            self.assertIn("resume-tailored.pdf", names)
            self.assertIn("evidence-map.json", names)
            self.assertNotIn("submission-record.json", names)
            resume = (output / "resume-tailored.md").read_text("utf-8")
            self.assertIn("Built Python data pipelines for internal analytics.", resume)
            self.assertNotIn("Maintained Angular components", resume)
            mapping = json.loads((output / "evidence-map.json").read_text("utf-8"))
            self.assertEqual([entry["claim_id"] for entry in mapping["claims"]], ["claim-python-1"])
            self.assertTrue((output / "resume-tailored.pdf").read_bytes().startswith(b"%PDF"))
            pdf_text = "\n".join(page.extract_text() for page in PdfReader(output / "resume-tailored.pdf").pages)
            self.assertIn("Built Python data pipelines for internal analytics.", pdf_text)

    def test_unapproved_profile_or_unverified_claim_is_rejected(self):
        job, match, profile = inputs()
        with tempfile.TemporaryDirectory() as directory:
            profile["approved_by_holder"] = False
            with self.assertRaises(ValueError):
                prepare_application(job, match, profile, Path(directory))
            profile["approved_by_holder"] = True
            profile["claims"][0]["evidence"]["reuse_approved"] = False
            with self.assertRaises(ValueError):
                prepare_application(job, match, profile, Path(directory))

    def test_unknown_eligibility_never_produces_package(self):
        job, _, profile = inputs()
        job = replace(job, mexico_eligibility="unknown")
        policy = SearchPolicy("fictional", ("python", "data"), ("senior",), ("remote",), 75000, "USD", 70)
        match = match_job(job, policy, "2026-10-13T15:00:00Z")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                prepare_application(job, match, profile, Path(directory))

    def test_pdf_failure_leaves_no_partial_package_and_retry_succeeds(self):
        job, match, profile = inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("aji.application_package._write_pdf", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    prepare_application(job, match, profile, root)
            self.assertEqual(list(root.rglob("resume-tailored.md")), [])
            self.assertEqual(list(root.rglob("resume-tailored.pdf")), [])
            self.assertTrue(prepare_application(job, match, profile, root).exists())

    def test_large_approved_profile_produces_a_reviewable_resume(self):
        job, match, profile = inputs()
        profile["claims"] = [
            {
                "claim_id": f"claim-{index}",
                "text": f"Verified Python achievement {index}.",
                "keywords": ["python"],
                "evidence": {
                    "source_document": "fixture.pdf", "reference": f"page {index}",
                    "verified_at": "2026-10-13", "reuse_approved": True,
                },
            }
            for index in range(20)
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = prepare_application(job, match, profile, Path(directory))
            mapping = json.loads((output / "evidence-map.json").read_text("utf-8"))
            resume = (output / "resume-tailored.md").read_text("utf-8")
            letter = (output / "cover-letter.md").read_text("utf-8")
            self.assertEqual(len(mapping["claims"]), 12)
            self.assertEqual(resume.count("Verified Python achievement"), 12)
            self.assertEqual(letter.count("Verified Python achievement"), 3)
            self.assertNotIn("Verified Python achievement 19.", resume)

    def test_approved_contact_appears_in_both_resume_formats(self):
        job, match, profile = inputs()
        profile["contact"] = {
            "email": "candidate@example.invalid",
            "phone": "+52 55 0000 0000",
            "location": "Mexico City, Mexico",
            "links": ["https://example.invalid/portfolio"],
        }
        with tempfile.TemporaryDirectory() as directory:
            output = prepare_application(job, match, profile, Path(directory))
            resume = (output / "resume-tailored.md").read_text("utf-8")
            pdf_text = "\n".join(page.extract_text() for page in PdfReader(output / "resume-tailored.pdf").pages)
            for value in ("candidate@example.invalid", "+52 55 0000 0000", "Mexico City, Mexico",
                          "https://example.invalid/portfolio"):
                self.assertIn(value, resume)
                self.assertIn(value, pdf_text)

    def test_package_includes_quoted_requirement_matrix_with_unverified_gaps(self):
        job, match, profile = inputs()
        job = replace(job, description="Required: five years of Python experience. "
                     "Nice to have: Kubernetes.")
        with tempfile.TemporaryDirectory() as directory:
            output = prepare_application(job, match, profile, Path(directory))
            matrix = json.loads((output / "requirements-evidence.json").read_text("utf-8"))
            self.assertEqual(matrix[0]["status"], "related_evidence")
            self.assertIn("five years", matrix[0]["quote"])
            self.assertEqual(matrix[1]["status"], "unverified")
            self.assertNotIn("meets_requirement", str(matrix))


if __name__ == "__main__":
    unittest.main()
