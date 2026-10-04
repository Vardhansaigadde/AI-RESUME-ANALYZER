import { motion } from 'framer-motion';
import { ArrowUpRight, BadgeCheck, CalendarClock, GraduationCap, Sparkle } from 'lucide-react';
import { formatSkill } from '../../utils/format';

function SkillGroup({ title, skills, covered }) {
  if (!skills.length) return null;
  const have = new Set(covered);
  return (
    <div>
      <p className="label">
        {title} · you have {covered.length}/{skills.length}
      </p>
      <div className="mb-2 h-1.5 overflow-hidden rounded-full bg-sunken">
        <motion.div
          className="h-full rounded-full bg-ok"
          initial={{ width: 0 }}
          animate={{ width: `${(covered.length / skills.length) * 100}%` }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
      <ul className="flex flex-wrap gap-1.5">
        {skills.map((s) => (
          <li
            key={s}
            className={`rounded-lg px-2 py-0.5 text-sm font-medium ${
              have.has(s) ? 'bg-highlight/70 dark:bg-highlight/50' : 'border border-dashed border-pen/50 text-pen'
            }`}
          >
            {formatSkill(s)}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** "This job at a glance": what the posting asks for and how you cover it. */
export default function JobInsightsCard({ insights }) {
  if (!insights) return null;
  const years =
    insights.years_min == null
      ? 'Not stated'
      : insights.years_max != null
        ? `${insights.years_min}–${insights.years_max} years`
        : `${insights.years_min}+ years`;

  const facts = [
    { icon: BadgeCheck, label: 'Level', value: insights.level, good: insights.entry_friendly },
    { icon: CalendarClock, label: 'Experience', value: years },
    { icon: GraduationCap, label: 'Degree', value: insights.degree_mentioned ? 'Mentioned' : 'Not mentioned' },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-5 sm:p-6 lg:col-span-2"
      aria-labelledby="job-glance"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 id="job-glance" className="font-display text-xl font-semibold">
          This job at a glance
        </h3>
        {insights.entry_friendly && (
          <motion.span
            initial={{ scale: 0, rotate: -15 }}
            animate={{ scale: 1, rotate: -3 }}
            transition={{ type: 'spring', stiffness: 400, damping: 12, delay: 0.3 }}
            className="inline-flex items-center gap-1 rounded-full bg-ok-soft px-3 py-1 text-xs font-bold text-ok"
          >
            <Sparkle className="size-3.5" aria-hidden /> Open to students & freshers
          </motion.span>
        )}
      </div>

      <dl className="mt-4 grid gap-3 sm:grid-cols-3">
        {facts.map(({ icon: Icon, label, value, good }) => (
          <div key={label} className="flex items-center gap-3 rounded-xl bg-sunken/60 px-3.5 py-2.5">
            <Icon className={`size-5 ${good ? 'text-ok' : 'text-muted'}`} aria-hidden />
            <div>
              <dt className="text-xs text-muted">{label}</dt>
              <dd className="text-sm font-semibold">{value}</dd>
            </div>
          </div>
        ))}
      </dl>

      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <SkillGroup title="Must-have skills" skills={insights.must_have} covered={insights.must_have_covered} />
        <SkillGroup title="Nice to have" skills={insights.nice_to_have} covered={insights.nice_to_have_covered} />
      </div>
      {insights.also_mentioned.length > 0 && (
        <p className="mt-4 text-sm text-muted">
          Also mentioned: {insights.also_mentioned.map(formatSkill).join(', ')}
        </p>
      )}

      {insights.lead_with.length > 0 && (
        <p className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-xl bg-accent-soft/60 px-3.5 py-2.5 text-sm">
          <ArrowUpRight className="size-4 text-accent" aria-hidden />
          <span className="font-semibold text-accent">Put these first in your Skills section:</span>
          {insights.lead_with.map(formatSkill).join(', ')}
        </p>
      )}
      <p className="mt-3 text-xs text-muted">Read automatically from the posting; unusual layouts can be misread.</p>
    </motion.section>
  );
}
