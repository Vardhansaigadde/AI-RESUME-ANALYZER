import { AnimatePresence, motion } from 'framer-motion';
import { ArrowUpRight, Briefcase, CalendarClock, ClipboardList, LogIn, Plus, Trash2 } from 'lucide-react';
import { useId, useState } from 'react';
import { useApplications } from '../../hooks/useApplications';
import { useAuth } from '../../lib/authContext';
import { STAGES } from '../../lib/cloud';
import Button from '../ui/Button';

const STAGE_TONE = {
  saved: 'bg-sunken text-muted',
  applied: 'bg-accent-soft text-accent',
  interview: 'bg-warn-soft text-warn',
  offer: 'bg-ok-soft text-ok',
  rejected: 'bg-pen-soft text-pen',
};

function daysUntil(date) {
  if (!date) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((new Date(`${date}T00:00:00`) - today) / 86_400_000);
}

function Deadline({ date }) {
  const days = daysUntil(date);
  if (days == null) return null;
  const tone = days < 0 ? 'text-muted line-through' : days <= 3 ? 'text-pen font-semibold' : 'text-muted';
  const text = days < 0 ? 'Deadline passed' : days === 0 ? 'Due today' : days === 1 ? 'Due tomorrow' : `Due in ${days} days`;
  return (
    <span className={`inline-flex items-center gap-1 text-xs ${tone}`}>
      <CalendarClock className="size-3.5" aria-hidden />
      {text}
    </span>
  );
}

function AppCard({ app, onUpdate, onRemove }) {
  const [notes, setNotes] = useState(app.notes);
  const id = useId();
  const job = app.job || {};
  return (
    <motion.li layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} className="card p-3.5">
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <a href={app.url} target="_blank" rel="noreferrer" className="group inline-flex items-start gap-1 font-semibold leading-snug hover:underline">
            {job.title || app.url}
            <ArrowUpRight className="mt-0.5 size-3.5 shrink-0 text-muted" aria-hidden />
          </a>
          <p className="truncate text-sm text-muted">{[job.company, job.location].filter(Boolean).join(' · ')}</p>
        </div>
        {job.fit_score != null && (
          <span className="rounded-lg bg-sunken px-1.5 py-0.5 font-mono text-xs font-bold" title="Your fit score when you saved it">
            {Math.round(job.fit_score)}
          </span>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor={`${id}-stage`}>
          Stage
        </label>
        <select
          id={`${id}-stage`}
          value={app.status}
          onChange={(e) => onUpdate(app.id, { status: e.target.value })}
          className={`cursor-pointer rounded-lg border-0 px-2 py-1 text-xs font-bold ${STAGE_TONE[app.status]}`}
        >
          {STAGES.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
        <label className="sr-only" htmlFor={`${id}-deadline`}>
          Deadline
        </label>
        <input
          id={`${id}-deadline`}
          type="date"
          value={app.deadline || ''}
          onChange={(e) => onUpdate(app.id, { deadline: e.target.value || null })}
          className="rounded-lg border border-line bg-card px-2 py-0.5 text-xs"
        />
        <Deadline date={app.deadline} />
      </div>

      <label className="sr-only" htmlFor={`${id}-notes`}>
        Notes
      </label>
      <textarea
        id={`${id}-notes`}
        rows={2}
        value={notes}
        maxLength={2000}
        onChange={(e) => setNotes(e.target.value)}
        onBlur={() => notes !== app.notes && onUpdate(app.id, { notes })}
        placeholder="Notes: referral, interview date, contact…"
        className="field mt-2 w-full resize-y text-sm"
      />

      <div className="mt-2 flex items-center justify-between text-xs text-muted">
        <span>{job.source ? `via ${job.source}` : 'Added by you'}</span>
        <button
          type="button"
          onClick={() => window.confirm('Remove this application from your tracker?') && onRemove(app.id)}
          className="inline-flex cursor-pointer items-center gap-1 rounded-lg px-1.5 py-1 hover:bg-pen-soft hover:text-pen"
        >
          <Trash2 className="size-3.5" aria-hidden />
          Remove
        </button>
      </div>
    </motion.li>
  );
}

function AddJob({ onAdd }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: '', company: '', url: '' });
  const [busy, setBusy] = useState(false);
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      let url = form.url.trim();
      if (!/^https?:\/\//i.test(url)) url = `https://${url}`;
      await onAdd({ title: form.title.trim(), company: form.company.trim(), url, source: '' });
      setForm({ title: '', company: '', url: '' });
      setOpen(false);
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <Button variant="secondary" icon={Plus} onClick={() => setOpen(true)}>
        Add a job
      </Button>
    );
  }
  return (
    <form onSubmit={submit} className="card grid w-full gap-3 p-4 sm:grid-cols-[1fr_1fr_1.4fr_auto] sm:items-end">
      <div>
        <label htmlFor="add-title" className="label">
          Role
        </label>
        <input id="add-title" required maxLength={150} value={form.title} onChange={set('title')} placeholder="Data Analyst Intern" className="field w-full" />
      </div>
      <div>
        <label htmlFor="add-company" className="label">
          Company
        </label>
        <input id="add-company" maxLength={120} value={form.company} onChange={set('company')} placeholder="Acme" className="field w-full" />
      </div>
      <div>
        <label htmlFor="add-url" className="label">
          Link to the posting
        </label>
        <input id="add-url" required maxLength={1000} value={form.url} onChange={set('url')} placeholder="linkedin.com/jobs/view/…" className="field w-full" />
      </div>
      <div className="flex gap-2">
        <Button type="submit" variant="primary" loading={busy}>
          Add
        </Button>
        <Button variant="ghost" onClick={() => setOpen(false)}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

/** Application tracker: every saved or added job, by stage. Needs an account. */
export default function TrackerPage({ notify, onNavigate }) {
  const { user, ready, enabled, openSignIn } = useAuth();
  const { items, loading, error, save, update, remove } = useApplications();
  const [stage, setStage] = useState('all');

  const run = (fn) => async (...args) => {
    try {
      await fn(...args);
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    }
  };

  const header = (
    <>
      <h1 className="font-display text-4xl font-bold tracking-tight">My applications</h1>
      <p className="mt-2 max-w-2xl text-lg text-muted">
        Every job you've saved or applied to, from the first click to the offer. Save jobs from Find jobs, or add ones you found
        on LinkedIn, Internshala and other sites.
      </p>
    </>
  );

  if (!enabled || (ready && !user)) {
    return (
      <motion.main initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="mx-auto w-full max-w-6xl px-4 pt-8 sm:px-6 sm:pt-10">
        {header}
        <div className="card mt-8 flex flex-col items-center p-10 text-center">
          <ClipboardList className="size-10 text-accent" aria-hidden />
          <h2 className="mt-4 font-display text-2xl font-semibold">Sign in to track your applications</h2>
          <p className="mt-2 max-w-md text-sm text-muted">Your tracker is saved to your account, so it's there on your phone and laptop.</p>
          {enabled && (
            <Button variant="primary" icon={LogIn} className="mt-5" onClick={() => openSignIn('Sign in to keep track of every job you apply to.')}>
              Sign in
            </Button>
          )}
        </div>
      </motion.main>
    );
  }

  const counts = Object.fromEntries(STAGES.map((s) => [s.id, items.filter((x) => x.status === s.id).length]));
  const visible = stage === 'all' ? items : items.filter((x) => x.status === stage);

  return (
    <motion.main initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="mx-auto w-full max-w-7xl px-4 pt-8 sm:px-6 sm:pt-10">
      {header}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <div role="tablist" aria-label="Stage" className="flex flex-wrap gap-1.5">
          {[{ id: 'all', label: 'All' }, ...STAGES].map((s) => (
            <button
              key={s.id}
              type="button"
              role="tab"
              aria-selected={stage === s.id}
              onClick={() => setStage(s.id)}
              className={`cursor-pointer rounded-full px-3 py-1 text-sm font-semibold transition ${
                stage === s.id ? 'bg-ink text-paper' : 'bg-card text-muted hover:text-ink'
              }`}
            >
              {s.label}
              <span className="ml-1.5 font-mono text-xs opacity-70">{s.id === 'all' ? items.length : counts[s.id]}</span>
            </button>
          ))}
        </div>
        <AddJob onAdd={run(save)} />
      </div>

      {error && <p className="mt-4 rounded-xl bg-pen-soft px-3 py-2 text-sm text-pen">{error}</p>}

      {!loading && items.length === 0 ? (
        <div className="card mt-6 flex flex-col items-center p-10 text-center">
          <Briefcase className="size-10 text-muted" aria-hidden />
          <h2 className="mt-4 font-display text-xl font-semibold">Nothing tracked yet</h2>
          <p className="mt-2 max-w-md text-sm text-muted">Save openings from Find jobs with the bookmark button, or add a job you found elsewhere.</p>
          <Button variant="secondary" className="mt-5" onClick={() => onNavigate('/jobs')}>
            Find jobs
          </Button>
        </div>
      ) : stage === 'all' ? (
        // Board: one column per stage on wide screens
        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {STAGES.map((s) => (
            <section key={s.id} aria-label={s.label} className="rounded-2xl bg-sunken/50 p-2.5">
              <h2 className="mb-2 flex items-center justify-between px-1.5 text-sm font-bold">
                {s.label}
                <span className={`rounded-full px-2 py-0.5 text-xs ${STAGE_TONE[s.id]}`}>{counts[s.id]}</span>
              </h2>
              <ul className="space-y-2.5">
                <AnimatePresence>
                  {items
                    .filter((x) => x.status === s.id)
                    .map((app) => (
                      <AppCard key={app.id} app={app} onUpdate={run(update)} onRemove={run(remove)} />
                    ))}
                </AnimatePresence>
              </ul>
            </section>
          ))}
        </div>
      ) : (
        <ul className="mt-6 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence>
            {visible.map((app) => (
              <AppCard key={app.id} app={app} onUpdate={run(update)} onRemove={run(remove)} />
            ))}
          </AnimatePresence>
        </ul>
      )}
    </motion.main>
  );
}
