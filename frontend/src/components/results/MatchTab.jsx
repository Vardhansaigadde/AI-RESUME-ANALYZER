import { motion } from 'framer-motion';
import { Check, Copy, Lightbulb, Plus, TriangleAlert } from 'lucide-react';
import { useState } from 'react';
import { FEATURE_LABELS, formatRole, formatSkill } from '../../utils/format';
import Button from '../ui/Button';
import JobInsightsCard from './JobInsightsCard';

const reveal = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 260, damping: 24 } },
};

function SectionTitle({ children, aside }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h3 className="font-display text-xl font-semibold">{children}</h3>
      {aside}
    </div>
  );
}

function Breakdown({ breakdown, warnings }) {
  const entries = Object.entries(breakdown || {}).filter(([key]) => key !== 'baseline');
  const maxAbs = Math.max(1, ...entries.map(([, v]) => Math.abs(v)));
  return (
    <motion.section variants={reveal} className="card p-5 sm:p-6">
      <SectionTitle>Why this score?</SectionTitle>
      {warnings?.length > 0 && (
        <div className="mb-4 space-y-2" role="note">
          {warnings.map((w) => (
            <p key={w} className="flex gap-2 rounded-xl bg-warn-soft px-3 py-2 text-sm text-ink">
              <TriangleAlert className="mt-0.5 size-4 shrink-0 text-warn" aria-hidden />
              {w}
            </p>
          ))}
        </div>
      )}
      {entries.length === 0 ? (
        <p className="text-sm text-muted">No breakdown available for this result.</p>
      ) : (
        <>
          <p className="mb-4 text-sm text-muted">
            Starts at <span className="font-mono font-semibold text-ink">{(breakdown.baseline ?? 0).toFixed(0)}</span> (a typical
            resume–job pair), then each factor adds or removes points.
          </p>
          <ul className="space-y-3.5">
            {entries.map(([key, value], i) => {
              const positive = value >= 0;
              return (
                <li key={key}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="font-medium">{FEATURE_LABELS[key] || key}</span>
                    <span className={`font-mono font-bold ${positive ? 'text-ok' : 'text-pen'}`}>
                      {positive ? '+' : '−'}
                      {Math.abs(value).toFixed(1)}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-sunken">
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
        </>
      )}
    </motion.section>
  );
}

/** Matched skill: a highlighter stroke swipes in behind the label. */
function MatchedChip({ skill, index }) {
  return (
    <li className="relative">
      <motion.span
        aria-hidden
        className="absolute inset-0 rounded-md bg-highlight"
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

/** Missing skill: a red-pen wavy underline draws itself in. */
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

function Skills({ matched, missing }) {
  return (
    <motion.section variants={reveal} className="card p-5 sm:p-6">
      <SectionTitle>Skills from the job</SectionTitle>
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <p className="label">You have ({matched.length})</p>
          {matched.length ? (
            <ul className="flex flex-wrap gap-2">
              {matched.map((s, i) => (
                <MatchedChip key={s} skill={s} index={i} />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">None of the job’s listed skills were found in your resume.</p>
          )}
        </div>
        <div>
          <p className="label">Missing ({missing.length})</p>
          {missing.length ? (
            <ul className="flex flex-wrap gap-2">
              {missing.map((s, i) => (
                <MissingChip key={s} skill={s} index={i} />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">Nothing missing. Every skill the job lists is on your resume.</p>
          )}
        </div>
      </div>
    </motion.section>
  );
}

// Suggestions quote canonical lowercase skills ('ci/cd'); display them like the chips
const formatSuggestion = (text) => text.replace(/'([^']+)'/g, (_, skill) => `'${formatSkill(skill)}'`);

function Suggestions({ suggestions }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(suggestions.map((s, i) => `${i + 1}. ${formatSuggestion(s)}`).join('\n'));
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // clipboard blocked: nothing to do
    }
  };
  return (
    <motion.section variants={reveal} className="card p-5 sm:p-6">
      <SectionTitle
        aside={
          suggestions.length > 0 && (
            <Button variant="secondary" size="sm" icon={copied ? Check : Copy} onClick={copy}>
              {copied ? 'Copied' : 'Copy'}
            </Button>
          )
        }
      >
        What to improve
      </SectionTitle>
      {suggestions.length === 0 ? (
        <p className="text-sm text-muted">No suggestions. This resume covers the job well.</p>
      ) : (
        <ol className="space-y-2.5">
          {suggestions.map((s, i) => (
            <motion.li
              key={s}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + i * 0.06 }}
              className="flex gap-3 rounded-xl bg-sunken/60 px-3.5 py-3 text-sm"
            >
              <Lightbulb className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
              <span>{formatSuggestion(s)}</span>
            </motion.li>
          ))}
        </ol>
      )}
    </motion.section>
  );
}

function Roles({ roles, confidence }) {
  return (
    <motion.section variants={reveal} className="card p-5 sm:p-6">
      <SectionTitle>Closest job categories</SectionTitle>
      <p className="-mt-2 mb-4 text-sm text-muted">Based on 2,484 example resumes across 24 industries.</p>
      {confidence === 'low' && (
        <p className="mb-4 flex gap-2 rounded-xl bg-warn-soft px-3 py-2 text-sm">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-warn" aria-hidden />
          No category stands out clearly. Adding more detail to your resume helps.
        </p>
      )}
      <ul className="space-y-3.5">
        {roles.map(({ role, match_percent }, i) => (
          <li key={role}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="font-semibold">
                <span className="mr-2 font-mono text-xs text-muted">#{i + 1}</span>
                {formatRole(role)}
              </span>
              <span className="font-mono font-bold">{match_percent.toFixed(1)}%</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-sunken">
              <motion.div
                className={`h-full rounded-full ${i === 0 ? 'bg-accent' : 'bg-ink/30'}`}
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(match_percent, 100)}%` }}
                transition={{ duration: 1, delay: 0.2 + i * 0.1, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
          </li>
        ))}
      </ul>
    </motion.section>
  );
}

export default function MatchTab({ result }) {
  return (
    <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.07 } } }} className="grid gap-5 lg:grid-cols-2">
      <JobInsightsCard insights={result.job_insights} />
      <Breakdown breakdown={result.score_breakdown} warnings={result.score_warnings} />
      <Skills matched={result.matched_skills} missing={result.missing_skills} />
      <Suggestions suggestions={result.suggestions} />
      <Roles roles={result.suggested_roles} confidence={result.confidence} />
    </motion.div>
  );
}
