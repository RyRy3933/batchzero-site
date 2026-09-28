-- Batch Zero — mentor invites (/mentor-invite/)
--
-- THIS FILE IS DOCUMENTATION. Do not run section 1 against the live project: those objects
-- already exist there, and creating them again under different argument types would leave two
-- overloads of get_mentor_invite(), which makes PostgREST refuse the call as ambiguous and
-- breaks every outstanding invite link. Section 1 has a guard that stops exactly that.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- WHAT IS ACTUALLY LIVE (read out of the catalog on 2026-09-27 — this part is verified)
-- ─────────────────────────────────────────────────────────────────────────────
--   Table: public.mentors        ← NOT "mentor_invites". An earlier version of this file said
--                                  mentor_invites and that was wrong; it cost an afternoon.
--   Token: mentors.invite_token, type uuid (the client sends it as a string; PostgREST casts)
--
--   create_mentor_invite(p_admin_key text, p_full_name text, p_linkedin_url text,
--                        p_title text, p_company text, p_bio text) → token text
--       The admin key is a constant declared inside the function body:
--           ADMIN_KEY constant text := '…';
--       To change it, edit the function. It is ALSO stored now in private.settings under
--       'ambassador_admin_key' (supabase/ambassador-roster.sql lifted it out so the ambassador
--       invite tool could share one key) — change both if you ever rotate it.
--
--   get_mentor_invite(p_token uuid)
--       → full_name, linkedin_url, title, company, bio, email, areas_of_expertise, status
--
--   submit_mentor_signup(p_token, p_email, p_title, p_company, p_bio, p_areas, p_agree)
--       → marks the row completed and stores what the mentor confirmed. It always writes
--         areas_of_expertise, which is what supabase/mentor-roster.sql uses to tell a finished
--         mentor from an invite that was only created.
--
--   Added later by supabase/mentor-roster.sql: mentors.photo_url, mentors.published,
--   mentors.listed_at, list_mentors(), save_mentor_photo(), and the mentors_listed_at trigger.
--
-- The anon key may only EXECUTE those functions. It must never read public.mentors directly:
-- the table holds mentor email addresses, and the token in a row is a login for that row.

-- ─────────────────────────────────────────────────────────────────────────────
-- 0. Re-check any of that against the live project
-- ─────────────────────────────────────────────────────────────────────────────
-- select p.proname,
--        pg_get_function_identity_arguments(p.oid) as arguments,
--        p.prosecdef                               as security_definer,
--        pg_get_functiondef(p.oid)                 as definition
--   from pg_proc p join pg_namespace n on n.oid = p.pronamespace
--  where n.nspname = 'public'
--    and p.proname in ('create_mentor_invite', 'get_mentor_invite', 'submit_mentor_signup',
--                      'list_mentors', 'save_mentor_photo');
--
-- select column_name, data_type from information_schema.columns
--  where table_schema = 'public' and table_name = 'mentors' order by ordinal_position;
--
-- select relname, relrowsecurity as rls_on from pg_class where relname = 'mentors';

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Reference implementation — only for rebuilding this from scratch in a NEW project.
--    The guard below refuses to run if public.mentors already exists.
-- ─────────────────────────────────────────────────────────────────────────────
do $guard$
begin
  if to_regclass('public.mentors') is not null then
    raise exception
      'public.mentors already exists — this file is documentation, not a migration. Nothing was changed.';
  end if;
end
$guard$;

create table public.mentors (
  id                  uuid primary key default gen_random_uuid(),
  invite_token        uuid unique not null default gen_random_uuid(),
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

create index mentors_token_idx  on public.mentors (invite_token);
create index mentors_status_idx on public.mentors (status, created_at desc);

alter table public.mentors enable row level security;
revoke all on public.mentors from anon, authenticated;

create schema if not exists private;
create table if not exists private.settings (key text primary key, value text not null);
revoke all on schema private from anon, authenticated;
revoke all on private.settings from anon, authenticated;
-- insert into private.settings (key, value)
--      values ('mentor_admin_key', '<a long random string>')
--   on conflict (key) do update set value = excluded.value;

create or replace function public.create_mentor_invite(
  p_admin_key text, p_full_name text, p_linkedin_url text default null,
  p_title text default null, p_company text default null, p_bio text default null
) returns text
language plpgsql security definer set search_path = public, private as $$
declare v_token uuid;
begin
  if p_admin_key is null or not exists (
       select 1 from private.settings where key = 'mentor_admin_key' and value = p_admin_key) then
    raise exception 'Not authorised';
  end if;
  if coalesce(btrim(p_full_name), '') = '' then
    raise exception 'A name is required';
  end if;
  insert into public.mentors (full_name, linkedin_url, title, company, bio)
       values (btrim(p_full_name), p_linkedin_url, p_title, p_company, p_bio)
    returning invite_token into v_token;
  return v_token::text;
end $$;

create or replace function public.get_mentor_invite(p_token uuid)
returns table (full_name text, linkedin_url text, title text, company text,
               bio text, email text, areas_of_expertise text, status text)
language sql security definer set search_path = public stable as $$
  select m.full_name, m.linkedin_url, m.title, m.company,
         m.bio, m.email, m.areas_of_expertise, m.status
    from public.mentors m
   where m.invite_token = p_token
   limit 1;
$$;

create or replace function public.submit_mentor_signup(
  p_token uuid, p_email text, p_title text, p_company text,
  p_bio text, p_areas text, p_agree boolean
) returns void
language plpgsql security definer set search_path = public as $$
declare v_status text;
begin
  if not coalesce(p_agree, false) then
    raise exception 'You need to agree to the mentor terms';
  end if;
  if coalesce(btrim(p_email), '') !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then
    raise exception 'That email does not look right';
  end if;
  if length(coalesce(p_bio, '')) > 2000 or length(coalesce(p_areas, '')) > 500 then
    raise exception 'That is longer than we can store';
  end if;
  if coalesce(btrim(p_areas), '') = '' then
    raise exception 'Pick what you can mentor on';   -- the roster depends on this being set
  end if;

  select status into v_status from public.mentors where invite_token = p_token for update;
  if v_status is null      then raise exception 'Invite not found'; end if;
  if v_status <> 'pending' then raise exception 'This invite has already been used'; end if;

  update public.mentors
     set email = btrim(p_email), title = p_title, company = p_company, bio = p_bio,
         areas_of_expertise = p_areas, status = 'completed',
         agreed_terms_at = now(), completed_at = now()
   where invite_token = p_token;
end $$;

revoke all on function public.create_mentor_invite(text, text, text, text, text, text)
  from public, anon, authenticated;
grant execute on function public.create_mentor_invite(text, text, text, text, text, text) to anon;
grant execute on function public.get_mentor_invite(uuid)                                   to anon, authenticated;
grant execute on function public.submit_mentor_signup(uuid, text, text, text, text, text, boolean)
  to anon, authenticated;

-- Then run supabase/mentor-roster.sql to add the public roster on top of this.
