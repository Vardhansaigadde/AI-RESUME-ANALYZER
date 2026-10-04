import { AnimatePresence, motion } from 'framer-motion';
import { ArrowDown, ArrowUp, Check, Plus, Sparkles, Trash2, TriangleAlert, X } from 'lucide-react';
import { useId, useState } from 'react';
import { coachBullet } from '../../../lib/bulletCoach';
import { newId } from '../../../lib/resume';
import { formatSkill } from '../../../utils/format';
import Button from '../../ui/Button';

export function TextField({ label, value, onChange, placeholder, type = 'text', multiline = false, rows = 3 }) {
  const id = useId();
  const Tag = multiline ? 'textarea' : 'input';
  return (
    <div>
      <label htmlFor={id} className="label">
        {label}
      </label>
      <Tag
        id={id}
        type={multiline ? undefined : type}
        rows={multiline ? rows : undefined}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className={`field ${multiline ? 'resize-y leading-relaxed' : ''}`}
      />
    </div>
  );
}

/** Chip input: Enter or comma adds, × removes. `suggestions` are one-click additions. */
export function TagInput({ label, tags, onChange, placeholder, suggestions = [], suggestionsLabel }) {
  const id = useId();
  const [draft, setDraft] = useState('');
  const has = (t) => tags.some((x) => x.toLowerCase() === t.toLowerCase());
  const add = (raw) => {
    const items = raw
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);
    const fresh = items.filter((t, i) => !has(t) && items.findIndex((x) => x.toLowerCase() === t.toLowerCase()) === i);
    if (fresh.length) onChange([...tags, ...fresh]);
    setDraft('');
  };
  const open = suggestions.filter((s) => !has(formatSkill(s)) && !has(s));

  return (
    <div>
      <label htmlFor={id} className="label">
        {label}
      </label>
      <div className="field flex flex-wrap items-center gap-1.5 py-2">
        <AnimatePresence initial={false}>
          {tags.map((tag) => (
            <motion.span
              key={tag}
              layout
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.6, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 500, damping: 25 }}
              className="inline-flex items-center gap-1 rounded-lg bg-highlight/60 py-1 pr-1 pl-2 text-sm font-medium"
            >
              {tag}
              <button
                type="button"
                onClick={() => onChange(tags.filter((t) => t !== tag))}
                className="cursor-pointer rounded p-0.5 text-ink/60 hover:bg-ink/10 hover:text-ink"
                aria-label={`Remove ${tag}`}
              >
                <X className="size-3" />
              </button>
            </motion.span>
          ))}
        </AnimatePresence>
        <input
          id={id}
          value={draft}
          placeholder={tags.length ? 'Add more…' : placeholder}
          onChange={(e) => (e.target.value.endsWith(',') ? add(e.target.value) : setDraft(e.target.value))}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              add(draft);
            } else if (e.key === 'Backspace' && !draft && tags.length) {
              onChange(tags.slice(0, -1));
            }
          }}
          onBlur={() => draft.trim() && add(draft)}
          className="min-w-32 flex-1 bg-transparent py-1 text-sm outline-none"
        />
      </div>
      {open.length > 0 && (
        <div className="mt-2.5">
          <p className="mb-1.5 text-xs text-muted">{suggestionsLabel}</p>
          <div className="flex flex-wrap gap-1.5">
            {open.map((s) => (
              <motion.button
                key={s}
                type="button"
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.92 }}
                onClick={() => onChange([...tags, formatSkill(s)])}
                className="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-dashed border-pen/50 px-2 py-1 text-xs font-semibold text-pen hover:bg-pen-soft"
              >
                <Plus className="size-3" aria-hidden />
                {formatSkill(s)}
              </motion.button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/** Editable list of one-line items (bullets, certifications, links...). */
export function LineList({ label, items, onChange, placeholder, addLabel = 'Add', multiline = false, coach = false }) {
  const update = (i, value) => onChange(items.map((x, j) => (j === i ? value : x)));
  const Tag = multiline ? 'textarea' : 'input';
  return (
    <div>
      {label && <p className="label">{label}</p>}
      <ul className="space-y-2">
        <AnimatePresence initial={false}>
          {items.map((item, i) => (
            <motion.li
              key={i}
              layout
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="flex items-start gap-2"
            >
              {multiline && <span className="mt-3 size-1.5 shrink-0 rounded-full bg-ink/50" aria-hidden />}
              <div className="min-w-0 flex-1">
                <Tag
                  value={item}
                  rows={multiline ? 2 : undefined}
                  aria-label={`${label || addLabel} ${i + 1}`}
                  placeholder={placeholder}
                  onChange={(e) => update(i, e.target.value)}
                  className={`field ${multiline ? 'resize-y py-2 leading-relaxed' : 'py-2'}`}
                />
                {coach && <BulletFeedback text={item} />}
              </div>
              <button
                type="button"
                onClick={() => onChange(items.filter((_, j) => j !== i))}
                className="mt-1.5 cursor-pointer rounded-lg p-1.5 text-muted hover:bg-pen-soft hover:text-pen"
                aria-label={`Remove item ${i + 1}`}
              >
                <X className="size-4" />
              </button>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
      <Button variant="ghost" size="sm" icon={Plus} className="mt-2" onClick={() => onChange([...items, ''])}>
        {addLabel}
      </Button>
    </div>
  );
}

const LEVEL = {
  strong: { label: 'Strong', icon: Sparkles, className: 'bg-ok-soft text-ok' },
  ok: { label: 'Good', icon: Check, className: 'bg-accent-soft text-accent' },
  weak: { label: 'Needs work', icon: TriangleAlert, className: 'bg-warn-soft text-warn' },
};

/** Live bullet-coach feedback shown under a bullet while it is edited. */
function BulletFeedback({ text }) {
  const result = coachBullet(text);
  if (result.level === 'empty') return null;
  const level = LEVEL[result.level];
  const Icon = level.icon;
  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs" aria-live="polite">
      <motion.span
        key={result.level}
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 500, damping: 18 }}
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-bold ${level.className}`}
      >
        <Icon className="size-3" aria-hidden />
        {level.label}
      </motion.span>
      {result.good.map((g) => (
        <span key={g} className="text-ok">
          ✓ {g}
        </span>
      ))}
      {result.issues.map((issue) => (
        <span key={issue} className="text-warn">
          • {issue}
        </span>
      ))}
      {result.tip && <span className="w-full text-muted">{result.tip}</span>}
    </div>
  );
}

/** Cards for experience / projects / education entries. */
export function EntryList({ entries, onChange, titleLabel, subtitleLabel, titlePlaceholder, subtitlePlaceholder, addLabel }) {
  const update = (id, patch) => onChange(entries.map((e) => (e._id === id ? { ...e, ...patch } : e)));
  const move = (index, delta) => {
    const next = [...entries];
    const [item] = next.splice(index, 1);
    next.splice(index + delta, 0, item);
    onChange(next);
  };

  return (
    <div>
      <ul className="space-y-3">
        <AnimatePresence initial={false}>
          {entries.map((entry, i) => (
            <motion.li
              key={entry._id}
              layout
              initial={{ opacity: 0, y: -10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, rotate: 2 }}
              transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              className="rounded-2xl border border-line bg-sunken/40 p-4"
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="font-mono text-xs text-muted">#{i + 1}</span>
                <div className="flex gap-1">
                  <button
                    type="button"
                    disabled={i === 0}
                    onClick={() => move(i, -1)}
                    className="cursor-pointer rounded-lg p-1.5 text-muted hover:bg-card hover:text-ink disabled:opacity-30"
                    aria-label="Move up"
                  >
                    <ArrowUp className="size-4" />
                  </button>
                  <button
                    type="button"
                    disabled={i === entries.length - 1}
                    onClick={() => move(i, 1)}
                    className="cursor-pointer rounded-lg p-1.5 text-muted hover:bg-card hover:text-ink disabled:opacity-30"
                    aria-label="Move down"
                  >
                    <ArrowDown className="size-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onChange(entries.filter((e) => e._id !== entry._id))}
                    className="cursor-pointer rounded-lg p-1.5 text-muted hover:bg-pen-soft hover:text-pen"
                    aria-label={`Remove ${entry.title || 'entry'}`}
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <TextField label={titleLabel} value={entry.title} placeholder={titlePlaceholder} onChange={(v) => update(entry._id, { title: v })} />
                <TextField label={subtitleLabel} value={entry.subtitle} placeholder={subtitlePlaceholder} onChange={(v) => update(entry._id, { subtitle: v })} />
              </div>
              <div className="mt-3">
                <LineList
                  label="Bullet points"
                  items={entry.bullets}
                  multiline
                  placeholder="Start with a verb and add a number, e.g. Built a portal used by 300+ students"
                  addLabel="Add bullet"
                  coach
                  onChange={(bullets) => update(entry._id, { bullets })}
                />
              </div>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
      <Button
        variant="secondary"
        size="sm"
        icon={Plus}
        className="mt-3"
        onClick={() => onChange([...entries, { _id: newId(), title: '', subtitle: '', bullets: [''] }])}
      >
        {addLabel}
      </Button>
    </div>
  );
}
