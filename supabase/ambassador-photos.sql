-- Batch Zero — ambassador photos on /network/#ambassadors
--
-- Run once in Supabase → SQL Editor, after ambassador-roster.sql and ambassador-approve.sql.
-- Safe to run again.
--
-- WHAT CHANGES
--   Ambassador cards used to be initials only. Being listed (the show_publicly tick) now covers
--   the photo too, and the form copy says so. A photo shows only on a card that is already
--   public: list_ambassadors() keeps every existing gate (their tick, your `published` override).
--
--   Where the photo comes from, automatically:
--     1. The application form's "Verify with LinkedIn" button already stores the LinkedIn photo
--        link in the application (payload.photo_url). approve_ambassador() inserts the row; a
--        trigger here copies that link onto it. Nothing new to click.
--     2. The daily GitHub Action (tools/archive_mentor_photos.py) saves a copy into
--        assets/img/ambassadors/ before LinkedIn's link expires — the same as mentor photos —
--        and goes red, emailing you, for any listed ambassador who still has no photo.
--     3. No LinkedIn? Add one by hand:
--          python3 tools/archive_mentor_photos.py --add "Maya R." path/to/photo.jpg
--        (the name as it shows on their card), then commit assets/img/ambassadors/.
--
--   Hide just the photo:   update public.ambassadors set photo_url = null where display_name = 'Maya R.';
--                          and delete their file from assets/img/ambassadors/ + photos.json.
--   Hide the whole card:   update public.ambassadors set published = false where display_name = 'Maya R.';
--                          (the daily Action then deletes their saved photo from the site too)

do $guard$
begin
  if to_regclass('public.ambassadors') is null then
    raise exception 'public.ambassadors does not exist — run ambassador-roster.sql first';
  end if;
end
$guard$;

-- ── 1. the column ────────────────────────────────────────────────────────────
alter table public.ambassadors add column if not exists photo_url text;

-- only a LinkedIn image link — the same rule save_mentor_photo() applies to mentors
create or replace function private.licdn_photo(p_url text)
returns text language sql immutable set search_path = pg_catalog as $$
  select case
           when coalesce(p_url, '') ~ '^https://([a-z0-9-]+\.)+licdn\.com/[^\s"''<>]+$'
            and length(p_url) <= 500
           then p_url
         end;
$$;
revoke all on function private.licdn_photo(text) from public, anon, authenticated;

-- ── 2. copy the LinkedIn photo from the application when the row is created ───
create or replace function private.ambassador_photo_from_application()
returns trigger language plpgsql security definer set search_path = public, private as $$
begin
  if new.photo_url is null and new.application_id is not null then
    select private.licdn_photo(a.payload->>'photo_url') into new.photo_url
      from public.applications a
     where a.id = new.application_id;
  else
    new.photo_url := private.licdn_photo(new.photo_url);
  end if;
  return new;
end $$;
revoke all on function private.ambassador_photo_from_application() from public, anon, authenticated;

drop trigger if exists ambassadors_photo_from_application on public.ambassadors;
create trigger ambassadors_photo_from_application
  before insert on public.ambassadors
  for each row execute function private.ambassador_photo_from_application();

-- ambassadors approved before this script: pick up a LinkedIn photo if their application had one
update public.ambassadors am
   set photo_url = private.licdn_photo(ap.payload->>'photo_url')
  from public.applications ap
 where ap.id = am.application_id
   and am.photo_url is null
   and private.licdn_photo(ap.payload->>'photo_url') is not null;

-- ── 3. the public roster, now with photo_url ─────────────────────────────────
--     Same gates as ambassador-approve.sql. The return type changes, so drop first.
drop function if exists public.list_ambassadors() cascade;

create function public.list_ambassadors()
returns table (display_name text, school text, city text, grad_year text, focus text, photo_url text)
language sql security definer set search_path = public stable as $$
  select a.display_name, a.school, a.city, a.grad_year, a.focus, a.photo_url
    from public.ambassadors a
   where a.status = 'completed'
     and coalesce(a.show_publicly, false)      -- they ticked the box
     and coalesce(a.published, true)           -- you haven't hidden them
     and coalesce(btrim(a.display_name), '') <> ''
   order by a.listed_at desc nulls last, a.display_name
   limit 500;
$$;
revoke all on function public.list_ambassadors() from public;
grant execute on function public.list_ambassadors() to anon, authenticated;

notify pgrst, 'reload schema';

-- ── 4. what the site will show ───────────────────────────────────────────────
select display_name, school, (photo_url is not null) as has_linkedin_photo
  from public.list_ambassadors();
