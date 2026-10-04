import { AnimatePresence, motion } from 'framer-motion';
import { ClipboardList, LogIn, LogOut, Trash2, UserRound } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../../lib/authContext';

function Avatar({ user, size = 'size-9' }) {
  const photo = user.user_metadata?.avatar_url || user.user_metadata?.picture;
  const initial = (user.user_metadata?.full_name || user.email || '?').trim()[0]?.toUpperCase();
  return photo ? (
    <img src={photo} alt="" referrerPolicy="no-referrer" className={`${size} rounded-xl border border-line object-cover`} />
  ) : (
    <span className={`grid ${size} place-items-center rounded-xl bg-accent font-bold text-white`}>{initial}</span>
  );
}

/** "Sign in" for guests; an account menu for signed-in users. */
export default function UserMenu({ onNavigate, notify }) {
  const { user, ready, enabled, openSignIn, signOut, deleteAccount } = useAuth();
  const [open, setOpen] = useState(false);
  const box = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => !box.current?.contains(e.target) && setOpen(false);
    const onKey = (e) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (!enabled || !ready) return null;

  if (!user) {
    return (
      <button
        type="button"
        onClick={() => openSignIn()}
        className="inline-flex h-10 cursor-pointer items-center gap-1.5 rounded-xl border border-line bg-card px-3 text-sm font-semibold hover:border-ink/40"
      >
        <LogIn className="size-4" aria-hidden />
        <span className="hidden sm:inline">Sign in</span>
      </button>
    );
  }

  const remove = async () => {
    setOpen(false);
    const ok = window.confirm(
      'Delete your FitLens account? Your saved resumes, learning progress and tracked applications are deleted permanently. This cannot be undone.',
    );
    if (!ok) return;
    try {
      await deleteAccount();
      notify({ tone: 'success', message: 'Your account and all its data were deleted.' });
      onNavigate('/');
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    }
  };

  const item = 'flex w-full cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm hover:bg-sunken';
  return (
    <div ref={box} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="Account menu"
        className="cursor-pointer rounded-xl"
      >
        <Avatar user={user} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            role="menu"
            className="card absolute right-0 z-50 mt-2 w-64 p-1.5 shadow-[var(--shadow-lift)]"
          >
            <div className="flex items-center gap-3 px-3 py-2.5">
              <Avatar user={user} size="size-8" />
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">{user.user_metadata?.full_name || 'Signed in'}</p>
                <p className="truncate text-xs text-muted">{user.email}</p>
              </div>
            </div>
            <div className="my-1 h-px bg-line" />
            <button type="button" role="menuitem" className={item} onClick={() => { setOpen(false); onNavigate('/tracker'); }}>
              <ClipboardList className="size-4 text-muted" aria-hidden />
              My applications
            </button>
            <button type="button" role="menuitem" className={item} onClick={() => { setOpen(false); onNavigate('/build'); }}>
              <UserRound className="size-4 text-muted" aria-hidden />
              My resumes
            </button>
            <button type="button" role="menuitem" className={item} onClick={() => { setOpen(false); signOut(); }}>
              <LogOut className="size-4 text-muted" aria-hidden />
              Sign out
            </button>
            <div className="my-1 h-px bg-line" />
            <button type="button" role="menuitem" className={`${item} text-pen hover:bg-pen-soft`} onClick={remove}>
              <Trash2 className="size-4" aria-hidden />
              Delete account
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
