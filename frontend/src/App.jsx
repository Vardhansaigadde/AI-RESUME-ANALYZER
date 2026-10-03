import React, { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import UploadView from './components/UploadView';
import AnalyzingView from './components/AnalyzingView';
import ResultsView from './components/ResultsView';
import NotFoundView from './components/NotFoundView';
import PrivacyPolicyView from './components/PrivacyPolicyView';
import TermsOfUseView from './components/TermsOfUseView';
import Toast from './components/Toast';

// Demo payloads for ?demo=high / ?demo=low. They mirror the real
// /api/analyze response shape (lowercase canonical skills, dataset role
// labels, the 3 model features and a score_breakdown that sums to the score)
// so the demo exercises exactly the same rendering paths as a live result.
const DEMO_HIGH_RESULT = {
  match_score: 82.86,
  matched_skills: ['docker', 'git', 'machine learning', 'python', 'rest api', 'sql'],
  missing_skills: ['aws', 'ci/cd', 'kubernetes'],
  features: {
    tfidf_similarity: 0.2851,
    skill_overlap_ratio: 0.6667,
    resume_word_count: 612,
  },
  score_breakdown: {
    baseline: 39.33,
    tfidf_similarity: 20.04,
    skill_overlap_ratio: 24.38,
    resume_word_count: -0.89,
  },
  resume_skills_count: 14,
  required_skills_count: 9,
  suggested_roles: [
    { role: 'INFORMATION-TECHNOLOGY', match_percent: 71.2 },
    { role: 'ENGINEERING', match_percent: 12.4 },
    { role: 'CONSULTANT', match_percent: 4.1 },
  ],
  suggestions: [
    "'aws': This is a commonly required skill across job postings — strongly consider adding it.",
    "Consider adding 'ci/cd' to better match the job requirements.",
    "Consider adding 'kubernetes' to better match the job requirements.",
  ],
  confidence: 'high',
};

const DEMO_LOW_RESULT = {
  match_score: 30.49,
  matched_skills: ['git', 'python'],
  missing_skills: ['aws', 'ci/cd', 'docker', 'kubernetes', 'rest api', 'sql', 'terraform'],
  features: {
    tfidf_similarity: 0.0712,
    skill_overlap_ratio: 0.2222,
    resume_word_count: 168,
  },
  score_breakdown: {
    baseline: 39.33,
    tfidf_similarity: -8.05,
    skill_overlap_ratio: 3.08,
    resume_word_count: -3.87,
  },
  resume_skills_count: 5,
  required_skills_count: 9,
  suggested_roles: [
    { role: 'INFORMATION-TECHNOLOGY', match_percent: 38.5 },
    { role: 'ENGINEERING', match_percent: 17.9 },
    { role: 'DESIGNER', match_percent: 9.3 },
  ],
  suggestions: [
    "'sql': This is a commonly required skill across job postings — strongly consider adding it.",
    "Consider adding 'aws' to better match the job requirements.",
    "Consider adding 'docker' to better match the job requirements.",
    "Include a dedicated 'Projects' section to showcase practical, hands-on applications of your skills.",
  ],
  confidence: 'low',
};

// The backend runs on Render's free tier, which sleeps when idle; the first
// request after a sleep can take close to a minute.
const REQUEST_TIMEOUT_MS = 120000;

export default function App() {
  const getInitialView = () => {
    if (typeof window === 'undefined') return 'upload';
    const pathname = window.location.pathname.replace(/\/+$/, '') || '/';
    if (pathname === '/privacy') return 'privacy';
    if (pathname === '/terms') return 'terms';
    if (pathname !== '/' && pathname !== '/index.html') {
      return 'not-found';
    }
    const demoParam = new URLSearchParams(window.location.search).get('demo');
    if (demoParam === 'results' || demoParam === 'high' || demoParam === 'low') {
      return 'results';
    }
    return 'upload';
  };

  const demoParam = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('demo') : null;
  const isDemo = demoParam === 'results' || demoParam === 'high' || demoParam === 'low';
  const initialResult = demoParam === 'low' ? DEMO_LOW_RESULT : isDemo ? DEMO_HIGH_RESULT : null;
  const [view, setView] = useState(getInitialView); // 'upload' | 'analyzing' | 'results' | 'not-found' | 'privacy' | 'terms'
  const [file, setFile] = useState(null);
  const [jobText, setJobText] = useState('');
  const [result, setResult] = useState(initialResult);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handlePopState = () => {
      const pathname = window.location.pathname.replace(/\/+$/, '') || '/';
      if (pathname === '/privacy') {
        setView('privacy');
      } else if (pathname === '/terms') {
        setView('terms');
      } else if (pathname !== '/' && pathname !== '/index.html') {
        setView('not-found');
      } else {
        const demo = new URLSearchParams(window.location.search).get('demo');
        if (demo === 'results' || demo === 'high' || demo === 'low') {
          setView('results');
        } else {
          setView('upload');
        }
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleGoHome = () => {
    if (window.location.pathname !== '/') {
      window.history.pushState({}, '', '/');
    }
    setView('upload');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleGoPrivacy = (e) => {
    if (e) e.preventDefault();
    if (window.location.pathname !== '/privacy') {
      window.history.pushState({}, '', '/privacy');
    }
    setView('privacy');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleGoTerms = (e) => {
    if (e) e.preventDefault();
    if (window.location.pathname !== '/terms') {
      window.history.pushState({}, '', '/terms');
    }
    setView('terms');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please upload your resume file (PDF or DOCX).');
      return;
    }
    if (!jobText.trim()) {
      setError('Please enter a job description to analyze.');
      return;
    }

    setError(null);
    setView('analyzing');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const formData = new FormData();
      formData.append('resume_file', file);
      formData.append('job_description', jobText);

      // Support VITE_API_BASE_URL env var, Vite dev proxy, or Vercel rewrites
      const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
      const apiUrl = `${apiBase}/api/analyze`;
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorMsg = `Server error (${response.status})`;
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // Response was not JSON (e.g. a proxy error page while the server wakes up)
          if (response.status === 502 || response.status === 503 || response.status === 504) {
            errorMsg = 'The analysis server is starting up. Please wait a moment and try again.';
          }
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setResult(data);
      setView('results');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Analysis failed:', err);
      if (err.name === 'AbortError') {
        setError('The analysis took too long. The server may be waking up — please try again.');
      } else if (err instanceof TypeError) {
        setError('Could not reach the analysis server. Check your connection and try again.');
      } else {
        setError(err.message || 'Failed to complete analysis. Please try again.');
      }
      setView('upload');
    } finally {
      clearTimeout(timeoutId);
    }
  };

  // Stable reference so the Toast's auto-dismiss timer isn't restarted on every render
  const clearError = useCallback(() => setError(null), []);

  const handleReset = () => {
    handleGoHome();
  };

  return (
    <div style={{ position: 'relative', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Ambient background orbs for dark views */}
      {view !== 'results' && (
        <div className="ambient-background">
          <div className="ambient-orb orb-1" />
          <div className="ambient-orb orb-2" />
          <div className="ambient-orb orb-3" />
        </div>
      )}

      {/* Slide-in Error Toast */}
      <Toast message={error} onClose={clearError} />

      {/* Top Navigation Bar */}
      <header
        className="app-navbar"
        style={{
          borderBottom: view === 'results' ? '1px solid var(--border-light)' : '1px solid rgba(255, 255, 255, 0.06)',
          background: view === 'results' ? '#FFFFFF' : 'transparent',
          color: view === 'results' ? 'var(--navy-deep)' : '#FFFFFF',
          transition: 'background 0.3s ease, border-color 0.3s ease',
        }}
      >
        <div
          className="brand-container"
          onClick={handleGoHome}
          style={{ cursor: 'pointer' }}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && handleGoHome()}
          title="Go to FitLens Home"
        >
          <div className="brand-logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="22" y1="12" x2="18" y2="12" />
              <line x1="6" y1="12" x2="2" y2="12" />
              <line x1="12" y1="6" x2="12" y2="2" />
              <line x1="12" y1="22" x2="12" y2="18" />
            </svg>
          </div>
          <div>
            <span className="brand-title" style={{ color: view === 'results' ? 'var(--navy-deep)' : '#FFFFFF' }}>
              Fit<span>Lens</span>
            </span>
          </div>
        </div>

      </header>

      {/* View Switcher with Smooth AnimatePresence */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <AnimatePresence mode="wait">
          {view === 'upload' && (
            <motion.div key="upload" style={{ width: '100%', flex: 1, display: 'flex' }}>
              <UploadView
                file={file}
                setFile={setFile}
                jobText={jobText}
                setJobText={setJobText}
                onAnalyze={handleAnalyze}
                onError={setError}
              />
            </motion.div>
          )}

          {view === 'analyzing' && (
            <motion.div key="analyzing" style={{ width: '100%', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AnalyzingView />
            </motion.div>
          )}

          {view === 'results' && result && (
            <motion.div key="results" style={{ width: '100%', flex: 1 }}>
              <ResultsView result={result} onReset={handleReset} />
            </motion.div>
          )}

          {view === 'not-found' && (
            <motion.div key="not-found" style={{ width: '100%', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <NotFoundView onHome={handleGoHome} />
            </motion.div>
          )}

          {view === 'privacy' && (
            <motion.div key="privacy" style={{ width: '100%', flex: 1, display: 'flex' }}>
              <PrivacyPolicyView onHome={handleGoHome} />
            </motion.div>
          )}

          {view === 'terms' && (
            <motion.div key="terms" style={{ width: '100%', flex: 1, display: 'flex' }}>
              <TermsOfUseView onHome={handleGoHome} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Minimal Footer with Legal Links */}
      <footer
        style={{
          position: 'relative',
          zIndex: 1,
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          maxWidth: '1200px',
          width: '92%',
          margin: '0 auto',
          padding: '1.5rem 0',
          fontSize: '0.82rem',
          color: view === 'results' ? 'var(--text-muted)' : 'rgba(255, 255, 255, 0.45)',
          borderTop: view === 'results' ? '1px solid var(--border-light)' : '1px solid rgba(255, 255, 255, 0.06)',
          background: view === 'results' ? '#FFFFFF' : 'transparent',
          gap: '1rem',
        }}
      >
        <div>
          <span>© 2026 FitLens. All rights reserved.</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            id="footer-privacy-btn"
            onClick={handleGoPrivacy}
            style={{
              background: 'none',
              border: 'none',
              padding: 0,
              font: 'inherit',
              cursor: 'pointer',
              color: 'inherit',
              textDecoration: 'none',
              transition: 'color 0.2s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--brand-teal)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'inherit')}
          >
            Privacy Policy
          </button>
          <span style={{ opacity: 0.35 }}>•</span>
          <button
            id="footer-terms-btn"
            onClick={handleGoTerms}
            style={{
              background: 'none',
              border: 'none',
              padding: 0,
              font: 'inherit',
              cursor: 'pointer',
              color: 'inherit',
              textDecoration: 'none',
              transition: 'color 0.2s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--brand-teal)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'inherit')}
          >
            Terms of Use
          </button>
        </div>
      </footer>
    </div>
  );
}
