// Supabase client for optional sign-in and saved data. The anon key is public by
// design; row-level security in supabase/schema.sql keeps each user's rows private.
// Without the two env vars (e.g. in CI), accounts are simply switched off.
import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase =
  url && key
    ? createClient(url, key, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, flowType: 'pkce' },
      })
    : null;

export const authEnabled = Boolean(supabase);
