-- Batch Zero — referrals ($100 per accepted startup)
--
-- Run once in Supabase → SQL Editor, after schema.sql, ambassadors.sql and review.sql.
-- Safe to run again.
--
-- WHAT IT DOES
--   1. Lets /refer/ store referrers in public.applications with type = 'referrer'. Like
--      ambassadors.sql, the type has to be added in BOTH places that list the allowed types
--      (the column CHECK and the insert policy). Until this runs, referral.js falls back to
--      type 'unknown' with payload.kind = 'referrer', so no signup is lost either way.
--   2. Adds referral_report(admin_key): every founder application that names a referrer — by
--      code (payload.ref, from the link they applied through) or by name (payload.referred_by,
--      what they typed) — with the matched referrer's contact details and the founder's status.
--      Filter on founder_status = 'accepted' and you have the payout list.
--
-- HOW A FOUNDER IS MATCHED TO A REFERRER
--   payload.ref on the founder row  =  payload.code on a referrer row  (exact, case-insensitive).
--   No code → the typed name comes back in referred_by_typed for you to match by eye.
--   Rule printed on /refer/: one $100 per accepted startup, to the referrer whose code is on the
--   application; no code → whoever the founder named.

-- 1 ── allow the type ─────────────────────────────────────────────────────────
alter table public.applications drop constraint if exists applications_type_check;
alter table public.applications add constraint applications_type_check
  check (type in ('founder','mentor','investor','sponsor','ambassador','referrer','unknown'));

drop policy if exists "anon can submit applications" on public.applications;
create policy "anon can submit applications"
  on public.applications for insert
  to anon
  with check (
    type in ('founder','mentor','investor','sponsor','ambassador','referrer','unknown')
    and length(coalesce(email,'')) <= 200
    and pg_column_size(payload) <= 20000
  );

-- referrers stored before this ran (type 'unknown', kind 'referrer') become proper rows
update public.applications
   set type = 'referrer'
 where type = 'unknown' and payload->>'kind' = 'referrer';

create index if not exists applications_ref_idx  on public.applications (lower(payload->>'ref'))  where type = 'founder';
create index if not exists applications_code_idx on public.applications (lower(payload->>'code')) where type = 'referrer';

-- 2 ── the payout report ──────────────────────────────────────────────────────
drop function if exists public.referral_report(text);

create or replace function public.referral_report(p_admin_key text)
returns table (
  founder_id        uuid,
  applied_at        timestamptz,
  founder_name      text,
  startup           text,
  founder_status    text,
  ref_code          text,
  referred_by_typed text,
  referrer_name     text,
  referrer_email    text,
  referrer_role     text,
  referrer_school   text,
  referrer_club     text
)
language plpgsql security definer set search_path = public, private as $$
begin
  perform private.check_admin_key(p_admin_key);       -- defined in review.sql
  return query
    select f.id, f.created_at, f.name, f.payload->>'company', f.status,
           nullif(f.payload->>'ref', ''), nullif(btrim(f.payload->>'referred_by'), ''),
           r.name, r.email, r.payload->>'role', r.payload->>'school', nullif(r.payload->>'club', '')
      from public.applications f
      left join lateral (
             select x.name, x.email, x.payload
               from public.applications x
              where x.type = 'referrer'
                and lower(x.payload->>'code') = lower(f.payload->>'ref')
              order by x.created_at
              limit 1) r on true
     where f.type = 'founder'
       and (coalesce(f.payload->>'ref', '') <> '' or coalesce(btrim(f.payload->>'referred_by'), '') <> '')
     order by (f.status = 'accepted') desc, f.created_at desc;
end $$;

grant execute on function public.referral_report(text) to anon;   -- the key, not the role, is the gate

notify pgrst, 'reload schema';

-- Check it took:
--   select pg_get_constraintdef(oid) from pg_constraint where conname = 'applications_type_check';
--   select * from public.referral_report('<admin key>');
--   payout list:  select * from public.referral_report('<admin key>') where founder_status = 'accepted';
