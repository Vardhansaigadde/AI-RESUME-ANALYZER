"""Live job and internship search, with the resume's fit score on every posting.

Postings come from free job APIs and are scored locally with the same match
model as /api/analyze. Only the search words, country and job type are sent to
the job sites; the resume never leaves this server.

Sources:
- Himalayas (https://himalayas.app/api): remote jobs worldwide, no key needed.
  Its data refreshes daily, so results are cached for six hours.
- Adzuna (https://developer.adzuna.com): on-site jobs in India and other
  countries. Optional: switched on by the ADZUNA_APP_ID and ADZUNA_APP_KEY
  environment variables (a free developer key). Its API returns only a short
  snippet of each posting, so those fit scores are rougher.

- Remote OK (https://remoteok.com/api): remote jobs, no key needed. Its terms
  ask for a followed link back and naming "Remote OK" as the source.
- Arbeitnow (https://www.arbeitnow.com/api/job-board-api): jobs in Europe,
  mostly Germany, no key needed. It has no search, so the newest 300 postings
  are cached for an hour and filtered here. Shown for Germany and Anywhere.
- Jooble (https://jooble.org/api/about): on-site jobs in India and elsewhere.
  Optional: switched on by the JOOBLE_API_KEY environment variable (free key).
  Like Adzuna it returns only a snippet of each posting.

Every source asks that each posting links back to it and names it as the
source, which the frontend does (plain links, no rel="nofollow").
"""

from __future__ import annotations

from collections import Counter, OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import lru_cache
import html
import json
import logging
import os
import re
import threading
import time
from typing import Any
from urllib.parse import urlencode
import urllib.request

from app.schemas.jobs import JobPosting, JobSource, SkillDemand
from app.services.data_cleaning import clean_text
from app.services.matcher import match_resume_to_job
from app.services.role_gap import TARGET_ROLES_PATH
from app.services.skill_extractor import extract_skills
from app.services.skills_inventory import DOMAIN_GROUP, SOFT_GROUP, group_of

logger = logging.getLogger(__name__)

USER_AGENT = "FitLens/1.0 (+https://resumefitlens.vercel.app)"
HTTP_TIMEOUT = 10  # seconds per request to a job site
MAX_JOB_WORDS = 800  # longer postings are cut before scoring (keeps a search to a few seconds)
RESULTS_PER_SOURCE = 20
DEMAND_TOP = 12  # skills shown in "what these openings ask for"
DEMAND_MIN_JOBS = 3  # fewer postings say little about demand

# Countries offered in the UI. Adzuna covers only some of them.
COUNTRIES = {
    "IN": "India",
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "DE": "Germany",
    "SG": "Singapore",
    "AE": "United Arab Emirates",
}
ANYWHERE = "ANY"
ADZUNA_COUNTRIES = {"IN", "US", "GB", "CA", "AU", "DE", "SG"}
CURRENCY = {"IN": "₹", "US": "$", "GB": "£", "CA": "C$", "AU": "A$", "DE": "€", "SG": "S$"}

HIMALAYAS_URL = "https://himalayas.app/jobs/api/search"
ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"
REMOTEOK_URL = "https://remoteok.com/api"
ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"
JOOBLE_URL = "https://jooble.org/api/{key}"
ARBEITNOW_COUNTRIES = {"DE", ANYWHERE}
FEED_TTL = 3600  # Remote OK and Arbeitnow feeds, shared by every search

# Query words that say what kind of job, not what it is about
GERMAN_PLACES = frozenset(
    "germany deutschland berlin munich münchen hamburg frankfurt cologne köln stuttgart düsseldorf leipzig "
    "dresden hannover nuremberg nürnberg bremen essen dortmund bonn karlsruhe mannheim".split()
)
QUERY_FILLER = frozenset("job jobs role roles remote fresher freshers entry level intern internship trainee".split())

# Titles that are clearly not for students or freshers
SENIOR_TITLE = re.compile(
    r"\b(senior|sr\.?|lead|principal|staff|manager|head|director|architect|vp|chief)\b", re.IGNORECASE
)
INTERN_TITLE = re.compile(
    r"\b(intern|interns|internship|trainee|apprentice|apprenticeship|werkstudent)\b", re.IGNORECASE
)


class SourceError(Exception):
    """A job site could not be reached or returned something unusable."""


class _TTLCache:
    """Small thread-safe cache of search results, so popular searches hit the job sites rarely."""

    def __init__(self, max_entries: int = 256) -> None:
        self._data: OrderedDict[tuple, tuple[float, list[dict]]] = OrderedDict()
        self._lock = threading.Lock()
        self.max_entries = max_entries

    def get(self, key: tuple, ttl: float) -> list[dict] | None:
        with self._lock:
            hit = self._data.get(key)
            if hit is None or time.monotonic() - hit[0] > ttl:
                return None
            return hit[1]

    def put(self, key: tuple, value: list[dict]) -> None:
        with self._lock:
            self._data[key] = (time.monotonic(), value)
            self._data.move_to_end(key)
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


CACHE = _TTLCache()


def _http_get_json(url: str) -> Any:
    """GET a JSON document (patched in tests)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:  # noqa: S310 (fixed https URLs)
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # network errors, HTTP 4xx/5xx, bad JSON
        raise SourceError(str(exc)) from exc


def _http_post_json(url: str, payload: dict) -> Any:
    """POST JSON and read JSON back (patched in tests). The URL may hold a key, so it is never logged."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:  # noqa: S310 (fixed https URL)
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise SourceError(type(exc).__name__ + (f" {exc.code}" if hasattr(exc, "code") else "")) from exc


def matches_query(query: str, *texts: str) -> bool:
    """Every meaningful query word appears in these texts (for feeds that can't be searched).

    Callers pass the title and tags only: a description mentions too much (a Vue role
    "works alongside our Python team") to say what the job is.
    """
    words = [w for w in clean_text(query).split() if w not in QUERY_FILLER]
    if not words:  # e.g. "internship": only the kind of job was asked for
        return not INTERN_TITLE.search(query) or bool(INTERN_TITLE.search(" ".join(texts)))
    have = set(clean_text(" ".join(texts)).split())
    return all(w in have for w in words)


def _feed(url: str) -> Any:
    """A whole-feed download shared by every search for FEED_TTL seconds."""
    key = ("feed", url)
    cached = CACHE.get(key, FEED_TTL)
    if cached is not None:
        return cached
    data = _http_get_json(url)
    CACHE.put(key, data)
    return data


def html_to_text(raw: str) -> str:
    """Plain text from a posting's HTML description."""
    text = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", raw or "", flags=re.IGNORECASE)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\s*\n\s*", "\n", text).strip()


def _excerpt(text: str, limit: int = 220) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[:limit].rsplit(" ", 1)[0] + "…"


def _iso_date(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        if isinstance(value, int | float) or str(value).isdigit():
            return datetime.fromtimestamp(int(value), tz=UTC).date().isoformat()
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except ValueError, OverflowError, OSError:
        return ""


def _money(value: Any, symbol: str) -> str:
    amount = float(value)
    if symbol == "₹" and amount >= 100_000:
        return f"{amount / 100_000:.1f} L"  # lakh, as Indian postings quote pay
    if amount >= 10_000:
        return f"{amount / 1000:,.0f}k"
    return f"{amount:,.0f}"


def _salary(low: Any, high: Any, symbol: str, period: str = "") -> str:
    try:
        lo = float(low) if low not in (None, "") else None
        hi = float(high) if high not in (None, "") else None
    except TypeError, ValueError:
        return ""
    if not lo and not hi:
        return ""
    parts = list(dict.fromkeys(_money(v, symbol) for v in (lo, hi) if v))
    text = symbol + " – ".join(parts)
    return f"{text} / {period}" if period else text


# --------------------------------------------------------------------------- sources


def adzuna_keys() -> tuple[str, str] | None:
    app_id = os.getenv("ADZUNA_APP_ID", "").strip()
    app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
    return (app_id, app_key) if app_id and app_key else None


def fetch_himalayas(query: str, country: str, kind: str) -> list[dict]:
    params: dict[str, str] = {"q": query, "sort": "relevant"}
    if country != ANYWHERE:
        params["country"] = country
    if kind == "internship":
        params["employment_type"] = "Intern"
    elif kind == "entry":
        params["seniority"] = "Entry-level"
    data = _http_get_json(f"{HIMALAYAS_URL}?{urlencode(params)}")
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise SourceError("unexpected response")

    postings = []
    for job in data["jobs"][:RESULTS_PER_SOURCE]:
        url = job.get("applicationLink") or job.get("guid") or ""
        title = (job.get("title") or "").strip()
        if not url or not title:
            continue
        places = job.get("locationRestrictions") or []
        text = html_to_text(job.get("description") or job.get("excerpt") or "")
        seniority = job.get("seniority") or []
        postings.append(
            {
                "id": f"himalayas:{job.get('guid') or url}",
                "title": title,
                "company": (job.get("companyName") or "").strip(),
                "location": "Remote · " + (", ".join(places[:3]) if places else "Worldwide"),
                "remote": True,
                "employment_type": job.get("employmentType") or "",
                "level": seniority[0] if seniority else "",
                "posted": _iso_date(job.get("pubDate")),
                "salary": _salary(
                    job.get("minSalary"),
                    job.get("maxSalary"),
                    (job.get("currency") or "") + " " if job.get("currency") else "",
                    "year" if job.get("salaryPeriod") == "annual" else (job.get("salaryPeriod") or ""),
                ),
                "url": url,
                "source": "Himalayas",
                "text": text,
                "short_description": False,
            }
        )
    return postings


def fetch_adzuna(query: str, country: str, kind: str) -> list[dict]:
    keys = adzuna_keys()
    if keys is None:
        return []
    params = {
        "app_id": keys[0],
        "app_key": keys[1],
        "what": query,
        "results_per_page": str(RESULTS_PER_SOURCE),
        "max_days_old": "45",
        "content-type": "application/json",
    }
    if kind == "internship":
        params["what_or"] = "intern internship trainee apprentice"
    url = ADZUNA_URL.format(country=country.lower()) + "?" + urlencode(params)
    data = _http_get_json(url)
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise SourceError("unexpected response")

    postings = []
    for job in data["results"]:
        title = html_to_text(job.get("title") or "")
        link = job.get("redirect_url") or ""
        if not title or not link:
            continue
        contract = " ".join(
            filter(None, [(job.get("contract_time") or "").replace("_", " "), job.get("contract_type") or ""])
        )
        postings.append(
            {
                "id": f"adzuna:{job.get('id') or link}",
                "title": title,
                "company": ((job.get("company") or {}).get("display_name") or "").strip(),
                "location": ((job.get("location") or {}).get("display_name") or "").strip(),
                "remote": False,
                "employment_type": contract.capitalize(),
                "level": "",
                "posted": _iso_date(job.get("created")),
                "salary": ""
                if str(job.get("salary_is_predicted")) == "1"
                else _salary(job.get("salary_min"), job.get("salary_max"), CURRENCY.get(country, ""), "year"),
                "url": link,
                "source": "Adzuna",
                "text": html_to_text(job.get("description") or ""),
                "short_description": True,
            }
        )
    return postings


def _remoteok_tag(query: str) -> str:
    """Remote OK filters by tag: use the first skill in the query ("python developer" -> python)."""
    skills = sorted(extract_skills(clean_text(query)))
    return skills[0].replace(" ", "-") if skills else ""


def fetch_remoteok(query: str, country: str, kind: str) -> list[dict]:
    tag = _remoteok_tag(query)
    data = _feed(f"{REMOTEOK_URL}?{urlencode({'tag': tag})}" if tag else REMOTEOK_URL)
    if not isinstance(data, list):
        raise SourceError("unexpected response")
    place = COUNTRIES.get(country, "").lower()

    postings = []
    for job in data:
        if not isinstance(job, dict) or "position" not in job:
            continue  # the first item is Remote OK's terms notice
        title = (job.get("position") or "").strip()
        url = job.get("url") or ""
        if not title or not url:
            continue
        location = (job.get("location") or "").strip()
        if (
            country != ANYWHERE
            and location
            and not any(word in location.lower() for word in ("worldwide", "anywhere", "global", place))
        ):
            continue
        tags = [str(t) for t in job.get("tags") or []]
        if not matches_query(query, title, " ".join(tags)):
            continue
        if location.lower() in ("remote", "anywhere"):
            location = ""
        text = html_to_text(job.get("description") or "")
        postings.append(
            {
                "id": f"remoteok:{job.get('id') or url}",
                "title": title,
                "company": (job.get("company") or "").strip(),
                "location": "Remote · " + (location or "Worldwide"),
                "remote": True,
                "employment_type": "",
                "level": "",
                "posted": _iso_date(job.get("epoch") or job.get("date")),
                "salary": _salary(job.get("salary_min"), job.get("salary_max"), "$", "year"),
                "url": url,
                "source": "Remote OK",
                "text": text,
                "short_description": False,
            }
        )
        if len(postings) >= RESULTS_PER_SOURCE:
            break
    return postings


def fetch_arbeitnow(query: str, country: str, kind: str) -> list[dict]:
    data = _feed(ARBEITNOW_URL)
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise SourceError("unexpected response")

    postings = []
    for job in data["data"]:
        title = (job.get("title") or "").strip()
        url = job.get("url") or ""
        if not title or not url:
            continue
        tags = [str(t) for t in job.get("tags") or []]
        if not matches_query(query, title, " ".join(tags)):
            continue
        remote = job.get("remote") is True
        location = (job.get("location") or "").strip()
        if location.lower() == "remote":
            location = ""
        if country == "DE" and not (remote or set(location.lower().replace(",", " ").split()) & GERMAN_PLACES):
            continue
        text = html_to_text(job.get("description") or "")
        types = [str(t) for t in job.get("job_types") or []]
        postings.append(
            {
                "id": f"arbeitnow:{job.get('slug') or url}",
                "title": title,
                "company": (job.get("company_name") or "").strip(),
                "location": ("Remote · " if remote else "") + (location or "Europe"),
                "remote": remote,
                "employment_type": ", ".join(types),
                "level": "",
                "posted": _iso_date(job.get("created_at")),
                "salary": "",
                "url": url,
                "source": "Arbeitnow",
                "text": text,
                "short_description": False,
            }
        )
        if len(postings) >= RESULTS_PER_SOURCE:
            break
    return postings


def jooble_key() -> str:
    return os.getenv("JOOBLE_API_KEY", "").strip()


def fetch_jooble(query: str, country: str, kind: str) -> list[dict]:
    key = jooble_key()
    if not key:
        return []
    payload = {
        "keywords": f"{query} internship" if kind == "internship" else query,
        "location": "" if country == ANYWHERE else COUNTRIES.get(country, ""),
        "page": "1",
    }
    data = _http_post_json(JOOBLE_URL.format(key=key), payload)
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise SourceError("unexpected response")

    postings = []
    for job in data["jobs"][:RESULTS_PER_SOURCE]:
        title = html_to_text(job.get("title") or "")
        link = job.get("link") or ""
        if not title or not link:
            continue
        postings.append(
            {
                "id": f"jooble:{job.get('id') or link}",
                "title": title,
                "company": (job.get("company") or "").strip(),
                "location": (job.get("location") or "").strip(),
                "remote": False,
                "employment_type": (job.get("type") or "").strip(),
                "level": "",
                "posted": _iso_date((job.get("updated") or "")[:19]),
                "salary": (job.get("salary") or "").strip(),
                "url": link,
                "source": "Jooble",
                "text": html_to_text(job.get("snippet") or ""),
                "short_description": True,
            }
        )
    return postings


SOURCES = {
    "Himalayas": {"fetch": fetch_himalayas, "url": "https://himalayas.app", "ttl": 6 * 3600},
    "Remote OK": {"fetch": fetch_remoteok, "url": "https://remoteok.com", "ttl": FEED_TTL},
    "Adzuna": {"fetch": fetch_adzuna, "url": "https://www.adzuna.com", "ttl": 3600},
    "Jooble": {"fetch": fetch_jooble, "url": "https://jooble.org", "ttl": 3600},
    "Arbeitnow": {"fetch": fetch_arbeitnow, "url": "https://www.arbeitnow.com", "ttl": FEED_TTL},
}
ONSITE_SOURCES = ("Adzuna", "Jooble")


def _source_off_reason(name: str, country: str) -> str:
    if name == "Adzuna":
        if adzuna_keys() is None:
            return "On-site jobs are not set up on this server."
        if country not in ADZUNA_COUNTRIES:
            return "On-site jobs aren't available for this location."
    if name == "Jooble" and not jooble_key():
        return "Jooble isn't set up on this server."
    if name == "Arbeitnow" and country not in ARBEITNOW_COUNTRIES:
        return "Only has jobs in Europe, mostly Germany."
    return ""


def _fetch_cached(name: str, query: str, country: str, kind: str) -> list[dict]:
    source = SOURCES[name]
    key = (name, query.lower(), country, kind)
    cached = CACHE.get(key, source["ttl"])
    if cached is not None:
        return cached
    postings = source["fetch"](query, country, kind)
    CACHE.put(key, postings)
    return postings


# --------------------------------------------------------------------------- search


@lru_cache(maxsize=1)
def _role_skills() -> frozenset[str]:
    """Every core skill of a target role (app/data/target_roles.json)."""
    roles = json.loads(TARGET_ROLES_PATH.read_text(encoding="utf-8"))["roles"] if TARGET_ROLES_PATH.exists() else {}
    return frozenset(skill for skills in roles.values() for skill in skills)


def is_relevant(skill: str) -> bool:
    """Worth showing on a job card: no soft skills, and domain words only when a role lists them.

    The catch-all domain group holds both real skills ("accounting", "seo") and words
    that appear in almost any posting ("reporting", "research", "management").
    """
    group = group_of(skill)
    if group == SOFT_GROUP:
        return False
    return group != DOMAIN_GROUP or skill in _role_skills()


def rank_skills(skills: list[str]) -> list[str]:
    """Technical skills first, then domain skills; generic and soft skills are left out."""
    return sorted((s for s in skills if is_relevant(s)), key=lambda s: (group_of(s) == DOMAIN_GROUP, s))


def _keep(posting: dict, kind: str) -> bool:
    title = posting["title"]
    if kind == "internship":
        return "intern" in posting["employment_type"].lower() or bool(INTERN_TITLE.search(title))
    if kind == "entry":
        return not SENIOR_TITLE.search(title)
    return True


def search_jobs(resume_text: str | None, query: str, country: str, kind: str) -> dict[str, Any]:
    """Fetch live postings from every enabled source and score the resume against each one."""
    query = " ".join(query.split())
    country = country.upper()

    sources: list[JobSource] = []
    enabled = []
    for name, source in SOURCES.items():
        reason = _source_off_reason(name, country)
        if reason:
            sources.append(JobSource(name=name, url=source["url"], status="off", note=reason))
        else:
            enabled.append(name)

    found: dict[str, list[dict] | Exception] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(enabled))) as pool:
        futures = {name: pool.submit(_fetch_cached, name, query, country, kind) for name in enabled}
        for name, future in futures.items():
            try:
                found[name] = future.result()
            except Exception as exc:
                logger.warning("Job source %s failed: %s", name, exc)
                found[name] = exc

    postings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for name in enabled:
        result = found[name]
        if isinstance(result, Exception):
            sources.append(
                JobSource(
                    name=name,
                    url=SOURCES[name]["url"],
                    status="unavailable",
                    note="Couldn't reach it, try again later.",
                )
            )
            continue
        kept = 0
        for posting in result:
            dedupe = (posting["title"].lower(), posting["company"].lower())
            if dedupe in seen or not _keep(posting, kind):
                continue
            seen.add(dedupe)
            postings.append(posting)
            kept += 1
        sources.append(JobSource(name=name, url=SOURCES[name]["url"], status="ok", count=kept))

    jobs = []
    for posting in postings:
        job_text = " ".join(f"{posting['title']}\n{posting['text']}".split(" ")[:MAX_JOB_WORDS])
        if resume_text:
            scored = match_resume_to_job(resume_text=resume_text, job_text=job_text)
        else:
            # No resume: list the skills the posting asks for
            asked = sorted(extract_skills(clean_text(job_text)))
            scored = {"match_score": None, "matched_skills": [], "missing_skills": asked}
        jobs.append(
            JobPosting(
                **{k: v for k, v in posting.items() if k != "text"},
                excerpt=_excerpt(posting["text"]),
                fit_score=scored["match_score"],
                matched_skills=rank_skills(scored["matched_skills"]),
                missing_skills=rank_skills(scored["missing_skills"]),
            )
        )
    if resume_text:
        jobs.sort(key=lambda j: (-(j.fit_score or 0), j.title))
    else:
        jobs.sort(key=lambda j: j.posted, reverse=True)

    order = list(SOURCES)
    sources.sort(key=lambda s: order.index(s.name))
    return {
        "query": query,
        "country": country,
        "kind": kind,
        "jobs": jobs,
        "sources": sources,
        "scored": bool(resume_text),
        "skill_demand": skill_demand(jobs),
    }


def skill_demand(jobs: list[JobPosting], top: int = DEMAND_TOP) -> list[SkillDemand]:
    """The skills these postings ask for most, and whether the resume has them."""
    if len(jobs) < DEMAND_MIN_JOBS:
        return []
    counts: Counter[str] = Counter()
    have: set[str] = set()
    for job in jobs:
        counts.update(set(job.matched_skills) | set(job.missing_skills))
        have.update(job.matched_skills)
    # Most common first; ties alphabetically so results are stable
    common = sorted(((s, n) for s, n in counts.items() if n >= 2), key=lambda x: (-x[1], x[0]))[:top]
    return [SkillDemand(skill=s, count=n, share=round(n / len(jobs), 3), have=s in have) for s, n in common]
