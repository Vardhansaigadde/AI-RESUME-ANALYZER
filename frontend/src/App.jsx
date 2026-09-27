import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import UploadView from './components/UploadView';
import AnalyzingView from './components/AnalyzingView';
import ResultsView from './components/ResultsView';
import NotFoundView from './components/NotFoundView';
import PrivacyPolicyView from './components/PrivacyPolicyView';
import TermsOfUseView from './components/TermsOfUseView';
import Toast from './components/Toast';

const DEMO_HIGH_RESULT = {
  match_score: 84.5,
  matched_skills: ['Python', 'SQL', 'FastAPI', 'Machine Learning', 'Docker', 'Git', 'Pandas'],
  missing_skills: ['Kubernetes', 'AWS', 'CI/CD'],
  features: {
    tfidf_similarity: 0.782,
    skill_overlap: 0.70,
    role_alignment: 0.85,
  },
  resume_skills_count: 14,
  required_skills_count: 10,
  suggested_roles: [
    { role: 'Data Scientist', match_percent: 88.4 },
    { role: 'Machine Learning Engineer', match_percent: 76.2 },
    { role: 'Software Engineer', match_percent: 62.1 },
  ],
  suggestions: [
    'Add evidence of production Kubernetes deployment experience to match infrastructure requirements.',
    'Mention hands-on experience with AWS cloud services (S3, EC2, ECS) in your project summaries.',
    'Highlight automated testing and CI/CD pipelines you configured or maintained.',
  ],
  confidence: 'high',
};

const DEMO_LOW_RESULT = {
  match_score: 28.0,
  matched_skills: ['Python', 'Git'],
  missing_skills: ['Kubernetes', 'AWS', 'CI/CD', 'Docker', 'Microservices', 'GraphQL', 'Terraform'],
  features: {
    tfidf_similarity: 0.312,
    skill_overlap: 0.22,
    role_alignment: 0.35,
  },
  resume_skills_count: 3,
  required_skills_count: 9,
  suggested_roles: [
    { role: 'Data Analyst', match_percent: 36.5 },
    { role: 'Technical Writer', match_percent: 29.8 },
    { role: 'Operations', match_percent: 21.4 },
  ],
  suggestions: [
    'Target role requires significant cloud infrastructure tooling (AWS, Terraform, Kubernetes).',
    'Demonstrate microservices and CI/CD pipeline automation projects in your experience section.',
    'Include hands-on containerization and distributed system design achievements.',
  ],
  confidence: 'low',
};

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
      });

      if (!response.ok) {
        let errorMsg = `Server error (${response.status})`;
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // Response was not JSON
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setResult(data);
      setView('results');
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(err.message || 'Failed to complete analysis. Please ensure the backend is running.');
      setView('upload');
    }
  };

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
      <Toast message={error} onClose={() => setError(null)} />

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
