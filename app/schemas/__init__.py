"""Data schemas package.

Defines Pydantic models for request validation, API response formatting,
and structured representations of resumes, candidates, and job descriptions.
"""

from app.schemas.analysis import (
    AnalyzeResponse,
    RolePrediction,
    RolesOnlyResponse,
    SuggestRolesResponse,
)

__all__ = [
    "AnalyzeResponse",
    "RolePrediction",
    "RolesOnlyResponse",
    "SuggestRolesResponse",
]
