import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Check, Download, LayoutTemplate, Plus, RotateCcw, Sparkles, Wand2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { downloadFixedDocx, tailorResume } from '../../lib/api';
import { formatSkill } from '../../utils/format';
import ScaledPage from '../resume/ScaledPage';
import Button from '../ui/Button';

const KIND_LABEL = {
  added: 'Added',
  rewrote: 'Rewritten',
  reordered: 'Reordered',
  new: 'New',
  fixed: 'Fixed',
  suggestion: 'Suggestion',
};
const KIND_TONE = {
  added: 'bg-ok-soft text-ok',
  new: 'bg-ok-soft text-ok',
  rewrote: 'bg-accent-soft text-accent',
  reordered: 'bg-accent-soft text-accent',
  fixed: 'bg-accent-soft text-accent',
  suggestion: 'bg-warn-soft text-warn',
};
const LAYOUT_ONLY = new Set(['skills-group', 'projects-order', 'headline']);

function Score({ label, before, after, suffix = '' }) {
  if (before == null && after == null) return null;
  const up = after > before;
  return (
    <div className="rounded-xl border border-line bg-card px-4 py-3">
      <p className="text-xs font-semibold text-muted">{label}</p>
      <p className="mt-1 flex items-center gap-2 font-display text-2xl font-bold">
        <span className="text-muted">{before}{suffix}</span>
        <ArrowRight className="size-4 text-muted" aria-hidden />
        <span className={up ? 'text-ok' : ''}>
          {after}
          {suffix}
        </span>
      </p>
    </div>
  );
}

function ChangeItem({ change, onToggle, busy, wordFile }) {
  const suggestion = change.kind === 'suggestion';
  return (
    <li className={`rounded-xl border p-3 text-sm ${change.applied ? 'border-line bg-card' : 'border-dashed border-line bg-sunken/50'}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <span className={`mr-2 inline-block rounded-full px-2 py-0.5 text-[11px] font-bold ${KIND_TONE[change.kind]}`}>
            {KIND_LABEL[change.kind]}
          </span>
          <span className="font-semibold">{change.title}</span>
          {wordFile && LAYOUT_ONLY.has(change.id) && (
            <span className="mt-0.5 block text-xs text-muted">Builder only: your Word file keeps its own layout.</span>
          )}
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => onToggle(change)}
          className="inline-flex shrink-0 cursor-pointer items-center gap-1 rounded-lg border border-line px-2.5 py-1 text-xs font-semibold hover:border-ink/40 disabled:opacity-50"
        >
          {change.applied ? (
            <>
              <RotateCcw className="size-3.5" aria-hidden /> {suggestion ? 'Keep mine' : 'Undo'}
            </>
          ) : (
            <>
              <Check className="size-3.5" aria-hidden /> {suggestion ? 'Use this' : 'Keep'}
            </>
          )}
        </button>
      </div>
      {change.before && (
        <p className="mt-2 text-muted line-through decoration-muted/60">{change.before}</p>
      )}
      {change.after && (
        <p className={`mt-1 rounded-lg px-2 py-1 ${change.applied ? 'bg-highlight/50 dark:bg-highlight/25' : 'text-muted'}`}>
          {change.after}
        </p>
      )}
    </li>
  );
}

/**
 * "Generate a fixed resume": the student's own resume with the report's issues fixed,
 * every change highlighted with Keep / Undo. Word uploads can be downloaded as their
 * own file (own fonts and layout); everything can also open in the builder.
 */
export default function FixedResume({ resume, jobText, defaultRole, roles, file, onBack, onOpenBuilder, notify }) {
  const hasJob = Boolean(jobText?.trim());
  const [role, setRole] = useState(hasJob ? '' : defaultRole || '');
  const [confirmed, setConfirmed] = useState([]);
  const [skip, setSkip] = useState([]);
  const [accept, setAccept] = useState([]);
  const [state, setState] = useState({ loading: true, error: null, data: null });
  const [downloading, setDownloading] = useState(false);
  const wordFile = Boolean(file && /\.docx$/i.test(file.name));

  const payload = useMemo(
    () => ({
      resume,
      jobDescription: hasJob ? jobText : '',
      targetRole: hasJob ? '' : role,
      confirmedSkills: confirmed,
      skip,
      accept,
    }),
    [resume, hasJob, jobText, role, confirmed, skip, accept],
  );

  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    tailorResume(payload).then(
      (data) => live && setState({ loading: false, error: null, data }),
      (err) => live && setState((s) => ({ ...s, loading: false, error: err.message })),
    );
    return () => {
      live = false;
    };
  }, [payload]);

  const toggle = (change) => {
    if (change.id === 'skills-confirmed') {
      setConfirmed([]); // undoing "I know ..." skills removes them
    } else if (change.kind === 'suggestion') {
      setAccept((list) => (change.applied ? list.filter((id) => id !== change.id) : [...list, change.id]));
    } else {
      setSkip((list) => (change.applied ? [...list, change.id] : list.filter((id) => id !== change.id)));
    }
  };

  const downloadWord = async () => {
    setDownloading(true);
    try {
      const { applied, missed } = await downloadFixedDocx(file, payload);
      notify({
        tone: 'success',
        message: missed
          ? `Downloaded your Word file with ${applied} changes. ${missed} couldn't be placed in your file; add them by hand or use the builder.`
          : `Downloaded your own Word file with ${applied} changes, in your fonts and layout.`,
      });
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setDownloading(false);
    }
  };

  const { data, loading, error } = state;
  const kept = data ? data.changes.filter((c) => c.applied).length : 0;

  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="pb-8">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 font-display text-2xl font-bold">
            <Wand2 className="size-6 text-accent" aria-hidden /> Your fixed resume
          </h2>
          <p className="mt-0.5 text-sm text-muted">
            {hasJob
              ? 'Fixed for the job you pasted.'
              : role
                ? `Fixed for ${role} roles.`
                : 'A general clean-up. Pick a role to tailor it.'}{' '}
            Every change is highlighted: keep it or undo it. We never invent experience, numbers or skills.
          </p>
        </div>
        <Button variant="ghost" icon={ArrowLeft} onClick={onBack}>
          Back to report
        </Button>
      </div>

      {!hasJob && (
        <label className="mb-5 flex max-w-md flex-col gap-1 text-sm font-semibold">
          Tailor it for
          <select value={role} onChange={(e) => setRole(e.target.value)} className="field cursor-pointer font-normal">
            <option value="">No role: general clean-up only</option>
            {(roles || []).map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
      )}

      {error && <p className="mb-4 rounded-xl bg-pen-soft px-4 py-3 text-sm text-pen">{error}</p>}

      {!data ? (
        <div className="min-h-[40vh] animate-pulse rounded-2xl border border-line bg-card" aria-busy="true" />
      ) : (
        <>
          <div className="mb-5 grid gap-3 sm:grid-cols-3">
            <Score label="Job match" before={data.before.match} after={data.after.match} />
            <Score label="ATS score" before={data.before.ats} after={data.after.ats} />
            {data.after.role_total != null && (
              <Score
                label={`${data.role} core skills shown`}
                before={data.before.role_have}
                after={data.after.role_have}
                suffix={` / ${data.after.role_total}`}
              />
            )}
          </div>

          <div className="grid gap-6 lg:grid-cols-[1fr_minmax(0,26rem)]">
            <div className="space-y-6">
              <div className="flex flex-wrap gap-2">
                {wordFile && (
                  <Button icon={Download} loading={downloading} disabled={loading} onClick={downloadWord}>
                    Download my Word file, fixed
                  </Button>
                )}
                <Button
                  variant={wordFile ? 'secondary' : 'primary'}
                  icon={LayoutTemplate}
                  disabled={loading}
                  onClick={() => onOpenBuilder(data.resume, data.template)}
                >
                  Open in builder
                </Button>
              </div>
              {!wordFile && (
                <p className="-mt-3 text-xs text-muted">
                  Want to keep your own design? Upload your resume as a Word (.docx) file and we'll edit it in place.
                </p>
              )}

              <div>
                <h3 className="mb-2 font-semibold">
                  What we changed <span className="font-normal text-muted">({kept} kept)</span>
                </h3>
                {data.changes.length === 0 ? (
                  <p className="text-sm text-muted">Your resume is already in good shape: nothing to fix.</p>
                ) : (
                  <ul className={`space-y-2 ${loading ? 'opacity-60' : ''}`}>
                    {data.changes.map((change) => (
                      <ChangeItem key={change.id} change={change} onToggle={toggle} busy={loading} wordFile={wordFile} />
                    ))}
                  </ul>
                )}
              </div>

              {data.suggested_skills.length > 0 && (
                <div>
                  <h3 className="font-semibold">Skills {hasJob ? 'the job' : 'the role'} wants that your resume doesn't show</h3>
                  <p className="mb-2 text-sm text-muted">Tick only the ones you really know. We won't add them otherwise.</p>
                  <div className="flex flex-wrap gap-1.5">
                    {data.suggested_skills.map((skill) => (
                      <button
                        key={skill}
                        type="button"
                        disabled={loading}
                        onClick={() => setConfirmed((list) => [...list, skill])}
                        className="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-dashed border-accent/60 px-2 py-1 text-xs font-semibold text-accent hover:bg-accent-soft disabled:opacity-50"
                      >
                        <Plus className="size-3" aria-hidden />
                        I know {formatSkill(skill)}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {data.notes.length > 0 && (
                <div className="rounded-xl border border-line bg-card p-4">
                  <h3 className="mb-2 flex items-center gap-2 font-semibold">
                    <Sparkles className="size-4 text-accent" aria-hidden /> Only you can add these
                  </h3>
                  <ul className="list-disc space-y-1 pl-5 text-sm">
                    {data.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="lg:sticky lg:top-32 lg:self-start">
              <p className="mb-2 text-xs font-semibold text-muted">Preview ({data.template === 'tech-compact' ? 'Tech Compact' : 'Tech Classic'} template)</p>
              <div className={`overflow-hidden rounded-xl border border-line bg-white shadow-sm ${loading ? 'opacity-60' : ''}`}>
                <ScaledPage resume={data.resume} templateId={data.template} />
              </div>
              {wordFile && (
                <p className="mt-2 text-xs text-muted">Your downloaded Word file keeps your own design instead.</p>
              )}
            </div>
          </div>
        </>
      )}
    </motion.section>
  );
}
