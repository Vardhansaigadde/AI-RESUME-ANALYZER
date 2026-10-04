"""Resume analysis and role suggestion orchestration pipeline.

Coordinates file extraction, model verification, match scoring,
suggestion generation, and role prediction into complete API response shapes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from datetime import date

from app.ml.features import DEFAULT_VECTORIZER_PATH as TFIDF_VECTORIZER_PATH
from app.schemas.resume import StructuredResume
from app.services.ats_checker import check_ats
from app.services.data_cleaning import clean_text
from app.services.job_decoder import decode_job
from app.services.job_search import ANYWHERE, COUNTRIES, search_jobs
from app.services.learning_plan import build_learning_plan
from app.services.matcher import DEFAULT_MODEL_PATH as MATCH_SCORER_PATH
from app.services.matcher import match_resume_to_job
from app.services.parser import LayoutInfo, extract_text_from_file, inspect_layout
from app.services.resume_sections import looks_like_student, parse_resume, render_resume_text
from app.services.role_gap import compare_with_role, resolve_role
from app.services.role_predictor import (
    DEFAULT_CLASSIFIER_PATH as ROLE_CLASSIFIER_PATH,
)
from app.services.role_predictor import (
    DEFAULT_VECTORIZER_PATH as ROLE_VECTORIZER_PATH,
)
from app.services.role_predictor import (
    predict_roles_with_confidence,
)
from app.services.skill_extractor import extract_skills
from app.services.skills_inventory import build_inventory
from app.services.suggestions import generate_suggestions

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Megabytes
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

REQUIRED_ANALYZE_MODELS: list[tuple[str, Path]] = [
    ("match_scorer.joblib", MATCH_SCORER_PATH),
    ("tfidf_vectorizer.joblib", TFIDF_VECTORIZER_PATH),
    ("role_classifier.joblib", ROLE_CLASSIFIER_PATH),
    ("role_vectorizer.joblib", ROLE_VECTORIZER_PATH),
]

REQUIRED_ROLE_MODELS: list[tuple[str, Path]] = [
    ("role_classifier.joblib", ROLE_CLASSIFIER_PATH),
    ("role_vectorizer.joblib", ROLE_VECTORIZER_PATH),
]


class PipelineError(Exception):
    """Exception raised for pipeline validation and processing errors with HTTP status codes."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def verify_models_present(models: list[tuple[str, Path]]) -> None:
    """Ensure all required trained model artifacts exist on disk before inference.

    Raises:
        PipelineError(status_code=503): Clear error detail with missing model names.
    """
    missing = [name for name, path in models if not path.exists()]
    if missing:
        missing_str = ", ".join(missing)
        logger.error("Missing required model artifacts in models/: %s", missing_str)
        raise PipelineError(
            f"Required model artifact(s) missing from models/: {missing_str}. "
            "Please run model training before calling this endpoint.",
            status_code=503,
        )


def validate_and_extract_file(
    content: bytes | None,
    filename: str | None,
) -> str:
    """Validate uploaded resume file size, extension, and extract clean text.

    Args:
        content: Raw bytes of the uploaded file.
        filename: Name of the uploaded file including extension.

    Returns:
        Extracted text string from PDF or DOCX document.

    Raises:
        PipelineError(status_code=400): If file is invalid, unsupported, empty,
        oversized, or contains unreadable text.
    """
    if not filename:
        raise PipelineError(
            "Resume file is required. Please upload a PDF or DOCX file.",
            status_code=400,
        )

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise PipelineError(
            f"Invalid file type '{ext}'. Only PDF (.pdf) and DOCX (.docx) files are supported.",
            status_code=400,
        )

    if not content:
        raise PipelineError("Uploaded file is empty.", status_code=400)

    if len(content) > MAX_FILE_SIZE:
        raise PipelineError(
            f"File size exceeds the 5MB limit ({len(content)} bytes uploaded).",
            status_code=400,
        )

    # Magic-byte validation to prevent malformed or malicious file processing
    if ext == ".pdf" and not content.startswith(b"%PDF-"):
        raise PipelineError(
            f"Invalid file content for '{filename}': File header does not match PDF format.",
            status_code=400,
        )
    if ext == ".docx" and not content.startswith(b"PK\x03\x04"):
        raise PipelineError(
            f"Invalid file content for '{filename}': File header does not match DOCX format.",
            status_code=400,
        )

    try:
        text = extract_text_from_file(content, filename)
    except Exception as exc:
        logger.warning("Document parsing failed for file with extension '%s': %s", ext, exc)
        raise PipelineError(
            f"Failed to extract text from '{filename}': The file could not be read or is corrupted.",
            status_code=400,
        ) from exc

    cleaned_text = text.strip()
    if not cleaned_text:
        if ext == ".pdf":
            # pdfplumber only reads embedded text; a scanned or image-only PDF has none
            raise PipelineError(
                f"'{filename}' has no selectable text; it looks like a scanned image. "
                "Please upload a text-based PDF (e.g. exported from Word or Google Docs) "
                "or a DOCX file.",
                status_code=400,
            )
        raise PipelineError(
            f"Uploaded file '{filename}' contains no readable text.",
            status_code=400,
        )

    return cleaned_text


def run_full_analysis(
    resume_bytes: bytes | None = None,
    filename: str | None = None,
    resume_text: str | None = None,
    job_description: str | None = None,
    is_json: bool = False,
    required_models: list[tuple[str, Path]] | None = None,
    student_mode: bool = False,
    target_role: str | None = None,
) -> dict[str, Any]:
    """Execute end-to-end resume-to-job match analysis.

    The job description is optional: without one, the report is resume-only
    (ATS check, role gap, skills inventory, editor) and job fields are empty.

    Validates inputs, extracts document text, verifies model presence, computes
    match score, generates actionable suggestions, and predicts role categories.

    Args:
        resume_bytes: Raw bytes from uploaded PDF/DOCX file.
        filename: Uploaded file name.
        resume_text: Raw resume text (used in JSON requests).
        job_description: Target job description text.
        is_json: Whether the request originated from a JSON payload.
        required_models: List of model files to verify (defaults to REQUIRED_ANALYZE_MODELS).

    Returns:
        Complete dictionary matching the AnalyzeResponse schema.
    """
    # 1. Validate & extract resume text
    layout: LayoutInfo | None = None
    if is_json:
        if not resume_text or not str(resume_text).strip():
            raise PipelineError("resume_text must not be empty.", status_code=422)
        resume_content_text = str(resume_text).strip()
        job_content_text = str(job_description or "").strip()
    else:
        if resume_bytes is None:
            raise PipelineError(
                "Resume file is required. Please upload a PDF or DOCX file.",
                status_code=400,
            )
        resume_content_text = validate_and_extract_file(resume_bytes, filename)
        layout = inspect_layout(resume_bytes, filename)
        job_content_text = str(job_description or "").strip()

    # 2. Verify all required models exist on disk
    models_to_check = required_models if required_models is not None else REQUIRED_ANALYZE_MODELS
    verify_models_present(models_to_check)

    return _analyze_text(
        resume_content_text,
        job_content_text,
        parse_resume(resume_content_text),
        layout,
        student_mode=student_mode,
        target_role=target_role,
    )


def run_recheck(
    resume: StructuredResume,
    job_description: str = "",
    student_mode: bool = False,
    target_role: str | None = None,
) -> dict[str, Any]:
    """Analyze an edited, structured resume (as it would appear in the downloaded .docx)."""
    job_content_text = str(job_description or "").strip()
    resume_content_text = render_resume_text(resume)
    if not resume_content_text.strip():
        raise PipelineError("The resume is empty.", status_code=422)
    verify_models_present(REQUIRED_ANALYZE_MODELS)
    return _analyze_text(
        resume_content_text, job_content_text, resume, layout=None, student_mode=student_mode, target_role=target_role
    )


def run_job_search(resume: StructuredResume, query: str, country: str, kind: str) -> dict[str, Any]:
    """Live postings for a search, each scored against the (possibly edited) resume."""
    country = country.strip().upper()
    if country != ANYWHERE and country not in COUNTRIES:
        raise PipelineError("Unsupported country.", status_code=422)
    resume_text = render_resume_text(resume)
    if not clean_text(resume_text):
        raise PipelineError("The resume is empty.", status_code=422)
    return search_jobs(resume_text, query, country, kind)


def run_role_gap(resume: StructuredResume, target_role: str, with_learning_plan: bool = True) -> dict[str, Any]:
    """Role gap (and its learning plan) for an edited resume, without re-running the models."""
    resume_skills = extract_skills(clean_text(render_resume_text(resume)))
    role = resolve_role(target_role, [])
    if role is None:
        raise PipelineError("No target roles are available.", status_code=503)
    gap = compare_with_role(resume_skills, role)
    plan = build_learning_plan(gap.missing, "", None, role=role, have=resume_skills) if with_learning_plan else []
    return {"role_gap": gap, "learning_plan": plan}


def _analyze_text(
    resume_content_text: str,
    job_content_text: str,
    resume: StructuredResume,
    layout: LayoutInfo | None,
    student_mode: bool = False,
    target_role: str | None = None,
) -> dict[str, Any]:
    """Full report for resume text, matched against a job when one is given."""
    has_job = bool(job_content_text)
    resume_skills = extract_skills(clean_text(resume_content_text))

    # 3. Compute match score & skill breakdown (job mode only)
    if has_job:
        match_result = match_resume_to_job(resume_text=resume_content_text, job_text=job_content_text)
    else:
        match_result = {
            "match_score": None,
            "matched_skills": [],
            "missing_skills": [],
            "features": {},
            "score_breakdown": {},
            "score_warnings": [],
            "resume_skills_count": len(resume_skills),
            "required_skills_count": 0,
        }

    # 4. Generate prioritized suggestions
    suggestions = generate_suggestions(
        missing_skills=match_result["missing_skills"],
        resume_text=resume_content_text,
    )

    # 5. Predict top-3 role categories
    roles, confidence = predict_roles_with_confidence(
        resume_text=resume_content_text,
        top_n=3,
    )

    # 6. ATS-friendliness report
    ats = check_ats(
        resume_content_text,
        resume,
        layout=layout,
        job_skill_overlap=match_result["features"].get("skill_overlap_ratio") if has_job else None,
        missing_skills=match_result["missing_skills"],
        student_mode=student_mode,
    )

    # 7. Target-role gap; job insights; learning plan for the job's (or role's) gaps
    role = resolve_role(target_role, roles)
    role_gap = compare_with_role(resume_skills, role) if role else None
    if has_job:
        insights = decode_job(job_content_text, resume_skills)
        learning_plan = build_learning_plan(
            match_result["missing_skills"], job_content_text, insights, have=resume_skills
        )
    else:
        insights = None
        learning_plan = (
            build_learning_plan(role_gap.missing, "", None, role=role, have=resume_skills) if role_gap else []
        )

    return {
        **match_result,
        "mode": "job" if has_job else "resume_only",
        "role_gap": role_gap,
        "skills_inventory": build_inventory(resume_content_text),
        "resume": resume,
        "ats": ats,
        "job_insights": insights,
        "learning_plan": learning_plan,
        "student_mode": student_mode,
        "student_detected": looks_like_student(resume_content_text, resume, date.today().year),
        "suggested_roles": roles,
        "suggestions": suggestions,
        "confidence": confidence,
    }


def run_role_suggestion(
    resume_bytes: bytes | None = None,
    filename: str | None = None,
    resume_text: str | None = None,
    top_n: int = 3,
    is_json: bool = False,
    required_models: list[tuple[str, Path]] | None = None,
) -> dict[str, Any]:
    """Predict job roles from an uploaded resume file or raw text.

    Args:
        resume_bytes: Raw bytes from uploaded PDF/DOCX file.
        filename: Uploaded file name.
        resume_text: Raw resume text string.
        top_n: Number of role categories to predict.
        is_json: Whether the request originated from a JSON payload.
        required_models: List of model files to verify (defaults to REQUIRED_ROLE_MODELS).

    Returns:
        Dictionary matching the SuggestRolesResponse schema.
    """
    if is_json:
        if not resume_text or not str(resume_text).strip():
            raise PipelineError("resume_text must not be empty.", status_code=422)
        resume_content_text = str(resume_text).strip()
    else:
        if resume_bytes is not None:
            resume_content_text = validate_and_extract_file(resume_bytes, filename)
        elif resume_text is not None and str(resume_text).strip():
            resume_content_text = str(resume_text).strip()
        else:
            raise PipelineError(
                "Resume file is required. Please upload a PDF or DOCX file.",
                status_code=400,
            )

    # Verify role models exist
    models_to_check = required_models if required_models is not None else REQUIRED_ROLE_MODELS
    verify_models_present(models_to_check)

    roles, confidence = predict_roles_with_confidence(
        resume_text=resume_content_text,
        top_n=top_n,
    )

    return {
        "suggested_roles": roles,
        "confidence": confidence,
    }
