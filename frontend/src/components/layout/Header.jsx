import { motion } from 'framer-motion';
import { Moon, ScanSearch, Sun } from 'lucide-react';

export default function Header({ dark, onToggleTheme, onHome }) {
  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-paper/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <a
          href="/"
          onClick={(e) => {
            e.preventDefault();
            onHome();
          }}
          className="group flex items-center gap-2.5"
          aria-label="FitLens home"
        >
          <motion.span
            whileHover={{ rotate: -12, scale: 1.08 }}
            transition={{ type: 'spring', stiffness: 400, damping: 14 }}
            className="grid size-9 place-items-center rounded-xl bg-ink text-paper shadow-[0_3px_0_0_var(--color-accent)]"
          >
            <ScanSearch className="size-5" aria-hidden />
          </motion.span>
          <span className="font-display text-xl font-bold tracking-tight">
            Fit<span className="marker px-0.5">Lens</span>
          </span>
        </a>

        <motion.button
          type="button"
          onClick={onToggleTheme}
          whileTap={{ scale: 0.9, rotate: 20 }}
          className="grid size-10 cursor-pointer place-items-center rounded-xl border border-line bg-card text-ink hover:border-ink/40"
          aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
          title={dark ? 'Light theme' : 'Dark theme'}
        >
          <motion.span key={dark ? 'moon' : 'sun'} initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }}>
            {dark ? <Moon className="size-4.5" /> : <Sun className="size-4.5" />}
          </motion.span>
        </motion.button>
      </div>
    </header>
  );
}
