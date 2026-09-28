-- Batch Zero — public mentor roster (/network/ and /mentors/)
--
-- Run once in Supabase → SQL Editor. Safe to run again: every step is idempotent.
--
-- WHAT THIS IS FOR
--   A mentor finishes /mentor-invite/ and their card appears on the site on the next page
--   load. Nothing to approve, no second step. The card shows name, title, company, their
--   top-three areas and their LinkedIn photo — and nothing else. Email, bio, LinkedIn URL
--   and the invite token stay unreadable to the public key.
--
-- HOW "SIGNED UP" IS DECIDED
--   areas_of_expertise is the tell. create_mentor_invite() never sets it (it has no areas
--   argument); submit_mentor_signup() always does, because the form makes them pick three.
--   So a row with areas filled in is a mentor who finished, and nothing else is.
--   published is an override: null/true = on the site, false = hidden.
--
-- THE TABLE
--   public.mentors, keyed for the invite flow by invite_token (uuid). This script reads the
--   column types out of the catalog rather than assuming them, so it works whether
--   areas_of_expertise is text or text[].

-- ── 0. stop early if this is pointed at the wrong database ───────────────────
do $guard$
begin
  if to_regclass('public.mentors') is null then
    raise exception 'public.mentors does not exist in this project — nothing was changed';
  end if;
  if not exists (
    select 1 from information_schema.columns
     where table_schema = 'public' and table_name = 'mentors' and column_name = 'invite_token'
  ) then
    raise exception 'public.mentors has no invite_token column — nothing was changed';
  end if;
end
$guard$;

-- ── 1. the three columns the roster needs ────────────────────────────────────
alter table public.mentors add column if not exists photo_url text;
alter table public.mentors add column if not exists published boolean;    -- null = show, false = hide
alter table public.mentors add column if not exists listed_at timestamptz;

-- ── 2. clear out any earlier version of these three functions ────────────────
--     (dropping by identity avoids leaving two overloads behind, which would make
--      PostgREST refuse the call as ambiguous)
do $drops$
declare r record;
begin
  for r in
    select p.oid::regprocedure as sig
      from pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in ('list_mentors', 'save_mentor_photo', 'mentors_stamp_listed_at')
  loop
    execute 'drop function ' || r.sig || ' cascade';
  end loop;
end
$drops$;

-- ── 3. the roster reader, the listed_at stamp, and the backfill ──────────────
do $build$
declare
  v_type text;
  v_m    text;   -- "their areas, as one string" over the table alias m
  v_new  text;   -- the same thing over NEW, inside the trigger
begin
  select data_type into v_type
    from information_schema.columns
   where table_schema = 'public' and table_name = 'mentors' and column_name = 'areas_of_expertise';

  if v_type is null then
    raise exception 'public.mentors has no areas_of_expertise column — nothing was changed';
  elsif v_type = 'ARRAY' then
    v_m   := 'array_to_string(m.areas_of_expertise, '', '')';
    v_new := 'array_to_string(new.areas_of_expertise, '', '')';
  else
    v_m   := 'm.areas_of_expertise::text';
    v_new := 'new.areas_of_expertise::text';
  end if;

  -- everything the public page is allowed to see, and not one column more
  execute format($fn$
    create or replace function public.list_mentors()
    returns table (full_name text, title text, company text, areas_of_expertise text, photo_url text)
    language sql security definer set search_path = public stable as $body$
      select m.full_name::text, m.title::text, m.company::text, %1$s, m.photo_url::text
        from public.mentors m
       where coalesce(m.published, true)
         and coalesce(btrim(%1$s), '') <> ''
       order by m.listed_at desc nulls last, m.full_name
       limit 500;
    $body$
  $fn$, v_m);

  -- stamp the moment they finished, so the newest mentor leads the page
  execute format($fn$
    create or replace function public.mentors_stamp_listed_at() returns trigger
    language plpgsql as $body$
    begin
      if coalesce(btrim(%1$s), '') <> '' and new.listed_at is null then
        new.listed_at := now();
      end if;
      return new;
    end
    $body$
  $fn$, v_new);

  -- anyone who already signed up (hello, first mentor) gets a stamp now
  execute format($fn$
    update public.mentors m
       set listed_at = coalesce(m.listed_at, now())
     where coalesce(btrim(%1$s), '') <> ''
  $fn$, v_m);
end
$build$;

drop trigger if exists mentors_listed_at on public.mentors;
create trigger mentors_listed_at
before insert or update on public.mentors
for each row execute function public.mentors_stamp_listed_at();

-- ── 4. remember the LinkedIn photo ───────────────────────────────────────────
--     Called by /mentor-invite/ right after a mentor confirms, when they signed in with
--     LinkedIn. Holding the invite token is the permission: it only ever touches that row.
create or replace function public.save_mentor_photo(p_token text, p_photo_url text)
returns void
language plpgsql security definer set search_path = public as $$
begin
  if coalesce(p_token, '') !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then
    raise exception 'Invalid invite token';
  end if;
  -- a whole URL on a licdn.com host, nothing else: no other domain, no look-alike
  -- ("notlicdn.com", "licdn.com.evil.net"), no spaces or quotes smuggled into the value
  if coalesce(p_photo_url, '') !~ '^https://([a-z0-9-]+\.)+licdn\.com/[^\s"''<>]+$'
     or length(p_photo_url) > 500 then
    raise exception 'Photo must be a LinkedIn image URL';
  end if;
  update public.mentors
     set photo_url = p_photo_url
   where invite_token = p_token::uuid;
end $$;

-- ── 5. what the public key may call ──────────────────────────────────────────
grant execute on function public.list_mentors()                 to anon, authenticated;
grant execute on function public.save_mentor_photo(text, text)  to anon, authenticated;

-- tell PostgREST about the new functions straight away instead of waiting for it to notice
notify pgrst, 'reload schema';

-- ── 6. what the site will show, and why ──────────────────────────────────────
--     on_site = true  → this person's card is live right now
select m.full_name,
       coalesce(m.published, true)
         and coalesce(btrim(m.areas_of_expertise::text), '') <> ''  as on_site,
       coalesce(btrim(m.areas_of_expertise::text), '') <> ''        as finished_signup,
       coalesce(m.published, true)                                  as not_hidden,
       (m.photo_url is not null)                                    as has_photo,
       m.listed_at,
       (select count(*) from public.list_mentors())                 as cards_on_page
  from public.mentors m
 order by m.listed_at desc nulls last, m.full_name;

-- Later, if you ever need them:
--   hide someone     update public.mentors set published = false where full_name = 'Name Here';
--   show them again  update public.mentors set published = null  where full_name = 'Name Here';
--   swap the photo   update public.mentors set photo_url = 'https://…' where full_name = 'Name Here';
