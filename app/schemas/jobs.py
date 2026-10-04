"""Schemas for the live job and internship search."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.resume import StructuredResume

JobKind = Literal["all", "internship", "entry"]


class JobSearchRequest(BaseModel):
    """Edited resume plus what to search for. Only `query`, `country` and `kind` leave the server."""

    resume: StructuredResume
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
    fit_score: float = Field(..., description="Match score of the resume against this posting (0-100).")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    short_description: bool = Field(False, description="True when the source only gives a snippet of the posting.")


class JobSource(BaseModel):
    name: str
    url: str
    status: Literal["ok", "unavailable", "off"]
    count: int = 0
    note: str = ""


class JobSearchResponse(BaseModel):
    query: str
    country: str
    kind: JobKind
    jobs: list[JobPosting]
    sources: list[JobSource]
