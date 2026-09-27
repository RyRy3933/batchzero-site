-- Batch Zero — allow ambassador applications
--
-- /apply/ambassadors/ writes into the same public.applications table as the other four forms,
-- with type = 'ambassador'. Both the column CHECK and the insert policy list the allowed types,
-- so both have to learn the new one or every ambassador application is rejected by the database.
--
-- Safe to run on the live project: it re-creates the constraint and the policy with the same
-- rules as supabase/schema.sql, plus 'ambassador'. Existing rows are unaffected.

alter table public.applications drop constraint if exists applications_type_check;
alter table public.applications add constraint applications_type_check
  check (type in ('founder','mentor','investor','sponsor','ambassador','unknown'));

drop policy if exists "anon can submit applications" on public.applications;
create policy "anon can submit applications"
  on public.applications for insert
  to anon
  with check (
    type in ('founder','mentor','investor','sponsor','ambassador','unknown')
    and length(coalesce(email,'')) <= 200
    and pg_column_size(payload) <= 20000
  );

-- Check it took:
--   select pg_get_constraintdef(oid) from pg_constraint where conname = 'applications_type_check';
--   select with_check from pg_policies where policyname = 'anon can submit applications';
