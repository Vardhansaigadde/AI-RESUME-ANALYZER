"""Tests for the project picker."""

import json
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.insights import JobInsights
from app.services.project_picker import gap_weights, load_projects, pick_projects
from app.services.resume_sections import parse_resume
from tests.test_resume_tools import STUDENT_RESUME

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parent.parent


class CatalogTests(unittest.TestCase):
    def test_catalog_is_valid(self):
        taxonomy = {
            s.lower() for s in json.loads((REPO_ROOT / "app/data/skills_list.json").read_text(encoding="utf-8"))
        }
        projects = load_projects()
        self.assertGreaterEqual(len(projects), 30)
        self.assertEqual(len({p["id"] for p in projects}), len(projects))
        for project in projects:
            with self.subTest(project=project["id"]):
                self.assertTrue(set(project["skills"]) <= taxonomy)
                self.assertIn(project["level"], {"beginner", "intermediate", "advanced"})
                self.assertGreater(project["hours"], 0)
                self.assertGreaterEqual(len(project["steps"]), 3)
                self.assertTrue(project["bullet"])


class PickerTests(unittest.TestCase):
    def test_weights(self):
        insights = JobInsights(level="Entry level", entry_friendly=True, must_have=["sql"], nice_to_have=["tableau"])
        self.assertEqual(
            gap_weights(["sql", "tableau", "excel", "communication"], insights), {"sql": 3, "tableau": 2, "excel": 1}
        )
        # Without a job: by position in the role's importance order
        self.assertEqual(gap_weights(["a", "b", "c"]), {"a": 3, "b": 2, "c": 1})

    def test_one_project_closes_several_gaps(self):
        picks = pick_projects(["tableau", "sql", "data visualization", "data analysis"], have={"python", "excel"})
        self.assertEqual(picks[0].id, "tableau-story")
        self.assertEqual(set(picks[0].closes), {"tableau", "sql", "data visualization", "data analysis"})

    def test_second_pick_covers_what_the_first_leaves(self):
        picks = pick_projects(["terraform", "aws", "kubernetes", "docker", "ci/cd"], have={"linux", "git", "python"})
        self.assertEqual(len(picks), 2)
        self.assertFalse(set(picks[0].closes) & set(picks[1].closes))
        self.assertTrue({"kubernetes", "docker"} <= set(picks[0].closes) | set(picks[1].closes))

    def test_reuses_known_skills_and_lists_extras(self):
        (pick, *_) = pick_projects(["flask", "postgresql", "rest api", "docker"], have={"python", "sql", "git"})
        self.assertEqual(pick.id, "flask-expense-api")
        self.assertEqual(set(pick.uses), {"python", "sql", "git"})
        self.assertEqual(pick.also_learn, [])

    def test_no_pick_for_minor_or_unknown_gaps(self):
        self.assertEqual(pick_projects([], have={"python"}), [])
        self.assertEqual(pick_projects(["accounting", "quickbooks"], have=set()), [])
        # A single low-priority gap isn't worth a whole project
        insights = JobInsights(level="Entry level", entry_friendly=True)
        self.assertEqual(pick_projects(["vue"], have=set(), insights=insights), [])

    def test_at_most_two_picks(self):
        gaps = ["react", "typescript", "rest api", "angular", "vue", "figma", "node.js"]
        self.assertLessEqual(len(pick_projects(gaps, have={"html", "css", "javascript"})), 2)


class EndpointTests(unittest.TestCase):
    def test_role_gap_returns_picks(self):
        resume = parse_resume(STUDENT_RESUME).model_dump()
        body = client.post("/api/role-gap", json={"resume": resume, "target_role": "DevOps / Cloud Engineer"}).json()
        self.assertTrue(body["project_picks"])
        missing = set(body["role_gap"]["missing"])
        for pick in body["project_picks"]:
            self.assertTrue(set(pick["closes"]) <= missing)


if __name__ == "__main__":
    unittest.main()
