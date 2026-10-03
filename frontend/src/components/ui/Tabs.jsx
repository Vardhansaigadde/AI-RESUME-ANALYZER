import { motion } from 'framer-motion';

/**
 * Accessible tab list whose active marker is a highlighter stroke that
 * springs between tabs (shared layoutId).
 */
export default function Tabs({ tabs, active, onChange, idPrefix = 'tab' }) {
  const onKeyDown = (event) => {
    const index = tabs.findIndex((t) => t.id === active);
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault();
      const next = (index + (event.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length;
      onChange(tabs[next].id);
      document.getElementById(`${idPrefix}-${tabs[next].id}`)?.focus();
    }
  };

  return (
    <div role="tablist" aria-label="Result views" className="flex gap-1 rounded-2xl border border-line bg-card p-1.5" onKeyDown={onKeyDown}>
      {tabs.map(({ id, label, short, icon: Icon, badge }) => {
        const selected = id === active;
        return (
          <button
            key={id}
            id={`${idPrefix}-${id}`}
            role="tab"
            type="button"
            aria-selected={selected}
            aria-controls={`${idPrefix}-panel-${id}`}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(id)}
            className={`relative flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-xl px-2.5 py-2.5 text-sm font-semibold sm:px-4 whitespace-nowrap transition-colors ${
              selected ? 'text-ink' : 'text-muted hover:text-ink'
            }`}
          >
            {selected && (
              <motion.span
                layoutId={`${idPrefix}-marker`}
                className="absolute inset-0 rounded-xl bg-highlight/70 dark:bg-highlight/50"
                transition={{ type: 'spring', stiffness: 420, damping: 32 }}
              />
            )}
            <span className="relative flex items-center gap-2">
              {Icon && <Icon className="size-4" aria-hidden />}
              <span className="sm:hidden">{short || label}</span>
              <span className="hidden sm:inline">{label}</span>
              {badge != null && (
                <span className="rounded-full bg-ink/8 px-1.5 py-0.5 font-mono text-[11px] dark:bg-white/10">{badge}</span>
              )}
            </span>
          </button>
        );
      })}
    </div>
  );
}
