-- Batch Zero — approve an ambassador straight onto the site
--
-- Run once in Supabase → SQL Editor, after ambassador-roster.sql and review.sql.
-- Safe to run again.
--
-- WHAT CHANGES
--   Before: approving an application created a signup link, and the applicant had to fill in a
--   second form before their card appeared. They had already typed all of it once, so the only
--   thing the second form really collected was consent to being on a public page.
--
--   Now the application form itself asks that ("Show me on the Batch Zero network page" plus
--   the name they want shown), so approve_ambassador() can publish on the spot.
--
--   The invite-link flow stays for people who never applied — someone you recruit directly.
--
-- WHAT THIS GIVES UP, SAID PLAINLY
--   list_ambassadors() no longer requires a parent or guardian on record for an under-18.
--   That check is removed because the application form does not collect guardian details.
--   What is left protecting a student is their own opt-in tick, the fact that the card shows
--   the name THEY chose (first name + last initial by default), and your `published = false`
--   override. The site still tells applicants a guardian signs a consent form before they
--   start — nothing in the database enforces that any more, so it is on you to actually do it.

do $guard$
begin
  if to_regclass('public.ambassadors') is null then
    raise exception 'public.ambassadors does not exist — run ambassador-roster.sql first';
  end if;
end
$guard$;

-- ── 1. remember which application a row came from, so approving twice is harmless ────
alter table public.ambassadors add column if not exists application_id uuid;
create unique index if not exists ambassadors_application_idx
  on public.ambassadors (application_id) where application_id is not null;

-- ── 2. the roster gate, without the guardian clause ──────────────────────────────────
create or replace function public.list_ambassadors()
returns table (display_name text, school text, city text, grad_year text, focus text)
language sql security definer set search_path = public stable as $$
  select a.display_name, a.school, a.city, a.grad_year, a.focus
    from public.ambassadors a
   where a.status = 'completed'
     and coalesce(a.show_publicly, false)      -- they ticked the box
     and coalesce(a.published, true)           -- you haven't hidden them
     and coalesce(btrim(a.display_name), '') <> ''
   order by a.listed_at desc nulls last, a.display_name
   limit 500;
$$;
grant execute on function public.list_ambassadors() to anon, authenticated;

-- ── 3. approve ───────────────────────────────────────────────────────────────────────
drop function if exists public.approve_ambassador(text, uuid) cascade;

create or replace function public.approve_ambassador(p_admin_key text, p_application_id uuid)
returns table (full_name text, display_name text, published boolean, already boolean)
language plpgsql security definer set search_path = public, private as $$
declare
  a         public.applications%rowtype;
  v_exists  public.ambassadors%rowtype;
  v_display text;
  v_show    boolean;
  v_school  text;
  v_city    text;
  v_focus   text;
  v_parts   text[];
begin
  perform private.check_admin_key(p_admin_key);

  select * into a from public.applications where id = p_application_id;
  if a.id is null then raise exception 'No such application'; end if;
  if a.type <> 'ambassador' then raise exception 'That is not an ambassador application'; end if;

  -- already approved? say so and change nothing
  select * into v_exists from public.ambassadors where application_id = p_application_id;
  if v_exists.id is not null then
    return query select v_exists.full_name, v_exists.display_name,
                        coalesce(v_exists.show_publicly, false) and coalesce(v_exists.published, true),
                        true;
    return;
  end if;

  -- the name they chose, or first name + last initial
  v_display := nullif(btrim(coalesce(a.payload->>'display_name', '')), '');
  if v_display is null then
    v_parts := regexp_split_to_array(btrim(coalesce(a.name, '')), '\s+');
    if array_length(v_parts, 1) >= 2 then
      v_display := v_parts[1] || ' ' || upper(left(v_parts[array_length(v_parts, 1)], 1)) || '.';
    else
      v_display := coalesce(v_parts[1], a.name);
    end if;
  end if;

  -- only a tick counts as consent to being listed
  v_show := coalesce(a.payload->>'show_publicly', 'no') = 'yes';

  -- "Monte Vista High, Danville CA" → school, city
  v_school := btrim(split_part(coalesce(a.payload->>'school', ''), ',', 1));
  v_city   := nullif(btrim(split_part(coalesce(a.payload->>'school', ''), ',', 2)), '');

  -- how they'll reach people becomes the card's tags
  if jsonb_typeof(a.payload->'channels') = 'array' then
    select string_agg(x, ', ') into v_focus
      from (select jsonb_array_elements_text(a.payload->'channels') as x limit 3) t;
  else
    v_focus := nullif(btrim(coalesce(a.payload->>'channels', '')), '');
  end if;

  insert into public.ambassadors
      (application_id, full_name, email, school, city, grad_year, display_name, focus,
       is_adult, show_publicly, status, agreed_terms_at, completed_at, listed_at)
  values
      (p_application_id, coalesce(a.name, v_display), a.email,
       nullif(v_school, ''), v_city, nullif(btrim(coalesce(a.payload->>'grad_year', '')), ''),
       v_display, v_focus,
       null, v_show, 'completed', a.created_at, now(), now());

  update public.applications set status = 'accepted' where id = p_application_id;

  return query select coalesce(a.name, v_display), v_display, v_show, false;
end $$;

grant execute on function public.approve_ambassador(text, uuid) to anon;

notify pgrst, 'reload schema';

-- ── 4. where things stand ────────────────────────────────────────────────────────────
select (select count(*) from public.applications
         where type = 'ambassador' and status not in ('archived','rejected'))      as ambassador_applications,
       (select count(*) from public.applications
         where type = 'ambassador' and payload->>'show_publicly' = 'yes')          as opted_in_to_the_page,
       (select count(*) from public.ambassadors)                                   as ambassadors,
       (select count(*) from public.list_ambassadors())                            as cards_on_page;

-- If someone applied before the opt-in tick existed and later tells you they're happy to be
-- listed, that is the one case you set by hand:
--   update public.ambassadors set show_publicly = true where full_name = 'Name Here';
