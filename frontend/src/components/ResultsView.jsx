import React from 'react';
import { motion } from 'framer-motion';
import ScoreGauge from './ScoreGauge';
import SkillChips from './SkillChips';
import RoleBarChart from './RoleBarChart';
import SuggestionsSection from './SuggestionsSection';

export default function ResultsView({ result, onReset }) {
  const matchedSkills = result?.matched_skills || [];
  const missingSkills = result?.missing_skills || [];
  const suggestions = result?.suggestions || [];
  const suggestedRoles = result?.suggested_roles || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -25 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      style={{
        background: 'var(--off-white)',
        color: 'var(--text-dark)',
        minHeight: '100vh',
        width: '100%',
        padding: '2.5rem 1.5rem 5rem 1.5rem',
      }}
    >
      <div style={{ maxWidth: '1180px', margin: '0 auto' }}>
        {/* TOP BAR / NAVIGATION */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
            marginBottom: '2.2rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Analysis Results
              </span>
            </div>
            <h1
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 'clamp(1.6rem, 3vw, 2.2rem)',
                fontWeight: 800,
                color: 'var(--navy-deep)',
                letterSpacing: '-0.02em',
              }}
            >
              Resume Fit Assessment
            </h1>
          </div>

          <button
            id="try-another-job-btn"
            onClick={onReset}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: '#FFFFFF',
              border: '1px solid var(--border-light)',
              padding: '10px 22px',
              borderRadius: 'var(--radius-full)',
              color: 'var(--navy-deep)',
              fontWeight: 700,
              fontSize: '0.92rem',
              cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--teal)';
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = 'var(--shadow-md)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-light)';
              e.currentTarget.style.transform = 'none';
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
            <span>Try Another Job</span>
          </button>
        </div>

        {/* SECTION 1: SCORE OVERVIEW CARD */}
        <ScoreGauge result={result} />

        {/* SECTION 2: SKILLS BREAKDOWN (MATCHED VS MISSING) */}
        <SkillChips matchedSkills={matchedSkills} missingSkills={missingSkills} />

        {/* SECTION 3: SUGGESTIONS & SUGGESTED ROLES GRID */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '1.75rem',
          }}
        >
          <SuggestionsSection suggestions={suggestions} onReset={onReset} />
          <RoleBarChart suggestedRoles={suggestedRoles} confidence={result?.confidence} />
        </div>
      </div>
    </motion.div>
  );
}
