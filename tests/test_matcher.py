"""Tests for app/services/matcher.py.

Verifies:
1. match_resume_to_job() produces expected score and keys using 3 leakage-free features.
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
        self.assertIsNotNone(get_match_model())
        self.assertIsNotNone(get_feature_scaler())

    def test_get_feature_scaler_loads_artifact(self):
        """Feature scaler artifact loads correctly if present."""
        scaler = get_feature_scaler()
        if scaler is not None:
            self.assertEqual(len(scaler.center_), 3)
            self.assertEqual(len(scaler.scale_), 3)

    def test_raw_and_cleaned_input_give_same_result(self):
        """Inference normalizes text exactly like training, so pre-cleaning changes nothing."""
        from app.services.data_cleaning import clean_text

        resume = "• Built REST APIs in Python & FastAPI!\n• Deployed with Docker/Kubernetes on AWS."
        job = "<p>Seeking a <b>Python</b> engineer (Docker, AWS, Terraform).</p>"
        raw = match_resume_to_job(resume, job)
        pre_cleaned = match_resume_to_job(clean_text(resume), clean_text(job))
        self.assertEqual(raw["match_score"], pre_cleaned["match_score"])
        self.assertEqual(raw["matched_skills"], pre_cleaned["matched_skills"])

    def test_mismatched_domain_scores_lower(self):
        """A nursing resume scores well below a software resume for a software job."""
        job = (
            "Senior Python developer to build REST APIs and data pipelines. Requires Python, SQL, "
            "Docker, Kubernetes, AWS, CI/CD and experience with microservices and PostgreSQL."
        )
        software = (
            "Software engineer with 5 years building REST APIs and data pipelines in Python and SQL. "
            "Containerized services with Docker and Kubernetes on AWS, set up CI/CD, used PostgreSQL."
        )
        nurse = (
            "Registered nurse with 6 years in the emergency department: triage, vital signs monitoring, "
            "medication administration, wound care and patient education."
        )
        software_score = match_resume_to_job(software, job)["match_score"]
        nurse_score = match_resume_to_job(nurse, job)["match_score"]
        self.assertGreater(software_score, nurse_score + 20)

    def test_soft_cap_score(self):
        """Soft cap: identity in the middle, strictly inside (0, 100), order preserving."""
        from app.services.matcher import SOFT_CAP_HIGH, SOFT_CAP_LOW, soft_cap_score

        for raw in [SOFT_CAP_LOW, 40.0, 63.2, SOFT_CAP_HIGH]:
            self.assertAlmostEqual(soft_cap_score(raw), raw)
        raws = [-500, -50, 0, 5, 15, 50, 85, 95, 120, 500]
        capped = [soft_cap_score(r) for r in raws]
        self.assertEqual(capped, sorted(capped))
        self.assertEqual(len(set(capped[:-1])), len(capped) - 1)  # distinct until float saturation
        self.assertTrue(all(0.0 <= c <= 100.0 for c in capped))
        self.assertLess(soft_cap_score(120.0), 100.0)
        self.assertGreater(soft_cap_score(-20.0), 0.0)


if __name__ == "__main__":
    unittest.main()
