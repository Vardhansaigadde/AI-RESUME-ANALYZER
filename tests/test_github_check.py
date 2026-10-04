"""Tests for the GitHub proof check."""

from datetime import UTC, datetime
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.github import GithubProfile, GithubRepo
from app.schemas.resume import StructuredResume
from app.services.github_check import check_github, repo_skills, tag_to_skill

client = TestClient(app)
NOW = datetime(2026, 10, 1, tzinfo=UTC)

RESUME = StructuredResume(
    name="Asha Rao",
    links=["github.com/asha-dev"],
    skills=["Python", "React", "Docker", "Kubernetes", "SQL", "Communication"],
    projects=[{"title": "Expense tracker", "bullets": ["Built a Flask app with SQL storage."]}],
)
PROFILE = GithubProfile(login="asha-dev", name="Asha Rao", bio="CS student · Python & React")
REPOS = [
    GithubRepo(
        name="expense-tracker",
        description="Flask app to track expenses with SQLite",
        topics=["python", "flask", "sql"],
        language="Python",
        pushed_at="2026-09-20T10:00:00Z",
        stargazers_count=3,
        homepage="https://expenses.example.com",
    ),
    GithubRepo(
        name="portfolio",
        description="My portfolio site",
        topics=["reactjs", "tailwindcss"],
        language="JavaScript",
        pushed_at="2026-08-01T10:00:00Z",
    ),
    GithubRepo(
        name="ml-notebooks", description="", topics=[], language="Jupyter Notebook", pushed_at="2025-01-01T00:00:00Z"
    ),
    GithubRepo(name="docker-curriculum", fork=True, language="Dockerfile", topics=["docker"]),
    GithubRepo(name="asha-dev", description="Profile README", language=None),
]


class TagTests(unittest.TestCase):
    def test_topics_and_languages(self):
        self.assertEqual(tag_to_skill("machine-learning"), "machine learning")
        self.assertEqual(tag_to_skill("nodejs"), "node.js")
        self.assertEqual(tag_to_skill("reactjs"), "react")
        self.assertEqual(tag_to_skill("Jupyter Notebook"), "python")
        self.assertEqual(tag_to_skill("Dockerfile"), "docker")
        self.assertIsNone(tag_to_skill("hacktoberfest"))

    def test_repo_skills(self):
        self.assertTrue({"python", "flask", "sql"} <= repo_skills(REPOS[0]))
        self.assertIn("react", repo_skills(REPOS[1]))


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.result = check_github(RESUME, PROFILE, REPOS, now=NOW)

    def test_proven_and_unproven(self):
        proven = {e.skill: e.repos for e in self.result["proven"]}
        self.assertEqual(proven["python"][0], "expense-tracker")  # most stars first
        self.assertIn("ml-notebooks", proven["python"])
        self.assertIn("react", proven)
        self.assertIn("sql", proven)
        # A forked repo isn't the student's own work
        self.assertIn("docker", self.result["unproven"])
        self.assertIn("kubernetes", self.result["unproven"])
        # Soft skills are never judged
        self.assertNotIn("communication", self.result["unproven"])

    def test_hidden_skills(self):
        hidden = {e.skill for e in self.result["hidden"]}
        self.assertIn("javascript", hidden)
        self.assertNotIn("python", hidden)

    def test_stats(self):
        stats = self.result["stats"]
        self.assertEqual(stats.own_repos, 4)
        self.assertEqual(stats.forks, 1)
        self.assertEqual(stats.stars, 3)
        self.assertEqual(stats.active_recently, 2)

    def test_checks(self):
        checks = {c.id: c.status for c in self.result["checks"]}
        self.assertEqual(checks["repos"], "pass")
        self.assertEqual(checks["activity"], "pass")
        self.assertEqual(checks["descriptions"], "warn")  # 3 of 4 described
        self.assertEqual(checks["topics"], "pass")
        self.assertEqual(checks["demo"], "pass")
        self.assertEqual(checks["profile-readme"], "pass")
        self.assertEqual(checks["bio"], "pass")
        self.assertEqual(checks["resume-link"], "pass")

    def test_empty_profile(self):
        result = check_github(StructuredResume(skills=["Python"]), GithubProfile(login="new-user"), [], now=NOW)
        checks = {c.id: c for c in result["checks"]}
        self.assertEqual(checks["repos"].status, "fail")
        self.assertEqual(checks["activity"].status, "fail")
        self.assertIn("new-user", checks["profile-readme"].tip)
        self.assertEqual(checks["resume-link"].status, "warn")
        self.assertEqual(result["unproven"], ["python"])


class EndpointTests(unittest.TestCase):
    def test_endpoint(self):
        payload = {
            "resume": RESUME.model_dump(),
            "profile": PROFILE.model_dump(),
            "repos": [r.model_dump() for r in REPOS],
        }
        response = client.post("/api/github-check", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["login"], "asha-dev")
        self.assertTrue(body["proven"])

    def test_validation(self):
        bad = {"resume": {}, "profile": {"login": ""}, "repos": []}
        self.assertEqual(client.post("/api/github-check", json=bad).status_code, 422)
        too_many = {"resume": {}, "profile": {"login": "x"}, "repos": [{"name": "r"}] * 101}
        self.assertEqual(client.post("/api/github-check", json=too_many).status_code, 422)


if __name__ == "__main__":
    unittest.main()
