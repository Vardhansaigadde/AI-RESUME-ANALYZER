"""Unit and integration tests for FastAPI endpoints."""

import unittest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestEndpoints(unittest.TestCase):
    """Test suite for HTTP API endpoints."""

    def test_read_root(self):
        """Root healthcheck endpoint returns active status."""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "active")

    def test_suggest_roles_endpoint(self):
        """POST /api/suggest-roles returns top-N suggested roles."""
        payload = {
            "resume_text": "Experienced Python Software Engineer building REST APIs with FastAPI, Docker, and PostgreSQL.",
            "top_n": 3,
        }
        response = client.post("/api/suggest-roles", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggested_roles", data)
        self.assertEqual(len(data["suggested_roles"]), 3)
        self.assertIn("role", data["suggested_roles"][0])
        self.assertIn("match_percent", data["suggested_roles"][0])

    def test_suggest_roles_empty_validation(self):
        """POST /api/suggest-roles returns 422 for empty resume_text."""
        response = client.post("/api/suggest-roles", json={"resume_text": "   ", "top_n": 3})
        self.assertEqual(response.status_code, 422)

    def test_analyze_endpoint(self):
        """POST /api/analyze returns match score, skill breakdown, features, and suggested roles."""
        payload = {
            "resume_text": "Python Developer with experience in Django, PostgreSQL, Docker, AWS.",
            "job_text": "Looking for Python Engineer proficient in Django and PostgreSQL with Docker knowledge.",
        }
        response = client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("match_score", data)
        self.assertIn("matched_skills", data)
        self.assertIn("missing_skills", data)
        self.assertIn("features", data)
        self.assertIn("suggested_roles", data)
        self.assertGreaterEqual(data["match_score"], 0.0)
        self.assertLessEqual(data["match_score"], 100.0)
        self.assertEqual(len(data["suggested_roles"]), 3)

    def test_not_found_endpoint(self):
        """Non-existent endpoints return clean 404 without leaking internals."""
        response = client.get("/api/nonexistent-route-for-testing")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data, {"detail": "Not Found"})

    def test_unhandled_exception_returns_clean_500(self):
        """Unhandled exceptions return a sanitized 500 detail without leaking traces."""
        # Dynamically mount a test route that raises an unhandled exception
        @app.get("/api/test-trigger-unhandled-error")
        def trigger_error():
            raise RuntimeError("Database connection suddenly dropped: password=secret_token_123")

        safe_client = TestClient(app, raise_server_exceptions=False)
        response = safe_client.get("/api/test-trigger-unhandled-error")
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data, {"detail": "Something went wrong. Please try again."})
        self.assertNotIn("secret_token_123", response.text)
        self.assertNotIn("Traceback", response.text)


    def test_docs_disabled_by_default(self):
        """Interactive API documentation is disabled by default in production."""
        # /docs and /openapi.json should return 404 when ENABLE_DOCS is false (default)
        if not app.docs_url:
            response = client.get("/docs")
            self.assertEqual(response.status_code, 404)
        if not app.openapi_url:
            response = client.get("/openapi.json")
            self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
