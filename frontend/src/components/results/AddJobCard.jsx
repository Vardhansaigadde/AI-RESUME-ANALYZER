import { motion } from 'framer-motion';
import { Briefcase, Sparkles } from 'lucide-react';
import { useId, useState } from 'react';
import { SAMPLE_JOBS } from '../../lib/sampleJobs';
import Button from '../ui/Button';

const MIN_WORDS = 5;

/** Shown in resume-only results: paste a job (or pick a sample) to get a match score. */
export default function AddJobCard({ onSubmit, loading }) {
  const id = useId();
  const [text, setText] = useState('');
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card border-dashed p-5 sm:p-6 lg:col-span-2"
      aria-labelledby={`${id}-heading`}
    >
      <div className="flex items-start gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-highlight/70 text-ink">
          <Briefcase className="size-5" aria-hidden />
        </span>
        <div>
          <h3 id={`${id}-heading`} className="font-display text-xl font-semibold">
            Have a job in mind?
          </h3>
          <p className="text-sm text-muted">
            Add a posting to get a match score, the job decoded, missing skills and a learning plan for that job.
          </p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-1.5">
        <span className="mr-1 inline-flex items-center gap-1 text-xs text-muted">
          <Sparkles className="size-3.5" aria-hidden /> Samples:
        </span>
        {SAMPLE_JOBS.map((job) => (
          <button
            key={job.id}
            type="button"
            onClick={() => setText(job.text)}
            className={`cursor-pointer rounded-full border px-2.5 py-1 text-xs font-medium ${
              text === job.text ? 'border-accent bg-accent-soft text-accent' : 'border-line hover:border-ink/40'
            }`}
          >
            {job.title}
          </button>
        ))}
      </div>
      <label htmlFor={id} className="sr-only">
        Job description
      </label>
      <textarea
        id={id}
        rows={5}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste the job posting…"
        className="field mt-3 resize-y leading-relaxed"
      />
      <div className="mt-3 flex justify-end">
        <Button icon={Briefcase} loading={loading} disabled={words < MIN_WORDS} onClick={() => onSubmit(text.trim())}>
          Match with this job
        </Button>
      </div>
    </motion.section>
  );
}
