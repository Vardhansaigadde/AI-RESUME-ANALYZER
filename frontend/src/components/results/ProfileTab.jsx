import { motion } from 'framer-motion';
import { Check, Plus, Target, TriangleAlert } from 'lucide-react';
import { useId, useMemo } from 'react';
import { resumeStrength } from '../../lib/strength';
import { formatSkill } from '../../utils/format';

const GRADE_STYLE = {
  A: 'bg-ok-soft text-ok',
  B: 'bg-accent-soft text-accent',
  C: 'bg-warn-soft text-warn',
  D: 'bg-pen-soft text-pen',
};

const reveal = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 260, damping: 24 } },
};

function GradeBadge({ grade, size = 'sm', delay = 0 }) {
  const big = size === 'lg';
  return (
    <motion.span
      initial={{ scale: 0, rotate: -20 }}
      animate={{ scale: 1, rotate: big ? -6 : 0 }}
      transition={{ type: 'spring', stiffness: 420, damping: 14, delay }}
      className={`grid shrink-0 place-items-center rounded-xl font-display font-bold ${GRADE_STYLE[grade]} ${
        big ? 'size-16 text-4xl' : 'size-9 text-lg'
      }`}
    >
      {grade}
    </motion.span>
  );
}

/** Section-by-section grades, recomputed live from the editor draft. */
function StrengthReport({ resume, studentMode, onEdit }) {
  const report = useMemo(() => resumeStrength(resume, { studentMode }), [resume, studentMode]);
  return (
    <motion.section variants={reveal} className="card p-5 sm:p-6 lg:col-span-2" aria-labelledby="strength-heading">
      <div className="flex flex-wrap items-center gap-4">
        <GradeBadge grade={report.grade} size="lg" />
        <div className="flex-1">
          <h3 id="strength-heading" className="font-display text-xl font-semibold">
            Resume strength
          </h3>
          <p className="text-sm text-muted">
            Graded section by section ({report.score}/100). Updates as you edit{studentMode ? ', with student expectations' : ''}.
          </p>
        </div>
      </div>
      <ul className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {report.sections.map((section, i) => (
          <li key={section.name} className="flex gap-3 rounded-xl bg-sunken/60 p-3">
            <GradeBadge grade={section.grade} delay={0.1 + i * 0.05} />
            <div className="min-w-0">
              <p className="font-semibold">{section.name}</p>
              {section.notes.map((note) => (
                <p key={note} className="text-sm text-muted">
                  {note}
                </p>
              ))}
            </div>
          </li>
        ))}
      </ul>
      {report.weakest.length > 0 && (
        <div className="mt-5">
          <p className="label">Weakest bullet points</p>
          <ul className="space-y-2">
            {report.weakest.map((b) => (
              <li key={`${b.where}-${b.text}`} className="rounded-xl border border-warn/30 bg-warn-soft/40 px-3.5 py-2.5 text-sm">
                <p>
                  <span className="text-xs text-muted">{b.where}: </span>“{b.text}”
                </p>
                <p className="mt-1 text-xs text-warn">
                  <TriangleAlert className="mr-1 inline size-3.5" aria-hidden />
                  {b.issues.join(' · ')}
                  {b.tip ? ` — ${b.tip}` : ''}
                </p>
              </li>
            ))}
          </ul>
          <button type="button" onClick={onEdit} className="mt-3 cursor-pointer text-sm font-semibold text-accent underline underline-offset-4">
            Fix them in the editor →
          </button>
        </div>
      )}
    </motion.section>
  );
}

/** Core skills of a target job role: have vs missing, with a role picker. */
function RoleGapCard({ gap, onRoleChange, loading, isResumeOnly }) {
  const selectId = useId();
  if (!gap) return null;
  const pct = Math.round(gap.coverage * 100);
  return (
    <motion.section variants={reveal} className="card p-5 sm:p-6" aria-labelledby="role-gap-heading">
      <div className="flex items-start gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent">
          <Target className="size-5" aria-hidden />
        </span>
        <div className="flex-1">
          <h3 id="role-gap-heading" className="font-display text-xl font-semibold">
            Target role
          </h3>
          <p className="text-sm text-muted">Core skills employers expect for this role.</p>
        </div>
      </div>
      <label htmlFor={selectId} className="label mt-4">
        Compare with
      </label>
      <select
        id={selectId}
        value={gap.role}
        disabled={loading}
        onChange={(e) => onRoleChange(e.target.value)}
        className="field cursor-pointer"
      >
        {gap.available_roles.map((role) => (
          <option key={role} value={role}>
            {role}
          </option>
        ))}
      </select>

      <div className="mt-4">
        <div className="mb-1 flex justify-between text-sm">
          <span className="font-semibold">
            You have {gap.have.length} of {gap.have.length + gap.missing.length} core skills
          </span>
          <span className="font-mono font-bold">{pct}%</span>
        </div>
        <div className="h-2.5 overflow-hidden rounded-full bg-sunken">
          <motion.div
            key={gap.role}
            className={`h-full rounded-full ${pct >= 70 ? 'bg-ok' : pct >= 40 ? 'bg-accent' : 'bg-warn'}`}
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
      </div>

      {gap.have.length > 0 && (
        <ul className="mt-4 flex flex-wrap gap-1.5" aria-label="Core skills you have">
          {gap.have.map((s) => (
            <li key={s} className="inline-flex items-center gap-1 rounded-lg bg-highlight/70 px-2 py-0.5 text-sm font-medium dark:bg-highlight/50">
              <Check className="size-3.5" aria-hidden />
              {formatSkill(s)}
            </li>
          ))}
        </ul>
      )}
      {gap.missing.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Core skills you are missing">
          {gap.missing.map((s) => (
            <li key={s} className="inline-flex items-center gap-1 rounded-lg border border-dashed border-pen/50 px-2 py-0.5 text-sm font-medium text-pen">
              <Plus className="size-3.5" aria-hidden />
              {formatSkill(s)}
            </li>
          ))}
        </ul>
      )}
      {isResumeOnly && gap.missing.length > 0 && (
        <p className="mt-4 text-xs text-muted">The Skill plan tab shows how to learn the missing ones, most important first.</p>
      )}
    </motion.section>
  );
}

function SkillsInventory({ groups }) {
  const total = groups.reduce((n, g) => n + g.skills.length, 0);
  return (
    <motion.section variants={reveal} className="card p-5 sm:p-6" aria-labelledby="inventory-heading">
      <h3 id="inventory-heading" className="font-display text-xl font-semibold">
        Skills found <span className="font-mono text-base text-muted">({total})</span>
      </h3>
      <p className="mb-4 text-sm text-muted">Everything we recognised in your resume. ×N means it appears N times.</p>
      {total === 0 ? (
        <p className="text-sm text-muted">No known skills found. Add a Skills section listing your tools and technologies.</p>
      ) : (
        <dl className="space-y-3">
          {groups.map((group) => (
            <div key={group.group}>
              <dt className="label">{group.group}</dt>
              <dd className="flex flex-wrap gap-1.5">
                {group.skills.map(({ skill, count }) => (
                  <span key={skill} className="rounded-lg border border-line bg-sunken/50 px-2 py-0.5 text-sm">
                    {formatSkill(skill)}
                    {count > 1 && <span className="ml-1 font-mono text-xs text-muted">×{count}</span>}
                  </span>
                ))}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </motion.section>
  );
}

export default function ProfileTab({ result, draft, onRoleChange, roleLoading, onEdit, children }) {
  return (
    <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.07 } } }} className="grid gap-5 lg:grid-cols-2">
      {children}
      <StrengthReport resume={draft} studentMode={result.student_mode} onEdit={onEdit} />
      <RoleGapCard gap={result.role_gap} onRoleChange={onRoleChange} loading={roleLoading} isResumeOnly={result.mode === 'resume_only'} />
      <SkillsInventory groups={result.skills_inventory || []} />
    </motion.div>
  );
}
