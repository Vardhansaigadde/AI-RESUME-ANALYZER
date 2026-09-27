import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';

const SAMPLE_JOB = `Senior Software Engineer
We are seeking an experienced developer with strong skills in Python, SQL, Docker, and RESTful API design. 
Experience with cloud platforms (AWS or GCP), microservices architecture, and modern CI/CD practices is highly preferred. 
Key responsibilities include collaborating with product managers, leading technical architecture discussions, 
and mentoring junior engineers. Strong problem solving and communication skills required.`;

export default function UploadView({ file, setFile, jobText, setJobText, onAnalyze }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  // Compute word and character counts
  const trimmed = jobText.trim();
  const wordCount = trimmed ? trimmed.split(/\s+/).length : 0;
  const charCount = jobText.length;
  const isValid = Boolean(file && wordCount >= 5);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (f) => {
    const ext = f.name.toLowerCase();
    if (!ext.endsWith('.pdf') && !ext.endsWith('.docx')) {
      alert('Please upload a PDF (.pdf) or Word document (.docx).');
      return;
    }
    setFile(f);
  };

  const removeFile = (e) => {
    e.stopPropagation();
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Staggered animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.12,
        delayChildren: 0.05,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 22, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] },
    },
  };

  return (
    <motion.main
      className="upload-view-container"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      exit={{ opacity: 0, y: -20, transition: { duration: 0.25 } }}
      style={{
        position: 'relative',
        zIndex: 1,
        maxWidth: '1180px',
        width: '100%',
        margin: '0 auto',
        padding: '1.5rem 1.5rem 3rem 1.5rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {/* 1. Header / Hero section */}
      <motion.div variants={itemVariants} style={{ textAlign: 'center', maxWidth: '780px', marginBottom: '2.5rem' }}>
        <h1
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: 'clamp(2.1rem, 4.5vw, 3.2rem)',
            fontWeight: 800,
            lineHeight: 1.15,
            letterSpacing: '-0.03em',
            color: '#FFFFFF',
            marginBottom: '1rem',
          }}
        >
          Analyze Resume & Job Fit with <span style={{ color: 'var(--brand-teal-light)' }}>Precision</span>
        </h1>

        <p
          style={{
            fontSize: 'clamp(0.98rem, 1.8vw, 1.15rem)',
            color: 'var(--text-light-muted)',
            lineHeight: 1.6,
            maxWidth: '680px',
            margin: '0 auto',
          }}
        >
          See how well your resume matches a job — and what to fix before you apply.
        </p>
      </motion.div>

      {/* 2. Main Upload & Input Grid */}
      <motion.div
        variants={itemVariants}
        style={{
          width: '100%',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.75rem',
          marginBottom: '2rem',
        }}
      >
        {/* LEFT COLUMN: Resume Dropzone */}
        <div
          style={{
            background: 'var(--navy-card)',
            backdropFilter: 'blur(16px)',
            border: '1px solid var(--navy-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.75rem',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '8px',
                  background: 'var(--brand-teal-bg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--brand-teal-light)',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                }}
              >
                1
              </div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#FFFFFF' }}>Your Resume</h2>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-light-muted)' }}>PDF or DOCX</span>
          </div>

          <motion.div
            id="resume-dropzone"
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            animate={{
              scale: isDragging ? 1.02 : 1,
              borderColor: isDragging ? 'var(--brand-teal-light)' : file ? 'var(--success)' : 'rgba(13, 148, 136, 0.3)',
              backgroundColor: isDragging
                ? 'var(--brand-teal-bg)'
                : file
                ? 'rgba(16, 185, 129, 0.05)'
                : 'rgba(21, 27, 65, 0.45)',
            }}
            transition={{ duration: 0.2 }}
            style={{
              flex: 1,
              minHeight: '260px',
              borderWidth: '2px',
              borderStyle: 'dashed',
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem 1.5rem',
              textAlign: 'center',
              cursor: 'pointer',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              id="resume-file-input"
            />

            {!file ? (
              <>
                <motion.div
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                  style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '20px',
                    background: 'var(--brand-teal-bg)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '1rem',
                    color: 'var(--brand-teal-light)',
                  }}
                >
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                </motion.div>
                <p style={{ fontWeight: 600, fontSize: '1.05rem', color: '#FFFFFF', marginBottom: '0.4rem' }}>
                  {isDragging ? 'Drop resume here...' : 'Drag and drop your resume'}
                </p>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-light-muted)', marginBottom: '1.25rem' }}>
                  Supports PDF or DOCX up to 5MB
                </p>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '8px 18px',
                    background: 'rgba(255, 255, 255, 0.08)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    color: '#FFFFFF',
                    transition: 'background 0.2s',
                  }}
                >
                  Browse Files
                </span>
              </>
            ) : (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', damping: 20 }}
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}
              >
                {/* Checkmark animation container */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 18 }}
                  style={{
                    width: '68px',
                    height: '68px',
                    borderRadius: '50%',
                    background: 'var(--success-bg)',
                    border: '2px solid var(--success)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '1rem',
                    color: 'var(--success)',
                    boxShadow: '0 0 24px rgba(16, 185, 129, 0.4)',
                  }}
                >
                  <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </motion.div>

                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.07)',
                    padding: '8px 16px',
                    borderRadius: '12px',
                    maxWidth: '100%',
                    marginBottom: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                  }}
                >
                  <span style={{ fontSize: '1.2rem' }}>📄</span>
                  <div style={{ textAlign: 'left', overflow: 'hidden' }}>
                    <p style={{ fontWeight: 600, fontSize: '0.92rem', color: '#FFFFFF', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '220px' }}>
                      {file.name}
                    </p>
                    <span style={{ fontSize: '0.75rem', color: 'var(--success)' }}>
                      {(file.size / 1024).toFixed(1)} KB • Ready for analysis
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current && fileInputRef.current.click()}
                    style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '8px',
                      color: '#FFFFFF',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      padding: '5px 12px',
                      cursor: 'pointer',
                    }}
                  >
                    Change File
                  </button>
                  <button
                    type="button"
                    onClick={removeFile}
                    style={{
                      background: 'var(--danger-bg)',
                      border: '1px solid var(--danger-border)',
                      borderRadius: '8px',
                      color: 'var(--danger)',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      padding: '5px 12px',
                      cursor: 'pointer',
                    }}
                  >
                    Remove
                  </button>
                </div>
              </motion.div>
            )}
          </motion.div>
        </div>

        {/* RIGHT COLUMN: Job Description */}
        <div
          style={{
            background: 'var(--navy-card)',
            backdropFilter: 'blur(16px)',
            border: '1px solid var(--navy-border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.75rem',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '8px',
                  background: 'var(--brand-teal-bg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--brand-teal-light)',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                }}
              >
                2
              </div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#FFFFFF' }}>Target Job Description</h2>
            </div>
            <button
              type="button"
              onClick={() => setJobText(SAMPLE_JOB)}
              style={{
                background: 'var(--brand-teal-bg)',
                border: '1px solid var(--brand-teal-border)',
                color: 'var(--brand-teal-light)',
                fontSize: '0.75rem',
                fontWeight: 600,
                padding: '4px 10px',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              title="Quick test with a sample Software Engineer job posting"
            >
              Fill Sample Job
            </button>
          </div>

          <div style={{ position: 'relative', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <textarea
              id="job-description-input"
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              placeholder="Paste the target job description here (requirements, responsibilities, skills)..."
              style={{
                width: '100%',
                flex: 1,
                minHeight: '260px',
                background: 'rgba(21, 27, 65, 0.45)',
                border: '1px solid rgba(13, 148, 136, 0.25)',
                borderRadius: 'var(--radius-lg)',
                padding: '1.1rem 1.1rem 2.8rem 1.1rem',
                color: '#FFFFFF',
                fontFamily: 'var(--font-body)',
                fontSize: '0.92rem',
                lineHeight: 1.6,
                resize: 'none',
                outline: 'none',
                transition: 'border-color 0.2s, box-shadow 0.2s',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = 'var(--brand-teal-light)';
                e.target.style.boxShadow = '0 0 16px rgba(13, 148, 136, 0.25)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = 'rgba(13, 148, 136, 0.25)';
                e.target.style.boxShadow = 'none';
              }}
            />

            {/* Live Counter Badge */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{
                position: 'absolute',
                bottom: '12px',
                right: '12px',
                background: 'rgba(15, 23, 42, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(8px)',
                padding: '4px 10px',
                borderRadius: '8px',
                fontSize: '0.74rem',
                fontWeight: 600,
                color: wordCount >= 5 ? 'var(--brand-teal-light)' : 'var(--text-light-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span>{wordCount} words</span>
              <span style={{ opacity: 0.4 }}>•</span>
              <span>{charCount} chars</span>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* 3. Action Section */}
      <motion.div variants={itemVariants} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <button
          id="analyze-fit-button"
          onClick={onAnalyze}
          disabled={!isValid}
          className={isValid ? 'analyze-button-enabled' : ''}
          style={{
            position: 'relative',
            padding: '16px 44px',
            fontSize: '1.1rem',
            fontWeight: 700,
            fontFamily: 'var(--font-heading)',
            letterSpacing: '-0.01em',
            borderRadius: 'var(--radius-full)',
            border: 'none',
            cursor: isValid ? 'pointer' : 'not-allowed',
            background: isValid
              ? 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)'
              : 'rgba(255, 255, 255, 0.12)',
            color: isValid ? '#FFFFFF' : 'rgba(255, 255, 255, 0.35)',
            transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <span>Analyze My Fit</span>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </button>

        {!isValid && (
          <p style={{ marginTop: '0.75rem', fontSize: '0.82rem', color: 'var(--text-light-muted)', opacity: 0.8 }}>
            {!file && wordCount < 5
              ? 'Upload your resume and enter a job description to begin.'
              : !file
              ? 'Please upload your resume (.pdf or .docx).'
              : 'Please enter a job description (at least 5 words).'}
          </p>
        )}
      </motion.div>
    </motion.main>
  );
}
