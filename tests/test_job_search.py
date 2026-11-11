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


REMOTEOK = [
    {"legal": "API Terms of Service: please link back to Remote OK."},
    {
        "id": "7",
        "position": "Junior Python Developer",
        "company": "Snake Co",
        "location": "Worldwide",
        "tags": ["python", "django"],
        "description": "<p>Build APIs with Python and Django.</p>",
        "epoch": "1790000000",
        "salary_min": "40000",
        "salary_max": "60000",
        "url": "https://remoteOK.com/remote-jobs/7",
    },
    {  # restricted to another country: left out for India
        "id": "8",
        "position": "Python Engineer",
        "company": "Euro Co",
        "location": "Warsaw",
        "tags": ["python"],
        "description": "Python",
        "url": "https://remoteOK.com/remote-jobs/8",
    },
    {  # doesn't mention the query
        "id": "9",
        "position": "Designer",
        "company": "Pixel",
        "location": "",
        "tags": ["figma"],
        "description": "Figma",
        "url": "https://remoteOK.com/remote-jobs/9",
    },
]

ARBEITNOW = {
    "data": [
        {
            "slug": "werkstudent-python",
            "company_name": "Berlin Labs",
            "title": "Werkstudent Python Developer (m/w/d)",
            "description": "<p>Python, SQL and Docker.</p>",
            "remote": False,
            "url": "https://www.arbeitnow.com/jobs/companies/berlin-labs/werkstudent-python",
            "tags": ["IT"],
            "job_types": ["Internship"],
            "location": "Berlin",
            "created_at": 1790000000,
        },
        {
            "slug": "sales",
            "company_name": "Shop",
            "title": "Account Executive",
            "description": "Sales",
            "remote": False,
            "url": "https://www.arbeitnow.com/jobs/companies/shop/sales",
            "location": "Munich",
        },
    ]
}

JOOBLE = {
    "totalCount": 1,
    "jobs": [
        {
            "id": 99,
            "title": "Python Developer <b>Fresher</b>",
            "company": "Hyd Soft",
            "location": "Hyderabad, Telangana",
            "snippet": "&nbsp;Python, Django and SQL...",
            "salary": "₹3 - 5 LPA",
            "type": "Full-time",
            "link": "https://jooble.org/desc/99",
            "updated": "2026-10-01T10:00:00.0000000",
        },
        {  # mentions python only in passing: not a Python job
            "id": 100,
            "title": "Sr Engineer - Paint Simulation",
            "company": "AutoCo",
            "snippet": "CFD and paint simulation; scripting in Python is a plus.",
            "link": "https://jooble.org/desc/100",
        },
    ],
}


def fake_get(urls_seen):
    def get(url):
        urls_seen.append(url)
        if url.startswith(job_search.HIMALAYAS_URL):
            return HIMALAYAS
        if "adzuna" in url:
            return ADZUNA
        if url.startswith(job_search.REMOTEOK_URL):
            return REMOTEOK
        if url.startswith(job_search.ARBEITNOW_URL):
            return ARBEITNOW
        raise AssertionError(url)

    return get


def himalayas_urls(urls):
    return [u for u in urls if u.startswith(job_search.HIMALAYAS_URL)]


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
        self.assertEqual(len([j for j in result["jobs"] if j.source == "Himalayas"]), 2)
        sources = {s.name: s for s in result["sources"]}
        self.assertEqual(sources["Himalayas"].status, "ok")
        self.assertEqual(sources["Adzuna"].status, "off")
        self.assertEqual(len(himalayas_urls(self.urls)), 1)
        params = parse_qs(urlparse(himalayas_urls(self.urls)[0]).query)
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
        self.assertEqual([j.company for j in interns["jobs"]], ["Acme"])  # Arbeitnow's posting isn't "software"
        params = parse_qs(urlparse(himalayas_urls(self.urls)[0]).query)
        self.assertEqual(params["employment_type"], ["Intern"])
        self.assertNotIn("country", params)

        job_search.CACHE.clear()
        entry = job_search.search_jobs(STUDENT_RESUME, "software", "ANY", "entry")
        self.assertNotIn("Bigco", [j.company for j in entry["jobs"]])
        self.assertEqual(parse_qs(urlparse(himalayas_urls(self.urls)[-1]).query)["seniority"], ["Entry-level"])

    def test_results_are_cached(self):
        job_search.search_jobs(STUDENT_RESUME, "Python", "IN", "all")
        job_search.search_jobs(STUDENT_RESUME, "python", "IN", "all")
        self.assertEqual(len(himalayas_urls(self.urls)), 1)

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

    def test_remoteok_postings(self):
        result = job_search.search_jobs(STUDENT_RESUME, "python developer", "IN", "all")
        remote_ok = [j for j in result["jobs"] if j.source == "Remote OK"]
        self.assertEqual([j.company for j in remote_ok], ["Snake Co"])  # no notice, no Warsaw, no designer
        self.assertEqual(remote_ok[0].location, "Remote · Worldwide")
        self.assertEqual(remote_ok[0].salary, "$40k – 60k / year")
        self.assertIn("https://remoteok.com/api?tag=python", self.urls)

    def test_arbeitnow_only_for_germany_and_anywhere(self):
        india = job_search.search_jobs(STUDENT_RESUME, "python", "IN", "all")
        self.assertEqual({s.name: s.status for s in india["sources"]}["Arbeitnow"], "off")
        self.assertFalse(any("arbeitnow" in u for u in self.urls))
        germany = job_search.search_jobs(STUDENT_RESUME, "python", "DE", "all")
        self.assertEqual([j.company for j in germany["jobs"] if j.source == "Arbeitnow"], ["Berlin Labs"])

    def test_feeds_are_downloaded_once_for_all_searches(self):
        job_search.search_jobs(STUDENT_RESUME, "python", "ANY", "all")
        job_search.search_jobs(STUDENT_RESUME, "python sql", "ANY", "all")
        self.assertEqual(sum("arbeitnow" in u for u in self.urls), 1)

    def test_jooble_needs_a_key_and_hides_it(self):
        with mock.patch.dict("os.environ", {"JOOBLE_API_KEY": ""}):
            off = job_search.search_jobs(STUDENT_RESUME, "python", "IN", "all")
        self.assertEqual({s.name: s.status for s in off["sources"]}["Jooble"], "off")

        job_search.CACHE.clear()
        posted = []

        def fake_post(url, payload):
            posted.append((url, payload))
            return JOOBLE

        with (
            mock.patch.dict("os.environ", {"JOOBLE_API_KEY": "secret-key"}),
            mock.patch.object(job_search, "_http_post_json", side_effect=fake_post),
        ):
            result = job_search.search_jobs(STUDENT_RESUME, "python", "IN", "internship")
        self.assertEqual(posted[0][0], "https://jooble.org/api/secret-key")
        self.assertEqual(posted[0][1]["location"], "India")
        self.assertEqual(posted[0][1]["keywords"], "python internship")
        self.assertFalse(
            any(j.source == "Jooble" for j in result["jobs"])
        )  # "Python Developer Fresher" is not an internship title

        job_search.CACHE.clear()
        with (
            mock.patch.dict("os.environ", {"JOOBLE_API_KEY": "secret-key"}),
            mock.patch.object(job_search, "_http_post_json", side_effect=fake_post),
        ):
            result = job_search.search_jobs(STUDENT_RESUME, "python", "IN", "all")
        jooble = [j for j in result["jobs"] if j.source == "Jooble"]
        self.assertEqual([j.company for j in jooble], ["Hyd Soft"])  # the paint-simulation role is left out
        jooble = jooble[0]
        self.assertEqual(jooble.title, "Python Developer Fresher")
        self.assertEqual(jooble.salary, "₹3 - 5 LPA")
        self.assertEqual(jooble.posted, "2026-10-01")
        self.assertTrue(jooble.short_description)

    def test_query_matching(self):
        self.assertTrue(job_search.matches_query("python developer jobs", "Junior Python Developer"))
        self.assertFalse(job_search.matches_query("data analyst", "Data Engineer"))
        self.assertTrue(job_search.matches_query("remote jobs", "Anything"))
        self.assertTrue(job_search.matches_query("internship", "Growth Strategy Intern"))
        self.assertFalse(job_search.matches_query("internship", "Account Executive"))

    def test_germany_keeps_german_places(self):
        job_search.CACHE.clear()
        london = {**ARBEITNOW["data"][0], "slug": "london", "company_name": "Tea Co", "location": "London"}
        with mock.patch.dict(ARBEITNOW, {"data": [*ARBEITNOW["data"], london]}):
            germany = job_search.search_jobs(STUDENT_RESUME, "python", "DE", "all")
        self.assertEqual([j.company for j in germany["jobs"] if j.source == "Arbeitnow"], ["Berlin Labs"])

    def test_soft_skills_left_out(self):
        self.assertEqual(job_search.rank_skills(["leadership", "sql", "python"]), ["python", "sql"])

    def test_generic_domain_words_left_out(self):
        # "accounting" is a real skill (a target role lists it); "reporting" is noise
        self.assertEqual(job_search.rank_skills(["reporting", "accounting", "sql"]), ["sql", "accounting"])


def _posting(matched, missing):
    return job_search.JobPosting(
        id=str(matched + missing),
        title="t",
        company="c",
        url="https://example.com",
        source="Himalayas",
        fit_score=50,
        matched_skills=matched,
        missing_skills=missing,
    )


class SkillDemandTests(unittest.TestCase):
    def test_counts_share_and_have(self):
        jobs = [
            _posting(["python"], ["sql", "aws"]),
            _posting(["python"], ["sql"]),
            _posting([], ["sql", "docker"]),
            _posting(["python"], ["docker"]),
        ]
        demand = job_search.skill_demand(jobs)
        self.assertEqual([(d.skill, d.count) for d in demand], [("python", 3), ("sql", 3), ("docker", 2)])
        self.assertEqual(demand[0].share, 0.75)
        self.assertTrue(demand[0].have)
        self.assertFalse(demand[1].have)

    def test_needs_enough_postings(self):
        self.assertEqual(job_search.skill_demand([_posting(["python"], []), _posting(["python"], [])]), [])

    def test_search_returns_demand(self):
        job_search.CACHE.clear()
        with mock.patch.object(job_search, "_http_get_json", side_effect=fake_get([])):
            result = job_search.search_jobs(STUDENT_RESUME, "sql", "IN", "all")
        self.assertIn("skill_demand", result)  # two postings: too few to report
        self.assertEqual(result["skill_demand"], [])


class JobSearchEndpointTests(unittest.TestCase):
    def setUp(self):
        job_search.CACHE.clear()
        patcher = mock.patch.object(job_search, "_http_get_json", side_effect=fake_get([]))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_search(self):
        response = client.post("/api/jobs", json={"resume": RESUME, "query": "sql", "country": "IN", "kind": "all"})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(len(body["jobs"]), 2)  # Himalayas' two; Remote OK's posting isn't about SQL
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
        with mock.patch.dict("os.environ", {"ADZUNA_APP_ID": "", "ADZUNA_APP_KEY": "", "JOOBLE_API_KEY": ""}):
            body = client.get("/api/jobs/options").json()
        self.assertFalse(body["onsite_enabled"])
        self.assertEqual(body["countries"][0], {"code": "IN", "name": "India", "onsite": False})


if __name__ == "__main__":
    unittest.main()
