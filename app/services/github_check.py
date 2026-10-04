"""GitHub proof check: which resume skills public repositories back up.

Recruiters open a student's GitHub to see whether the skills on the resume are
real. This compares the two: skills a repository shows (its language, topics,
name and description), technical resume skills no public repository shows,
skills the repositories show that the resume leaves out, and a few profile
habits that make a GitHub worth opening.

The repositories come from the browser (GitHub's public API); nothing here
calls GitHub.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import lru_cache
import json
from pathlib import Path
import re

from app.schemas.github import (
    GithubCheckItem,
    GithubProfile,
    GithubRepo,
    GithubStats,
    SkillEvidence,
)
from app.schemas.resume import StructuredResume
from app.services.data_cleaning import clean_text
from app.services.resume_sections import render_resume_text
from app.services.skill_extractor import SKILL_ALIASES, extract_skills
from app.services.skills_inventory import group_of

SKILLS_PATH = Path(__file__).resolve().parent.parent / "data" / "skills_list.json"

# Skills a public repository can actually show
PROVABLE_GROUPS = {"Programming languages", "Web & frameworks", "Data & AI", "Databases", "Cloud & DevOps"}

# GitHub language names that aren't skill names
LANGUAGE_SKILLS = {
    "jupyter notebook": "python",
    "shell": "bash",
    "dockerfile": "docker",
    "hcl": "terraform",
    "scss": "css",
    "less": "css",
    "plpgsql": "postgresql",
    "tsql": "sql",
}

RECENT = timedelta(days=183)
VERY_RECENT = timedelta(days=90)


@lru_cache(maxsize=1)
def _taxonomy() -> frozenset[str]:
    return frozenset(s.strip().lower() for s in json.loads(SKILLS_PATH.read_text(encoding="utf-8")))


def tag_to_skill(tag: str) -> str | None:
    """A repository topic or language as a canonical skill ("machine-learning" -> "machine learning")."""
    name = re.sub(r"[-_]+", " ", tag.strip().lower())
    if name in LANGUAGE_SKILLS:
        return LANGUAGE_SKILLS[name]
    if name in _taxonomy():
        return name
    return SKILL_ALIASES.get(name) or SKILL_ALIASES.get(name.replace(" ", ""))


def repo_skills(repo: GithubRepo) -> set[str]:
    """Skills a repository shows through its language, topics, name and description."""
    skills = {s for s in (tag_to_skill(t) for t in [*repo.topics, repo.language or ""] if t) if s}
    words = re.sub(r"[-_]+", " ", repo.name)
    skills |= extract_skills(clean_text(f"{words}. {repo.description or ''}"))
    return skills


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _count(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def _evidence(skill_repos: dict[str, list[str]], skills: list[str]) -> list[SkillEvidence]:
    return [SkillEvidence(skill=s, repos=skill_repos[s][:3]) for s in skills]


def _checks(
    profile: GithubProfile, own: list[GithubRepo], resume: StructuredResume, now: datetime
) -> list[GithubCheckItem]:
    checks: list[GithubCheckItem] = []

    def add(check_id: str, title: str, status: str, detail: str, tip: str = "") -> None:
        checks.append(GithubCheckItem(id=check_id, title=title, status=status, detail=detail, tip=tip))

    n = len(own)
    add(
        "repos",
        "Your own projects",
        "pass" if n >= 3 else "warn" if n else "fail",
        f"{_count(n, 'public repository', 'public repositories')} of your own (not forks).",
        "" if n >= 3 else "Recruiters look for 2-3 solid projects. Make your best coursework or side projects public.",
    )

    pushes = [t for t in (_parse_time(r.pushed_at) for r in own) if t]
    latest = max(pushes, default=None)
    if latest and now - latest <= VERY_RECENT:
        add("activity", "Recent activity", "pass", f"Last push {latest.date().isoformat()}.")
    else:
        add(
            "activity",
            "Recent activity",
            "warn" if latest and now - latest <= RECENT else "fail",
            f"Last push {latest.date().isoformat()}." if latest else "No pushes found.",
            "An active profile reads as a learning one: push to a project at least every few weeks.",
        )

    described = sum(bool((r.description or "").strip()) for r in own)
    if n:
        add(
            "descriptions",
            "Repository descriptions",
            "pass" if described >= 0.8 * n else "warn",
            f"{described} of {n} repositories have a one-line description.",
            "" if described >= 0.8 * n else "Add a one-line description to each repo: what it does and the stack.",
        )
        tagged = sum(bool(r.topics) for r in own)
        add(
            "topics",
            "Topics (tags)",
            "pass" if tagged >= n / 2 else "warn",
            f"{tagged} of {n} repositories have topics.",
            "" if tagged >= n / 2 else "Add topics such as python, react or machine-learning so skills are visible.",
        )
        demos = sum(bool((r.homepage or "").strip()) for r in own)
        add(
            "demo",
            "Live demo links",
            "pass" if demos else "warn",
            f"{_count(demos, 'repository links', 'repositories link')} to a live demo."
            if demos
            else "No repository links to a live demo.",
            ""
            if demos
            else "Deploy one project (Vercel, Netlify, GitHub Pages, Render) and set it as the repo website.",
        )

    has_readme = any(r.name.lower() == profile.login.lower() for r in own)
    add(
        "profile-readme",
        "Profile README",
        "pass" if has_readme else "warn",
        "You have a profile README." if has_readme else "No profile README.",
        ""
        if has_readme
        else f"Create a public repo named {profile.login} with a README: who you are, your stack "
        "and your best projects. It shows at the top of your profile.",
    )
    filled = bool((profile.name or "").strip()) and bool((profile.bio or "").strip())
    add(
        "bio",
        "Name and bio",
        "pass" if filled else "warn",
        "Your profile has a name and a bio." if filled else "Your profile is missing a name or a bio.",
        "" if filled else "Add your full name and a one-line bio such as 'CS student · Python & React'.",
    )
    linked = any(f"github.com/{profile.login.lower()}" in link.lower() for link in resume.links)
    add(
        "resume-link",
        "Linked from your resume",
        "pass" if linked else "warn",
        "Your resume links to this profile." if linked else "Your resume doesn't link to this profile.",
        "" if linked else f"Add github.com/{profile.login} next to your email in the resume header.",
    )
    return checks


def check_github(
    resume: StructuredResume, profile: GithubProfile, repos: list[GithubRepo], now: datetime | None = None
) -> dict:
    """Compare a resume's skills with what the public repositories show."""
    now = now or datetime.now(UTC)
    own = [r for r in repos if not r.fork]
    forks = len(repos) - len(own)

    # Most-starred, then most recent repos first, so evidence lists the best ones
    ordered = sorted(own, key=lambda r: (r.stargazers_count, r.pushed_at or ""), reverse=True)
    skill_repos: dict[str, list[str]] = {}
    for repo in ordered:
        for skill in sorted(repo_skills(repo)):
            skill_repos.setdefault(skill, []).append(repo.name)

    # Items in the Skills section are skills by definition, even without the context
    # words the free-text extractor needs for ambiguous names such as "React" or "Go"
    resume_skills = extract_skills(clean_text(render_resume_text(resume)))
    resume_skills |= {s for s in (tag_to_skill(item) for item in resume.skills) if s}
    provable = sorted(s for s in resume_skills if group_of(s) in PROVABLE_GROUPS)
    shown = set(skill_repos)
    proven = [s for s in provable if s in shown]
    unproven = [s for s in provable if s not in shown]
    hidden = sorted(
        (s for s in shown - resume_skills if group_of(s) in PROVABLE_GROUPS),
        key=lambda s: (-len(skill_repos[s]), s),
    )

    recent = sum(1 for r in own if (t := _parse_time(r.pushed_at)) and now - t <= RECENT)
    return {
        "login": profile.login,
        "proven": _evidence(skill_repos, proven),
        "unproven": unproven,
        "hidden": _evidence(skill_repos, hidden),
        "checks": _checks(profile, own, resume, now),
        "stats": GithubStats(
            own_repos=len(own),
            forks=forks,
            stars=sum(r.stargazers_count for r in own),
            active_recently=recent,
        ),
    }
