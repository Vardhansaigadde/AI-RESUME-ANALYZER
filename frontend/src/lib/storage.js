// Small per-browser conveniences (resume draft, roadmap ticks, pace). Storage can be
// unavailable (private mode, blocked site data), so every access is guarded and the
// app works without it.

export const KEYS = {
  builder: 'fitlens:builder',
  progress: 'fitlens:roadmap-progress',
  pace: 'fitlens:hours-per-week',
};

export function readStorage(key, fallback = null) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function writeStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Not saved; the page still works
  }
}
