"""Schemas for the live job and internship search."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.resume import StructuredResume

JobKind = Literal["all", "internship", "entry"]


class JobSearchRequest(BaseModel):
    """Edited resume plus what to search for. Only `query`, `country` and `kind` leave the server."""

    resume: StructuredResume | None = Field(None, description="Without a resume, postings aren't scored.")
    query: str = Field(..., min_length=2, max_length=80, description="Role or keywords, e.g. 'data analyst'.")
    country: str = Field("IN", min_length=2, max_length=8, description="ISO country code, or 'ANY' for anywhere.")
    kind: JobKind = "all"


class JobPosting(BaseModel):
    """One live posting with the resume's fit score against it."""

    id: str
    title: str
    company: str
    location: str = ""
    remote: bool = False
    employment_type: str = ""
    level: str = ""
    posted: str = Field("", description="ISO date the posting was published.")
    salary: str = ""
    url: str = Field(..., description="The posting on the source site (where students apply).")
    source: str
    excerpt: str = ""
    fit_score: float | None = Field(None, description="Match score of the resume against this posting (0-100).")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    short_description: bool = Field(False, description="True when the source only gives a snippet of the posting.")


class JobSource(BaseModel):
    name: str
    url: str
    status: Literal["ok", "unavailable", "off"]
    count: int = 0
    note: str = ""


class SkillDemand(BaseModel):
    """How often a skill appears across the postings found."""

    skill: str
    count: int
    share: float = Field(..., description="Share of postings that mention the skill (0-1).")
    have: bool = Field(..., description="Whether the resume shows it.")


class JobSearchResponse(BaseModel):
    query: str
    country: str
    kind: JobKind
    jobs: list[JobPosting]
    sources: list[JobSource]
    scored: bool = Field(True, description="False when no resume was sent: missing_skills are then all skills asked.")
    skill_demand: list[SkillDemand] = Field(
        default_factory=list, description="Most-requested skills across these postings, most common first."
    )
