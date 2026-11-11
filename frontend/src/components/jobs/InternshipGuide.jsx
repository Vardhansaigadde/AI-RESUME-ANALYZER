import { ChevronDown, Mail, Rocket, ShieldAlert, Sparkles, Zap } from 'lucide-react';
import { useState } from 'react';
import { BOOSTERS, FIELDS, RED_FLAGS, ROUTES, SPEED, TEMPLATES, YEARS } from '../../lib/internshipGuide';
import { BulletList, CopyCard, ExternalLink, Section } from '../ui/Guide';

const SPEED_ORDER = { fast: 0, medium: 1, slow: 2 };
const SPEED_TONE = { fast: 'bg-ok-soft text-ok', medium: 'bg-accent-soft text-accent', slow: 'bg-warn-soft text-warn' };

function Chips({ label, options, value, onChange }) {
  return (
    <div role="radiogroup" aria-label={label} className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button
          key={o.id}
          type="button"
          role="radio"
          aria-checked={value === o.id}
          onClick={() => onChange(o.id)}
          className={`cursor-pointer rounded-full border px-3 py-1.5 text-sm font-semibold transition ${
            value === o.id ? 'border-ink bg-highlight/60 dark:bg-highlight/40' : 'border-line bg-card text-muted hover:border-ink/40'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function RouteCard({ route, open, onToggle, onNavigate }) {
  return (
    <li className={`card overflow-hidden ${open ? 'md:col-span-2' : ''}`}>
      <button type="button" onClick={onToggle} aria-expanded={open} className="flex w-full cursor-pointer items-start gap-3 p-5 text-left">
        <span className="flex-1">
          <span className={`mb-1.5 inline-block rounded-full px-2 py-0.5 text-xs font-bold ${SPEED_TONE[route.speed]}`}>
            {SPEED[route.speed]}
          </span>
          <span className="block font-display text-lg font-semibold">{route.title}</span>
          <span className="mt-1 block text-sm text-muted">{route.why}</span>
          <span className="mt-2 block text-sm">
            <span className="text-muted">Pay: </span>
            <span className="font-semibold">{route.pay}</span>
          </span>
        </span>
        <ChevronDown className={`mt-1 size-5 shrink-0 text-muted transition ${open ? 'rotate-180' : ''}`} aria-hidden />
      </button>
      {open && (
        <div className="grid gap-5 border-t border-line px-5 pt-4 pb-5 text-sm md:grid-cols-[2fr_1fr]">
          <ol className="list-decimal space-y-1.5 pl-5">
            {route.steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          {route.links.length > 0 && (
            <div className="flex flex-col items-start gap-1.5">
              <p className="text-xs font-bold tracking-wide text-muted uppercase">Official links</p>
              {route.links.map((link) => (
                <ExternalLink key={link.href} href={link.href} onNavigate={onNavigate}>
                  {link.label}
                </ExternalLink>
              ))}
            </div>
          )}
        </div>
      )}
    </li>
  );
}

const fits = (list, value) => value === 'any' || list.length === 0 || list.includes(value);

/** Every way to a paid internship, filtered by the student's year and field. */
export default function InternshipGuide({ notify, onNavigate }) {
  const [year, setYear] = useState('any');
  const [field, setField] = useState('any');
  const [open, setOpen] = useState(null);
  const routes = ROUTES.filter((r) => fits(r.years, year) && fits(r.fields, field)).sort(
    (a, b) => SPEED_ORDER[a.speed] - SPEED_ORDER[b.speed],
  );

  return (
    <div>
      <div className="flex max-w-3xl gap-3 rounded-2xl border border-line bg-card p-4 text-sm">
        <Sparkles className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
        <p>
          <span className="font-semibold">Use several routes at once.</span> Most students who land a paid internship combine
          quick applications (green) with one or two longer bets (yellow) like NPTEL, research fellowships or open source.
          Programs change dates and rules every year, so always check the official link.
        </p>
      </div>

      <Section id="routes" icon={Rocket} title="Ways to get a paid internship" subtitle="Pick your year and field. Fastest routes first.">
        <div className="mb-5 space-y-3">
          <Chips label="Your year" options={YEARS} value={year} onChange={setYear} />
          <Chips label="Your field" options={FIELDS} value={field} onChange={setField} />
        </div>
        <ul className="grid gap-4 md:grid-cols-2">
          {routes.map((route) => (
            <RouteCard
              key={route.id}
              route={route}
              open={open === route.id}
              onToggle={() => setOpen(open === route.id ? null : route.id)}
              onNavigate={onNavigate}
            />
          ))}
        </ul>
      </Section>

      <Section id="boosters" icon={Zap} title="Make every application count">
        <BulletList items={BOOSTERS} />
      </Section>

      <Section id="messages" icon={Mail} title="Emails and messages that get replies" subtitle="Copy, replace the {braces} and make the first line personal.">
        <ul className="grid gap-4 md:grid-cols-2">
          {TEMPLATES.map((t) => (
            <CopyCard key={t.id} title={t.title} text={t.text} notify={notify} />
          ))}
        </ul>
      </Section>

      <Section id="fake" icon={ShieldAlert} title="Fake internships to avoid" subtitle="Report fraud at cybercrime.gov.in or call 1930.">
        <BulletList items={RED_FLAGS} icon={ShieldAlert} tone="text-pen" />
      </Section>
    </div>
  );
}
