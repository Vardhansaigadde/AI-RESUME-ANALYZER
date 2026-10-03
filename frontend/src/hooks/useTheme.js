import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'fitlens-theme';

function systemPrefersDark() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches;
}

function savedTheme() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

/** Light/dark theme: follows the system until the user picks one, then remembers it. */
export function useTheme() {
  const [dark, setDark] = useState(() => (savedTheme() ? savedTheme() === 'dark' : systemPrefersDark()));

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  // Keep following the system setting while the user hasn't chosen
  useEffect(() => {
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!media) return undefined;
    const onChange = (event) => {
      if (!savedTheme()) setDark(event.matches);
    };
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, []);

  const toggle = useCallback(() => {
    setDark((current) => {
      const next = !current;
      try {
        localStorage.setItem(STORAGE_KEY, next ? 'dark' : 'light');
      } catch {
        // storage unavailable: the choice lasts for this page view only
      }
      return next;
    });
  }, []);

  return { dark, toggle };
}
