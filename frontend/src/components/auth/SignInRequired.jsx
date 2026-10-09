import { motion } from 'framer-motion';
import { Lock, LogIn } from 'lucide-react';
import { useAuth } from '../../lib/authContext';
import Button from '../ui/Button';

/**
 * Shown instead of a tool that needs an account. `page` wraps it in a full page
 * (with the tool's title); without it, it renders as a card inside a page.
 */
export default function SignInRequired({ title, text, reason, page = false, icon: Icon = Lock }) {
  const { openSignIn } = useAuth();
  const card = (
    <div className="card mt-8 flex flex-col items-center p-10 text-center">
      <span className="grid size-12 place-items-center rounded-2xl bg-accent-soft text-accent">
        <Icon className="size-6" aria-hidden />
      </span>
      <h2 className="mt-4 font-display text-2xl font-semibold">Sign in to use {title}</h2>
      <p className="mt-2 max-w-md text-sm text-muted">{text}</p>
      <Button variant="primary" icon={LogIn} className="mt-5" onClick={() => openSignIn(reason || text)}>
        Sign in free
      </Button>
      <p className="mt-3 text-xs text-muted">Google or an email link. Checking your resume works without an account.</p>
    </div>
  );
  if (!page) return card;
  return (
    <motion.main
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="mx-auto w-full max-w-6xl px-4 pt-8 sm:px-6 sm:pt-10"
    >
      <h1 className="font-display text-4xl font-bold tracking-tight">{title}</h1>
      {card}
    </motion.main>
  );
}
