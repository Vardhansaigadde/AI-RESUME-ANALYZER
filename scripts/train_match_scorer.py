"""Model training pipeline for resume-job match scoring.

The dataset contains 2,385 rows but only 23 unique job descriptions, so a
plain random split would put the same job description in both train and test
and inflate every metric. All evaluation here is grouped by job_text:

1. cross_validate(): GroupKFold (k=5) over job descriptions for every
   candidate regressor. RobustScaler is fitted inside each fold (Pipeline), so
   no test-fold statistics leak into training. These are the numbers quoted
   in README.md.
2. mismatch_sanity_check(): the dataset only pairs resumes with jobs from
   their own category, so it has no labels for clearly mismatched pairs. This
   check scores resumes against jobs from OTHER categories and verifies the
   model ranks them below same-category pairs. It measures behaviour; it does
   not invent labels.
3. train_full(): fits the production RobustScaler + Ridge on all rows.

Run:
    python -m app.ml.features          # regenerate data/processed/features.csv
    python scripts/train_match_scorer.py

Writes models/match_scorer.joblib, models/feature_scaler.joblib and
reports/match_scorer_metrics.json.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

from app.ml.features import FEATURE_COLUMNS, build_features

logger = logging.getLogger(__name__)

FEATURES_CSV = REPO_ROOT / "data" / "processed" / "features.csv"
SOURCE_CSV = REPO_ROOT / "data" / "processed" / "job_resume_fit_clean.csv.gz"
MODEL_OUT = REPO_ROOT / "models" / "match_scorer.joblib"
SCALER_OUT = REPO_ROOT / "models" / "feature_scaler.joblib"
METRICS_OUT = REPO_ROOT / "reports" / "match_scorer_metrics.json"

TARGET_COLUMN = "ai_match_score"
N_FOLDS = 5
RANDOM_STATE = 42

CANDIDATES: Dict[str, object] = {
    "Ridge": Ridge(alpha=1.0),
    "GradientBoosting": GradientBoostingRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=RANDOM_STATE,
    ),
    "RandomForest": RandomForestRegressor(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=4,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
}


def _sep(char: str = "=", width: int = 72) -> str:
    return char * width


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def load_training_data(
    features_csv: Path = FEATURES_CSV,
    source_csv: Path = SOURCE_CSV,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    """Load the feature matrix, target, job-description groups and source rows."""
    if not features_csv.exists():
        raise FileNotFoundError(
            f"Feature matrix not found at {features_csv}. Run `python -m app.ml.features` first."
        )
    if not source_csv.exists():
        raise FileNotFoundError(f"Source CSV not found at {source_csv}")

    feat_df = pd.read_csv(features_csv)
    src_df = pd.read_csv(source_csv)
    if len(src_df) != len(feat_df):
        raise ValueError(
            f"Row count mismatch: {features_csv.name} has {len(feat_df)} rows "
            f"but {source_csv.name} has {len(src_df)} rows."
        )

    X = feat_df[FEATURE_COLUMNS].copy()
    y = feat_df[TARGET_COLUMN].astype(float)
    groups = src_df["job_text"].fillna("").astype(str)
    return X, y, groups, src_df


def cross_validate(
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series,
    n_folds: int = N_FOLDS,
) -> Dict[str, Dict[str, float]]:
    """GroupKFold cross-validation (grouped by job description) for every candidate.

    Returns:
        {model_name: {"r2_mean", "r2_std", "rmse_mean", "rmse_std", "mae_mean", "mae_std"}}
    """
    gkf = GroupKFold(n_splits=n_folds)
    results: Dict[str, Dict[str, float]] = {}

    print(_sep())
    print(f"GROUPKFOLD CROSS-VALIDATION (k={n_folds}, grouped by job description)")
    print(f"  rows={len(X):,}  job descriptions={groups.nunique()}")
    print(_sep())

    for name, estimator in CANDIDATES.items():
        r2s, rmses, maes = [], [], []
        for train_idx, test_idx in gkf.split(X, y, groups=groups):
            model = make_pipeline(RobustScaler(), clone(estimator))
            model.fit(X.iloc[train_idx], y.iloc[train_idx])
            pred = model.predict(X.iloc[test_idx])
            y_true = y.iloc[test_idx].to_numpy()
            r2s.append(r2_score(y_true, pred))
            rmses.append(_rmse(y_true, pred))
            maes.append(mean_absolute_error(y_true, pred))

        results[name] = {
            "r2_mean": float(np.mean(r2s)),
            "r2_std": float(np.std(r2s)),
            "rmse_mean": float(np.mean(rmses)),
            "rmse_std": float(np.std(rmses)),
            "mae_mean": float(np.mean(maes)),
            "mae_std": float(np.std(maes)),
        }
        r = results[name]
        print(
            f"  {name:<18} R2 = {r['r2_mean']:.4f} +/- {r['r2_std']:.4f} | "
            f"RMSE = {r['rmse_mean']:.2f} +/- {r['rmse_std']:.2f} | "
            f"MAE = {r['mae_mean']:.2f} +/- {r['mae_std']:.2f}"
        )
    print(_sep())
    return results


def train_full(
    X: pd.DataFrame,
    y: pd.Series,
    model_out: Path = MODEL_OUT,
    scaler_out: Path = SCALER_OUT,
    alpha: float = 1.0,
) -> Tuple[Ridge, RobustScaler, Dict[str, Any]]:
    """Fit the production RobustScaler + Ridge on every row and persist both."""
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    model = Ridge(alpha=alpha)
    model.fit(X_scaled, y)

    y_pred = model.predict(X_scaled)
    info: Dict[str, Any] = {
        "in_sample_r2": float(r2_score(y, y_pred)),
        "in_sample_rmse": _rmse(y.to_numpy(), y_pred),
        "intercept": float(model.intercept_),
        "coefficients_scaled": dict(zip(FEATURE_COLUMNS, map(float, model.coef_))),
        "points_per_unit": {
            col: float(coef / scale)
            for col, coef, scale in zip(FEATURE_COLUMNS, model.coef_, scaler.scale_)
        },
    }

    print("\nPRODUCTION RIDGE (fit on all rows)")
    print(f"  In-sample R2 = {info['in_sample_r2']:.4f}  (training fit, NOT generalization)")
    for col in FEATURE_COLUMNS:
        print(
            f"  {col:<22} scaled coef = {info['coefficients_scaled'][col]:>8.3f}"
            f"   points per raw unit = {info['points_per_unit'][col]:>10.4f}"
        )
    print(f"  intercept (median pair) = {info['intercept']:.2f}")

    scaler_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, scaler_out)
    joblib.dump(model, model_out)
    print(f"\nSaved {scaler_out.relative_to(REPO_ROOT)} and {model_out.relative_to(REPO_ROOT)}")
    return model, scaler, info


def mismatch_sanity_check(
    model: Ridge,
    scaler: RobustScaler,
    src_df: pd.DataFrame,
    n_pairs: int = 300,
    random_state: int = RANDOM_STATE,
) -> Dict[str, float]:
    """Score resumes against jobs from other categories vs. their own category.

    The training data never contains a cross-category pair, so this is the only
    evidence of how the model treats an obvious mismatch (e.g. a nurse resume
    against a software job).
    """
    rng = np.random.default_rng(random_state)
    jobs_by_category = (
        src_df.drop_duplicates("job_text").set_index("category")["job_text"].to_dict()
    )
    categories = list(jobs_by_category)
    sample = src_df.sample(n=min(n_pairs, len(src_df)), random_state=random_state)

    def score(resume: str, job: str) -> float:
        feats = build_features(resume, job, as_dataframe=True)[FEATURE_COLUMNS]
        return float(np.clip(model.predict(scaler.transform(feats))[0], 0.0, 100.0))

    same, other = [], []
    for _, row in sample.iterrows():
        same.append(score(row["resume_text"], row["job_text"]))
        other_cat = rng.choice([c for c in categories if c != row["category"]])
        other.append(score(row["resume_text"], jobs_by_category[other_cat]))

    same_arr, other_arr = np.array(same), np.array(other)
    result = {
        "pairs": int(len(sample)),
        "same_category_mean_score": float(same_arr.mean()),
        "other_category_mean_score": float(other_arr.mean()),
        "other_category_p90_score": float(np.percentile(other_arr, 90)),
        "share_same_category_scored_higher": float(np.mean(same_arr > other_arr)),
    }
    print("\nMISMATCHED-PAIR SANITY CHECK (resume vs. a job from another category)")
    print(f"  pairs                      : {result['pairs']}")
    print(f"  mean score, own category   : {result['same_category_mean_score']:.1f}")
    print(f"  mean score, other category : {result['other_category_mean_score']:.1f}")
    print(f"  90th pct, other category   : {result['other_category_p90_score']:.1f}")
    print(f"  own-category pair ranked higher in {result['share_same_category_scored_higher']:.1%} of cases")
    return result


def main() -> None:
    X, y, groups, src_df = load_training_data()
    cv_results = cross_validate(X, y, groups)
    model, scaler, info = train_full(X, y)
    sanity = mismatch_sanity_check(model, scaler, src_df)

    metrics = {
        "dataset": {
            "rows": int(len(X)),
            "unique_job_descriptions": int(groups.nunique()),
            "target": TARGET_COLUMN,
            "features": FEATURE_COLUMNS,
        },
        "cross_validation": {
            "method": f"GroupKFold(n_splits={N_FOLDS}) grouped by job_text; RobustScaler fitted per fold",
            "results": cv_results,
            "production_model": "Ridge",
        },
        "production_model": info,
        "mismatched_pair_sanity_check": sanity,
        "scikit_learn_version": sklearn.__version__,
    }
    METRICS_OUT.parent.mkdir(parents=True, exist_ok=True)
    METRICS_OUT.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"\nMetrics written to {METRICS_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
