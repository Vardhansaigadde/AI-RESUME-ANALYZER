"""Tests for app/ml/features.py.

Verifies:
1. build_features() generates a DataFrame with expected columns and valid values.
2. build_features(as_dataframe=False) returns expected dictionary representation.
3. calculate_tfidf_similarity() handles standard and edge-case text inputs.
4. Processed features dataset (features.csv) exists with 2,385 rows and no nulls.
5. Serialized TF-IDF vectorizer artifact loads and transforms inputs.
"""

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from app.ml.features import (
    FEATURE_COLUMNS,
    build_features,
    calculate_tfidf_similarity,
    get_tfidf_vectorizer,
)


class TestFeaturesUnit(unittest.TestCase):
    """Unit tests for feature builder functions."""

    def setUp(self):
        self.sample_resume = (
            "Experienced Python developer with expertise in SQL, Docker, and REST APIs. "
            "Led backend architecture and data analysis pipelines using AWS."
        )
        self.sample_job = (
            "Looking for a Senior Backend Developer proficient in Python, SQL, Docker, "
            "and cloud platforms (AWS). Experience with microservices required."
        )

    def test_build_features_returns_dataframe(self):
        """build_features() returns a 1-row DataFrame with exact FEATURE_COLUMNS."""
        feat_df = build_features(self.sample_resume, self.sample_job, as_dataframe=True)
        self.assertIsInstance(feat_df, pd.DataFrame)
        self.assertEqual(len(feat_df), 1)
        self.assertEqual(list(feat_df.columns), FEATURE_COLUMNS)

    def test_build_features_returns_dict(self):
        """build_features(as_dataframe=False) returns a dictionary matching FEATURE_COLUMNS."""
        feat_dict = build_features(self.sample_resume, self.sample_job, as_dataframe=False)
        self.assertIsInstance(feat_dict, dict)
        self.assertEqual(set(feat_dict.keys()), set(FEATURE_COLUMNS))
        for col, val in feat_dict.items():
            self.assertIsInstance(val, float, f"Feature {col} value should be float")

    def test_feature_values_in_valid_ranges(self):
        """Features must fall into expected numeric bounds."""
        feat_df = build_features(self.sample_resume, self.sample_job)
        row = feat_df.iloc[0]

        self.assertGreater(row["tfidf_similarity"], 0.0)
        self.assertLessEqual(row["tfidf_similarity"], 1.0)

        self.assertGreater(row["skill_overlap_ratio"], 0.0)
        self.assertLessEqual(row["skill_overlap_ratio"], 1.0)

        self.assertGreater(row["resume_word_count"], 0)

    def test_calculate_tfidf_similarity_empty_inputs(self):
        """calculate_tfidf_similarity() returns 0.0 for empty texts."""
        self.assertEqual(calculate_tfidf_similarity("", "some job text"), 0.0)
        self.assertEqual(calculate_tfidf_similarity("some resume text", ""), 0.0)
        self.assertEqual(calculate_tfidf_similarity("", ""), 0.0)

    def test_calculate_tfidf_similarity_identical_texts(self):
        """calculate_tfidf_similarity() returns ~1.0 for identical text."""
        text = "python sql docker kubernetes machine learning data analysis"
        sim = calculate_tfidf_similarity(text, text)
        self.assertAlmostEqual(sim, 1.0, places=3)


class TestFeaturesArtifacts(unittest.TestCase):
    """Integration checks for saved artifacts."""

    def test_tfidf_vectorizer_artifact_exists(self):
        """models/tfidf_vectorizer.joblib must exist and be loadable."""
        vec = get_tfidf_vectorizer()
        self.assertIsNotNone(vec, "TF-IDF vectorizer artifact could not be loaded.")
        self.assertGreater(len(vec.vocabulary_), 0)

    def test_features_csv_exists_and_valid(self):
        """data/processed/features.csv must exist with 2,385 rows and no nulls."""
        csv_path = REPO_ROOT / "data" / "processed" / "features.csv"
        self.assertTrue(csv_path.exists(), f"features.csv not found at {csv_path}")

        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 2385, f"Expected 2385 rows, got {len(df)}")

        expected_cols = FEATURE_COLUMNS + ["ai_match_score"]
        self.assertEqual(list(df.columns), expected_cols)
        self.assertEqual(df.isnull().sum().sum(), 0, "features.csv contains unexpected null values")


if __name__ == "__main__":
    unittest.main()
