import { motion } from 'framer-motion';
import { Moon, ScanSearch, Sun } from 'lucide-react';
import { HOME, TOOLS } from '../../lib/tools';
import UserMenu from '../auth/UserMenu';

function Link({ path, onNavigate, className, children, ...props }) {
  return (
    <a
      href={path}
      onClick={(e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey) return;
        e.preventDefault();
        onNavigate(path);
      }}
      className={className}
      {...props}
    >
      {children}
    </a>
  );
}

/** Top bar: logo, tool links (desktop) and the theme switch; a bottom tab bar on phones. */
export default function Header({ dark, onToggleTheme, page, onNavigate, notify }) {
  return (
    <>
      <header className="sticky top-0 z-40 border-b border-line/70 bg-paper/80 backdrop-blur-md print:hidden">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link path="/" onNavigate={onNavigate} className="group flex items-center gap-2.5" aria-label="FitLens home">
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
          </Link>

          <nav aria-label="Tools" className="hidden items-center gap-1 md:flex">
            {TOOLS.map((tool) => {
              const active = page === tool.id;
              return (
                <Link
                  key={tool.id}
                  path={tool.path}
                  onNavigate={onNavigate}
                  aria-current={active ? 'page' : undefined}
                  className={`relative rounded-xl px-3 py-2 text-sm font-semibold transition-colors ${
                    active ? 'text-ink' : 'text-muted hover:text-ink'
                  }`}
                >
                  {active && (
                    <motion.span
                      layoutId="nav-marker"
                      className="absolute inset-0 rounded-xl bg-highlight/70 dark:bg-highlight/50"
                      transition={{ type: 'spring', stiffness: 420, damping: 32 }}
                    />
                  )}
                  <span className="relative">{tool.short}</span>
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-2">
          <UserMenu onNavigate={onNavigate} notify={notify} />
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
        </div>
      </header>

      {/* Phones: app-style bottom tab bar */}
      <nav
        aria-label="Tools"
        className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-card/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden print:hidden"
      >
        <ul className="grid grid-cols-5">
          {[HOME, ...TOOLS].map((tool) => {
            const active = page === tool.id;
            const Icon = tool.icon;
            return (
              <li key={tool.id}>
                <Link
                  path={tool.path}
                  onNavigate={onNavigate}
                  aria-current={active ? 'page' : undefined}
                  className={`flex flex-col items-center gap-0.5 py-2 text-[11px] font-semibold ${active ? 'text-ink' : 'text-muted'}`}
                >
                  <span className={`grid h-7 w-12 place-items-center rounded-full transition ${active ? 'bg-highlight/70 dark:bg-highlight/50' : ''}`}>
                    <Icon className="size-4.5" aria-hidden />
                  </span>
                  {tool.short}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </>
  );
}
