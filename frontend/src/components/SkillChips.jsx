import React from 'react';
import { motion } from 'framer-motion';
import { formatSkill } from '../utils/format';

const chipContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.04, // 40ms stagger per chip
    },
  },
};

const chipVariant = {
  hidden: { opacity: 0, scale: 0.8, y: 10 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: 0.28, ease: 'easeOut' },
  },
};

export default function SkillChips({ matchedSkills = [], missingSkills = [] }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '1.75rem',
        marginBottom: '2rem',
      }}
    >
      {/* Matched Skills Card */}
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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '10px',
                background: 'rgba(16, 185, 129, 0.16)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--success)',
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy-deep)' }}>
              Matched Skills
            </h3>
          </div>
          <span
            style={{
              background: 'rgba(16, 185, 129, 0.14)',
              color: 'var(--success-dark)',
              fontSize: '0.78rem',
              fontWeight: 700,
              padding: '3px 10px',
              borderRadius: '999px',
            }}
          >
            {matchedSkills.length} Verified
          </span>
        </div>

        {matchedSkills.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
            No direct skill matches detected. Consider tailoring your resume with role keywords.
          </p>
        ) : (
          <motion.div
            variants={chipContainerVariants}
            initial="hidden"
            animate="visible"
            style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}
          >
            {matchedSkills.map((skill) => (
              <motion.span
                key={skill}
                variants={chipVariant}
                style={{
                  background: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  color: '#065f46',
                  fontSize: '0.84rem',
                  fontWeight: 600,
                  padding: '6px 13px',
                  borderRadius: 'var(--radius-full)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>✓</span>
                <span>{formatSkill(skill)}</span>
              </motion.span>
            ))}
          </motion.div>
        )}
      </div>

      {/* Missing Skills Card */}
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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '10px',
                background: 'rgba(239, 68, 68, 0.14)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--danger)',
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy-deep)' }}>
              Missing Skills
            </h3>
          </div>
          <span
            style={{
              background: 'rgba(239, 68, 68, 0.12)',
              color: 'var(--danger)',
              fontSize: '0.78rem',
              fontWeight: 700,
              padding: '3px 10px',
              borderRadius: '999px',
            }}
          >
            {missingSkills.length} Opportunity Gaps
          </span>
        </div>

        {missingSkills.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
            Outstanding! No missing skills detected from the job description.
          </p>
        ) : (
          <motion.div
            variants={chipContainerVariants}
            initial="hidden"
            animate="visible"
            style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}
          >
            {missingSkills.map((skill) => (
              <motion.span
                key={skill}
                variants={chipVariant}
                style={{
                  background: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  color: '#b91c1c',
                  fontSize: '0.84rem',
                  fontWeight: 600,
                  padding: '6px 13px',
                  borderRadius: 'var(--radius-full)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>+</span>
                <span>{formatSkill(skill)}</span>
              </motion.span>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}
