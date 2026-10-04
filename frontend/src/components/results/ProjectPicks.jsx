import { AnimatePresence, motion } from 'framer-motion';
import { Check, ChevronDown, Clock, Copy, Hammer } from 'lucide-react';
import { useState } from 'react';
import { formatSkill } from '../../utils/format';

const LEVEL = {
  beginner: 'bg-ok-soft text-ok',
  intermediate: 'bg-accent-soft text-accent',
  advanced: 'bg-pen-soft text-pen',
};

function Chips({ label, skills, className }) {
  if (!skills.length) return null;
  return (
    <p className="flex flex-wrap items-center gap-1.5 text-sm">
      <span className="mr-0.5 text-xs font-semibold text-muted">{label}</span>
      {skills.map((s) => (
        <span key={s} className={`rounded-md px-1.5 py-0.5 font-medium ${className}`}>
          {formatSkill(s)}
        </span>
      ))}
    </p>
  );
}

function ProjectCard({ project, index }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const stepsId = `project-steps-${project.id}`;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(project.bullet);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard blocked: the bullet is still visible to select by hand
    }
  };

  return (
    <motion.li
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 24, delay: index * 0.08 }}
      className="card flex flex-col p-4 sm:p-5"
    >
      <div className="flex items-start gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-highlight/70 dark:bg-highlight/50">
          <Hammer className="size-4.5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <h4 className="font-display text-lg leading-snug font-semibold">{project.title}</h4>
          <p className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-muted">
            <span className={`rounded-full px-2 py-0.5 font-bold ${LEVEL[project.level]}`}>{project.level}</span>
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3" aria-hidden />~{project.hours} h
            </span>
          </p>
        </div>
      </div>

      <p className="mt-3 text-sm text-muted">{project.summary}</p>

      <div className="mt-3 space-y-1.5">
        <Chips label={`Closes ${project.closes.length} ${project.closes.length === 1 ? 'gap' : 'gaps'}`} skills={project.closes} className="bg-highlight/70 dark:bg-highlight/50" />
        <Chips label="Builds on" skills={project.uses} className="bg-sunken" />
        <Chips label="Also learn" skills={project.also_learn} className="bg-sunken text-muted" />
      </div>

      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls={stepsId}
        className="mt-4 flex cursor-pointer items-center gap-1 self-start text-sm font-semibold text-accent"
      >
        How to build it
        <motion.span animate={{ rotate: open ? 180 : 0 }}>
          <ChevronDown className="size-4" aria-hidden />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={stepsId}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <ol className="mt-2 space-y-1.5 text-sm">
              {project.steps.map((step, i) => (
                <li key={step} className="flex gap-2">
                  <span className="grid size-5 shrink-0 place-items-center rounded-full bg-sunken font-mono text-[11px] font-bold text-muted">
                    {i + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mt-auto pt-4">
        <div className="rounded-xl border border-dashed border-line p-3">
          <div className="mb-1 flex items-center justify-between gap-2">
            <span className="text-xs font-semibold text-muted">Resume bullet when it’s done</span>
            <button
              type="button"
              onClick={copy}
              className="inline-flex cursor-pointer items-center gap-1 text-xs font-semibold text-accent"
            >
              {copied ? <Check className="size-3.5" aria-hidden /> : <Copy className="size-3.5" aria-hidden />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p className="text-sm italic">{project.bullet}</p>
          <p className="mt-1 text-xs text-muted">Replace the numbers with your real results.</p>
        </div>
      </div>
    </motion.li>
  );
}

/** One or two portfolio projects that close several skill gaps at once. */
export default function ProjectPicks({ projects }) {
  if (!projects?.length) return null;
  const covered = new Set(projects.flatMap((p) => p.closes)).size;
  return (
    <section className="mb-8">
      <h3 className="font-display text-xl font-semibold">
        {projects.length === 1 ? 'Build this project' : 'Build these projects'}
      </h3>
      <p className="mt-1 mb-4 text-sm text-muted">
        {projects.length === 1 ? 'One project' : `${projects.length} projects`} that cover {covered} of your skill gaps, so
        you learn them by building something you can show, not by watching courses.
      </p>
      <ul className="grid gap-4 md:grid-cols-2">
        {projects.map((project, i) => (
          <ProjectCard key={project.id} project={project} index={i} />
        ))}
      </ul>
    </section>
  );
}
