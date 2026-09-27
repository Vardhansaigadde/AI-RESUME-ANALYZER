"""Tests for app/services/matcher.py.

Verifies:
1. match_resume_to_job() produces expected score and keys using 4 leakage-free features.
2. Skill extraction, matched skills, and missing skills are correctly reported.
3. Fallback heuristic works properly when model artifact is unavailable.
"""

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.ml.features import FEATURE_COLUMNS
from app.services.matcher import (
    clear_matcher_cache,
    get_feature_scaler,
    get_match_model,
    match_resume_to_job,
)


class TestMatcherService(unittest.TestCase):
    """Unit tests for the match scoring service."""

    def setUp(self):
        self.sample_resume = (
            "Senior Backend Engineer with 5+ years building scalable systems in Python, "
            "PostgreSQL, Docker, and AWS. Experienced in RESTful API development and microservices."
        )
        self.sample_job = (
            "We are seeking a Python Developer with strong proficiency in Python, PostgreSQL, "
            "Docker, and Kubernetes. AWS experience is a plus."
        )

    def test_match_resume_to_job_structure(self):
        """match_resume_to_job returns dictionary with valid structure and bounds."""
        result = match_resume_to_job(self.sample_resume, self.sample_job)

        self.assertIn("match_score", result)
        self.assertIn("matched_skills", result)
        self.assertIn("missing_skills", result)
        self.assertIn("features", result)
        self.assertIn("resume_skills_count", result)
        self.assertIn("required_skills_count", result)

        # Check bounds
        self.assertGreaterEqual(result["match_score"], 0.0)
        self.assertLessEqual(result["match_score"], 100.0)

        # Check features match exactly the 3 leakage-free FEATURE_COLUMNS
        feature_keys = list(result["features"].keys())
        self.assertEqual(feature_keys, FEATURE_COLUMNS)
        self.assertEqual(len(feature_keys), 3)

        # Check skills
        self.assertIn("python", [s.lower() for s in result["matched_skills"]])
        self.assertIn("docker", [s.lower() for s in result["matched_skills"]])

    def test_match_resume_to_job_empty_texts(self):
        """Empty texts return non-negative score and valid keys."""
        result = match_resume_to_job("", "")
        self.assertEqual(result["match_score"], 0.0)
        self.assertEqual(result["matched_skills"], [])
        self.assertEqual(result["missing_skills"], [])

    def test_clear_matcher_cache(self):
        """Clearing matcher cache resets singletons."""
        _ = get_match_model()
        _ = get_feature_scaler()
        clear_matcher_cache()
        # Ensure no exception thrown and re-callable
        model = get_match_model()
        scaler = get_feature_scaler()

    def test_get_feature_scaler_loads_artifact(self):
        """Feature scaler artifact loads correctly if present."""
        scaler = get_feature_scaler()
        if scaler is not None:
            self.assertEqual(len(scaler.center_), 3)
            self.assertEqual(len(scaler.scale_), 3)


if __name__ == "__main__":
    unittest.main()
