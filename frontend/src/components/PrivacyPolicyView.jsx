import React from 'react';
import { motion } from 'framer-motion';

export default function PrivacyPolicyView({ onHome }) {
  return (
    <motion.main
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: 'relative',
        zIndex: 1,
        maxWidth: '820px',
        width: '92%',
        margin: '3rem auto 4rem auto',
        padding: '3rem 2.5rem',
        background: 'var(--navy-card)',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--navy-border)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: '0 25px 60px rgba(10, 14, 38, 0.5)',
        color: 'var(--text-primary)',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header Bar with Back Button */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '2rem',
          borderBottom: '1px solid var(--navy-border)',
          paddingBottom: '1.25rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <span
            style={{
              display: 'inline-block',
              background: 'var(--brand-teal-bg)',
              color: 'var(--brand-teal-light)',
              border: '1px solid var(--brand-teal-border)',
              padding: '3px 12px',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.78rem',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              marginBottom: '0.5rem',
            }}
          >
            Legal & Privacy
          </span>
          <h1
            style={{
              fontSize: '2rem',
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              margin: 0,
            }}
          >
            Privacy Policy
          </h1>
        </div>

        <button
          id="privacy-back-home-btn"
          onClick={onHome}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--navy-elevated)',
            color: 'var(--brand-teal-light)',
            border: '1px solid var(--navy-border)',
            padding: '8px 16px',
            borderRadius: 'var(--radius-md)',
            fontWeight: 600,
            fontSize: '0.88rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--brand-teal)';
            e.currentTarget.style.background = 'var(--navy-hover)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--navy-border)';
            e.currentTarget.style.background = 'var(--navy-elevated)';
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          Back to Home
        </button>
      </div>

      <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '2.5rem' }}>
        Effective Date: September 2026 • FitLens Application
      </p>

      {/* Section 1: Data We Collect */}
      <section style={{ marginBottom: '2.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>1.</span> Information You Provide
        </h2>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: '0 0 0.75rem 0' }}>
          When you use FitLens to evaluate how well your resume matches a target job posting, we collect only the information you explicitly provide:
        </p>
        <ul style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.95rem', paddingLeft: '1.5rem', margin: 0 }}>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>Uploaded Resume Content:</strong> Text and structured information extracted from PDF or DOCX files you choose to upload.
          </li>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>Job Description Text:</strong> The job posting or role requirements text you submit for comparison.
          </li>
        </ul>
      </section>

      {/* Section 2: In-Memory Processing & Zero Persistence */}
      <section style={{ marginBottom: '2.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>2.</span> How Data Is Handled: 100% In-Memory Processing
        </h2>
        <div
          style={{
            background: 'rgba(13, 148, 136, 0.08)',
            border: '1px solid var(--brand-teal-border)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem 1.5rem',
            marginBottom: '1rem',
          }}
        >
          <p style={{ color: 'var(--brand-teal-light)', fontWeight: 600, fontSize: '0.95rem', margin: '0 0 0.5rem 0' }}>
            🔒 Zero Disk Persistence Guarantee
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6, margin: 0 }}>
            FitLens handles all resume files and job descriptions exclusively in volatile system memory (RAM). We do not write uploaded files to disk, do not create temporary filesystem files, and maintain no persistent database of user resumes.
          </p>
        </div>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: '0 0 0.75rem 0' }}>
          Specifically:
        </p>
        <ul style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.95rem', paddingLeft: '1.5rem', margin: 0 }}>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>Immediate Lifecycle Discard:</strong> File bytes and parsed text are extracted in-memory, analyzed by our scoring pipeline, and immediately discarded and garbage-collected once your analysis response is sent.
          </li>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>No Server Log Exposure:</strong> Resume body text, extracted candidate names, and personal credentials are never written to application logs. Server logs record only standard operational status and non-sensitive metadata (such as file extension and HTTP status codes).
          </li>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>No Account or History Tracking:</strong> We do not require accounts or store past analysis results on our servers.
          </li>
        </ul>
      </section>

      {/* Section 3: Machine Learning Model Transparency */}
      <section style={{ marginBottom: '2.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>3.</span> Machine Learning & Training Data
        </h2>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: '0 0 0.75rem 0' }}>
          Our resume scoring and role prediction models (Ridge regression match scorer and LinearSVC role predictor) were trained exclusively on independent, third-party benchmark datasets prior to application deployment.
        </p>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: 0 }}>
          <strong style={{ color: 'var(--text-primary)' }}>Your data is never used to train or refine our models.</strong> Uploaded resumes and job postings are strictly utilized for real-time inference during your active session.
        </p>
      </section>

      {/* Section 4: No Third-Party Sharing or Sale */}
      <section style={{ marginBottom: '2.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>4.</span> Third-Party Disclosure & Selling
        </h2>
        <ul style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.95rem', paddingLeft: '1.5rem', margin: 0 }}>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>We do not sell your data:</strong> FitLens does not sell, rent, license, or monetize your resume, job postings, or personal information under any circumstances.
          </li>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>No Third-Party AI API Routing:</strong> All parsing, skill extraction, and machine learning models execute locally on our application server. Your resume content is never sent to external AI providers or third-party cloud analytics services.
          </li>
        </ul>
      </section>

      {/* Section 5: Contact Info */}
      <section style={{ borderTop: '1px solid var(--navy-border)', paddingTop: '1.75rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>5.</span> Contact Us
        </h2>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: '0 0 1rem 0' }}>
          If you have any questions, concerns, or requests regarding this Privacy Policy or our in-memory data handling practices, please contact us at:
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--brand-teal-light)', fontWeight: 600, fontSize: '0.95rem' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
          <a href="mailto:privacy@fitlens.ai" style={{ color: 'var(--brand-teal-light)', textDecoration: 'none' }}>
            privacy@fitlens.ai
          </a>
        </div>
      </section>

      {/* Bottom Home Button */}
      <div style={{ marginTop: '2.5rem', textAlign: 'center' }}>
        <button
          onClick={onHome}
          style={{
            background: 'var(--brand-teal)',
            color: '#FFFFFF',
            fontWeight: 600,
            fontSize: '0.95rem',
            padding: '10px 24px',
            borderRadius: 'var(--radius-md)',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 4px 14px var(--brand-teal-glow)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--brand-teal-hover)';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--brand-teal)';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          Return to Analyzer
        </button>
      </div>
    </motion.main>
  );
}
