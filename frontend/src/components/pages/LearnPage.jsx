import { motion } from 'framer-motion';
import { ArrowUpRight, Map as MapIcon, Plus, Route, Search, Sparkles, X } from 'lucide-react';
import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { fetchLearnCatalog, fetchLearnPlan } from '../../lib/api';
import { KEYS, readStorage } from '../../lib/storage';
import { formatSkill } from '../../utils/format';
import LearnTab from '../results/LearnTab';
import Button from '../ui/Button';

const MAX_GOALS = 8;
const POPULAR = ['python', 'sql', 'react', 'machine learning', 'data structures', 'docker', 'excel', 'power bi', 'java', 'aws'];

function Chip({ children, onRemove, tone = 'bg-accent-soft text-accent' }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full py-1 pr-1 pl-3 text-sm font-semibold ${tone}`}>
      {children}
      <button
        type="button"
        onClick={onRemove}
        className="grid size-5 cursor-pointer place-items-center rounded-full hover:bg-black/10"
        aria-label={`Remove ${children}`}
      >
        <X className="size-3" aria-hidden />
      </button>
    </span>
  );
}

/** Search box over the catalog that also accepts any skill name. */
function SkillPicker({ catalog, onPick, placeholder, exclude = [] }) {
  const [text, setText] = useState('');
  const [open, setOpen] = useState(false);
  const id = useId();
  const matches = useMemo(() => {
    const q = text.trim().toLowerCase();
    const pool = catalog.filter((s) => !exclude.includes(s.skill));
    if (!q) return pool.slice(0, 8);
    return pool.filter((s) => s.skill.includes(q) || formatSkill(s.skill).toLowerCase().includes(q)).slice(0, 8);
  }, [text, catalog, exclude]);

  const pick = (skill) => {
    if (!skill.trim()) return;
    onPick(skill.trim().toLowerCase());
    setText('');
  };

  return (
    <div className="relative">
      <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" aria-hidden />
      <input
        id={id}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            pick(matches[0] && text.trim() ? matches[0].skill : text);
          }
        }}
        placeholder={placeholder}
        maxLength={50}
        role="combobox"
        aria-expanded={open}
        aria-controls={`${id}-list`}
        className="field w-full pl-9"
      />
      {open && (matches.length > 0 || text.trim()) && (
        <ul id={`${id}-list`} role="listbox" className="card absolute inset-x-0 top-full z-20 mt-1 max-h-72 overflow-y-auto p-1 shadow-[var(--shadow-lift)]">
          {matches.map((s) => (
            <li key={s.skill} role="option" aria-selected="false">
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => pick(s.skill)}
                className="flex w-full cursor-pointer items-baseline justify-between gap-3 rounded-lg px-3 py-2 text-left hover:bg-sunken"
              >
                <span>
                  <span className="font-semibold">{formatSkill(s.skill)}</span>
                  <span className="ml-2 line-clamp-1 text-xs text-muted">{s.what}</span>
                </span>
                <span className="shrink-0 font-mono text-xs text-muted">~{s.hours} h</span>
              </button>
            </li>
          ))}
          {text.trim() && !matches.some((m) => m.skill === text.trim().toLowerCase()) && (
            <li role="option" aria-selected="false">
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => pick(text)}
                className="flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-sunken"
              >
                <Plus className="size-4 text-muted" aria-hidden />
                Add “{text.trim()}”
              </button>
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

/** Search links for a skill without a curated roadmap (clearly not hand-checked). */
function UnknownSkill({ skill }) {
  const q = encodeURIComponent(skill);
  const links = [
    { label: 'Official docs (search)', url: `https://www.google.com/search?q=${q}+official+documentation` },
    { label: 'Full course videos', url: `https://www.youtube.com/results?search_query=${q}+full+course+for+beginners` },
    { label: 'freeCodeCamp articles', url: `https://www.freecodecamp.org/news/search/?query=${q}` },
    { label: 'roadmap.sh roadmaps', url: 'https://roadmap.sh/roadmaps' },
  ];
  return (
    <li className="card p-4">
      <p className="font-semibold">{formatSkill(skill)}</p>
      <p className="mt-0.5 text-sm text-muted">
        We don't have a hand-checked roadmap for this one yet. These searches are a good start:
      </p>
      <ul className="mt-3 flex flex-wrap gap-2">
        {links.map((l) => (
          <li key={l.label}>
            <a
              href={l.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 rounded-lg border border-line px-3 py-1.5 text-sm font-medium hover:border-accent"
            >
              {l.label}
              <ArrowUpRight className="size-3.5 text-muted" aria-hidden />
            </a>
          </li>
        ))}
      </ul>
    </li>
  );
}

/** Learn a skill: choose skills or a career path, get the full roadmap. */
export default function LearnPage({ notify }) {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const [catalog, setCatalog] = useState({ skills: [], roles: [] });
  const [mode, setMode] = useState(params.get('role') ? 'path' : 'skill');
  const [goals, setGoals] = useState(() =>
    (params.get('skills') || '')
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)
      .slice(0, MAX_GOALS),
  );
  const [role, setRole] = useState(params.get('role') || '');
  const [known, setKnown] = useState([]);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const resultRef = useRef(null);
  const savedSkills = useMemo(() => readStorage(KEYS.builder)?.resume?.skills || [], []);

  const build = async (skills = goals) => {
    if (!skills.length) return;
    setLoading(true);
    try {
      const data = await fetchLearnPlan(skills, known);
      setPlan(data);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let live = true;
    fetchLearnCatalog()
      .then((data) => {
        if (!live) return;
        setCatalog(data);
        // Links such as /learn?role=Data%20Analyst or ?skills=sql start right away
        const startRole = data.roles.find((r) => r.role === params.get('role'));
        if (startRole) {
          const skills = startRole.skills.slice(0, MAX_GOALS);
          setGoals(skills);
          build(skills);
        } else if (goals.length) build(goals);
      })
      .catch((err) => notify({ tone: 'error', message: err.message }));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const addGoal = (skill) => {
    if (goals.includes(skill)) return;
    if (goals.length >= MAX_GOALS) {
      notify({ tone: 'error', message: `Up to ${MAX_GOALS} skills at a time. Finish a few first!` });
      return;
    }
    setGoals([...goals, skill]);
  };

  const choosePath = (r) => {
    setRole(r.role);
    setGoals(r.skills.filter((s) => !known.includes(s)).slice(0, MAX_GOALS));
  };

  const paths = catalog.roles.filter((r) => r.skills.length >= 3);
  const chosenRole = catalog.roles.find((r) => r.role === role);

  return (
    <motion.main
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="mx-auto w-full max-w-6xl px-4 pt-8 sm:px-6 sm:pt-10"
    >
      <h1 className="font-display text-4xl font-bold tracking-tight">Learn a skill</h1>
      <p className="mt-2 max-w-2xl text-lg text-muted">
        Pick what you want to learn. You get the order to learn it in, free videos and docs, a checklist for each step, a
        weekly schedule and projects that prove it.
      </p>

      <section className="card mt-6 p-4 sm:p-6">
        <div role="tablist" aria-label="What to learn" className="mb-5 inline-flex rounded-xl bg-sunken p-1">
          {[
            { id: 'skill', label: 'Specific skills', icon: Sparkles },
            { id: 'path', label: 'A career path', icon: Route },
          ].map((m) => {
            const Icon = m.icon;
            return (
              <button
                key={m.id}
                type="button"
                role="tab"
                aria-selected={mode === m.id}
                onClick={() => setMode(m.id)}
                className={`inline-flex cursor-pointer items-center gap-1.5 rounded-lg px-4 py-1.5 text-sm font-semibold ${
                  mode === m.id ? 'bg-card shadow-sm' : 'text-muted'
                }`}
              >
                <Icon className="size-4" aria-hidden />
                {m.label}
              </button>
            );
          })}
        </div>

        {mode === 'skill' ? (
          <div>
            <SkillPicker catalog={catalog.skills} onPick={addGoal} exclude={goals} placeholder="Search a skill: Python, React, Power BI…" />
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-muted">Popular:</span>
              {POPULAR.filter((s) => !goals.includes(s)).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => addGoal(s)}
                  className="cursor-pointer rounded-full border border-line px-3 py-1 text-sm hover:border-ink/40"
                >
                  {formatSkill(s)}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {paths.map((r) => (
              <li key={r.role}>
                <button
                  type="button"
                  onClick={() => choosePath(r)}
                  aria-pressed={role === r.role}
                  className={`h-full w-full cursor-pointer rounded-xl border-2 px-3 py-2.5 text-left transition ${
                    role === r.role ? 'border-accent bg-accent-soft/50' : 'border-line hover:border-ink/30'
                  }`}
                >
                  <span className="block font-semibold">{r.role}</span>
                  <span className="block text-xs text-muted">{r.skills.length} core skills</span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {goals.length > 0 && (
          <div className="mt-5">
            <h2 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">
              I want to learn ({goals.length}/{MAX_GOALS})
            </h2>
            <div className="flex flex-wrap gap-2">
              {goals.map((g) => (
                <Chip key={g} onRemove={() => setGoals(goals.filter((x) => x !== g))}>
                  {formatSkill(g)}
                </Chip>
              ))}
            </div>
          </div>
        )}

        <div className="mt-5 border-t border-line pt-5">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-xs font-bold tracking-wide text-muted uppercase">Skills I already know (optional)</h2>
            {savedSkills.length > 0 && known.length === 0 && (
              <button
                type="button"
                onClick={() => setKnown([...new Set(savedSkills.map((s) => s.toLowerCase()))].slice(0, 150))}
                className="cursor-pointer text-sm font-semibold text-accent hover:underline"
              >
                Use the skills from my resume
              </button>
            )}
          </div>
          <p className="mb-2 text-sm text-muted">We skip prerequisites you already know, e.g. JavaScript before React.</p>
          <SkillPicker catalog={catalog.skills} onPick={(s) => !known.includes(s) && setKnown([...known, s])} exclude={known} placeholder="Add a skill you know" />
          {known.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {known.map((k) => (
                <Chip key={k} tone="bg-ok-soft text-ok" onRemove={() => setKnown(known.filter((x) => x !== k))}>
                  {formatSkill(k)}
                </Chip>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <Button variant="accent" size="lg" icon={MapIcon} loading={loading} disabled={!goals.length} onClick={() => build()}>
            Make my roadmap
          </Button>
        </div>
      </section>

      <div ref={resultRef} className="scroll-mt-24">
        {plan && (
          <div className="mt-8">
            {plan.unknown.length > 0 && (
              <ul className="mb-6 grid gap-3 md:grid-cols-2">
                {plan.unknown.map((s) => (
                  <UnknownSkill key={s} skill={s} />
                ))}
              </ul>
            )}
            {plan.learning_plan.length > 0 && (
              <LearnTab
                plan={plan.learning_plan}
                projects={plan.project_picks}
                missingCount={plan.learning_plan.length}
                role={null}
                roleRoadmap={mode === 'path' ? chosenRole?.roadmap : ''}
                roadmapRole={mode === 'path' ? chosenRole?.role : ''}
                intro="Your skills in the order to learn them, with anything they build on first."
              />
            )}
          </div>
        )}
      </div>
    </motion.main>
  );
}
