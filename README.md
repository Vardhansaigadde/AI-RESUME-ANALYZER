# FitLens — Resume Analyzer

[![CI](https://github.com/Vardhansaigadde/AI-RESUME-ANALYZER/actions/workflows/ci.yml/badge.svg)](https://github.com/Vardhansaigadde/AI-RESUME-ANALYZER/actions/workflows/ci.yml)

Upload a resume (PDF or DOCX) and, optionally, paste a job description (or pick a sample). Built
with students and freshers in mind. The report has five tabs:

| Tab | What you get |
| --- | --- |
| **Overview** | With a job: a **match score (0–100)** and why, plus the posting decoded (level, experience, must-have and nice-to-have skills you have or lack, which skills to list first). Always: a **resume strength** grade per section, your **target-role gap** (core skills of 25 job-title roles), the job categories your resume resembles, every **skill found**, and a **GitHub proof check** (which resume skills your public repos back up, which they don't, skills your repos show that the resume misses, and profile fixes). |
| **ATS check** | A 0–100 estimate of how well applicant tracking systems can read the resume (layout, sections, contact details, bullets, keywords), each problem with a fix. **Student mode** adds a fresher checklist (projects, internships, CGPA, GitHub, one page). |
| **Edit & re-check** | The resume split into editable sections, a live **bullet coach** (weak openers, missing numbers, passive voice), one-click re-check, and download as an ATS-friendly `.docx`. |
| **Skill plan** | **One or two portfolio projects** that close several gaps at once (steps and a ready resume bullet), then a study **roadmap** for the missing skills (from the job, or your target role when there's no job): in learning order with missing prerequisites first, hours and a week-by-week estimate at your pace, docs + a free course + a YouTube video for each skill, a "done when you can…" checklist with progress saved in the browser, a project that proves it, and roadmap.sh links. |
| **Find jobs** | Live jobs and internships (search by role, country, and All / Internships / Entry-level), each with **your fit score**, the skills you have and miss, and a link to apply. |

Live app: <https://resumefitlens.vercel.app> · Backend: FastAPI on Render · Frontend: React + Vite on Vercel

## How it works

```text
Browser (React, Vercel)
  │  POST {VITE_API_BASE_URL}/api/analyze   multipart: resume_file + job_description
  ▼
FastAPI on Render (Docker)
  app/main.py                 CORS, 6 MB body limit, 20 req/min per-IP rate limit
  app/routers/analyze.py      /analyze, /recheck, /resume/docx, /suggest-roles
  app/services/pipeline.py    file checks (type, 5 MB, magic bytes) → orchestration
    ├─ parser.py              pdfplumber / python-docx → text, plus layout facts (tables, columns, images…)
    ├─ data_cleaning.py       same normalization used to build the training data
    ├─ skill_extractor.py     regex over a 436-skill taxonomy + aliases (k8s → kubernetes)
    ├─ matcher.py             3 features → RobustScaler → Ridge → soft-capped score + breakdown
    ├─ suggestions.py         rule-based, max 5 (2 slots reserved for structural issues)
    ├─ role_predictor.py      TF-IDF → calibrated LinearSVC (24 categories) + skill-overlap fallback
    ├─ resume_sections.py     resume text ↔ editable sections (contact, skills, experience…)
    ├─ ats_checker.py         rule-based ATS-friendliness report (+ student checklist)
    ├─ job_decoder.py         must-haves, nice-to-haves, level and years from the posting
    ├─ learning_plan.py       missing skills → resources + project ideas (app/data/learning_resources.json)
    ├─ role_gap.py            resume vs a target job role (app/data/target_roles.json)
    ├─ skills_inventory.py    skills found, grouped and counted
    └─ resume_docx.py         sections → ATS-friendly .docx
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
"Why this score".

Raw linear predictions can run past 100 (up to 119 even on training data), so instead of a hard
clip the score is **soft-capped**: unchanged between 15 and 85, smoothly compressed beyond, never a
flat 0 or 100, and ranking-preserving. When the cap changes a score, the breakdown includes a
`range_adjustment` line so it still adds up. Resumes under 150 words or job descriptions under 50
words get `score_warnings`, because they are far outside the training data.

### Job categories

A TF-IDF (word + bigram, sublinear TF) → `CalibratedClassifierCV(LinearSVC)` classifier trained on
2,484 resumes in 24 industry categories (e.g. `INFORMATION-TECHNOLOGY`, `HEALTHCARE`). If the top
probability is low or the resume is short, predictions are blended with skill overlap against
hand-curated role profiles (`app/data/role_profiles.json`). The response says `"confidence": "low"`
when the final top probability is below 50 %: on held-out resumes those predictions were right
~34 % of the time, versus ~70 % above it.

### ATS check

`app/services/ats_checker.py` checks the things that most often break applicant tracking systems
and weights them into a 0–100 estimate (pass = full weight, warn = half, fail = 0):

| Area | Checks |
| --- | --- |
| Format & layout (uploaded file) | text extracts cleanly, no tables, single column (PDF column detection), no images, no text boxes, contact details not only in the page header/footer, ≤ 2 pages |
| Content | email, phone, LinkedIn/portfolio link, standard section headings, 250–1,000 words, bullet points, bullets with numbers, bullets starting with action verbs, no emoji/icon characters |
| Keywords | share of the job's skills found in the resume |

It is a transparent heuristic, not the output of a real ATS. Edited or pasted resumes are exported
through the plain single-column `.docx` template, so their layout checks count as passes.

### Edit & re-check

`resume_sections.py` splits the extracted text into contact details, summary, skills, experience,
projects, education, certifications and other sections (headings, bullets, wrapped lines and date
lines are recognised; all 2,484 dataset resumes parse without errors). The UI shows them as an
editable form; **Re-check** analyzes the edited version (`POST /api/recheck`) and **Download**
builds an ATS-friendly `.docx` (`POST /api/resume/docx`: one column, standard headings, real Word
bullet lists, no tables, images or headers).

### Student features

- **Job decoder** (`job_decoder.py`) reads the posting line by line: skills under headings such as
  "Requirements" are must-haves, those under "Nice to have" or in lines with "is a plus" /
  "preferred" are nice-to-haves, and the rest are "also mentioned". It also extracts years of
  experience, level (entry / mid / senior) and whether a degree is mentioned.
- **Learning plan** (`learning_plan.py`) uses `app/data/learning_resources.json`: 75 common skills,
  each with a one-line explanation, free resources from official docs and well-known free
  platforms, a YouTube video, a project idea, an hours estimate, a three-item "done when you
  can…" checklist, prerequisites and a roadmap.sh link (details in
  `scripts/learning_roadmap_data.py`). The plan is a study order: prerequisites the resume doesn't
  show (JavaScript before React, Linux before Docker) are inserted before the skills that need
  them. `scripts/build_learning_resources.py` requests every link, checks every video with
  YouTube's oEmbed endpoint (no API key; it also records the real title and channel), rejects
  prerequisite loops, and refuses to write the file if anything is broken. Target roles get a
  roadmap.sh link too (`app/data/role_roadmaps.json`).
- **Project picker** (`project_picker.py`) chooses one or two projects from 36 student-sized ideas
  in `app/data/project_ideas.json`. Each missing skill is weighted (must-have 3, nice-to-have 2,
  mentioned 1; for a target role, by its importance order); a project scores the gaps it closes,
  plus a little for reusing skills the student has, minus a little for unrelated new skills. The
  second pick is scored only on gaps the first leaves open, and a project must close gaps worth at
  least 2 points to be suggested.
- **Student mode** adds weighted checks to the ATS report: education before experience, 2+
  projects, an internship or training, grades in the Education section, a GitHub/portfolio link and
  one-page length. `student_detected` is true for resumes with student wording or a graduation year
  that hasn't passed.
- **Bullet coach** runs in the browser (`frontend/src/lib/bulletCoach.js`) so feedback is instant.

### Resume-only mode

An empty job description gives `"mode": "resume_only"`: `match_score` is `null` and the job fields are
empty, but the ATS check (minus the keyword check), role predictions, `role_gap`, `skills_inventory`
and a role-based `learning_plan` are returned. Target roles live in `app/data/target_roles.json`
(built and validated by `scripts/build_target_roles.py`): job-title roles with core skills in
order of importance, plus a default role for each classifier category. They are separate from the
classifier's 24 dataset categories because those are broad (the dataset's IT category is mostly
infrastructure resumes) and would give a software student misleading gaps. The resume strength
report is computed in the browser (`frontend/src/lib/strength.js`) so it updates while editing.

### GitHub proof check

The browser reads the student's public profile and repositories straight from GitHub's API (no
sign-in or key; each visitor has GitHub's free 60 requests an hour, instead of every user sharing
the server's), then `POST /api/github-check` (`app/services/github_check.py`) compares them with
the resume. A repository shows a skill through its language (`Jupyter Notebook` → Python,
`Dockerfile` → Docker), topics (`machine-learning`, `nodejs`) and name/description; forks don't
count. Only technical groups (languages, web, data & AI, databases, cloud & DevOps) are judged.
The report lists skills backed by a repo, skills with no public proof, skills the repos show that
the resume leaves out (one click adds them to the editor), and a profile checklist: own projects,
recent activity, descriptions, topics, live demos, a profile README, name and bio, and whether the
resume links to the profile.

### Live job search

`POST /api/jobs` (`app/services/job_search.py`) fetches current postings and scores the resume
against each one with the same match model, so they can be sorted by fit. Only the search words,
country and job type are sent to the job sites; the resume stays on the server.

- **[Himalayas](https://himalayas.app/api)** — remote jobs, including India-only and internship
  roles. Free, no key. Its data refreshes daily, so results are cached for 6 hours.
- **[Adzuna](https://developer.adzuna.com)** — on-site jobs in India and six other countries.
  Optional: set `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` (free developer key). Adzuna returns only a
  snippet of each posting, so those scores are rougher (the card says so). Cached for 1 hour.

Both ask that listings link back to them and name them as the source, which every card does.
Results are cached in memory by (source, query, country, type), so popular searches rarely reach
the job sites. Remotive and Arbeitnow were considered and left out: Remotive's free API now
returns only a handful of jobs, and Arbeitnow is almost all Germany. Skill extraction is cached by
text, so scoring 20 postings takes about a second.

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
| **Ridge (production)** | **0.377 ± 0.156** | **17.71 ± 2.14** | 14.48 ± 2.11 |
| Random forest | 0.349 ± 0.174 | 18.13 ± 2.50 | 14.66 ± 2.69 |
| Gradient boosting | 0.280 ± 0.127 | 19.29 ± 3.18 | 15.52 ± 3.20 |

Predictions are soft-capped exactly as in production. (The original model scored 0.360; the soft cap
and the larger skill taxonomy raised it to 0.377.)

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
  job* a resume was scored against, which no model can know for a new job; R² ≈ 0.37 is a
  realistic ceiling here.
- **Unrelated jobs can still score in the high 30s.** In the mismatched-pair check, 10 % of
  other-category pairs scored above ~40.
- **Wording over meaning.** TF-IDF similarity is the strongest feature, so paraphrased experience
  ("built REST services" vs "REST API") is partly missed. Skill aliases reduce this. Sentence
  embeddings would help more but were left out to fit Render's 512 MB free tier.
- **Industry categories, not job titles.** The classifier knows 24 broad categories, some of which
  overlap: `ADVOCATE` contains many patient-advocate resumes. The 206-word nursing resume that the
  first model confidently called `ADVOCATE` (48.7 %) is now `HEALTHCARE`, but only 38 % vs 35 %,
  so it is reported as low confidence. The flag catches unclear predictions, not a model that is
  confidently wrong.
- **The dataset resumes are long professional ones** (median ≈ 760 words), so short student resumes
  rely more on the skill-overlap fallback.
- **Text-based files only.** Scanned or image-only PDFs have no text layer; the API explains this
  and asks for a text-based PDF or DOCX (OCR would not fit the free tier).

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

Checks (the same ones CI runs on every push and pull request):

```bash
ruff check . && ruff format --check . && pytest
```

```bash
cd frontend && npm run lint && npm run build
```

### API

`POST /api/analyze` — multipart `resume_file` (PDF/DOCX, ≤ 5 MB) + `job_description`, or JSON
`{"resume_text": "...", "job_text": "..."}`. Returns `match_score`, `score_breakdown`, `features`,
`matched_skills`, `missing_skills` (sorted), `score_warnings`, `suggestions`, `suggested_roles`,
`confidence`, `resume` (editable sections), `ats` (score, verdict, checks), `job_insights`,
`learning_plan`, `project_picks`, `student_mode` and `student_detected`. Add `student_mode=true` (form field or
JSON) for the student checklist.

`POST /api/recheck` — JSON `{"resume": {...sections}, "job_description": "...", "student_mode": false}`. Same response as
`/api/analyze`, for the edited resume.

`POST /api/resume/docx` — JSON resume sections; returns an ATS-friendly `.docx` download.

`POST /api/role-gap` — JSON `{"resume": {...}, "target_role": "Data Analyst"}`; returns `role_gap`, a
role-based `learning_plan` and `project_picks` without re-running the models.

`job_description` is optional on `/api/analyze` and `/api/recheck`; both also accept `target_role`.

`POST /api/jobs` — JSON `{"resume": {...}, "query": "data analyst", "country": "IN", "kind": "internship"}`
(`kind`: `all`, `internship` or `entry`; `country`: a code from `/api/jobs/options` or `ANY`). Returns
`jobs` (each with `fit_score`, `matched_skills`, `missing_skills`, `url`, `source`), sorted by fit,
and the status of each `sources` entry.

`POST /api/github-check` — JSON `{"resume": {...}, "profile": {...}, "repos": [...]}` with the
public GitHub profile and up to 100 repositories as GitHub's API returns them. Returns `proven`,
`unproven`, `hidden`, `checks` and `stats`.

`GET /api/jobs/options` — countries for the job search and whether on-site jobs are enabled.

`POST /api/suggest-roles` — a resume file or `resume_text`, optional `top_n` (1–24).

`GET /` (or `HEAD /`) — health check.

Errors are JSON `{"detail": "..."}`: 400 invalid file or input, 413 body over 6 MB, 422 validation,
429 more than 20 requests per minute from one IP (with `Retry-After`), 503 model files missing.

## Retraining the models

```bash
python scripts/build_processed_data.py     # raw → data/processed/*.csv.gz
python scripts/build_skills_taxonomy.py    # → app/data/skills_list.json
python -m app.ml.features                  # → data/processed/features.csv + models/tfidf_vectorizer.joblib
python scripts/train_match_scorer.py       # → match_scorer + feature_scaler, reports/match_scorer_metrics.json
python scripts/train_role_classifier.py    # → role_classifier + role_vectorizer, reports/role_classifier_metrics.json
python scripts/evaluate_pipeline.py        # → reports/evaluation_summary.md
python scripts/build_learning_resources.py # checks every link and video → app/data/learning_resources.json
python scripts/build_target_roles.py       # validates job-title roles → app/data/target_roles.json
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
| `RATE_LIMIT_PER_MINUTE` | `20` | POST requests (analyze, re-check, download, job search) per client IP per minute (`0` disables) |
| `LOG_LEVEL` | `INFO` | log level |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | unset | free [Adzuna](https://developer.adzuna.com) key; switches on on-site jobs in the job search |

On the free plan the service sleeps after ~15 minutes idle. The `Keep backend awake` GitHub Actions
workflow pings the health check every 10 minutes from 07:30 to 00:30 IST (~510 of the 750 free
hours a month), so daytime visitors don't wait. Outside those hours the first request can take up
to a minute; models load at startup and the frontend shows a "waking up" notice and waits up to
120 s. GitHub pauses scheduled workflows after 60 days without repository activity; re-enable it
from the Actions tab if needed.

**Frontend (Vercel).** The Vercel project's Root Directory is `frontend`, so `frontend/vercel.json`
is the active config: Vite build to `dist/` and SPA fallback to `index.html`. The Vercel
environment variable `VITE_API_BASE_URL=https://ai-resume-analyzer-xb45.onrender.com` makes the
browser call the backend directly (hence `CORS_ORIGINS` above). If that variable is removed,
requests go to `/api/*` on the Vercel domain and the rewrite in `vercel.json` forwards them to the
same backend.

## Project structure

```text
app/                FastAPI app (main.py, rate_limit.py), routers, schemas (analysis, resume, insights, jobs, github), services, ml/, data/*.json
data/raw/           source datasets (.csv.gz)
data/processed/     cleaned datasets and features.csv (generated)
models/             serialized models (~5.2 MB total)
scripts/            data processing, training and evaluation
reports/            metrics JSON written by training + evaluation_summary.md
notebooks/          exploratory data analysis
tests/              pytest suite
frontend/           React + Vite app (see frontend/README.md)
.github/workflows/  CI (lint + tests + build) and the keep-awake ping
```
