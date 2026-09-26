-- Batch Zero — public mentor roster (/mentors/)
--
-- ADDITIVE ONLY. This file adds columns and two new functions; it never replaces the three
-- functions the invite flow already uses (see supabase/mentor-invites.sql). Safe to run once
-- against the live project as-is.
--
-- What it does:
--   * remembers the LinkedIn photo for a confirmed mentor           (save_mentor_photo)
--   * exposes ONLY what the public page shows                       (list_mentors)
--
-- What the public key can read, and nothing else: name, title, company, areas, photo.
-- Email, token and everything else stay unreadable — list_mentors() never selects them.

alter table public.mentor_invites add column if not exists photo_url text;
alter table public.mentor_invites add column if not exists published boolean not null default true;
alter table public.mentor_invites add column if not exists listed_at timestamptz not null default now();

-- Called by /mentor-invite/ right after a mentor confirms, when they signed in with LinkedIn.
-- The invite token is the permission: only someone holding it can set that row's photo.
create or replace function public.save_mentor_photo(p_token text, p_photo_url text)
returns void
language plpgsql security definer set search_path = public as $$
begin
  if coalesce(p_photo_url, '') !~ '^https://[a-z0-9.-]*licdn\.com/' then
    raise exception 'Photo must be a LinkedIn image URL';
  end if;
  update public.mentor_invites
     set photo_url = p_photo_url, listed_at = now()
   where token = p_token and status = 'completed';
end $$;

-- The public roster. Newest first.
create or replace function public.list_mentors()
returns table (full_name text, title text, company text, areas_of_expertise text, photo_url text)
language sql security definer set search_path = public stable as $$
  select full_name, title, company, areas_of_expertise, photo_url
    from public.mentor_invites
   where status = 'completed' and published
   order by listed_at desc, full_name;
$$;

grant execute on function public.save_mentor_photo(text, text) to anon;
grant execute on function public.list_mentors() to anon;

-- Hide someone from the page without deleting them:
--   update public.mentor_invites set published = false where full_name = 'Name Here';
-- Swap an expiring LinkedIn photo for one you host yourself:
--   update public.mentor_invites set photo_url = 'https://…' where full_name = 'Name Here';
