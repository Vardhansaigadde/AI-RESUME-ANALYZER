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
from typing import Any, Callable, Dict, Optional, Tuple

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from app.schemas import (
    AnalyzeResponse,
    RolePrediction,
    RolesOnlyResponse,
    SuggestRolesResponse,
)
from app.services.pipeline import (
    MAX_FILE_SIZE,
    REQUIRED_ANALYZE_MODELS,
    REQUIRED_ROLE_MODELS,
    PipelineError,
    run_full_analysis,
    run_role_suggestion,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

MAX_TOP_N = 24  # number of role categories the classifier knows


async def _read_json_object(request: Request) -> Dict[str, Any]:
    """Parse the request body as a JSON object or raise a clean 400/422."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body.")
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="JSON body must be an object.")
    return body


def _as_optional_text(value: Any, field: str) -> Optional[str]:
    """Validate that a JSON field is a string (or missing)."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise HTTPException(status_code=422, detail=f"{field} must be a string.")
    return value


def _validate_top_n(value: Any) -> int:
    """Coerce top_n to an int in [1, MAX_TOP_N] or raise a clean 422."""
    try:
        top_n = int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="top_n must be an integer.")
    if not 1 <= top_n <= MAX_TOP_N:
        raise HTTPException(
            status_code=422, detail=f"top_n must be between 1 and {MAX_TOP_N}."
        )
    return top_n


async def _read_upload(uploaded_file: Optional[UploadFile]) -> Tuple[Optional[bytes], Optional[str]]:
    """Read an uploaded file, stopping as soon as it exceeds the size limit.

    The request body itself is already capped by BodySizeLimitMiddleware in
    app.main; this keeps at most MAX_FILE_SIZE + 1 bytes in memory so the
    pipeline can report the 5MB limit precisely.
    """
    if uploaded_file is None:
        return None, None
    content = await uploaded_file.read(MAX_FILE_SIZE + 1)
    return content, uploaded_file.filename


async def _run_pipeline(func: Callable[..., Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
    """Run a CPU-bound pipeline function in the threadpool.

    Parsing, regex skill extraction and model inference are synchronous and
    CPU-heavy; running them on the event loop would block every other request
    (including health checks) until they finish.
    """
    try:
        return await run_in_threadpool(func, **kwargs)
    except PipelineError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


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
        body = await _read_json_object(request)
        raw_resume = _as_optional_text(body.get("resume_text"), "resume_text")
        raw_job = _as_optional_text(
            body.get("job_description") or body.get("job_text"), "job_text"
        )
        return await _run_pipeline(
            run_full_analysis,
            resume_text=raw_resume,
            job_description=raw_job,
            is_json=True,
            required_models=REQUIRED_ANALYZE_MODELS,
        )

    # 2. Multipart form data flow (file upload + job_description)
    file_bytes, filename = await _read_upload(resume_file or file)
    raw_job = job_description if job_description is not None else job_text

    return await _run_pipeline(
        run_full_analysis,
        resume_bytes=file_bytes,
        filename=filename,
        job_description=raw_job,
        is_json=False,
        required_models=REQUIRED_ANALYZE_MODELS,
    )


@router.post("/suggest-roles", response_model=SuggestRolesResponse)
async def suggest_roles(
    request: Request,
    resume_file: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    top_n: str = Form("3"),
) -> Dict[str, Any]:
    """Predict the top-N most likely job role categories for a resume.

    Works standalone with an uploaded resume file (PDF or DOCX), or with
    a raw resume_text string (via Form data or JSON payload).
    """
    content_type = request.headers.get("content-type", "")

    # 1. JSON payload support
    if "application/json" in content_type:
        body = await _read_json_object(request)
        return await _run_pipeline(
            run_role_suggestion,
            resume_text=_as_optional_text(body.get("resume_text"), "resume_text"),
            top_n=_validate_top_n(body.get("top_n", 3)),
            is_json=True,
            required_models=REQUIRED_ROLE_MODELS,
        )

    # 2. File upload or form data
    file_bytes, filename = await _read_upload(resume_file or file)

    return await _run_pipeline(
        run_role_suggestion,
        resume_bytes=file_bytes,
        filename=filename,
        resume_text=resume_text,
        top_n=_validate_top_n(top_n),
        is_json=False,
        required_models=REQUIRED_ROLE_MODELS,
    )


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
