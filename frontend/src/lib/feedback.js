// Feedback from the "Was this helpful?" buttons and the footer form, saved by
// supabase/feedback.sql. Only the page, thumbs, the typed message and an email
// the visitor chose to give are sent: never resume content.
import { visitorId } from './analytics';
import { readStorage, writeStorage } from './storage';
import { supabase } from './supabase';

const ASKED_KEY = 'fitlens:feedback-given';

export const feedbackEnabled = Boolean(supabase);

/** Pages where the visitor already answered, so we never ask twice. */
export function alreadyAnswered(page) {
  return Boolean(readStorage(ASKED_KEY, {})[page]);
}

export function markAnswered(page) {
  writeStorage(ASKED_KEY, { ...readStorage(ASKED_KEY, {}), [page]: true });
}

/** Returns true when saved. Never throws. */
export async function sendFeedback({ page, kind, rating = null, message = null, contact = null }) {
  const id = visitorId();
  if (!supabase || !id) return false;
  try {
    const { data, error } = await supabase.rpc('submit_feedback', {
      visitor_key: id,
      page_name: page,
      feedback_kind: kind,
      thumbs: rating,
      feedback_message: message,
      reply_to: contact,
    });
    return !error && data === true;
  } catch {
    return false;
  }
}
