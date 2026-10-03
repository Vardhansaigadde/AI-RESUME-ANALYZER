"""End-to-end pipeline integration check.

Runs the complete inference stack (DOCX parsing -> skill extraction -> match
scoring -> suggestions -> role prediction with confidence fallback) on a
50-row sample of data/processed/job_resume_fit_clean.csv.gz plus a handful of
short, student-style resumes, and writes reports/evaluation_summary.md.

This is a wiring / integration check, NOT a generalization estimate: both
production models are refit on their full datasets, so the 50 sampled rows are
training data. Generalization numbers come from the training scripts and are
read from:
  - reports/match_scorer_metrics.json   (scripts/train_match_scorer.py)
  - reports/role_classifier_metrics.json (scripts/train_role_classifier.py)

Run:
    python scripts/evaluate_pipeline.py
"""

from __future__ import annotations

from datetime import date
import io
import json
import logging
from pathlib import Path
import sys
from typing import Any

import docx

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.services.data_cleaning import clean_text
from app.services.matcher import match_resume_to_job
from app.services.parser import extract_text_from_file
from app.services.role_predictor import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MIN_WORD_COUNT,
    REPORTED_CONFIDENCE_THRESHOLD,
    _load_classifier,
    _load_vectorizer,
    clear_role_predictor_cache,
    predict_roles_with_confidence,
)
from app.services.suggestions import generate_suggestions
from scripts.synthetic_resumes import SYNTHETIC_SHORT_RESUMES

logger = logging.getLogger(__name__)

FIT_CLEAN_CSV = REPO_ROOT / "data" / "processed" / "job_resume_fit_clean.csv.gz"
MATCH_METRICS_JSON = REPO_ROOT / "reports" / "match_scorer_metrics.json"
ROLE_METRICS_JSON = REPO_ROOT / "reports" / "role_classifier_metrics.json"
REPORT_MD = REPO_ROOT / "reports" / "evaluation_summary.md"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run the training scripts first (see README).")
    return json.loads(path.read_text(encoding="utf-8"))


def _docx_bytes(text: str) -> bytes:
    document = docx.Document()
    document.add_paragraph(text)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def run_sample_evaluation(n_samples: int = 50, random_state: int = 42) -> pd.DataFrame:
    """Run the full pipeline on sampled dataset rows (in-sample integration check)."""
    df = pd.read_csv(FIT_CLEAN_CSV).sample(n=n_samples, random_state=random_state)
    rows = []
    for _, row in df.iterrows():
        parsed = extract_text_from_file(_docx_bytes(str(row["resume_text"])), "resume.docx")
        match = match_resume_to_job(parsed, str(row["job_text"]))
        suggestions = generate_suggestions(match["missing_skills"], parsed)
        roles, confidence = predict_roles_with_confidence(parsed, top_n=3)
        predicted = [r["role"] for r in roles]
        true_category = str(row["category"]).strip().upper()
        rows.append(
            {
                "id": row["ID"],
                "category": true_category,
                "resume_words": len(parsed.split()),
                "true_score": float(row["ai_match_score"]),
                "pred_score": float(match["match_score"]),
                "suggestions": len(suggestions),
                "predicted_roles": predicted,
                "top1_hit": bool(predicted) and predicted[0] == true_category,
                "top3_hit": true_category in predicted,
                "confidence": confidence,
            }
        )
    return pd.DataFrame(rows)


def run_sparse_cohort() -> list[dict[str, Any]]:
    """Compare raw ML predictions with the fallback on short student-style resumes."""
    clf, vec = _load_classifier(), _load_vectorizer()
    records = []
    for item in SYNTHETIC_SHORT_RESUMES:
        proba = clf.predict_proba(vec.transform([clean_text(item["text"])]))[0]
        top = int(np.argmax(proba))
        roles, confidence = predict_roles_with_confidence(item["text"], top_n=3)
        records.append(
            {
                **item,
                "words": len(item["text"].split()),
                "raw_top1": str(clf.classes_[top]),
                "raw_top1_prob": float(proba[top]) * 100,
                "final_top1": roles[0]["role"],
                "final_top1_pct": roles[0]["match_percent"],
                "final_top3": [r["role"] for r in roles],
                "confidence": confidence,
            }
        )
    return records


def build_report(sample: pd.DataFrame, sparse: list[dict[str, Any]]) -> str:
    match_metrics = _load_json(MATCH_METRICS_JSON)
    role_metrics = _load_json(ROLE_METRICS_JSON)
    cv = match_metrics["cross_validation"]["results"]["Ridge"]
    sanity = match_metrics["mismatched_pair_sanity_check"]
    test = role_metrics["test"]
    policy = role_metrics["fallback_policy"]

    mae = mean_absolute_error(sample["true_score"], sample["pred_score"])
    rmse = float(np.sqrt(mean_squared_error(sample["true_score"], sample["pred_score"])))
    r2 = r2_score(sample["true_score"], sample["pred_score"])

    md = f"""# End-to-End Pipeline Evaluation

**Generated**: {date.today().isoformat()} by `scripts/evaluate_pipeline.py`

This report has two parts:

1. **Generalization benchmarks**, copied from the metrics the training scripts write
   (`reports/match_scorer_metrics.json`, `reports/role_classifier_metrics.json`).
   These are the numbers to quote.
2. **An integration check** that runs the full production pipeline on 50 dataset rows and
   19 short synthetic resumes. Both models are refit on all their data before deployment,
   so the 50 rows are training data: this part proves the wiring works, not that the
   models generalize.

## 1. Generalization benchmarks

### Match scorer (Ridge on 3 features)

GroupKFold, k = 5, grouped by job description ({match_metrics["dataset"]["unique_job_descriptions"]} unique jobs,
{match_metrics["dataset"]["rows"]:,} pairs):

| Metric | Value |
| --- | --- |
| R² | {cv["r2_mean"]:.3f} ± {cv["r2_std"]:.3f} |
| RMSE (0–100 scale) | {cv["rmse_mean"]:.2f} ± {cv["rmse_std"]:.2f} |
| MAE | {cv["mae_mean"]:.2f} ± {cv["mae_std"]:.2f} |

Mismatched-pair check: the dataset only pairs resumes with jobs from their own category, so
{sanity["pairs"]} resumes were also scored against a job from another category. Mean score is
{sanity["same_category_mean_score"]:.1f} for own-category pairs vs {sanity["other_category_mean_score"]:.1f} for
other-category pairs, and the own-category pair scores higher in
{sanity["share_same_category_scored_higher"]:.0%} of cases.

### Role classifier ({role_metrics["production_model"]})

Stratified 80/20 split, {test["test_resumes"]} test resumes. Most dataset resumes open with an
ALL-CAPS title that repeats the label, so accuracy is shown with and without that line:

| Test set | Top-1 (ML only) | Top-3 (ML only) | Top-1 with fallback | Low-confidence rate |
| --- | --- | --- | --- | --- |
| Full resume, title kept (optimistic) | {test["with_title"]["top1_accuracy"]:.1%} | {test["with_title"]["top3_accuracy"]:.1%} | – | – |
"""
    for key, label in [
        ("full_no_title", "Full resume, title removed"),
        ("snippet_250", "250-word snippet"),
        ("snippet_120", "120-word snippet"),
        ("snippet_60", "60-word snippet"),
    ]:
        r = test[key]
        md += (
            f"| {label} | {r['ml_only_top1_accuracy']:.1%} | {r['ml_only_top3_accuracy']:.1%} | "
            f"{r['with_fallback_top1_accuracy']:.1%} | {r['low_confidence_rate']:.0%} |\n"
        )

    md += f"""
The "with fallback" column is slightly lower than ML-only on these dataset resumes; see the
short synthetic resumes in section 2 for why the fallback is still used.

Fallback policy (tuned on out-of-fold training predictions): when the classifier's top probability
is below {DEFAULT_CONFIDENCE_THRESHOLD:.0%} or the resume has fewer than {DEFAULT_MIN_WORD_COUNT} words,
predictions are blended 50/50 with role-profile skill overlap (or replaced by it when the top
probability is below {policy["very_low_confidence"]:.0%}). The API reports `confidence: "low"` when the
final top probability is below {REPORTED_CONFIDENCE_THRESHOLD:.0%}; on held-out resumes and snippets
those predictions were right ~34% of the time, versus ~70% at or above it.

## 2. Integration check (in-sample, 50 dataset rows)

All {len(sample)} rows ran DOCX parsing → skill extraction → match scoring → suggestions → role
prediction without errors.

| Metric | Value |
| --- | --- |
| Match score MAE / RMSE / R² | {mae:.2f} / {rmse:.2f} / {r2:.3f} |
| Role top-1 / top-3 | {sample["top1_hit"].mean():.0%} / {sample["top3_hit"].mean():.0%} |
| Low-confidence predictions | {int((sample["confidence"] == "low").sum())} / {len(sample)} |
| Resume length | median {int(sample["resume_words"].median())} words (range {sample["resume_words"].min()}–{sample["resume_words"].max()}) |

### Short synthetic resumes (fallback behaviour)

Dataset resumes are long professional ones; these {len(sparse)} hand-written short resumes
(`scripts/synthetic_resumes.py`) represent students and freshers. Raw ML top-1 is correct for
**{sum(s["raw_top1"] == s["true_role"] for s in sparse)}/{len(sparse)}**; with the fallback the final
top-1 is correct for **{sum(s["final_top1"] == s["true_role"] for s in sparse)}/{len(sparse)}**. This is why
the fallback is kept even though it costs 1–2 points on dataset resumes.

| Profile | Words | Raw ML top-1 | Final top-1 | In final top-3? | Confidence |
| --- | --- | --- | --- | --- | --- |
"""
    for s in sparse:
        hit = "yes" if s["true_role"] in s["final_top3"] else "no"
        md += (
            f"| {s['name']} (expected {s['true_role']}) | {s['words']} | {s['raw_top1']} ({s['raw_top1_prob']:.1f}%) | "
            f"{s['final_top1']} ({s['final_top1_pct']:.1f}%) | {hit} | `{s['confidence']}` |\n"
        )

    md += """
## Known limitations

- The match-score target (`ai_match_score`) was produced by an AI model, not recruiters, and
  only 23 job descriptions exist, so R² ≈ 0.36 is the realistic ceiling for this data.
- The classifier predicts the dataset's 24 industry categories, not specific job titles, and some
  categories overlap (e.g. ADVOCATE contains patient advocates, which pulls in nursing resumes).
- Confidence flags catch diffuse or short inputs; they cannot catch a model that is confidently wrong.
"""
    return md


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
    clear_role_predictor_cache()
    sample = run_sample_evaluation()
    sparse = run_sparse_cohort()
    REPORT_MD.write_text(build_report(sample, sparse), encoding="utf-8")
    print(f"Report written to {REPORT_MD.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
