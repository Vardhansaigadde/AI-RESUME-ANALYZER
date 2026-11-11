// Reports browser crashes to the backend (POST /api/client-error), where they
// are logged next to API errors. Only the error message, stack and page path
// are sent: never resume text, form contents or the query string.
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const MAX_REPORTS = 5; // per page load, so a crash loop can't flood the API
const sent = new Set();

export function reportError(error, kind = 'error') {
  if (import.meta.env.DEV || sent.size >= MAX_REPORTS) return;
  const message = String(error?.message || error || 'Unknown error').slice(0, 500);
  if (sent.has(message)) return;
  sent.add(message);
  try {
    fetch(`${API_BASE}/api/client-error`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        kind,
        message,
        stack: String(error?.stack || '').slice(0, 4000),
        path: window.location.pathname.slice(0, 200),
      }),
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* reporting must never break the page */
  }
}

export function installErrorReporting() {
  window.addEventListener('error', (event) => reportError(event.error || event.message, 'error'));
  window.addEventListener('unhandledrejection', (event) => reportError(event.reason, 'rejection'));
}
