-- FitLens usage counts and the private admin dashboard.
-- Run once in Supabase → SQL Editor → New query → Run (after schema.sql).
-- Safe to run again.
--
-- What is stored: for each day, a random id per browser (made in the browser,
-- no IP address, no resume content), the account id if the visitor was signed
-- in, and how many times each page was opened. Everything lives in the
-- "private" schema, which the website's public API cannot read at all.
--
-- Only accounts listed in private.admins get numbers back from site_stats();
-- everyone else gets null. Add yourself AFTER you have signed in to the site
-- once (replace the email, run it in the SQL editor, never commit it):
--
--   insert into private.admins (user_id)
--   select id from auth.users
--   where email = 'you@example.com' and email_confirmed_at is not null
--   on conflict do nothing;

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create table if not exists private.admins (
  user_id uuid primary key references auth.users (id) on delete cascade,
  added_at timestamptz not null default now()
);

-- One row per browser per day; user_id is set if they were signed in that day
create table if not exists private.daily_visitors (
  day date not null,
  visitor_id uuid not null,
  user_id uuid references auth.users (id) on delete set null,
  primary key (day, visitor_id)
);
create index if not exists daily_visitors_user_idx on private.daily_visitors (user_id, day);

-- Page opens per day, split by signed in or not
create table if not exists private.daily_events (
  day date not null,
  event text not null,
  signed_in boolean not null,
  hits integer not null default 0,
  primary key (day, event, signed_in)
);

revoke all on all tables in schema private from public, anon, authenticated;

-- Days follow Indian time
create or replace function private.today()
returns date
language sql
stable
set search_path = ''
as $$
  select (now() at time zone 'Asia/Kolkata')::date;
$$;

create or replace function private.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from private.admins a
    join auth.users u on u.id = a.user_id
    where a.user_id = auth.uid() and u.email_confirmed_at is not null
  );
$$;

-- Called by the website on each page open. It can only add counts.
drop function if exists public.track_visit(uuid, text);
create or replace function public.track_visit(visitor_key uuid, page_name text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  today date := private.today();
begin
  if visitor_key is null
    or page_name not in ('home', 'check', 'analysis', 'build', 'jobs', 'learn', 'tracker', 'privacy', 'terms') then
    return;
  end if;
  insert into private.daily_visitors (day, visitor_id, user_id)
  values (today, visitor_key, auth.uid())
  on conflict (day, visitor_id)
    do update set user_id = coalesce(private.daily_visitors.user_id, excluded.user_id);
  insert into private.daily_events (day, event, signed_in, hits)
  values (today, page_name, auth.uid() is not null, 1)
  on conflict (day, event, signed_in)
    do update set hits = private.daily_events.hits + 1;
end;
$$;

-- The admin dashboard's numbers; null for anyone who is not an admin
create or replace function public.site_stats()
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  today date := private.today();
begin
  if not private.is_admin() then
    return null;
  end if;

  return jsonb_build_object(
    'generated_at', now(),
    'users', jsonb_build_object(
      'total', (select count(*) from auth.users),
      'new_today', (select count(*) from auth.users where (created_at at time zone 'Asia/Kolkata')::date = today),
      'new_7d', (select count(*) from auth.users where (created_at at time zone 'Asia/Kolkata')::date > today - 7),
      'new_30d', (select count(*) from auth.users where (created_at at time zone 'Asia/Kolkata')::date > today - 30),
      'active_today', (select count(distinct user_id) from private.daily_visitors where day = today),
      'active_7d', (select count(distinct user_id) from private.daily_visitors where day > today - 7),
      'active_30d', (select count(distinct user_id) from private.daily_visitors where day > today - 30)
    ),
    'visitors', jsonb_build_object(
      'today', (select count(*) from private.daily_visitors where day = today and user_id is null),
      'last_7d', (select count(distinct visitor_id) from private.daily_visitors where day > today - 7 and user_id is null),
      'last_30d', (select count(distinct visitor_id) from private.daily_visitors where day > today - 30 and user_id is null),
      'all_time', (select count(distinct visitor_id) from private.daily_visitors where user_id is null)
    ),
    'daily', (
      select coalesce(jsonb_agg(jsonb_build_object('day', s.day, 'visitors', s.guests, 'users', s.users) order by s.day), '[]'::jsonb)
      from (
        select g.day,
          count(v.visitor_id) filter (where v.user_id is null) as guests,
          count(distinct v.user_id) as users
        from (select (today - n) as day from generate_series(0, 29) as n) g
        left join private.daily_visitors v on v.day = g.day
        group by g.day
      ) s
    ),
    'pages', (
      select coalesce(jsonb_object_agg(e.event, jsonb_build_object('guests', e.guests, 'users', e.users)), '{}'::jsonb)
      from (
        select event,
          coalesce(sum(hits) filter (where not signed_in), 0) as guests,
          coalesce(sum(hits) filter (where signed_in), 0) as users
        from private.daily_events
        where day > today - 30
        group by event
      ) e
    ),
    'saved', jsonb_build_object(
      'resumes', (select count(*) from public.resumes),
      'applications', (select count(*) from public.applications),
      'roadmaps', (select count(*) from public.learning_progress)
    )
  );
end;
$$;

revoke all on function private.today() from public, anon, authenticated;
revoke all on function private.is_admin() from public, anon, authenticated;
revoke all on function public.track_visit(uuid, text) from public;
grant execute on function public.track_visit(uuid, text) to anon, authenticated;
revoke all on function public.site_stats() from public, anon;
grant execute on function public.site_stats() to authenticated;
