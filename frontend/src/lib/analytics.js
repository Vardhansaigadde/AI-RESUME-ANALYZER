// Anonymous usage counts for the site owner: which pages are opened each day, by
// how many browsers, and whether they were signed in. The browser gets a random
// id (no IP, no resume content); counts go to supabase/admin.sql's track_visit().
import { supabase } from './supabase';

const VISITOR_KEY = 'fitlens:visitor';
const TRACKED = new Set(['home', 'check', 'analysis', 'build', 'jobs', 'learn', 'tracker', 'privacy', 'terms']);

function visitorId() {
  try {
    let id = localStorage.getItem(VISITOR_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(VISITOR_KEY, id);
    }
    return id;
  } catch {
    return null; // storage blocked: this visit is simply not counted
  }
}

/** Count one page open. Never throws and never blocks the page. */
export function trackVisit(page) {
  if (!supabase || !TRACKED.has(page)) return;
  const id = visitorId();
  if (!id) return;
  supabase
    .rpc('track_visit', { visitor_key: id, page_name: page })
    .then(() => {}, () => {}); // counting is best effort
}
