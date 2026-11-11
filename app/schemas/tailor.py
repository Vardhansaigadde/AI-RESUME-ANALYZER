"""Schemas for "Generate a fixed resume"."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.resume import StructuredResume

ChangeId = str


class TailorRequest(BaseModel):
    resume: StructuredResume
    job_description: str = Field("", max_length=20_000, description="Optional: tailor to this job.")
    target_role: str = Field("", max_length=60, description="Optional: tailor to this role when there is no job.")
    confirmed_skills: list[str] = Field(
        default_factory=list, max_length=30, description="Suggested skills the student ticked as really known."
    )
    skip: list[ChangeId] = Field(default_factory=list, max_length=300, description="Changes the student undid.")
    accept: list[ChangeId] = Field(default_factory=list, max_length=50, description="Suggestions the student took.")


class TailorChange(BaseModel):
    """One thing FitLens changed (or suggests), so the student can keep or undo it."""

    id: ChangeId
    section: str
    kind: Literal["added", "rewrote", "reordered", "new", "fixed", "suggestion"]
    title: str
    before: str = ""
    after: str = ""
    applied: bool = True


class ScorePair(BaseModel):
    match: float | None = None
    ats: float | None = None
    role_have: int | None = Field(None, description="Role mode: the role's core skills the resume shows.")
    role_total: int | None = None


class TailorResponse(BaseModel):
    mode: Literal["job", "role", "general"]
    role: str = ""
    resume: StructuredResume
    template: str
    changes: list[TailorChange]
    suggested_skills: list[str] = Field(
        default_factory=list, description="Skills the job or role wants that the resume doesn't show: add only if true."
    )
    notes: list[str] = Field(default_factory=list, description="Things only the student can add.")
    before: ScorePair
    after: ScorePair
