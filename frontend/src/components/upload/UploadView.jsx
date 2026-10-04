import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRight, FileText, Gauge, PencilLine, ScanText, Sparkles, Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';
import Button from '../ui/Button';
import Switch from '../ui/Switch';

// Matches MAX_FILE_SIZE in app/services/pipeline.py
const MAX_FILE_BYTES = 5 * 1024 * 1024;
const MIN_JOB_WORDS = 5;

const SAMPLE_JOB = `Junior Software Engineer

We're hiring a junior engineer to build and maintain backend services and internal tools.

Responsibilities
- Build REST APIs in Python and maintain SQL databases
- Containerize services with Docker and deploy them on AWS
- Write tests, review code and use Git in an Agile team

Requirements
- Strong Python and object-oriented programming skills
- Good knowledge of data structures and algorithms
- Experience with SQL and Git; Docker or cloud exposure is a plus
- Clear communication and problem solving`;

const FEATURES = [
  { icon: Gauge, title: 'Match score', text: 'How well you fit this job, and why.' },
  { icon: ScanText, title: 'ATS check', text: 'Will applicant tracking software read it?' },
  { icon: PencilLine, title: 'Edit & export', text: 'Fix it here, download an ATS-friendly .docx.' },
];

const item = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 260, damping: 24 } },
};

export default function UploadView({ file, setFile, jobText, setJobText, studentMode, setStudentMode, onAnalyze, onError }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const words = jobText.trim() ? jobText.trim().split(/\s+/).length : 0;
  const ready = Boolean(file) && words >= MIN_JOB_WORDS;

  const pick = (f) => {
    if (!f) return;
    const name = f.name.toLowerCase();
    if (!name.endsWith('.pdf') && !name.endsWith('.docx')) {
      onError('Please upload a PDF (.pdf) or Word document (.docx).');
    } else if (f.size > MAX_FILE_BYTES) {
      onError(`That file is ${(f.size / 1048576).toFixed(1)} MB. Resumes must be 5 MB or smaller.`);
    } else if (f.size === 0) {
      onError('That file is empty. Please choose another file.');
    } else {
      onError(null);
      setFile(f);
    }
  };

  const clearFile = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <motion.main
      initial="hidden"
      animate="show"
      exit={{ opacity: 0, y: -12 }}
      variants={{ show: { transition: { staggerChildren: 0.08 } } }}
      className="mx-auto w-full max-w-6xl px-4 pt-10 sm:px-6 sm:pt-16"
    >
      <motion.div variants={item} className="mx-auto max-w-3xl text-center">
        <p className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-line bg-card px-3 py-1 text-xs font-semibold text-muted">
          <Sparkles className="size-3.5 text-accent" aria-hidden /> Free · no sign-up · nothing stored
        </p>
        <h1 className="font-display text-4xl leading-[1.08] font-bold tracking-tight sm:text-6xl">
          Will your resume make it <span className="marker">past the bots?</span>
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-base text-muted sm:text-lg">
          Check how well your resume fits a job, whether applicant tracking systems can read it, and fix it on the spot.
        </p>
      </motion.div>

      <motion.ul variants={item} className="mx-auto mt-8 grid max-w-3xl gap-3 sm:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, text }, i) => (
          <motion.li
            key={title}
            whileHover={{ y: -3, rotate: i === 1 ? 0 : i === 0 ? -1 : 1 }}
            className="flex items-start gap-3 rounded-2xl border border-line bg-card/70 p-3.5"
          >
            <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent">
              <Icon className="size-4.5" aria-hidden />
            </span>
            <span>
              <span className="block text-sm font-semibold">{title}</span>
              <span className="block text-xs text-muted">{text}</span>
            </span>
          </motion.li>
        ))}
      </motion.ul>

      <motion.div variants={item} className="mt-10 grid gap-5 lg:grid-cols-2">
        {/* Resume file */}
        <section className="card flex flex-col p-5 sm:p-6" aria-labelledby="resume-heading">
          <div className="mb-4 flex items-baseline justify-between">
            <h2 id="resume-heading" className="font-display text-xl font-semibold">
              <span className="mr-2 font-mono text-sm text-accent">01</span>Your resume
            </h2>
            <span className="text-xs text-muted">PDF or DOCX · max 5 MB</span>
          </div>

          <motion.div
            role="button"
            tabIndex={0}
            aria-label={file ? `Selected file ${file.name}. Press Enter to choose another file.` : 'Choose a resume file'}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), inputRef.current?.click())}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              pick(e.dataTransfer.files?.[0]);
            }}
            animate={{ scale: dragging ? 1.02 : 1, rotate: dragging ? -0.6 : 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className={`relative flex min-h-64 flex-1 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center transition-colors ${
              dragging ? 'border-accent bg-accent-soft' : file ? 'border-ok/50 bg-ok-soft/40' : 'border-line bg-sunken/50 hover:border-ink/30'
            }`}
          >
            <input
              ref={inputRef}
              id="resume-file-input"
              type="file"
              className="hidden"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(e) => pick(e.target.files?.[0])}
            />
            <AnimatePresence mode="wait">
              {file ? (
                <motion.div
                  key="file"
                  initial={{ y: -30, opacity: 0, rotate: -6 }}
                  animate={{ y: 0, opacity: 1, rotate: -2 }}
                  exit={{ y: 20, opacity: 0 }}
                  transition={{ type: 'spring', stiffness: 320, damping: 18 }}
                  className="relative w-full max-w-xs rounded-xl border border-line bg-card p-4 text-left shadow-[var(--shadow-lift)]"
                >
                  <div className="flex items-center gap-3">
                    <span className="grid size-10 place-items-center rounded-lg bg-ok-soft text-ok">
                      <FileText className="size-5" aria-hidden />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold">{file.name}</p>
                      <p className="text-xs text-muted">{(file.size / 1024).toFixed(0)} KB · ready</p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        clearFile();
                      }}
                      className="cursor-pointer rounded-md p-1 text-muted hover:bg-pen-soft hover:text-pen"
                      aria-label="Remove file"
                    >
                      <X className="size-4" />
                    </button>
                  </div>
                  <div className="mt-3 space-y-1.5" aria-hidden>
                    {[90, 70, 82].map((w) => (
                      <div key={w} className="h-1.5 rounded-full bg-sunken" style={{ width: `${w}%` }} />
                    ))}
                  </div>
                </motion.div>
              ) : (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <motion.span
                    animate={{ y: [0, -6, 0] }}
                    transition={{ duration: 2.6, repeat: Infinity, ease: 'easeInOut' }}
                    className="mx-auto mb-4 grid size-14 place-items-center rounded-2xl bg-card text-ink shadow-[var(--shadow-paper)]"
                  >
                    <Upload className="size-6" aria-hidden />
                  </motion.span>
                  <p className="font-semibold">{dragging ? 'Drop it like it’s hot' : 'Drag & drop your resume'}</p>
                  <p className="mt-1 text-sm text-muted">
                    or <span className="font-semibold text-accent underline underline-offset-4">browse files</span>
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </section>

        {/* Job description */}
        <section className="card flex flex-col p-5 sm:p-6" aria-labelledby="job-heading">
          <div className="mb-4 flex items-baseline justify-between gap-2">
            <h2 id="job-heading" className="font-display text-xl font-semibold">
              <span className="mr-2 font-mono text-sm text-accent">02</span>Target job
            </h2>
            <Button variant="ghost" size="sm" icon={Sparkles} onClick={() => setJobText(SAMPLE_JOB)}>
              Use a sample
            </Button>
          </div>
          <label htmlFor="job-description-input" className="sr-only">
            Job description
          </label>
          <textarea
            id="job-description-input"
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste the full job posting: responsibilities, requirements, skills…"
            className="field min-h-64 flex-1 resize-y leading-relaxed"
          />
          <p className={`mt-2 text-right font-mono text-xs ${words >= 50 ? 'text-ok' : 'text-muted'}`}>
            {words} words{words > 0 && words < 50 ? ' · paste the full posting for a reliable score' : ''}
          </p>
        </section>
      </motion.div>

      <motion.div variants={item} className="mt-8 flex flex-col items-center gap-5">
        <div className="card px-5 py-4">
          <Switch
            checked={studentMode}
            onChange={setStudentMode}
            label="I'm a student / fresher"
            description="Adds a student checklist: projects, internships, CGPA, GitHub, one page."
          />
        </div>
        <Button id="analyze-fit-button" size="lg" icon={ArrowRight} disabled={!ready} onClick={onAnalyze}>
          Analyze my resume
        </Button>
        {!ready && (
          <p className="text-sm text-muted">
            {!file && words < MIN_JOB_WORDS
              ? 'Add your resume and paste a job description to start.'
              : !file
                ? 'Add your resume to start.'
                : 'Paste a job description to start.'}
          </p>
        )}
      </motion.div>
    </motion.main>
  );
}
