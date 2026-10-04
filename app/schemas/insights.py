"""Schemas for job insights and the skill-gap learning plan."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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


class LearningItem(BaseModel):
    """How to close one skill gap."""

    skill: str
    what: str
    why: str = Field("", description="The line of the job posting that mentions the skill.")
    resources: list[LearningResource] = Field(default_factory=list)
    project: str = Field("", description="A small project that proves the skill on a resume.")
    priority: Literal["must-have", "nice-to-have", "mentioned"] = "mentioned"
