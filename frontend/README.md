# FitLens frontend

React 19 + Vite + Tailwind CSS 4 single-page app for the Resume Analyzer. Upload a resume
(PDF/DOCX) and a job description to get a match score with a per-factor breakdown, a decoded view
of the job, an ATS check (with a student / fresher checklist), a skill-gap learning plan, and an
editor with a live bullet coach to fix the resume, re-check it and download an ATS-friendly `.docx`.

Live: <https://resumefitlens.vercel.app>

## Design

A "paper & highlighter" theme: warm paper surfaces, ink text, one ink-blue accent, highlighter
yellow for matches and a red pen for gaps. Fraunces for headings, Inter for text, JetBrains Mono
for numbers. Light and dark themes follow the system setting until the user picks one (saved in
`localStorage`).

Motion (Framer Motion) is small and purposeful: matched skills get a highlighter swipe, missing
ones a hand-drawn red underline, the ATS score lands like a rubber stamp, the active tab is a
highlighter stroke that springs between tabs, and scores count up. Everything respects the OS
"reduce motion" setting (`MotionConfig reducedMotion="user"`).

## Run locally

```bash
npm install
npm run dev        # http://localhost:5173
```

The dev server proxies `/api/*` to `http://127.0.0.1:8000` (see `vite.config.js`), so start the
backend from the repository root first:

```bash
uvicorn app.main:app --reload
```

Other scripts: `npm run build` (production bundle in `dist/`), `npm run preview` (serve the build),
`npm run lint` (oxlint).

## How it talks to the API

`src/lib/api.js` calls `${VITE_API_BASE_URL}/api/...` with a 120 s timeout (the free Render
instance can take close to a minute to wake up):

| Call | Endpoint |
| --- | --- |
| Analyze an upload | `POST /api/analyze` (multipart `resume_file`, `job_description`) |
| Re-check the edited resume | `POST /api/recheck` (JSON) |
| Download the edited resume | `POST /api/resume/docx` (JSON → `.docx`) |

| Environment | `VITE_API_BASE_URL` | Requests go to |
| --- | --- | --- |
| `npm run dev` | unset | `/api/*` → Vite proxy → `http://127.0.0.1:8000` |
| Vercel (production) | `https://ai-resume-analyzer-xb45.onrender.com` (Vercel env var) | the Render backend directly; it allows this origin via `CORS_ORIGINS` |
| Vercel without the env var | unset | `/api/*` → `vercel.json` rewrite → the same Render backend |

## Demo mode

Open `/?demo=high` or `/?demo=low` to see the results page with sample data (same shape as a real
`/api/analyze` response, defined in `src/lib/demo.js`) without running the backend.

## Structure

```text
src/
├── App.jsx                      routing (/, /privacy, /terms), upload → analyzing → results flow
├── main.jsx, index.css          entry point; Tailwind theme tokens (light + dark) and base styles
├── lib/
│   ├── api.js                   fetch wrappers, timeouts, error messages, .docx download
│   ├── bulletCoach.js           instant rule-based feedback on resume bullets
│   ├── demo.js                  demo payloads
│   └── resume.js                editor draft helpers, score colours
├── hooks/                       useCountUp (number animation), useTheme (light/dark)
├── utils/format.js              display labels for skills, roles and score factors
└── components/
    ├── layout/                  Header (logo, theme toggle), Footer
    ├── ui/                      Button, Switch, Tabs (animated), Toast
    ├── upload/UploadView.jsx    hero, resume drop zone, job description, student-mode switch
    ├── AnalyzingView.jsx        loading state with a cold-start notice
    ├── results/
    │   ├── ResultsView.jsx      summary + tabs, student mode, re-check/download actions
    │   ├── SummaryCards.jsx     match dial, ATS stamp, closest job category
    │   ├── MatchTab.jsx         job at a glance, score breakdown, skills, suggestions, categories
    │   ├── JobInsightsCard.jsx  decoded job posting
    │   ├── AtsTab.jsx           ATS checklist with fixes
    │   ├── EditTab.jsx          section-by-section resume editor
    │   ├── LearnTab.jsx         skill-gap learning plan
    │   └── edit/fields.jsx      fields, skill tag input, list/entry editors, bullet coach
    ├── pages/LegalPages.jsx     Privacy, Terms, 404
    └── ErrorBoundary.jsx
```

## Deployment (Vercel)

The Vercel project's **Root Directory is `frontend`**, so `frontend/vercel.json` is the active
config: Vite build to `dist/`, `/api/*` rewritten to the Render backend, and every other path
served `index.html` for client-side routing.
