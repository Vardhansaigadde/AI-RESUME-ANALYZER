"""Tests for the learning roadmap: study order, prerequisites and roadmap data."""

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services import learning_plan
from app.services.learning_plan import build_learning_plan, load_resources
from app.services.resume_sections import parse_resume
from app.services.role_gap import available_roles, compare_with_role, role_roadmaps
from tests.test_resume_tools import STUDENT_RESUME

client = TestClient(app)


class RoadmapDataTests(unittest.TestCase):
    def test_every_skill_has_roadmap_details(self):
        resources = load_resources()
        for skill, entry in resources.items():
            with self.subTest(skill=skill):
                self.assertGreater(entry["hours"], 0)
                self.assertEqual(len(entry["done"]), 3)
                videos = [r for r in entry["resources"] if r["kind"] == "video"]
                self.assertEqual(len(videos), 1)
                self.assertTrue(videos[0]["url"].startswith("https://www.youtube.com/watch?v="))
                self.assertTrue(videos[0]["by"])
                self.assertTrue(set(entry["needs"]) <= set(resources))
                if entry["roadmap"]:
                    self.assertTrue(entry["roadmap"].startswith("https://roadmap.sh/"))

    def test_prerequisites_never_loop(self):
        resources = load_resources()

        def depth(skill, path=()):
            self.assertNotIn(skill, path, f"loop: {path + (skill,)}")
            return 1 + max((depth(n, path + (skill,)) for n in resources[skill]["needs"]), default=0)

        for skill in resources:
            depth(skill)

    def test_role_roadmaps(self):
        roadmaps = role_roadmaps()
        self.assertTrue(set(roadmaps) <= set(available_roles()))
        self.assertEqual(roadmaps["Data Analyst"], "https://roadmap.sh/data-analyst")
        self.assertEqual(compare_with_role({"python"}, "Frontend Developer").roadmap, "https://roadmap.sh/frontend")
        self.assertEqual(compare_with_role({"python"}, "Teacher").roadmap, "")


class StudyOrderTests(unittest.TestCase):
    def test_missing_prerequisites_come_first(self):
        plan = build_learning_plan(["react"], "", None, role="Frontend Developer", have={"html"})
        self.assertEqual([i.skill for i in plan], ["javascript", "css", "react"])
        self.assertEqual(plan[0].priority, "prerequisite")
        self.assertEqual(plan[0].needed_for, ["react"])
        self.assertEqual(plan[0].why, "")
        self.assertEqual(plan[-1].priority, "core-skill")

    def test_known_skills_are_not_prerequisites(self):
        plan = build_learning_plan(["react"], "", None, role="Frontend Developer", have={"html", "css", "javascript"})
        self.assertEqual([i.skill for i in plan], ["react"])

    def test_missing_prerequisite_keeps_its_own_priority(self):
        plan = build_learning_plan(["react", "javascript"], "", None, role="Frontend Developer", have={"html", "css"})
        self.assertEqual([i.skill for i in plan], ["javascript", "react"])
        self.assertEqual(plan[0].priority, "core-skill")
        self.assertEqual(plan[0].needed_for, ["react"])

    def test_no_prerequisites_without_resume_skills(self):
        plan = build_learning_plan(["react"], "", None, role="Frontend Developer")
        self.assertEqual([i.skill for i in plan], ["react"])

    def test_items_carry_roadmap_fields(self):
        (item,) = build_learning_plan(["sql"], "", None, role="Data Analyst", have=set())
        self.assertGreater(item.hours, 0)
        self.assertEqual(len(item.done), 3)
        self.assertEqual(item.roadmap, "https://roadmap.sh/sql")
        self.assertEqual(item.resources[-1].kind, "video")

    def test_cut_drops_orphaned_prerequisites(self):
        original = learning_plan.MAX_ITEMS
        learning_plan.MAX_ITEMS = 2
        try:
            plan = build_learning_plan(["react"], "", None, role="Frontend Developer", have=set())
        finally:
            learning_plan.MAX_ITEMS = original
        # html and css made the cut but react did not, so they have nothing to lead to
        self.assertEqual(plan, [])


class EndpointTests(unittest.TestCase):
    def test_role_gap_returns_study_order(self):
        resume = parse_resume(STUDENT_RESUME).model_dump()
        body = client.post("/api/role-gap", json={"resume": resume, "target_role": "Frontend Developer"}).json()
        self.assertEqual(body["role_gap"]["roadmap"], "https://roadmap.sh/frontend")
        skills = [i["skill"] for i in body["learning_plan"]]
        for item in body["learning_plan"]:
            for later in item["needed_for"]:
                self.assertLess(skills.index(item["skill"]), skills.index(later))


if __name__ == "__main__":
    unittest.main()
