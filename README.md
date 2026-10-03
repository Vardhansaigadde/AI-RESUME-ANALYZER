# FitLens — Resume Analyzer

Upload a resume (PDF or DOCX) and paste a job description. FitLens returns:

- a **match score (0–100)** with a breakdown of what raised or lowered it,
- the job's skills you **have** and are **missing**,
- up to five **suggestions** (missing skills first, plus structural fixes),
- the three **job categories** your resume most resembles, with a high/low confidence flag.

Live app: <https://resumefitlens.vercel.app> · Backend: FastAPI on Render · Frontend: React + Vite on Vercel

## How it works

```text
Browser (React, Vercel)
  │  POST /api/analyze  multipart: resume_file + job_description
  ▼
Vercel rewrite /api/*  ──►  FastAPI on Render (Docker)
  app/routers/analyze.py      validation, threadpool execution
  app/services/pipeline.py    file checks (type, 5 MB, magic bytes) → orchestration
    ├─ parser.py              pdfplumber / python-docx → text
    ├─ data_cleaning.py       same normalization used to build the training data
    ├─ skill_extractor.py     regex over a 423-skill taxonomy + aliases (k8s → kubernetes)
    ├─ matcher.py             3 features → RobustScaler → Ridge → score + breakdown
    ├─ suggestions.py         rule-based, max 5 (2 slots reserved for structural issues)
    └─ role_predictor.py      TF-IDF → calibrated LinearSVC (24 categories) + skill-overlap fallback
```

### Match score

A Ridge regression on three features, all computable at inference time:

| Feature | Meaning | Effect (from `reports/match_scorer_metrics.json`) |
| --- | --- | --- |
| `tfidf_similarity` | TF-IDF cosine similarity of resume and job text | ≈ +1.3 points per +0.01 similarity |
| `skill_overlap_ratio` | share of the job's skills found in the resume | ≈ +4.8 points per +10 % of required skills |
| `resume_word_count` | resume length | ≈ +0.7 points per +100 words |

Because the model is linear, the API also returns `score_breakdown`: a baseline (≈ 39, the
score of a median training pair) plus each feature's signed contribution. The UI shows it as
"Why this score?".

### Job categories

A TF-IDF (word + bigram, sublinear TF) → `CalibratedClassifierCV(LinearSVC)` classifier trained on
2,484 resumes in 24 industry categories (e.g. `INFORMATION-TECHNOLOGY`, `HEALTHCARE`). If the top
probability is low or the resume is short, predictions are blended with skill overlap against
hand-curated role profiles (`app/data/role_profiles.json`) and the response says
`"confidence": "low"`.

## Data

| File | Rows | Used for |
| --- | --- | --- |
| `data/raw/Resume.csv.gz` | 2,484 resumes, 24 categories | role classifier |
| `data/raw/job_resume_fit.csv.gz` | 2,385 resume–job pairs, **23** unique job descriptions | match scorer (target: `ai_match_score`) |

Data files are stored gzipped (pandas reads `.csv.gz` directly). `data/processed/` is generated
by `scripts/build_processed_data.py`.

## Model performance

All numbers below are produced by the training scripts and stored in `reports/*.json`;
`reports/evaluation_summary.md` summarizes them.

**Match scorer** — GroupKFold (k = 5) grouped by job description, so no job description is in both
training and test folds:

| Model | R² | RMSE (0–100) | MAE |
| --- | --- | --- | --- |
| **Ridge (production)** | **0.360 ± 0.175** | **17.93 ± 2.30** | 14.65 ± 2.27 |
| Random forest | 0.352 ± 0.198 | 18.02 ± 2.54 | 14.55 ± 2.77 |
| Gradient boosting | 0.246 ± 0.262 | 19.33 ± 2.78 | 15.67 ± 2.98 |

The dataset never pairs a resume with a job from another category, so a separate check scores
300 resumes against a random other-category job: those pairs average **28** vs **45** for
own-category pairs, and the own-category pair scores higher **86 %** of the time.

**Role classifier** — stratified 80/20 split (497 test resumes):

Most dataset resumes open with an ALL-CAPS title that repeats the label ("SALES ASSOCIATE …"),
which lets a model read the answer. Real resumes usually open with a name, so the honest
numbers are the ones with that title removed:

| Test set | Top-1 | Top-3 | Macro F1 |
| --- | --- | --- | --- |
| Full resume, title kept (optimistic) | 73.2 % | 92.2 % | 0.688 |
| **Full resume, title removed** | **70.0 %** | **89.5 %** | **0.660** |
| 250-word snippet | 62.8 % | 80.3 % | 0.592 |
| 120-word snippet | 52.9 % | 70.4 % | 0.490 |

(The original model scored 73.8 % with titles but 67.6 % without; sublinear TF and consistent text
cleaning raised the title-removed figure to 70.0 %.)

**Short resumes and the fallback.** On dataset resumes the skill-overlap fallback costs 1–2 points.
On 19 hand-written short, student-style resumes (`scripts/synthetic_resumes.py`) the raw model gets
**12/19** right and the fallback **19/19**, so it is kept for resumes under 100 words or with a top
probability under 25 %. Those thresholds were tuned on out-of-fold training predictions.

## Limitations

- **Small, AI-labelled match data.** Only 23 job descriptions, and the target score was produced
  by an AI model rather than recruiters. About half of the score variance is explained by *which
  job* a resume was scored against, which no model can know for a new job; R² ≈ 0.36 is a
  realistic ceiling here.
- **Wording over meaning.** TF-IDF similarity is the strongest feature, so paraphrased experience
  ("built REST services" vs "REST API") is partly missed. Skill aliases reduce this. Sentence
  embeddings would help more but were left out to fit Render's 512 MB free tier.
- **Industry categories, not job titles.** The classifier knows 24 broad categories, some of which
  overlap: `ADVOCATE` contains many patient-advocate resumes. The 206-word nursing resume that the
  first model confidently called `ADVOCATE` (48.7 %) is now `HEALTHCARE`, but only 38 % vs 35 %.
  The confidence flag catches diffuse predictions and short resumes, not a model that is
  confidently wrong.
- **The dataset resumes are long professional ones** (median ≈ 760 words), so short student resumes
  rely more on the skill-overlap fallback.

## Run locally

Requires Python 3.14 (the version the pinned dependencies and models were built with) and Node 20+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://127.0.0.1:8000  (set ENABLE_DOCS=true for /docs)
```

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173, proxies /api to :8000
```

Tests: `pytest` (backend) and `npm run lint && npm run build` (frontend).

### API

`POST /api/analyze` — multipart `resume_file` (PDF/DOCX, ≤ 5 MB) + `job_description`, or JSON
`{"resume_text": "...", "job_text": "..."}`. Returns `match_score`, `score_breakdown`, `features`,
`matched_skills`, `missing_skills` (sorted), `suggestions`, `suggested_roles`, `confidence`.

`POST /api/suggest-roles` — a resume file or `resume_text`, optional `top_n` (1–24).

`GET /` — health check.

## Retraining the models

```bash
python scripts/build_processed_data.py     # raw → data/processed/*.csv.gz
python scripts/build_skills_taxonomy.py    # → app/data/skills_list.json
python -m app.ml.features                  # → data/processed/features.csv + models/tfidf_vectorizer.joblib
python scripts/train_match_scorer.py       # → match_scorer + feature_scaler, reports/match_scorer_metrics.json
python scripts/train_role_classifier.py    # → role_classifier + role_vectorizer, reports/role_classifier_metrics.json
python scripts/evaluate_pipeline.py        # → reports/evaluation_summary.md
```

`requirements.txt` pins scikit-learn to the version that pickled `models/*.joblib`. If you upgrade
scikit-learn, rerun the steps above before deploying.

## Deployment

**Backend (Render).** The service `AI-RESUME-ANALYZER` (<https://ai-resume-analyzer-xb45.onrender.com>,
region Virginia) builds the `Dockerfile` (Python 3.14-slim, non-root user, only `app/` and
`models/` copied) and redeploys on every push to `main`. The container listens on `$PORT`, which
Render sets. The service was created in the dashboard, so its settings live there; `render.yaml`
mirrors them for recreating it as a Blueprint. Environment variables (set in the dashboard):

| Variable | Default | Purpose |
| --- | --- | --- |
| `CORS_ORIGINS` | localhost dev origins | comma-separated origins allowed to call the API; must include `https://resumefitlens.vercel.app` |
| `ENABLE_DOCS` | `false` | expose `/docs` and `/openapi.json` |
| `LOG_LEVEL` | `INFO` | log level |

On the free plan the service sleeps after ~15 minutes idle; the first request then takes up to a
minute. Models are loaded at startup, and the frontend shows a "waking up" notice and waits up to
120 s.

**Frontend (Vercel).** The Vercel project's Root Directory is `frontend`, so `frontend/vercel.json`
is the active config: Vite build to `dist/` and SPA fallback to `index.html`. The Vercel
environment variable `VITE_API_BASE_URL=https://ai-resume-analyzer-xb45.onrender.com` makes the
browser call the backend directly (hence `CORS_ORIGINS` above). If that variable is removed,
requests go to `/api/*` on the Vercel domain and the rewrite in `vercel.json` forwards them to the
same backend.

## Project structure

```text
app/                FastAPI app (main.py), routers, schemas, services, ml/features.py, data/*.json
data/raw/           source datasets (.csv.gz)
data/processed/     cleaned datasets and features.csv (generated)
models/             serialized models (~5.2 MB total)
scripts/            data processing, training and evaluation
reports/            metrics JSON written by training + evaluation_summary.md
notebooks/          exploratory data analysis
tests/              pytest suite
frontend/           React + Vite app (see frontend/README.md)
```
