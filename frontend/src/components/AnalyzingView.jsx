import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

// The API answers in one response, so these describe what the server does;
// they advance once and hold on the last step until the result arrives.
const STEPS = ['Reading your resume', 'Finding skills and sections', 'Comparing with the job', 'Checking ATS-friendliness'];
const STEP_MS = 1100;
// Render's free tier sleeps when idle; after this long, explain the wait.
const SLOW_NOTICE_MS = 8000;
const LINES = [92, 64, 80, 0, 48, 88, 72, 84, 0, 56, 76, 68];

export default function AnalyzingView({ label = 'Analyzing' }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const timer = setInterval(() => setElapsed(Date.now() - start), 200);
    return () => clearInterval(timer);
  }, []);

  const step = Math.min(Math.floor(elapsed / STEP_MS), STEPS.length - 1);

  return (
    <motion.main
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="mx-auto flex w-full max-w-md flex-col items-center px-4 pt-16 sm:pt-24"
    >
      {/* A resume page being "read" by a highlighter */}
      <motion.div
        initial={{ rotate: -4, y: 20 }}
        animate={{ rotate: -2, y: 0 }}
        transition={{ type: 'spring', stiffness: 120, damping: 12 }}
        className="card relative w-60 p-5"
        aria-hidden
      >
        <div className="mb-4 h-3 w-24 rounded-full bg-ink/80" />
        <div className="space-y-2.5">
          {LINES.map((width, i) =>
            width === 0 ? (
              <div key={i} className="h-2" />
            ) : (
              <div key={i} className="relative h-2 rounded-full bg-sunken" style={{ width: `${width}%` }}>
                <motion.div
                  className="absolute inset-y-[-3px] left-0 rounded-sm bg-highlight/80"
                  initial={{ width: '0%' }}
                  animate={{ width: ['0%', '100%', '100%', '0%'] }}
                  transition={{ duration: 2.4, times: [0, 0.35, 0.8, 1], repeat: Infinity, delay: i * 0.18, ease: 'easeInOut' }}
                />
              </div>
            ),
          )}
        </div>
      </motion.div>

      <div className="mt-10 text-center" role="status" aria-live="polite">
        <h2 className="font-display text-2xl font-semibold">{label}…</h2>
        <motion.p key={step} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="mt-2 text-sm text-muted">
          {STEPS[step]}
        </motion.p>
      </div>

      <div className="mt-6 flex w-48 gap-1.5" aria-hidden>
        {STEPS.map((s, i) => (
          <div key={s} className="h-1.5 flex-1 overflow-hidden rounded-full bg-sunken">
            <motion.div className="h-full bg-accent" initial={{ width: 0 }} animate={{ width: i <= step ? '100%' : 0 }} transition={{ duration: 0.4 }} />
          </div>
        ))}
      </div>

      {elapsed >= SLOW_NOTICE_MS && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8 max-w-sm text-center text-sm text-muted">
          Still working ({Math.round(elapsed / 1000)}s). The server sleeps when idle, so the first analysis can take up to a minute.
        </motion.p>
      )}
    </motion.main>
  );
}
