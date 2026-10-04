"""Pick portfolio projects that close several skill gaps at once.

A list of eight skills to learn is easy to put off; one project that covers four
of them is a plan. Projects come from app/data/project_ideas.json (curated,
student-sized). Each missing skill has a weight (must-have 3, nice-to-have 2,
mentioned 1; for a target role, by its place in the role's importance order).
A project scores the weight of the gaps it closes, plus a little for reusing
skills the student already has, minus a little for each unrelated new skill it
drags in. Picks are greedy: the second project is scored only on gaps the first
one leaves open, so together they cover as much as possible.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from app.schemas.insights import JobInsights, ProjectPick
from app.services.suggestions import GENERIC_SOFT_SKILLS

PROJECTS_PATH = Path(__file__).resolve().parent.parent / "data" / "project_ideas.json"
MAX_PICKS = 2  # one or two focused projects beat a long list
REUSE_BONUS = 0.3  # per skill the student already has (builds on strengths)
EXTRA_PENALTY = 0.4  # per skill that is neither missing nor already known


@lru_cache(maxsize=1)
def load_projects(path: Path = PROJECTS_PATH) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def gap_weights(missing: list[str], insights: JobInsights | None = None) -> dict[str, float]:
    """How much closing each missing skill matters. ``missing`` is in importance order."""
    skills = [s for s in missing if s not in GENERIC_SOFT_SKILLS]
    if insights is not None:
        must, nice = set(insights.must_have), set(insights.nice_to_have)
        return {s: 3.0 if s in must else 2.0 if s in nice else 1.0 for s in skills}
    n = len(skills)
    return {s: 3.0 if i < n / 3 else 2.0 if i < 2 * n / 3 else 1.0 for i, s in enumerate(skills)}


def pick_projects(
    missing: list[str], have: set[str], insights: JobInsights | None = None, limit: int = MAX_PICKS
) -> list[ProjectPick]:
    """Up to ``limit`` projects that together close the most important gaps."""
    weights = gap_weights(missing, insights)
    open_gaps = set(weights)
    picks: list[ProjectPick] = []
    used: set[str] = set()

    while open_gaps and len(picks) < limit:
        best, best_score, best_gain = None, 0.0, 0.0
        for project in load_projects():
            if project["id"] in used:
                continue
            skills = set(project["skills"])
            closes = skills & open_gaps
            if not closes:
                continue
            gain = sum(weights[s] for s in closes)
            extra = skills - set(weights) - have
            score = gain + REUSE_BONUS * len(skills & have) - EXTRA_PENALTY * len(extra)
            if score > best_score:
                best, best_score, best_gain = project, score, gain
        # Worth suggesting only if it closes an important gap or two smaller ones
        if best is None or best_gain < 2.0:
            break
        skills = best["skills"]
        picks.append(
            ProjectPick(
                id=best["id"],
                title=best["title"],
                summary=best["summary"],
                level=best["level"],
                hours=best["hours"],
                closes=[s for s in skills if s in open_gaps],
                uses=[s for s in skills if s in have],
                also_learn=[s for s in skills if s not in weights and s not in have],
                steps=best["steps"],
                bullet=best["bullet"],
            )
        )
        used.add(best["id"])
        open_gaps -= set(skills)
    return picks
