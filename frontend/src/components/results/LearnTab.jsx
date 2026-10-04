import { motion } from 'framer-motion';
import { BookOpen, Clock, Code2, ExternalLink, FileText, GraduationCap, Hammer, PartyPopper, PlayCircle, Quote } from 'lucide-react';
import { formatSkill } from '../../utils/format';

const KIND = {
  docs: { icon: FileText, label: 'Docs' },
  course: { icon: GraduationCap, label: 'Course' },
  tutorial: { icon: BookOpen, label: 'Tutorial' },
  practice: { icon: Code2, label: 'Practice' },
  book: { icon: BookOpen, label: 'Book' },
  video: { icon: PlayCircle, label: 'Video' },
};

const PRIORITY = {
  'must-have': 'bg-pen-soft text-pen',
  'nice-to-have': 'bg-accent-soft text-accent',
  mentioned: 'bg-sunken text-muted',
};

function PlanCard({ item, index }) {
  return (
    <motion.li
      initial={{ opacity: 0, y: 16, rotate: index % 2 ? 0.6 : -0.6 }}
      animate={{ opacity: 1, y: 0, rotate: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 22, delay: index * 0.06 }}
      whileHover={{ y: -3 }}
      className="card flex flex-col p-5"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs text-muted">{String(index + 1).padStart(2, '0')}</span>
        <h3 className="font-display text-xl font-semibold">{formatSkill(item.skill)}</h3>
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${PRIORITY[item.priority]}`}>{item.priority}</span>
      </div>
      <p className="mt-2 text-sm text-muted">{item.what}</p>

      {item.why && (
        <blockquote className="mt-3 flex gap-2 rounded-xl bg-sunken/60 px-3 py-2 text-sm italic">
          <Quote className="mt-0.5 size-3.5 shrink-0 text-muted" aria-hidden />
          <span>
            <span className="not-italic font-semibold">From the job: </span>
            {item.why}
          </span>
        </blockquote>
      )}

      {item.resources.length > 0 && (
        <ul className="mt-4 space-y-2">
          {item.resources.map((res) => {
            const kind = KIND[res.kind] || KIND.docs;
            const Icon = kind.icon;
            return (
              <li key={res.url}>
                <a
                  href={res.url}
                  target="_blank"
                  rel="noreferrer"
                  className="group flex items-center gap-3 rounded-xl border border-line px-3 py-2 text-sm transition hover:border-accent hover:bg-accent-soft/40"
                >
                  <Icon className="size-4 shrink-0 text-accent" aria-hidden />
                  <span className="flex-1 font-medium">{res.title}</span>
                  {res.time && (
                    <span className="hidden items-center gap-1 text-xs text-muted sm:flex">
                      <Clock className="size-3" aria-hidden />
                      {res.time}
                    </span>
                  )}
                  <span className="text-xs text-muted">{kind.label}</span>
                  <ExternalLink className="size-3.5 text-muted transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden />
                </a>
              </li>
            );
          })}
        </ul>
      )}

      {item.project && (
        <p className="mt-4 flex gap-2 rounded-xl border border-dashed border-ok/50 bg-ok-soft/40 px-3 py-2 text-sm">
          <Hammer className="mt-0.5 size-4 shrink-0 text-ok" aria-hidden />
          <span>
            <span className="font-semibold">Prove it: </span>
            {item.project}
          </span>
        </p>
      )}
    </motion.li>
  );
}

/** Learning plan for the job's missing skills. */
export default function LearnTab({ plan, missingCount }) {
  if (!plan?.length) {
    return (
      <div className="card flex flex-col items-center p-10 text-center">
        <motion.span initial={{ scale: 0, rotate: -20 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: 'spring', stiffness: 300, damping: 12 }}>
          <PartyPopper className="size-10 text-accent" aria-hidden />
        </motion.span>
        <h3 className="mt-4 font-display text-2xl font-semibold">
          {missingCount ? 'No learning plan for these skills yet' : 'No skill gaps to close'}
        </h3>
        <p className="mt-2 max-w-md text-sm text-muted">
          {missingCount
            ? 'The missing skills are specialised ones we don’t have curated resources for. Their official documentation is the best place to start.'
            : 'Your resume already covers every skill the job lists.'}
        </p>
      </div>
    );
  }
  return (
    <div>
      <p className="mb-5 text-sm text-muted">
        Free resources for the skills this job asks for that your resume doesn’t show yet, most important first. Learn
        them, build the small project, then add it to your resume.
      </p>
      <ul className="grid gap-5 lg:grid-cols-2">
        {plan.map((item, i) => (
          <PlanCard key={item.skill} item={item} index={i} />
        ))}
      </ul>
    </div>
  );
}
