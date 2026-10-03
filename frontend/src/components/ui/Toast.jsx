import { AnimatePresence, motion } from 'framer-motion';
import { CircleAlert, CircleCheck, X } from 'lucide-react';
import { useEffect } from 'react';

/** Top-centred toast. `toast` is { message, tone: 'error' | 'success' } or null. */
export default function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(onClose, toast.tone === 'success' ? 3500 : 7000);
    return () => clearTimeout(timer);
  }, [toast, onClose]);

  const error = toast?.tone !== 'success';
  const Icon = error ? CircleAlert : CircleCheck;

  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex justify-center px-4">
      <AnimatePresence>
        {toast && (
          <motion.div
            key={toast.message}
            role={error ? 'alert' : 'status'}
            initial={{ y: -40, opacity: 0, rotate: -2 }}
            animate={{ y: 0, opacity: 1, rotate: 0 }}
            exit={{ y: -30, opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 400, damping: 26 }}
            className={`pointer-events-auto flex max-w-xl items-start gap-3 rounded-2xl border px-4 py-3 text-sm font-medium shadow-[var(--shadow-lift)] ${
              error ? 'border-pen/30 bg-pen-soft text-ink' : 'border-ok/30 bg-ok-soft text-ink'
            }`}
          >
            <Icon className={`mt-0.5 size-4 shrink-0 ${error ? 'text-pen' : 'text-ok'}`} aria-hidden />
            <span className="flex-1">{toast.message}</span>
            <button type="button" onClick={onClose} aria-label="Dismiss" className="cursor-pointer rounded-md p-0.5 text-muted hover:text-ink">
              <X className="size-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
