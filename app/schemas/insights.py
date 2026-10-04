"""Schemas for job insights and the skill-gap learning plan."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.resume import StructuredResume


class JobInsights(BaseModel):
    """Rule-based reading of the job posting (see app.services.job_decoder)."""

    level: Literal["Entry level", "Mid level", "Senior", "Not stated"]
    entry_friendly: bool
    years_min: int | None = None
    years_max: int | None = None
    degree_mentioned: bool = False
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    also_mentioned: list[str] = Field(
        default_factory=list, description="Skills in the posting (e.g. under Responsibilities) not marked either way."
    )
    must_have_covered: list[str] = Field(default_factory=list)
    nice_to_have_covered: list[str] = Field(default_factory=list)
    lead_with: list[str] = Field(default_factory=list, description="Your matching skills to list first.")


class LearningResource(BaseModel):
    title: str
    url: str
    kind: Literal["docs", "course", "tutorial", "practice", "book", "video"]
    time: str = ""
    by: str = Field("", description="Channel or author (videos).")


class LearningItem(BaseModel):
    """How to close one skill gap."""

    skill: str
    what: str
    why: str = Field("", description="The line of the job posting that mentions the skill.")
    resources: list[LearningResource] = Field(default_factory=list)
    project: str = Field("", description="A small project that proves the skill on a resume.")
    priority: Literal["must-have", "nice-to-have", "mentioned", "core-skill", "prerequisite", "goal"] = "mentioned"
    hours: int = Field(0, description="Rough hours to learn the basics and build the project.")
    done: list[str] = Field(default_factory=list, description='"Done when you can..." checklist.')
    roadmap: str = Field("", description="roadmap.sh roadmap for the skill, if there is one.")
    needed_for: list[str] = Field(
        default_factory=list, description="Later skills in the plan that build on this one (prerequisites)."
    )


class ProjectPick(BaseModel):
    """A portfolio project that closes several skill gaps at once (app/data/project_ideas.json)."""

    id: str
    title: str
    summary: str
    level: Literal["beginner", "intermediate", "advanced"]
    hours: int
    closes: list[str] = Field(default_factory=list, description="Missing skills this project covers.")
    uses: list[str] = Field(default_factory=list, description="Skills you already have that it builds on.")
    also_learn: list[str] = Field(default_factory=list, description="Other skills it needs.")
    steps: list[str] = Field(default_factory=list)
    bullet: str = Field("", description="An example resume bullet once it's built.")


class RoleGap(BaseModel):
    """Resume skills compared with a role's skill profile (app/data/role_profiles.json)."""

    role: str
    have: list[str] = Field(default_factory=list, description="Profile skills found in the resume, most common first.")
    missing: list[str] = Field(default_factory=list, description="Profile skills not in the resume, most common first.")
    coverage: float = Field(0.0, description="Share of the profile's skills the resume shows (0-1).")
    roadmap: str = Field("", description="roadmap.sh roadmap for the role, if there is one.")
    available_roles: list[str] = Field(default_factory=list)


class InventorySkill(BaseModel):
    skill: str
    count: int


class InventoryGroup(BaseModel):
    group: str
    skills: list[InventorySkill]


class RoleGapRequest(BaseModel):
    """Edited resume plus the role to compare it with."""

    resume: StructuredResume
    target_role: str = Field(..., min_length=1, max_length=60)


class LearnRequest(BaseModel):
    """Skills a student wants to learn, and the ones they already know (to skip prerequisites)."""

    skills: list[str] = Field(..., min_length=1, max_length=8)
    known: list[str] = Field(default_factory=list, max_length=150)


class LearnResponse(BaseModel):
    learning_plan: list[LearningItem]
    project_picks: list[ProjectPick] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list, description="Requested skills without a curated roadmap.")


class RoleGapResponse(BaseModel):
    role_gap: RoleGap
    learning_plan: list[LearningItem]
    project_picks: list[ProjectPick] = Field(default_factory=list)
