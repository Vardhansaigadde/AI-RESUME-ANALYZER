"""Feature engineering module for resume-job matching.

Constructs feature representations from resume text and job descriptions using
only leakage-free features that can be reliably computed at inference:
1. TF-IDF cosine similarity between resume_text and job_text.
2. Skill overlap ratio: matched_skills_count / required_skills_count using
   app.services.skill_extractor (extract_skills and compare_skills).
3. Resume word count.

(Note: job_word_count was tested and dropped due to severe out-of-domain linear
extrapolation sensitivity on varying job description lengths.)

Provides:
- build_features(): Reusable single-pair feature builder for API inference.
- build_feature_matrix_from_csv(): Batch pipeline for training dataset generation
  with progress logging and correlation analysis.
- make_group_split(): Group-aware train/test split keyed by job_text.
"""

import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.skill_extractor import compare_skills, extract_skills

logger = logging.getLogger(__name__)

# Standard ordered 3 leakage-free feature columns used by downstream ML models
FEATURE_COLUMNS: List[str] = [
    "tfidf_similarity",
    "skill_overlap_ratio",
    "resume_word_count",
]

DEFAULT_VECTORIZER_PATH: Path = REPO_ROOT / "models" / "tfidf_vectorizer.joblib"
_CACHED_VECTORIZER: Optional[TfidfVectorizer] = None


def get_tfidf_vectorizer(
    model_path: Path = DEFAULT_VECTORIZER_PATH,
) -> Optional[TfidfVectorizer]:
    """Retrieve or load cached TF-IDF vectorizer artifact.

    Args:
        model_path: Path to serialized vectorizer joblib file.

    Returns:
        Fitted TfidfVectorizer if available, else None.
    """
    global _CACHED_VECTORIZER
    if _CACHED_VECTORIZER is not None:
        return _CACHED_VECTORIZER

    if model_path.exists():
        try:
            _CACHED_VECTORIZER = joblib.load(model_path)
            logger.info("Loaded pre-fitted TF-IDF vectorizer from %s", model_path)
            return _CACHED_VECTORIZER
        except Exception as exc:
            logger.warning("Could not load vectorizer from %s: %s", model_path, exc)
            return None
    return None


def calculate_tfidf_similarity(
    resume_text: str,
    job_text: str,
    vectorizer: Optional[TfidfVectorizer] = None,
) -> float:
    """Compute cosine similarity between resume and job description using TF-IDF.

    Args:
        resume_text: Text of the resume.
        job_text: Text of the job description.
        vectorizer: Pre-fitted TfidfVectorizer. If None, attempts to load the
            default saved vectorizer artifact. If not found, fits a pairwise
            vectorizer directly on the two documents.

    Returns:
        Cosine similarity score in range [0.0, 1.0].
    """
    if not resume_text or not job_text:
        return 0.0

    if vectorizer is None:
        vectorizer = get_tfidf_vectorizer()

    if vectorizer is not None:
        try:
            vecs = vectorizer.transform([resume_text, job_text])
            sim = cosine_similarity(vecs[0:1], vecs[1:2])[0, 0]
            return float(np.clip(sim, 0.0, 1.0))
        except Exception as exc:
            logger.warning("Error using pre-fitted vectorizer: %s. Falling back.", exc)

    # Fallback: fit pairwise directly on the two texts
    fallback_vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    vecs = fallback_vec.fit_transform([resume_text, job_text])
    sim = cosine_similarity(vecs[0:1], vecs[1:2])[0, 0]
    return float(np.clip(sim, 0.0, 1.0))


def build_features(
    resume_text: str,
    job_text: str,
    vectorizer: Optional[TfidfVectorizer] = None,
    as_dataframe: bool = True,
) -> Union[pd.DataFrame, Dict[str, float]]:
    """Build feature vector for a single resume-job pair using 4 leakage-free features.

    Designed for real-time inference in FastAPI endpoints as well as offline
    batch evaluation.

    Args:
        resume_text: Raw or cleaned resume text string.
        job_text: Raw or cleaned job description text string.
        vectorizer: Optional pre-fitted TfidfVectorizer instance.
        as_dataframe: If True, returns a 1-row pd.DataFrame matching FEATURE_COLUMNS.
            If False, returns a dictionary of feature names to float values.

    Returns:
        pd.DataFrame (1, num_features) or Dict[str, float].
    """
    res_clean = str(resume_text or "")
    job_clean = str(job_text or "")

    # 1. TF-IDF Cosine Similarity
    tfidf_sim = calculate_tfidf_similarity(res_clean, job_clean, vectorizer=vectorizer)

    # 2. Skill Extraction & Overlap Ratio
    resume_skills = extract_skills(res_clean)
    job_skills = extract_skills(job_clean)
    matched_skills, _ = compare_skills(resume_skills, job_skills)
    skill_overlap_ratio = (
        len(matched_skills) / len(job_skills) if job_skills else 0.0
    )

    # 3. Resume Word Count
    resume_word_count = float(len(res_clean.split()))

    feat_dict: Dict[str, float] = {
        "tfidf_similarity": float(tfidf_sim),
        "skill_overlap_ratio": float(skill_overlap_ratio),
        "resume_word_count": float(resume_word_count),
    }

    if as_dataframe:
        return pd.DataFrame([feat_dict], columns=FEATURE_COLUMNS)
    return feat_dict


def build_feature_matrix_from_csv(
    input_csv: Path = REPO_ROOT / "data" / "processed" / "job_resume_fit_clean.csv",
    output_csv: Path = REPO_ROOT / "data" / "processed" / "features.csv",
    vectorizer_path: Path = DEFAULT_VECTORIZER_PATH,
    print_every: int = 200,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Batch feature generation pipeline for dataset.

    Extracts features for all rows in the processed CSV, saves the fitted
    TF-IDF vectorizer artifact to models/, exports the complete feature matrix
    to data/processed/features.csv, and prints correlation analysis with
    ai_match_score.

    Args:
        input_csv: Path to job_resume_fit_clean.csv.
        output_csv: Path to destination features.csv.
        vectorizer_path: Path to serialize fitted TfidfVectorizer.
        print_every: Frequency for logging progress rows.

    Returns:
        Tuple of (X, y):
            - X: DataFrame of features (FEATURE_COLUMNS).
            - y: Series of ai_match_score.
    """
    logger.info("Loading dataset from %s", input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input dataset not found at {input_csv}")

    df = pd.read_csv(input_csv)
    total_rows = len(df)
    logger.info("Loaded %d rows for feature generation.", total_rows)

    # Ensure text columns are clean strings
    res_texts = df["resume_text"].fillna("").astype(str).tolist()
    job_texts = df["job_text"].fillna("").astype(str).tolist()

    # 1. Fit TF-IDF Vectorizer across all unique corpus documents
    print("\n" + "=" * 65)
    print("STEP 1: Fitting TF-IDF Vectorizer...")
    print("=" * 65)
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=10000,
        ngram_range=(1, 2),
    )
    all_corpus = pd.concat([pd.Series(res_texts), pd.Series(job_texts)]).unique()
    vectorizer.fit(all_corpus)

    # Serialize vectorizer artifact
    vectorizer_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, vectorizer_path)
    print(f"Saved fitted TF-IDF vectorizer ({len(vectorizer.vocabulary_):,} vocabulary items)")
    print(f"  -> {vectorizer_path}")

    # Vectorized cosine similarity computation
    vec_res = vectorizer.transform(res_texts)
    vec_job = vectorizer.transform(job_texts)
    tfidf_sims = np.asarray(vec_res.multiply(vec_job).sum(axis=1)).ravel()

    # 2. Word Counts
    resume_word_counts = [len(t.split()) for t in res_texts]
    job_word_counts = [len(t.split()) for t in job_texts]

    # 3. Cache Job Skills Extraction (few unique job descriptions)
    unique_job_texts = list(set(job_texts))
    print(f"\nCaching skill extraction for {len(unique_job_texts)} unique job descriptions...")
    job_skills_cache = {jt: extract_skills(jt) for jt in unique_job_texts}

    # 4. Extract Skills for Resumes and Calculate Overlap Ratios
    print("\n" + "=" * 65)
    print(f"STEP 2: Extracting skills across {total_rows:,} rows (progress every {print_every})...")
    print("=" * 65)

    import time
    t0 = time.time()
    skill_overlap_ratios = []
    resume_skills_cache: Dict[str, List[str]] = {}

    for idx, (res_text, job_text) in enumerate(zip(res_texts, job_texts)):
        if res_text not in resume_skills_cache:
            resume_skills_cache[res_text] = extract_skills(res_text)
        res_skills = resume_skills_cache[res_text]
        j_skills = job_skills_cache[job_text]

        matched, _ = compare_skills(res_skills, j_skills)
        ratio = len(matched) / len(j_skills) if j_skills else 0.0
        skill_overlap_ratios.append(ratio)

        row_num = idx + 1
        if row_num % print_every == 0 or row_num == total_rows:
            pct = (row_num / total_rows) * 100.0
            elapsed = time.time() - t0
            print(f"  Processed {row_num:>4}/{total_rows:,} rows ({pct:>5.1f}%) - elapsed: {elapsed:>5.1f}s", flush=True)

    # 5. Assemble Feature Matrix & Target (3 leakage-free features)
    X = pd.DataFrame(
        {
            "tfidf_similarity": tfidf_sims,
            "skill_overlap_ratio": skill_overlap_ratios,
            "resume_word_count": resume_word_counts,
        },
        columns=FEATURE_COLUMNS,
    )
    y = df["ai_match_score"].astype(float)

    # 6. Save to CSV
    output_df = X.copy()
    output_df["ai_match_score"] = y.values
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_csv, index=False)
    print(f"\nSaved feature matrix to: {output_csv} ({output_df.shape[0]} rows x {output_df.shape[1]} cols)")

    # 7. Correlation Analysis
    correlations = output_df.corr()["ai_match_score"].drop("ai_match_score").sort_values(ascending=False)

    print("\n" + "=" * 65)
    print("FEATURE CORRELATION WITH TARGET (ai_match_score):")
    print("=" * 65)
    print(f"{'Feature Name':<30} {'Pearson Correlation (r)':>25}")
    print("-" * 65)
    for feat, corr_val in correlations.items():
        print(f"  {feat:<28}: {corr_val:>18.4f}")
    print("=" * 65 + "\n")

    return X, y


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    build_feature_matrix_from_csv()
