# End-to-End Pipeline Evaluation

**Generated**: 2026-10-03 by `scripts/evaluate_pipeline.py`

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

GroupKFold, k = 5, grouped by job description (23 unique jobs,
2,385 pairs):

| Metric | Value |
| --- | --- |
| R² | 0.360 ± 0.175 |
| RMSE (0–100 scale) | 17.93 ± 2.30 |
| MAE | 14.65 ± 2.27 |

Mismatched-pair check: the dataset only pairs resumes with jobs from their own category, so
300 resumes were also scored against a job from another category. Mean score is
45.2 for own-category pairs vs 28.2 for
other-category pairs, and the own-category pair scores higher in
86% of cases.

### Role classifier (CalibratedClassifierCV(LinearSVC, cv=5))

Stratified 80/20 split, 497 test resumes. Most dataset resumes open with an
ALL-CAPS title that repeats the label, so accuracy is shown with and without that line:

| Test set | Top-1 (ML only) | Top-3 (ML only) | Top-1 with fallback | Low-confidence rate |
| --- | --- | --- | --- | --- |
| Full resume, title kept (optimistic) | 73.2% | 92.2% | – | – |
| Full resume, title removed | 70.0% | 89.5% | 67.4% | 10% |
| 250-word snippet | 62.8% | 80.3% | 61.8% | 19% |
| 120-word snippet | 52.9% | 70.4% | 51.1% | 24% |
| 60-word snippet | 43.9% | 62.2% | 39.2% | 100% |

The "with fallback" column is slightly lower than ML-only on these dataset resumes; see the
short synthetic resumes in section 2 for why the fallback is still used.

Fallback policy (tuned on out-of-fold training predictions): a prediction is low-confidence when
the top probability is below 25% or the resume has fewer than
100 words. Low-confidence predictions are blended 50/50 with role-profile skill
overlap (or replaced by it when the top probability is below 15%).

## 2. Integration check (in-sample, 50 dataset rows)

All 50 rows ran DOCX parsing → skill extraction → match scoring → suggestions → role
prediction without errors.

| Metric | Value |
| --- | --- |
| Match score MAE / RMSE / R² | 13.72 / 17.01 / 0.605 |
| Role top-1 / top-3 | 100% / 100% |
| Low-confidence predictions | 0 / 50 |
| Resume length | median 717 words (range 165–1727) |

### Short synthetic resumes (fallback behaviour)

Dataset resumes are long professional ones; these 19 hand-written short resumes
(`scripts/synthetic_resumes.py`) represent students and freshers. Raw ML top-1 is correct for
**12/19**; with the fallback the final
top-1 is correct for **19/19**. This is why
the fallback is kept even though it costs 1–2 points on dataset resumes.

| Profile | Words | Raw ML top-1 | Final top-1 | In final top-3? | Confidence |
| --- | --- | --- | --- | --- | --- |
| CS / AI-ML student (expected INFORMATION-TECHNOLOGY) | 52 | AVIATION (20.0%) | INFORMATION-TECHNOLOGY (31.3%) | yes | `low` |
| Junior accounting intern (expected ACCOUNTANT) | 29 | ACCOUNTANT (66.2%) | ACCOUNTANT (64.9%) | yes | `low` |
| UI/UX design student (expected DESIGNER) | 30 | DESIGNER (67.2%) | DESIGNER (60.9%) | yes | `low` |
| HR recruitment assistant (expected HR) | 28 | HR (81.4%) | HR (78.2%) | yes | `low` |
| Entry-level digital marketer (expected DIGITAL-MEDIA) | 25 | DIGITAL-MEDIA (85.5%) | DIGITAL-MEDIA (78.4%) | yes | `low` |
| Frontend web developer (expected INFORMATION-TECHNOLOGY) | 23 | ARTS (12.2%) | INFORMATION-TECHNOLOGY (71.4%) | yes | `low` |
| Python backend engineer (expected INFORMATION-TECHNOLOGY) | 23 | ENGINEERING (21.0%) | INFORMATION-TECHNOLOGY (38.8%) | yes | `low` |
| Certified public accountant (expected ACCOUNTANT) | 24 | ACCOUNTANT (70.8%) | ACCOUNTANT (72.9%) | yes | `low` |
| Emergency room nurse (expected HEALTHCARE) | 24 | ADVOCATE (55.5%) | HEALTHCARE (58.0%) | yes | `low` |
| High school math teacher (expected TEACHER) | 23 | TEACHER (80.2%) | TEACHER (90.1%) | yes | `low` |
| Executive chef (expected CHEF) | 23 | CHEF (80.1%) | CHEF (80.1%) | yes | `low` |
| Full stack engineer (expected INFORMATION-TECHNOLOGY) | 26 | ENGINEERING (14.5%) | INFORMATION-TECHNOLOGY (71.4%) | yes | `low` |
| Junior software engineer (expected INFORMATION-TECHNOLOGY) | 18 | ENGINEERING (32.5%) | INFORMATION-TECHNOLOGY (46.7%) | yes | `low` |
| Data analyst intern (expected INFORMATION-TECHNOLOGY) | 20 | SALES (16.8%) | INFORMATION-TECHNOLOGY (20.8%) | yes | `low` |
| Mechanical engineering graduate (expected ENGINEERING) | 13 | ENGINEERING (75.4%) | ENGINEERING (62.7%) | yes | `low` |
| Line cook (expected CHEF) | 16 | CHEF (80.1%) | CHEF (80.1%) | yes | `low` |
| Personal trainer (expected FITNESS) | 13 | FITNESS (87.4%) | FITNESS (93.7%) | yes | `low` |
| Retail sales associate (expected SALES) | 14 | SALES (74.7%) | SALES (57.3%) | yes | `low` |
| Elementary school teacher (expected TEACHER) | 12 | TEACHER (84.2%) | TEACHER (92.1%) | yes | `low` |

## Known limitations

- The match-score target (`ai_match_score`) was produced by an AI model, not recruiters, and
  only 23 job descriptions exist, so R² ≈ 0.36 is the realistic ceiling for this data.
- The classifier predicts the dataset's 24 industry categories, not specific job titles, and some
  categories overlap (e.g. ADVOCATE contains patient advocates, which pulls in nursing resumes).
- Confidence flags catch diffuse or short inputs; they cannot catch a model that is confidently wrong.
