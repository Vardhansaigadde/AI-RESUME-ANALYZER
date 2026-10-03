import React from 'react';
import { motion } from 'framer-motion';
import { useCountUp } from '../hooks/useCountUp';
import { formatRole } from '../utils/format';

// Subcomponent for individual animated role progress bar
function RoleBarItem({ role, percent, rank }) {
  const animatedPercent = useCountUp(percent, 1200);

  const getBarColor = (r) => {
    if (r === 1) return 'linear-gradient(90deg, #0d9488, #14b8a6)';
    if (r === 2) return 'linear-gradient(90deg, #1b2340, #0d9488)';
    return 'linear-gradient(90deg, #64748b, #94a3b8)';
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 800,
              color: rank === 1 ? 'var(--brand-teal)' : 'var(--text-muted)',
              background: rank === 1 ? 'var(--brand-teal-bg)' : 'var(--off-white)',
              padding: '2px 6px',
              borderRadius: '6px',
            }}
          >
            #{rank}
          </span>
          <span style={{ fontWeight: 700, fontSize: '0.94rem', color: 'var(--navy-deep)' }}>
            {formatRole(role)}
          </span>
        </div>
        <span style={{ fontWeight: 800, fontSize: '0.94rem', color: rank === 1 ? 'var(--brand-teal)' : 'var(--text-body)' }}>
          {animatedPercent.toFixed(1)}%
        </span>
      </div>

      <div
        style={{
          width: '100%',
          height: '10px',
          background: 'var(--border-light)',
          borderRadius: '5px',
          overflow: 'hidden',
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(percent, 100)}%` }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          style={{
            height: '100%',
            background: getBarColor(rank),
            borderRadius: '5px',
          }}
        />
      </div>
    </div>
  );
}

export default function RoleBarChart({ suggestedRoles = [], confidence = 'high' }) {
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.25rem' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '10px',
            background: 'rgba(245, 158, 11, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--amber)',
          }}
        >
          🎯
        </div>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy-deep)' }}>
          Top Role Matches
        </h3>
      </div>

      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
        Job categories your resume most resembles, based on 2,484 example resumes.
      </p>

      {confidence === 'low' && (
        <div
          style={{
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.84rem',
            color: '#b45309',
            fontWeight: 600,
          }}
        >
          <span>⚠️</span>
          <span>Role suggestions are less certain — try adding more detail to your resume.</span>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {suggestedRoles.map((roleObj, idx) => (
          <RoleBarItem
            key={roleObj.role}
            role={roleObj.role}
            percent={roleObj.match_percent}
            rank={idx + 1}
          />
        ))}
      </div>
    </div>
  );
}
