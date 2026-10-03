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
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import numpy as np

from app.services.data_cleaning import clean_text
from app.services.skill_extractor import extract_skills

logger = logging.getLogger(__name__)

DEFAULT_CLASSIFIER_PATH = REPO_ROOT / "models" / "role_classifier.joblib"
DEFAULT_VECTORIZER_PATH = REPO_ROOT / "models" / "role_vectorizer.joblib"
DEFAULT_ROLE_PROFILES_PATH = REPO_ROOT / "app" / "data" / "role_profiles.json"

# Low-confidence fallback policy, tuned by scripts/train_role_classifier.py on
# out-of-fold training predictions (see reports/role_classifier_metrics.json).
DEFAULT_CONFIDENCE_THRESHOLD = 0.25
DEFAULT_MIN_WORD_COUNT = 100
# Raw overlap counts beat size-normalized (cosine) overlap both on dataset
# snippets and on short synthetic resumes, so normalization is off by default.
DEFAULT_SIZE_NORMALIZED_OVERLAP = False

_CACHED_CLASSIFIER: Optional[object] = None
_CACHED_VECTORIZER: Optional[object] = None
_CACHED_ROLE_PROFILES: Optional[Dict[str, List[str]]] = None


def is_low_confidence(
    probabilities: object,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    word_count: Optional[int] = None,
    min_word_count: int = DEFAULT_MIN_WORD_COUNT,
) -> bool:
    """Return True if top-1 predicted probability is below threshold OR word count is below min_word_count.

    Full-length resumes usually get a decisive top probability, whereas short or
    sparse resumes produce diffuse probabilities spread across many classes, and
    very short texts have too few TF-IDF features to trust on their own. The
    defaults (DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_MIN_WORD_COUNT) were tuned by
    scripts/train_role_classifier.py.

    Args:
        probabilities: Array, sequence, or dict of predicted probabilities.
        threshold: Probability cutoff below which predictions are considered
            low confidence (default DEFAULT_CONFIDENCE_THRESHOLD).
        word_count: Total word count of the resume text, if available.
        min_word_count: Minimum resume word length required to trust raw ML
            probabilities (default DEFAULT_MIN_WORD_COUNT).

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


VERY_LOW_CONFIDENCE = 0.15


def skill_overlap_distribution(
    classes: Sequence[str],
    resume_skills: Set[str],
    profiles: Dict[str, List[str]],
    size_normalized: bool = DEFAULT_SIZE_NORMALIZED_OVERLAP,
) -> Optional[np.ndarray]:
    """Distribution over roles from resume-skill overlap with each role profile.

    By default each role's score is the number of resume skills found in its
    profile. Larger profiles (e.g. INFORMATION-TECHNOLOGY) can collect more
    overlap; size_normalized=True divides by sqrt(|profile|) (cosine similarity)
    to remove that, but in evaluation it was less accurate (it sends short
    frontend-developer resumes to the 13-skill DESIGNER profile), so it is only
    kept to let scripts/train_role_classifier.py compare the two variants.

    Returns None when there is no overlap with any profile.
    """
    if not resume_skills or not profiles:
        return None
    scores = np.array(
        [
            len(resume_skills & set(profiles.get(role, [])))
            / (np.sqrt(max(len(profiles.get(role, [])), 1)) if size_normalized else 1.0)
            for role in classes
        ],
        dtype=float,
    )
    total = scores.sum()
    if total <= 0:
        return None
    return scores / total


def blend_with_skill_overlap(
    ml_proba: np.ndarray,
    classes: Sequence[str],
    resume_skills: Set[str],
    profiles: Dict[str, List[str]],
    very_low_threshold: float = VERY_LOW_CONFIDENCE,
    size_normalized: bool = DEFAULT_SIZE_NORMALIZED_OVERLAP,
) -> np.ndarray:
    """Combine low-confidence ML probabilities with role-profile skill overlap.

    - top-1 ML probability < very_low_threshold: use skill overlap alone.
    - otherwise: 50/50 average of ML probabilities and skill overlap.
    - no skill overlap at all: keep the ML probabilities unchanged.
    """
    skill_proba = skill_overlap_distribution(
        classes, set(resume_skills), profiles, size_normalized=size_normalized
    )
    if skill_proba is None:
        return ml_proba
    top_1_ml = float(np.max(ml_proba))
    if top_1_ml < very_low_threshold:
        logger.info(
            "predict_roles: very low ML confidence (%.1f%%); using skill overlap.", top_1_ml * 100
        )
        return skill_proba
    logger.info("predict_roles: low confidence; blending ML 50/50 with skill overlap.")
    return 0.5 * np.asarray(ml_proba) + 0.5 * skill_proba


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
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    min_word_count: int = DEFAULT_MIN_WORD_COUNT,
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], str]]:
    """Predict the top-N most likely job role categories for a resume.

    Uses the production CalibratedClassifierCV model trained on 2,484 resumes
    across 24 job categories. When the top-1 probability is below
    confidence_threshold OR the resume is shorter than min_word_count words, the
    result is marked "low" confidence and blended with role-profile skill overlap
    (see blend_with_skill_overlap): skill overlap alone below VERY_LOW_CONFIDENCE,
    otherwise a 50/50 average. Confident predictions use the classifier directly.

    On dataset resumes the blend costs 1-2 points of accuracy, but on short,
    skill-list style resumes (students, freshers) it fixes most of the raw
    model's errors, which is why it is kept.

    Args:
        resume_text: Raw or cleaned resume text string.
        top_n: Number of top role predictions to return (default 3).
        classifier_path: Path to role_classifier.joblib artifact.
        vectorizer_path: Path to role_vectorizer.joblib artifact.
        role_profiles_path: Path to role_profiles.json fallback artifact.
        return_confidence: If True, returns a tuple (roles, confidence_str)
            where confidence_str is "high" or "low". Default is False.
        confidence_threshold: Cutoff below which ML predictions are deemed low
            confidence (default DEFAULT_CONFIDENCE_THRESHOLD).
        min_word_count: Resume word count below which ML TF-IDF features are deemed
            too sparse to trust alone (default DEFAULT_MIN_WORD_COUNT).

    Returns:
        List of dicts sorted by descending match_percent, each with:
            - "role": str -- category label (e.g. "INFORMATION-TECHNOLOGY")
            - "match_percent": float -- calibrated/blended probability * 100, rounded to 1 dp
        If return_confidence is True, returns (results, "high" | "low").
        Returns empty list (or ([], "low")) if models are unavailable or text is empty.
    """
    # Same normalization as data/processed/resume_clean.csv.gz used for training
    text = clean_text(resume_text)
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
        low_conf = is_low_confidence(
            ml_proba,
            threshold=confidence_threshold,
            word_count=word_count,
            min_word_count=min_word_count,
        )
        confidence_str = "low" if low_conf else "high"

        effective_proba = ml_proba
        if low_conf:
            effective_proba = blend_with_skill_overlap(
                ml_proba,
                classes,
                extract_skills(text),
                _load_role_profiles(role_profiles_path),
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
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    min_word_count: int = DEFAULT_MIN_WORD_COUNT,
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

