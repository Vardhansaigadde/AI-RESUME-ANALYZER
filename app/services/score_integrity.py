"""Keep the match score honest.

The match model scores word and skill overlap, so on its own it can be gamed
and it can't tell a listed skill from a used one. These checks run around it:

- Copied text: runs of 8+ words that also appear in the job description are
  removed before scoring (no honest pair in the training data shares even
  one such run), so pasting the job post no longer inflates the score.
- Keyword lists: a resume that is mostly skill words (over 40%; real
  resumes peak at 17%) is capped, because it shows no evidence.
- Evidence: a matched skill counts fully when an experience or project entry
  uses it, and partly when it is only listed.
- Implied skills: Machine Learning implies Python, NumPy and pandas
  (app/data/implied_skills.json). They earn partial credit and are not
  suggested as things to learn, but they stay "missing" for ATS, which only
  matches the exact word; the report asks the student to add them.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from app.services.data_cleaning import clean_text
from app.services.skill_extractor import extract_skill_counts, extract_skills

COPY_RUN_WORDS = 8
COPY_MIN_WORDS = 15
KEYWORD_SHARE = 0.40
KEYWORD_LIST_CAP = 25.0
LISTED_ONLY_WEIGHT = 0.75
IMPLIED_WEIGHT = 0.5

IMPLIED_PATH = Path(__file__).resolve().parent.parent / "data" / "implied_skills.json"


@lru_cache(maxsize=1)
def _implications() -> dict[str, list[str]]:
    data = json.loads(IMPLIED_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def implied_by(skills: set[str]) -> dict[str, str]:
    """Skills implied by the ones a resume shows: {implied skill: the skill that implies it}."""
    implied: dict[str, str] = {}
    for skill in sorted(skills):
        for target in _implications().get(skill, []):
            if target not in skills:
                implied.setdefault(target, skill)
    return implied


def strip_copied(resume_clean: str, job_clean: str) -> tuple[str, int]:
    """Remove resume words that sit in 8+ word runs also found in the job text.

    Returns the remaining text and how many words were removed (0 when below
    COPY_MIN_WORDS, so a shared company name or short phrase never counts).
    """
    resume_words, job_words = resume_clean.split(), job_clean.split()
    n = COPY_RUN_WORDS
    if len(resume_words) < n or len(job_words) < n:
        return resume_clean, 0
    job_runs = {tuple(job_words[i : i + n]) for i in range(len(job_words) - n + 1)}
    copied = [False] * len(resume_words)
    for i in range(len(resume_words) - n + 1):
        if tuple(resume_words[i : i + n]) in job_runs:
            copied[i : i + n] = [True] * n
    removed = sum(copied)
    if removed < COPY_MIN_WORDS:
        return resume_clean, 0
    return " ".join(w for w, c in zip(resume_words, copied, strict=True) if not c), removed


def skill_share(text_clean: str) -> float:
    """Share of the words that are skill names (0..1)."""
    words = text_clean.split()
    if not words:
        return 0.0
    counts = extract_skill_counts(text_clean)
    skill_words = sum(len(skill.split()) * count for skill, count in counts.items())
    return min(1.0, skill_words / len(words))


FUNCTION_WORDS = frozenset(
    "a an the and or of to in on at for with by from using used built building developed into as is was were "
    "my our i we this that which while".split()
)


def is_keyword_list(text_clean: str) -> bool:
    """Mostly skill names and almost no sentence words: a keyword list, not a description of work.

    Real sentences ("Python developer with SQL ... building REST APIs for 3 years") have
    connecting words, even when they are dense with skills.
    """
    words = text_clean.split()
    if len(words) < 10 or skill_share(text_clean) < KEYWORD_SHARE:
        return False
    return sum(w in FUNCTION_WORDS for w in words) <= max(2, len(words) // 25)


def evidenced_skills(resume_text: str, job_clean: str = "") -> set[str] | None:
    """Skills used in experience, project or activity entries; None when the resume has no such entries
    (then evidence can't be judged and no skill is down-weighted)."""
    from app.services.resume_sections import parse_resume  # local import: resume_sections is heavy

    resume = parse_resume(resume_text)
    parts: list[str] = []
    for entry in [*resume.experience, *resume.projects]:
        parts.extend([entry.title, entry.subtitle, *entry.bullets])
    for extra in resume.additional:
        parts.extend(extra.items)
    text = clean_text(" ".join(p for p in parts if p))
    if not text:
        return None
    if job_clean:
        text, _ = strip_copied(text, job_clean)
    return extract_skills(text)


def effective_overlap(
    resume_skills: set[str], job_skills: set[str], evidenced: set[str] | None, implied: dict[str, str]
) -> float:
    """Share of the job's skills the resume covers, weighting evidence and implied skills."""
    if not job_skills:
        return 0.0
    credit = 0.0
    for skill in job_skills:
        if skill in resume_skills:
            credit += 1.0 if evidenced is None or skill in evidenced else LISTED_ONLY_WEIGHT
        elif skill in implied:
            credit += IMPLIED_WEIGHT
    return credit / len(job_skills)
