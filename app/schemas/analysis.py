"""Pydantic schemas for resume analysis and role prediction API endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.insights import InventoryGroup, JobInsights, LearningItem, RoleGap
from app.schemas.resume import AtsReport, StructuredResume


class RolePrediction(BaseModel):
    role: str
    match_percent: float


class AnalyzeResponse(BaseModel):
    mode: Literal["job", "resume_only"] = Field(
        "job", description="resume_only when no job description was given; job fields are then empty."
    )
    match_score: float | None
    matched_skills: list[str]
    missing_skills: list[str]
    features: dict[str, float]
    score_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Baseline plus the points each feature adds or removes. When the score "
            "is soft-capped near 0 or 100, a range_adjustment entry is included, so "
            "the values always sum to match_score."
        ),
    )
    score_warnings: list[str] = Field(
        default_factory=list,
        description="Reasons the score may be unreliable, e.g. a very short resume.",
    )
    resume_skills_count: int
    required_skills_count: int
    suggested_roles: list[RolePrediction]
    suggestions: list[str]
    confidence: Literal["high", "low"] = "high"
    resume: StructuredResume = Field(
        default_factory=StructuredResume,
        description="The resume split into editable sections (best-effort parse).",
    )
    ats: AtsReport | None = Field(None, description="Rule-based ATS-friendliness estimate.")
    job_insights: JobInsights | None = Field(None, description="Must-haves, level and coverage for the posting.")
    learning_plan: list[LearningItem] = Field(default_factory=list, description="How to close the skill gaps.")
    student_mode: bool = Field(False, description="Whether the student / fresher checklist was applied.")
    student_detected: bool = Field(False, description="The resume looks like a student's or fresher's.")
    role_gap: RoleGap | None = Field(None, description="Core skills of the target role you have and lack.")
    skills_inventory: list[InventoryGroup] = Field(default_factory=list, description="Skills found, grouped.")


class SuggestRolesResponse(BaseModel):
    suggested_roles: list[RolePrediction]
    confidence: Literal["high", "low"] = "high"


__all__ = [
    "RolePrediction",
    "AnalyzeResponse",
    "SuggestRolesResponse",
]
