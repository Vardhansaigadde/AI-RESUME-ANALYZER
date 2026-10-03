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

/** Analyze an uploaded resume file against a job description. */
export async function analyzeResume(file, jobDescription) {
  const form = new FormData();
  form.append('resume_file', file);
  form.append('job_description', jobDescription);
  const response = await request('/api/analyze', { method: 'POST', body: form });
  return response.json();
}

/** Re-analyze an edited, structured resume. */
export async function recheckResume(resume, jobDescription) {
  const response = await request('/api/recheck', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume, job_description: jobDescription }),
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
