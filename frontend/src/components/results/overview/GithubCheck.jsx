import { motion } from 'framer-motion';
import { AlertTriangle, ArrowUpRight, Check, GitFork, Plus, RefreshCw, Search, Star, X } from 'lucide-react';
import { useId, useState } from 'react';
import { checkGithub } from '../../../lib/api';
import { reveal } from '../../../lib/motion';
import { githubFromLinks } from '../../../lib/resume';
import { formatSkill } from '../../../utils/format';
import Button from '../../ui/Button';

const USERNAME = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$/;

const STATUS = {
  pass: { icon: Check, className: 'bg-ok-soft text-ok' },
  warn: { icon: AlertTriangle, className: 'bg-warn-soft text-warn' },
  fail: { icon: X, className: 'bg-pen-soft text-pen' },
};

function Column({ title, hint, children, empty }) {
  return (
    <div className="rounded-2xl border border-line p-4">
      <h4 className="font-semibold">{title}</h4>
      <p className="mt-0.5 mb-3 text-xs text-muted">{hint}</p>
      {children || <p className="text-sm text-muted">{empty}</p>}
    </div>
  );
}

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

function Report({ data, resumeSkills, onAddSkills, onReset }) {
  const { profile, stats } = data;
  // Skills added from here (or typed in the editor) since the check drop out of the list
  const listed = new Set((resumeSkills || []).map((s) => s.toLowerCase()));
  const hidden = data.hidden.filter((h) => !listed.has(h.skill) && !listed.has(formatSkill(h.skill).toLowerCase()));
  const added = data.hidden.length - hidden.length;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        {profile.avatar_url && <img src={profile.avatar_url} alt="" className="size-11 rounded-full border border-line" />}
        <div className="min-w-0 flex-1">
          <a
            href={profile.html_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 font-semibold hover:underline"
          >
            {profile.name || profile.login}
            <span className="font-normal text-muted">@{profile.login}</span>
            <ArrowUpRight className="size-3.5 text-muted" aria-hidden />
          </a>
          <p className="flex flex-wrap gap-x-3 text-sm text-muted">
            <span>{plural(stats.own_repos, 'own repo')}</span>
            {stats.forks > 0 && (
              <span className="inline-flex items-center gap-1">
                <GitFork className="size-3.5" aria-hidden />
                {plural(stats.forks, 'fork')}
              </span>
            )}
            <span className="inline-flex items-center gap-1">
              <Star className="size-3.5" aria-hidden />
              {stats.stars}
            </span>
            <span>{stats.active_recently} active in the last 6 months</span>
          </p>
        </div>
        <Button variant="ghost" size="sm" icon={RefreshCw} onClick={onReset}>
          Check another
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <Column
          title={`Backed by your repos (${data.proven.length})`}
          hint="Resume skills a public project shows."
          empty="None of your listed technical skills show in a public repo yet."
        >
          {data.proven.length > 0 && (
            <ul className="flex flex-wrap gap-1.5">
              {data.proven.map((e) => (
                <li
                  key={e.skill}
                  title={`In ${e.repos.join(', ')}`}
                  className="inline-flex items-center gap-1 rounded-md bg-ok-soft px-2 py-0.5 text-sm font-medium text-ok"
                >
                  <Check className="size-3.5" aria-hidden />
                  {formatSkill(e.skill)}
                </li>
              ))}
            </ul>
          )}
        </Column>

        <Column
          title={`No public proof yet (${data.unproven.length})`}
          hint="Recruiters may ask about these. Build a small project or make one public."
          empty="Every technical skill on your resume shows in a repo."
        >
          {data.unproven.length > 0 && (
            <ul className="flex flex-wrap gap-1.5">
              {data.unproven.map((s) => (
                <li key={s} className="rounded-md bg-pen-soft px-2 py-0.5 text-sm font-medium text-pen">
                  {formatSkill(s)}
                </li>
              ))}
            </ul>
          )}
        </Column>

        <Column
          title={`In your repos, not your resume (${hidden.length})`}
          hint="Skills you've shown but don't list. Add the ones you'd discuss in an interview."
          empty={added ? 'Added to your Skills. Re-check to update your scores.' : 'Your resume already lists them.'}
        >
          {hidden.length > 0 && (
            <>
              <ul className="flex flex-wrap gap-1.5">
                {hidden.map((e) => (
                  <li key={e.skill}>
                    <button
                      type="button"
                      onClick={() => onAddSkills([e.skill])}
                      title={`In ${e.repos.join(', ')}. Click to add to your Skills.`}
                      className="inline-flex cursor-pointer items-center gap-1 rounded-md bg-accent-soft px-2 py-0.5 text-sm font-medium text-accent transition hover:brightness-95"
                    >
                      <Plus className="size-3.5" aria-hidden />
                      {formatSkill(e.skill)}
                    </button>
                  </li>
                ))}
              </ul>
              {hidden.length > 1 && (
                <button
                  type="button"
                  onClick={() => onAddSkills(hidden.map((h) => h.skill))}
                  className="mt-3 cursor-pointer text-sm font-semibold text-accent hover:underline"
                >
                  Add all to my Skills
                </button>
              )}
            </>
          )}
        </Column>
      </div>

      <div>
        <h4 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Profile checklist</h4>
        <ul className="grid gap-2 md:grid-cols-2">
          {data.checks.map((c) => {
            const status = STATUS[c.status];
            const Icon = status.icon;
            return (
              <li key={c.id} className="flex gap-2.5 rounded-xl bg-sunken/50 px-3 py-2 text-sm">
                <span className={`mt-0.5 grid size-5 shrink-0 place-items-center rounded-full ${status.className}`}>
                  <Icon className="size-3" strokeWidth={3} aria-hidden />
                </span>
                <span>
                  <span className="font-semibold">{c.title}: </span>
                  <span className="text-muted">{c.detail}</span>
                  {c.tip && <span className="mt-0.5 block">{c.tip}</span>}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

/**
 * GitHub proof check: which resume skills the student's public repos back up.
 * `state` lives in ResultsView so the report survives switching tabs.
 */
export default function GithubCheck({ resume, state, setState, onAddSkills }) {
  const id = useId();
  const [username, setUsername] = useState(() => state.username || githubFromLinks(resume.links));
  const valid = USERNAME.test(username.trim());

  const run = async () => {
    const login = username.trim();
    if (!USERNAME.test(login)) return;
    setState({ loading: true, error: null, data: null, username: login });
    try {
      const data = await checkGithub(resume, login);
      setState({ loading: false, error: null, data, username: login });
    } catch (err) {
      setState({ loading: false, error: err.message, data: null, username: login });
    }
  };

  return (
    <motion.section variants={reveal} className="card p-5 sm:p-6 lg:col-span-full">
      <header className="mb-4">
        <h3 className="font-display text-lg font-semibold">GitHub proof check</h3>
        <p className="mt-0.5 text-sm text-muted">
          Recruiters open your GitHub to see if your skills are real. See which ones your public repos back up.
        </p>
      </header>

      {state.data ? (
        <Report data={state.data} resumeSkills={resume.skills} onAddSkills={onAddSkills} onReset={() => setState({ loading: false, error: null, data: null, username })} />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            run();
          }}
        >
          <div className="flex flex-col gap-3 sm:flex-row">
            <label htmlFor={id} className="sr-only">
              GitHub username
            </label>
            <div className="relative flex-1">
              <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-sm text-muted">github.com/</span>
              <input
                id={id}
                value={username}
                onChange={(e) => setUsername(e.target.value.replace(/^@/, ''))}
                maxLength={39}
                placeholder="your-username"
                autoComplete="off"
                spellCheck={false}
                className="field w-full pl-[6.4rem]"
              />
            </div>
            <Button type="submit" variant="accent" icon={Search} loading={state.loading} disabled={!valid}>
              Check my GitHub
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted">
            Reads only your public profile and repositories, straight from GitHub. No sign-in.
          </p>
          {state.error && (
            <p role="alert" className="mt-3 rounded-xl bg-pen-soft px-3 py-2 text-sm text-pen">
              {state.error}
            </p>
          )}
        </form>
      )}
    </motion.section>
  );
}
