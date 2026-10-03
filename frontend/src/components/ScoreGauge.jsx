import React from 'react';
import { motion } from 'framer-motion';
import { FEATURE_LABELS } from '../utils/format';
import { useCountUp } from '../hooks/useCountUp';


// "Why this score?": the match score is a linear model, so it splits exactly
// into a baseline plus one signed contribution per feature.
function ScoreBreakdown({ breakdown }) {
  const entries = Object.entries(breakdown || {}).filter(([key]) => key !== 'baseline');
  if (entries.length === 0) return null;

  const baseline = breakdown.baseline ?? 0;
  const maxAbs = Math.max(...entries.map(([, v]) => Math.abs(v)), 1);

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-deep)', marginBottom: '0.35rem' }}>
        Why this score?
      </h3>
      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.85rem', lineHeight: 1.5 }}>
        Starts at {baseline.toFixed(0)} (a typical resume–job pair), then each factor adds or removes points.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {entries.map(([key, value]) => {
          const positive = value >= 0;
          return (
            <div key={key}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-body)', fontWeight: 600 }}>{FEATURE_LABELS[key] || key}</span>
                <span style={{ fontWeight: 800, color: positive ? 'var(--success-dark)' : 'var(--danger)' }}>
                  {positive ? '+' : '−'}{Math.abs(value).toFixed(1)} pts
                </span>
              </div>
              <div style={{ height: '6px', background: 'var(--border-light)', borderRadius: '3px', overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(Math.abs(value) / maxAbs) * 100}%` }}
                  transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
                  style={{ height: '100%', borderRadius: '3px', background: positive ? 'var(--success)' : 'var(--danger)' }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ScoreGauge({ result }) {
  const matchScore = result?.match_score ?? 0;
  const animatedScore = useCountUp(matchScore, 1500);

  // Dynamic color configuration
  const getScoreTheme = (score) => {
    if (score < 40) {
      return {
        color: '#EF4444',
        trackColor: 'rgba(239, 68, 68, 0.15)',
        badge: 'Needs Improvement',
        badgeBg: 'rgba(239, 68, 68, 0.12)',
        desc: 'Significant skill and qualification gaps identified for this role.',
      };
    }
    if (score <= 70) {
      return {
        color: '#F59E0B',
        trackColor: 'rgba(245, 158, 11, 0.15)',
        badge: 'Moderate Alignment',
        badgeBg: 'rgba(245, 158, 11, 0.12)',
        desc: 'Core qualifications present with targeted growth opportunities.',
      };
    }
    return {
      color: '#10B981',
      arcColor: '#10B981',
      trackColor: 'rgba(16, 185, 129, 0.15)',
      badge: 'Strong Candidate Match',
      badgeBg: 'rgba(16, 185, 129, 0.12)',
      desc: 'High semantic alignment and strong technical skill coverage.',
    };
  };

  const theme = getScoreTheme(matchScore);

  // SVG Gauge calculations
  const radius = 78;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (matchScore / 100) * circumference;

  const matchedSkills = result?.matched_skills || [];
  const missingSkills = result?.missing_skills || [];

  return (
    <div
      className="hover-lift"
      style={{
        background: 'var(--card-white)',
        borderRadius: 'var(--radius-xl)',
        padding: '2.5rem',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-sm)',
        marginBottom: '2rem',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '2.5rem',
        alignItems: 'center',
      }}
    >
      {/* Circular Score Gauge */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ position: 'relative', width: '200px', height: '200px' }}>
          <svg width="200" height="200" viewBox="0 0 200 200" style={{ transform: 'rotate(-90deg)' }}>
            {/* Background Track Circle */}
            <circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke={theme.trackColor}
              strokeWidth="16"
            />
            {/* Animated Arc Circle */}
            <motion.circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke={theme.arcColor || theme.color}
              strokeWidth="16"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
            />
          </svg>

          {/* Centered Number Display */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'baseline' }}>
              <span
                id="match-score-value"
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '3.2rem',
                  fontWeight: 800,
                  color: 'var(--navy-deep)',
                  lineHeight: 1,
                }}
              >
                {animatedScore.toFixed(0)}
              </span>
              <span style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-muted)' }}>%</span>
            </div>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Match Score
            </span>
          </div>
        </div>
      </div>

      {/* Score Meta Details */}
      <div>
        <div
          style={{
            display: 'inline-block',
            background: theme.badgeBg,
            color: theme.color,
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            fontWeight: 700,
            fontSize: '0.85rem',
            marginBottom: '1rem',
          }}
        >
          {theme.badge}
        </div>

        <h2
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: '1.4rem',
            fontWeight: 700,
            color: 'var(--navy-deep)',
            marginBottom: '0.5rem',
          }}
        >
          Fit Summary
        </h2>

        <p style={{ color: 'var(--text-body)', lineHeight: 1.6, fontSize: '0.96rem', marginBottom: '1.5rem' }}>
          {theme.desc}
        </p>

        {/* Quick Metrics Pill Bar */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ background: 'var(--off-white)', padding: '10px 16px', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
            <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Matched Skills
            </span>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--success)' }}>
              {matchedSkills.length}
            </span>
          </div>

          <div style={{ background: 'var(--off-white)', padding: '10px 16px', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
            <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Missing Skills
            </span>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--danger)' }}>
              {missingSkills.length}
            </span>
          </div>

          <div style={{ background: 'var(--off-white)', padding: '10px 16px', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
            <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Text Match
            </span>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy)' }}>
              {result?.features?.tfidf_similarity !== undefined
                ? `${(result.features.tfidf_similarity * 100).toFixed(1)}%`
                : 'N/A'}
            </span>
          </div>
        </div>

        <ScoreBreakdown breakdown={result?.score_breakdown} />
      </div>
    </div>
  );
}
