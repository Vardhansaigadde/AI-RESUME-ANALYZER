import React from 'react';
import { motion } from 'framer-motion';

export default function NotFoundView({ onHome }) {
  return (
    <motion.main
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: 'relative',
        zIndex: 1,
        maxWidth: '680px',
        width: '90%',
        margin: '5rem auto',
        padding: '3.5rem 2rem',
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
      {/* 404 Numerical & Target Graphic */}
      <div style={{ position: 'relative', marginBottom: '2rem' }}>
        <motion.div
          animate={{ scale: [1, 1.08, 1], rotate: [0, 5, -5, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            width: '96px',
            height: '96px',
            borderRadius: '28px',
            background: 'var(--brand-teal-bg)',
            border: '2px solid var(--brand-teal-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.5rem auto',
            boxShadow: '0 0 35px var(--brand-teal-glow)',
          }}
        >
          <span style={{ fontSize: '3rem' }}>🧭</span>
        </motion.div>

        <span
          style={{
            display: 'inline-block',
            background: 'var(--brand-teal-bg)',
            color: 'var(--brand-teal-light)',
            border: '1px solid var(--brand-teal-border)',
            padding: '4px 14px',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.82rem',
            fontWeight: 700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: '1rem',
          }}
        >
          404 • Page Not Found
        </span>

        <h1
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: 'clamp(2rem, 4vw, 2.7rem)',
            fontWeight: 800,
            color: '#FFFFFF',
            lineHeight: 1.2,
            marginBottom: '0.8rem',
            letterSpacing: '-0.02em',
          }}
        >
          Lost in Fit<span style={{ color: 'var(--brand-teal-light)' }}>Lens</span>?
        </h1>

        <p
          style={{
            fontSize: '0.96rem',
            color: 'var(--text-light-muted)',
            lineHeight: 1.6,
            maxWidth: '480px',
            margin: '0 auto',
          }}
        >
          The page you are looking for doesn't exist, has been moved, or the link may be broken. Let's get you back on track to analyze your resume fit.
        </p>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
        <button
          id="not-found-home-btn"
          onClick={onHome}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
            color: '#FFFFFF',
            border: 'none',
            padding: '14px 32px',
            borderRadius: 'var(--radius-full)',
            fontFamily: 'var(--font-heading)',
            fontSize: '1rem',
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(13, 148, 136, 0.4)',
            transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 8px 28px rgba(13, 148, 136, 0.6)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'none';
            e.currentTarget.style.boxShadow = '0 4px 20px rgba(13, 148, 136, 0.4)';
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          <span>Back to Home</span>
        </button>
      </div>
    </motion.main>
  );
}
