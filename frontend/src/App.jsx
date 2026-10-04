import { AnimatePresence } from 'framer-motion';
import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import AnalyzingView from './components/AnalyzingView';
import Footer from './components/layout/Footer';
import Header from './components/layout/Header';
import Dashboard from './components/pages/Dashboard';
import { NotFoundPage, PrivacyPage, TermsPage } from './components/pages/LegalPages';
import ResultsView from './components/results/ResultsView';
import Toast from './components/ui/Toast';
import UploadView from './components/upload/UploadView';
import { useTheme } from './hooks/useTheme';
import { analyzeResume, recheckResume } from './lib/api';
import { DEMO_HIGH_RESULT, DEMO_LOW_RESULT, DEMO_RESUME_ONLY_RESULT } from './lib/demo';

// Loaded when first opened, to keep the first page fast
const BuilderPage = lazy(() => import('./components/pages/BuilderPage'));
const JobsPage = lazy(() => import('./components/pages/JobsPage'));
const LearnPage = lazy(() => import('./components/pages/LearnPage'));

const PAGES = {
  '/': 'home',
  '/index.html': 'home',
  '/check': 'check',
  '/build': 'build',
  '/jobs': 'jobs',
  '/learn': 'learn',
  '/privacy': 'privacy',
  '/terms': 'terms',
};
const DEMO_JOB = 'Junior software engineer: Python, SQL, Docker, AWS, Kubernetes, CI/CD and REST APIs.';

function demoResult() {
  const demo = new URLSearchParams(window.location.search).get('demo');
  if (demo === 'low') return DEMO_LOW_RESULT;
  if (demo === 'resume') return DEMO_RESUME_ONLY_RESULT;
  if (demo === 'high' || demo === 'results') return DEMO_HIGH_RESULT;
  return null;
}

function currentPage() {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  // ?demo=… opens a sample report
  if (demoResult() && PAGES[path] === 'home') return 'check';
  return PAGES[path] || 'not-found';
}

export default function App() {
  const { dark, toggle } = useTheme();
  const [page, setPage] = useState(currentPage);
  const [file, setFile] = useState(null);
  const [jobText, setJobText] = useState(() => (demoResult() && demoResult().mode !== 'resume_only' ? DEMO_JOB : ''));
  const [studentMode, setStudentMode] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  // `original` is the analysis of the upload; `result` changes after re-checks
  const [original, setOriginal] = useState(demoResult);
  const [result, setResult] = useState(demoResult);
  // A resume handed from the report's editor to the builder
  const [builderSeed, setBuilderSeed] = useState(null);
  const [toast, setToast] = useState(null);

  const notify = useCallback((t) => setToast(t), []);
  const clearToast = useCallback(() => setToast(null), []);
  const showError = useCallback((message) => setToast(message ? { tone: 'error', message } : null), []);

  useEffect(() => {
    const onPop = () => setPage(currentPage());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const navigate = useCallback((path) => {
    if (window.location.pathname + window.location.search !== path) window.history.pushState({}, '', path);
    setPage(currentPage());
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const goHome = useCallback(() => navigate('/'), [navigate]);

  const startOver = () => {
    setResult(null);
    setOriginal(null);
    navigate('/check');
  };

  const analyze = async (mode = studentMode, job = jobText) => {
    setToast(null);
    setAnalyzing(true);
    window.scrollTo({ top: 0 });
    try {
      const data = await analyzeResume(file, job, mode);
      setOriginal(data);
      setResult(data);
    } catch (err) {
      setToast({ tone: 'error', message: err.message });
    } finally {
      setAnalyzing(false);
    }
  };

  // "Check my score" from the builder: a resume-only report for the built resume
  const checkBuiltResume = async (resume) => {
    setToast(null);
    setAnalyzing(true);
    navigate('/check');
    try {
      const data = await recheckResume(resume, '', studentMode, null);
      setFile(null);
      setJobText('');
      setOriginal(data);
      setResult(data);
    } catch (err) {
      setToast({ tone: 'error', message: err.message });
    } finally {
      setAnalyzing(false);
    }
  };

  const openInBuilder = (draft) => {
    setBuilderSeed(draft);
    navigate('/build');
  };

  let content;
  if (page === 'home') content = <Dashboard key="home" onNavigate={navigate} />;
  else if (page === 'build')
    content = (
      <BuilderPage key="build" notify={notify} onCheck={checkBuiltResume} seed={builderSeed} onSeedUsed={() => setBuilderSeed(null)} />
    );
  else if (page === 'jobs') content = <JobsPage key="jobs" resume={result?.resume || null} onNavigate={navigate} />;
  else if (page === 'learn') content = <LearnPage key="learn" notify={notify} onNavigate={navigate} />;
  else if (page === 'privacy') content = <PrivacyPage key="privacy" onHome={goHome} />;
  else if (page === 'terms') content = <TermsPage key="terms" onHome={goHome} />;
  else if (page === 'not-found') content = <NotFoundPage key="404" onHome={goHome} />;
  else if (analyzing) content = <AnalyzingView key="analyzing" />;
  else if (result)
    content = (
      <ResultsView
        key={[DEMO_HIGH_RESULT, DEMO_LOW_RESULT, DEMO_RESUME_ONLY_RESULT].includes(original) ? 'demo' : 'results'}
        result={result}
        original={original}
        jobText={jobText}
        onResult={setResult}
        onStartOver={startOver}
        canReanalyze={Boolean(file)}
        onReanalyze={({ studentMode: mode = studentMode, job = jobText } = {}) => {
          setStudentMode(mode);
          setJobText(job);
          analyze(mode, job);
        }}
        onJobText={setJobText}
        onOpenBuilder={openInBuilder}
        notify={notify}
      />
    );
  else
    content = (
      <UploadView
        key="upload"
        file={file}
        setFile={setFile}
        jobText={jobText}
        setJobText={setJobText}
        studentMode={studentMode}
        setStudentMode={setStudentMode}
        onAnalyze={() => analyze()}
        onError={showError}
      />
    );

  return (
    <div className="flex min-h-screen flex-col pb-16 md:pb-0">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-card focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <Header dark={dark} onToggleTheme={toggle} page={page} onNavigate={navigate} />
      <Toast toast={toast} onClose={clearToast} />
      <div id="main" className="flex-1">
        <Suspense fallback={<div className="min-h-[60vh]" aria-busy="true" />}>
          <AnimatePresence mode="wait">{content}</AnimatePresence>
        </Suspense>
      </div>
      <Footer onNavigate={navigate} />
    </div>
  );
}
