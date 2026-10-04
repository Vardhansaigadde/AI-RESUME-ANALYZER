"""Schemas for the GitHub proof check.

The browser fetches the public profile and repositories from GitHub's API (so
each student uses their own free rate limit) and sends them here together with
the resume; the backend only compares the two.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.resume import StructuredResume


class GithubProfile(BaseModel):
    login: str = Field(..., min_length=1, max_length=39)
    name: str | None = Field(None, max_length=255)
    bio: str | None = Field(None, max_length=500)
    avatar_url: str = Field("", max_length=500)
    html_url: str = Field("", max_length=500)
    public_repos: int = 0
    followers: int = 0


class GithubRepo(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=1000)
    topics: list[str] = Field(default_factory=list, max_length=20)
    language: str | None = Field(None, max_length=60)
    fork: bool = False
    archived: bool = False
    pushed_at: str | None = Field(None, max_length=40)
    stargazers_count: int = 0
    html_url: str = Field("", max_length=500)
    homepage: str | None = Field(None, max_length=500)


class GithubCheckRequest(BaseModel):
    resume: StructuredResume
    profile: GithubProfile
    repos: list[GithubRepo] = Field(default_factory=list, max_length=100)


class SkillEvidence(BaseModel):
    skill: str
    repos: list[str] = Field(default_factory=list, description="Up to three repositories that show the skill.")


class GithubCheckItem(BaseModel):
    id: str
    title: str
    status: Literal["pass", "warn", "fail"]
    detail: str
    tip: str = ""


class GithubStats(BaseModel):
    own_repos: int
    forks: int
    stars: int
    active_recently: int = Field(..., description="Own repositories pushed in the last 6 months.")


class GithubCheckResponse(BaseModel):
    login: str
    proven: list[SkillEvidence] = Field(default_factory=list, description="Resume skills a public repo shows.")
    unproven: list[str] = Field(default_factory=list, description="Technical resume skills no public repo shows.")
    hidden: list[SkillEvidence] = Field(
        default_factory=list, description="Skills the repos show that the resume doesn't mention."
    )
    checks: list[GithubCheckItem]
    stats: GithubStats
