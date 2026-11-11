import { ArrowUpRight, Check, Copy } from 'lucide-react';

/** Building blocks shared by the long guides (Earn, Get a paid internship). */

export function Section({ id, icon: Icon, title, subtitle, children }) {
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

/** A link that opens another site in a new tab, or (for "/path" links) moves inside FitLens. */
export function ExternalLink({ href, children, className = '', onNavigate }) {
  const internal = href.startsWith('/');
  return (
    <a
      href={href}
      target={internal ? undefined : '_blank'}
      rel={internal ? undefined : 'noreferrer'}
      onClick={
        internal && onNavigate
          ? (e) => {
              e.preventDefault();
              onNavigate(href);
            }
          : undefined
      }
      className={`inline-flex items-center gap-1 font-semibold text-accent underline-offset-2 hover:underline ${className}`}
    >
      {children}
      {!internal && <ArrowUpRight className="size-3.5" aria-hidden />}
    </a>
  );
}

export function BulletList({ items, icon: Icon = Check, tone = 'text-ok' }) {
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

/** A message template with a Copy button. */
export function CopyCard({ title, text, notify }) {
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      notify?.({ tone: 'success', message: 'Copied. Replace the {braces} before sending.' });
    } catch {
      notify?.({ tone: 'error', message: "Couldn't copy. Select the text and copy it instead." });
    }
  };
  return (
    <li className="card flex flex-col p-5">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="font-semibold">{title}</h3>
        <button
          type="button"
          onClick={copy}
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-line px-2.5 py-1 text-xs font-semibold hover:border-ink/40"
        >
          <Copy className="size-3.5" aria-hidden />
          Copy
        </button>
      </div>
      <pre className="flex-1 rounded-xl bg-sunken p-3 font-sans text-sm whitespace-pre-wrap">{text}</pre>
    </li>
  );
}
