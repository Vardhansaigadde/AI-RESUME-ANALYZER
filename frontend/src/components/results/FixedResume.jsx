import { motion } from 'framer-motion';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  Download,
  LayoutTemplate,
  Plus,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Wand2,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { downloadFixedDocx, tailorResume } from '../../lib/api';
import { applyChanges, selectionKey, selectionPayload } from '../../lib/fixedResume';
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

function Score({ label, before, after, suffix = '', stale }) {
  if (before == null && after == null) return null;
  const up = after > before;
  return (
    <div className="rounded-xl border border-line bg-card px-4 py-3">
      <p className="text-xs font-semibold text-muted">{label}</p>
      <p className={`mt-1 flex items-center gap-2 font-display text-2xl font-bold ${stale ? 'opacity-50' : ''}`}>
        <span className="text-muted">
          {before}
          {suffix}
        </span>
        <ArrowRight className="size-4 text-muted" aria-hidden />
        <span className={up ? 'text-ok' : ''}>
          {after}
          {suffix}
        </span>
      </p>
    </div>
  );
}

function ChangeItem({ change, kept, onToggle, wordFile }) {
  const suggestion = change.kind === 'suggestion';
  return (
    <li className={`rounded-xl border p-3 text-sm ${kept ? 'border-line bg-card' : 'border-dashed border-line bg-sunken/50'}`}>
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
          onClick={() => onToggle(change)}
          aria-pressed={kept}
          className="inline-flex shrink-0 cursor-pointer items-center gap-1 rounded-lg border border-line px-2.5 py-1 text-xs font-semibold hover:border-ink/40"
        >
          {kept ? (
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
      {change.before && <p className="mt-2 text-muted line-through decoration-muted/60">{change.before}</p>}
      {change.after && (
        <p className={`mt-1 rounded-lg px-2 py-1 ${kept ? 'bg-highlight/50 dark:bg-highlight/25' : 'text-muted'}`}>
          {change.after}
        </p>
      )}
    </li>
  );
}

function SkillChip({ label, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-dashed border-accent/60 px-2 py-1 text-xs font-semibold text-accent hover:bg-accent-soft"
    >
      <Plus className="size-3" aria-hidden />
      {label}
    </button>
  );
}

/**
 * "Generate a fixed resume": the student's own resume with the report's issues fixed.
 * Every change is highlighted with Keep / Undo, applied instantly in the browser
 * (lib/fixedResume.js); scores update with one "Re-score". Word uploads can be downloaded
 * as their own file (own fonts and layout); everything can also open in the builder.
 */
export default function FixedResume({ resume, jobText, defaultRole, roles, file, onBack, onOpenBuilder, notify }) {
  const hasJob = Boolean(jobText?.trim());
  const [role, setRole] = useState(hasJob ? '' : defaultRole || '');
  const [data, setData] = useState(null);
  const [kept, setKept] = useState(() => new Set());
  const [confirmed, setConfirmed] = useState([]);
  const [scoredKey, setScoredKey] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [pageWarning, setPageWarning] = useState(null);
  const latest = useRef(0);
  const wordFile = Boolean(file && /\.docx$/i.test(file.name));
  const target = { jobDescription: hasJob ? jobText : '', targetRole: hasJob ? '' : role };

  const load = useCallback(
    async (selection = { skip: [], accept: [] }, confirmedSkills = []) => {
      const request = ++latest.current;
      setLoading(true);
      setError(null);
      try {
        const next = await tailorResume({ resume, ...target, confirmedSkills, ...selection });
        if (request !== latest.current) return; // a newer request (e.g. another role) won
        const keptIds = new Set(next.changes.filter((c) => c.applied).map((c) => c.id));
        setData(next);
        setKept(keptIds);
        setScoredKey(selectionKey(keptIds, confirmedSkills));
      } catch (err) {
        if (request === latest.current) setError(err.message);
      } finally {
        if (request === latest.current) setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [resume, hasJob, jobText, role],
  );

  // A new job or role starts fresh; keep and undo never call the server
  useEffect(() => {
    load(undefined, confirmed);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load]);

  const preview = useMemo(() => (data ? applyChanges(resume, data, kept, confirmed) : null), [resume, data, kept, confirmed]);
  const stale = data ? selectionKey(kept, confirmed) !== scoredKey : false;

  const toggle = (change) => {
    if (change.id === 'skills-confirmed') {
      setConfirmed([]); // undoing "I know ..." skills removes them
      return;
    }
    setKept((current) => {
      const next = new Set(current);
      if (next.has(change.id)) next.delete(change.id);
      else next.add(change.id);
      return next;
    });
  };

  const confirm = (skill) => setConfirmed((list) => (list.includes(skill) ? list : [...list, skill]));
  const unconfirm = (skill) => setConfirmed((list) => list.filter((s) => s !== skill));
  const rescore = () => load(selectionPayload(data, kept), confirmed);

  const downloadWord = async () => {
    setDownloading(true);
    setPageWarning(null);
    try {
      const result = await downloadFixedDocx(file, {
        resume,
        ...target,
        confirmedSkills: confirmed,
        ...selectionPayload(data, kept),
      });
      const [before, after] = result.pages;
      if (after > before) {
        setPageWarning(
          `Your Word file probably grew from ${before} to ${after} page${after > 1 ? 's' : ''}. Undo a change or two, shorten a long bullet, or use the builder's compact template.`,
        );
      }
      notify({
        tone: 'success',
        message: result.missed
          ? `Downloaded your Word file with ${result.applied} changes. ${result.missed} couldn't be placed in your file; add them by hand or use the builder.`
          : `Downloaded your own Word file with ${result.applied} changes, in your fonts and layout.`,
      });
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setDownloading(false);
    }
  };

  const confirmedLower = new Set(confirmed.map((s) => s.toLowerCase()));
  const likely = data ? data.likely_skills.filter((s) => !confirmedLower.has(s.skill.toLowerCase())) : [];
  const suggested = data ? data.suggested_skills.filter((s) => !confirmedLower.has(s.toLowerCase())) : [];
  const keptCount = data ? data.changes.filter((c) => kept.has(c.id)).length : 0;

  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="pb-8">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 font-display text-2xl font-bold">
            <Wand2 className="size-6 text-accent" aria-hidden /> Your fixed resume
          </h2>
          <p className="mt-0.5 text-sm text-muted">
            {hasJob ? 'Fixed for the job you pasted.' : role ? `Fixed for ${role} roles.` : 'A general clean-up. Pick a role to tailor it.'}{' '}
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
          <div className="mb-2 grid gap-3 sm:grid-cols-3">
            <Score label="Job match" before={data.before.match} after={data.after.match} stale={stale} />
            <Score label="ATS score" before={data.before.ats} after={data.after.ats} stale={stale} />
            {data.after.role_total != null && (
              <Score
                label={`${data.role} core skills shown`}
                before={data.before.role_have}
                after={data.after.role_have}
                suffix={` / ${data.after.role_total}`}
                stale={stale}
              />
            )}
          </div>
          <div className="mb-5 flex min-h-9 flex-wrap items-center gap-3 text-sm">
            {stale ? (
              <>
                <span className="text-muted">Scores are from before your latest choices.</span>
                <Button size="sm" variant="secondary" icon={RefreshCw} loading={loading} onClick={rescore}>
                  Re-score
                </Button>
              </>
            ) : (
              loading && <span className="text-muted">Scoring…</span>
            )}
          </div>

          <div className="grid gap-6 lg:grid-cols-[1fr_minmax(0,26rem)]">
            <div className="space-y-6">
              <div className="flex flex-wrap gap-2">
                {wordFile && (
                  <Button icon={Download} loading={downloading} onClick={downloadWord}>
                    Download my Word file, fixed
                  </Button>
                )}
                <Button
                  variant={wordFile ? 'secondary' : 'primary'}
                  icon={LayoutTemplate}
                  onClick={() => onOpenBuilder(preview, data.template)}
                >
                  Open in builder
                </Button>
              </div>
              {pageWarning && (
                <p className="-mt-3 flex gap-2 rounded-xl bg-warn-soft px-3 py-2 text-sm text-warn">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
                  {pageWarning}
                </p>
              )}
              {!wordFile && (
                <p className="-mt-3 text-xs text-muted">
                  Want to keep your own design? Upload your resume as a Word (.docx) file and we'll edit it in place.
                </p>
              )}

              {data.notes.length > 0 && (
                <div className="rounded-xl border border-line bg-card p-4">
                  <h3 className="mb-2 flex items-center gap-2 font-semibold">
                    <Sparkles className="size-4 text-accent" aria-hidden /> Only you can do these
                  </h3>
                  <ul className="list-disc space-y-1 pl-5 text-sm">
                    {data.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div>
                <h3 className="mb-2 font-semibold">
                  What we changed <span className="font-normal text-muted">({keptCount} kept)</span>
                </h3>
                {data.changes.length === 0 ? (
                  <p className="text-sm text-muted">Your resume is already in good shape: nothing to fix.</p>
                ) : (
                  <ul className="space-y-2">
                    {data.changes
                      .filter((c) => c.id !== 'skills-confirmed')
                      .map((change) => (
                        <ChangeItem
                          key={change.id}
                          change={change}
                          kept={kept.has(change.id)}
                          onToggle={toggle}
                          wordFile={wordFile}
                        />
                      ))}
                  </ul>
                )}
              </div>

              {confirmed.length > 0 && (
                <div>
                  <h3 className="mb-2 font-semibold">Skills you added</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {confirmed.map((skill) => (
                      <span key={skill} className="inline-flex items-center gap-1 rounded-lg bg-ok-soft px-2 py-1 text-xs font-semibold text-ok">
                        {formatSkill(skill)}
                        <button
                          type="button"
                          onClick={() => unconfirm(skill)}
                          className="cursor-pointer rounded hover:bg-black/10"
                          aria-label={`Remove ${skill}`}
                        >
                          <X className="size-3" aria-hidden />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {likely.length > 0 && (
                <div>
                  <h3 className="font-semibold">You very likely know these</h3>
                  <p className="mb-2 text-sm text-muted">
                    {hasJob ? 'The job asks for them' : 'The role needs them'}, and your skills suggest you've used them. Tick the
                    ones you really have; ATS only finds the exact word.
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {likely.map((s) => (
                      <SkillChip key={s.skill} label={`I know ${formatSkill(s.skill)} (from ${s.because})`} onClick={() => confirm(s.skill)} />
                    ))}
                  </div>
                </div>
              )}

              {suggested.length > 0 && (
                <div>
                  <h3 className="font-semibold">Skills {hasJob ? 'the job' : 'the role'} wants that your resume doesn't show</h3>
                  <p className="mb-2 text-sm text-muted">Tick only the ones you really know. We won't add them otherwise.</p>
                  <div className="flex flex-wrap gap-1.5">
                    {suggested.map((skill) => (
                      <SkillChip key={skill} label={`I know ${formatSkill(skill)}`} onClick={() => confirm(skill)} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="lg:sticky lg:top-32 lg:self-start">
              <p className="mb-2 text-xs font-semibold text-muted">
                Preview ({data.template === 'tech-compact' ? 'Tech Compact' : 'Tech Classic'} template)
              </p>
              <div className="overflow-hidden rounded-xl border border-line bg-white shadow-sm">
                <ScaledPage resume={preview} templateId={data.template} />
              </div>
              {wordFile && <p className="mt-2 text-xs text-muted">Your downloaded Word file keeps your own design instead.</p>}
            </div>
          </div>
        </>
      )}
    </motion.section>
  );
}
