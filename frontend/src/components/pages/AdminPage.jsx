import { motion } from 'framer-motion';
import { RefreshCw } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../lib/authContext';
import { supabase } from '../../lib/supabase';
import Button from '../ui/Button';
import { NotFoundPage } from './LegalPages';

const PAGE_LABELS = {
  home: 'Home',
  check: 'Check page',
  analysis: 'Resumes analyzed',
  build: 'Builder',
  jobs: 'Jobs',
  learn: 'Learn',
  tracker: 'Tracker',
  privacy: 'Privacy',
  terms: 'Terms',
};

const fmt = (n) => Number(n || 0).toLocaleString('en-IN');

function Stat({ label, value, hint }) {
  return (
    <div className="rounded-xl border border-line p-3">
      <p className="text-xs font-semibold text-muted">{label}</p>
      <p className="mt-1 font-display text-2xl font-bold">{fmt(value)}</p>
      {hint && <p className="text-xs text-muted">{hint}</p>}
    </div>
  );
}

function Group({ title, note, children }) {
  return (
    <section className="card p-4 sm:p-5">
      <h2 className="font-semibold">{title}</h2>
      {note && <p className="text-sm text-muted">{note}</p>}
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">{children}</div>
    </section>
  );
}

/** Last 30 days: visitors (not signed in) and signed-in users per day. */
function DailyChart({ daily }) {
  const max = Math.max(1, ...daily.map((d) => d.visitors + d.users));
  return (
    <section className="card p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">Last 30 days</h2>
        <p className="flex items-center gap-3 text-xs text-muted">
          <span className="flex items-center gap-1">
            <span className="size-2.5 rounded-sm bg-accent" aria-hidden /> Signed-in users
          </span>
          <span className="flex items-center gap-1">
            <span className="size-2.5 rounded-sm bg-ink/25" aria-hidden /> Visitors
          </span>
        </p>
      </div>
      <div className="mt-4 flex h-40 items-end gap-1" role="img" aria-label="Daily visitors and signed-in users, last 30 days">
        {daily.map((d) => (
          <div key={d.day} className="group relative flex h-full flex-1 flex-col justify-end" title={`${d.day}: ${d.visitors} visitors, ${d.users} users`}>
            <div className="w-full rounded-t-sm bg-ink/25" style={{ height: `${(d.visitors / max) * 100}%` }} />
            <div className="w-full bg-accent" style={{ height: `${(d.users / max) * 100}%` }} />
          </div>
        ))}
      </div>
      <div className="mt-1 flex justify-between text-xs text-muted">
        <span>{daily[0]?.day}</span>
        <span>{daily.at(-1)?.day}</span>
      </div>
    </section>
  );
}

function Pages({ pages }) {
  const rows = Object.entries(pages)
    .map(([key, v]) => ({ key, guests: Number(v.guests), users: Number(v.users) }))
    .sort((a, b) => b.guests + b.users - (a.guests + a.users));
  return (
    <section className="card p-4 sm:p-5">
      <h2 className="font-semibold">What people use</h2>
      <p className="text-sm text-muted">Page opens in the last 30 days.</p>
      {rows.length === 0 ? (
        <p className="mt-3 text-sm text-muted">No visits recorded yet.</p>
      ) : (
        <table className="mt-3 w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="py-1 font-semibold">Page</th>
              <th className="py-1 text-right font-semibold">Visitors</th>
              <th className="py-1 text-right font-semibold">Signed in</th>
              <th className="py-1 text-right font-semibold">Total</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key} className="border-t border-line">
                <td className="py-1.5">{PAGE_LABELS[r.key] || r.key}</td>
                <td className="py-1.5 text-right">{fmt(r.guests)}</td>
                <td className="py-1.5 text-right">{fmt(r.users)}</td>
                <td className="py-1.5 text-right font-semibold">{fmt(r.guests + r.users)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

/**
 * Owner-only usage dashboard. Not linked anywhere. The database decides who may
 * see it (site_stats() returns nothing unless the signed-in account is an admin);
 * everyone else gets the ordinary 404 page, so it looks like no such page exists.
 */
export default function AdminPage({ onHome }) {
  const { user, ready } = useAuth();
  const [state, setState] = useState({ status: 'checking', stats: null });

  const load = useCallback(async () => {
    if (!supabase || !user) {
      setState({ status: 'denied', stats: null });
      return;
    }
    setState((s) => ({ ...s, status: s.stats ? 'refreshing' : 'checking' }));
    const { data, error } = await supabase.rpc('site_stats');
    setState(error || !data ? { status: 'denied', stats: null } : { status: 'ok', stats: data });
  }, [user]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  if (!ready || state.status === 'checking') return <main className="min-h-[60vh]" />;
  if (state.status === 'denied') return <NotFoundPage onHome={onHome} />;

  const { users, visitors, daily, pages, saved, generated_at: at } = state.stats;
  return (
    <motion.main
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto w-full max-w-6xl space-y-4 px-4 pt-8 sm:px-6 sm:pt-10"
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-4xl font-bold tracking-tight">Site usage</h1>
          <p className="mt-1 text-sm text-muted">Updated {new Date(at).toLocaleString('en-IN')} · days in Indian time</p>
        </div>
        <Button variant="secondary" icon={RefreshCw} loading={state.status === 'refreshing'} onClick={load}>
          Refresh
        </Button>
      </div>

      <Group title="Signed-in users" note="People with an account.">
        <Stat label="Total accounts" value={users.total} />
        <Stat label="New today" value={users.new_today} hint={`${fmt(users.new_7d)} this week · ${fmt(users.new_30d)} in 30 days`} />
        <Stat label="Active today" value={users.active_today} hint="Opened the site signed in" />
        <Stat label="Active, 7 / 30 days" value={users.active_7d} hint={`${fmt(users.active_30d)} in 30 days`} />
      </Group>

      <Group title="Visitors" note="Browsers that used the site without signing in (each counted once per day).">
        <Stat label="Today" value={visitors.today} />
        <Stat label="Last 7 days" value={visitors.last_7d} />
        <Stat label="Last 30 days" value={visitors.last_30d} />
        <Stat label="All time" value={visitors.all_time} />
      </Group>

      <DailyChart daily={daily} />

      <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
        <Pages pages={pages} />
        <section className="card p-4 sm:p-5">
          <h2 className="font-semibold">Saved by users</h2>
          <dl className="mt-3 space-y-2 text-sm">
            {[
              ['Resumes', saved.resumes],
              ['Tracked applications', saved.applications],
              ['Learning roadmaps', saved.roadmaps],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between border-b border-line pb-2">
                <dt className="text-muted">{label}</dt>
                <dd className="font-semibold">{fmt(value)}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </motion.main>
  );
}
