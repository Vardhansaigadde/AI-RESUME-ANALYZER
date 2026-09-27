import React from 'react';
import { motion } from 'framer-motion';

export default function TermsOfUseView({ onHome }) {
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
            Terms & Conditions
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
            Terms of Use
          </h1>
        </div>

        <button
          id="terms-back-home-btn"
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

      {/* Section 1: Informational & Self-Assessment Purposes */}
      <section style={{ marginBottom: '2.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>1.</span> Informational & Educational Service Only
        </h2>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: '0 0 0.75rem 0' }}>
          FitLens is an AI-powered resume and job description analysis tool designed strictly for candidate informational, self-assessment, and educational preparation purposes.
        </p>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: 0 }}>
          All match scores, skill comparisons, suggested additions, and role recommendations are algorithmically generated predictions produced by local machine learning models and heuristic parsing. They do not constitute professional career counseling, recruitment decisions, or hiring advice.
        </p>
      </section>

      {/* Section 2: No Guarantee of Job Outcomes */}
      <section style={{ marginBottom: '2.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>2.</span> No Guarantee of Job Outcomes
        </h2>
        <div
          style={{
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem 1.5rem',
            marginBottom: '1rem',
          }}
        >
          <p style={{ color: '#FBBF24', fontWeight: 600, fontSize: '0.95rem', margin: '0 0 0.5rem 0' }}>
            ⚠️ Important Disclaimer on Hiring Outcomes
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6, margin: 0 }}>
            FitLens makes no warranties, express or implied, that a high match score or implementing suggestions will result in an interview invitation, job offer, employment, or career milestone.
          </p>
        </div>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: 0 }}>
          Hiring decisions involve numerous human, cultural, technical, and organizational considerations beyond automated keyword matching and semantic analysis. You are solely responsible for verifying the accuracy and truthfulness of any information on your resume before submitting it to employers.
        </p>
      </section>

      {/* Section 3: Ownership of Resume Content */}
      <section style={{ marginBottom: '2.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>3.</span> User Ownership & Content Rights
        </h2>
        <ul style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.95rem', paddingLeft: '1.5rem', margin: 0 }}>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>You Retain All Rights:</strong> You maintain full ownership, copyright, and intellectual property rights in your resume documents, text, personal details, and work history.
          </li>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>Limited Processing License:</strong> By uploading your document, you grant FitLens only the limited, temporary license to read and parse the file in volatile memory strictly to generate your match analysis. No transfer of ownership occurs.
          </li>
        </ul>
      </section>

      {/* Section 4: Service Provided "As-Is" */}
      <section style={{ marginBottom: '2.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>4.</span> "As-Is" Disclaimer & Limitation of Liability
        </h2>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: '0 0 0.75rem 0' }}>
          FitLens is provided on an <strong>"AS-IS"</strong> and <strong>"AS-AVAILABLE"</strong> basis without warranties of any kind, whether express, implied, statutory, or otherwise, including but not limited to warranties of merchantability, fitness for a particular purpose, or non-infringement.
        </p>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: 0 }}>
          To the maximum extent permitted by law, FitLens, its creators, and affiliates shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising out of or related to your use of the service.
        </p>
      </section>

      {/* Section 5: Contact Info */}
      <section style={{ borderTop: '1px solid var(--navy-border)', paddingTop: '1.75rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--brand-teal)' }}>5.</span> Contact Us
        </h2>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.95rem', margin: '0 0 1rem 0' }}>
          For inquiries or legal notices concerning these Terms of Use, please reach out to:
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--brand-teal-light)', fontWeight: 600, fontSize: '0.95rem' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
          <a href="mailto:legal@fitlens.ai" style={{ color: 'var(--brand-teal-light)', textDecoration: 'none' }}>
            legal@fitlens.ai
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
