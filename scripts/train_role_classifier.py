"""Training and evaluation pipeline for resume role classification.

1. Loads data/raw/Resume.csv.gz (2,484 resumes, 24 categories) and applies the
   same clean_text() normalization used at inference.
2. Stratified 80/20 split. Benchmarks LogisticRegression, LinearSVC and
   MultinomialNB, selecting by macro F1 on test resumes WITH THEIR LEADING
   TITLE REMOVED (strip_leading_title): most dataset resumes open with an
   all-caps title that repeats the label ("SALES ASSOCIATE ..."), so accuracy
   on the untouched text overstates real-world performance.
3. Tunes the low-confidence fallback (probability threshold, minimum word
   count, size-normalized vs. raw skill overlap) on out-of-fold predictions
   from the TRAINING split only, using full resumes and short 60/120/250-word
   snippets that mimic student resumes. The test split is used only to report
   the chosen policy.
4. Refits the production model on all rows and saves:
     models/role_classifier.joblib, models/role_vectorizer.joblib,
     reports/role_classifier_metrics.json

Run:
    python scripts/train_role_classifier.py
"""

from __future__ import annotations

import itertools
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

from app.services.data_cleaning import clean_text, strip_leading_title
from app.services.role_predictor import (
    VERY_LOW_CONFIDENCE,
    _load_role_profiles,
    blend_with_skill_overlap,
    is_low_confidence,
)
from app.services.skill_extractor import extract_skills

logger = logging.getLogger(__name__)

INPUT_CSV = REPO_ROOT / "data" / "raw" / "Resume.csv.gz"
MODEL_OUT = REPO_ROOT / "models" / "role_classifier.joblib"
VECTORIZER_OUT = REPO_ROOT / "models" / "role_vectorizer.joblib"
METRICS_OUT = REPO_ROOT / "reports" / "role_classifier_metrics.json"

RANDOM_STATE = 42
SMALLEST_CLASSES: List[str] = ["AGRICULTURE", "AUTOMOBILE", "BPO"]
SNIPPET_LENGTHS: Tuple[int, ...] = (60, 120, 250)

# Chosen by 5-fold CV on the training split (title-removed accuracy):
# sublinear_tf and min_df=2 help short and title-less resumes; 5k vs 20k
# features and C=1 vs 0.3 were within noise / worse.
VECTORIZER_PARAMS: Dict[str, Any] = {
    "max_features": 5000,
    "stop_words": "english",
    "ngram_range": (1, 2),
    "sublinear_tf": True,
    "min_df": 2,
}

# Fallback policy grid (production defaults in app/services/role_predictor.py)
THRESHOLD_GRID = (0.25, 0.35, 0.45)
MIN_WORDS_GRID = (100, 150, 200)


def _sep(char: str = "=", width: int = 78) -> str:
    return char * width


def _snippet(text: str, n_words: int, rng: np.random.Generator) -> str:
    """Contiguous random window of n_words from text (whole text if shorter)."""
    words = text.split()
    if len(words) <= n_words:
        return text
    start = int(rng.integers(0, len(words) - n_words))
    return " ".join(words[start : start + n_words])


def _new_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(**VECTORIZER_PARAMS)


def _new_calibrated_svc() -> CalibratedClassifierCV:
    return CalibratedClassifierCV(
        estimator=LinearSVC(random_state=RANDOM_STATE, max_iter=5000), cv=5
    )


def _topk_accuracy(proba: np.ndarray, classes: np.ndarray, y_true: Sequence[str], k: int) -> float:
    top = np.argsort(proba, axis=1)[:, ::-1][:, :k]
    return float(np.mean([y in classes[idx] for y, idx in zip(y_true, top)]))


def load_dataset(path: Path = INPUT_CSV) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Resume dataset not found at {path}")
    df = pd.read_csv(path)
    df["text"] = df["Resume_str"].map(clean_text)
    df["text_no_title"] = df["Resume_str"].map(strip_leading_title).map(clean_text)
    return df


def benchmark_candidates(
    train: pd.DataFrame, test: pd.DataFrame
) -> Tuple[str, Dict[str, Dict[str, float]]]:
    """Fit candidate classifiers and compare them on the held-out test split."""
    vectorizer = _new_vectorizer()
    X_train = vectorizer.fit_transform(train["text"])
    X_test = vectorizer.transform(test["text"])
    X_test_nt = vectorizer.transform(test["text_no_title"])

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=2000, random_state=RANDOM_STATE),
        "LinearSVC": LinearSVC(random_state=RANDOM_STATE, max_iter=5000),
        "MultinomialNB": MultinomialNB(),
    }
    results: Dict[str, Dict[str, float]] = {}
    print(_sep())
    print("CANDIDATE BENCHMARK (stratified 80/20 test split)")
    print(_sep())
    print(f"{'Model':<20} | {'Acc':>6} | {'MacroF1':>7} | {'Acc no-title':>12} | {'F1 no-title':>11} | {'Small-class F1':>14}")
    for name, clf in candidates.items():
        clf.fit(X_train, train["Category"])
        pred = clf.predict(X_test)
        pred_nt = clf.predict(X_test_nt)
        report = classification_report(test["Category"], pred_nt, output_dict=True, zero_division=0)
        results[name] = {
            "accuracy": float(accuracy_score(test["Category"], pred)),
            "macro_f1": float(f1_score(test["Category"], pred, average="macro")),
            "accuracy_no_title": float(accuracy_score(test["Category"], pred_nt)),
            "macro_f1_no_title": float(f1_score(test["Category"], pred_nt, average="macro")),
            "small_classes_f1_no_title": float(
                np.mean([report.get(c, {}).get("f1-score", 0.0) for c in SMALLEST_CLASSES])
            ),
        }
        r = results[name]
        print(
            f"{name:<20} | {r['accuracy']:>6.3f} | {r['macro_f1']:>7.3f} | "
            f"{r['accuracy_no_title']:>12.3f} | {r['macro_f1_no_title']:>11.3f} | "
            f"{r['small_classes_f1_no_title']:>14.3f}"
        )
    winner = max(results, key=lambda n: results[n]["macro_f1_no_title"])
    print(f"\nWinner by title-removed macro F1: {winner}")
    return winner, results


def _make_estimator(winner: str):
    if winner == "LinearSVC":
        return _new_calibrated_svc()
    if winner == "LogisticRegression":
        return LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)
    return MultinomialNB()


def _evaluation_texts(
    df: pd.DataFrame, rng: np.random.Generator
) -> Dict[str, Tuple[List[str], List[str]]]:
    """Title-removed full resumes plus short snippets of each, with labels."""
    sets = {"full_no_title": (df["text_no_title"].tolist(), df["Category"].tolist())}
    for n in SNIPPET_LENGTHS:
        sets[f"snippet_{n}"] = (
            [_snippet(t, n, rng) for t in df["text_no_title"]],
            df["Category"].tolist(),
        )
    return sets


def _policy_accuracy(
    proba: np.ndarray,
    classes: np.ndarray,
    texts: List[str],
    skills: List[set],
    y_true: List[str],
    profiles: Dict[str, List[str]],
    threshold: float,
    min_words: int,
    size_normalized: bool,
) -> Tuple[float, float, float]:
    """Top-1 accuracy, top-3 accuracy and low-confidence rate of a fallback policy."""
    top1, top3, low = 0, 0, 0
    for p, text, sk, y in zip(proba, texts, skills, y_true):
        low_conf = is_low_confidence(p, threshold=threshold, word_count=len(text.split()), min_word_count=min_words)
        eff = p
        if low_conf:
            low += 1
            eff = blend_with_skill_overlap(
                p, classes, sk, profiles, VERY_LOW_CONFIDENCE, size_normalized=size_normalized
            )
        order = np.argsort(eff)[::-1]
        top1 += classes[order[0]] == y
        top3 += y in classes[order[:3]]
    n = len(y_true)
    return top1 / n, top3 / n, low / n


def tune_fallback_policy(
    train: pd.DataFrame, winner: str, profiles: Dict[str, List[str]]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Grid-search the fallback policy on out-of-fold predictions of the training split."""
    rng = np.random.default_rng(RANDOM_STATE)
    eval_sets = _evaluation_texts(train, rng)
    oof: Dict[str, np.ndarray] = {}
    classes = None
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    for name in eval_sets:
        oof[name] = np.zeros((len(train), train["Category"].nunique()))

    for fit_idx, val_idx in skf.split(train, train["Category"]):
        vec = _new_vectorizer()
        model = _make_estimator(winner)
        model.fit(vec.fit_transform(train["text"].iloc[fit_idx]), train["Category"].iloc[fit_idx])
        classes = model.classes_
        for name, (texts, _) in eval_sets.items():
            oof[name][val_idx] = model.predict_proba(vec.transform([texts[i] for i in val_idx]))

    skills = {name: [extract_skills(t) for t in texts] for name, (texts, _) in eval_sets.items()}

    grid = []
    for threshold, min_words, size_norm in itertools.product(THRESHOLD_GRID, MIN_WORDS_GRID, (True, False)):
        per_set = {}
        for name, (texts, y) in eval_sets.items():
            per_set[name] = _policy_accuracy(
                oof[name], classes, texts, skills[name], y, profiles, threshold, min_words, size_norm
            )[0]
        grid.append(
            {
                "threshold": threshold,
                "min_words": min_words,
                "size_normalized_overlap": size_norm,
                "top1_by_set": per_set,
                "mean_top1": float(np.mean(list(per_set.values()))),
            }
        )

    # ML-only reference (fallback never engaged)
    ml_only = {
        name: float(np.mean(classes[np.argmax(oof[name], axis=1)] == np.array(y)))
        for name, (_, y) in eval_sets.items()
    }

    print("\n" + _sep())
    print("FALLBACK POLICY TUNING (out-of-fold, training split only; top-1 accuracy)")
    print(_sep())
    print("  ML only (no fallback): " + "  ".join(f"{k}={v:.3f}" for k, v in ml_only.items()))
    for g in sorted(grid, key=lambda g: -g["mean_top1"])[:6]:
        print(
            f"  thr={g['threshold']:.2f} min_words={g['min_words']:>3} size_norm={str(g['size_normalized_overlap']):<5} "
            f"mean={g['mean_top1']:.3f}  " + "  ".join(f"{k}={v:.3f}" for k, v in g["top1_by_set"].items())
        )
    best = max(grid, key=lambda g: g["mean_top1"])
    best = {**best, "ml_only_top1_by_set": ml_only}
    return best, grid


def evaluate_on_test(
    train: pd.DataFrame,
    test: pd.DataFrame,
    winner: str,
    policy: Dict[str, Any],
    profiles: Dict[str, List[str]],
) -> Dict[str, Any]:
    """Report the chosen model + fallback policy on the untouched test split."""
    vec = _new_vectorizer()
    model = _make_estimator(winner)
    model.fit(vec.fit_transform(train["text"]), train["Category"])
    classes = model.classes_

    proba_full = model.predict_proba(vec.transform(test["text"]))
    rng = np.random.default_rng(RANDOM_STATE + 1)
    eval_sets = _evaluation_texts(test, rng)

    result: Dict[str, Any] = {
        "test_resumes": int(len(test)),
        "with_title": {
            "top1_accuracy": float(np.mean(classes[np.argmax(proba_full, 1)] == test["Category"].to_numpy())),
            "top3_accuracy": _topk_accuracy(proba_full, classes, test["Category"].tolist(), 3),
            "macro_f1": float(f1_score(test["Category"], classes[np.argmax(proba_full, 1)], average="macro")),
        },
    }
    for name, (texts, y) in eval_sets.items():
        proba = model.predict_proba(vec.transform(texts))
        pred = classes[np.argmax(proba, 1)]
        skills = [extract_skills(t) for t in texts]
        top1, top3, low_rate = _policy_accuracy(
            proba, classes, texts, skills, y, profiles,
            policy["threshold"], policy["min_words"], policy["size_normalized_overlap"],
        )
        result[name] = {
            "ml_only_top1_accuracy": float(np.mean(pred == np.array(y))),
            "ml_only_top3_accuracy": _topk_accuracy(proba, classes, y, 3),
            "ml_only_macro_f1": float(f1_score(y, pred, average="macro")),
            "with_fallback_top1_accuracy": float(top1),
            "with_fallback_top3_accuracy": float(top3),
            "low_confidence_rate": float(low_rate),
        }

    print("\n" + _sep())
    print("HELD-OUT TEST SPLIT (chosen model + fallback policy)")
    print(_sep())
    wt = result["with_title"]
    print(f"  with title    : top1={wt['top1_accuracy']:.3f}  top3={wt['top3_accuracy']:.3f}  macroF1={wt['macro_f1']:.3f}  (optimistic)")
    for name in eval_sets:
        r = result[name]
        print(
            f"  {name:<14}: ML top1={r['ml_only_top1_accuracy']:.3f} top3={r['ml_only_top3_accuracy']:.3f} | "
            f"with fallback top1={r['with_fallback_top1_accuracy']:.3f} top3={r['with_fallback_top3_accuracy']:.3f} "
            f"| low-confidence {r['low_confidence_rate']:.0%}"
        )
    return result


def main() -> None:
    df = load_dataset()
    print(f"Loaded {len(df):,} resumes, {df['Category'].nunique()} categories")
    train, test = train_test_split(
        df, test_size=0.20, random_state=RANDOM_STATE, stratify=df["Category"]
    )
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)
    profiles = _load_role_profiles()

    winner, benchmark = benchmark_candidates(train, test)
    policy, grid = tune_fallback_policy(train, winner, profiles)
    print(
        f"\nChosen policy: threshold={policy['threshold']}, min_words={policy['min_words']}, "
        f"size_normalized_overlap={policy['size_normalized_overlap']}"
    )
    test_metrics = evaluate_on_test(train, test, winner, policy, profiles)

    # Production artifact: refit on every row
    vectorizer = _new_vectorizer()
    final_model = _make_estimator(winner)
    final_model.fit(vectorizer.fit_transform(df["text"]), df["Category"])
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, MODEL_OUT)
    joblib.dump(vectorizer, VECTORIZER_OUT)
    print(f"\nSaved {MODEL_OUT.relative_to(REPO_ROOT)} and {VECTORIZER_OUT.relative_to(REPO_ROOT)}")

    metrics = {
        "dataset": {
            "rows": int(len(df)),
            "categories": int(df["Category"].nunique()),
            "class_counts": {k: int(v) for k, v in df["Category"].value_counts().items()},
        },
        "vectorizer_params": {k: (list(v) if isinstance(v, tuple) else v) for k, v in VECTORIZER_PARAMS.items()},
        "benchmark": benchmark,
        "production_model": "CalibratedClassifierCV(LinearSVC, cv=5)" if winner == "LinearSVC" else winner,
        "fallback_policy": {
            "threshold": policy["threshold"],
            "min_words": policy["min_words"],
            "size_normalized_overlap": policy["size_normalized_overlap"],
            "very_low_confidence": VERY_LOW_CONFIDENCE,
            "tuned_on": "5-fold out-of-fold predictions on the training split",
            "oof_top1_by_set": policy["top1_by_set"],
            "oof_ml_only_top1_by_set": policy["ml_only_top1_by_set"],
        },
        "fallback_policy_grid": grid,
        "test": test_metrics,
        "scikit_learn_version": sklearn.__version__,
    }
    METRICS_OUT.parent.mkdir(parents=True, exist_ok=True)
    METRICS_OUT.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"Metrics written to {METRICS_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
