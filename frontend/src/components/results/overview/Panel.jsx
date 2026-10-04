import { motion } from 'framer-motion';
import { reveal } from '../../../lib/motion';

/** A card with a consistent heading row: title, optional subtitle and right-hand slot. */
export default function Panel({ title, subtitle, aside, className = '', children }) {
  return (
    <motion.section variants={reveal} className={`card p-5 sm:p-6 ${className}`}>
      {(title || aside) && (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && <h3 className="font-display text-lg font-semibold">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
          </div>
          {aside}
        </header>
      )}
      {children}
    </motion.section>
  );
}

/** Small uppercase label with a rule, separating groups of panels. */
export function SectionLabel({ children }) {
  return (
    <div className="flex items-center gap-3 pt-2 lg:col-span-full">
      <span className="text-xs font-bold tracking-[0.14em] text-muted uppercase">{children}</span>
      <span className="h-px flex-1 bg-line" />
    </div>
  );
}
