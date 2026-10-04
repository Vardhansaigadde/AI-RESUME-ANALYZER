// API client for the FitLens backend.
// VITE_API_BASE_URL is set on Vercel (direct calls to Render); locally it is
// unset and Vite proxies /api to the backend on :8000.
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

// Render's free tier can take close to a minute to wake up
const REQUEST_TIMEOUT_MS = 120000;

async function request(path, options) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, signal: controller.signal });
    if (!response.ok) {
      throw new Error(await errorMessage(response));
    }
    return response;
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('The request took too long. The server may be waking up, so please try again.');
    }
    if (err instanceof TypeError) {
      throw new Error('Could not reach the analysis server. Check your connection and try again.');
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function errorMessage(response) {
  try {
    const data = await response.json();
    if (typeof data?.detail === 'string') return data.detail;
    if (Array.isArray(data?.detail)) return 'Some fields are invalid. Please check your input and try again.';
  } catch {
    // Not JSON, e.g. a proxy error page while the server wakes up
  }
  if ([502, 503, 504].includes(response.status)) {
    return 'The analysis server is starting up. Please wait a moment and try again.';
  }
  return `Server error (${response.status}). Please try again.`;
}

/** Analyze an uploaded resume file, against a job description if one is given. */
export async function analyzeResume(file, jobDescription, studentMode = false, targetRole = null) {
  const form = new FormData();
  form.append('resume_file', file);
  form.append('job_description', jobDescription || '');
  form.append('student_mode', studentMode ? 'true' : 'false');
  if (targetRole) form.append('target_role', targetRole);
  const response = await request('/api/analyze', { method: 'POST', body: form });
  return response.json();
}

/** Re-analyze an edited, structured resume. */
export async function recheckResume(resume, jobDescription, studentMode = false, targetRole = null) {
  const response = await request('/api/recheck', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resume,
      job_description: jobDescription || '',
      student_mode: studentMode,
      target_role: targetRole,
    }),
  });
  return response.json();
}

/** Compare the resume with another target job role (no model re-run). */
export async function fetchRoleGap(resume, targetRole) {
  const response = await request('/api/role-gap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume, target_role: targetRole }),
  });
  return response.json();
}

/** Download the structured resume as an ATS-friendly .docx file. */
export async function downloadResumeDocx(resume) {
  const response = await request('/api/resume/docx', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(resume),
  });
  const blob = await response.blob();
  const match = /filename="([^"]+)"/.exec(response.headers.get('content-disposition') || '');
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = match ? match[1] : 'resume.docx';
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Live jobs and internships, each scored against the resume. Only the search words reach the job sites. */
export async function searchJobs(resume, { query, country, kind }) {
  const response = await request('/api/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume, query, country, kind }),
  });
  return response.json();
}

/** Countries the job search supports, and whether on-site jobs are switched on. */
export async function fetchJobOptions() {
  const response = await request('/api/jobs/options', { method: 'GET' });
  return response.json();
}

const GITHUB_API = 'https://api.github.com';

async function githubGet(path) {
  let response;
  try {
    response = await fetch(`${GITHUB_API}${path}`, { headers: { Accept: 'application/vnd.github+json' } });
  } catch {
    throw new Error('Could not reach GitHub. Check your connection and try again.');
  }
  if (response.status === 404) throw new Error('No GitHub user with that username.');
  if (response.status === 403 || response.status === 429) {
    const reset = Number(response.headers.get('x-ratelimit-reset'));
    const minutes = reset ? Math.max(1, Math.ceil((reset * 1000 - Date.now()) / 60000)) : null;
    throw new Error(
      `GitHub's free hourly limit for your network is used up${minutes ? `; try again in ${minutes} min` : ''}.`,
    );
  }
  if (!response.ok) throw new Error(`GitHub error (${response.status}). Please try again.`);
  return response.json();
}

/**
 * GitHub proof check. The browser reads the public profile and repositories
 * straight from GitHub (each visitor has their own free rate limit), then the
 * backend compares them with the resume.
 */
export async function checkGithub(resume, username) {
  const login = encodeURIComponent(username);
  const [user, repos] = await Promise.all([
    githubGet(`/users/${login}`),
    githubGet(`/users/${login}/repos?per_page=100&sort=pushed&type=owner`),
  ]);
  const cut = (text, n) => (text ? String(text).slice(0, n) : null);
  const response = await request('/api/github-check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resume,
      profile: {
        login: user.login,
        name: cut(user.name, 255),
        bio: cut(user.bio, 500),
        avatar_url: user.avatar_url || '',
        html_url: user.html_url || '',
        public_repos: user.public_repos || 0,
        followers: user.followers || 0,
      },
      repos: repos.slice(0, 100).map((r) => ({
        name: r.name,
        description: cut(r.description, 1000),
        topics: (r.topics || []).slice(0, 20),
        language: r.language,
        fork: r.fork,
        archived: r.archived,
        pushed_at: r.pushed_at,
        stargazers_count: r.stargazers_count || 0,
        html_url: r.html_url || '',
        homepage: cut(r.homepage, 500),
      })),
    }),
  });
  return { ...(await response.json()), profile: user };
}
