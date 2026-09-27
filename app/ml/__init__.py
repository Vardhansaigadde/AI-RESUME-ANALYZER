"""Machine learning package.

Contains feature extraction pipelines, vectorizers, and scoring utilities
used at runtime to compute match scores between resumes and job descriptions.
"""

from app.ml.features import (
    DEFAULT_VECTORIZER_PATH,
    FEATURE_COLUMNS,
    build_feature_matrix_from_csv,
    build_features,
    calculate_tfidf_similarity,
    get_tfidf_vectorizer,
)

__all__ = [
    "DEFAULT_VECTORIZER_PATH",
    "FEATURE_COLUMNS",
    "build_features",
    "build_feature_matrix_from_csv",
    "calculate_tfidf_similarity",
    "get_tfidf_vectorizer",
]
