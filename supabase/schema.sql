-- FitLens accounts: run once in Supabase → SQL Editor → New query → Run.
-- Safe to run again: it only creates what is missing.
--
-- Signing in is optional. Signed-in users can save resumes, roadmap progress
-- and tracked job applications. Row-level security makes sure every user can
-- only read and change their own rows, even though the browser talks to the
-- database directly with the public anon key.

-- Resumes (a user can keep several versions, e.g. one per role) -------------
create table if not exists public.resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  title text not null default 'My resume' check (char_length(title) <= 80),
  template text not null default 'campus' check (char_length(template) <= 40),
  accent text check (accent is null or accent ~ '^#[0-9a-fA-F]{6}$'),
  data jsonb not null default '{}'::jsonb check (pg_column_size(data) < 200000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists resumes_user_idx on public.resumes (user_id, updated_at desc);

-- Learning roadmap progress (one row per user) --------------------------------
create table if not exists public.learning_progress (
  user_id uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  progress jsonb not null default '{}'::jsonb check (pg_column_size(progress) < 50000),
  hours_per_week smallint not null default 8 check (hours_per_week between 1 and 80),
  updated_at timestamptz not null default now()
);

-- Job applications (the tracker) ------------------------------------------------
create table if not exists public.applications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  url text not null check (char_length(url) <= 1000),
  job jsonb not null default '{}'::jsonb check (pg_column_size(job) < 20000),
  status text not null default 'saved'
    check (status in ('saved', 'applied', 'interview', 'offer', 'rejected')),
  notes text not null default '' check (char_length(notes) <= 2000),
  deadline date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, url)
);
create index if not exists applications_user_idx on public.applications (user_id, updated_at desc);

-- Keep updated_at current ---------------------------------------------------------
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists resumes_touch on public.resumes;
create trigger resumes_touch before update on public.resumes
  for each row execute function public.touch_updated_at();
drop trigger if exists learning_progress_touch on public.learning_progress;
create trigger learning_progress_touch before update on public.learning_progress
  for each row execute function public.touch_updated_at();
drop trigger if exists applications_touch on public.applications;
create trigger applications_touch before update on public.applications
  for each row execute function public.touch_updated_at();

-- Row-level security: each user sees and changes only their own rows ------------
alter table public.resumes enable row level security;
alter table public.learning_progress enable row level security;
alter table public.applications enable row level security;

drop policy if exists "own resumes" on public.resumes;
create policy "own resumes" on public.resumes
  for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "own progress" on public.learning_progress;
create policy "own progress" on public.learning_progress
  for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "own applications" on public.applications;
create policy "own applications" on public.applications
  for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

-- Nobody who isn't signed in can touch these tables
revoke all on public.resumes, public.learning_progress, public.applications from anon;
grant select, insert, update, delete on public.resumes, public.learning_progress, public.applications to authenticated;

-- "Delete my account": removes the user; their rows go with it (on delete cascade)
create or replace function public.delete_my_account()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'Not signed in';
  end if;
  delete from auth.users where id = auth.uid();
end;
$$;

revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
