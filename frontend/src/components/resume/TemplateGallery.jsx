import { AnimatePresence, motion } from 'framer-motion';
import { Check, ShieldCheck, X } from 'lucide-react';
import { useEffect } from 'react';
import { TEMPLATES } from '../../lib/templates';
import ScaledPage from './ScaledPage';

/** Full-screen picker with a live thumbnail of every template. */
export default function TemplateGallery({ open, onClose, resume, selected, onSelect }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = overflow;
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 overflow-y-auto bg-ink/40 p-3 backdrop-blur-sm sm:p-6"
          onClick={onClose}
          role="dialog"
          aria-modal="true"
          aria-labelledby="gallery-title"
        >
          <motion.div
            initial={{ y: 24, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 24, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            onClick={(e) => e.stopPropagation()}
            className="card mx-auto max-w-6xl p-4 sm:p-6"
          >
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <h2 id="gallery-title" className="font-display text-2xl font-semibold">
                  Choose a template
                </h2>
                <p className="mt-1 flex items-center gap-1.5 text-sm text-muted">
                  <ShieldCheck className="size-4 text-ok" aria-hidden />
                  All {TEMPLATES.length} are ATS-friendly: one column, standard headings, no tables, icons or photos.
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="grid size-9 shrink-0 cursor-pointer place-items-center rounded-xl border border-line hover:border-ink/40"
                aria-label="Close"
              >
                <X className="size-4" />
              </button>
            </div>

            <ul className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
              {TEMPLATES.map((t) => {
                const active = t.id === selected;
                return (
                  <li key={t.id}>
                    <button
                      type="button"
                      onClick={() => {
                        onSelect(t.id);
                        onClose();
                      }}
                      aria-pressed={active}
                      className={`group w-full cursor-pointer rounded-2xl border-2 p-2 text-left transition ${
                        active ? 'border-accent bg-accent-soft/40' : 'border-transparent hover:border-line'
                      }`}
                    >
                      <div className="relative overflow-hidden rounded-lg shadow-[0_1px_4px_rgba(0,0,0,0.18)] transition group-hover:-translate-y-0.5">
                        <div className="h-64 overflow-hidden bg-white sm:h-72">
                          <ScaledPage resume={resume} templateId={t.id} />
                        </div>
                        {active && (
                          <span className="absolute top-2 right-2 grid size-7 place-items-center rounded-full bg-accent text-white">
                            <Check className="size-4" strokeWidth={3} aria-hidden />
                          </span>
                        )}
                      </div>
                      <div className="mt-2 px-1">
                        <span className="flex items-center gap-2 font-semibold">
                          {t.name}
                          <span className="size-2.5 rounded-full" style={{ background: t.accent }} aria-hidden />
                        </span>
                        <span className="mt-0.5 line-clamp-2 block text-xs text-muted">{t.description}</span>
                        <span className="mt-1.5 flex flex-wrap gap-1">
                          {t.best_for.map((tag) => (
                            <span key={tag} className="rounded-full bg-sunken px-2 py-0.5 text-[10px] font-semibold text-muted">
                              {tag}
                            </span>
                          ))}
                        </span>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
