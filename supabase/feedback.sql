-- FitLens feedback: the "Was this helpful?" buttons and the footer form.
-- Run once in Supabase → SQL Editor → New query → Run (after admin.sql, which
-- creates the private schema and private.is_admin()). Safe to run again.
-- If Supabase asks about row-level security, choose "Enable RLS".
--
-- What is stored: the page, a thumbs up/down, the message the visitor typed,
-- an email ONLY if they chose to give one for a reply, and the same random
-- browser id used for visit counts (to stop spam). No IP address, no account
-- id, no resume content. Visitors can only send; only admins can read.

create table if not exists private.feedback (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  visitor_id uuid not null,
  page text not null check (page in ('results', 'earn', 'internships', 'site')),
  kind text not null check (kind in ('rating', 'message')),
  rating smallint check (rating in (-1, 1)),
  message text check (char_length(message) <= 1000),
  contact text check (char_length(contact) <= 200)
);
create index if not exists feedback_created_idx on private.feedback (created_at desc);
create index if not exists feedback_visitor_idx on private.feedback (visitor_id, created_at);

alter table private.feedback enable row level security;
revoke all on private.feedback from public, anon, authenticated;

-- Send feedback. Returns true when saved; false when invalid or over the limits
-- (10 a day per browser, 1,000 a day in total).
create or replace function public.submit_feedback(
  visitor_key uuid,
  page_name text,
  feedback_kind text,
  thumbs smallint default null,
  feedback_message text default null,
  reply_to text default null
)
returns boolean
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  msg text := nullif(btrim(coalesce(feedback_message, '')), '');
  email text := nullif(btrim(coalesce(reply_to, '')), '');
  since timestamptz := now() - interval '1 day';
begin
  if visitor_key is null
    or page_name not in ('results', 'earn', 'internships', 'site')
    or feedback_kind not in ('rating', 'message')
    or (thumbs is not null and thumbs not in (-1, 1))
    or (feedback_kind = 'rating' and thumbs is null)
    or (feedback_kind = 'message' and msg is null)
    or char_length(coalesce(msg, '')) > 1000
    or char_length(coalesce(email, '')) > 200 then
    return false;
  end if;

  if (select count(*) from private.feedback where visitor_id = visitor_key and created_at > since) >= 10
    or (select count(*) from private.feedback where created_at > since) >= 1000 then
    return false;
  end if;

  insert into private.feedback (visitor_id, page, kind, rating, message, contact)
  values (visitor_key, page_name, feedback_kind, thumbs, msg, email);
  return true;
end;
$$;

-- For the admin dashboard: thumbs per page (30 days) and the latest messages.
-- Null for anyone who is not an admin.
create or replace function public.admin_feedback()
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if not private.is_admin() then
    return null;
  end if;

  return jsonb_build_object(
    'ratings', (
      select coalesce(jsonb_object_agg(r.page, jsonb_build_object('up', r.up, 'down', r.down)), '{}'::jsonb)
      from (
        select page,
          count(*) filter (where rating = 1) as up,
          count(*) filter (where rating = -1) as down
        from private.feedback
        where kind = 'rating' and created_at > now() - interval '30 days'
        group by page
      ) r
    ),
    'messages', (
      select coalesce(jsonb_agg(jsonb_build_object(
        'at', m.created_at, 'page', m.page, 'rating', m.rating, 'message', m.message, 'contact', m.contact
      ) order by m.created_at desc), '[]'::jsonb)
      from (
        select * from private.feedback where kind = 'message' order by created_at desc limit 100
      ) m
    )
  );
end;
$$;

revoke all on function public.submit_feedback(uuid, text, text, smallint, text, text) from public;
grant execute on function public.submit_feedback(uuid, text, text, smallint, text, text) to anon, authenticated;
revoke all on function public.admin_feedback() from public, anon;
grant execute on function public.admin_feedback() to authenticated;
