"""Pydantic schemas for resume analysis and role prediction API endpoints."""

from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class RolePrediction(BaseModel):
    role: str
    match_percent: float


class AnalyzeResponse(BaseModel):
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    features: Dict[str, float]
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Points each feature adds to (or removes from) the model baseline. "
            "baseline + the feature contributions = match_score before clipping to 0-100."
        ),
    )
    resume_skills_count: int
    required_skills_count: int
    suggested_roles: List[RolePrediction]
    suggestions: List[str]
    confidence: Literal["high", "low"] = "high"


class SuggestRolesResponse(BaseModel):
    suggested_roles: List[RolePrediction]
    confidence: Literal["high", "low"] = "high"


RolesOnlyResponse = SuggestRolesResponse

__all__ = [
    "RolePrediction",
    "AnalyzeResponse",
    "SuggestRolesResponse",
    "RolesOnlyResponse",
]
