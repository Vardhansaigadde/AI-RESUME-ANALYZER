import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, CircleCheck, CircleMinus, CircleX, Info, PencilLine, TriangleAlert } from 'lucide-react';
import { useState } from 'react';
import { formatSkill } from '../../utils/format';
import Button from '../ui/Button';

const STATUS = {
  fail: { icon: CircleX, color: 'text-pen', bg: 'bg-pen-soft', label: 'Fix' },
  warn: { icon: TriangleAlert, color: 'text-warn', bg: 'bg-warn-soft', label: 'Improve' },
  pass: { icon: CircleCheck, color: 'text-ok', bg: 'bg-ok-soft', label: 'Good' },
  skip: { icon: CircleMinus, color: 'text-muted', bg: 'bg-sunken', label: 'Not checked' },
};
const CATEGORY = { format: 'Format & layout', content: 'Content', keywords: 'Job keywords', student: 'Student checklist' };
const ORDER = { fail: 0, warn: 1, pass: 2, skip: 3 };

// "…from the posting: aws, ci/cd." -> "…from the posting: AWS, CI/CD."
const formatSkillList = (tip) =>
  tip.replace(/: (.+)\.$/, (_, list) => `: ${list.split(', ').map(formatSkill).join(', ')}.`);

function CheckRow({ check, index }) {
  const s = STATUS[check.status];
  const Icon = s.icon;
  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="flex gap-3 rounded-xl border border-line bg-card px-4 py-3"
    >
      <motion.span
        initial={{ scale: 0, rotate: -45 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: 'spring', stiffness: 500, damping: 15, delay: 0.1 + index * 0.04 }}
        className={`mt-0.5 ${s.color}`}
      >
        <Icon className="size-5" aria-hidden />
      </motion.span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-semibold">{check.title}</p>
          <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${s.bg} ${s.color}`}>{s.label}</span>
          <span className="text-xs text-muted">{CATEGORY[check.category]}</span>
        </div>
        <p className="mt-1 text-sm text-muted">{check.detail}</p>
        {check.tip && check.status !== 'pass' && (
          <p className="mt-2 rounded-lg bg-accent-soft/60 px-2.5 py-1.5 text-sm">
            <span className="font-semibold text-accent">How to fix: </span>
            {check.id === 'keywords' ? formatSkillList(check.tip) : check.tip}
          </p>
        )}
      </div>
    </motion.li>
  );
}

export default function AtsTab({ ats, onEdit }) {
  const [showPassed, setShowPassed] = useState(false);
  if (!ats) return null;
  const sorted = [...ats.checks].sort((a, b) => ORDER[a.status] - ORDER[b.status]);
  const issues = sorted.filter((c) => c.status === 'fail' || c.status === 'warn');
  const passed = sorted.filter((c) => c.status === 'pass');
  const skipped = sorted.filter((c) => c.status === 'skip');

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_20rem]">
      <div className="space-y-5">
        <section>
          <h3 className="mb-3 font-display text-xl font-semibold">
            {issues.length ? `${issues.length} thing${issues.length > 1 ? 's' : ''} to fix` : 'No problems found'}
          </h3>
          {issues.length > 0 ? (
            <ul className="space-y-2.5">
              {issues.map((c, i) => (
                <CheckRow key={c.id} check={c} index={i} />
              ))}
            </ul>
          ) : (
            <motion.p
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="rounded-xl bg-ok-soft px-4 py-3 text-sm"
            >
              Every check passed. Applicant tracking systems should read this resume cleanly.
            </motion.p>
          )}
        </section>

        <section>
          <button
            type="button"
            onClick={() => setShowPassed((v) => !v)}
            aria-expanded={showPassed}
            className="flex w-full cursor-pointer items-center justify-between rounded-xl px-1 py-2 text-left font-display text-lg font-semibold"
          >
            {passed.length} checks passed
            <motion.span animate={{ rotate: showPassed ? 180 : 0 }}>
              <ChevronDown className="size-5 text-muted" aria-hidden />
            </motion.span>
          </button>
          <AnimatePresence initial={false}>
            {showPassed && (
              <motion.ul
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="space-y-2.5 overflow-hidden"
              >
                {[...passed, ...skipped].map((c, i) => (
                  <CheckRow key={c.id} check={c} index={i} />
                ))}
              </motion.ul>
            )}
          </AnimatePresence>
        </section>
      </div>

      <aside className="space-y-4">
        <div className="card p-5">
          <p className="font-display text-lg font-semibold">Fix it here</p>
          <p className="mt-1 text-sm text-muted">
            Edit your resume section by section, re-check the score, then download a clean, ATS-friendly .docx.
          </p>
          <Button className="mt-4 w-full" icon={PencilLine} onClick={onEdit}>
            Open the editor
          </Button>
        </div>
        <div className="flex gap-2 rounded-2xl border border-dashed border-line p-4 text-xs text-muted">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>
            This is a rule-based estimate of common ATS problems (unreadable text, tables, columns, missing sections or
            keywords). Real ATS differ, so treat it as a checklist, not a guarantee.
          </p>
        </div>
      </aside>
    </div>
  );
}
