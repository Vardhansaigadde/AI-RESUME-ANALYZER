import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const PIPELINE_STEPS = [
  {
    title: 'Reading your resume...',
    subtitle: 'Extracting candidate text, skills taxonomy, and document structure',
    icon: '📄',
  },
  {
    title: 'Comparing with the job description...',
    subtitle: 'Extracting required job competencies and computing TF-IDF similarity',
    icon: '🔍',
  },
  {
    title: 'Calculating your fit score...',
    subtitle: 'Applying RobustScaler and predicting alignment via trained Ridge regression',
    icon: '📊',
  },
  {
    title: 'Finding your best-fit roles...',
    subtitle: 'Querying calibrated LinearSVC classifier for top role probabilities',
    icon: '🎯',
  },
];

// The API answers in a single response, so the steps below describe what the
// server does rather than report live progress: they advance once and then
// hold on the last step until the result arrives.
const STEP_INTERVAL_MS = 1250;
// Render's free tier sleeps when idle; after this long, explain the wait.
const SLOW_NOTICE_MS = 8000;

export default function AnalyzingView() {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      setElapsedMs(elapsed);
      setCurrentStepIndex(Math.min(Math.floor(elapsed / STEP_INTERVAL_MS), PIPELINE_STEPS.length - 1));
    }, 250);

    return () => clearInterval(interval);
  }, []);

  const currentStep = PIPELINE_STEPS[currentStepIndex];
  const isSlow = elapsedMs >= SLOW_NOTICE_MS;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.25 } }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: 'relative',
        zIndex: 1,
        maxWidth: '680px',
        width: '90%',
        margin: '5rem auto',
        padding: '3rem 2rem',
        background: 'var(--navy-card)',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--navy-border)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: '0 25px 60px rgba(10, 14, 38, 0.5)',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {/* Animated Radar / Pulsing Core */}
      <div style={{ position: 'relative', width: '130px', height: '130px', marginBottom: '2.5rem' }}>
        {/* Outer Ring Pulse */}
        <motion.div
          animate={{ scale: [1, 1.45, 1], opacity: [0.35, 0, 0.35] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: '50%',
            border: '2px solid var(--brand-teal)',
            boxShadow: '0 0 25px var(--brand-teal-glow)',
          }}
        />

        {/* Middle Ring Pulse */}
        <motion.div
          animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0.1, 0.5] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut', delay: 0.4 }}
          style={{
            position: 'absolute',
            inset: '12px',
            borderRadius: '50%',
            border: '2px solid var(--brand-teal-light)',
          }}
        />

        {/* Core Animated Orb */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
          style={{
            position: 'absolute',
            inset: '24px',
            borderRadius: '50%',
            background: 'conic-gradient(from 0deg, var(--brand-teal-light), var(--brand-teal), var(--brand-teal-light))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 35px var(--brand-teal-glow)',
          }}
        >
          <div
            style={{
              width: '58px',
              height: '58px',
              borderRadius: '50%',
              background: 'var(--navy-deep)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.6rem',
            }}
          >
            <motion.span
              key={currentStep.icon}
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {currentStep.icon}
            </motion.span>
          </div>
        </motion.div>
      </div>

      {/* Dynamic Cycling Step Text */}
      <div style={{ minHeight: '80px', marginBottom: '2rem' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
          >
            <h2
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.45rem',
                fontWeight: 700,
                color: '#FFFFFF',
                marginBottom: '0.4rem',
              }}
            >
              {currentStep.title}
            </h2>
            <p
              style={{
                fontSize: '0.88rem',
                color: 'var(--brand-teal-light)',
                opacity: 0.9,
                fontWeight: 500,
              }}
            >
              {currentStep.subtitle}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Step Pipeline Indicators */}
      <div
        style={{
          display: 'flex',
          gap: '10px',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          maxWidth: '320px',
        }}
      >
        {PIPELINE_STEPS.map((step, idx) => {
          const isActive = idx === currentStepIndex;
          const isDone = idx < currentStepIndex;

          return (
            <div
              key={step.title}
              style={{
                flex: 1,
                height: '6px',
                borderRadius: '3px',
                background: isActive
                  ? 'var(--brand-teal)'
                  : isDone
                  ? 'rgba(13, 148, 136, 0.45)'
                  : 'rgba(255, 255, 255, 0.12)',
                boxShadow: isActive ? '0 0 10px var(--brand-teal-glow)' : 'none',
                transition: 'all 0.3s ease',
              }}
            />
          );
        })}
      </div>

      <div
        role="status"
        aria-live="polite"
        style={{ marginTop: '1.75rem', fontSize: '0.78rem', color: 'var(--text-light-muted)', maxWidth: '420px', lineHeight: 1.5 }}
      >
        {isSlow
          ? `Still working (${Math.round(elapsedMs / 1000)}s). The server sleeps when idle, so the first analysis can take up to a minute.`
          : 'Analyzing your resume…'}
      </div>
    </motion.div>
  );
}
