"""Unit tests for the resume suggestions service (app/services/suggestions.py).

Verifies:
1. High-frequency concrete/technical skills receive strong phrasing ("commonly required").
2. Generic soft skills (communication, leadership, etc.) are excluded from strong phrasing and use neutral framing.
3. Low-frequency or unknown skills use neutral framing.
4. Missing skills are prioritized by frequency, with high-frequency technical skills first.
5. Structural health checks (missing numbers, no projects section, resume too short) work correctly.
6. Total suggestions are capped at 5.
7. Edge cases (empty inputs, duplicates, None) are handled gracefully.
"""

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.suggestions import (
    generate_suggestions,
    is_high_frequency_technical_skill,
)


class TestSuggestionsService(unittest.TestCase):
    """Test suite for resume suggestions and prioritization logic."""

    def setUp(self):
        # A full, well-structured dummy resume that passes all structural checks
        self.good_resume = (
            "Senior Software Engineer with 8 years of experience building high-scale distributed systems. "
            "Led a team of 12 engineers delivering 15 major microservices deployed on AWS and Docker. "
            "Optimized SQL database query latency by 45%, saving $120,000 annually in cloud infrastructure costs. "
            "Projects: Designed an automated data processing pipeline handling 500 million daily records using Python. "
            "Architected real-time analytics dashboard with React, reducing reporting turnaround by 60%. "
            "Collaborated with cross-functional product and design teams to launch 3 customer-facing web applications. "
            "Maintained 99.99% system uptime across all production environments while enforcing CI/CD best practices. "
            "Mentored 6 junior developers and established code review standards across engineering organizations. "
            "Education: B.S. in Computer Science. Technical Certifications: AWS Certified Solutions Architect. "
            "Additional achievements include authoring 4 internal engineering whitepapers on distributed consensus protocols."
        )

    def test_high_frequency_technical_skill_strong_framing(self):
        """High-frequency technical skills receive the strong 'commonly required' phrasing."""
        suggestions = generate_suggestions(
            missing_skills=["excel"],
            resume_text=self.good_resume,
        )
        self.assertEqual(len(suggestions), 1)
        self.assertIn("excel", suggestions[0].lower())
        self.assertIn(
            "This is a commonly required skill across job postings — strongly consider adding it",
            suggestions[0],
        )

    def test_autocad_high_frequency_strong_framing(self):
        """Autocad (rank 82 in taxonomy) receives strong phrasing."""
        suggestions = generate_suggestions(
            missing_skills=["autocad"],
            resume_text=self.good_resume,
        )
        self.assertEqual(len(suggestions), 1)
        self.assertIn("autocad", suggestions[0].lower())
        self.assertIn("commonly required skill across job postings", suggestions[0])

    def test_generic_soft_skills_excluded_from_strong_framing(self):
        """Generic soft skills like communication and leadership get neutral framing despite high dataset frequency."""
        for soft_skill in ["communication", "leadership", "teamwork", "problem solving", "time management"]:
            suggestions = generate_suggestions(
                missing_skills=[soft_skill],
                resume_text=self.good_resume,
            )
            self.assertEqual(len(suggestions), 1)
            # Must NOT use strong framing
            self.assertNotIn("commonly required skill across job postings", suggestions[0])
            self.assertNotIn("strongly consider adding it", suggestions[0])
            # Must use neutral framing
            self.assertIn("Consider adding", suggestions[0])
            self.assertIn(soft_skill, suggestions[0].lower())

    def test_low_frequency_or_unknown_skill_neutral_framing(self):
        """Uncommon or uncataloged skills receive neutral phrasing."""
        suggestions = generate_suggestions(
            missing_skills=["obscure_custom_library_xyz"],
            resume_text=self.good_resume,
        )
        self.assertEqual(len(suggestions), 1)
        self.assertNotIn("commonly required skill across job postings", suggestions[0])
        self.assertIn("Consider adding 'obscure_custom_library_xyz'", suggestions[0])

    def test_frequency_based_prioritization(self):
        """High-frequency technical skills appear before niche tools and generic soft skills."""
        missing = ["communication", "niche_tool_xyz", "excel", "autocad", "leadership"]
        suggestions = generate_suggestions(
            missing_skills=missing,
            resume_text=self.good_resume,
        )

        # High-frequency technical skills (excel rank 16, autocad rank 82) must be first two
        self.assertIn("excel", suggestions[0].lower())
        self.assertIn("strongly consider adding it", suggestions[0])

        self.assertIn("autocad", suggestions[1].lower())
        self.assertIn("strongly consider adding it", suggestions[1])

        # Next should be niche tool (concrete, but lower frequency)
        self.assertIn("niche_tool_xyz", suggestions[2].lower())

        # Soft skills (communication, leadership) are placed after concrete skills
        remaining_text = " ".join(suggestions[3:]).lower()
        self.assertIn("communication", remaining_text)
        self.assertIn("leadership", remaining_text)

    def test_cap_total_suggestions_at_5(self):
        """Output suggestions must be capped at 5 even with many missing skills and structural issues."""
        many_missing = [
            "excel",
            "autocad",
            "database",
            "crm",
            "salesforce",
            "python",
            "sql",
            "docker",
        ]
        # Empty resume triggers 3 structural suggestions as well
        suggestions = generate_suggestions(
            missing_skills=many_missing,
            resume_text="",
        )
        self.assertEqual(len(suggestions), 5)

    def test_structural_check_missing_numbers(self):
        """Resumes without numbers trigger a recommendation for quantifiable metrics."""
        text_without_numbers = (
            "Software engineer with extensive experience in backend services and web applications. "
            "Implemented new features, worked on projects, resolved customer issues, and improved reliability."
        )
        suggestions = generate_suggestions(
            missing_skills=[],
            resume_text=text_without_numbers,
        )
        has_metrics_suggestion = any("quantifiable metrics" in s.lower() or "numbers" in s.lower() for s in suggestions)
        self.assertTrue(has_metrics_suggestion)

        # Conversely, resume with numbers should not trigger this
        good_suggestions = generate_suggestions(
            missing_skills=[],
            resume_text=self.good_resume,
        )
        has_metrics_suggestion_good = any(
            "quantifiable metrics" in s.lower() or "numbers" in s.lower() for s in good_suggestions
        )
        self.assertFalse(has_metrics_suggestion_good)

    def test_structural_check_no_projects(self):
        """Resumes without a 'projects' section trigger a recommendation to add one."""
        text_without_projects = (
            "10 years experience as an accountant. Handled 500 tax audits and 20 corporate balance sheets. " * 10
        )
        suggestions = generate_suggestions(
            missing_skills=[],
            resume_text=text_without_projects,
        )
        has_projects_suggestion = any("projects" in s.lower() for s in suggestions)
        self.assertTrue(has_projects_suggestion)

        # Resume with projects should not trigger this
        good_suggestions = generate_suggestions(
            missing_skills=[],
            resume_text=self.good_resume,
        )
        has_projects_suggestion_good = any("projects" in s.lower() for s in good_suggestions)
        self.assertFalse(has_projects_suggestion_good)

    def test_structural_check_resume_too_short(self):
        """Short resumes (< 150 words) trigger a suggestion to expand."""
        short_resume = "Software Engineer with experience in Python and 5 projects."
        suggestions = generate_suggestions(
            missing_skills=[],
            resume_text=short_resume,
        )
        has_short_suggestion = any("too short" in s.lower() for s in suggestions)
        self.assertTrue(has_short_suggestion)

        # Good resume (> 150 words) does not trigger this
        good_suggestions = generate_suggestions(
            missing_skills=[],
            resume_text=self.good_resume,
        )
        has_short_suggestion_good = any("too short" in s.lower() for s in good_suggestions)
        self.assertFalse(has_short_suggestion_good)

    def test_edge_cases_empty_and_none(self):
        """None and empty inputs execute cleanly without raising exceptions."""
        res1 = generate_suggestions(missing_skills=[], resume_text="")
        self.assertIsInstance(res1, list)
        self.assertLessEqual(len(res1), 5)

        res2 = generate_suggestions(missing_skills=None, resume_text="")
        self.assertIsInstance(res2, list)

        res3 = generate_suggestions(missing_skills=["   ", ""], resume_text="Valid resume with 10 projects.")
        self.assertIsInstance(res3, list)

    def test_deduplication_of_missing_skills(self):
        """Duplicate missing skills are deduplicated into a single suggestion."""
        suggestions = generate_suggestions(
            missing_skills=["excel", "Excel", "EXCEL"],
            resume_text=self.good_resume,
        )
        self.assertEqual(len(suggestions), 1)
        self.assertIn("excel", suggestions[0].lower())

    def test_is_high_frequency_technical_skill_helper(self):
        """Helper correctly identifies high-frequency technical skills vs soft skills."""
        self.assertTrue(is_high_frequency_technical_skill("excel"))
        self.assertTrue(is_high_frequency_technical_skill("autocad"))
        self.assertFalse(is_high_frequency_technical_skill("communication"))
        self.assertFalse(is_high_frequency_technical_skill("leadership"))
        self.assertFalse(is_high_frequency_technical_skill("non_existent_skill_xyz"))

    def test_structural_guaranteed_slot_with_many_missing_skills(self):
        """Short resume with 6+ missing technical skills guarantees structural warnings survive the cap."""
        short_resume = "Software developer specializing in web apps."
        many_technical_missing = [
            "excel",
            "autocad",
            "database",
            "crm",
            "salesforce",
            "python",
        ]
        suggestions = generate_suggestions(
            missing_skills=many_technical_missing,
            resume_text=short_resume,
        )
        self.assertEqual(len(suggestions), 5)
        # Structural check for resume length MUST survive
        has_short = any("too short" in s.lower() for s in suggestions)
        self.assertTrue(has_short, "'too short' structural warning must survive the cap at 5")
        # Structural check for metrics also survives
        has_metrics = any("quantifiable metrics" in s.lower() or "numbers" in s.lower() for s in suggestions)
        self.assertTrue(has_metrics, "'quantifiable metrics' warning should be present in reserved slots")


if __name__ == "__main__":
    unittest.main()
