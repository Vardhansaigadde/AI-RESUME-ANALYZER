"""Model training pipeline for resume-job match scoring.

Phase 3.2  –  Group-aware train / test split + model selection.

The dataset contains ~2,385 rows spread across only ~23 unique job
descriptions.  A plain random split would leak job-description text
into both train and test sets, inflating every metric.  Instead we
use GroupShuffleSplit keyed by job_text so that every resume evaluated
against a particular job description lands entirely in either train or
test – never both.

Trains three candidate regressors and picks the best by held-out RMSE:
  1. GradientBoostingRegressor  (default / recommended)
  2. RandomForestRegressor
  3. Ridge regression (linear baseline)

Saves the winning model to models/match_scorer.joblib.
Prints a full evaluation report (RMSE, MAE, R²) on the held-out group.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)

FEATURES_CSV = REPO_ROOT / "data" / "processed" / "features.csv"
SOURCE_CSV = REPO_ROOT / "data" / "processed" / "job_resume_fit_clean.csv"
MODEL_OUT = REPO_ROOT / "models" / "match_scorer.joblib"
SCALER_OUT = REPO_ROOT / "models" / "feature_scaler.joblib"

FEATURE_COLUMNS = [
    "tfidf_similarity",
    "skill_overlap_ratio",
    "resume_word_count",
]

TARGET_COLUMN = "ai_match_score"

CANDIDATES: Dict[str, object] = {
    "GradientBoosting": GradientBoostingRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
    ),
    "RandomForest": RandomForestRegressor(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=4,
        random_state=42,
        n_jobs=-1,
    ),
    "Ridge": Ridge(alpha=1.0),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sep(char: str = "=", width: int = 65) -> str:
    return char * width


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def make_group_split(
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series,
    test_size: float = 0.20,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Group-aware train/test split.

    Ensures every resume evaluated against a given job description ends up
    entirely in either train or test, not split across both.  This prevents
    data leakage caused by the ~23 repeated job descriptions sharing vocabulary
    with every associated resume.

    Args:
        X:            Feature DataFrame (rows = resume-job pairs).
        y:            Target Series (ai_match_score).
        groups:       Series of group labels (job_text or a job_id).
        test_size:    Fraction of groups to hold out (default 20 %).
        random_state: RNG seed for reproducibility.

    Returns:
        (X_train, X_test, y_train, y_test)
    """
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    train_groups = groups.iloc[train_idx].unique().tolist()
    test_groups  = groups.iloc[test_idx].unique().tolist()

    print(_sep())
    print("GROUP-AWARE TRAIN / TEST SPLIT")
    print(_sep())
    print(f"  Total rows       : {len(X):,}")
    print(f"  Total groups     : {groups.nunique():,}  (unique job descriptions)")
    print(f"  Train rows       : {len(train_idx):,}  ({len(train_groups)} job groups)")
    print(f"  Test  rows       : {len(test_idx):,}  ({len(test_groups)} job groups)")
    print(f"  Test  fraction   : {len(test_idx)/len(X)*100:.1f}%")
    print()
    print("  Groups in TRAIN:")
    for g in sorted(train_groups):
        cnt = (groups == g).sum()
        print(f"    [{cnt:>4} rows]  {str(g)[:80]}")
    print()
    print("  Groups in TEST:")
    for g in sorted(test_groups):
        cnt = (groups == g).sum()
        print(f"    [{cnt:>4} rows]  {str(g)[:80]}")
    print(_sep())

    return (
        X.iloc[train_idx].reset_index(drop=True),
        X.iloc[test_idx].reset_index(drop=True),
        y.iloc[train_idx].reset_index(drop=True),
        y.iloc[test_idx].reset_index(drop=True),
    )


# ---------------------------------------------------------------------------
# Evaluation helper
# ---------------------------------------------------------------------------

def _evaluate(
    name: str,
    model: object,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, float]:
    """Fit model on train, evaluate on test, return metric dict."""
    model.fit(X_train, y_train)  # type: ignore[union-attr]
    y_pred = model.predict(X_test)  # type: ignore[union-attr]

    metrics = {
        "rmse": _rmse(y_test.values, y_pred),
        "mae":  float(mean_absolute_error(y_test, y_pred)),
        "r2":   float(r2_score(y_test, y_pred)),
    }

    # Also evaluate on train to check for over-fitting
    y_train_pred = model.predict(X_train)  # type: ignore[union-attr]
    train_rmse = _rmse(y_train.values, y_train_pred)

    print(f"\n  {name}")
    print(f"    Train RMSE : {train_rmse:.4f}   |  Test RMSE : {metrics['rmse']:.4f}")
    print(f"    Test  MAE  : {metrics['mae']:.4f}  |  Test R2   : {metrics['r2']:.4f}")

    return metrics


# ---------------------------------------------------------------------------
# Main training entry point
# ---------------------------------------------------------------------------

def train(
    features_csv: Path = FEATURES_CSV,
    source_csv: Path = SOURCE_CSV,
    model_out: Path = MODEL_OUT,
    test_size: float = 0.20,
    random_state: int = 42,
) -> object:
    """Run full training pipeline and persist the best model.

    Args:
        features_csv:  Pre-computed feature matrix (from features.py).
        source_csv:    Original dataset (needed for job_text group labels).
        model_out:     Destination path for the serialised model.
        test_size:     Fraction of job groups to hold out.
        random_state:  Global RNG seed.

    Returns:
        The fitted best-performing sklearn estimator.
    """
    # ------------------------------------------------------------------
    # 1. Load features
    # ------------------------------------------------------------------
    print("\n" + _sep())
    print("PHASE 3 -- MODEL TRAINING")
    print(_sep())

    if not features_csv.exists():
        raise FileNotFoundError(
            f"Feature matrix not found at {features_csv}. "
            "Run `python -m app.ml.features` first."
        )

    feat_df = pd.read_csv(features_csv)
    logger.info("Loaded feature matrix: %s", feat_df.shape)

    X = feat_df[FEATURE_COLUMNS].copy()
    y = feat_df[TARGET_COLUMN].astype(float)

    print(f"\n  Feature matrix : {X.shape[0]:,} rows x {X.shape[1]} features")
    print(f"  Target range   : [{y.min():.1f}, {y.max():.1f}]  mean={y.mean():.2f}")

    # ------------------------------------------------------------------
    # 2. Build group labels from source CSV  (job_text column)
    # ------------------------------------------------------------------
    if not source_csv.exists():
        raise FileNotFoundError(f"Source CSV not found at {source_csv}")

    src_df = pd.read_csv(source_csv)
    if len(src_df) != len(feat_df):
        raise ValueError(
            f"Row count mismatch: features.csv has {len(feat_df)} rows "
            f"but {source_csv.name} has {len(src_df)} rows."
        )

    groups = src_df["job_text"].fillna("").astype(str)

    print(f"\n  Unique job groups: {groups.nunique()}")
    group_counts = groups.value_counts()
    print("  Rows per group (top 5):")
    for jt, cnt in group_counts.head(5).items():
        print(f"    [{cnt:>4}]  {str(jt)[:75]}...")

    # ------------------------------------------------------------------
    # 3. Group-aware split
    # ------------------------------------------------------------------
    print()
    X_train, X_test, y_train, y_test = make_group_split(
        X, y, groups, test_size=test_size, random_state=random_state
    )

    # ------------------------------------------------------------------
    # 4. Scale features & compare candidates
    # ------------------------------------------------------------------
    print("\n" + _sep())
    print("MODEL COMPARISON (features scaled with RobustScaler; test set = held-out job groups)")
    print(_sep())

    scaler = RobustScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train), columns=FEATURE_COLUMNS
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=FEATURE_COLUMNS
    )

    results: Dict[str, Dict[str, float]] = {}
    fitted_models: Dict[str, object] = {}

    for name, model in CANDIDATES.items():
        metrics = _evaluate(name, model, X_train_scaled, y_train, X_test_scaled, y_test)
        results[name] = metrics
        fitted_models[name] = model

    # ------------------------------------------------------------------
    # 5. Select winner (lowest test RMSE)
    # ------------------------------------------------------------------
    best_name = min(results, key=lambda n: results[n]["rmse"])
    best_model = fitted_models[best_name]
    best_metrics = results[best_name]

    print("\n" + _sep())
    print(f"WINNER: {best_name}")
    print(f"  Test RMSE : {best_metrics['rmse']:.4f}")
    print(f"  Test MAE  : {best_metrics['mae']:.4f}")
    print(f"  Test R2   : {best_metrics['r2']:.4f}")
    print(_sep())

    # Feature importances (tree-based models only)
    if hasattr(best_model, "feature_importances_"):
        print("\nFeature importances:")
        importances = best_model.feature_importances_
        for feat, imp in sorted(
            zip(FEATURE_COLUMNS, importances), key=lambda x: -x[1]
        ):
            bar = "X" * int(imp * 40)
            print(f"  {feat:<30}  {imp:.4f}  {bar}")

    # ------------------------------------------------------------------
    # 6. Persist model & scaler
    # ------------------------------------------------------------------
    scaler_out = SCALER_OUT
    scaler_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, scaler_out)
    print(f"\nScaler saved to: {scaler_out}")

    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, model_out)
    print(f"Model saved to: {model_out}")

    return best_model


def train_full(
    features_csv: Path = FEATURES_CSV,
    model_out: Path = MODEL_OUT,
    scaler_out: Path = SCALER_OUT,
    alpha: float = 1.0,
) -> Tuple[Ridge, RobustScaler]:
    """Train Ridge regression on the entire 2,385-row dataset with RobustScaler.

    Fits RobustScaler on all training features, scales the feature matrix,
    fits Ridge(alpha=alpha), and persists both artifacts:
    - models/feature_scaler.joblib
    - models/match_scorer.joblib
    """
    if not features_csv.exists():
        raise FileNotFoundError(f"Feature matrix not found at {features_csv}")

    feat_df = pd.read_csv(features_csv)
    X = feat_df[FEATURE_COLUMNS]
    y = feat_df[TARGET_COLUMN].astype(float)

    print("\n" + _sep())
    print("TRAINING FINAL RIDGE MODEL ON FULL DATASET (3 FEATURES) WITH ROBUSTSCALER")
    print(_sep())
    print(f"  Rows        : {len(X):,}")
    print(f"  Features    : {list(X.columns)}")
    print(f"  Target mean : {y.mean():.2f} (std={y.std():.2f})")

    # Fit RobustScaler
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    model = Ridge(alpha=alpha)
    model.fit(X_scaled, y)

    # In-sample metrics for reference
    y_pred = model.predict(X_scaled)
    print(f"  In-sample RMSE : {_rmse(y.values, y_pred):.4f}")
    print(f"  In-sample R2   : {r2_score(y, y_pred):.4f}")

    print("\n  Coefficients (scaled):")
    for col, coef, scale in zip(FEATURE_COLUMNS, model.coef_, scaler.scale_):
        print(f"    {col:<25}: scaled = {coef:>10.4f}  (unscaled equivalent = {coef/scale:>10.4f})")
    print(f"    {'intercept':<25}: {model.intercept_:>10.4f}")

    # Persist scaler and model
    scaler_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, scaler_out)
    print(f"\nSaved production RobustScaler to: {scaler_out}")

    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)
    print(f"Saved production Ridge model to: {model_out}")
    print(_sep() + "\n")
    return model, scaler


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    if "--split" in sys.argv:
        train()
    else:
        train_full()
