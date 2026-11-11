import { MessageSquare, ThumbsDown, ThumbsUp, X } from 'lucide-react';
import { useId, useState } from 'react';
import { alreadyAnswered, feedbackEnabled, markAnswered, sendFeedback } from '../../lib/feedback';
import Button from './Button';

/** Message box with an optional email. Used after a thumbs click and in the footer form. */
function MessageForm({ placeholder, onSend, onCancel, cancelLabel = 'Skip' }) {
  const id = useId();
  const [message, setMessage] = useState('');
  const [contact, setContact] = useState('');
  const [sending, setSending] = useState(false);
  const [failed, setFailed] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    setSending(true);
    setFailed(false);
    const ok = await onSend({ message: message.trim(), contact: contact.trim() || null });
    setSending(false);
    if (!ok) setFailed(true);
  };

  return (
    <form onSubmit={submit} className="mt-3 space-y-2">
      <label htmlFor={`${id}-msg`} className="sr-only">
        Your feedback
      </label>
      <textarea
        id={`${id}-msg`}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        maxLength={1000}
        rows={3}
        placeholder={placeholder}
        className="field w-full resize-y"
      />
      <label htmlFor={`${id}-contact`} className="sr-only">
        Email (optional)
      </label>
      <input
        id={`${id}-contact`}
        type="email"
        value={contact}
        onChange={(e) => setContact(e.target.value)}
        maxLength={200}
        placeholder="Email, only if you want a reply (optional)"
        className="field w-full"
      />
      <p className="text-xs text-muted">Please don't paste your resume or personal details. Your email is used only to reply.</p>
      {failed && <p className="text-xs text-pen">Couldn't send right now. Please try again in a moment.</p>}
      <div className="flex gap-2">
        <Button type="submit" size="sm" loading={sending} disabled={!message.trim()}>
          Send
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>
          {cancelLabel}
        </Button>
      </div>
    </form>
  );
}

/**
 * A quiet "Was this helpful?" line at the end of a page. Nothing pops up: it only
 * opens a message box after a click, and a page that was answered never asks again.
 */
export function HelpfulPrompt({ page, question = 'Was this helpful?' }) {
  const [step, setStep] = useState(() => (alreadyAnswered(page) ? 'hidden' : 'ask'));
  const [rating, setRating] = useState(null);
  if (!feedbackEnabled || step === 'hidden') return null;

  const rate = (value) => {
    setRating(value);
    setStep('details');
    markAnswered(page);
    sendFeedback({ page, kind: 'rating', rating: value });
  };

  return (
    <div className="mx-auto mt-12 max-w-xl rounded-2xl border border-line px-4 py-3 text-sm print:hidden">
      {step === 'ask' && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          <span className="text-muted">{question}</span>
          <div className="flex gap-1.5">
            <button
              type="button"
              onClick={() => rate(1)}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 font-semibold hover:border-ok hover:text-ok"
            >
              <ThumbsUp className="size-4" aria-hidden /> Yes
            </button>
            <button
              type="button"
              onClick={() => rate(-1)}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 font-semibold hover:border-pen hover:text-pen"
            >
              <ThumbsDown className="size-4" aria-hidden /> No
            </button>
          </div>
        </div>
      )}
      {step === 'details' && (
        <div>
          <p className="font-semibold">Thanks! {rating > 0 ? 'What helped most?' : 'What was missing or confusing?'}</p>
          <p className="text-xs text-muted">Optional. One line is enough.</p>
          <MessageForm
            placeholder={rating > 0 ? 'What should we keep or add?' : 'What should we fix?'}
            onSend={async (data) => {
              const ok = await sendFeedback({ page, kind: 'message', rating, ...data });
              if (ok) setStep('done');
              return ok;
            }}
            onCancel={() => setStep('done')}
          />
        </div>
      )}
      {step === 'done' && <p className="text-center text-muted">Thank you. It really helps us improve FitLens.</p>}
    </div>
  );
}

/** "Feedback" in the footer: opens a small form in place, only when clicked. */
export function FooterFeedback() {
  const [open, setOpen] = useState(false);
  const [sent, setSent] = useState(false);
  if (!feedbackEnabled) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setOpen(!open);
          setSent(false);
        }}
        aria-expanded={open}
        className="inline-flex cursor-pointer items-center gap-1 hover:text-ink"
      >
        <MessageSquare className="size-3.5" aria-hidden />
        Feedback
      </button>
      {open && (
        <div className="card fixed inset-x-4 bottom-20 z-50 mx-auto max-w-md p-4 text-sm text-ink shadow-[var(--shadow-lift)] md:bottom-6">
          <div className="flex items-start justify-between gap-2">
            <p className="font-semibold">{sent ? 'Thank you!' : 'Tell us what to fix or add'}</p>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="grid size-7 cursor-pointer place-items-center rounded-lg text-muted hover:bg-sunken"
              aria-label="Close feedback"
            >
              <X className="size-4" aria-hidden />
            </button>
          </div>
          {sent ? (
            <p className="mt-1 text-muted">We read every message.</p>
          ) : (
            <MessageForm
              placeholder="A bug, an idea, something confusing…"
              cancelLabel="Cancel"
              onSend={async (data) => {
                const ok = await sendFeedback({ page: 'site', kind: 'message', ...data });
                if (ok) setSent(true);
                return ok;
              }}
              onCancel={() => setOpen(false)}
            />
          )}
        </div>
      )}
    </>
  );
}
