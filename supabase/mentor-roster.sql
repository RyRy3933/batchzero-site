-- Batch Zero — public mentor roster (/network/ and the homepage "Mentors:" strip)
--
-- Run in Supabase → SQL Editor. Safe to run again: every step is idempotent. Re-run it whenever
-- this file changes — it rebuilds list_mentors() from scratch.
--
-- WHAT THIS IS FOR
--   A mentor finishes /mentor-invite/ and their card appears on the site on the next page
--   load. Nothing to approve, no second step. Cards show name, title, company, their
--   top-three areas, their photo, their short bio and a link to their LinkedIn profile —
--   all of which the mentor terms (section 2) and the signup checkbox cover. Email and the
--   invite token stay unreadable to the public key.
--
-- CHANGELOG
--   2026-10-18  list_mentors() also returns bio and linkedin_url, for the homepage strip.
--               linkedin_url is only returned when it is a linkedin.com profile link (/in/ or
--               /pub/), so a typo or a stray value can never become a link on the site; the
--               page checks it again before using it. Bio is trimmed and capped at 600 chars.
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
  v_bio  text;   -- the bio column, or null if this project doesn't have one
  v_li   text;   -- the LinkedIn profile URL, only when it really is one
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

  -- bio and linkedin_url are written by create_mentor_invite()/submit_mentor_signup(). Read them
  -- only if the columns exist, so this script can't fail on an older table.
  if exists (select 1 from information_schema.columns
              where table_schema = 'public' and table_name = 'mentors' and column_name = 'bio') then
    v_bio := 'nullif(btrim(left(m.bio::text, 600)), '''')';
  else
    v_bio := 'null::text';
  end if;
  if exists (select 1 from information_schema.columns
              where table_schema = 'public' and table_name = 'mentors' and column_name = 'linkedin_url') then
    -- a linkedin.com (or country subdomain) /in/ or /pub/ profile, with or without https://,
    -- no spaces, quotes or angle brackets; anything else comes back as null
    v_li := $re$case when btrim(m.linkedin_url::text) ~* '^(https?://)?([a-z0-9-]+\.)?linkedin\.com/(in|pub)/[^\s"''<>]+$'
                       and length(btrim(m.linkedin_url::text)) <= 300
                     then btrim(m.linkedin_url::text) end$re$;
  else
    v_li := 'null::text';
  end if;

  -- everything the public page is allowed to see, and not one column more
  execute format($fn$
    create or replace function public.list_mentors()
    returns table (full_name text, title text, company text, areas_of_expertise text, photo_url text,
                   bio text, linkedin_url text)
    language sql security definer set search_path = public stable as $body$
      select m.full_name::text, m.title::text, m.company::text, %1$s, m.photo_url::text,
             %2$s, %3$s
        from public.mentors m
       where coalesce(m.published, true)
         and coalesce(btrim(%1$s), '') <> ''
       order by m.listed_at desc nulls last, m.full_name
       limit 500;
    $body$
  $fn$, v_m, v_bio, v_li);

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

-- ── 7. what each card will show on the homepage strip ───────────────────────
--     no bio → the card shows "title · company" instead; no link → no "View on LinkedIn"
select l.full_name,
       l.bio is not null          as has_bio,
       l.linkedin_url is not null as has_linkedin_link,
       l.linkedin_url
  from public.list_mentors() l;

-- Later, if you ever need them:
--   hide someone     update public.mentors set published = false where full_name = 'Name Here';
--   show them again  update public.mentors set published = null  where full_name = 'Name Here';
--   swap the photo   update public.mentors set photo_url = 'https://…' where full_name = 'Name Here';
--   set a bio        update public.mentors set bio = '…' where full_name = 'Name Here';
--   fix their link   update public.mentors set linkedin_url = 'https://www.linkedin.com/in/…' where full_name = 'Name Here';
