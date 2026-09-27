"""Role prediction service for resume classification.

Loads the production CalibratedClassifierCV (LinearSVC) model and its TF-IDF
vectorizer from models/ and provides predict_roles() for returning the top-N
predicted job categories with calibrated probability percentages.

The models/ artifacts are created by scripts/train_role_classifier.py.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_CLASSIFIER_PATH = REPO_ROOT / "models" / "role_classifier.joblib"
DEFAULT_VECTORIZER_PATH = REPO_ROOT / "models" / "role_vectorizer.joblib"
DEFAULT_ROLE_PROFILES_PATH = REPO_ROOT / "app" / "data" / "role_profiles.json"

_CACHED_CLASSIFIER: Optional[object] = None
_CACHED_VECTORIZER: Optional[object] = None
_CACHED_ROLE_PROFILES: Optional[Dict[str, List[str]]] = None


def is_low_confidence(
    probabilities: object,
    threshold: float = 0.35,
    word_count: Optional[int] = None,
    min_word_count: int = 150,
) -> bool:
    """Return True if top-1 predicted probability is below threshold OR word count is below min_word_count.

    Validated confident predictions on full-length resumes are typically 65-82%,
    whereas sparse or short resumes yield diffuse probabilities across classes (e.g. 14-26%).
    Furthermore, any resume under ~150 words has an intrinsically sparse TF-IDF vector
    that cannot be reliably trusted on ML unigrams/bigrams alone.

    Args:
        probabilities: Array, sequence, or dict of predicted probabilities.
        threshold: Probability cutoff below which predictions are considered
            low confidence (default 0.35, i.e. 35%).
        word_count: Total word count of the resume text, if available.
        min_word_count: Minimum resume word length required to trust raw ML
            probabilities (default 150 words).

    Returns:
        True if word_count < min_word_count OR maximum probability is strictly
        below threshold, False otherwise.
    """
    if word_count is not None and word_count < min_word_count:
        return True

    if probabilities is None:
        return True
    if isinstance(probabilities, dict):
        vals = list(probabilities.values())
        if not vals:
            return True
        return float(max(vals)) < threshold
    if isinstance(probabilities, np.ndarray):
        if probabilities.size == 0:
            return True
        return float(np.max(probabilities)) < threshold
    try:
        prob_list = list(probabilities)  # type: ignore
        if not prob_list:
            return True
        return float(max(prob_list)) < threshold
    except (TypeError, ValueError):
        return True


def _load_classifier(path: Path = DEFAULT_CLASSIFIER_PATH) -> Optional[object]:
    """Load or return cached CalibratedClassifierCV model."""
    global _CACHED_CLASSIFIER
    if _CACHED_CLASSIFIER is not None:
        return _CACHED_CLASSIFIER
    if path.exists():
        try:
            _CACHED_CLASSIFIER = joblib.load(path)
            logger.info("Loaded role classifier from %s", path)
            return _CACHED_CLASSIFIER
        except Exception as exc:
            logger.warning("Failed to load role classifier from %s: %s", path, exc)
    return None


def _load_vectorizer(path: Path = DEFAULT_VECTORIZER_PATH) -> Optional[object]:
    """Load or return cached TF-IDF vectorizer."""
    global _CACHED_VECTORIZER
    if _CACHED_VECTORIZER is not None:
        return _CACHED_VECTORIZER
    if path.exists():
        try:
            _CACHED_VECTORIZER = joblib.load(path)
            logger.info("Loaded role vectorizer from %s", path)
            return _CACHED_VECTORIZER
        except Exception as exc:
            logger.warning("Failed to load role vectorizer from %s: %s", path, exc)
    return None


def _load_role_profiles(path: Path = DEFAULT_ROLE_PROFILES_PATH) -> Dict[str, List[str]]:
    """Load or return cached hand-curated role skill profiles."""
    global _CACHED_ROLE_PROFILES
    if _CACHED_ROLE_PROFILES is not None:
        return _CACHED_ROLE_PROFILES
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                _CACHED_ROLE_PROFILES = json.load(f)
            logger.info("Loaded role profiles from %s", path)
            return _CACHED_ROLE_PROFILES
        except Exception as exc:
            logger.warning("Failed to load role profiles from %s: %s", path, exc)
    return {}


def clear_role_predictor_cache() -> None:
    """Clear all cached model and profile artifacts (useful in testing)."""
    global _CACHED_CLASSIFIER, _CACHED_VECTORIZER, _CACHED_ROLE_PROFILES
    _CACHED_CLASSIFIER = None
    _CACHED_VECTORIZER = None
    _CACHED_ROLE_PROFILES = None


def predict_roles(
    resume_text: str,
    top_n: int = 3,
    classifier_path: Path = DEFAULT_CLASSIFIER_PATH,
    vectorizer_path: Path = DEFAULT_VECTORIZER_PATH,
    role_profiles_path: Path = DEFAULT_ROLE_PROFILES_PATH,
    return_confidence: bool = False,
    confidence_threshold: float = 0.35,
    min_word_count: int = 150,
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], str]]:
    """Predict the top-N most likely job role categories for a resume.

    Uses the production CalibratedClassifierCV model trained on 2,484 resumes
    across 24 job categories. When top-1 probability is below confidence_threshold (default 35%)
    OR resume word count is below min_word_count (default 150 words), engages a
    confidence-aware fallback:
    - Extracts canonical skills from the resume via skill_extractor.py
    - Computes skill overlap against role profiles from role_profiles.json
    - If ML confidence is very low (< 15%), ranks roles directly by skill overlap.
    - If ML confidence is moderately low (15% to 35%) or resume is short (< 150 words),
      blends ML probabilities and skill-overlap scores via a 50/50 weighted average.
    - If ML confidence is high (>= 35%) and resume is >= 150 words, relies purely
      on the ML classifier.

    Args:
        resume_text: Raw or cleaned resume text string.
        top_n: Number of top role predictions to return (default 3).
        classifier_path: Path to role_classifier.joblib artifact.
        vectorizer_path: Path to role_vectorizer.joblib artifact.
        role_profiles_path: Path to role_profiles.json fallback artifact.
        return_confidence: If True, returns a tuple (roles, confidence_str)
            where confidence_str is "high" or "low". Default is False.
        confidence_threshold: Cutoff below which ML predictions are deemed low
            confidence (default 0.35, i.e. 35%).
        min_word_count: Resume word count below which ML TF-IDF features are deemed
            too sparse to trust alone (default 150 words).

    Returns:
        List of dicts sorted by descending match_percent, each with:
            - "role": str -- category label (e.g. "INFORMATION-TECHNOLOGY")
            - "match_percent": float -- calibrated/blended probability * 100, rounded to 1 dp
        If return_confidence is True, returns (results, "high" | "low").
        Returns empty list (or ([], "low")) if models are unavailable or text is empty.
    """
    text = str(resume_text or "").strip()
    if not text:
        logger.warning("predict_roles called with empty resume text")
        return ([], "low") if return_confidence else []

    clf = _load_classifier(classifier_path)
    vec = _load_vectorizer(vectorizer_path)

    if clf is None or vec is None:
        logger.error(
            "Role predictor unavailable -- classifier=%s vectorizer=%s",
            clf is not None,
            vec is not None,
        )
        return ([], "low") if return_confidence else []

    try:
        word_count = len(text.split())
        X = vec.transform([text])
        ml_proba = clf.predict_proba(X)[0]  # shape (n_classes,)
        classes = clf.classes_

        # Determine confidence level based on raw ML top-1 probability and word count
        top_1_ml = float(np.max(ml_proba))
        low_conf = is_low_confidence(
            ml_proba,
            threshold=confidence_threshold,
            word_count=word_count,
            min_word_count=min_word_count,
        )
        confidence_str = "low" if low_conf else "high"

        effective_proba = ml_proba

        # If low confidence or sparse/short resume, engage skill-overlap fallback
        if low_conf:
            from app.services.skill_extractor import extract_skills

            resume_skills = set(extract_skills(text))
            profiles = _load_role_profiles(role_profiles_path)

            if resume_skills and profiles:
                overlap_counts = {
                    role: len(resume_skills & set(profiles.get(role, [])))
                    for role in classes
                }
                total_overlap = sum(overlap_counts.values())

                if total_overlap > 0:
                    skill_proba = np.array(
                        [overlap_counts[role] / total_overlap for role in classes]
                    )

                    if top_1_ml < 0.15:
                        # Very low ML confidence (< 15%): rely directly on skill overlap
                        effective_proba = skill_proba
                        logger.info(
                            "predict_roles: Very low ML confidence (%.1f%% < 15%%); using direct skill overlap fallback.",
                            top_1_ml * 100,
                        )
                    else:
                        # Moderately low ML confidence or short resume: 50/50 blend
                        effective_proba = 0.5 * ml_proba + 0.5 * skill_proba
                        logger.info(
                            "predict_roles: Low confidence or short resume (%.1f%% < %.0f%% or %d < %d words); using 50/50 ML + skill overlap blend.",
                            top_1_ml * 100,
                            confidence_threshold * 100,
                            word_count,
                            min_word_count,
                        )

        # Sort by descending effective probability and take top_n
        top_indices = np.argsort(effective_proba)[::-1][:top_n]
        results = [
            {
                "role": str(classes[i]),
                "match_percent": round(float(effective_proba[i]) * 100, 1),
            }
            for i in top_indices
        ]

        if return_confidence:
            return results, confidence_str
        return results

    except Exception as exc:
        logger.exception("predict_roles inference failed: %s", exc)
        return ([], "low") if return_confidence else []


def predict_roles_with_confidence(
    resume_text: str,
    top_n: int = 3,
    classifier_path: Path = DEFAULT_CLASSIFIER_PATH,
    vectorizer_path: Path = DEFAULT_VECTORIZER_PATH,
    role_profiles_path: Path = DEFAULT_ROLE_PROFILES_PATH,
    confidence_threshold: float = 0.35,
    min_word_count: int = 150,
) -> Tuple[List[Dict[str, Any]], str]:
    """Predict top-N roles and return (results, confidence), where confidence is 'high' or 'low'."""
    return predict_roles(
        resume_text=resume_text,
        top_n=top_n,
        classifier_path=classifier_path,
        vectorizer_path=vectorizer_path,
        role_profiles_path=role_profiles_path,
        return_confidence=True,
        confidence_threshold=confidence_threshold,
        min_word_count=min_word_count,
    )

