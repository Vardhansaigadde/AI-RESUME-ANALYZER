# FitLens frontend

React 19 + Vite single-page app for the Resume Analyzer. It uploads a resume
(PDF/DOCX) and a job description to the FastAPI backend and shows the match
score, a per-factor score breakdown, matched and missing skills, suggestions
and the closest job categories.

Live: <https://resumefitlens.vercel.app>

## Run locally

```bash
npm install
npm run dev        # http://localhost:5173
```

The dev server proxies `/api/*` to `http://127.0.0.1:8000` (see
`vite.config.js`), so start the backend from the repository root first:

```bash
uvicorn app.main:app --reload
```

Other scripts: `npm run build` (production bundle in `dist/`), `npm run preview`
(serve the build), `npm run lint` (oxlint).

## How it talks to the API

`src/App.jsx` posts `multipart/form-data` (`resume_file`, `job_description`) to
`${VITE_API_BASE_URL}/api/analyze`. `VITE_API_BASE_URL` is normally left
unset, so requests go to the same origin and are forwarded:

| Environment | `/api/*` goes to |
| --- | --- |
| `npm run dev` | Vite proxy → `http://127.0.0.1:8000` |
| Vercel | `vercel.json` rewrite → `https://resume-analyzer-backend.onrender.com` |

Requests time out after 120 s, because the free Render instance can take
close to a minute to wake up.

## Demo mode

Open `/?demo=high` or `/?demo=low` to render the results page with sample
data that has the same shape as a real `/api/analyze` response, so you can
work on the UI without running the backend.

## Structure

```text
src/
├── App.jsx                  view switching, routing (/, /privacy, /terms), API call
├── components/
│   ├── UploadView.jsx       file drop zone (type/size checks) + job description
│   ├── AnalyzingView.jsx    loading state with a cold-start notice
│   ├── ResultsView.jsx      results layout
│   ├── ScoreGauge.jsx       score gauge, quick metrics, "Why this score?" breakdown
│   ├── SkillChips.jsx       matched / missing skills
│   ├── SuggestionsSection.jsx
│   ├── RoleBarChart.jsx     top job categories + low-confidence notice
│   ├── Toast.jsx            error toast
│   ├── ErrorBoundary.jsx
│   └── NotFoundView.jsx, PrivacyPolicyView.jsx, TermsOfUseView.jsx
├── hooks/useCountUp.js      number count-up animation
└── utils/format.js          display labels for skills, roles and score factors
```

## Deployment (Vercel)

The Vercel project's **Root Directory is `frontend`**, so `frontend/vercel.json`
is the active config: Vite build to `dist/`, `/api/*` rewritten to the Render
backend, and every other path served `index.html` for client-side routing.
