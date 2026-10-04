import { motion } from 'framer-motion';
import { Check, Plus } from 'lucide-react';
import { useId, useMemo } from 'react';
import { resumeStrength } from '../../../lib/strength';
import { formatRole, formatSkill } from '../../../utils/format';
import Panel from './Panel';

const GRADE_STYLE = {
  A: 'bg-ok-soft text-ok',
  B: 'bg-accent-soft text-accent',
  C: 'bg-warn-soft text-warn',
  D: 'bg-pen-soft text-pen',
};

function Grade({ grade, large = false, delay = 0 }) {
  return (
    <motion.span
      initial={{ scale: 0, rotate: -20 }}
      animate={{ scale: 1, rotate: large ? -6 : 0 }}
      transition={{ type: 'spring', stiffness: 420, damping: 14, delay }}
      className={`grid shrink-0 place-items-center rounded-xl font-display font-bold ${GRADE_STYLE[grade]} ${
        large ? 'size-14 text-3xl' : 'size-8 text-base'
      }`}
    >
      {grade}
    </motion.span>
  );
}

/** Section grades and weakest bullets, recomputed live from the editor draft. */
export function StrengthReport({ resume, studentMode, onEdit }) {
  const report = useMemo(() => resumeStrength(resume, { studentMode }), [resume, studentMode]);
  return (
    <Panel
      title="Resume strength"
      subtitle={`Section by section${studentMode ? ', judged as a student resume' : ''}. Updates as you edit.`}
      aside={<Grade grade={report.grade} large />}
      className="lg:col-span-full"
    >
      <ul className="grid gap-x-6 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
        {report.sections.map((section, i) => (
          <li key={section.name} className="flex items-start gap-3">
            <Grade grade={section.grade} delay={0.1 + i * 0.05} />
            <div className="min-w-0">
              <p className="text-sm font-semibold">{section.name}</p>
              <p className="text-sm text-muted">{section.notes.join(' ')}</p>
            </div>
          </li>
        ))}
      </ul>
      {report.weakest.length > 0 && (
        <div className="mt-5 border-t border-line pt-4">
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="text-sm font-semibold">Weakest bullet points</p>
            <button type="button" onClick={onEdit} className="cursor-pointer text-sm font-semibold text-accent hover:underline">
              Fix in editor →
            </button>
          </div>
          <ul className="space-y-1.5">
            {report.weakest.map((b) => (
              <li key={`${b.where}-${b.text}`} className="text-sm">
                <span className="text-ink">“{b.text}”</span>{' '}
                <span className="text-warn">— {b.issues.slice(0, 2).join(', ').toLowerCase()}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Panel>
  );
}

/** Core skills of a target job role, plus the closest dataset categories. */
export function TargetRole({ gap, roles, confidence, onRoleChange, loading }) {
  const selectId = useId();
  if (!gap) return null;
  const pct = Math.round(gap.coverage * 100);
  const total = gap.have.length + gap.missing.length;
  return (
    <Panel title="Target role" subtitle="Core skills employers expect for the role.">
      <label htmlFor={selectId} className="sr-only">
        Target role
      </label>
      <select id={selectId} value={gap.role} disabled={loading} onChange={(e) => onRoleChange(e.target.value)} className="field cursor-pointer">
        {gap.available_roles.map((role) => (
          <option key={role} value={role}>
            {role}
          </option>
        ))}
      </select>

      <div className="mt-4 mb-1 flex justify-between text-sm">
        <span>
          {gap.have.length} of {total} core skills
        </span>
        <span className="font-mono font-bold">{pct}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-sunken">
        <motion.div
          key={gap.role}
          className={`h-full rounded-full ${pct >= 70 ? 'bg-ok' : pct >= 40 ? 'bg-accent' : 'bg-warn'}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>

      <ul className="mt-4 flex flex-wrap gap-1.5" aria-label="Core skills">
        {gap.have.map((s) => (
          <li key={s} className="inline-flex items-center gap-1 rounded-md bg-highlight/70 px-2 py-0.5 text-sm dark:bg-highlight/50">
            <Check className="size-3.5" aria-hidden />
            {formatSkill(s)}
          </li>
        ))}
        {gap.missing.map((s) => (
          <li key={s} className="inline-flex items-center gap-1 rounded-md border border-dashed border-pen/50 px-2 py-0.5 text-sm text-pen">
            <Plus className="size-3.5" aria-hidden />
            {formatSkill(s)}
          </li>
        ))}
      </ul>

      {roles?.length > 0 && (
        <p className="mt-4 border-t border-line pt-3 text-xs text-muted">
          Your resume reads most like{' '}
          {roles
            .slice(0, 2)
            .map((r) => `${formatRole(r.role)} (${r.match_percent.toFixed(0)}%)`)
            .join(' or ')}
          {confidence === 'low' ? ', though no category stands out clearly.' : '.'}
        </p>
      )}
    </Panel>
  );
}

/** Every skill found in the resume, grouped. */
export function SkillsFound({ groups }) {
  const total = groups.reduce((n, g) => n + g.skills.length, 0);
  return (
    <Panel title={`Skills found (${total})`} subtitle="Everything we recognised; ×N = mentioned N times.">
      {total === 0 ? (
        <p className="text-sm text-muted">No known skills found. Add a Skills section listing your tools and technologies.</p>
      ) : (
        <dl className="space-y-3">
          {groups.map((group) => (
            <div key={group.group}>
              <dt className="mb-1 text-xs font-semibold text-muted">{group.group}</dt>
              <dd className="flex flex-wrap gap-1.5">
                {group.skills.map(({ skill, count }) => (
                  <span key={skill} className="rounded-md bg-sunken px-2 py-0.5 text-sm">
                    {formatSkill(skill)}
                    {count > 1 && <span className="ml-1 font-mono text-xs text-muted">×{count}</span>}
                  </span>
                ))}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </Panel>
  );
}
