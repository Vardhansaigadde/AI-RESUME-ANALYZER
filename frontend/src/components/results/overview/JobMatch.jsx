import { motion } from 'framer-motion';
import { ArrowUpRight, Check, Plus, Sparkle, TriangleAlert } from 'lucide-react';
import { FEATURE_LABELS, formatSkill } from '../../../utils/format';
import Panel from './Panel';

/** Skill the resume has: a highlighter stroke swipes in behind it. */
function HaveChip({ skill, index }) {
  return (
    <li className="relative">
      <motion.span
        aria-hidden
        className="absolute inset-0 rounded-md bg-highlight/80 dark:bg-highlight/60"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        style={{ originX: 0 }}
        transition={{ duration: 0.35, delay: 0.2 + index * 0.05, ease: 'easeOut' }}
      />
      <span className="relative flex items-center gap-1 px-2 py-1 text-sm font-semibold whitespace-nowrap">
        <Check className="size-3.5" aria-hidden />
        {formatSkill(skill)}
      </span>
    </li>
  );
}

/** Skill the resume lacks: a red-pen wavy underline draws itself in. */
function MissingChip({ skill, index }) {
  return (
    <li className="relative px-2 py-1 text-sm font-semibold whitespace-nowrap">
      <span className="flex items-center gap-1">
        <Plus className="size-3.5 text-pen" aria-hidden />
        {formatSkill(skill)}
      </span>
      <svg className="absolute -bottom-0.5 left-1 h-2 w-[calc(100%-0.5rem)] text-pen" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden>
        <motion.path
          d="M0 4 Q 6 0 12 4 T 24 4 T 36 4 T 48 4 T 60 4 T 72 4 T 84 4 T 96 4 T 108 4"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.5, delay: 0.3 + index * 0.05 }}
        />
      </svg>
    </li>
  );
}

function SkillList({ title, skills, covered }) {
  if (!skills.length) return null;
  const have = skills.filter((s) => covered.includes(s));
  const missing = skills.filter((s) => !covered.includes(s));
  return (
    <div>
      <p className="label">
        {title} · {have.length}/{skills.length}
      </p>
      <ul className="flex flex-wrap gap-x-1.5 gap-y-2" aria-label={title}>
        {have.map((s, i) => (
          <HaveChip key={s} skill={s} index={i} />
        ))}
        {missing.map((s, i) => (
          <MissingChip key={s} skill={s} index={have.length + i} />
        ))}
      </ul>
    </div>
  );
}

/** The posting at a glance: level, experience, and which skills you have / lack. */
export function JobSummary({ insights, matched, missing }) {
  if (!insights) return null;
  const years =
    insights.years_min == null
      ? null
      : insights.years_max != null
        ? `${insights.years_min}–${insights.years_max} years`
        : `${insights.years_min}+ years`;
  const meta = [insights.level !== 'Not stated' && insights.level, years, insights.degree_mentioned && 'Degree mentioned'].filter(Boolean);
  // Postings with no clear requirement sections still have skills: fall back to matched / missing
  const hasSections = insights.must_have.length + insights.nice_to_have.length > 0;

  return (
    <Panel
      title="The job"
      subtitle={meta.join(' · ') || 'Level and experience not stated'}
      className="lg:col-span-3"
      aside={
        insights.entry_friendly && (
          <motion.span
            initial={{ scale: 0, rotate: -15 }}
            animate={{ scale: 1, rotate: -3 }}
            transition={{ type: 'spring', stiffness: 400, damping: 12, delay: 0.3 }}
            className="inline-flex shrink-0 items-center gap-1 rounded-full bg-ok-soft px-3 py-1 text-xs font-bold text-ok"
          >
            <Sparkle className="size-3.5" aria-hidden /> Student-friendly
          </motion.span>
        )
      }
    >
      <div className="space-y-5">
        {hasSections ? (
          <>
            <SkillList title="Must-have" skills={insights.must_have} covered={insights.must_have_covered} />
            <SkillList title="Nice to have" skills={insights.nice_to_have} covered={insights.nice_to_have_covered} />
          </>
        ) : (
          <SkillList title="Skills in the posting" skills={[...matched, ...missing]} covered={matched} />
        )}
      </div>
      {insights.also_mentioned.length > 0 && (
        <p className="mt-4 text-xs text-muted">Also mentioned: {insights.also_mentioned.map(formatSkill).join(', ')}</p>
      )}
      {insights.lead_with.length > 0 && (
        <p className="mt-4 flex gap-2 border-t border-line pt-4 text-sm">
          <ArrowUpRight className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
          <span>
            <span className="font-semibold">List these first in your Skills section:</span>{' '}
            {insights.lead_with.map(formatSkill).join(', ')}
          </span>
        </p>
      )}
    </Panel>
  );
}

/** How the match score was built: baseline plus each factor's points. */
export function ScoreBreakdown({ breakdown, warnings }) {
  const entries = Object.entries(breakdown || {}).filter(([key]) => key !== 'baseline');
  const maxAbs = Math.max(1, ...entries.map(([, v]) => Math.abs(v)));
  return (
    <Panel
      title="Why this score"
      subtitle={entries.length ? `Starts at ${(breakdown.baseline ?? 0).toFixed(0)} for a typical pair, then:` : undefined}
      className="lg:col-span-2"
    >
      {warnings?.length > 0 && (
        <div className="mb-4 space-y-2" role="note">
          {warnings.map((w) => (
            <p key={w} className="flex gap-2 rounded-xl bg-warn-soft px-3 py-2 text-xs">
              <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-warn" aria-hidden />
              {w}
            </p>
          ))}
        </div>
      )}
      <ul className="space-y-3.5">
        {entries.map(([key, value], i) => {
          const positive = value >= 0;
          return (
            <li key={key}>
              <div className="mb-1 flex justify-between gap-3 text-sm">
                <span>{FEATURE_LABELS[key] || key}</span>
                <span className={`font-mono font-bold ${positive ? 'text-ok' : 'text-pen'}`}>
                  {positive ? '+' : '−'}
                  {Math.abs(value).toFixed(1)}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-sunken">
                <motion.div
                  className={`h-full rounded-full ${positive ? 'bg-ok' : 'bg-pen'}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${(Math.abs(value) / maxAbs) * 100}%` }}
                  transition={{ duration: 0.9, delay: 0.15 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}
