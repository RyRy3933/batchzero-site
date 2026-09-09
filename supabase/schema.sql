-- Batch Zero — applications table
-- Run this once in Supabase → SQL Editor. Safe to re-run.

create extension if not exists pgcrypto;

create table if not exists public.applications (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  type        text not null check (type in ('founder','mentor','investor','sponsor','unknown')),
  name        text,
  email       text,
  payload     jsonb not null,
  source      text,
  user_agent  text,
  status      text not null default 'new' check (status in ('new','reviewing','accepted','rejected','archived')),
  notes       text
);

create index if not exists applications_type_created_idx on public.applications (type, created_at desc);
create index if not exists applications_email_idx on public.applications (lower(email));

-- Row Level Security: the public anon key may INSERT only. It can never read, update or delete.
alter table public.applications enable row level security;

drop policy if exists "anon can submit applications" on public.applications;
create policy "anon can submit applications"
  on public.applications for insert
  to anon
  with check (
    type in ('founder','mentor','investor','sponsor','unknown')
    and length(coalesce(email,'')) <= 200
    and pg_column_size(payload) <= 20000
  );

-- Nobody but service_role / the dashboard reads rows (no select policy for anon or authenticated).

-- Optional: keep the REST surface tight
revoke all on public.applications from anon;
grant insert on public.applications to anon;
