-- Batch Zero — the review desk (/review/)
--
-- Run once in Supabase → SQL Editor, after schema.sql, ambassadors.sql and ambassador-roster.sql.
-- Safe to run again.
--
-- WHAT THIS IS FOR
--   Applications land in public.applications with every answer inside a jsonb payload, which
--   means the only way to read one is Supabase's table editor. This gives /review/ three
--   functions so you can read them on a page, mark them, and turn a yes into an invite link
--   without copying anything by hand.
--
-- WHO CAN CALL THESE
--   Only someone holding the admin key — the same key the two invite tools use, stored in
--   private.settings under 'ambassador_admin_key'. The key is checked inside each function, so
--   the public key alone gets nothing.
--
--   These functions return applicants' names, emails and schools, and most applicants are
--   minors. Treat the admin key like a password: make it long, never put it in the repo, and
--   change it (in private.settings AND in create_mentor_invite's body) if it ever leaks.

do $guard$
declare n int;
begin
  -- the second check has to be dynamic: naming a table that does not exist fails at plan
  -- time, before the first `if` ever runs
  if to_regclass('private.settings') is not null then
    execute 'select count(*) from private.settings where key = ''ambassador_admin_key''' into n;
  end if;
  if coalesce(n, 0) = 0 then
    raise exception
      'No admin key on file. Run supabase/ambassador-roster.sql first — nothing was changed.';
  end if;
end
$guard$;

do $drops$
declare r record;
begin
  for r in
    select p.oid::regprocedure as sig
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in ('list_applications', 'set_application_status', 'list_outstanding_invites')
  loop
    execute 'drop function ' || r.sig || ' cascade';
  end loop;
end
$drops$;

-- shared gate, so the key is checked the same way everywhere
create or replace function private.check_admin_key(p_admin_key text) returns void
language plpgsql security definer set search_path = private as $$
begin
  if p_admin_key is null or not exists (
       select 1 from private.settings where key = 'ambassador_admin_key' and value = p_admin_key) then
    raise exception 'Not authorised';
  end if;
end $$;

-- ── read the queue ───────────────────────────────────────────────────────────
create or replace function public.list_applications(
  p_admin_key text,
  p_type      text default null,          -- null = every type
  p_status    text default null            -- null = everything except archived/rejected
) returns table (id uuid, created_at timestamptz, type text, name text,
                 email text, payload jsonb, status text, notes text)
language plpgsql security definer set search_path = public, private as $$
begin
  perform private.check_admin_key(p_admin_key);
  return query
    select a.id, a.created_at, a.type, a.name, a.email, a.payload, a.status, a.notes
      from public.applications a
     where (p_type is null or a.type = p_type)
       and (case when p_status is null then a.status not in ('archived', 'rejected')
                 else a.status = p_status end)
     order by a.created_at desc
     limit 500;
end $$;

-- ── mark one ─────────────────────────────────────────────────────────────────
create or replace function public.set_application_status(
  p_admin_key text, p_id uuid, p_status text, p_notes text default null
) returns void
language plpgsql security definer set search_path = public, private as $$
begin
  perform private.check_admin_key(p_admin_key);
  if p_status not in ('new', 'reviewing', 'accepted', 'rejected', 'archived') then
    raise exception 'Unknown status';
  end if;
  if length(coalesce(p_notes, '')) > 2000 then
    raise exception 'That note is longer than we can store';
  end if;
  update public.applications
     set status = p_status,
         notes  = coalesce(nullif(btrim(coalesce(p_notes, '')), ''), notes)
   where id = p_id;
  if not found then raise exception 'No such application'; end if;
end $$;

-- ── who has a link but has not used it ───────────────────────────────────────
--     This is the chase list: an invite only turns into a card when they fill it in.
create or replace function public.list_outstanding_invites(p_admin_key text)
returns table (kind text, full_name text, email text, invite_token uuid, extra text)
language plpgsql security definer set search_path = public, private as $$
begin
  perform private.check_admin_key(p_admin_key);
  return query
    select 'mentor'::text, m.full_name, m.email, m.invite_token,
           nullif(btrim(concat_ws(' · ', m.title, m.company)), '')
      from public.mentors m
     where coalesce(btrim(m.areas_of_expertise), '') = ''      -- never finished the form
    union all
    select 'ambassador'::text, a.full_name, a.email, a.invite_token,
           nullif(btrim(concat_ws(' · ', a.school, a.city)), '')
      from public.ambassadors a
     where a.status = 'pending'
     order by 1, 2;
end $$;

-- ── what the page may call (the key, not the role, is the gate) ──────────────
grant execute on function public.list_applications(text, text, text)            to anon;
grant execute on function public.set_application_status(text, uuid, text, text) to anon;
grant execute on function public.list_outstanding_invites(text)                 to anon;
revoke all on function private.check_admin_key(text) from public, anon, authenticated;

notify pgrst, 'reload schema';

select (select count(*) from public.applications where status not in ('archived','rejected')) as in_the_queue,
       (select count(*) from public.applications where type = 'ambassador') as ambassador_applications,
       (select count(*) from public.mentors where coalesce(btrim(areas_of_expertise),'') = '') as mentor_links_unused,
       (select count(*) from public.ambassadors where status = 'pending') as ambassador_links_unused;
