-- Batch Zero — mentor invites (/mentor-invite/)
--
-- ⚠️  READ THIS FIRST. These objects ALREADY EXIST in the live project (they were created in a
--     separate session, and the SQL was never committed). This file is a reference implementation
--     reconstructed from what the front-end calls — it has NOT been diffed against the live
--     definitions. Do not run it against a project that already has them: run section 0 first and
--     reconcile. Replace this file with the real definitions once you've dumped them.
--     (The implementation below was exercised in a scratch Postgres: wrong admin key refused,
--     anon blocked from the table, agreement and email checked, invite usable exactly once.)
--
-- The contract the site depends on (this part IS verified — it's what assets/js/mentor-invite.js
-- and assets/js/mentor-invite-admin.js call, with the public anon key):
--
--   create_mentor_invite(p_admin_key, p_full_name, p_linkedin_url, p_title, p_company, p_bio)
--       → returns the invite token (text). Admin-only: the key is checked inside the function.
--   get_mentor_invite(p_token)
--       → returns one row: full_name, title, company, linkedin_url, email,
--         areas_of_expertise, bio, status ('pending' | 'completed').
--   submit_mentor_signup(p_token, p_email, p_title, p_company, p_bio, p_areas, p_agree)
--       → marks the invite completed and stores what the mentor confirmed.
--
-- The anon key may only EXECUTE these three functions. It must never be able to read the table
-- directly: it holds mentor email addresses, and the token in one row is a login for that row.

-- ───────────────────────────────────────────────────────────────────────────
-- 0. Verification — run this BEFORE anything else and compare with the below.
-- ───────────────────────────────────────────────────────────────────────────
-- select p.proname,
--        pg_get_function_identity_arguments(p.oid) as arguments,
--        p.prosecdef                               as security_definer,
--        pg_get_functiondef(p.oid)                 as definition
--   from pg_proc p join pg_namespace n on n.oid = p.pronamespace
--  where n.nspname = 'public'
--    and p.proname in ('create_mentor_invite', 'get_mentor_invite', 'submit_mentor_signup');
--
-- select table_schema, table_name, column_name, data_type
--   from information_schema.columns
--  where table_name ilike '%mentor%'
--  order by table_schema, table_name, ordinal_position;
--
-- select relname, relrowsecurity as rls_on from pg_class where relname ilike '%mentor%';

-- ───────────────────────────────────────────────────────────────────────────
-- 1. Reference implementation — ONLY run this if section 0 came back empty.
-- ───────────────────────────────────────────────────────────────────────────
create extension if not exists pgcrypto;

-- the admin key lives in its own schema so PostgREST never exposes it
create schema if not exists private;

create table if not exists private.settings (
  key   text primary key,
  value text not null
);
-- set the admin key once (pick something long):
--   insert into private.settings (key, value) values ('mentor_admin_key', '<long random string>')
--   on conflict (key) do update set value = excluded.value;

create table if not exists public.mentor_invites (
  id                  uuid primary key default gen_random_uuid(),
  token               text unique not null default encode(gen_random_bytes(24), 'hex'),
  created_at          timestamptz not null default now(),
  full_name           text not null,
  linkedin_url        text,
  title               text,
  company             text,
  bio                 text,
  email               text,
  areas_of_expertise  text,
  status              text not null default 'pending' check (status in ('pending', 'completed', 'revoked')),
  agreed_terms_at     timestamptz,
  completed_at        timestamptz
);

create index if not exists mentor_invites_token_idx  on public.mentor_invites (token);
create index if not exists mentor_invites_status_idx on public.mentor_invites (status, created_at desc);

-- No direct table access for the public key: RLS on, no policies, no grants.
alter table public.mentor_invites enable row level security;
revoke all on public.mentor_invites from anon, authenticated;

-- create an invite (admin only)
create or replace function public.create_mentor_invite(
  p_admin_key text, p_full_name text, p_linkedin_url text default null,
  p_title text default null, p_company text default null, p_bio text default null
) returns text
language plpgsql security definer set search_path = public, private as $$
declare v_token text;
begin
  if p_admin_key is null or p_admin_key <> (select value from private.settings where key = 'mentor_admin_key') then
    raise exception 'Not authorised';
  end if;
  if coalesce(trim(p_full_name), '') = '' then
    raise exception 'A name is required';
  end if;
  insert into public.mentor_invites (full_name, linkedin_url, title, company, bio)
       values (trim(p_full_name), p_linkedin_url, p_title, p_company, p_bio)
    returning token into v_token;
  return v_token;
end $$;

-- read one invite by its token (the token is the only thing protecting this row)
create or replace function public.get_mentor_invite(p_token text)
returns table (full_name text, title text, company text, linkedin_url text,
               email text, areas_of_expertise text, bio text, status text)
language sql security definer set search_path = public stable as $$
  select full_name, title, company, linkedin_url, email, areas_of_expertise, bio, status
    from public.mentor_invites
   where token = p_token
   limit 1;
$$;

-- the mentor confirms their details
create or replace function public.submit_mentor_signup(
  p_token text, p_email text, p_title text, p_company text,
  p_bio text, p_areas text, p_agree boolean
) returns void
language plpgsql security definer set search_path = public as $$
declare v_status text;
begin
  if not coalesce(p_agree, false) then
    raise exception 'You need to agree to the mentor terms';
  end if;
  if coalesce(trim(p_email), '') !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then
    raise exception 'That email does not look right';
  end if;
  if length(coalesce(p_bio, '')) > 2000 or length(coalesce(p_areas, '')) > 500 then
    raise exception 'That is longer than we can store';
  end if;

  select status into v_status from public.mentor_invites where token = p_token for update;
  if v_status is null then raise exception 'Invite not found'; end if;
  if v_status <> 'pending' then raise exception 'This invite has already been used'; end if;

  update public.mentor_invites
     set email = trim(p_email), title = p_title, company = p_company, bio = p_bio,
         areas_of_expertise = p_areas, status = 'completed',
         agreed_terms_at = now(), completed_at = now()
   where token = p_token;
end $$;

-- the public key may only call these three
revoke all on function public.create_mentor_invite(text, text, text, text, text, text) from public, anon, authenticated;
grant execute on function public.create_mentor_invite(text, text, text, text, text, text) to anon;
grant execute on function public.get_mentor_invite(text) to anon;
grant execute on function public.submit_mentor_signup(text, text, text, text, text, text, boolean) to anon;

-- Reading the roster is a dashboard job (service_role), same as applications:
--   select full_name, email, title, company, areas_of_expertise, status, completed_at
--     from public.mentor_invites order by created_at desc;
