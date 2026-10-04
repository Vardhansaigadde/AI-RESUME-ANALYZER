// Saved data for signed-in users (tables in supabase/schema.sql). Every call is
// scoped to the signed-in user by row-level security; user_id defaults to auth.uid().
import { supabase } from './supabase';

function check({ data, error }) {
  if (error) throw new Error(error.message || 'Could not reach your account. Please try again.');
  return data;
}

// Resumes ------------------------------------------------------------------------

export async function listResumes() {
  return check(
    await supabase.from('resumes').select('id, title, template, accent, updated_at').order('updated_at', { ascending: false }),
  );
}

export async function loadResume(id) {
  return check(await supabase.from('resumes').select('*').eq('id', id).single());
}

/** Insert (no id) or update a resume; returns the saved row. */
export async function saveResume({ id, title, template, accent, data }) {
  const row = { title: (title || 'My resume').slice(0, 80), template, accent: accent || null, data };
  const query = id
    ? supabase.from('resumes').update(row).eq('id', id)
    : supabase.from('resumes').insert(row);
  return check(await query.select('id, title, template, accent, updated_at').single());
}

export async function deleteResume(id) {
  check(await supabase.from('resumes').delete().eq('id', id));
}

// Learning progress ----------------------------------------------------------------

export async function loadProgress() {
  return check(await supabase.from('learning_progress').select('progress, hours_per_week').maybeSingle());
}

export async function saveProgress(progress, hoursPerWeek) {
  check(
    await supabase
      .from('learning_progress')
      .upsert({ progress, hours_per_week: hoursPerWeek }, { onConflict: 'user_id' }),
  );
}

// Job applications ---------------------------------------------------------------

export const STAGES = [
  { id: 'saved', label: 'Saved' },
  { id: 'applied', label: 'Applied' },
  { id: 'interview', label: 'Interview' },
  { id: 'offer', label: 'Offer' },
  { id: 'rejected', label: 'Not this time' },
];

export async function listApplications() {
  return check(await supabase.from('applications').select('*').order('updated_at', { ascending: false }));
}

/** Save a job to the tracker (once per URL); returns the row. */
export async function saveApplication(job) {
  const snapshot = {
    title: job.title,
    company: job.company || '',
    location: job.location || '',
    source: job.source || '',
    fit_score: job.fit_score ?? null,
    posted: job.posted || '',
  };
  return check(
    await supabase
      .from('applications')
      .upsert({ url: job.url, job: snapshot }, { onConflict: 'user_id,url', ignoreDuplicates: false })
      .select()
      .single(),
  );
}

export async function updateApplication(id, patch) {
  return check(await supabase.from('applications').update(patch).eq('id', id).select().single());
}

export async function deleteApplication(id) {
  check(await supabase.from('applications').delete().eq('id', id));
}
