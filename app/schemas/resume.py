"""Schemas for the structured (editable) resume and the ATS-friendliness report."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MAX_TEXT = 5_000
MAX_ITEMS = 60


class ResumeEntry(BaseModel):
    """One job, project or degree: a title line, an optional subtitle and bullet points."""

    title: str = Field("", max_length=300)
    subtitle: str = Field("", max_length=300)
    bullets: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)


class ExtraSection(BaseModel):
    """Any other section (languages, interests, volunteering...), kept as plain lines."""

    heading: str = Field(..., max_length=100)
    items: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)


class StructuredResume(BaseModel):
    """Resume content split into standard sections so it can be edited and re-rendered."""

    name: str = Field("", max_length=120)
    headline: str = Field("", max_length=200)
    email: str = Field("", max_length=200)
    phone: str = Field("", max_length=60)
    location: str = Field("", max_length=120)
    links: list[str] = Field(default_factory=list, max_length=10)
    summary: str = Field("", max_length=MAX_TEXT)
    skills: list[str] = Field(default_factory=list, max_length=150)
    experience: list[ResumeEntry] = Field(default_factory=list, max_length=MAX_ITEMS)
    projects: list[ResumeEntry] = Field(default_factory=list, max_length=MAX_ITEMS)
    education: list[ResumeEntry] = Field(default_factory=list, max_length=MAX_ITEMS)
    certifications: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)
    achievements: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)
    additional: list[ExtraSection] = Field(default_factory=list, max_length=20)


AtsStatus = Literal["pass", "warn", "fail", "skip"]


class AtsCheck(BaseModel):
    id: str
    category: Literal["format", "content", "keywords", "student"]
    title: str
    status: AtsStatus
    detail: str
    tip: str = ""


class AtsReport(BaseModel):
    """Rule-based ATS-friendliness estimate. A heuristic, not the output of a real ATS."""

    score: float
    verdict: Literal["ATS-friendly", "Needs a few fixes", "Needs work"]
    checks: list[AtsCheck]


class RecheckRequest(BaseModel):
    """Edited resume plus the job description to analyze it against."""

    resume: StructuredResume
    job_description: str = Field(..., min_length=1, max_length=20_000)
    student_mode: bool = False
