import { AnimatePresence, motion } from 'framer-motion';
import { Cloud, Mail, MailCheck, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { AuthContext } from '../../lib/authContext';
import { supabase } from '../../lib/supabase';
import Button from '../ui/Button';

function GoogleLogo() {
  return (
    <svg viewBox="0 0 48 48" className="size-5" aria-hidden>
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 7.9 3l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z" />
      <path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.1 7.9 3l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z" />
    </svg>
  );
}

function SignInDialog({ open, reason, onClose }) {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  // Come back to the same page after signing in
  const redirectTo = () => `${window.location.origin}${window.location.pathname}`;

  const google = async () => {
    setBusy('google');
    setError('');
    const { error: err } = await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: redirectTo() } });
    if (err) {
      setError(err.message);
      setBusy(null);
    }
  };

  const magicLink = async (e) => {
    e.preventDefault();
    setBusy('email');
    setError('');
    const { error: err } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: redirectTo() },
    });
    setBusy(null);
    if (err) setError(err.message);
    else setSent(true);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[60] grid place-items-center bg-ink/40 p-4 backdrop-blur-sm"
          onClick={onClose}
          role="dialog"
          aria-modal="true"
          aria-labelledby="signin-title"
        >
          <motion.div
            initial={{ y: 20, scale: 0.97 }}
            animate={{ y: 0, scale: 1 }}
            exit={{ y: 20, scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
            onClick={(e) => e.stopPropagation()}
            className="card relative w-full max-w-sm p-6"
          >
            <button
              type="button"
              onClick={onClose}
              className="absolute top-3 right-3 grid size-8 cursor-pointer place-items-center rounded-lg text-muted hover:bg-sunken"
              aria-label="Close"
            >
              <X className="size-4" />
            </button>

            {sent ? (
              <div className="py-4 text-center">
                <MailCheck className="mx-auto size-10 text-ok" aria-hidden />
                <h2 id="signin-title" className="mt-3 font-display text-2xl font-semibold">
                  Check your inbox
                </h2>
                <p className="mt-2 text-sm text-muted">
                  We sent a sign-in link to <span className="font-semibold text-ink">{email}</span>. Open it on this device. It
                  may take a minute, and check spam if it doesn't arrive.
                </p>
              </div>
            ) : (
              <>
                <span className="grid size-11 place-items-center rounded-2xl bg-accent-soft text-accent">
                  <Cloud className="size-5" aria-hidden />
                </span>
                <h2 id="signin-title" className="mt-4 font-display text-2xl font-semibold">
                  Sign in to FitLens
                </h2>
                <p className="mt-1 text-sm text-muted">
                  {reason || 'Save your resumes, learning progress and job applications, and pick up on any device.'}
                </p>

                <Button variant="secondary" className="mt-5 w-full" onClick={google} loading={busy === 'google'}>
                  {busy !== 'google' && <GoogleLogo />}
                  Continue with Google
                </Button>

                <div className="my-4 flex items-center gap-3 text-xs text-muted">
                  <span className="h-px flex-1 bg-line" />
                  or
                  <span className="h-px flex-1 bg-line" />
                </div>

                <form onSubmit={magicLink}>
                  <label htmlFor="signin-email" className="label">
                    Email
                  </label>
                  <input
                    id="signin-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    autoComplete="email"
                    className="field w-full"
                  />
                  <Button type="submit" variant="primary" icon={Mail} className="mt-3 w-full" loading={busy === 'email'}>
                    Email me a sign-in link
                  </Button>
                </form>
                <p className="mt-4 text-center text-xs text-muted">No password needed. Checking your resume also works without an account.</p>
              </>
            )}
            {error && (
              <p role="alert" className="mt-3 rounded-xl bg-pen-soft px-3 py-2 text-sm text-pen">
                {error}
              </p>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/** Optional accounts: session state, the sign-in dialog, sign-out and account deletion. */
export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(!supabase);
  const [dialog, setDialog] = useState({ open: false, reason: '', id: 0 });

  useEffect(() => {
    if (!supabase) return undefined;
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null);
      setReady(true);
    });
    const { data } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);
      setReady(true);
      if (event === 'SIGNED_IN') {
        setDialog((d) => ({ ...d, open: false }));
        // Drop the one-time ?code= from the address bar after the sign-in redirect
        const url = new URL(window.location.href);
        if (url.searchParams.has('code')) {
          url.searchParams.delete('code');
          window.history.replaceState({}, '', url.pathname + url.search + url.hash);
        }
      }
    });
    return () => data.subscription.unsubscribe();
  }, []);

  // A new id remounts the dialog, so each opening starts clean
  const openSignIn = useCallback((reason = '') => setDialog((d) => ({ open: true, reason, id: d.id + 1 })), []);
  const closeSignIn = useCallback(() => setDialog((d) => ({ ...d, open: false })), []);

  const signOut = useCallback(async () => {
    await supabase?.auth.signOut();
  }, []);

  const deleteAccount = useCallback(async () => {
    const { error } = await supabase.rpc('delete_my_account');
    if (error) throw new Error(error.message);
    await supabase.auth.signOut();
  }, []);

  const value = useMemo(
    () => ({ user, ready, enabled: Boolean(supabase), openSignIn, signOut, deleteAccount }),
    [user, ready, openSignIn, signOut, deleteAccount],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
      {supabase && <SignInDialog key={dialog.id} open={dialog.open} reason={dialog.reason} onClose={closeSignIn} />}
    </AuthContext.Provider>
  );
}
