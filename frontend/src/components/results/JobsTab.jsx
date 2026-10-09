import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowUpRight,
  Bookmark,
  BookmarkCheck,
  Briefcase,
  Building2,
  Check,
  Clock,
  MapPin,
  RefreshCw,
  Search,
  ShieldCheck,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useEffect, useId, useRef, useState } from 'react';
import { fetchJobOptions, searchJobs } from '../../lib/api';
import { useApplications } from '../../hooks/useApplications';
import { useAuth } from '../../lib/authContext';
import { jobSiteLinks } from '../../lib/jobSites';
import { scoreTone } from '../../lib/resume';
import { formatSkill } from '../../utils/format';
import SignInRequired from '../auth/SignInRequired';
import Button from '../ui/Button';
import HackathonLinks from './HackathonLinks';

const KINDS = [
  { id: 'all', label: 'All jobs' },
  { id: 'internship', label: 'Internships' },
  { id: 'entry', label: 'Entry-level' },
  { id: 'hackathon', label: 'Hackathons' },
];

const FALLBACK_COUNTRIES = [{ code: 'IN', name: 'India', onsite: false }];

// Fetched once per page load
let optionsRequest = null;
const jobOptions = () => (optionsRequest ??= fetchJobOptions().catch(() => (optionsRequest = null)));

const SORTS = {
  fit: (a, b) => b.fit_score - a.fit_score,
  new: (a, b) => (b.posted || '').localeCompare(a.posted || ''),
};

function postedAgo(iso) {
  if (!iso) return '';
  const days = Math.floor((Date.now() - new Date(`${iso}T00:00:00Z`).getTime()) / 86_400_000);
  if (days <= 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 30) return `${days} days ago`;
  const months = Math.floor(days / 30);
  return months === 1 ? '1 month ago' : `${months} months ago`;
}

function FitBadge({ score }) {
  const tone = scoreTone(score);
  return (
    <div
      className={`grid size-14 shrink-0 place-items-center rounded-2xl ${tone.bg} ${tone.text}`}
      title="How well your resume fits this posting"
    >
      <div className="text-center leading-none">
        <div className="font-mono text-lg font-bold">{Math.round(score)}</div>
        <div className="mt-0.5 text-[9px] font-bold tracking-[0.15em]">FIT</div>
      </div>
    </div>
  );
}

function Meta({ icon: Icon, children }) {
  if (!children) return null;
  return (
    <span className="inline-flex items-center gap-1">
      <Icon className="size-3.5 shrink-0" aria-hidden />
      {children}
    </span>
  );
}

function JobCard({ job, index, saved, onSave }) {
  const have = job.matched_skills.slice(0, 4);
  const scored = job.fit_score != null;
  const missing = job.missing_skills.slice(0, scored ? 3 : 6);
  const tags = [job.employment_type, job.level].filter((t, i, all) => t && all.indexOf(t) === i);
  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 24, delay: Math.min(index, 8) * 0.04 }}
      className="card flex flex-col p-4 sm:p-5"
    >
      <div className="flex gap-4">
        {scored && <FitBadge score={job.fit_score} />}
        <div className="min-w-0 flex-1">
          <h3 className="line-clamp-2 font-display text-lg leading-snug font-semibold" title={job.title}>
            {job.title}
          </h3>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted">
            <Meta icon={Building2}>{job.company}</Meta>
            <Meta icon={MapPin}>{job.location}</Meta>
          </div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
        {tags.map((tag) => (
          <span key={tag} className="rounded-full bg-sunken px-2 py-0.5 font-semibold">
            {tag}
          </span>
        ))}
        {job.salary && (
          <span className="inline-flex items-center gap-1 rounded-full bg-ok-soft px-2 py-0.5 font-semibold text-ok">
            <Wallet className="size-3" aria-hidden />
            {job.salary}
          </span>
        )}
        {job.posted && (
          <span className="inline-flex items-center gap-1 px-1 text-muted">
            <Clock className="size-3" aria-hidden />
            {postedAgo(job.posted)}
          </span>
        )}
      </div>

      {job.excerpt && <p className="mt-3 line-clamp-2 text-sm text-muted">{job.excerpt}</p>}

      {(have.length > 0 || missing.length > 0) && (
        <div className="mt-3 space-y-1.5 text-sm">
          {have.length > 0 && (
            <p>
              <span className="font-semibold">You have </span>
              {have.map((s) => (
                <span key={s} className="mr-1 rounded bg-highlight/70 px-1.5 py-0.5 font-medium dark:bg-highlight/50">
                  {formatSkill(s)}
                </span>
              ))}
            </p>
          )}
          {missing.length > 0 && (
            <p>
              <span className="font-semibold">{scored ? 'Missing ' : 'Skills asked '}</span>
              {missing.map((s, i) => (
                <span key={s} className={`font-medium ${scored ? 'text-pen' : ''}`}>
                  {formatSkill(s)}
                  {i < missing.length - 1 && ', '}
                </span>
              ))}
            </p>
          )}
        </div>
      )}

      <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-4">
        <span className="text-xs text-muted">
          via {job.source}
          {job.short_description && ' · scored from a short preview'}
        </span>
        <span className="flex items-center gap-2">
          {onSave && (
            <button
              type="button"
              onClick={() => onSave(job)}
              disabled={saved}
              aria-label={saved ? 'Saved to your applications' : 'Save to your applications'}
              title={saved ? 'In your applications' : 'Save to your applications'}
              className={`grid size-9 cursor-pointer place-items-center rounded-xl border transition disabled:cursor-default ${
                saved ? 'border-ok/40 bg-ok-soft text-ok' : 'border-line hover:border-ink/40'
              }`}
            >
              {saved ? <BookmarkCheck className="size-4" aria-hidden /> : <Bookmark className="size-4" aria-hidden />}
            </button>
          )}
          <a
            href={job.url}
            target="_blank"
            rel="noreferrer"
            className="group inline-flex items-center gap-1 rounded-xl bg-ink px-3 py-1.5 text-sm font-semibold text-paper transition hover:bg-ink/90"
          >
            View &amp; apply
            <ArrowUpRight
              className="size-4 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              aria-hidden
            />
          </a>
        </span>
      </div>
    </motion.li>
  );
}

function SkeletonCard() {
  return (
    <li className="card animate-pulse p-5" aria-hidden>
      <div className="flex gap-4">
        <div className="size-14 rounded-2xl bg-sunken" />
        <div className="flex-1 space-y-2 pt-1">
          <div className="h-4 w-3/4 rounded bg-sunken" />
          <div className="h-3 w-1/2 rounded bg-sunken" />
        </div>
      </div>
      <div className="mt-4 h-3 w-full rounded bg-sunken" />
      <div className="mt-2 h-3 w-5/6 rounded bg-sunken" />
    </li>
  );
}

/** The skills these openings ask for most, with the ones the resume shows ticked. */
function SkillDemand({ demand, total, scored }) {
  if (!demand?.length) return null;
  const have = demand.filter((d) => d.have).length;
  const tone = (d) => (!scored ? 'bg-accent/70' : d.have ? 'bg-ok' : 'bg-pen/70');
  return (
    <section className="card mb-5 p-4 sm:p-5">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="flex items-center gap-2 font-display text-lg font-semibold">
          <TrendingUp className="size-4.5 text-accent" aria-hidden />
          What these {total} openings ask for
        </h3>
        {scored && (
          <p className="text-sm text-muted">
            You show <span className="font-semibold text-ink">{have}</span> of the top {demand.length}
          </p>
        )}
      </div>
      <ul className="grid gap-x-8 gap-y-2 md:grid-cols-2">
        {demand.map((d, i) => {
          const pct = Math.round(d.share * 100);
          return (
            <li
              key={d.skill}
              className="grid grid-cols-[7.5rem_1fr_2.5rem] items-center gap-3 text-sm sm:grid-cols-[9rem_1fr_2.5rem]"
            >
              <span className="flex min-w-0 items-center gap-1.5">
                {d.have ? (
                  <Check className="size-3.5 shrink-0 text-ok" strokeWidth={3} aria-label="On your resume" />
                ) : (
                  <span className="size-3.5 shrink-0" aria-hidden />
                )}
                <span className={`truncate ${scored && !d.have ? 'font-semibold text-pen' : 'font-medium'}`}>
                  {formatSkill(d.skill)}
                </span>
              </span>
              <span className="h-2 overflow-hidden rounded-full bg-sunken">
                <motion.span
                  className={`block h-full rounded-full ${tone(d)}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.6, delay: i * 0.03, ease: 'easeOut' }}
                />
              </span>
              <span className="text-right font-mono text-xs text-muted">{pct}%</span>
            </li>
          );
        })}
      </ul>
      <p className="mt-3 text-xs text-muted">
        Share of these postings that mention each skill.
        {scored
          ? ' Red ones aren’t on your resume yet: if you have them, add them; if not, they’re worth learning next.'
          : ' Check your resume first to see which ones you already show.'}
      </p>
    </section>
  );
}

function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <p className="mt-6 text-center text-xs text-muted">
      Jobs from{' '}
      {sources
        .filter((s) => s.status !== 'off')
        .map((s, i, list) => (
          <span key={s.name}>
            <a
              href={s.url}
              target="_blank"
              rel="noreferrer"
              className="font-semibold underline-offset-2 hover:underline"
            >
              {s.name}
            </a>
            {s.status === 'unavailable' && ' (unavailable right now)'}
            {i < list.length - 2 ? ', ' : i === list.length - 2 ? ' and ' : ''}
          </span>
        ))}
      . Listings refresh every few hours; always check the posting before applying.
    </p>
  );
}

/**
 * Live jobs and internships with your fit score on each.
 * `state` lives in ResultsView so results survive switching tabs.
 */
/** Prefilled searches on the big job sites (we can't list their jobs, but can open their search). */
function SiteLinks({ query, kind, countryName }) {
  const [city, setCity] = useState('');
  const id = useId();
  if (query.trim().length < 2) return null;
  const links = jobSiteLinks({ query, kind, city, country: countryName });
  return (
    <section className="card mt-4 p-4 sm:p-5">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="font-semibold">Search the big job sites too</h3>
          <p className="text-sm text-muted">Opens each site's own search for “{query.trim()}”, already filled in.</p>
        </div>
        <div>
          <label htmlFor={id} className="mb-1 block text-xs font-semibold text-muted">
            City (optional)
          </label>
          <input
            id={id}
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Bengaluru, Pune, Remote…"
            maxLength={40}
            className="field w-48"
          />
        </div>
      </div>
      <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {links.map((site) => (
          <li key={site.name}>
            <a
              href={site.url}
              target="_blank"
              rel="noreferrer"
              className="group flex h-full flex-col rounded-xl border border-line px-3 py-2 transition hover:border-accent hover:bg-accent-soft/40"
            >
              <span className="flex items-center justify-between gap-1 font-semibold">
                {site.name}
                <ArrowUpRight
                  className="size-3.5 text-muted transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                  aria-hidden
                />
              </span>
              <span className="text-xs text-muted">{site.note}</span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function JobsTab({ resume, defaultQuery, defaultKind, studentMode, state, setState }) {
  const id = useId();
  const [form, setForm] = useState(
    () =>
      state.params || {
        query: defaultQuery || 'Software Engineer',
        country: 'IN',
        kind: defaultKind || (studentMode ? 'internship' : 'all'),
      },
  );
  const [countries, setCountries] = useState(FALLBACK_COUNTRIES);
  const [sort, setSort] = useState('fit');
  const { user, ready, enabled, openSignIn } = useAuth();
  // Jobs need an account when accounts are set up
  const locked = enabled && (!ready || !user);

  const run = async (params = form) => {
    const query = params.query.trim();
    // Hackathons are links to other sites, not a job search
    if (locked || query.length < 2 || params.kind === 'hackathon') return;
    // Only the latest search may update the results
    const requestId = `${Date.now()}-${Math.random()}`;
    setState((s) => ({ ...s, loading: true, error: null, params, requestId }));
    try {
      const data = await searchJobs(resume, { ...params, query });
      setState((s) => (s.requestId === requestId ? { loading: false, error: null, params, data } : s));
    } catch (err) {
      setState((s) => (s.requestId === requestId ? { ...s, loading: false, error: err.message } : s));
    }
  };

  const started = useRef(false);

  useEffect(() => {
    let live = true;
    jobOptions().then((opts) => live && opts?.countries?.length && setCountries(opts.countries));
    return () => {
      live = false;
    };
  }, []);

  useEffect(() => {
    // First visit (or right after signing in): search with the target role, once even under StrictMode
    if (!locked && !started.current && !state.data && !state.loading) {
      started.current = true;
      run();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locked]);

  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }));
  const searchWith = (changes) => {
    const next = { ...form, ...changes };
    setForm(next);
    run(next);
  };

  const hackathons = form.kind === 'hackathon';
  const { data, loading, error } = state;
  const applications = useApplications();
  const saveJob = async (job) => {
    if (!user) {
      openSignIn('Sign in to save jobs and track your applications.');
      return;
    }
    try {
      await applications.save(job);
    } catch {
      // A failed save leaves the button as it was; the tracker page shows errors
    }
  };
  const jobs = data ? [...data.jobs].sort(SORTS[sort]) : [];
  const onsiteOff = data?.sources?.find((s) => s.name === 'Adzuna' && s.status === 'off');

  if (locked) {
    return ready ? (
      <SignInRequired
        icon={Briefcase}
        title="Jobs, internships & hackathons"
        text="See live openings with your fit score on each, one-click searches on LinkedIn, Internshala and Naukri, and open hackathons. Save jobs to your tracker."
        reason="Sign in to search jobs, internships and hackathons."
      />
    ) : (
      <div className="min-h-[40vh]" aria-busy="true" />
    );
  }

  return (
    <div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          run();
        }}
        className="card p-4 sm:p-5"
      >
        <div className={`flex flex-col gap-3 sm:flex-row ${hackathons ? 'hidden' : ''}`}>
          <div className="relative flex-1">
            <label htmlFor={`${id}-q`} className="sr-only">
              Role or keywords
            </label>
            <Search
              className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted"
              aria-hidden
            />
            <input
              id={`${id}-q`}
              value={form.query}
              onChange={(e) => set('query')(e.target.value)}
              maxLength={80}
              placeholder="Role or keywords, e.g. data analyst"
              className="field w-full pl-9"
            />
          </div>
          <div className="flex gap-3">
            <label htmlFor={`${id}-c`} className="sr-only">
              Where
            </label>
            <select
              id={`${id}-c`}
              value={form.country}
              onChange={(e) => set('country')(e.target.value)}
              className="field flex-1 cursor-pointer sm:w-44 sm:flex-none"
            >
              {countries.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
              <option value="ANY">Anywhere (remote)</option>
            </select>
            <Button type="submit" variant="accent" icon={Search} loading={loading}>
              Search
            </Button>
          </div>
        </div>

        <div className={`flex flex-wrap items-center justify-between gap-3 ${hackathons ? '' : 'mt-3'}`}>
          <div role="radiogroup" aria-label="Job type" className="inline-flex rounded-xl bg-sunken p-1">
            {KINDS.map((k) => (
              <button
                key={k.id}
                type="button"
                role="radio"
                aria-checked={form.kind === k.id}
                onClick={() => searchWith({ kind: k.id })}
                className={`relative cursor-pointer rounded-lg px-3 py-1 text-sm font-semibold transition ${
                  form.kind === k.id ? 'text-ink' : 'text-muted hover:text-ink'
                }`}
              >
                {form.kind === k.id && (
                  <motion.span
                    layoutId={`${id}-kind`}
                    className="absolute inset-0 rounded-lg bg-card shadow-sm"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative">{k.label}</span>
              </button>
            ))}
          </div>
          <p className="flex items-center gap-1.5 text-xs text-muted">
            <ShieldCheck className="size-3.5 text-ok" aria-hidden />
            Only your search words go to job sites, never your resume.
          </p>
        </div>
      </form>

      {hackathons ? (
        <div className="mt-4">
          <HackathonLinks />
        </div>
      ) : (
        <SiteLinks
          query={form.query}
          kind={form.kind}
          countryName={form.country === 'ANY' ? '' : countries.find((c) => c.code === form.country)?.name || 'India'}
        />
      )}

      <div className={`mt-5 ${hackathons ? 'hidden' : ''}`} aria-live="polite">
        {error && !loading && (
          <div className="card flex flex-col items-center gap-3 p-8 text-center">
            <p className="text-sm text-muted">{error}</p>
            <Button variant="secondary" icon={RefreshCw} onClick={() => run()}>
              Try again
            </Button>
          </div>
        )}

        {loading && (
          <>
            <p className="mb-3 text-sm text-muted">Finding openings and scoring your resume against each one…</p>
            <ul className="grid gap-4 lg:grid-cols-2">
              {[0, 1, 2, 3].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </ul>
          </>
        )}

        {!loading && !error && data && (
          <>
            <SkillDemand demand={data.skill_demand} total={data.jobs.length} scored={data.scored !== false} />
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm">
                <span className="font-semibold">{jobs.length}</span>{' '}
                <span className="text-muted">
                  {jobs.length === 1 ? 'opening' : 'openings'} for “{data.query}”
                  {onsiteOff && data.country !== 'ANY' && ' · remote roles'}
                </span>
              </p>
              {jobs.length > 1 && (
                <label className="flex items-center gap-2 text-sm text-muted">
                  Sort by
                  <select
                    value={sort}
                    onChange={(e) => setSort(e.target.value)}
                    className="cursor-pointer rounded-lg border border-line bg-card px-2 py-1 text-sm text-ink"
                  >
                    <option value="fit">Best fit</option>
                    <option value="new">Newest</option>
                  </select>
                </label>
              )}
            </div>

            {jobs.length === 0 ? (
              <div className="card p-8 text-center">
                <h3 className="font-display text-xl font-semibold">No openings found</h3>
                <p className="mx-auto mt-2 max-w-md text-sm text-muted">
                  Try a broader search such as “developer” or “analyst”, switch to All jobs, or choose Anywhere
                  (remote).
                </p>
              </div>
            ) : (
              <ul className="grid gap-4 lg:grid-cols-2">
                <AnimatePresence>
                  {jobs.map((job, i) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      index={i}
                      saved={applications.savedUrls.has(job.url)}
                      onSave={enabled ? saveJob : undefined}
                    />
                  ))}
                </AnimatePresence>
              </ul>
            )}
            {jobs.length < 5 && data.country !== 'ANY' && (
              <p className="mt-4 text-center text-sm text-muted">
                Few matches here.{' '}
                <button
                  type="button"
                  onClick={() => searchWith({ country: 'ANY' })}
                  className="cursor-pointer font-semibold text-accent hover:underline"
                >
                  Search remote jobs anywhere
                </button>
              </p>
            )}
            <Sources sources={data.sources} />
          </>
        )}
      </div>
    </div>
  );
}
