import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronDown,
  Clock,
  Code2,
  ExternalLink,
  FileText,
  GraduationCap,
  Hammer,
  Map as MapIcon,
  PartyPopper,
  PlayCircle,
  Quote,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { formatSkill } from '../../utils/format';
import ProjectPicks from './ProjectPicks';

const KIND = {
  docs: { icon: FileText, label: 'Docs' },
  course: { icon: GraduationCap, label: 'Course' },
  tutorial: { icon: BookOpen, label: 'Tutorial' },
  practice: { icon: Code2, label: 'Practice' },
  book: { icon: BookOpen, label: 'Book' },
  video: { icon: PlayCircle, label: 'Video' },
};

const PRIORITY = {
  'must-have': { label: 'must-have', className: 'bg-pen-soft text-pen' },
  'nice-to-have': { label: 'nice-to-have', className: 'bg-accent-soft text-accent' },
  mentioned: { label: 'mentioned', className: 'bg-sunken text-muted' },
  'core-skill': { label: 'core skill', className: 'bg-accent-soft text-accent' },
  prerequisite: { label: 'learn first', className: 'bg-warn-soft text-warn' },
};

const HOURS_PER_WEEK = [4, 6, 8, 10, 15, 20];
const PROGRESS_KEY = 'fitlens:roadmap-progress';
const PACE_KEY = 'fitlens:hours-per-week';

// Progress lives only in this browser; storage can be unavailable (private mode)
function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Not saved; the page still works
  }
}

const joinSkills = (skills) => skills.map(formatSkill).join(', ');

function weekLabel(start, end) {
  return start === end ? `Week ${start}` : `Weeks ${start}–${end}`;
}

/** When each unfinished step happens at the chosen pace, in plan order. */
function schedule(plan, isDone, hoursPerWeek) {
  let elapsed = 0;
  const weeks = {};
  for (const item of plan) {
    if (isDone(item) || !item.hours) continue;
    const start = Math.floor(elapsed / hoursPerWeek) + 1;
    elapsed += item.hours;
    weeks[item.skill] = weekLabel(start, Math.max(start, Math.ceil(elapsed / hoursPerWeek)));
  }
  return { weeks, totalWeeks: Math.ceil(elapsed / hoursPerWeek), remainingHours: elapsed };
}

function Resource({ res }) {
  const kind = KIND[res.kind] || KIND.docs;
  const Icon = kind.icon;
  const video = res.kind === 'video';
  return (
    <li>
      <a
        href={res.url}
        target="_blank"
        rel="noreferrer"
        className="group flex items-center gap-3 rounded-xl border border-line px-3 py-2 text-sm transition hover:border-accent hover:bg-accent-soft/40"
      >
        <Icon className={`size-4 shrink-0 ${video ? 'text-pen' : 'text-accent'}`} aria-hidden />
        <span className="min-w-0 flex-1">
          <span className="line-clamp-2 font-medium sm:line-clamp-1">{res.title}</span>
          {res.by && <span className="block text-xs text-muted">{res.by} · YouTube</span>}
        </span>
        {res.time && (
          <span className="hidden items-center gap-1 text-xs text-muted sm:flex">
            <Clock className="size-3" aria-hidden />
            {res.time}
          </span>
        )}
        <span className="hidden text-xs text-muted sm:inline">{kind.label}</span>
        <ExternalLink className="size-3.5 shrink-0 text-muted transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden />
      </a>
    </li>
  );
}

function Checklist({ items, ticks, onTick }) {
  return (
    <ul className="space-y-1.5">
      {items.map((text, i) => {
        const checked = Boolean(ticks[i]);
        return (
          <li key={text}>
            <label className="flex cursor-pointer items-start gap-2.5 text-sm">
              <input type="checkbox" checked={checked} onChange={() => onTick(i)} className="peer sr-only" />
              <span
                className={`mt-0.5 grid size-4.5 shrink-0 place-items-center rounded-md border-2 transition peer-focus-visible:ring-2 peer-focus-visible:ring-accent ${
                  checked ? 'border-ok bg-ok text-white' : 'border-line bg-card'
                }`}
                aria-hidden
              >
                {checked && <Check className="size-3" strokeWidth={3} />}
              </span>
              <span className={checked ? 'text-muted line-through' : ''}>{text}</span>
            </label>
          </li>
        );
      })}
    </ul>
  );
}

function Step({ item, index, last, done, week, open, onToggle, ticks, onTick }) {
  const priority = PRIORITY[item.priority] || PRIORITY.mentioned;
  const panelId = `step-${index}`;
  return (
    <li className="relative flex gap-3 sm:gap-4">
      {/* Timeline rail */}
      <div className="flex flex-col items-center">
        <motion.span
          animate={{ scale: done ? [1, 1.25, 1] : 1 }}
          transition={{ duration: 0.35 }}
          className={`grid size-8 shrink-0 place-items-center rounded-full border-2 font-mono text-xs font-bold ${
            done ? 'border-ok bg-ok text-white' : open ? 'border-ink bg-ink text-paper' : 'border-line bg-card text-muted'
          }`}
        >
          {done ? <Check className="size-4" strokeWidth={3} aria-hidden /> : index + 1}
        </motion.span>
        {!last && <span className={`w-0.5 flex-1 ${done ? 'bg-ok/50' : 'bg-line'}`} />}
      </div>

      <div className={`card mb-4 min-w-0 flex-1 overflow-hidden ${done ? 'opacity-75' : ''}`}>
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={open}
          aria-controls={panelId}
          className="flex w-full cursor-pointer items-start gap-3 p-4 text-left sm:px-5"
        >
          <span className="min-w-0 flex-1">
            <span className="flex flex-wrap items-center gap-2">
              <span className={`font-display text-lg font-semibold ${done ? 'line-through decoration-ok/60' : ''}`}>
                {formatSkill(item.skill)}
              </span>
              <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${priority.className}`}>{priority.label}</span>
            </span>
            <span className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted">
              {done ? <span className="font-semibold text-ok">Done</span> : week && <span className="font-semibold text-ink">{week}</span>}
              {item.hours > 0 && <span>~{item.hours} h</span>}
              {item.needed_for.length > 0 && <span>Needed for {joinSkills(item.needed_for)}</span>}
            </span>
          </span>
          <motion.span animate={{ rotate: open ? 180 : 0 }} className="mt-1">
            <ChevronDown className="size-5 text-muted" aria-hidden />
          </motion.span>
        </button>

        <AnimatePresence initial={false}>
          {open && (
            <motion.div
              id={panelId}
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="overflow-hidden"
            >
              <div className="space-y-4 border-t border-line p-4 sm:px-5">
                <p className="text-sm text-muted">{item.what}</p>

                {item.why && (
                  <blockquote className="flex gap-2 rounded-xl bg-sunken/60 px-3 py-2 text-sm italic">
                    <Quote className="mt-0.5 size-3.5 shrink-0 text-muted" aria-hidden />
                    <span>
                      <span className="font-semibold not-italic">{item.priority === 'core-skill' ? 'Why: ' : 'From the job: '}</span>
                      {item.why}
                    </span>
                  </blockquote>
                )}

                {item.resources.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Learn</h4>
                    <ul className="space-y-2">
                      {item.resources.map((res) => (
                        <Resource key={res.url} res={res} />
                      ))}
                    </ul>
                  </div>
                )}

                {item.done.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Done when you can</h4>
                    <Checklist items={item.done} ticks={ticks} onTick={onTick} />
                  </div>
                )}

                {item.project && (
                  <p className="flex gap-2 rounded-xl border border-dashed border-ok/50 bg-ok-soft/40 px-3 py-2 text-sm">
                    <Hammer className="mt-0.5 size-4 shrink-0 text-ok" aria-hidden />
                    <span>
                      <span className="font-semibold">Prove it: </span>
                      {item.project}
                    </span>
                  </p>
                )}

                <div className="flex flex-wrap items-center justify-between gap-2">
                  {item.roadmap ? (
                    <a
                      href={item.roadmap}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-sm font-semibold text-accent hover:underline"
                    >
                      Full {formatSkill(item.skill)} roadmap
                      <ArrowUpRight className="size-3.5" aria-hidden />
                    </a>
                  ) : (
                    <span />
                  )}
                  {item.done.length === 0 && (
                    <button
                      type="button"
                      onClick={() => onTick(0)}
                      className="cursor-pointer rounded-lg border border-line px-3 py-1 text-sm font-semibold hover:border-ink/40"
                    >
                      {done ? 'Mark as not done' : 'Mark as done'}
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </li>
  );
}

/** The skill gaps as a study roadmap: order, time, resources, checklists and saved progress. */
export default function LearnTab({ plan, projects, missingCount, role, roleRoadmap, roadmapRole }) {
  const [progress, setProgress] = useState(() => readStorage(PROGRESS_KEY, {}));
  const [hoursPerWeek, setHoursPerWeek] = useState(() => readStorage(PACE_KEY, 8));
  const [openSkill, setOpenSkill] = useState(null);

  useEffect(() => writeStorage(PROGRESS_KEY, progress), [progress]);
  useEffect(() => writeStorage(PACE_KEY, hoursPerWeek), [hoursPerWeek]);

  const steps = useMemo(() => plan || [], [plan]);
  const isDone = (item) => {
    const ticks = progress[item.skill] || [];
    const needed = Math.max(item.done.length, 1);
    return ticks.filter(Boolean).length >= needed;
  };
  const doneCount = steps.filter(isDone).length;
  const { weeks, totalWeeks, remainingHours } = schedule(steps, isDone, hoursPerWeek);
  // Open the first unfinished step until the user picks one
  const current = openSkill ?? steps.find((s) => !isDone(s))?.skill ?? null;

  const tick = (skill, i) =>
    setProgress((p) => {
      const ticks = [...(p[skill] || [])];
      ticks[i] = !ticks[i];
      return { ...p, [skill]: ticks };
    });

  if (!steps.length) {
    return (
      <div className="card flex flex-col items-center p-10 text-center">
        <motion.span initial={{ scale: 0, rotate: -20 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: 'spring', stiffness: 300, damping: 12 }}>
          <PartyPopper className="size-10 text-accent" aria-hidden />
        </motion.span>
        <h3 className="mt-4 font-display text-2xl font-semibold">
          {missingCount ? 'No learning plan for these skills yet' : role ? `You cover every core ${role} skill` : 'No skill gaps to close'}
        </h3>
        <p className="mt-2 max-w-md text-sm text-muted">
          {missingCount
            ? 'The missing skills are specialised ones we don’t have curated resources for. Their official documentation is the best place to start.'
            : 'Your resume already covers every skill the job lists.'}
        </p>
        {roleRoadmap && roadmapRole && (
          <a href={roleRoadmap} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-accent hover:underline">
            See the full {roadmapRole} roadmap to go further
            <ArrowUpRight className="size-3.5" aria-hidden />
          </a>
        )}
      </div>
    );
  }

  const allDone = doneCount === steps.length;
  return (
    <div>
      <ProjectPicks projects={projects} />
      <div className="card mb-6 p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="font-display text-xl font-semibold">{allDone ? 'Roadmap complete!' : 'Your study roadmap'}</h3>
            <p className="mt-1 text-sm text-muted">
              {role ? `Core ${role} skills your resume doesn’t show yet` : 'Skills this job asks for that your resume doesn’t show yet'}, in the order
              to learn them. Tick the checklist as you go; it’s saved in this browser.
            </p>
          </div>
          {roleRoadmap && roadmapRole && (
            <a
              href={roleRoadmap}
              target="_blank"
              rel="noreferrer"
              className="inline-flex shrink-0 items-center gap-1.5 rounded-xl border border-line px-3 py-1.5 text-sm font-semibold transition hover:border-ink/40"
            >
              <MapIcon className="size-4 text-accent" aria-hidden />
              Full {roadmapRole} roadmap
              <ArrowUpRight className="size-3.5 text-muted" aria-hidden />
            </a>
          )}
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
          <div>
            <div className="mb-1.5 flex justify-between text-xs font-semibold">
              <span>
                {doneCount} of {steps.length} skills done
              </span>
              {!allDone && remainingHours > 0 && <span className="text-muted">~{remainingHours} h to go</span>}
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-sunken">
              <motion.div
                className="h-full rounded-full bg-ok"
                initial={false}
                animate={{ width: `${(doneCount / steps.length) * 100}%` }}
                transition={{ type: 'spring', stiffness: 120, damping: 20 }}
              />
            </div>
          </div>
          {!allDone && totalWeeks > 0 && (
            <label className="flex items-center gap-2 text-sm">
              <span className="text-muted">At</span>
              <select
                value={hoursPerWeek}
                onChange={(e) => setHoursPerWeek(Number(e.target.value))}
                className="cursor-pointer rounded-lg border border-line bg-card px-2 py-1 font-semibold"
              >
                {HOURS_PER_WEEK.map((h) => (
                  <option key={h} value={h}>
                    {h} h
                  </option>
                ))}
              </select>
              <span className="text-muted">a week:</span>
              <span className="font-semibold whitespace-nowrap">
                ~{totalWeeks} {totalWeeks === 1 ? 'week' : 'weeks'}
              </span>
            </label>
          )}
        </div>
      </div>

      <ol>
        {steps.map((item, i) => (
          <Step
            key={item.skill}
            item={item}
            index={i}
            last={i === steps.length - 1}
            done={isDone(item)}
            week={weeks[item.skill]}
            open={current === item.skill}
            onToggle={() => setOpenSkill(current === item.skill ? '' : item.skill)}
            ticks={progress[item.skill] || []}
            onTick={(n) => tick(item.skill, n)}
          />
        ))}
      </ol>
    </div>
  );
}
