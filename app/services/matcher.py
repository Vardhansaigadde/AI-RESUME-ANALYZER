"""Match scoring service for resume-job evaluations.

Coordinates feature extraction and inference against the trained Ridge regression
model (models/match_scorer.joblib) using the 3 leakage-free features:
1. tfidf_similarity
2. skill_overlap_ratio
3. resume_word_count
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import numpy as np

from app.ml.features import FEATURE_COLUMNS, build_features
from app.services.data_cleaning import clean_text
from app.services.skill_extractor import compare_skills, extract_skills

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = REPO_ROOT / "models" / "match_scorer.joblib"
DEFAULT_SCALER_PATH = REPO_ROOT / "models" / "feature_scaler.joblib"
_CACHED_MODEL: Optional[object] = None
_CACHED_SCALER: Optional[object] = None


def get_match_model(model_path: Path = DEFAULT_MODEL_PATH) -> Optional[object]:
    """Retrieve or load cached regression scoring model.

    Args:
        model_path: Path to serialized Ridge model artifact.

    Returns:
        Fitted model instance if available, else None.
    """
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL

    if model_path.exists():
        try:
            _CACHED_MODEL = joblib.load(model_path)
            logger.info("Loaded match scoring model from %s", model_path)
            return _CACHED_MODEL
        except Exception as exc:
            logger.warning("Failed to load match scorer from %s: %s", model_path, exc)
            return None
    return None


def get_feature_scaler(scaler_path: Path = DEFAULT_SCALER_PATH) -> Optional[object]:
    """Retrieve or load cached feature scaler artifact.

    Args:
        scaler_path: Path to serialized RobustScaler artifact.

    Returns:
        Fitted RobustScaler instance if available, else None.
    """
    global _CACHED_SCALER
    if _CACHED_SCALER is not None:
        return _CACHED_SCALER

    if scaler_path.exists():
        try:
            _CACHED_SCALER = joblib.load(scaler_path)
            logger.info("Loaded feature scaler from %s", scaler_path)
            return _CACHED_SCALER
        except Exception as exc:
            logger.warning("Failed to load feature scaler from %s: %s", scaler_path, exc)
            return None
    return None


def clear_matcher_cache() -> None:
    """Clear cached in-memory model and scaler artifacts."""
    global _CACHED_MODEL, _CACHED_SCALER
    _CACHED_MODEL = None
    _CACHED_SCALER = None


def match_resume_to_job(
    resume_text: str,
    job_text: str,
    model_path: Path = DEFAULT_MODEL_PATH,
    scaler_path: Path = DEFAULT_SCALER_PATH,
) -> Dict[str, Any]:
    """Compute overall match score and skill breakdown for a resume against a job.

    Uses only the 3 leakage-free features for inference:
    - tfidf_similarity
    - skill_overlap_ratio
    - resume_word_count

    Args:
        resume_text: Cleaned or raw resume text string.
        job_text: Cleaned or raw job description text string.
        model_path: Path to match_scorer.joblib artifact.
        scaler_path: Path to feature_scaler.joblib artifact.

    Returns:
        Dictionary containing:
            - match_score: float in range [0.0, 100.0] rounded to 2 decimal places.
            - matched_skills: sorted list of skills appearing in both resume and job.
            - missing_skills: sorted list of job skills not present in resume.
            - features: dictionary of the 3 computed feature values.
            - score_breakdown: points each feature adds to / removes from the
              model's baseline (see explain_score()).
            - resume_skills_count: total extracted skills from resume.
            - required_skills_count: total extracted skills from job description.
    """
    # Same normalization as the training data (data/processed/*.csv.gz)
    res_clean = clean_text(resume_text)
    job_clean = clean_text(job_text)

    # Guard: if either input is empty, return 0.0 match score
    if not res_clean or not job_clean:
        return {
            "match_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "features": {col: 0.0 for col in FEATURE_COLUMNS},
            "score_breakdown": {},
            "resume_skills_count": 0,
            "required_skills_count": 0,
        }

    # Extract & compare skills
    resume_skills = extract_skills(res_clean)
    job_skills = extract_skills(job_clean)
    matched_skills, missing_skills = compare_skills(resume_skills, job_skills)

    # Build 3-feature DataFrame
    feature_df = build_features(
        resume_text=res_clean,
        job_text=job_clean,
        as_dataframe=True,
    )
    feature_dict = feature_df.iloc[0].to_dict()

    # Predict score using trained Ridge regressor with RobustScaler
    model = get_match_model(model_path=model_path)
    scaler = get_feature_scaler(scaler_path=scaler_path)
    breakdown: Dict[str, float] = {}
    if model is not None:
        try:
            X_input = feature_df[FEATURE_COLUMNS]
            if scaler is not None:
                X_input = scaler.transform(X_input)
            raw_pred = float(model.predict(X_input)[0])
            score = float(np.clip(raw_pred, 0.0, 100.0))
            breakdown = explain_score(model, np.asarray(X_input)[0])
        except Exception as exc:
            logger.warning("Prediction failed (%s); falling back to heuristic score", exc)
            score = _heuristic_fallback_score(feature_dict)
    else:
        logger.info("Model not found; using heuristic fallback score")
        score = _heuristic_fallback_score(feature_dict)

    return {
        "match_score": round(score, 2),
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills),
        "features": {k: round(v, 4) for k, v in feature_dict.items()},
        "score_breakdown": breakdown,
        "resume_skills_count": len(resume_skills),
        "required_skills_count": len(job_skills),
    }


def explain_score(model: object, scaled_row: np.ndarray) -> Dict[str, float]:
    """Decompose a linear model's prediction into per-feature contributions.

    For the Ridge scorer, prediction = intercept + sum(coef_i * scaled_x_i), so
    each feature's contribution is exactly coef_i * scaled_x_i. "baseline" is
    the intercept (the score of a median training pair, since RobustScaler
    centers on the median). Contributions are reported before clipping to
    [0, 100]. Returns {} for models without coef_/intercept_.
    """
    coef = getattr(model, "coef_", None)
    intercept = getattr(model, "intercept_", None)
    if coef is None or intercept is None:
        return {}
    coef = np.ravel(coef)
    if len(coef) != len(FEATURE_COLUMNS) or len(scaled_row) != len(FEATURE_COLUMNS):
        return {}
    breakdown = {"baseline": round(float(intercept), 2)}
    for col, c, x in zip(FEATURE_COLUMNS, coef, scaled_row):
        breakdown[col] = round(float(c * x), 2)
    return breakdown


def _heuristic_fallback_score(features: Dict[str, float]) -> float:
    """Heuristic fallback score when model artifact is unavailable."""
    sim = features.get("tfidf_similarity", 0.0)
    overlap = features.get("skill_overlap_ratio", 0.0)
    # 60% weight on skill overlap, 40% on tfidf cosine
    heuristic = (overlap * 0.60 + sim * 0.40) * 100.0
    return float(np.clip(heuristic, 0.0, 100.0))
