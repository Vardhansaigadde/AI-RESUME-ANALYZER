"""Resume suggestions service for generating actionable resume improvements.

Generates rule-based suggestions per missing skill, prioritizing high-frequency
technical/concrete skills derived from the taxonomy (app/data/skills_list.json),
while excluding generic soft skills from strong framing. Also evaluates structural
resume health (quantifiable numbers, dedicated projects section, resume length).
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
import json
import logging
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

logger = logging.getLogger(__name__)

DEFAULT_SKILLS_PATH = REPO_ROOT / "app" / "data" / "skills_list.json"

# Cutoff rank in skills_list.json to be considered a high-demand skill
DEFAULT_FREQUENCY_THRESHOLD = 150
MAX_SUGGESTIONS = 5
DEFAULT_MAX_STRUCTURAL_SUGGESTIONS = 2
MIN_RESUME_WORDS = 100

# Generic soft skills to exclude from the strong "frequently required" framing.
# These skills are too generic to act on meaningfully, so they always receive
# neutral framing and lower priority than concrete technical tools/skills.
GENERIC_SOFT_SKILLS: set[str] = {
    # Communication
    "communication",
    "communication skills",
    "oral communication",
    "written communication",
    "presentation",
    "presentation skills",
    "public speaking",
    # Leadership & Teamwork
    "leadership",
    "team leadership",
    "teamwork",
    "team collaboration",
    "collaboration",
    "team player",
    "team building",
    "team management",
    "personnel management",
    # Problem Solving & Decision Making
    "problem solving",
    "critical thinking",
    "analytical skills",
    "strategic thinking",
    "decision making",
    # Interpersonal & Behavioral attributes
    "time management",
    "interpersonal skills",
    "adaptability",
    "flexibility",
    "work ethic",
    "creativity",
    "attention to detail",
    "motivation",
    "self-motivation",
    "resilience",
    "conflict resolution",
    "relationship building",
    "organizational skills",
    "organization",
    "mentoring",
    "mentorship",
    "empathy",
    "professionalism",
    "negotiation",
    "client relationship building",
    "client relationship management",
    "independent work",
    "ability to work under pressure",
    "multitasking",
    "active listening",
    "positive attitude",
}


@lru_cache(maxsize=1)
def load_skill_rank_map(skills_path: Path = DEFAULT_SKILLS_PATH) -> dict[str, int]:
    """Load skills taxonomy and return a dict mapping normalized skill -> 0-indexed frequency rank.

    Lower rank index indicates higher dataset frequency.
    """
    path = Path(skills_path)
    if not path.exists():
        logger.warning("Skills list not found at %s", path)
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            skills: list[str] = json.load(f)
        return {s.strip().lower(): rank for rank, s in enumerate(skills) if s.strip()}
    except Exception as exc:
        logger.error("Failed to load skills list from %s: %s", path, exc)
        return {}


def is_high_frequency_technical_skill(
    skill: str,
    rank_map: dict[str, int] | None = None,
    frequency_threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
) -> bool:
    """Determine whether a skill is high-frequency and concrete/technical (not generic soft skill)."""
    norm = skill.strip().lower()
    if norm in GENERIC_SOFT_SKILLS:
        return False

    if rank_map is None:
        rank_map = load_skill_rank_map()

    rank = rank_map.get(norm)
    return rank is not None and rank < frequency_threshold


def check_structural_issues(resume_text: str, min_words: int = MIN_RESUME_WORDS) -> list[str]:
    """Perform structural health checks on the resume text.

    Checks:
    1. Missing quantifiable metrics / numbers.
    2. Missing dedicated 'Projects' section.
    3. Resume is too short (< min_words).
    """
    text = str(resume_text or "").strip()
    suggestions: list[str] = []

    # 1. Resume too short (most fundamental structural issue)
    word_count = len(text.split())
    if word_count < min_words:
        suggestions.append(
            "Your resume appears too short; expand on your work experience, accomplishments, and core responsibilities."
        )

    # 2. Missing numbers / metrics
    if not re.search(r"\d+", text):
        suggestions.append(
            "Add quantifiable metrics or numbers (e.g., percentages, revenue, team size) "
            "to demonstrate impact in your bullet points."
        )

    # 3. No "projects" section
    if not re.search(r"\bprojects?\b", text, re.IGNORECASE):
        suggestions.append(
            "Include a dedicated 'Projects' section to showcase practical, hands-on applications of your skills."
        )

    return suggestions


def generate_suggestions(
    missing_skills: Iterable[str] | None = None,
    resume_text: str = "",
    frequency_threshold: int = DEFAULT_FREQUENCY_THRESHOLD,
    max_suggestions: int = MAX_SUGGESTIONS,
    max_structural_suggestions: int = DEFAULT_MAX_STRUCTURAL_SUGGESTIONS,
    skills_path: Path = DEFAULT_SKILLS_PATH,
) -> list[str]:
    """Generate prioritized actionable suggestions for improving a resume.

    Cross-checks each missing skill against its dataset frequency rank in
    app/data/skills_list.json. High-frequency technical/tool-specific missing skills
    receive stronger phrasing ("This is a commonly required skill across job
    postings — strongly consider adding it") and are prioritized first. Generic soft
    skills and low-frequency skills receive neutral phrasing.

    Also incorporates structural resume checks (resume too short, missing numbers,
    no 'projects' section). To ensure critical structural deficiencies are not
    silently crowded out by a long list of missing skills, up to
    `max_structural_suggestions` slots (default: 2) are reserved for structural
    issues, with the remaining slots filled by prioritized skill recommendations.
    Total suggestions are capped at `max_suggestions` (default 5).

    Args:
        missing_skills: Iterable of missing skill names identified from job description.
        resume_text: Raw or cleaned resume text string.
        frequency_threshold: Maximum rank in taxonomy to qualify for high-demand framing.
        max_suggestions: Maximum number of suggestions to return (default: 5).
        max_structural_suggestions: Maximum number of slots to reserve for structural issues (default: 2).
        skills_path: Path to skills_list.json.

    Returns:
        List of suggestion strings capped at max_suggestions.
    """
    rank_map = load_skill_rank_map(skills_path)

    # Deduplicate missing skills while preserving first-seen capitalization
    seen: set[str] = set()
    unique_skills: list[str] = []
    for s in missing_skills or []:
        if not s:
            continue
        cleaned = str(s).strip()
        norm = cleaned.lower()
        if norm and norm not in seen:
            seen.add(norm)
            unique_skills.append(cleaned)

    # Prioritization sort key:
    # 0: High-frequency technical skills (sorted by ascending rank)
    # 1: Other technical / concrete skills (sorted by ascending rank, unranked = 9999)
    # 2: Generic soft skills (even if high-frequency, deprioritized after concrete skills)
    def priority_key(skill: str) -> tuple[int, int, str]:
        norm = skill.lower()
        rank = rank_map.get(norm, 9999)
        is_soft = norm in GENERIC_SOFT_SKILLS
        is_high_tech = (rank < frequency_threshold) and not is_soft

        if is_high_tech:
            category = 0
        elif not is_soft:
            category = 1
        else:
            category = 2

        return (category, rank, skill)

    sorted_skills = sorted(unique_skills, key=priority_key)

    skill_suggestions: list[str] = []
    for skill in sorted_skills:
        norm = skill.lower()
        rank = rank_map.get(norm, 9999)
        is_soft = norm in GENERIC_SOFT_SKILLS
        is_high_tech = (rank < frequency_threshold) and not is_soft

        if is_high_tech:
            # Strong framing for commonly demanded concrete/technical skills
            skill_suggestions.append(
                f"'{skill}': This is a commonly required skill across job postings — strongly consider adding it."
            )
        else:
            # Neutral phrasing for soft skills, lower-frequency skills, or unknown skills
            skill_suggestions.append(f"Consider adding '{skill}' to better match the job requirements.")

    # Structural resume checks
    structural_suggestions = check_structural_issues(resume_text)

    # Prioritize balanced allocation: guarantee slots for structural issues
    # so critical flaws (e.g. resume too short, missing metrics) are not
    # silently crowded out when there are many missing skills.
    guaranteed_structural = min(len(structural_suggestions), max_structural_suggestions)
    max_skill_slots = max(0, max_suggestions - guaranteed_structural)

    selected_skills = skill_suggestions[:max_skill_slots]
    remaining_slots = max(0, max_suggestions - len(selected_skills))
    selected_structural = structural_suggestions[:remaining_slots]

    return selected_skills + selected_structural
