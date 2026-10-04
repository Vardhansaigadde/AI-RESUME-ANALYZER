import { AnimatePresence, motion } from 'framer-motion';
import { Briefcase, ChevronDown } from 'lucide-react';
import { useId, useState } from 'react';
import { SAMPLE_JOBS } from '../../../lib/sampleJobs';
import Button from '../../ui/Button';
import { reveal } from '../../../lib/motion';

const MIN_WORDS = 5;

/** Resume-only reports: a one-line prompt that expands into a job form. */
export default function AddJobBar({ onSubmit, loading, open, setOpen }) {
  const id = useId();
  const [text, setText] = useState('');
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;

  return (
    <motion.section variants={reveal} id="add-job" className="card overflow-hidden lg:col-span-full">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls={id}
        className="flex w-full cursor-pointer items-center gap-3 p-4 text-left sm:px-6"
      >
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-highlight/70 text-ink dark:bg-highlight/50">
          <Briefcase className="size-4.5" aria-hidden />
        </span>
        <span className="flex-1">
          <span className="block font-semibold">Have a job in mind?</span>
          <span className="block text-sm text-muted">Add the posting for a match score and its missing skills.</span>
        </span>
        <motion.span animate={{ rotate: open ? 180 : 0 }}>
          <ChevronDown className="size-5 text-muted" aria-hidden />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div id={id} initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
            <div className="border-t border-line p-4 sm:px-6">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label htmlFor={`${id}-text`} className="label mb-0">
                  Job description
                </label>
                <select
                  aria-label="Use a sample job"
                  value=""
                  onChange={(e) => setText(SAMPLE_JOBS.find((j) => j.id === e.target.value)?.text || '')}
                  className="cursor-pointer rounded-lg border border-line bg-card px-2 py-1 text-xs text-muted"
                >
                  <option value="">Use a sample…</option>
                  {SAMPLE_JOBS.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title}
                    </option>
                  ))}
                </select>
              </div>
              <textarea
                id={`${id}-text`}
                rows={6}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste the job posting…"
                className="field mt-2 resize-y leading-relaxed"
              />
              <div className="mt-3 flex justify-end">
                <Button loading={loading} disabled={words < MIN_WORDS} onClick={() => onSubmit(text.trim())}>
                  Match with this job
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}
