"""Eligibility rules in Indian campus and fresher job posts, checked against the resume.

Posts often filter before anything else: "B.Tech (CSE/IT/ECE), 2026 batch,
60% or 6.5 CGPA throughout 10th, 12th and graduation, no active backlogs".
This reads those rules and checks each against the resume:

- pass: the resume clearly meets it
- fail: the resume clearly doesn't (e.g. CGPA 6.2 against 6.5)
- check: the post asks for it but the resume doesn't say (the student must
  check themselves; backlogs are never on a resume)

Nothing here changes the match score: a student who fails a hard rule is told
plainly, which is more useful than a lower number.
"""

from __future__ import annotations

import re

from app.schemas.insights import Eligibility, EligibilityCheck
from app.schemas.resume import StructuredResume

# Each branch / degree: (acronyms matched in capitals as whole words, phrases matched in any case).
# Acronyms are case-sensitive so the word "it" or "be" never counts as IT or B.E.
BRANCHES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "CSE": (("CSE", "CS"), ("computer science", "computer engineering")),
    "IT": (("IT",), ("information technology",)),
    "AI & ML": (("AIML", "AI&ML", "AI & ML", "AI/ML", "AI-ML"), ("artificial intelligence",)),
    "Data Science": ((), ("data science",)),
    "ECE": (("ECE",), ("electronics and communication", "electronics & communication")),
    "EEE": (("EEE",), ("electrical and electronics", "electrical & electronics", "electrical engineering")),
    "Mechanical": (("MECH",), ("mechanical",)),
    "Civil": ((), ("civil engineering", "civil")),
}
# Branches usually accepted where CSE is (CSE family)
CSE_FAMILY = {"CSE", "IT", "AI & ML", "Data Science"}

DEGREES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "B.Tech / B.E.": (
        ("B.E", "BTech", "B.Tech"),
        ("b.tech", "btech", "b. tech", "b.e.", "bachelor of engineering", "bachelor of technology"),
    ),
    "M.Tech": (("M.E",), ("m.tech", "mtech")),
    "MCA": (("MCA",), ("master of computer applications",)),
    "BCA": (("BCA",), ("bachelor of computer applications",)),
    "B.Sc": (("BSc", "B.Sc"), ("b.sc", "bachelor of science")),
    "MBA": (("MBA",), ()),
}

_YEAR = r"(20\d{2})"
_BATCH_RES = [
    re.compile(rf"{_YEAR}\s*(?:(?:/|,|or|and|&|-)\s*{_YEAR}\s*)?(?:batch|pass[\s-]?outs?|graduates?)", re.I),
    re.compile(
        rf"(?:batch|pass[\s-]?out|graduating|graduation year|year of passing|yop)\D{{0,25}}?{_YEAR}"
        rf"(?:\s*(?:/|,|or|and|&|-)\s*{_YEAR})?",
        re.I,
    ),
]
_CGPA_JOB = [
    re.compile(r"(\d{1,2}(?:\.\d{1,2})?)\s*(?:/\s*10\s*)?(?:cgpa|cpi|gpa|sgpa)", re.I),
    re.compile(
        r"(?:cgpa|cpi|gpa)\s*(?:of\s*)?(?:>=|≥|above|over|minimum|min\.?|at least|of at least)?\s*[:\-]?\s*"
        r"(\d{1,2}(?:\.\d{1,2})?)",
        re.I,
    ),
]
_PERCENT = re.compile(r"(\d{2}(?:\.\d{1,2})?)\s*%")
_PERCENT_CONTEXT = re.compile(r"throughout|aggregate|academics|marks|10th|12th|ssc|hsc|graduation|minimum|above", re.I)
_BACKLOG = re.compile(r"no\s+(?:active|live|current|standing|pending)?\s*backlogs?|backlogs?\s+not\s+allowed", re.I)
_TENTH = re.compile(r"\b(10th|ssc|class x\b|secondary school|matriculation)", re.I)
_TWELFTH = re.compile(r"\b(12th|hsc|class xii|intermediate|senior secondary|pre[- ]university|puc)\b", re.I)
_RES_CGPA = [
    re.compile(r"(?:cgpa|cpi|gpa|sgpa)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?)", re.I),
    re.compile(r"(\d(?:\.\d{1,2})?)\s*/\s*10\b"),
]


def _find_any(text: str, table: dict[str, tuple[tuple[str, ...], tuple[str, ...]]]) -> set[str]:
    found: set[str] = set()
    for name, (acronyms, phrases) in table.items():
        if any(re.search(rf"(?<![A-Za-z]){re.escape(a)}(?![A-Za-z])", text) for a in acronyms) or any(
            re.search(rf"(?<![a-z]){re.escape(p)}(?![a-z])", text, re.I) for p in phrases
        ):
            found.add(name)
    return found


def _job_batches(job: str) -> set[int]:
    years: set[int] = set()
    for pattern in _BATCH_RES:
        for match in pattern.finditer(job):
            years.update(int(y) for y in match.groups() if y)
    return years


def _job_cgpa(job: str) -> float | None:
    values = [float(m.group(1)) for p in _CGPA_JOB for m in p.finditer(job)]
    values = [v for v in values if 4.0 <= v <= 10.0]
    return max(values) if values else None


def _job_percent(job: str) -> float | None:
    values = []
    for match in _PERCENT.finditer(job):
        window = job[max(0, match.start() - 60) : match.end() + 60]
        value = float(match.group(1))
        if 35 <= value <= 99 and _PERCENT_CONTEXT.search(window):
            values.append(value)
    return max(values) if values else None


def _education_text(resume: StructuredResume, resume_text: str) -> str:
    entries = " | ".join(f"{e.title} {e.subtitle} {e.date}" for e in resume.education)
    return entries or resume_text


def _grad_year(resume: StructuredResume, resume_text: str) -> int | None:
    years = [
        int(y)
        for e in resume.education
        for y in re.findall(r"(20\d{2})", " ".join([e.title, e.subtitle, e.date, *e.bullets]))
    ]
    if not years:
        match = re.search(r"(?:expected|graduating|graduation|class of|batch)\D{0,15}(20\d{2})", resume_text, re.I)
        years = [int(match.group(1))] if match else []
    return max(years) if years else None


def _resume_cgpa(text: str) -> float | None:
    for pattern in _RES_CGPA:
        for match in pattern.finditer(text):
            value = float(match.group(1))
            if 4.0 <= value <= 10.0:
                return value
    return None


def _school_marks(resume_text: str, pattern: re.Pattern) -> float | None:
    for line in resume_text.splitlines():
        if pattern.search(line):
            match = _PERCENT.search(line)
            if match:
                return float(match.group(1))
    return None


def check_eligibility(job_text: str, resume: StructuredResume, resume_text: str) -> Eligibility | None:
    """Eligibility checks for the rules a job post states; None when it states none."""
    job = job_text or ""
    checks: list[EligibilityCheck] = []
    edu_text = _education_text(resume, resume_text)

    batches = _job_batches(job)
    if batches:
        year = _grad_year(resume, resume_text)
        wanted = " or ".join(str(y) for y in sorted(batches))
        if year is None:
            checks.append(
                EligibilityCheck(
                    id="batch",
                    label=f"{wanted} batch",
                    status="check",
                    detail="Add your graduation year to the Education section.",
                )
            )
        else:
            ok = year in batches
            checks.append(
                EligibilityCheck(
                    id="batch",
                    label=f"{wanted} batch",
                    status="pass" if ok else "fail",
                    detail=f"Your resume says {year}.",
                )
            )

    wanted_branches = _find_any(job, BRANCHES)
    if wanted_branches and not re.search(r"any (?:branch|stream|discipline)|all branches", job, re.I):
        mine = _find_any(edu_text, BRANCHES)
        label = "Branch: " + ", ".join(sorted(wanted_branches))
        if not mine:
            checks.append(
                EligibilityCheck(
                    id="branch", label=label, status="check", detail="Write your branch in the Education section."
                )
            )
        else:
            ok = bool(mine & wanted_branches) or (bool(mine & CSE_FAMILY) and "CSE" in wanted_branches)
            checks.append(
                EligibilityCheck(
                    id="branch",
                    label=label,
                    status="pass" if ok else "fail",
                    detail=f"Your resume says {', '.join(sorted(mine)).rstrip('.')}.",
                )
            )

    wanted_degrees = _find_any(job, DEGREES)
    if wanted_degrees:
        mine = _find_any(edu_text, DEGREES)
        label = "Degree: " + ", ".join(sorted(wanted_degrees))
        if mine:
            ok = bool(mine & wanted_degrees)
            checks.append(
                EligibilityCheck(
                    id="degree",
                    label=label,
                    status="pass" if ok else "fail",
                    detail=f"Your resume says {', '.join(sorted(mine)).rstrip('.')}.",
                )
            )
        else:
            checks.append(
                EligibilityCheck(
                    id="degree", label=label, status="check", detail="Write your degree in the Education section."
                )
            )

    cgpa_cut = _job_cgpa(job)
    if cgpa_cut is not None:
        mine = _resume_cgpa(edu_text) or _resume_cgpa(resume_text)
        label = f"CGPA {cgpa_cut:g} or above"
        if mine is None:
            checks.append(
                EligibilityCheck(
                    id="cgpa", label=label, status="check", detail="Add your CGPA to the Education section."
                )
            )
        else:
            checks.append(
                EligibilityCheck(
                    id="cgpa",
                    label=label,
                    status="pass" if mine >= cgpa_cut else "fail",
                    detail=f"Your resume says {mine:g}.",
                )
            )

    pct_cut = _job_percent(job)
    if pct_cut is not None:
        for label_name, pattern, check_id in (("10th", _TENTH, "tenth"), ("12th", _TWELFTH, "twelfth")):
            mine = _school_marks(resume_text, pattern)
            label = f"{label_name}: {pct_cut:g}% or above"
            if mine is None:
                checks.append(
                    EligibilityCheck(
                        id=check_id,
                        label=label,
                        status="check",
                        detail=f"Many campus jobs check {label_name} marks; add them if they help.",
                    )
                )
            else:
                checks.append(
                    EligibilityCheck(
                        id=check_id,
                        label=label,
                        status="pass" if mine >= pct_cut else "fail",
                        detail=f"Your resume says {mine:g}%.",
                    )
                )

    if _BACKLOG.search(job):
        checks.append(
            EligibilityCheck(
                id="backlogs",
                label="No active backlogs",
                status="check",
                detail="Resumes don't show this: make sure you have no active backlogs.",
            )
        )

    if not checks:
        return None
    statuses = {c.status for c in checks}
    status = "not_eligible" if "fail" in statuses else "check" if "check" in statuses else "eligible"
    return Eligibility(status=status, checks=checks)
