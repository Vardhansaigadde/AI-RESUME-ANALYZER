"""Service layer package.

Contains business logic, document extraction routines (PDF via pdfplumber,
DOCX via python-docx), ML inference pipelines, and recommendation generators.
"""

from app.services.data_cleaning import (
    clean_job_fit_dataframe,
    clean_resume_dataframe,
    clean_text,
    safe_parse_skills,
)
from app.services.parser import (
    extract_text_from_docx,
    extract_text_from_file,
    extract_text_from_pdf,
)
from app.services.pipeline import (
    PipelineError,
    run_full_analysis,
    run_role_suggestion,
)
from app.services.role_predictor import clear_role_predictor_cache, predict_roles
from app.services.skill_extractor import compare_skills, extract_skills
from app.services.suggestions import generate_suggestions

__all__ = [
    "PipelineError",
    "clean_job_fit_dataframe",
    "clean_resume_dataframe",
    "clean_text",
    "clear_role_predictor_cache",
    "compare_skills",
    "extract_skills",
    "extract_text_from_docx",
    "extract_text_from_file",
    "extract_text_from_pdf",
    "generate_suggestions",
    "predict_roles",
    "run_full_analysis",
    "run_role_suggestion",
    "safe_parse_skills",
]
