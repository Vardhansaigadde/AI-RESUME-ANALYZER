import React, { useState } from 'react';
import { motion } from 'framer-motion';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const slideInLeftVariant = {
  hidden: { opacity: 0, x: -24 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] },
  },
};

export default function SuggestionsSection({ suggestions = [], onReset }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!suggestions || suggestions.length === 0) return;
    const textToCopy = suggestions
      .map((item, idx) => `${idx + 1}. ${item}`)
      .join('\n\n');
    navigator.clipboard?.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="hover-lift"
      style={{
        background: 'var(--card-white)',
        borderRadius: 'var(--radius-xl)',
        padding: '1.75rem',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.25rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '10px',
              background: 'var(--brand-teal-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--brand-teal)',
            }}
          >
            💡
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy-deep)' }}>
            Actionable Recommendations
          </h3>
        </div>

        {suggestions.length > 0 && (
          <button
            id="copy-suggestions-btn"
            onClick={handleCopy}
            title="Copy recommendations to clipboard"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: copied ? 'var(--success-bg)' : 'var(--off-white)',
              border: `1px solid ${copied ? 'var(--success)' : 'var(--border-light)'}`,
              padding: '6px 12px',
              borderRadius: 'var(--radius-full)',
              color: copied ? 'var(--success-dark)' : 'var(--text-muted)',
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {copied ? (
              <>
                <span>✓</span>
                <span>Copied!</span>
              </>
            ) : (
              <>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                <span>Copy</span>
              </>
            )}
          </button>
        )}
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
      >
        {suggestions.map((item, idx) => (
          <motion.div
            key={idx}
            variants={slideInLeftVariant}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              background: 'var(--off-white)',
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
            }}
          >
            <span
              style={{
                width: '22px',
                height: '22px',
                borderRadius: '50%',
                background: 'var(--brand-teal-bg)',
                color: 'var(--brand-teal)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.78rem',
                fontWeight: 800,
                flexShrink: 0,
                marginTop: '2px',
              }}
            >
              {idx + 1}
            </span>
            <p style={{ fontSize: '0.91rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
              {item}
            </p>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
