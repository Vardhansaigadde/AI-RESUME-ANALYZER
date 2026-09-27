"""Training and evaluation pipeline for resume role classification.

Trains and evaluates three candidate text classifiers on 24 resume categories:
  1. LogisticRegression (multi-class multinomial)
  2. LinearSVC
  3. MultinomialNB

Evaluates on Accuracy and Macro F1 (specifically inspecting the 3 smallest
classes: AGRICULTURE, AUTOMOBILE, BPO). Selects the winning model, fits
probability calibration (CalibratedClassifierCV) if LinearSVC wins or uses
LogisticRegression directly if it wins/is competitive, and persists the
production model and vectorizer to models/.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

logger = logging.getLogger(__name__)

INPUT_CSV = REPO_ROOT / "data" / "processed" / "resume_clean.csv"
MODEL_OUT = REPO_ROOT / "models" / "role_classifier.joblib"
VECTORIZER_OUT = REPO_ROOT / "models" / "role_vectorizer.joblib"

SMALLEST_CLASSES: List[str] = ["AGRICULTURE", "AUTOMOBILE", "BPO"]


def _sep(char: str = "=", width: int = 78) -> str:
    return char * width


def train_and_evaluate_role_classifiers(
    data_path: Path = INPUT_CSV,
    model_output_path: Path = MODEL_OUT,
    vectorizer_output_path: Path = VECTORIZER_OUT,
    random_state: int = 42,
) -> Tuple[object, TfidfVectorizer]:
    """Train candidate role classifiers and persist the best model and vectorizer."""
    print("\n" + _sep())
    print("RESUME ROLE CLASSIFIER: MULTI-MODEL BENCHMARK & SELECTION")
    print(_sep())

    if not data_path.exists():
        raise FileNotFoundError(f"Clean resume dataset not found at {data_path}")

    df = pd.read_csv(data_path)
    print(f"\n1. Loaded dataset: {len(df):,} rows from {data_path.name}")
    print(f"   Unique categories ({df['Category'].nunique()}):")

    cat_counts = df["Category"].value_counts()
    for cat, count in cat_counts.items():
        tag = "  <-- small class" if cat in SMALLEST_CLASSES else ""
        print(f"     - {cat:<24}: {count:>4} samples{tag}")

    X_raw = df["Resume_str"].fillna("").astype(str)
    y = df["Category"].astype(str)

    # 2. Stratified 80/20 train/test split
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw,
        y,
        test_size=0.20,
        random_state=random_state,
        stratify=y,
    )
    print(f"\n2. Stratified split (80/20):")
    print(f"   Train samples: {len(X_train_raw):,}")
    print(f"   Test samples : {len(X_test_raw):,}")

    # 3. TF-IDF vectorization (max_features=5000, English stopwords)
    print(f"\n3. Fitting TF-IDF Vectorizer (max_features=5000, stop_words='english')...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words="english",
        ngram_range=(1, 2),
    )
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)
    print(f"   Vocabulary size: {len(vectorizer.vocabulary_):,} tokens")
    print(f"   X_train shape  : {X_train.shape}")
    print(f"   X_test shape   : {X_test.shape}")

    # 4. Define candidates
    candidates: Dict[str, object] = {
        "LogisticRegression": LogisticRegression(
            max_iter=1000,
            random_state=random_state,
        ),
        "LinearSVC": LinearSVC(
            random_state=random_state,
            max_iter=2000,
        ),
        "MultinomialNB": MultinomialNB(),
    }

    results: Dict[str, Dict[str, object]] = {}
    reports: Dict[str, Dict[str, Dict[str, float]]] = {}

    print("\n" + _sep("-"))
    print("4. Training and Evaluating Models...")
    print(_sep("-"))

    for name, clf in candidates.items():
        print(f"\n---> Training {name}...")
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        acc = float(accuracy_score(y_test, y_pred))
        macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
        weighted_f1 = float(f1_score(y_test, y_pred, average="weighted"))

        # Detailed per-class dictionary report
        report_dict = classification_report(
            y_test, y_pred, output_dict=True, zero_division=0
        )
        reports[name] = report_dict

        # Small classes performance
        small_f1s = {
            cls: report_dict.get(cls, {}).get("f1-score", 0.0)
            for cls in SMALLEST_CLASSES
        }
        small_macro_f1 = float(np.mean(list(small_f1s.values())))

        results[name] = {
            "model": clf,
            "accuracy": acc,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "small_classes_f1": small_f1s,
            "small_macro_f1": small_macro_f1,
            "y_pred": y_pred,
        }

        print(f"     Accuracy    : {acc:.4f}")
        print(f"     Macro F1    : {macro_f1:.4f}  (PRIMARY METRIC)")
        print(f"     Weighted F1 : {weighted_f1:.4f}")

    # 5. Summary benchmark table
    print("\n" + _sep())
    print("OVERALL MODEL BENCHMARK SUMMARY")
    print(_sep())
    print(f"{'Model':<22} | {'Accuracy':>10} | {'Macro F1':>10} | {'Weighted F1':>12} | {'Small Classes F1':>16}")
    print("-" * 78)
    for name, res in sorted(results.items(), key=lambda x: -x[1]["macro_f1"]):
        print(
            f"{name:<22} | {res['accuracy']:>10.4f} | {res['macro_f1']:>10.4f} | "
            f"{res['weighted_f1']:>12.4f} | {res['small_macro_f1']:>16.4f}"
        )
    print(_sep())

    # 6. Performance breakdown on the 3 smallest classes
    print("\n" + _sep())
    print("DEEP DIVE: PERFORMANCE ON 3 SMALLEST CLASSES")
    print(_sep())
    print(f"{'Class (Total N)':<24} | {'Metric':<10} | {'LogisticRegression':>18} | {'LinearSVC':>12} | {'MultinomialNB':>14}")
    print("-" * 88)

    for cls in SMALLEST_CLASSES:
        total_n = cat_counts[cls]
        test_n = int(reports["LogisticRegression"][cls]["support"])
        header_str = f"{cls} (n={total_n}, test={test_n})"

        lr_rep = reports["LogisticRegression"][cls]
        svc_rep = reports["LinearSVC"][cls]
        nb_rep = reports["MultinomialNB"][cls]

        print(f"{header_str:<24} | Precision  | {lr_rep['precision']:>18.4f} | {svc_rep['precision']:>12.4f} | {nb_rep['precision']:>14.4f}")
        print(f"{'':<24} | Recall     | {lr_rep['recall']:>18.4f} | {svc_rep['recall']:>12.4f} | {nb_rep['recall']:>14.4f}")
        print(f"{'':<24} | F1-Score   | {lr_rep['f1-score']:>18.4f} | {svc_rep['f1-score']:>12.4f} | {nb_rep['f1-score']:>14.4f}")
        print("-" * 88)

    # 7. Print Full Classification Reports
    for name in ["LogisticRegression", "LinearSVC", "MultinomialNB"]:
        print("\n" + _sep())
        print(f"FULL CLASSIFICATION REPORT: {name}")
        print(_sep())
        y_pred = results[name]["y_pred"]
        print(classification_report(y_test, y_pred, digits=4, zero_division=0))

    # 8. Winner selection & Calibration logic
    best_overall = max(results, key=lambda n: results[n]["macro_f1"])
    best_small = max(results, key=lambda n: results[n]["small_macro_f1"])

    lr_f1 = results["LogisticRegression"]["macro_f1"]
    svc_f1 = results["LinearSVC"]["macro_f1"]

    print("\n" + _sep())
    print("MODEL SELECTION ANALYSIS & CONCLUSION")
    print(_sep())
    print(f"  Best overall model by Macro F1 : {best_overall} (Macro F1 = {results[best_overall]['macro_f1']:.4f})")
    print(f"  Best model on 3 smallest classes: {best_small} (Small Classes Macro F1 = {results[best_small]['small_macro_f1']:.4f})")

    diff = svc_f1 - lr_f1
    print(f"  LinearSVC vs LogisticRegression Macro F1 Delta: {diff:+.4f}")

    final_model: object
    # If LinearSVC wins by a non-negligible margin (> 0.005), wrap with CalibratedClassifierCV
    if best_overall == "LinearSVC" and diff > 0.005:
        print("\n  LinearSVC won by meaningful margin. Applying CalibratedClassifierCV (cv=5)")
        print("  to provide calibrated predict_proba() probabilities for role matching percentages...")
        base_svc = LinearSVC(random_state=random_state, max_iter=2000)
        calibrated_svc = CalibratedClassifierCV(estimator=base_svc, cv=5)
        calibrated_svc.fit(X_train, y_train)

        # Test calibrated model
        cal_pred = calibrated_svc.predict(X_test)
        cal_acc = accuracy_score(y_test, cal_pred)
        cal_macro = f1_score(y_test, cal_pred, average="macro")
        print(f"  Calibrated LinearSVC test accuracy: {cal_acc:.4f}, Macro F1: {cal_macro:.4f}")
        final_model = calibrated_svc
        winner_name = "Calibrated LinearSVC (5-fold)"
    else:
        # LogisticRegression won or is virtually identical
        if lr_f1 >= svc_f1:
            print("\n  LogisticRegression won on Macro F1 and supports native predict_proba().")
            winner_name = "LogisticRegression"
            final_model = results["LogisticRegression"]["model"]
        else:
            print(f"\n  LogisticRegression is very close behind LinearSVC (delta={diff:.4f} <= 0.005).")
            print("  Using LogisticRegression directly as requested (native calibrated probabilities).")
            winner_name = "LogisticRegression"
            final_model = results["LogisticRegression"]["model"]

    # 9. Retrain final selected model on ALL data (train + test) for production artifact
    print(f"\nRetraining winning model ({winner_name}) on full 2,484 rows...")
    X_full = vectorizer.fit_transform(X_raw)
    final_model.fit(X_full, y)

    # 10. Persist artifacts
    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    vectorizer_output_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(final_model, model_output_path)
    joblib.dump(vectorizer, vectorizer_output_path)

    print(f"\nSaved production artifacts:")
    print(f"  1. Model     -> {model_output_path}")
    print(f"  2. Vectorizer -> {vectorizer_output_path} ({len(vectorizer.vocabulary_):,} features)")
    print(_sep() + "\n")

    return final_model, vectorizer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    train_and_evaluate_role_classifiers()
