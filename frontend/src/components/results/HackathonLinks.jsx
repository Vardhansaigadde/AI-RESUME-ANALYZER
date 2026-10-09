import { motion } from 'framer-motion';
import { ArrowUpRight, Lightbulb, Trophy } from 'lucide-react';
import { useId, useState } from 'react';
import { hackathonSiteLinks } from '../../lib/hackathonSites';

const MODES = [
  { id: 'any', label: 'Any' },
  { id: 'online', label: 'Online' },
  { id: 'in-person', label: 'In person' },
];

const TOPICS = ['AI', 'Web', 'Web3', 'Data', 'Cloud', 'Mobile', 'Cybersecurity', 'Open innovation'];

const TIPS = [
  'Check the registration deadline first; many close a week before the event.',
  'Team size is usually 2 to 4. Mix a builder, a designer and someone who pitches.',
  'Pick themes that match your resume skills so the project is easy to explain in interviews.',
  'Put the project on GitHub with a README and demo link, then add it to your resume.',
];

/** Hackathon finder: prefilled links to each platform's live listing (we can't list their events). */
export default function HackathonLinks() {
  const id = useId();
  const [topic, setTopic] = useState('');
  const [mode, setMode] = useState('any');
  const [city, setCity] = useState('');
  const links = hackathonSiteLinks({ topic, mode, city });

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_18rem]">
      <section className="card p-4 sm:p-5">
        <div className="mb-1 flex items-center gap-2">
          <Trophy className="size-5 text-accent" aria-hidden />
          <h3 className="font-semibold">Find open hackathons</h3>
        </div>
        <p className="text-sm text-muted">
          Hackathon sites don't share their listings, so we open each one's live page with your filters applied.
        </p>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor={`${id}-t`} className="mb-1 block text-xs font-semibold text-muted">
              Topic (optional)
            </label>
            <input
              id={`${id}-t`}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="AI, web3, healthcare…"
              maxLength={40}
              className="field w-full"
            />
          </div>
          <div role="radiogroup" aria-label="Where" className="inline-flex self-start rounded-xl bg-sunken p-1 sm:self-auto">
            {MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                role="radio"
                aria-checked={mode === m.id}
                onClick={() => setMode(m.id)}
                className={`relative cursor-pointer rounded-lg px-3 py-1 text-sm font-semibold transition ${
                  mode === m.id ? 'text-ink' : 'text-muted hover:text-ink'
                }`}
              >
                {mode === m.id && (
                  <motion.span
                    layoutId={`${id}-mode`}
                    className="absolute inset-0 rounded-lg bg-card shadow-sm"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative">{m.label}</span>
              </button>
            ))}
          </div>
          {mode === 'in-person' && (
            <div>
              <label htmlFor={`${id}-c`} className="mb-1 block text-xs font-semibold text-muted">
                City
              </label>
              <input
                id={`${id}-c`}
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Hyderabad, Pune…"
                maxLength={40}
                className="field w-full sm:w-40"
              />
            </div>
          )}
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5" aria-label="Popular topics">
          {TOPICS.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTopic(t)}
              aria-pressed={topic === t}
              className={`cursor-pointer rounded-full border px-2.5 py-0.5 text-xs font-semibold transition ${
                topic === t ? 'border-accent bg-accent-soft text-ink' : 'border-line text-muted hover:text-ink'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <ul className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
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

      <aside className="card p-4 sm:p-5">
        <div className="mb-2 flex items-center gap-2">
          <Lightbulb className="size-4 text-accent" aria-hidden />
          <h3 className="font-semibold">Before you register</h3>
        </div>
        <ul className="space-y-2 text-sm text-muted">
          {TIPS.map((tip) => (
            <li key={tip} className="flex gap-2">
              <span className="mt-2 size-1.5 shrink-0 rounded-full bg-accent" aria-hidden />
              {tip}
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
