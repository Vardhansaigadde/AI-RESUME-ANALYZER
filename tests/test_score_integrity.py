"""An honest match score: copied text, keyword lists, evidence, implied skills and eligibility."""

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services.eligibility import check_eligibility
from app.services.matcher import match_resume_to_job
from app.services.resume_sections import parse_resume
from app.services.score_integrity import implied_by, is_keyword_list, strip_copied
from app.services.skill_extractor import extract_skills

client = TestClient(app)

JOB = """Backend Developer (Fresher)
Requirements: Python, FastAPI or Django, REST APIs, PostgreSQL, Docker, Git.
Nice to have: AWS, CI/CD. You will build and maintain APIs, write tests and work with the product team."""

RESUME = """Asha Rao
asha@example.com | github.com/asha-dev
PROJECTS
Event Portal
Python, Flask, MySQL
• Built a web service with Flask and MySQL used by 1,200 students.
• Added login and email reminders, with unit tests.
EXPERIENCE
Software Intern, Acme
May 2026 – Jul 2026
• Built internal tools in Python for a team of 20.
SKILLS
Python, Flask, MySQL, Git, Linux, Docker
"""

CAMPUS_JOB = """Graduate Engineer Trainee - 2026 batch
Eligibility: B.Tech / B.E. in CSE, IT or ECE. Minimum 60% throughout 10th, 12th and graduation,
or 6.5 CGPA. No active backlogs. It is a full-time role in Bengaluru."""

CAMPUS_RESUME = """Asha Rao
EDUCATION
B.Tech in Computer Science and Engineering
Aditya University · CGPA 8.6/10
2022 – 2026
Class 12 (Intermediate), Narayana Junior College - 94%
Class 10 (SSC), Sri Chaitanya School - 88%
"""


class CopyAndKeywordTests(unittest.TestCase):
    def test_pasting_the_job_post_does_not_raise_the_score(self):
        honest = match_resume_to_job(RESUME, JOB)
        pasted = match_resume_to_job(RESUME + "\n" + JOB, JOB)
        self.assertAlmostEqual(pasted["match_score"], honest["match_score"], delta=1.0)
        self.assertGreater(pasted["integrity"]["copied_words"], 15)
        self.assertIn("copied from the job description", pasted["score_warnings"][0])

    def test_keyword_list_is_capped(self):
        result = match_resume_to_job("Python FastAPI Django REST APIs PostgreSQL Docker Git AWS CI/CD " * 3, JOB)
        self.assertLessEqual(result["match_score"], 25.0)
        self.assertTrue(result["integrity"]["keyword_list"])
        self.assertIn("keyword_list_cap", result["score_breakdown"])

    def test_dense_but_real_sentences_are_not_keyword_lists(self):
        self.assertFalse(is_keyword_list("python developer with sql, docker and aws building rest apis for 3 years"))

    def test_short_shared_phrases_are_not_copying(self):
        text, removed = strip_copied("built rest apis with python and docker", "rest apis with python and docker")
        self.assertEqual(removed, 0)
        self.assertIn("rest apis", text)


class EvidenceAndImpliedTests(unittest.TestCase):
    def test_used_skills_are_evidenced_listed_ones_are_not(self):
        result = match_resume_to_job(RESUME, JOB)
        self.assertIn("python", result["evidenced_skills"])
        self.assertIn("docker", result["listed_only_skills"])

    def test_implied_skills_partial_credit_but_still_missing_for_ats(self):
        self.assertEqual(
            implied_by({"machine learning"}),
            {"python": "machine learning", "numpy": "machine learning", "pandas": "machine learning"},
        )
        result = match_resume_to_job(
            "Trained machine learning models to predict churn with 91% accuracy for a telecom dataset project.",
            "Data analyst: python, pandas, sql and machine learning.",
        )
        self.assertIn("pandas", result["missing_skills"])
        self.assertIn("pandas", result["implied_skills"])

    def test_learning_plan_skips_implied_skills(self):
        response = client.post(
            "/api/recheck",
            json={
                "resume": {
                    "name": "Asha",
                    "skills": ["Machine Learning", "SQL"],
                    "projects": [
                        {"title": "Churn model", "bullets": ["Trained machine learning models on 10,000 customers."]}
                    ],
                },
                "job_description": "Data analyst: python, pandas, sql, machine learning and power bi.",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        planned = {item["skill"] for item in body["learning_plan"]}
        self.assertNotIn("pandas", planned)
        self.assertNotIn("python", planned)
        self.assertIn("pandas", body["implied_skills"])


class NewSkillTests(unittest.TestCase):
    def test_modern_and_campus_skills_are_recognised(self):
        self.assertEqual(
            extract_skills(
                "built apis with fastapi and next.js, a langchain rag chatbot with llms, dbms and tally erp"
            ),
            {"fastapi", "next.js", "langchain", "rag", "llms", "dbms", "tally"},
        )

    def test_everyday_words_are_not_skills(self):
        self.assertEqual(extract_skills("i would express interest; power transformers in substations"), set())


class EligibilityTests(unittest.TestCase):
    def check(self, resume_text):
        return check_eligibility(CAMPUS_JOB, parse_resume(resume_text), resume_text)

    def test_eligible_student(self):
        result = self.check(CAMPUS_RESUME)
        statuses = {c.id: c.status for c in result.checks}
        self.assertEqual(
            statuses,
            {
                "batch": "pass",
                "branch": "pass",
                "degree": "pass",
                "cgpa": "pass",
                "tenth": "pass",
                "twelfth": "pass",
                "backlogs": "check",
            },
        )
        self.assertEqual(result.status, "check")  # backlogs can't be read from a resume

    def test_not_eligible_student(self):
        low = (
            CAMPUS_RESUME.replace("8.6/10", "6.2/10")
            .replace("2022 – 2026", "2021 – 2025")
            .replace("Computer Science and Engineering", "Mechanical Engineering")
        )
        result = self.check(low)
        fails = {c.id for c in result.checks if c.status == "fail"}
        self.assertEqual(fails, {"batch", "branch", "cgpa"})
        self.assertEqual(result.status, "not_eligible")

    def test_the_word_it_is_not_the_it_branch(self):
        self.assertIsNone(check_eligibility("We love React and it is fun.", parse_resume(CAMPUS_RESUME), CAMPUS_RESUME))

    def test_date_line_becomes_the_entry_date(self):
        education = parse_resume(CAMPUS_RESUME).education[0]
        self.assertEqual(education.date, "2022 – 2026")
        self.assertNotIn("2022 – 2026", education.bullets)


if __name__ == "__main__":
    unittest.main()
