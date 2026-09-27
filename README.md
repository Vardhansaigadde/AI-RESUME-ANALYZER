# Resume Analyzer

An intelligent resume analysis and job-fit matching application powered by FastAPI and Machine Learning.

## Project Structure

```text
resume-analyzer/
├── app/
│   ├── main.py        # FastAPI entrypoint and application setup
│   ├── routers/       # API route controllers
│   ├── services/      # Business logic and parsing services (PDF/DOCX)
│   ├── ml/            # Machine learning inference and scoring pipelines
│   ├── schemas/       # Pydantic data schemas and validation models
│   ├── data/          # Application-level data or lookup resources
│   └── static/        # Static assets (UI files, CSS, JS, images)
├── data/
│   ├── raw/           # Raw datasets (e.g. Resume.csv, job_resume_fit.csv)
│   └── processed/     # Cleaned, tokenized, or transformed datasets
├── models/            # Serialized ML model artifacts (e.g., joblib/pkl)
├── notebooks/         # Jupyter notebooks for EDA and model experimentation
├── tests/             # Automated test suite
├── requirements.txt   # Project dependencies
└── README.md          # Project documentation
```

## Setup & Installation

1. **Activate the virtual environment**:
   - Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```
   API docs will be accessible at: `http://127.0.0.1:8000/docs`.

## Model Performance & Limitations

- **Expected Real-World Performance (Headline)**: Validated via GroupKFold ($k=5$, grouped by job description to prevent text leakage):
  - **Expected $R^2$**: $\approx 0.36$ ($0.3602 \pm 0.1744$)
  - **Expected RMSE**: $\approx 17.9$ ($17.95 \pm 2.40$ on a 0–100 match scale)
  *(Note: In-sample fit on training data is $R^2 = 0.5078$ / $\text{RMSE} = 17.28$, but this reflects training memorization; the GroupKFold metric represents true generalization to unseen job postings).*
- **Match Score Model Architecture**: Ridge regression trained on scaled features using `RobustScaler` with 3 leakage-free features:
  - `tfidf_similarity`: TF-IDF cosine similarity between resume and job description
  - `skill_overlap_ratio`: Fraction of job-required skills present in the resume
  - `resume_word_count`: Total word length of the resume
- **Feature Selection & Dropped Features**:
  - **`job_word_count` (Tested and Dropped)**: `job_word_count` was initially included as a 4th feature, yielding a marginal $+0.02$ $R^2$ gain ($R^2 \approx 0.38$). However, stress testing revealed that because the training dataset's job descriptions occupied an unnaturally narrow distribution (441–606 words), its negative linear coefficient ($-0.133$) introduced severe out-of-domain extrapolation sensitivity. In real-world inference, pasting a brief 18-word job description artificially inflated match scores by $+75$ to $+78$ points (assigning 84%+ scores to resumes with zero matching skills). Even with `RobustScaler` or log-transforms, linear models preserve this slope outside the narrow training distribution. Dropping `job_word_count` completely eliminated this sensitivity ($\Delta = 0.00$ points between short and long postings for identical qualifications) — a correctness and reliability improvement judged well worth trading off $\sim 0.02$ $R^2$.
  - **`skill_string_match_score` & `fuzzy_match_score` (Dropped)**: Two dataset-provided features were thoroughly evaluated and dropped because they could not be reliably reproduced at inference time without dataset ground truth and provided no measurable generalization improvement in production-realistic testing.
- **Role Classifier Handling of Short / Student Resumes (Confidence-Aware Hybrid Fallback)**:
  - **Diagnosis & Training Distribution Mismatch**: The 24-category role classifier (`CalibratedClassifierCV` over `LinearSVC`) was trained on 2,484 comprehensive professional resumes averaging **799.9 words** and **316.9 non-zero TF-IDF features** (median 317; 10th percentile = 192 features). Concise, bullet-pointed student or fresher resumes (e.g., 250–300 words with only ~120–130 non-zero TF-IDF features) sit well below training data density, producing diffuse probabilities across classes (e.g., top-1 probability of only **13.7%** on a 298-word student resume with noisy predictions like `AVIATION`).
  - **Confidence-Aware Skill-Overlap Fallback**:
    - `is_low_confidence(probabilities, threshold=0.35, word_count=..., min_word_count=150)` monitors the top-1 calibrated ML probability and resume word count.
    - When ML confidence drops below 35% OR the resume has fewer than 150 words (whose TF-IDF representation is intrinsically sparse), the system engages a fallback against hand-curated role profiles in [`app/data/role_profiles.json`](file:///c:/Users/vardh/OneDrive/Desktop/resume-analyzer/app/data/role_profiles.json) using canonical skills extracted via `skill_extractor.py`.
    - If ML confidence is critically low (< 15%), role ranking relies directly on empirical skill overlap, decisively prioritizing genuine candidate skills (e.g. propelling **`INFORMATION-TECHNOLOGY` to 63.2%** and **`ENGINEERING` to 15.8%** on the diagnostic student resume, eliminating `AVIATION`).
    - If ML confidence is moderately low (15% to 35%) or the resume is concise (< 150 words), the system applies a 50/50 weighted blend between the ML probability distribution and skill overlap scores.
    - Confident predictions ($\ge 35\%$ and $\ge 150$ words, typical for full standard resumes at 65–82%) continue to use the ML classifier directly.
    - *Note*: because role profile sizes vary (13-80 skills per category), roles with larger skill profiles have a structurally higher chance of accumulating overlap matches. This wasn't corrected for, since testing showed sensible results, but is a known characteristic of the current fallback method.
  - **Transparent API & UI Surfacing (`confidence` field)**: Both `POST /api/analyze` and `POST /api/suggest-roles` surface an explicit `"confidence": "high" | "low"` field in their schemas (`AnalyzeResponse` and `SuggestRolesResponse`/`RolesOnlyResponse`). The frontend displays a dedicated contextual notice (*"Role suggestions are less certain — try adding more detail to your resume"*) when confidence is low, providing full transparency to students and early-career candidates rather than presenting low-certainty guesses as definitive.
  - **Inherent Limitation: Low-Confidence vs. Confidently Wrong Misclassifications**:
    - The confidence monitoring mechanism (`is_low_confidence`) is specifically designed to catch **diffuse, low-confidence predictions** (e.g., top-1 probability $< 35\%$) and **sparse inputs** ($< 150$ words).
    - **It cannot catch high-confidence misclassifications where the model is confidently wrong.** For example, on a 24-word synthetic Emergency RN resume, raw ML predicted `ADVOCATE` at **55.4%** (true category `HEALTHCARE`). While that specific 24-word test case was intercepted by the secondary `word_count < 150` trigger and recovered to `HEALTHCARE` (53.5%) via skill blending, **this outcome was purely incidental due to resume brevity, not a real fix for the underlying model defect**.
    - **Real-World Length Verification (206 words)**: When evaluated on a realistic-length (206-word) bedside nurse resume containing typical clinical duties (*vital signs monitoring, intravenous medication administration, cardiac telemetry, triage, catheterization, patient care planning*), the resume **bypasses BOTH safety filters** ($206 \ge 150$ words, and top probability $48.7\% \ge 35\%$). As a result, the production service **confidently misclassifies the nurse as `ADVOCATE` at 48.7% with `"confidence": "high"`** (while `HEALTHCARE` languishes in second place at only 18.2%).
    - **Root Cause (Training Data Semantic Overlap)**: Detailed feature inspection reveals this occurs because the training dataset's `ADVOCATE` category contains extensive overlap with healthcare advocacy (43.2% mention "patient", 62.7% mention "health"). In the trained model, bedside nursing tokens like `vital signs` ($+0.311$), `vital` ($+0.374$), `monitoring` ($+0.391$), and `medication` ($+0.240$) carry strong *positive* weights toward `ADVOCATE`, while `HEALTHCARE` training weights heavily *penalize* those same unigrams/bigrams (`vital signs` at $-0.419$, `signs` at $-0.449$, `medication` at $-0.147$).
    - **Key Takeaway**: Raising the probability threshold (e.g. from 25% to 35%) and adding word-count fallbacks (< 150 words) effectively resolves diffuse guesses on sparse/student resumes, but **cannot prevent confidently wrong predictions when the classifier has learned an inverted decision boundary on full-length text**. High model confidence reflects internal conviction, not semantic truth.
- **Data Limitations**: Trained on 2,385 pairs across 23 unique job descriptions. Performance may vary on specialized niche roles outside the training vocabulary.

## Artifact Sizes & Free-Tier Platform Compatibility

All production machine learning models and taxonomy lookup dictionaries are compact and serialize to minimal disk and memory footprints:

| Artifact Path | Description | Size |
| :--- | :--- | :---: |
| `models/role_classifier.joblib` | Calibrated LinearSVC role classifier (24 classes) | 4.59 MB |
| `models/tfidf_vectorizer.joblib` | Match score TF-IDF vectorizer | 0.39 MB |
| `models/role_vectorizer.joblib` | Role classifier TF-IDF vectorizer (5,000 features) | 0.19 MB |
| `models/feature_scaler.joblib` | RobustScaler fitted on training features | 0.84 KB |
| `models/match_scorer.joblib` | 3-feature Ridge regression match scorer | 0.56 KB |
| `app/data/role_profiles.json` | 24 curated role taxonomy profiles | 10.01 KB |
| `app/data/skills_list.json` | 394 canonical skills taxonomy | 8.49 KB |
| `app/data/curated_technical_skills.json` | Curated technical skills dictionary | 1.81 KB |
| **Total Combined Footprint** | **All production models & data assets** | **~5.19 MB** |

> [!NOTE]
> At **5.19 MB total combined size**, these artifacts fit comfortably within the strict free-tier memory and storage limits of standard cloud platforms (e.g. Render 512 MB RAM, Railway 512 MB RAM, Fly.io, or AWS Free Tier). Cold-start load time for all model artifacts is under **150ms**.

---

## Deployment

The application is architected for decoupled, production deployment:
- **Backend (FastAPI)**: Deployed via Docker or Python on [Render](https://render.com) (or Railway / Fly.io).
- **Frontend (React + Vite)**: Deployed as a static SPA on [Vercel](https://vercel.com) (or Netlify / Cloudflare Pages).

### 1. Docker (Containerized Backend)

> [!WARNING]
> **Environment Status & Dockerfile Untested Caveat**:  
> Docker Desktop / Docker CLI is **not installed and cannot be run in this development environment** (the session runs under a non-elevated Windows user without Administrator rights, WSL2 has no installed Linux distribution, and no background Docker daemon is present).  
> Consequently, the [`Dockerfile`](file:///c:/Users/vardh/OneDrive/Desktop/resume-analyzer/Dockerfile) is **UNTESTED locally** and the commands below have not been executed against a running container in this environment. The container build, port binding, and `/api/analyze` endpoints should be verified once deployed to Render (or executed on a host machine with Docker available) before being trusted.

The provided [`Dockerfile`](file:///c:/Users/vardh/OneDrive/Desktop/resume-analyzer/Dockerfile) uses `python:3.11-slim`, installs production dependencies, copies only the required `app/` and `models/` folders (guided by [`.dockerignore`](file:///c:/Users/vardh/OneDrive/Desktop/resume-analyzer/.dockerignore)), and launches `uvicorn` on port 8000.

#### Build & Run Commands:
```bash
# Build the Docker image locally
docker build -t resume-analyzer-backend .

# Run the container (mapping host port 8000 to container port 8000)
docker run -d --name resume-api -p 8000:8000 resume-analyzer-backend

# Check container health and logs
docker logs -f resume-api

# Test the running container endpoint
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Experienced Python Software Engineer with FastAPI and Docker.",
    "job_text": "Seeking Python Backend Engineer with Docker and FastAPI."
  }'
```

---

### 2. Backend Deployment on Render

A pre-configured [`render.yaml`](file:///c:/Users/vardh/OneDrive/Desktop/resume-analyzer/render.yaml) blueprint is included in the repository root.

#### Option A: Automatic Blueprint Deploy (Recommended)
1. Push this repository to GitHub/GitLab.
2. In the Render Dashboard, select **New +** → **Blueprint**.
3. Connect your repository. Render automatically reads [`render.yaml`](file:///c:/Users/vardh/OneDrive/Desktop/resume-analyzer/render.yaml) and provisions the service.

#### Option B: Manual Web Service Setup
1. **Service Type**: Web Service
2. **Environment**: Docker (or Python 3.11+)
3. **Build Command** (if using Python): `pip install -r requirements.txt`
4. **Start Command** (if using Python): `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Health Check Path**: `/`
6. **Required Environment Variables**:
   * `PORT`: `8000` (or platform default)
   * `CORS_ORIGINS`: `https://your-frontend.vercel.app` (or `*` for initial testing)

---

### 3. Frontend Deployment on Vercel

The React frontend in [`frontend/`](file:///c:/Users/vardh/OneDrive/Desktop/resume-analyzer/frontend) is pre-configured with [`vercel.json`](file:///c:/Users/vardh/OneDrive/Desktop/resume-analyzer/frontend/vercel.json) to handle SPA routing and reverse-proxy `/api` requests to the Render backend.

#### Deployment Steps:
1. In the Vercel Dashboard, click **Add New Project** and import the repository.
2. Configure project settings:
   * **Root Directory**: `frontend`
   * **Framework Preset**: `Vite`
   * **Build Command**: `npm run build`
   * **Output Directory**: `dist`
   * **Install Command**: `npm install`
3. **Environment Variables**:
   * `VITE_API_BASE_URL`: `https://your-backend.onrender.com` (Optional if using the rewrite proxy in `vercel.json`).
4. Click **Deploy**. Vercel will build and serve the optimized bundle on global edge nodes.

