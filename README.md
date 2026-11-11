<div align="center">

<img src="frontend/public/favicon.svg" width="72" alt="FitLens logo" />

# FitLens — AI Resume Analyzer

**Scores a resume against any job with machine learning, explains the score, and turns every gap into a next step:<br/>fix the resume, build a better one, find matching jobs and hackathons, and learn the missing skills.**

[![Live demo](https://img.shields.io/badge/Live_demo-resumefitlens.vercel.app-2ea44f?style=for-the-badge)](https://resumefitlens.vercel.app)
[![Sample report](https://img.shields.io/badge/Sample_report-no_upload_needed-3451f0?style=for-the-badge)](https://resumefitlens.vercel.app/check?demo=high)

[![CI](https://github.com/Vardhansaigadde/AI-RESUME-ANALYZER/actions/workflows/ci.yml/badge.svg)](https://github.com/Vardhansaigadde/AI-RESUME-ANALYZER/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-281_passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9-F7931E?logo=scikitlearn&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_19-20232A?logo=react&logoColor=61DAFB)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?logo=supabase&logoColor=white)

<img src="docs/screenshots/report-overview.png" width="900" alt="FitLens resume report: job match score with an explanation, ATS score and resume strength" />

</div>

## Why FitLens

Students apply to dozens of jobs with one generic resume, often in a layout that applicant tracking
systems (ATS) can't read, and without knowing which skills they're missing. Existing checkers are paid,
send the resume to third-party AI services, or return a single number with no explanation.

FitLens is a free, full-stack web app that answers three questions — **How well do I fit this job? Why?
What do I do next?** — using models I trained and evaluated myself, without sending resumes to any AI
provider.

## Highlights

- **Two ML models, trained and validated without leakage.** A Ridge regression predicts the 0–100 match
  score (R² 0.38, RMSE 17.7 on *unseen jobs* with GroupKFold), and a calibrated Linear SVM predicts the job
  category (**73% top-1 / 92% top-3** across 24 categories on 497 held-out resumes). Each beat two other
  algorithms on the same data.
- **Explainable by design.** Every score is broken into the contribution of each factor ("Why this score"),
  and low-confidence predictions are flagged honestly.
- **Built for real resumes.** Parses PDF and Word files, including hidden GitHub/LinkedIn hyperlinks, Word
  bullet styles and two-column layouts, then runs an ATS-friendliness check with a fix for every problem.
- **Generates a resume from quick answers.** A student describes their projects in a few words; a rule-based
  generator writes the summary, action-verb bullets with formatted numbers and grouped skills, tailored to a
  pasted job (matching projects and skills first, missing keywords suggested, never invented).
- **End-to-end product.** Resume builder with 15 ATS-safe templates (PDF + Word) and clickable links, live jobs scored against
  the resume, hackathon finder, week-by-week learning roadmaps, an application tracker and accounts.
- **Fixes the resume for you.** One click rewrites weak bullets, adds Tech lines and the skills a student
  used or very likely knows, and writes a summary for the job or role, never inventing anything. Every change
  can be kept or undone, and Word files are edited in place in the student's own design.
- **Earn while you study.** A freelancing guide that starts from zero skills: services that free AI tools make
  doable, a 30-day plan to the first client, platforms, message templates, pricing, getting paid in India,
  scam warnings and tax basics, with services matched to the student's resume.
- **Production quality.** 342 automated tests and linting on every pull request (GitHub Actions), a
  Dockerised API with rate limiting and file-signature checks, and row-level security in PostgreSQL.
- **Privacy first.** Resumes are processed in memory and never stored or sent to an AI service.

## Features

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/report-ats.png" alt="ATS check" /><br/><b>ATS check</b> — layout, sections, contact details, bullet quality and keywords, each with a fix.</td>
    <td width="50%"><img src="docs/screenshots/report-edit.png" alt="Edit and re-check" /><br/><b>Edit &amp; re-check</b> — editable sections, a live bullet-point coach, instant re-scoring and Word export.</td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/builder.png" alt="Resume builder" /><br/><b>Resume builder</b> — 15 ATS-safe templates (incl. LaTeX-style tech layouts), clickable links, live preview, PDF and Word download.</td>
    <td><img src="docs/screenshots/jobs.png" alt="Live jobs" /><br/><b>Jobs &amp; internships</b> — live openings with a fit score each, what employers ask for, one-click searches on 8 job sites.</td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/report-skill-plan.png" alt="Skill plan" /><br/><b>Skill plan</b> — portfolio projects that close several gaps at once, with a ready-to-paste resume bullet.</td>
    <td><img src="docs/screenshots/learn.png" alt="Learning roadmap" /><br/><b>Learning roadmap</b> — skills in prerequisite order, free resources, checklists and a weekly schedule.</td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/hackathons.png" alt="Hackathons" /><br/><b>Hackathons</b> — live listings on Unstop, Devfolio, Devpost, MLH and more, filtered by topic and mode.</td>
    <td align="center"><img src="docs/screenshots/mobile-report.png" width="260" alt="Mobile view" /><br/><b>Responsive</b> — works on phones, with light and dark themes.</td>
  </tr>
</table>

## How it works

```mermaid
flowchart LR
    U([Student]) --> FE["React 19 + Vite<br/>(Vercel)"]
    FE -- "REST / JSON" --> API["FastAPI<br/>(Docker on Render)"]
    FE <--> SB[("Supabase<br/>Auth + Postgres + RLS")]
    FE <--> GH["GitHub API<br/>(proof check)"]
    subgraph Backend pipeline
      API --> P["Parse PDF / DOCX<br/>text, links, layout"]
      P --> C[Clean + split sections]
      C --> S["Extract skills<br/>436-skill taxonomy"]
      S --> M["Match scorer<br/>TF-IDF + Ridge"]
      S --> R["Role classifier<br/>TF-IDF + calibrated LinearSVC"]
      M --> A["ATS check, suggestions,<br/>learning plan"]
      R --> A
    end
    API --> J["Job APIs<br/>Himalayas, Remote OK, Adzuna,<br/>Jooble, Arbeitnow"]
```

### The machine learning

| | Match scorer (regression) | Role classifier (classification) |
| --- | --- | --- |
| **Data** | 2,385 resume–job pairs, 23 job descriptions | 2,484 resumes, 24 categories |
| **Features** | TF-IDF cosine similarity, skill-overlap ratio, resume length | Word + bigram TF-IDF (5,000 terms) |
| **Model** | Ridge regression (robust-scaled, soft-capped to 0–100) | Linear SVM + probability calibration, skill-overlap fallback |
| **Validation** | GroupKFold by job, so test jobs are never seen in training | Stratified 80/20 split, title line removed to avoid label leakage |
| **Result** | **R² 0.377 · RMSE 17.7 · MAE 14.5** (beat Random Forest and Gradient Boosting) | **73.2% top-1 · 92.2% top-3** (beat Logistic Regression and Naive Bayes) |

Decisions worth calling out:

- **No data leakage.** Columns produced by the labelling model were excluded from the features, the
  regression is validated on jobs it never saw, and the classifier is also tested with the resume title
  removed, because the title often repeats the label.
- **Simple models on purpose.** Ridge was both the most accurate and the only one whose prediction can be
  explained exactly, which is why the app can show "Why this score".
- **Short student resumes.** A skill-overlap fallback lifted correct predictions on 19 short student
  resumes from 12 to 19, at a cost of 1–2 points on long ones.
- **Honest limits.** The match target was produced by an AI model, not recruiters, which caps the R²
  achievable on this data. The full analysis is in the [technical guide](docs/TECHNICAL.md#model-performance).

## Tech stack

| Layer | Technologies |
| --- | --- |
| Machine learning | scikit-learn, pandas, NumPy, joblib |
| Backend | Python 3.14, FastAPI, Pydantic, pdfplumber, python-docx |
| Frontend | React 19, Vite, Tailwind CSS 4, Framer Motion |
| Data and auth | Supabase (PostgreSQL, Google / email sign-in, row-level security) |
| Quality and delivery | pytest (342 tests), ruff, GitHub Actions CI, Docker, Render, Vercel |

## Run it locally

Requires Python 3.14 and Node 20+.

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload     # API on http://127.0.0.1:8000
```

```bash
cd frontend
npm install
npm run dev                       # app on http://localhost:5173
```

Run the checks CI runs: `ruff check . && pytest`, and `npm run build` in `frontend/`.
Accounts are optional locally; see the [technical guide](docs/TECHNICAL.md#accounts-supabase) to enable them.

## Project structure

```text
app/            FastAPI app: routers, services (parser, matcher, classifier, ATS checker…), schemas
app/ml/         feature engineering shared by training and serving
app/data/       curated data: skill taxonomy, roles, learning resources, projects, templates
scripts/        data processing, training, evaluation and data-validation scripts
models/         trained models (.joblib)
reports/        model metrics written by the training scripts
frontend/       React app
tests/          pytest suite
supabase/       database schema and row-level security
docs/           technical guide and screenshots
```

## Documentation

- [Technical guide](docs/TECHNICAL.md): every module, the data, model results, API reference, retraining
  and deployment.
- [Frontend notes](frontend/README.md): design system and component structure.

## Author

**Gadde Vardhan Sai** — B.Tech, Computer Science and Engineering (AI & ML), Aditya University
· [GitHub](https://github.com/Vardhansaigadde)

Built as an academic project with R. Naveen, D. Pardhu and D. Tilak, guided by Mr. G. Siva Shankar.
