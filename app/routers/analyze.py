"""API router for resume analysis and role suggestion endpoints.

Provides:
  POST /api/analyze       -- Full resume-job match scoring, skill breakdown,
                             actionable suggestions, and top-3 role suggestions
                             from an uploaded PDF/DOCX resume file + job description.
  POST /api/suggest-roles -- Standalone top-N role predictions from an uploaded
                             resume file or resume text.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.schemas import (
    AnalyzeResponse,
    RolePrediction,
    RolesOnlyResponse,
    SuggestRolesResponse,
)
from app.services.pipeline import (
    REQUIRED_ANALYZE_MODELS,
    REQUIRED_ROLE_MODELS,
    PipelineError,
    run_full_analysis,
    run_role_suggestion,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: Request,
    resume_file: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    job_description: Optional[str] = Form(None),
    job_text: Optional[str] = Form(None),
) -> Dict[str, Any]:
    """Compute match score between a resume and a job description.

    Accepts a resume file (PDF or DOCX) along with job_description text.
    Also supports JSON payloads {"resume_text": "...", "job_text": "..."} for
    backwards-compatibility.
    """
    content_type = request.headers.get("content-type", "")

    # 1. JSON payload support (backwards-compatibility)
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body.")

        raw_resume = body.get("resume_text", "")
        raw_job = body.get("job_description") or body.get("job_text", "")

        try:
            return run_full_analysis(
                resume_text=raw_resume,
                job_description=raw_job,
                is_json=True,
                required_models=REQUIRED_ANALYZE_MODELS,
            )
        except PipelineError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message)

    # 2. Multipart form data flow (file upload + job_description)
    uploaded_file = resume_file or file
    file_bytes = None
    filename = None
    if uploaded_file is not None:
        file_bytes = await uploaded_file.read()
        filename = uploaded_file.filename

    raw_job = job_description if job_description is not None else job_text

    try:
        return run_full_analysis(
            resume_bytes=file_bytes,
            filename=filename,
            job_description=raw_job,
            is_json=False,
            required_models=REQUIRED_ANALYZE_MODELS,
        )
    except PipelineError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/suggest-roles", response_model=SuggestRolesResponse)
async def suggest_roles(
    request: Request,
    resume_file: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    top_n: int = Form(3),
) -> Dict[str, Any]:
    """Predict the top-N most likely job role categories for a resume.

    Works standalone with an uploaded resume file (PDF or DOCX), or with
    a raw resume_text string (via Form data or JSON payload).
    """
    content_type = request.headers.get("content-type", "")

    # 1. JSON payload support
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body.")

        raw_resume = body.get("resume_text", "")
        top_n_val = int(body.get("top_n", 3))

        try:
            return run_role_suggestion(
                resume_text=raw_resume,
                top_n=top_n_val,
                is_json=True,
                required_models=REQUIRED_ROLE_MODELS,
            )
        except PipelineError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message)

    # 2. File upload or form data
    uploaded_file = resume_file or file
    file_bytes = None
    filename = None
    if uploaded_file is not None:
        file_bytes = await uploaded_file.read()
        filename = uploaded_file.filename

    try:
        return run_role_suggestion(
            resume_bytes=file_bytes,
            filename=filename,
            resume_text=resume_text,
            top_n=top_n,
            is_json=False,
            required_models=REQUIRED_ROLE_MODELS,
        )
    except PipelineError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


__all__ = [
    "AnalyzeResponse",
    "REQUIRED_ANALYZE_MODELS",
    "REQUIRED_ROLE_MODELS",
    "RolePrediction",
    "RolesOnlyResponse",
    "SuggestRolesResponse",
    "analyze",
    "router",
    "suggest_roles",
]
