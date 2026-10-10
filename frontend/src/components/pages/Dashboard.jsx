import { motion } from 'framer-motion';
import { ArrowRight, ClipboardList, FilePenLine, GraduationCap, Moon, Sparkles, Sun, Sunrise, Sunset } from 'lucide-react';
import { useApplications } from '../../hooks/useApplications';
import { firstName, useAuth } from '../../lib/authContext';
import { STAGES } from '../../lib/cloud';
import { reveal } from '../../lib/motion';
import { KEYS, readStorage } from '../../lib/storage';
import { templateById } from '../../lib/templates';
import { TOOLS } from '../../lib/tools';
import { formatSkill } from '../../utils/format';


/** Things saved in this browser that the student can pick up again. */
function resumeItems() {
  const items = [];
  const builder = readStorage(KEYS.builder);
  if (builder?.resume && (builder.resume.name || builder.resume.experience?.length || builder.resume.projects?.length)) {
    items.push({
      icon: FilePenLine,
      title: 'Continue your resume',
      detail: `${builder.resume.name || 'Untitled'} · ${templateById(builder.template).name} template`,
      path: '/build',
    });
  }
  const progress = readStorage(KEYS.progress, {});
  const started = Object.entries(progress).filter(([, ticks]) => (ticks || []).some(Boolean));
  if (started.length) {
    items.push({
      icon: GraduationCap,
      title: 'Keep learning',
      detail: `In progress: ${started
        .slice(0, 3)
        .map(([skill]) => formatSkill(skill))
        .join(', ')}`,
      path: `/learn?skills=${encodeURIComponent(started.map(([skill]) => skill).slice(0, 8).join(','))}`,
    });
  }
  return items;
}

const QUICK_STARTS = [
  { label: 'Find internships in India', path: '/jobs?kind=internship' },
  { label: 'Learn SQL', path: '/learn?skills=sql' },
  { label: 'Become a Data Analyst', path: '/learn?role=Data%20Analyst' },
  { label: 'Build a fresher resume', path: '/build?template=fresher&start=sample' },
  { label: 'Check my resume against a job', path: '/check' },
];

// A different nudge each day (same all day), so the home page doesn't feel canned
const DAILY_LINES = [
  'One strong bullet beats three weak ones.',
  'Numbers make recruiters stop scrolling.',
  'Apply today, polish tomorrow.',
  'Your best project is your best bullet.',
  'Small edits, more callbacks.',
  'Ten focused applications beat fifty rushed ones.',
  'Every rejection is interview practice.',
  'A skill a day keeps the gaps away.',
  'Tailor the resume, not the truth.',
  'Ship one thing this week and add it to your resume.',
];

/** Greeting for the local time of day, with a matching icon. */
function timeGreeting(now = new Date()) {
  const hour = now.getHours();
  if (hour >= 5 && hour < 12) return { icon: Sunrise, text: 'Good morning' };
  if (hour >= 12 && hour < 17) return { icon: Sun, text: 'Good afternoon' };
  if (hour >= 17 && hour < 22) return { icon: Sunset, text: 'Good evening' };
  return { icon: Moon, text: 'Up late' };
}

function dailyLine(now = new Date()) {
  const day = Math.floor((now.getTime() - now.getTimezoneOffset() * 60000) / 86400000);
  return DAILY_LINES[day % DAILY_LINES.length];
}

function Greeting({ user }) {
  if (!user) {
    return (
      <p className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-accent-soft px-3 py-1 text-xs font-bold text-accent">
        <Sparkles className="size-3.5" aria-hidden />
        Free for students · check your resume without signing up
      </p>
    );
  }
  const { icon: Icon, text } = timeGreeting();
  const name = firstName(user);
  return (
    <div className="mb-4">
      <p className="flex items-center gap-2 font-display text-xl font-semibold">
        <span className="grid size-8 place-items-center rounded-full bg-highlight text-ink">
          <Icon className="size-4" aria-hidden />
        </span>
        {name ? `${text}, ${name}` : text}
      </p>
      <p className="mt-1 pl-10 text-sm text-muted italic">{dailyLine()}</p>
    </div>
  );
}

/** Signed in: applications by stage, linking to the tracker. */
function ApplicationsSummary({ onNavigate }) {
  const { items } = useApplications();
  const counts = STAGES.map((s) => ({ ...s, n: items.filter((x) => x.status === s.id).length }));
  return (
    <motion.section variants={reveal} className="mt-8">
      <h2 className="mb-3 text-xs font-bold tracking-[0.14em] text-muted uppercase">Your applications</h2>
      <a
        href="/tracker"
        onClick={(e) => {
          e.preventDefault();
          onNavigate('/tracker');
        }}
        className="card group flex flex-wrap items-center gap-x-6 gap-y-3 p-4 hover:border-ink/30 sm:p-5"
      >
        <ClipboardList className="size-6 text-accent" aria-hidden />
        {items.length === 0 ? (
          <span className="flex-1 text-sm text-muted">Nothing tracked yet. Save jobs from Find jobs to follow them here.</span>
        ) : (
          <ul className="flex flex-1 flex-wrap gap-x-6 gap-y-2">
            {counts.map((s) => (
              <li key={s.id} className="text-sm">
                <span className="font-display text-2xl font-semibold">{s.n}</span>{' '}
                <span className="text-muted">{s.label.toLowerCase()}</span>
              </li>
            ))}
          </ul>
        )}
        <span className="inline-flex items-center gap-1 text-sm font-semibold">
          Open tracker
          <ArrowRight className="size-4 transition group-hover:translate-x-1" aria-hidden />
        </span>
      </a>
    </motion.section>
  );
}

export default function Dashboard({ onNavigate }) {
  const { user } = useAuth();
  const continueItems = resumeItems();
  const go = (path) => (e) => {
    e.preventDefault();
    onNavigate(path);
  };

  return (
    <motion.main
      initial="hidden"
      animate="show"
      exit={{ opacity: 0 }}
      variants={{ show: { transition: { staggerChildren: 0.07 } } }}
      className="mx-auto w-full max-w-6xl px-4 pt-10 sm:px-6 sm:pt-14"
    >
      <motion.div variants={reveal} className="max-w-2xl">
        <Greeting user={user} />
        <h1 className="font-display text-4xl leading-tight font-bold tracking-tight sm:text-5xl">
          Everything you need to land your <span className="marker px-1">first job</span>
        </h1>
        <p className="mt-4 text-lg text-muted">
          Check and fix your resume, build a new one, find openings and learn the skills employers ask for, all in one place.
        </p>
      </motion.div>

      {user && <ApplicationsSummary onNavigate={onNavigate} />}

      {continueItems.length > 0 && (
        <motion.section variants={reveal} className="mt-8">
          <h2 className="mb-3 text-xs font-bold tracking-[0.14em] text-muted uppercase">Continue where you left off</h2>
          <ul className="grid gap-3 sm:grid-cols-2">
            {continueItems.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.title}>
                  <a
                    href={item.path}
                    onClick={go(item.path)}
                    className="card group flex items-center gap-3 p-4 transition hover:border-ink/30"
                  >
                    <Icon className="size-5 shrink-0 text-accent" aria-hidden />
                    <span className="min-w-0 flex-1">
                      <span className="block font-semibold">{item.title}</span>
                      <span className="block truncate text-sm text-muted">{item.detail}</span>
                    </span>
                    <ArrowRight className="size-4 text-muted transition group-hover:translate-x-0.5" aria-hidden />
                  </a>
                </li>
              );
            })}
          </ul>
        </motion.section>
      )}

      <ul className="mt-8 grid gap-4 sm:grid-cols-2">
        {TOOLS.map((tool) => {
          const Icon = tool.icon;
          return (
            <motion.li key={tool.id} variants={reveal} whileHover={{ y: -4 }} transition={{ type: 'spring', stiffness: 300, damping: 20 }}>
              <a href={tool.path} onClick={go(tool.path)} className="card group flex h-full flex-col p-6 hover:border-ink/30">
                <span className={`grid size-12 place-items-center rounded-2xl ${tool.tone}`}>
                  <Icon className="size-6" aria-hidden />
                </span>
                <h2 className="mt-4 font-display text-2xl font-semibold">{tool.label}</h2>
                <p className="mt-1.5 flex-1 text-muted">{tool.description}</p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold">
                  Open
                  <ArrowRight className="size-4 transition group-hover:translate-x-1" aria-hidden />
                </span>
              </a>
            </motion.li>
          );
        })}
      </ul>

      <motion.section variants={reveal} className="mt-8">
        <h2 className="mb-3 text-xs font-bold tracking-[0.14em] text-muted uppercase">Quick start</h2>
        <ul className="flex flex-wrap gap-2">
          {QUICK_STARTS.map((q) => (
            <li key={q.label}>
              <a
                href={q.path}
                onClick={go(q.path)}
                className="inline-flex rounded-full border border-line bg-card px-3.5 py-1.5 text-sm font-medium transition hover:border-ink/40"
              >
                {q.label}
              </a>
            </li>
          ))}
        </ul>
      </motion.section>
    </motion.main>
  );
}
