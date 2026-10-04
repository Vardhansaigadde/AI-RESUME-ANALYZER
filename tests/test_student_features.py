"""Tests for the job decoder, learning plan and student / fresher mode."""

import json
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services.ats_checker import check_ats
from app.services.job_decoder import decode_job
from app.services.learning_plan import build_learning_plan, load_resources
from app.services.resume_sections import looks_like_student, parse_resume
from tests.test_resume_tools import JOB, STUDENT_RESUME

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parent.parent

SECTIONED_JOB = """Junior Software Engineer

Responsibilities
- Build REST APIs in Python and maintain SQL databases
- Deploy services on AWS

Requirements
- Strong Python and object-oriented programming skills
- Experience with SQL and Git; Docker or cloud exposure is a plus

Nice to have
- Kubernetes
"""


class TestJobDecoder(unittest.TestCase):
    def test_sections_and_plus_phrases(self):
        insights = decode_job(SECTIONED_JOB, {"python", "sql", "html"})
        self.assertEqual(insights.level, "Entry level")
        self.assertTrue(insights.entry_friendly)
        self.assertEqual(set(insights.must_have), {"python", "object-oriented programming", "sql", "git"})
        self.assertEqual(set(insights.nice_to_have), {"docker", "kubernetes"})
        self.assertEqual(set(insights.also_mentioned), {"rest api", "aws"})
        self.assertEqual(set(insights.must_have_covered), {"python", "sql"})
        self.assertEqual(insights.lead_with[0], "python")  # mentioned most often

    def test_senior_years_and_degree(self):
        job = (
            "Senior Data Engineer\nRequirements:\n- 5+ years of experience with Spark and Airflow\n"
            "- Strong SQL\nNice to have:\n- Kafka\nBachelor's degree in Computer Science."
        )
        insights = decode_job(job, set())
        self.assertEqual(insights.level, "Senior")
        self.assertFalse(insights.entry_friendly)
        self.assertEqual((insights.years_min, insights.years_max), (5, None))
        self.assertTrue(insights.degree_mentioned)
        self.assertIn("spark", insights.must_have)
        self.assertEqual(insights.nice_to_have, ["kafka"])

    def test_fresher_range(self):
        insights = decode_job("Hiring freshers with Java and MySQL. 0-1 years experience. React is a plus.", set())
        self.assertEqual((insights.years_min, insights.years_max), (0, 1))
        self.assertEqual(insights.level, "Entry level")


class TestLearningPlan(unittest.TestCase):
    def test_resources_are_valid(self):
        resources = load_resources()
        taxonomy = {
            s.lower() for s in json.loads((REPO_ROOT / "app/data/skills_list.json").read_text(encoding="utf-8"))
        }
        self.assertGreaterEqual(len(resources), 60)
        for skill, entry in resources.items():
            self.assertIn(skill, taxonomy)
            self.assertTrue(entry["what"] and entry["project"])
            self.assertTrue(entry["resources"])
            for res in entry["resources"]:
                self.assertTrue(res["url"].startswith("https://"), res["url"])

    def test_priority_order_and_job_line(self):
        insights = decode_job(SECTIONED_JOB, set())
        plan = build_learning_plan(["kubernetes", "aws", "git", "communication"], SECTIONED_JOB, insights)
        # Soft skills come last, with evidence advice instead of courses
        self.assertEqual([i.skill for i in plan], ["git", "kubernetes", "aws", "communication"])
        self.assertEqual(plan[0].priority, "must-have")
        self.assertEqual(plan[0].why, "Experience with SQL and Git;")
        self.assertTrue(plan[0].resources)

    def test_soft_skill_gets_evidence_advice(self):
        plan = build_learning_plan(["communication"], "Clear communication skills are required.", None)
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].resources, [])
        self.assertIn("bullet", plan[0].project)

    def test_unknown_skills_are_skipped(self):
        self.assertEqual(build_learning_plan(["some unknown tool"], "We use some unknown tool.", None), [])


class TestStudentMode(unittest.TestCase):
    def test_student_detection(self):
        resume = parse_resume(STUDENT_RESUME)
        self.assertTrue(looks_like_student(STUDENT_RESUME, resume, 2026))
        senior = "Jordan Lee\nExperience\nEngineering Manager, Acme 2010 - 2024\nEducation\nMS, 2008"
        self.assertFalse(looks_like_student(senior, parse_resume(senior), 2026))

    def test_student_checks(self):
        resume = parse_resume(STUDENT_RESUME)
        report = check_ats(STUDENT_RESUME, resume, layout=None, student_mode=True)
        student = {c.id: c.status for c in report.checks if c.category == "student"}
        self.assertEqual(
            student,
            {
                "education_first": "pass",  # no Experience section to come before
                "projects": "pass",
                "internship": "warn",
                "grades": "pass",
                "github": "pass",
                "one_page": "pass",
            },
        )
        self.assertFalse(any(c.category == "student" for c in check_ats(STUDENT_RESUME, resume).checks))

    def test_percentages_in_bullets_are_not_grades(self):
        text = "Education\nB.Tech, State University 2024 - 2028\nProjects\nPortal\n2025\n- Cut load time by 40%"
        report = check_ats(text, parse_resume(text), student_mode=True)
        self.assertEqual({c.id: c.status for c in report.checks}["grades"], "warn")


class TestApiFields(unittest.TestCase):
    def test_analyze_and_recheck_carry_student_mode(self):
        body = client.post(
            "/api/analyze", json={"resume_text": STUDENT_RESUME, "job_text": JOB, "student_mode": True}
        ).json()
        self.assertTrue(body["student_mode"])
        self.assertTrue(body["student_detected"])
        self.assertEqual(body["job_insights"]["level"], "Entry level")
        self.assertTrue(body["learning_plan"])
        self.assertTrue(any(c["category"] == "student" for c in body["ats"]["checks"]))

        again = client.post(
            "/api/recheck", json={"resume": body["resume"], "job_description": JOB, "student_mode": True}
        ).json()
        self.assertTrue(again["student_mode"])
        off = client.post("/api/recheck", json={"resume": body["resume"], "job_description": JOB}).json()
        self.assertFalse(off["student_mode"])

    def test_form_flag(self):
        from tests.test_resume_tools import docx_bytes

        content = docx_bytes(lambda d: [d.add_paragraph(line) for line in STUDENT_RESUME.splitlines() if line.strip()])
        body = client.post(
            "/api/analyze",
            files={
                "resume_file": (
                    "r.docx",
                    content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"job_description": JOB, "student_mode": "true"},
        ).json()
        self.assertTrue(body["student_mode"])


if __name__ == "__main__":
    unittest.main()
