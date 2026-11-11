import { CircleCheck, CircleHelp, CircleX, Plus } from 'lucide-react';
import { formatSkill } from '../../../utils/format';
import Panel from './Panel';

const STATUS = {
  pass: { icon: CircleCheck, className: 'text-ok' },
  fail: { icon: CircleX, className: 'text-pen' },
  check: { icon: CircleHelp, className: 'text-warn' },
};

const VERDICT = {
  eligible: { text: 'You meet the eligibility rules in this post', className: 'bg-ok-soft text-ok' },
  not_eligible: { text: "You don't meet some eligibility rules in this post", className: 'bg-pen-soft text-pen' },
  check: { text: 'You meet what your resume shows. Check the rest yourself', className: 'bg-warn-soft text-warn' },
};

/** Batch, branch, CGPA, 10th/12th and backlog rules from the post, checked against the resume. */
export function EligibilityPanel({ eligibility }) {
  if (!eligibility) return null;
  const verdict = VERDICT[eligibility.status];
  return (
    <Panel title="Eligibility" subtitle="Rules this job post sets, before skills are even looked at." className="lg:col-span-full">
      <p className={`mb-4 inline-block rounded-full px-3 py-1 text-sm font-semibold ${verdict.className}`}>{verdict.text}</p>
      <ul className="grid gap-2 sm:grid-cols-2">
        {eligibility.checks.map((check) => {
          const { icon: Icon, className } = STATUS[check.status];
          return (
            <li key={check.id} className="flex gap-2.5 rounded-xl border border-line px-3 py-2">
              <Icon className={`mt-0.5 size-4 shrink-0 ${className}`} aria-hidden />
              <span className="text-sm">
                <span className="font-semibold">{check.label}</span>
                <span className="sr-only"> ({check.status})</span>
                {check.detail && <span className="block text-xs text-muted">{check.detail}</span>}
              </span>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}

function SkillList({ skills }) {
  return (
    <p className="text-sm">
      {skills.map(formatSkill).join(', ')}
    </p>
  );
}

/** Which matched skills a project or job backs up, which are only listed, and likely-known ones to add. */
export function SkillEvidence({ evidenced = [], listedOnly = [], implied = [], onAddSkills }) {
  if (!evidenced.length && !listedOnly.length && !implied.length) return null;
  return (
    <Panel
      title="Skill evidence"
      subtitle="Recruiters trust skills they can see you used. The score counts listed-only skills partly."
      className="lg:col-span-full"
    >
      <div className="grid gap-4 md:grid-cols-3">
        {evidenced.length > 0 && (
          <div>
            <p className="mb-1 text-xs font-bold tracking-wide text-ok uppercase">Used in your projects or jobs</p>
            <SkillList skills={evidenced} />
          </div>
        )}
        {listedOnly.length > 0 && (
          <div>
            <p className="mb-1 text-xs font-bold tracking-wide text-warn uppercase">Only listed</p>
            <SkillList skills={listedOnly} />
            <p className="mt-1 text-xs text-muted">
              To count them fully, add a line like <span className="font-semibold">“Tech: Python, Flask, MySQL”</span> under the
              project or internship where you used them.
            </p>
          </div>
        )}
        {implied.length > 0 && (
          <div>
            <p className="mb-1 text-xs font-bold tracking-wide text-accent uppercase">You likely know these</p>
            <p className="mb-2 text-xs text-muted">
              Your skills imply them, but ATS only finds the exact word. Add the ones you really use:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {implied.map((skill) => (
                <button
                  key={skill}
                  type="button"
                  onClick={() => onAddSkills?.([skill])}
                  className="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-dashed border-accent/60 px-2 py-1 text-xs font-semibold text-accent hover:bg-accent-soft"
                >
                  <Plus className="size-3" aria-hidden />
                  {formatSkill(skill)}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
