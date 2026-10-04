"""Tests for the live job search (job sites are faked; no network calls)."""

import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.main import app
from app.services import job_search
from app.services.resume_sections import parse_resume
from tests.test_resume_tools import STUDENT_RESUME

client = TestClient(app)
RESUME = parse_resume(STUDENT_RESUME).model_dump()

HIMALAYAS = {
    "jobs": [
        {
            "title": "Software Engineer Intern",
            "companyName": "Acme",
            "employmentType": "Intern",
            "seniority": ["Entry-level"],
            "locationRestrictions": ["India"],
            "description": "<p>We use <b>Python</b>, SQL and React &amp; Git.</p><ul><li>Docker</li></ul>",
            "pubDate": 1790000000,
            "minSalary": None,
            "maxSalary": None,
            "applicationLink": "https://himalayas.app/companies/acme/jobs/intern",
            "guid": "https://himalayas.app/companies/acme/jobs/intern",
        },
        {
            "title": "Senior Platform Engineer",
            "companyName": "Bigco",
            "employmentType": "Full Time",
            "seniority": ["Senior"],
            "locationRestrictions": [],
            "description": "<p>Kubernetes, Terraform, Go, AWS.</p>",
            "pubDate": 1790000000,
            "minSalary": 90000,
            "maxSalary": 120000,
            "currency": "USD",
            "salaryPeriod": "annual",
            "applicationLink": "https://himalayas.app/companies/bigco/jobs/platform",
        },
        {"title": "", "applicationLink": "https://himalayas.app/x"},  # unusable, skipped
    ]
}

ADZUNA = {
    "results": [
        {
            "id": "42",
            "title": "Graduate <strong>Trainee</strong> Developer",
            "company": {"display_name": "Desi Tech"},
            "location": {"display_name": "Bengaluru, Karnataka"},
            "description": "Java and SQL developer trainee, Spring Boot…",
            "created": "2026-09-30T08:00:00Z",
            "contract_time": "full_time",
            "salary_min": 400000,
            "salary_max": 600000,
            "salary_is_predicted": "0",
            "redirect_url": "https://www.adzuna.in/land/ad/42",
        },
        {  # same posting as on Himalayas: deduplicated
            "id": "43",
            "title": "Software Engineer Intern",
            "company": {"display_name": "Acme"},
            "description": "Python",
            "redirect_url": "https://www.adzuna.in/land/ad/43",
        },
    ]
}


def fake_get(urls_seen):
    def get(url):
        urls_seen.append(url)
        if url.startswith(job_search.HIMALAYAS_URL):
            return HIMALAYAS
        if "adzuna" in url:
            return ADZUNA
        raise AssertionError(url)

    return get


class JobSearchServiceTests(unittest.TestCase):
    def setUp(self):
        job_search.CACHE.clear()
        self.urls = []
        patcher = mock.patch.object(job_search, "_http_get_json", side_effect=fake_get(self.urls))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_himalayas_only_without_adzuna_keys(self):
        with mock.patch.dict("os.environ", {"ADZUNA_APP_ID": "", "ADZUNA_APP_KEY": ""}):
            result = job_search.search_jobs(STUDENT_RESUME, "software  engineer", "in", "all")
        self.assertEqual(result["query"], "software engineer")
        self.assertEqual(len(result["jobs"]), 2)
        sources = {s.name: s for s in result["sources"]}
        self.assertEqual(sources["Himalayas"].status, "ok")
        self.assertEqual(sources["Adzuna"].status, "off")
        self.assertEqual(len(self.urls), 1)
        params = parse_qs(urlparse(self.urls[0]).query)
        self.assertEqual(params["country"], ["IN"])
        self.assertEqual(params["q"], ["software engineer"])

    def test_postings_are_scored_and_sorted(self):
        result = job_search.search_jobs(STUDENT_RESUME, "python", "IN", "all")
        jobs = result["jobs"]
        self.assertEqual([j.fit_score for j in jobs], sorted((j.fit_score for j in jobs), reverse=True))
        intern = next(j for j in jobs if j.company == "Acme")
        self.assertIn("python", intern.matched_skills)
        self.assertEqual(intern.location, "Remote · India")
        self.assertEqual(intern.posted, "2026-09-21")
        self.assertNotIn("<", intern.excerpt)
        self.assertIn("React & Git", intern.excerpt)
        senior = next(j for j in jobs if j.company == "Bigco")
        self.assertEqual(senior.location, "Remote · Worldwide")
        self.assertEqual(senior.salary, "USD 90k – 120k / year")

    def test_internship_and_entry_filters(self):
        interns = job_search.search_jobs(STUDENT_RESUME, "software", "ANY", "internship")
        self.assertEqual([j.company for j in interns["jobs"]], ["Acme"])
        params = parse_qs(urlparse(self.urls[0]).query)
        self.assertEqual(params["employment_type"], ["Intern"])
        self.assertNotIn("country", params)

        job_search.CACHE.clear()
        entry = job_search.search_jobs(STUDENT_RESUME, "software", "ANY", "entry")
        self.assertNotIn("Bigco", [j.company for j in entry["jobs"]])
        self.assertEqual(parse_qs(urlparse(self.urls[-1]).query)["seniority"], ["Entry-level"])

    def test_results_are_cached(self):
        job_search.search_jobs(STUDENT_RESUME, "Python", "IN", "all")
        job_search.search_jobs(STUDENT_RESUME, "python", "IN", "all")
        self.assertEqual(len(self.urls), 1)

    def test_adzuna_when_keys_are_set(self):
        with mock.patch.dict("os.environ", {"ADZUNA_APP_ID": "id", "ADZUNA_APP_KEY": "key"}):
            result = job_search.search_jobs(STUDENT_RESUME, "developer", "IN", "internship")
        adzuna_url = next(u for u in self.urls if "adzuna" in u)
        self.assertTrue(adzuna_url.startswith("https://api.adzuna.com/v1/api/jobs/in/search/1?"))
        self.assertEqual(parse_qs(urlparse(adzuna_url).query)["what_or"], ["intern internship trainee apprentice"])
        trainee = next(j for j in result["jobs"] if j.source == "Adzuna")
        self.assertEqual(trainee.title, "Graduate Trainee Developer")
        self.assertEqual(trainee.salary, "₹4.0 L – 6.0 L / year")
        self.assertTrue(trainee.short_description)
        self.assertEqual(sum(j.company == "Acme" for j in result["jobs"]), 1)

    def test_adzuna_skipped_for_unsupported_country(self):
        with mock.patch.dict("os.environ", {"ADZUNA_APP_ID": "id", "ADZUNA_APP_KEY": "key"}):
            result = job_search.search_jobs(STUDENT_RESUME, "developer", "ANY", "all")
        self.assertFalse(any("adzuna" in u for u in self.urls))
        self.assertEqual({s.name: s.status for s in result["sources"]}["Adzuna"], "off")

    def test_failed_source_is_reported_not_raised(self):
        with mock.patch.object(job_search, "_http_get_json", side_effect=job_search.SourceError("timeout")):
            result = job_search.search_jobs(STUDENT_RESUME, "python", "IN", "all")
        self.assertEqual(result["jobs"], [])
        self.assertEqual(result["sources"][0].status, "unavailable")

    def test_soft_skills_left_out(self):
        self.assertEqual(job_search.rank_skills(["leadership", "sql", "python"]), ["python", "sql"])


class JobSearchEndpointTests(unittest.TestCase):
    def setUp(self):
        job_search.CACHE.clear()
        patcher = mock.patch.object(job_search, "_http_get_json", side_effect=fake_get([]))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_search(self):
        response = client.post("/api/jobs", json={"resume": RESUME, "query": "python", "country": "IN", "kind": "all"})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(len(body["jobs"]), 2)
        self.assertIn("fit_score", body["jobs"][0])
        self.assertNotIn("text", body["jobs"][0])

    def test_validation(self):
        bad = [
            {"resume": RESUME, "query": "x"},
            {"resume": RESUME, "query": "python", "kind": "freelance"},
            {"resume": RESUME, "query": "python", "country": "ZZ"},
        ]
        for payload in bad:
            self.assertEqual(client.post("/api/jobs", json=payload).status_code, 422, payload)

    def test_empty_resume_rejected(self):
        response = client.post("/api/jobs", json={"resume": {}, "query": "python"})
        self.assertEqual(response.status_code, 422)

    def test_options(self):
        with mock.patch.dict("os.environ", {"ADZUNA_APP_ID": "", "ADZUNA_APP_KEY": ""}):
            body = client.get("/api/jobs/options").json()
        self.assertFalse(body["onsite_enabled"])
        self.assertEqual(body["countries"][0], {"code": "IN", "name": "India", "onsite": False})


if __name__ == "__main__":
    unittest.main()
