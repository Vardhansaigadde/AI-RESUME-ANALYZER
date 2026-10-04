"""Tests for resume-only analysis: optional job description, role gap and skills inventory."""

import json
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services.role_gap import available_roles, compare_with_role, resolve_role
from app.services.skills_inventory import build_inventory, group_of
from tests.test_resume_tools import JOB, STUDENT_RESUME

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parent.parent


class TestTargetRoles(unittest.TestCase):
    def test_roles_file_is_consistent(self):
        data = json.loads((REPO_ROOT / "app/data/target_roles.json").read_text(encoding="utf-8"))
        taxonomy = {
            s.lower() for s in json.loads((REPO_ROOT / "app/data/skills_list.json").read_text(encoding="utf-8"))
        }
        categories = set(json.loads((REPO_ROOT / "app/data/role_profiles.json").read_text(encoding="utf-8")))
        self.assertGreaterEqual(len(data["roles"]), 20)
        for role, skills in data["roles"].items():
            self.assertTrue(set(skills) <= taxonomy, role)
        self.assertEqual(set(data["category_default"]), categories)
        self.assertTrue(set(data["category_default"].values()) <= set(data["roles"]))

    def test_resolve_role(self):
        self.assertEqual(resolve_role("Data Analyst", []), "Data Analyst")
        self.assertEqual(resolve_role("Not a role", [{"role": "ACCOUNTANT", "match_percent": 80}]), "Accountant")
        self.assertEqual(resolve_role(None, [{"role": "INFORMATION-TECHNOLOGY"}]), "Software Engineer")
        self.assertIn(resolve_role(None, []), available_roles())

    def test_compare_keeps_importance_order(self):
        gap = compare_with_role({"python", "git", "sql"}, "Software Engineer")
        self.assertEqual(gap.have, ["python", "git", "sql"])
        self.assertEqual(gap.missing[:3], ["data structures", "algorithms", "object-oriented programming"])
        self.assertAlmostEqual(gap.coverage, 3 / 15, places=3)


class TestSkillsInventory(unittest.TestCase):
    def test_groups_and_counts(self):
        groups = {g.group: {s.skill: s.count for s in g.skills} for g in build_inventory(STUDENT_RESUME)}
        self.assertEqual(groups["Programming languages"]["python"], 2)
        self.assertIn("html", groups["Web & frameworks"])
        self.assertIn("machine learning", groups["Data & AI"])

    def test_group_of(self):
        self.assertEqual(group_of("docker"), "Cloud & DevOps")
        self.assertEqual(group_of("communication"), "Soft skills")
        self.assertEqual(group_of("general ledger"), "Domain skills")


class TestResumeOnlyApi(unittest.TestCase):
    def test_json_without_job(self):
        body = client.post("/api/analyze", json={"resume_text": STUDENT_RESUME}).json()
        self.assertEqual(body["mode"], "resume_only")
        self.assertIsNone(body["match_score"])
        self.assertEqual(body["matched_skills"], [])
        self.assertIsNone(body["job_insights"])
        self.assertEqual(body["role_gap"]["role"], "Software Engineer")
        self.assertTrue(body["skills_inventory"])
        self.assertTrue(body["learning_plan"])
        self.assertTrue(all(i["priority"] == "core-skill" for i in body["learning_plan"]))
        self.assertEqual({c["id"]: c["status"] for c in body["ats"]["checks"]}["keywords"], "skip")

    def test_target_role_and_job_mode(self):
        body = client.post(
            "/api/analyze", json={"resume_text": STUDENT_RESUME, "job_text": JOB, "target_role": "Data Analyst"}
        ).json()
        self.assertEqual(body["mode"], "job")
        self.assertIsNotNone(body["match_score"])
        self.assertEqual(body["role_gap"]["role"], "Data Analyst")
        # With a job, the learning plan follows the job's gaps, not the role's
        self.assertTrue(all(i["priority"] != "core-skill" for i in body["learning_plan"]))

    def test_recheck_without_job(self):
        resume = client.post("/api/analyze", json={"resume_text": STUDENT_RESUME}).json()["resume"]
        body = client.post("/api/recheck", json={"resume": resume}).json()
        self.assertEqual(body["mode"], "resume_only")

    def test_role_gap_endpoint(self):
        resume = client.post("/api/analyze", json={"resume_text": STUDENT_RESUME}).json()["resume"]
        response = client.post("/api/role-gap", json={"resume": resume, "target_role": "Machine Learning Engineer"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["role_gap"]["role"], "Machine Learning Engineer")
        self.assertIn("machine learning", body["role_gap"]["have"])
        self.assertTrue(body["learning_plan"])
        self.assertEqual(client.post("/api/role-gap", json={"resume": resume, "target_role": ""}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
