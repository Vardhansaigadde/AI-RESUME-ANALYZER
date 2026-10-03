"""Integration tests for the resume analysis and role suggestion endpoints.

Tests:
1. Valid request with PDF resume and job description.
2. Valid request with DOCX resume and job description.
3. Missing resume file returns clear HTTP 400 error.
4. Wrong file type (non-PDF/DOCX) returns clear HTTP 400 error.
5. Empty job description text returns clear HTTP 400 error.
6. Oversized resume file (>5MB) returns clear HTTP 400 error.
7. Missing model artifact returns clear HTTP 503 error without stack trace.
8. Standalone POST /api/suggest-roles with PDF resume file.
9. Standalone POST /api/suggest-roles with DOCX resume file.
"""

import io
from pathlib import Path
import unittest
from unittest.mock import patch

import docx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def build_sample_pdf(text_lines: list[str]) -> bytes:
    """Generate a clean, valid PDF 1.4 byte payload containing the specified text lines."""
    stream_lines = ["BT", "/F1 10 Tf", "14 TL", "50 750 Td"]
    for line in text_lines:
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"({safe_line}) '")
    stream_lines.append("ET")
    content = "\n".join(stream_lines).encode("latin-1", "replace")

    pdf = (
        f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(content)} >>
stream
""".encode("latin-1")
        + content
        + """\nendstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000224 00000 n 
0000000300 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
400
%%EOF""".encode("latin-1")
    )
    return pdf


def build_sample_docx(text_lines: list[str]) -> bytes:
    """Generate a valid DOCX byte payload containing the specified text lines."""
    doc = docx.Document()
    for line in text_lines:
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestAnalyzeEndpoint(unittest.TestCase):
    """Test suite for /api/analyze and /api/suggest-roles multipart and error flows."""

    def setUp(self):
        self.sample_text_lines = [
            "Senior Software Engineer Resume",
            "Summary: 6 years experience developing scalable microservices and backend systems.",
            "Technical Skills: Python, SQL, Docker, AWS, React, PostgreSQL, REST APIs.",
            "Projects: Architected an automated real-time ingestion pipeline handling 100 million events.",
            "Experience: Optimized database queries saving 35% server load across 12 distributed clusters.",
        ]
        self.valid_pdf_bytes = build_sample_pdf(self.sample_text_lines)
        self.valid_docx_bytes = build_sample_docx(self.sample_text_lines)
        self.sample_job_desc = (
            "We are seeking a Senior Python Engineer with expertise in Python, SQL, Docker, and AWS. "
            "Experience building scalable backend APIs and database optimization is required."
        )

    def test_valid_pdf_request(self):
        """POST /api/analyze with valid PDF and job description returns full 200 AnalyzeResponse."""
        files = {"resume_file": ("resume.pdf", self.valid_pdf_bytes, "application/pdf")}
        data = {"job_description": self.sample_job_desc}

        response = client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        # Verify required AnalyzeResponse fields
        self.assertIn("match_score", payload)
        self.assertIn("matched_skills", payload)
        self.assertIn("missing_skills", payload)
        self.assertIn("features", payload)
        self.assertIn("resume_skills_count", payload)
        self.assertIn("required_skills_count", payload)
        self.assertIn("suggested_roles", payload)
        self.assertIn("suggestions", payload)
        self.assertIn("confidence", payload)
        self.assertIn(payload["confidence"], ["high", "low"])

        self.assertGreaterEqual(payload["match_score"], 0.0)
        self.assertLessEqual(payload["match_score"], 100.0)
        self.assertEqual(len(payload["suggested_roles"]), 3)
        self.assertIsInstance(payload["suggestions"], list)
        self.assertLessEqual(len(payload["suggestions"]), 5)

    def test_valid_docx_request(self):
        """POST /api/analyze with valid DOCX and job description returns full 200 AnalyzeResponse."""
        files = {
            "resume_file": (
                "resume.docx",
                self.valid_docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        data = {"job_description": self.sample_job_desc}

        response = client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("match_score", payload)
        self.assertEqual(len(payload["suggested_roles"]), 3)
        self.assertIsInstance(payload["suggestions"], list)

    def test_missing_file(self):
        """POST /api/analyze without a file returns 400 error."""
        data = {"job_description": self.sample_job_desc}

        response = client.post("/api/analyze", data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("resume file is required", response.json()["detail"].lower())

    def test_wrong_file_type(self):
        """POST /api/analyze with non-PDF/DOCX file returns 400 error."""
        files = {"resume_file": ("resume.txt", b"Plain text resume content", "text/plain")}
        data = {"job_description": self.sample_job_desc}

        response = client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"].lower()
        self.assertIn("invalid file type", detail)
        self.assertIn(".txt", detail)

    def test_empty_job_description(self):
        """POST /api/analyze with empty job_description text returns 400 error."""
        files = {"resume_file": ("resume.pdf", self.valid_pdf_bytes, "application/pdf")}
        data = {"job_description": "   "}

        response = client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("job_description text must not be empty", response.json()["detail"])

    def test_oversized_file(self):
        """POST /api/analyze with file exceeding 5MB returns 400 error."""
        # 5MB + 1024 bytes
        oversized_bytes = b"0" * (5 * 1024 * 1024 + 1024)
        files = {"resume_file": ("oversized.pdf", oversized_bytes, "application/pdf")}
        data = {"job_description": self.sample_job_desc}

        response = client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("5mb limit", response.json()["detail"].lower())

    def test_invalid_pdf_magic_bytes(self):
        """POST /api/analyze with non-PDF bytes in a .pdf file fails magic-byte check with 400."""
        files = {"resume_file": ("malicious.pdf", b"MZ\x90\x00\x03\x00\x00\x00DOS_HEADER", "application/pdf")}
        data = {"job_description": self.sample_job_desc}
        response = client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("file header does not match pdf format", response.json()["detail"].lower())

    def test_invalid_docx_magic_bytes(self):
        """POST /api/analyze with non-DOCX bytes in a .docx file fails magic-byte check with 400."""
        files = {
            "resume_file": (
                "malicious.docx",
                b"<script>alert(1)</script>",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        data = {"job_description": self.sample_job_desc}
        response = client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("file header does not match docx format", response.json()["detail"].lower())

    def test_corrupted_document_sanitized_error(self):
        """POST /api/analyze with corrupted file returns a clean 400 without leaking raw trace."""
        # Starts with %PDF- but is completely truncated/corrupted
        corrupted_pdf = b"%PDF-1.4\n%%EOF_CORRUPTED_STREAM_DATA"
        files = {"resume_file": ("corrupted.pdf", corrupted_pdf, "application/pdf")}
        data = {"job_description": self.sample_job_desc}
        response = client.post("/api/analyze", files=files, data=data)
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertIn("could not be read", detail.lower())
        self.assertNotIn("Traceback", detail)

    def test_missing_model_file(self):
        """POST /api/analyze returns 503 clear error message when a model file is missing."""
        files = {"resume_file": ("resume.pdf", self.valid_pdf_bytes, "application/pdf")}
        data = {"job_description": self.sample_job_desc}

        with patch(
            "app.routers.analyze.REQUIRED_ANALYZE_MODELS",
            [("match_scorer.joblib", Path("models/non_existent_model.joblib"))],
        ):
            response = client.post("/api/analyze", files=files, data=data)
            self.assertEqual(response.status_code, 503)
            self.assertIn("missing from models", response.json()["detail"].lower())
            self.assertIn("match_scorer.joblib", response.json()["detail"])

    def test_suggest_roles_standalone_pdf(self):
        """POST /api/suggest-roles works standalone with just a PDF resume file."""
        files = {"resume_file": ("resume.pdf", self.valid_pdf_bytes, "application/pdf")}
        response = client.post("/api/suggest-roles", files=files)
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("suggested_roles", payload)
        self.assertIn("confidence", payload)
        self.assertIn(payload["confidence"], ["high", "low"])
        self.assertEqual(len(payload["suggested_roles"]), 3)
        self.assertIn("role", payload["suggested_roles"][0])
        self.assertIn("match_percent", payload["suggested_roles"][0])

    def test_suggest_roles_standalone_docx(self):
        """POST /api/suggest-roles works standalone with just a DOCX resume file."""
        files = {
            "resume_file": (
                "resume.docx",
                self.valid_docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        response = client.post("/api/suggest-roles", files=files)
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("suggested_roles", payload)
        self.assertEqual(len(payload["suggested_roles"]), 3)

    def test_suggest_roles_missing_file_and_text(self):
        """POST /api/suggest-roles without file or text returns 400 error."""
        response = client.post("/api/suggest-roles", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("resume file is required", response.json()["detail"].lower())


class TestRequestHardening(unittest.TestCase):
    """Body-size limit, input validation, CORS and response-shape guarantees."""

    def test_request_body_over_limit_returns_413(self):
        """Bodies above the global cap are rejected before the endpoint runs."""
        huge = b"%PDF-" + b"0" * (7 * 1024 * 1024)
        response = client.post(
            "/api/analyze",
            files={"resume_file": ("big.pdf", huge, "application/pdf")},
            data={"job_description": "Python developer"},
        )
        self.assertEqual(response.status_code, 413)
        self.assertIn("5mb", response.json()["detail"].lower())

    def test_rejections_keep_cors_headers(self):
        """413s are produced inside CORS, so browsers can read the error message."""
        response = client.post(
            "/api/analyze",
            files={"resume_file": ("big.pdf", b"%PDF-" + b"0" * (7 * 1024 * 1024), "application/pdf")},
            data={"job_description": "Python developer"},
            headers={"Origin": "http://localhost:5173"},
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:5173")

    def test_scanned_pdf_gets_helpful_message(self):
        """A PDF with no text layer (like a scan) explains what to upload instead."""
        image_only_pdf = build_sample_pdf([])
        response = client.post(
            "/api/analyze",
            files={"resume_file": ("scan.pdf", image_only_pdf, "application/pdf")},
            data={"job_description": "Python developer with SQL and Docker experience."},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("scanned image", response.json()["detail"])

    def test_json_body_must_be_object(self):
        response = client.post("/api/analyze", json=["not", "an", "object"])
        self.assertEqual(response.status_code, 422)

    def test_json_fields_must_be_strings(self):
        response = client.post("/api/analyze", json={"resume_text": 123, "job_text": "python"})
        self.assertEqual(response.status_code, 422)

    def test_top_n_validation(self):
        for bad in ["abc", 0, 25, -1]:
            response = client.post("/api/suggest-roles", json={"resume_text": "Python developer", "top_n": bad})
            self.assertEqual(response.status_code, 422, bad)
        ok = client.post("/api/suggest-roles", json={"resume_text": "Python developer", "top_n": 5})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(len(ok.json()["suggested_roles"]), 5)

    def test_skills_sorted_and_breakdown_sums_to_score(self):
        response = client.post(
            "/api/analyze",
            json={
                "resume_text": (
                    "Backend engineer: Python, SQL, Docker, AWS, REST APIs, PostgreSQL. "
                    "Built data pipelines and CI/CD automation for 4 years."
                ),
                "job_text": "Hiring a Python engineer with SQL, Docker, Kubernetes, AWS and Terraform.",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["matched_skills"], sorted(payload["matched_skills"]))
        self.assertEqual(payload["missing_skills"], sorted(payload["missing_skills"]))

        breakdown = payload["score_breakdown"]
        self.assertTrue({"baseline", "tfidf_similarity", "skill_overlap_ratio", "resume_word_count"} <= set(breakdown))
        self.assertTrue(
            set(breakdown)
            <= {
                "baseline",
                "tfidf_similarity",
                "skill_overlap_ratio",
                "resume_word_count",
                "range_adjustment",
            }
        )
        # The breakdown (including any soft-cap adjustment) sums exactly to the score
        self.assertAlmostEqual(sum(breakdown.values()), payload["match_score"], delta=0.011)

    def test_short_inputs_never_score_flat_100_and_are_flagged(self):
        """A tiny resume that repeats the job ad is soft-capped below 100 and warned about."""
        response = client.post(
            "/api/analyze",
            json={
                "resume_text": "Python developer with SQL, Docker and AWS building REST APIs for 3 years.",
                "job_text": "Backend engineer: Python, SQL, Docker, Kubernetes, AWS.",
            },
        )
        payload = response.json()
        self.assertLess(payload["match_score"], 100.0)
        self.assertGreater(payload["match_score"], 85.0)
        self.assertIn("range_adjustment", payload["score_breakdown"])
        self.assertEqual(len(payload["score_warnings"]), 2)

    def test_full_length_inputs_have_no_warnings(self):
        resume = " ".join(["Experienced Python and SQL engineer building data pipelines."] * 30)
        job = " ".join(["We need a Python engineer with SQL, Docker and AWS skills."] * 8)
        payload = client.post("/api/analyze", json={"resume_text": resume, "job_text": job}).json()
        self.assertEqual(payload["score_warnings"], [])

    def test_cors_does_not_allow_credentials(self):
        response = client.options(
            "/api/analyze",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:5173")
        self.assertNotEqual(response.headers.get("access-control-allow-credentials"), "true")

    def test_unknown_origin_not_allowed(self):
        response = client.options(
            "/api/analyze",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
        self.assertIsNone(response.headers.get("access-control-allow-origin"))


if __name__ == "__main__":
    unittest.main()
