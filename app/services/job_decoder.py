"""Break a job posting down before applying.

decode_job() reads the posting line by line and works out:
- which skills are must-haves and which are nice-to-haves (from section
  headings such as "Requirements" / "Nice to have" and phrases such as
  "is a plus" or "preferred"),
- the years of experience asked for and the seniority level,
- whether it is open to students and freshers,
- how many must-haves and nice-to-haves the resume covers, and which of the
  candidate's matching skills to list first.

All of it is rule-based, so it explains itself but can misread unusual
postings; the UI presents it as a reading aid, not a verdict.
"""

from __future__ import annotations

from collections import Counter
import re

from app.schemas.insights import JobInsights
from app.services.skill_extractor import extract_skills

_MUST_HEADINGS = re.compile(
    r"^\s*(?:requirements?|required|qualifications?|must[- ]haves?|what you(?:'|’)?ll need|"
    r"what we(?:'|’)?re looking for|who you are|skills (?:and|&) experience|"
    r"basic qualifications|minimum qualifications|you have|you bring)\b",
    re.IGNORECASE,
)
_NICE_HEADINGS = re.compile(
    r"^\s*(?:nice[- ]to[- ]haves?|preferred(?: qualifications| skills)?|bonus(?: points)?|good[- ]to[- ]haves?|"
    r"pluses|desirable|additional (?:skills|qualifications)|it(?:'|’)?s a plus)\b",
    re.IGNORECASE,
)
_OTHER_HEADINGS = re.compile(
    r"^\s*(?:about (?:us|the (?:role|company|team))|responsibilities|what you(?:'|’)?ll do|the role|benefits|perks|"
    r"why join|our (?:team|company)|salary|compensation|location)\b",
    re.IGNORECASE,
)
_NICE_PHRASES = re.compile(
    r"\b(?:is a plus|are a plus|a plus|nice to have|preferred|bonus|good to have|is an advantage|desirable|ideally)\b",
    re.IGNORECASE,
)
_YEARS_RE = re.compile(
    r"(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|to)\s*(\d{1,2})\s*)?\+?\s*(?:years?|yrs?)",
    re.IGNORECASE,
)
_ENTRY_RE = re.compile(
    r"\b(?:intern(?:ship)?|fresher|freshers|entry[- ]level|graduate(?:s)?|new grad|junior|trainee|apprentice|"
    r"no (?:prior )?experience (?:required|needed)|final[- ]year students?|campus)\b",
    re.IGNORECASE,
)
_SENIOR_RE = re.compile(r"\b(?:senior|sr\.|lead|principal|staff|head of|director|architect|manager)\b", re.IGNORECASE)
_DEGREE_RE = re.compile(
    r"\b(?:bachelor(?:'s)?|master(?:'s)?|b\.?\s?tech|b\.?\s?e\b|m\.?\s?tech|b\.?\s?sc|degree|graduate in|phd)\b",
    re.IGNORECASE,
)


def _lines(text: str) -> list[str]:
    # Bullets and sentences both carry requirements; split on newlines and sentence ends
    parts = re.split(r"\n+|(?<=[.;])\s+(?=[A-Z])", str(text or ""))
    return [p.strip(" \t-•*·") for p in parts if p.strip(" \t-•*·")]


def _years(text: str) -> tuple[int | None, int | None]:
    """Smallest years-of-experience range mentioned next to 'experience'."""
    found: list[tuple[int, int | None]] = []
    for match in _YEARS_RE.finditer(text):
        window = text[match.end() : match.end() + 60].lower() + text[max(0, match.start() - 40) : match.start()].lower()
        if "experience" in window or "exp" in window:
            low = int(match.group(1))
            high = int(match.group(2)) if match.group(2) else None
            if low <= 30:
                found.append((low, high))
    if not found:
        return None, None
    low, high = min(found, key=lambda pair: pair[0])
    return low, high


def decode_job(job_text: str, resume_skills: set[str]) -> JobInsights:
    """Analyze a job posting against the resume's skills."""
    must: Counter = Counter()
    nice: Counter = Counter()
    mentioned: Counter = Counter()
    section = "other"
    for line in _lines(job_text):
        short = len(line.split()) <= 6
        if short and _MUST_HEADINGS.match(line):
            section = "must"
        elif short and _NICE_HEADINGS.match(line):
            section = "nice"
        elif short and _OTHER_HEADINGS.match(line):
            section = "other"
        skills = extract_skills(line)
        if not skills:
            continue
        if section == "nice" or _NICE_PHRASES.search(line):
            nice.update(skills)
        elif section == "must":
            must.update(skills)
        else:
            mentioned.update(skills)

    all_skills = Counter(must) + Counter(nice) + Counter(mentioned)
    # A skill listed as required anywhere is required; postings without a
    # requirements section treat everything not marked optional as required.
    must_set = set(must) or (set(mentioned) - set(nice))
    nice_set = set(nice) - must_set

    years_min, years_max = _years(job_text)
    if _ENTRY_RE.search(job_text) or (years_min is not None and years_min <= 1):
        level = "Entry level"
    elif _SENIOR_RE.search(job_text[:300]) or (years_min is not None and years_min >= 5):
        level = "Senior"
    elif years_min is not None:
        level = "Mid level"
    else:
        level = "Not stated"
    entry_friendly = level == "Entry level" or (years_min is not None and years_min <= 1)

    def ordered(skills: set[str]) -> list[str]:
        return sorted(skills, key=lambda s: (-all_skills[s], s))

    must_have = ordered(must_set)
    nice_to_have = ordered(nice_set)
    also_mentioned = ordered(set(all_skills) - must_set - nice_set)
    lead_with = [s for s in ordered(must_set | nice_set) if s in resume_skills][:6]

    return JobInsights(
        level=level,
        entry_friendly=entry_friendly,
        years_min=years_min,
        years_max=years_max,
        degree_mentioned=bool(_DEGREE_RE.search(job_text)),
        must_have=must_have,
        nice_to_have=nice_to_have,
        also_mentioned=also_mentioned,
        must_have_covered=[s for s in must_have if s in resume_skills],
        nice_to_have_covered=[s for s in nice_to_have if s in resume_skills],
        lead_with=lead_with,
    )
