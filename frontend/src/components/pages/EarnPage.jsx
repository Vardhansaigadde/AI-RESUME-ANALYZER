import { motion } from 'framer-motion';
import {
  ArrowUpRight,
  Bot,
  CalendarCheck,
  Check,
  ChevronDown,
  Copy,
  IndianRupee,
  Landmark,
  Receipt,
  ShieldAlert,
  Sparkles,
  Store,
  X,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import {
  AI_RULES,
  LEVELS,
  PAYMENTS,
  PLAN,
  PLATFORMS,
  PRICING,
  SCAMS,
  SERVICES,
  TAX,
  TEMPLATES,
  searchLinks,
  tutorialLink,
} from '../../lib/earn';
import { readStorage, writeStorage } from '../../lib/storage';

const PLAN_KEY = 'fitlens:earn-plan';
const SECTIONS = [
  ['services', 'What to sell'],
  ['plan', '30-day plan'],
  ['platforms', 'Where'],
  ['templates', 'Messages'],
  ['pricing', 'Pricing'],
  ['ai', 'Using AI'],
  ['paid', 'Getting paid'],
  ['scams', 'Scams'],
  ['tax', 'Tax'],
];

function Section({ id, icon: Icon, title, subtitle, children }) {
  return (
    <section id={id} className="mt-14 scroll-mt-24">
      <div className="mb-5 flex items-start gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-highlight/70 dark:bg-highlight/50">
          <Icon className="size-5" aria-hidden />
        </span>
        <div>
          <h2 className="font-display text-2xl font-bold">{title}</h2>
          {subtitle && <p className="mt-0.5 text-muted">{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

function ExternalLink({ href, children, className = '' }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className={`inline-flex items-center gap-1 font-semibold text-accent underline-offset-2 hover:underline ${className}`}
    >
      {children}
      <ArrowUpRight className="size-3.5" aria-hidden />
    </a>
  );
}

function ServiceCard({ service, open, onToggle, matched }) {
  return (
    <li className={`card overflow-hidden ${open ? 'sm:col-span-2' : ''}`}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full cursor-pointer items-start gap-3 p-5 text-left"
      >
        <span className="flex-1">
          {matched && (
            <span className="mb-1.5 inline-block rounded-full bg-ok-soft px-2 py-0.5 text-xs font-bold text-ok">
              Matches your resume
            </span>
          )}
          <span className="block font-display text-lg font-semibold">{service.title}</span>
          <span className="mt-1 block text-sm text-muted">{service.what}</span>
          <span className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm">
            <span>
              <span className="text-muted">Start at </span>
              <span className="font-semibold">{service.price}</span>
            </span>
            <span>
              <span className="text-muted">Learn in </span>
              <span className="font-semibold">{service.learn}</span>
            </span>
          </span>
        </span>
        <ChevronDown className={`mt-1 size-5 shrink-0 text-muted transition ${open ? 'rotate-180' : ''}`} aria-hidden />
      </button>
      {open && (
        <div className="grid gap-5 border-t border-line px-5 pt-4 pb-5 text-sm md:grid-cols-2">
          <div className="space-y-4">
            <div>
              <p className="mb-1 text-xs font-bold tracking-wide text-accent uppercase">Free tools that do the hard part</p>
              <ul className="list-disc space-y-0.5 pl-5">
                {service.tools.map((tool) => (
                  <li key={tool}>{tool}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-1 text-xs font-bold tracking-wide text-warn uppercase">What you still must do</p>
              <p>{service.youDo}</p>
            </div>
            <div>
              <p className="mb-1 text-xs font-bold tracking-wide text-ok uppercase">Your 3 samples</p>
              <p>{service.samples}</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <p className="mb-1 text-xs font-bold tracking-wide text-muted uppercase">Where the clients are</p>
              <p>{service.where}</p>
            </div>
            <div>
              <p className="mb-1.5 text-xs font-bold tracking-wide text-muted uppercase">Check demand and prices</p>
              <div className="flex flex-col items-start gap-1.5">
                <ExternalLink href={tutorialLink(service.search)}>Learn it free on YouTube</ExternalLink>
                {searchLinks(service.search).map((link) => (
                  <ExternalLink key={link.href} href={link.href}>
                    {link.label}
                  </ExternalLink>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </li>
  );
}

function Plan() {
  const [done, setDone] = useState(() => readStorage(PLAN_KEY, {}));
  const total = PLAN.reduce((n, w) => n + w.days.length, 0);
  const count = Object.values(done).filter(Boolean).length;
  const toggle = (key) => {
    const next = { ...done, [key]: !done[key] };
    setDone(next);
    writeStorage(PLAN_KEY, next);
  };
  return (
    <>
      <div className="mb-4 flex items-center gap-3">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-sunken" aria-hidden>
          <div className="h-full rounded-full bg-ok transition-all" style={{ width: `${(count / total) * 100}%` }} />
        </div>
        <span className="text-sm font-semibold">
          {count}/{total} done
        </span>
      </div>
      <ol className="grid gap-4 md:grid-cols-2">
        {PLAN.map((week) => (
          <li key={week.week} className="card p-5">
            <p className="text-xs font-bold tracking-wide text-accent uppercase">{week.week}</p>
            <h3 className="font-display text-lg font-semibold">{week.title}</h3>
            <ul className="mt-3 space-y-2">
              {week.days.map((task, i) => {
                const key = `${week.week}-${i}`;
                return (
                  <li key={key}>
                    <label className="flex cursor-pointer gap-2.5 text-sm">
                      <input
                        type="checkbox"
                        checked={Boolean(done[key])}
                        onChange={() => toggle(key)}
                        className="mt-0.5 size-4 shrink-0 accent-[var(--color-ok)]"
                      />
                      <span className={done[key] ? 'text-muted line-through' : ''}>{task}</span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-xs text-muted">Your ticks are saved in this browser.</p>
    </>
  );
}

function Template({ template, notify }) {
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(template.text);
      notify?.({ tone: 'success', message: 'Copied. Replace the {braces} before sending.' });
    } catch {
      notify?.({ tone: 'error', message: "Couldn't copy. Select the text and copy it instead." });
    }
  };
  return (
    <li className="card flex flex-col p-5">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="font-semibold">{template.title}</h3>
        <button
          type="button"
          onClick={copy}
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-line px-2.5 py-1 text-xs font-semibold hover:border-ink/40"
        >
          <Copy className="size-3.5" aria-hidden />
          Copy
        </button>
      </div>
      <pre className="flex-1 rounded-xl bg-sunken p-3 font-sans text-sm whitespace-pre-wrap">{template.text}</pre>
    </li>
  );
}

function BulletList({ items, icon: Icon = Check, tone = 'text-ok' }) {
  return (
    <ul className="card space-y-3 p-5">
      {items.map((item) => (
        <li key={item} className="flex gap-2.5 text-sm">
          <Icon className={`mt-0.5 size-4 shrink-0 ${tone}`} aria-hidden />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

/** Freelancing for students: what to sell (even with no skills), a 30-day plan, platforms, messages, payment, scams and tax. */
export default function EarnPage({ skills = [], notify }) {
  const resumeSkills = useMemo(() => new Set(skills.map((s) => String(s).toLowerCase())), [skills]);
  const matches = useMemo(
    () => new Set(SERVICES.filter((s) => s.skills.some((k) => resumeSkills.has(k))).map((s) => s.id)),
    [resumeSkills],
  );
  const [level, setLevel] = useState(() =>
    SERVICES.some((s) => s.level === 'tech' && matches.has(s.id)) ? 'tech' : 'zero',
  );
  const [open, setOpen] = useState(null);
  const shown = SERVICES.filter((s) => s.level === level).sort((a, b) => matches.has(b.id) - matches.has(a.id));

  return (
    <motion.main
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="mx-auto w-full max-w-6xl px-4 pt-8 pb-16 sm:px-6 sm:pt-10"
    >
      <p className="text-sm font-bold tracking-wide text-accent uppercase">Earn while you study</p>
      <h1 className="mt-1 font-display text-4xl font-bold tracking-tight sm:text-5xl">
        Your first freelance income, <span className="marker px-1">even from zero</span>
      </h1>
      <p className="mt-3 max-w-2xl text-lg text-muted">
        Pick one simple service, let free AI tools do the hard part, and follow a 30-day plan to your first paying client.
        No fees, no skills needed to start.
      </p>

      <div className="mt-5 flex max-w-3xl gap-3 rounded-2xl border border-line bg-card p-4 text-sm">
        <Sparkles className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
        <p>
          <span className="font-semibold">Honest expectations:</span> with about an hour a day, most beginners take 2–4 weeks to
          get their first small payment (often ₹200–1,000), and it grows with reviews. It is real work, not instant money.
          Anyone promising easy money for a fee is running a scam.
        </p>
      </div>

      <nav aria-label="On this page" className="mt-6 flex flex-wrap gap-2">
        {SECTIONS.map(([id, label]) => (
          <a key={id} href={`#${id}`} className="rounded-full border border-line px-3 py-1 text-sm font-semibold hover:border-ink/40">
            {label}
          </a>
        ))}
      </nav>

      <Section id="services" icon={Store} title="1. Pick what to sell" subtitle="Choose where you are starting. Open a card for the full how-to.">
        <div role="radiogroup" aria-label="Your starting point" className="mb-5 grid gap-2 sm:grid-cols-3">
          {LEVELS.map((l) => (
            <button
              key={l.id}
              type="button"
              role="radio"
              aria-checked={level === l.id}
              onClick={() => {
                setLevel(l.id);
                setOpen(null);
              }}
              className={`cursor-pointer rounded-2xl border p-4 text-left transition ${
                level === l.id ? 'border-ink bg-highlight/50 dark:bg-highlight/30' : 'border-line bg-card hover:border-ink/40'
              }`}
            >
              <span className="block font-semibold">{l.label}</span>
              <span className="mt-0.5 block text-sm text-muted">{l.hint}</span>
            </button>
          ))}
        </div>
        {matches.size > 0 && (
          <p className="mb-4 text-sm text-muted">
            Services marked <span className="font-semibold text-ok">Matches your resume</span> use skills from the resume you
            checked.
          </p>
        )}
        <ul className="grid gap-4 sm:grid-cols-2">
          {shown.map((service) => (
            <ServiceCard
              key={service.id}
              service={service}
              matched={matches.has(service.id)}
              open={open === service.id}
              onToggle={() => setOpen(open === service.id ? null : service.id)}
            />
          ))}
        </ul>
      </Section>

      <Section id="plan" icon={CalendarCheck} title="2. Your 30-day plan to the first ₹" subtitle="About an hour a day. Tick tasks off as you go.">
        <Plan />
      </Section>

      <Section id="platforms" icon={Store} title="3. Where to find clients" subtitle="Start local or with one platform. Fees change, so check before you price.">
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {PLATFORMS.map((p) => (
            <li key={p.name} className="card p-4 text-sm">
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold">{p.url ? <ExternalLink href={p.url}>{p.name}</ExternalLink> : p.name}</h3>
                {p.beginner && (
                  <span className="shrink-0 rounded-full bg-ok-soft px-2 py-0.5 text-xs font-bold text-ok">Beginner-friendly</span>
                )}
              </div>
              <p className="mt-1.5">{p.best}</p>
              <p className="mt-1.5 text-muted">Fee: {p.fee}</p>
            </li>
          ))}
        </ul>
      </Section>

      <Section id="templates" icon={Copy} title="4. Messages that get replies" subtitle="Copy, replace the {braces}, and personalise the first line.">
        <ul className="grid gap-4 md:grid-cols-2">
          {TEMPLATES.map((t) => (
            <Template key={t.id} template={t} notify={notify} />
          ))}
        </ul>
      </Section>

      <Section id="pricing" icon={IndianRupee} title="5. Pricing">
        <BulletList items={PRICING} />
      </Section>

      <Section id="ai" icon={Bot} title="6. Using AI the right way" subtitle="AI lets you start without skills. Checking its work is what clients pay you for.">
        <ul className="card grid gap-3 p-5 sm:grid-cols-2">
          {AI_RULES.map((rule) => (
            <li key={rule.text} className="flex gap-2.5 text-sm">
              {rule.ok ? (
                <Check className="mt-0.5 size-4 shrink-0 text-ok" aria-label="Do" />
              ) : (
                <X className="mt-0.5 size-4 shrink-0 text-pen" aria-label="Don't" />
              )}
              <span>{rule.text}</span>
            </li>
          ))}
        </ul>
      </Section>

      <Section id="paid" icon={Landmark} title="7. Getting paid in India">
        <ul className="grid gap-3 sm:grid-cols-2">
          {PAYMENTS.map((p) => (
            <li key={p.title} className="card p-4 text-sm">
              <h3 className="font-semibold">{p.title}</h3>
              <p className="mt-1">{p.text}</p>
            </li>
          ))}
        </ul>
      </Section>

      <Section id="scams" icon={ShieldAlert} title="8. Scams to avoid" subtitle="If someone asks you to pay to earn, stop. Report cyber fraud at cybercrime.gov.in or call 1930.">
        <BulletList items={SCAMS} icon={ShieldAlert} tone="text-pen" />
      </Section>

      <Section id="tax" icon={Receipt} title="9. Tax basics" subtitle="General information, not tax advice. Ask a CA when your income grows.">
        <BulletList items={TAX} />
        <p className="mt-3 text-sm">
          <ExternalLink href="https://www.incometax.gov.in">Income Tax Department e-filing</ExternalLink>
        </p>
      </Section>
    </motion.main>
  );
}
