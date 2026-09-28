-- Batch Zero — student ambassadors: invites, signup, and the public roster (/network/#ambassadors)
--
-- Run once in Supabase → SQL Editor, AFTER supabase/ambassadors.sql. Safe to run again.
--
-- The shape is deliberately the same as mentors: you create a one-off invite link from
-- /ambassador-invite/admin/, they fill it in at /ambassador-invite/?token=…, and their card is
-- on /network/ on the next page load. No approval step, nothing for you to remember.
--
-- WHERE IT DELIBERATELY DIFFERS FROM MENTORS, AND WHY
--   Ambassadors are high-school students, most of them under 18.
--     * No photos. Ever. The card is an initials tile — there is no photo column to fill.
--     * Nothing goes public unless they tick the box that says so (show_publicly).
--     * Under-18s must give a parent/guardian name and email before the card can appear.
--     * They choose the name that shows — "Maya R." is the default the form suggests.
--     * Email, guardian contact and the invite token are never readable by the public key.
--   published is your override on top of all that: null/true = follow their choice, false = hidden.

-- ── 0. the admin key ─────────────────────────────────────────────────────────
--     Reuses the key you already use for mentor invites when it's stored where this can find
--     it. If it isn't, this stops the whole script and tells you the one line to run first —
--     better than quietly leaving the invite endpoint unprotected.
do $key$
declare v_key text;
begin
  create schema if not exists private;
  create table if not exists private.settings (key text primary key, value text not null);
  -- the public key must never be able to read this
  revoke all on schema private from anon, authenticated;
  revoke all on private.settings from anon, authenticated;

  select value into v_key from private.settings where key = 'ambassador_admin_key';
  if v_key is not null then
    return;
  end if;

  select value into v_key from private.settings
   where key in ('mentor_admin_key', 'admin_key') limit 1;

  -- Nothing stored yet? The live create_mentor_invite() keeps its key as a constant in its own
  -- body. Lift it out here, inside the database, so ambassadors use the same key as mentors and
  -- the key never has to be typed, pasted or shown anywhere.
  if v_key is null then
    select (regexp_match(pg_get_functiondef(p.oid),
                         'ADMIN_KEY\s+constant\s+text\s*:=\s*''([^'']+)'''))[1]
      into v_key
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'create_mentor_invite'
     limit 1;
  end if;

  if v_key is not null then
    insert into private.settings (key, value) values ('ambassador_admin_key', v_key)
      on conflict (key) do nothing;
    raise notice 'Ambassador invites will use the same admin key as mentor invites.';
  else
    raise exception using message =
      'No admin key stored yet. Run this once, with a long random string of your own, then run this script again:  '
      'insert into private.settings (key, value) values (''ambassador_admin_key'', ''PUT-A-LONG-RANDOM-STRING-HERE'') '
      'on conflict (key) do update set value = excluded.value;';
  end if;
end
$key$;

-- ── 1. the table ─────────────────────────────────────────────────────────────
create table if not exists public.ambassadors (
  id               uuid primary key default gen_random_uuid(),
  invite_token     uuid unique not null default gen_random_uuid(),
  created_at       timestamptz not null default now(),
  full_name        text not null,
  email            text,
  school           text,
  city             text,
  grad_year        text,
  display_name     text,          -- what actually shows on the card
  focus            text,          -- comma-separated, shown as tags
  is_adult         boolean,
  guardian_name    text,
  guardian_email   text,
  show_publicly    boolean,       -- their choice
  published        boolean,       -- your override: null = follow their choice, false = hidden
  status           text not null default 'pending' check (status in ('pending', 'completed', 'revoked')),
  agreed_terms_at  timestamptz,
  completed_at     timestamptz,
  listed_at        timestamptz
);

create index if not exists ambassadors_token_idx  on public.ambassadors (invite_token);
create index if not exists ambassadors_status_idx on public.ambassadors (status, created_at desc);

-- The public key gets no direct access at all: it holds student and guardian email addresses,
-- and the token in a row is a one-time login for that row.
alter table public.ambassadors enable row level security;
revoke all on public.ambassadors from anon, authenticated;

-- ── 2. start clean, so no two overloads of the same name can confuse PostgREST ─
do $drops$
declare r record;
begin
  for r in
    select p.oid::regprocedure as sig
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in ('create_ambassador_invite', 'get_ambassador_invite',
                         'submit_ambassador_signup', 'list_ambassadors')
  loop
    execute 'drop function ' || r.sig || ' cascade';
  end loop;
end
$drops$;

-- ── 3. create an invite (you, from /ambassador-invite/admin/) ────────────────
create or replace function public.create_ambassador_invite(
  p_admin_key text,
  p_full_name text,
  p_email     text default null,
  p_school    text default null,
  p_city      text default null,
  p_grad_year text default null
) returns text
language plpgsql security definer set search_path = public, private as $$
declare v_token uuid;
begin
  if p_admin_key is null or not exists (
       select 1 from private.settings
        where key = 'ambassador_admin_key' and value = p_admin_key) then
    raise exception 'Not authorised';
  end if;
  if coalesce(btrim(p_full_name), '') = '' then
    raise exception 'A name is required';
  end if;

  insert into public.ambassadors (full_name, email, school, city, grad_year)
       values (btrim(p_full_name), nullif(btrim(coalesce(p_email, '')), ''),
               nullif(btrim(coalesce(p_school, '')), ''), nullif(btrim(coalesce(p_city, '')), ''),
               nullif(btrim(coalesce(p_grad_year, '')), ''))
    returning invite_token into v_token;
  return v_token::text;
end $$;

-- ── 4. read one invite by its token (the token is what protects the row) ─────
create or replace function public.get_ambassador_invite(p_token uuid)
returns table (full_name text, email text, school text, city text,
               grad_year text, display_name text, focus text, status text)
language sql security definer set search_path = public stable as $$
  select a.full_name, a.email, a.school, a.city,
         a.grad_year, a.display_name, a.focus, a.status
    from public.ambassadors a
   where a.invite_token = p_token
   limit 1;
$$;

-- ── 5. the ambassador fills it in ────────────────────────────────────────────
create or replace function public.submit_ambassador_signup(
  p_token          uuid,
  p_email          text,
  p_school         text,
  p_city           text,
  p_grad_year      text,
  p_display_name   text,
  p_focus          text,
  p_is_adult       boolean,
  p_guardian_name  text,
  p_guardian_email text,
  p_show_publicly  boolean,
  p_agree          boolean
) returns void
language plpgsql security definer set search_path = public as $$
declare v_status text;
begin
  if not coalesce(p_agree, false) then
    raise exception 'You need to agree to the terms to finish signing up';
  end if;
  if coalesce(btrim(p_email), '') !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then
    raise exception 'That email does not look right';
  end if;
  if coalesce(btrim(p_school), '') = '' then
    raise exception 'Which school?';
  end if;
  if coalesce(btrim(p_display_name), '') = '' then
    raise exception 'We need a name to show on the card';
  end if;
  -- a student under 18 cannot put themselves on a public website on their own say-so
  if not coalesce(p_is_adult, false)
     and coalesce(btrim(p_guardian_email), '') !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then
    raise exception 'A parent or guardian email is required if you are under 18';
  end if;
  if length(coalesce(p_display_name, '')) > 80
     or length(coalesce(p_school, '')) > 160
     or length(coalesce(p_city, '')) > 120
     or length(coalesce(p_focus, '')) > 400
     or length(coalesce(p_guardian_name, '')) > 120
     or length(coalesce(p_guardian_email, '')) > 200
     or length(coalesce(p_email, '')) > 200
     or length(coalesce(p_grad_year, '')) > 20 then
    raise exception 'That is longer than we can store';
  end if;

  select status into v_status from public.ambassadors where invite_token = p_token for update;
  if v_status is null then raise exception 'Invite not found'; end if;
  if v_status = 'revoked'   then raise exception 'This invite is no longer active'; end if;
  if v_status = 'completed' then raise exception 'This invite has already been used'; end if;

  update public.ambassadors
     set email           = btrim(p_email),
         school          = btrim(p_school),
         city            = nullif(btrim(coalesce(p_city, '')), ''),
         grad_year       = nullif(btrim(coalesce(p_grad_year, '')), ''),
         display_name    = btrim(p_display_name),
         focus           = nullif(btrim(coalesce(p_focus, '')), ''),
         is_adult        = coalesce(p_is_adult, false),
         guardian_name   = nullif(btrim(coalesce(p_guardian_name, '')), ''),
         guardian_email  = nullif(btrim(coalesce(p_guardian_email, '')), ''),
         show_publicly   = coalesce(p_show_publicly, false),
         status          = 'completed',
         agreed_terms_at = now(),
         completed_at    = now(),
         listed_at       = now()
   where invite_token = p_token;
end $$;

-- ── 6. the public roster ─────────────────────────────────────────────────────
--     Name, school, city, class year, tags. No email, no guardian, no token, no photo.
create or replace function public.list_ambassadors()
returns table (display_name text, school text, city text, grad_year text, focus text)
language sql security definer set search_path = public stable as $$
  select a.display_name, a.school, a.city, a.grad_year, a.focus
    from public.ambassadors a
   where a.status = 'completed'
     and coalesce(a.show_publicly, false)                 -- they said yes
     and coalesce(a.published, true)                      -- you haven't hidden them
     and (coalesce(a.is_adult, false)                     -- and, if under 18,
          or coalesce(btrim(a.guardian_email), '') <> '') -- a guardian is on record
     and coalesce(btrim(a.display_name), '') <> ''
   order by a.listed_at desc nulls last, a.display_name
   limit 500;
$$;

-- ── 7. what the public key may call ──────────────────────────────────────────
revoke all on function public.create_ambassador_invite(text, text, text, text, text, text)
  from public, anon, authenticated;
grant execute on function public.create_ambassador_invite(text, text, text, text, text, text) to anon;
grant execute on function public.get_ambassador_invite(uuid)                                  to anon, authenticated;
grant execute on function public.submit_ambassador_signup(uuid, text, text, text, text, text, text, boolean, text, text, boolean, boolean)
  to anon, authenticated;
grant execute on function public.list_ambassadors()                                            to anon, authenticated;

notify pgrst, 'reload schema';

-- ── 8. what the site will show ───────────────────────────────────────────────
select a.full_name,
       a.display_name,
       a.status,
       coalesce(a.show_publicly, false)                                   as they_said_yes,
       coalesce(a.published, true)                                        as not_hidden,
       coalesce(a.is_adult, false)
         or coalesce(btrim(a.guardian_email), '') <> ''                   as consent_on_file,
       a.listed_at,
       (select count(*) from public.list_ambassadors())                   as cards_on_page
  from public.ambassadors a
 order by a.listed_at desc nulls last, a.full_name;

-- Later, if you ever need them:
--   read the full list   select full_name, email, school, city, grad_year, guardian_email, status
--                          from public.ambassadors order by created_at desc;
--   hide someone         update public.ambassadors set published = false where full_name = 'Name Here';
--   end an invite        update public.ambassadors set status = 'revoked' where full_name = 'Name Here';
