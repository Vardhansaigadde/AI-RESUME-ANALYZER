"""Compare a resume's skills with a target job role.

Target roles (app/data/target_roles.json, built by scripts/build_target_roles.py)
are named after real job titles such as "Software Engineer" or "Data Analyst"
and list their core skills in order of importance. When no role is chosen,
the default is the one mapped from the resume's top predicted job category.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from app.schemas.insights import RoleGap

TARGET_ROLES_PATH = Path(__file__).resolve().parent.parent / "data" / "target_roles.json"


@lru_cache(maxsize=1)
def _load() -> dict:
    if not TARGET_ROLES_PATH.exists():
        return {"roles": {}, "category_default": {}}
    return json.loads(TARGET_ROLES_PATH.read_text(encoding="utf-8"))


def available_roles() -> list[str]:
    return list(_load()["roles"])


def resolve_role(target_role: str | None, predicted_roles: list[dict]) -> str | None:
    """The requested role if known, else the default for the top predicted category."""
    data = _load()
    roles = data["roles"]
    if target_role and target_role.strip() in roles:
        return target_role.strip()
    for prediction in predicted_roles:
        default = data["category_default"].get(prediction.get("role", ""))
        if default in roles:
            return default
    return next(iter(roles), None)


def compare_with_role(resume_skills: set[str], role: str) -> RoleGap:
    """Core skills of the role that the resume shows and lacks, in importance order."""
    core = _load()["roles"].get(role, [])
    have = [s for s in core if s in resume_skills]
    missing = [s for s in core if s not in resume_skills]
    return RoleGap(
        role=role,
        have=have,
        missing=missing,
        coverage=round(len(have) / len(core), 3) if core else 0.0,
        available_roles=available_roles(),
    )
