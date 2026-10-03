"""Unit tests for app.services.data_cleaning."""

import unittest
import pandas as pd
from app.services.data_cleaning import (
    clean_text,
    safe_parse_skills,
    clean_resume_dataframe,
    clean_job_fit_dataframe,
    strip_leading_title,
)


class TestDataCleaning(unittest.TestCase):
    def test_clean_text_preserves_tech_terms(self):
        raw = "<p>Experienced with <b>C++</b>, <b>C#</b>, .NET, Node.js, and CI/CD! &amp; 10+ years.</p>"
        cleaned = clean_text(raw)
        self.assertIn("c++", cleaned)
        self.assertIn("c#", cleaned)
        self.assertIn(".net", cleaned)
        self.assertIn("node.js", cleaned)
        self.assertIn("ci/cd", cleaned)
        self.assertIn("10+ years", cleaned)
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("&amp;", cleaned)

    def test_clean_text_whitespace_and_dividers(self):
        raw = "Header\n\n------------------\n\nBody   text... with    spaces."
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, "header body text with spaces.")

    def test_safe_parse_skills_valid(self):
        raw = "['python', 'fastapi', 'sql']"
        parsed = safe_parse_skills(raw)
        self.assertEqual(parsed, ['python', 'fastapi', 'sql'])

    def test_safe_parse_skills_malformed(self):
        raw = "['unclosed_list', 123"
        parsed = safe_parse_skills(raw)
        self.assertIsNone(parsed)

    def test_clean_resume_dataframe(self):
        df = pd.DataFrame({
            "ID": [1],
            "Resume_str": ["<h1>Data Scientist</h1> with Python & C++."],
            "Resume_html": ["<div>HTML Content</div>"],
            "Category": ["IT"]
        })
        cleaned = clean_resume_dataframe(df, drop_html=True)
        self.assertNotIn("Resume_html", cleaned.columns)
        self.assertEqual(cleaned["Resume_str"].iloc[0], "data scientist with python c++.")

    def test_clean_job_fit_dataframe_drop_malformed(self):
        df = pd.DataFrame({
            "ID": [1, 2],
            "resume_text": ["Resume 1", "Resume 2"],
            "job_text": ["Job 1", "Job 2"],
            "category": ["IT", "IT"],
            "job_required_skills": ["['python', 'sql']", "['python', 'c++']"],
            "resume_skill_list": ["['python']", "malformed_list["],
            "ai_matched_skills": ["['python']", "['c++']"],
            "ai_match_score": [80.0, 70.0],
            "skill_string_match_score": [50.0, 40.0],
            "fuzzy_match_score": [60.0, 55.0]
        })
        cleaned, dropped = clean_job_fit_dataframe(df)
        self.assertEqual(dropped, 1)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned["ID"].iloc[0], 1)


    def test_clean_text_is_idempotent(self):
        """Inference re-cleans already-clean training text; it must not change."""
        raw = "  Senior C++ / .NET Engineer — 10+ yrs; Node.js & CI/CD...\n\n<b>AWS</b>  "
        once = clean_text(raw)
        self.assertEqual(clean_text(once), once)

    def test_strip_leading_title(self):
        self.assertEqual(
            strip_leading_title("  SALES ASSOCIATE Summary My goal is to grow."),
            "Summary My goal is to grow.",
        )
        self.assertEqual(
            strip_leading_title("HR MANAGER/GENERALIST Summary Background in HR."),
            "Summary Background in HR.",
        )
        # No leading all-caps run: unchanged (whitespace normalized)
        self.assertEqual(strip_leading_title("Highlights  Prog. Languages: C"), "Highlights Prog. Languages: C")
        self.assertEqual(strip_leading_title(None), "")


if __name__ == "__main__":
    unittest.main()
