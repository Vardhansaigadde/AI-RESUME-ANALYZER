"""Turn missing job skills into a short learning plan.

Uses the curated, link-checked app/data/learning_resources.json (built by
scripts/build_learning_resources.py). Must-have skills come first, then
nice-to-haves, then skills the posting only mentions. Each item quotes the
line of the job posting that asks for the skill. Soft skills get advice on
showing them with evidence instead of course links.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re

from app.schemas.insights import JobInsights, LearningItem, LearningResource
from app.services.skill_extractor import extract_skills
from app.services.suggestions import GENERIC_SOFT_SKILLS

RESOURCES_PATH = Path(__file__).resolve().parent.parent / "data" / "learning_resources.json"
MAX_ITEMS = 8


@lru_cache(maxsize=1)
def load_resources(path: Path = RESOURCES_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _job_line(job_text: str, skill: str) -> str:
    """The first line or sentence of the posting that mentions the skill."""
    for part in re.split(r"\n+|(?<=[.;])\s+(?=[A-Z])", job_text):
        line = part.strip(" \t-•*·")
        if line and skill in extract_skills(line):
            return line if len(line) <= 220 else line[:217].rstrip() + "…"
    return ""


def build_learning_plan(
    missing_skills: list[str],
    job_text: str,
    insights: JobInsights | None,
    role: str | None = None,
) -> list[LearningItem]:
    """Learning plan for missing skills, most important first.

    With a job description, skills are ranked must-have > nice-to-have >
    mentioned and quote the posting. Without one (``role`` given), the skills
    are a target role's missing core skills, already in importance order.
    """
    resources = load_resources()
    must = set(insights.must_have) if insights else set()
    nice = set(insights.nice_to_have) if insights else set()

    def priority(skill: str) -> str:
        if role:
            return "core-skill"
        return "must-have" if skill in must else "nice-to-have" if skill in nice else "mentioned"

    if role:
        # Keep the role's importance order; soft skills last
        ranked = sorted(missing_skills, key=lambda s: s in GENERIC_SOFT_SKILLS)
    else:
        order = {"must-have": 0, "nice-to-have": 1, "mentioned": 2}
        ranked = sorted(missing_skills, key=lambda s: (order[priority(s)], s in GENERIC_SOFT_SKILLS, s))

    plan: list[LearningItem] = []
    for skill in ranked:
        entry = resources.get(skill)
        if entry:
            item = LearningItem(
                skill=skill,
                what=entry["what"],
                resources=[LearningResource(**res) for res in entry["resources"]],
                project=entry["project"],
            )
        elif skill in GENERIC_SOFT_SKILLS:
            item = LearningItem(
                skill=skill,
                what="A soft skill: recruiters look for evidence, not the word itself.",
                project=f"Add a bullet that shows {skill} in action, e.g. a team project, event or "
                "presentation you led, with a concrete result.",
            )
        else:
            continue  # no curated resources for this skill yet
        item.why = f"A core skill for {role} roles." if role else _job_line(job_text, skill)
        item.priority = priority(skill)
        plan.append(item)
        if len(plan) >= MAX_ITEMS:
            break
    return plan
