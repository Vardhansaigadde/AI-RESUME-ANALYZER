"""Pydantic schemas for resume analysis and role prediction API endpoints."""

from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel


class RolePrediction(BaseModel):
    role: str
    match_percent: float


class AnalyzeResponse(BaseModel):
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    features: Dict[str, float]
    resume_skills_count: int
    required_skills_count: int
    suggested_roles: List[RolePrediction]
    suggestions: List[str]
    confidence: str = "high"


class SuggestRolesResponse(BaseModel):
    suggested_roles: List[RolePrediction]
    confidence: str = "high"


RolesOnlyResponse = SuggestRolesResponse

__all__ = [
    "RolePrediction",
    "AnalyzeResponse",
    "SuggestRolesResponse",
    "RolesOnlyResponse",
]
