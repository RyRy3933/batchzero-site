// Runs supabase/ambassador-photos.sql against real Postgres (PGlite) on a copy of the live
// ambassadors + applications tables, and checks what list_ambassadors() hands the public key.
//
//   npm i --prefix /tmp/pglite @electric-sql/pglite          # once, anywhere outside the repo
//   PGLITE=/tmp/pglite/node_modules/@electric-sql/pglite/dist/index.js node tools/test_ambassador_photos_sql.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const { PGlite } = await import(process.env.PGLITE || "@electric-sql/pglite");
const ROOT = fileURLToPath(new URL("..", import.meta.url));
const SQL = readFileSync(ROOT + "supabase/ambassador-photos.sql", "utf8");
const db = new PGlite();

const LI = "https://media.licdn.com/dms/image/v2/X/profile-displayphoto-shrink_400_400/0?e=1&t=x";

await db.exec(`
  create role anon; create role authenticated;
  create schema private;
  create table public.applications (id uuid primary key default gen_random_uuid(), type text, name text,
    email text, payload jsonb, status text, created_at timestamptz default now());
  -- the live table: ambassador-roster.sql + ambassador-approve.sql
  create table public.ambassadors (
    id uuid primary key default gen_random_uuid(), invite_token uuid unique not null default gen_random_uuid(),
    created_at timestamptz not null default now(), full_name text not null, email text, school text, city text,
    grad_year text, display_name text, focus text, is_adult boolean, guardian_name text, guardian_email text,
    show_publicly boolean, published boolean, status text not null default 'pending', agreed_terms_at timestamptz,
    completed_at timestamptz, listed_at timestamptz, application_id uuid);
  alter table public.ambassadors enable row level security;
  revoke all on public.ambassadors from anon, authenticated;
  -- the live list_ambassadors() (5 columns), so the upgrade path is what's tested
  create function public.list_ambassadors()
  returns table (display_name text, school text, city text, grad_year text, focus text)
  language sql security definer set search_path = public stable as $$
    select a.display_name, a.school, a.city, a.grad_year, a.focus from public.ambassadors a
     where a.status = 'completed' and coalesce(a.show_publicly, false) and coalesce(a.published, true) $$;
  grant execute on function public.list_ambassadors() to anon, authenticated;

  insert into public.applications (id, type, name, payload) values
    ('00000000-0000-0000-0000-000000000001', 'ambassador', 'Li Signed', jsonb_build_object('photo_url', '${LI}')),
    ('00000000-0000-0000-0000-000000000002', 'ambassador', 'No Li',     '{}'),
    ('00000000-0000-0000-0000-000000000003', 'ambassador', 'Evil Link', '{"photo_url":"https://evil.example/x.jpg"}'),
    ('00000000-0000-0000-0000-000000000004', 'ambassador', 'Later',     jsonb_build_object('photo_url', '${LI}'));
  insert into public.ambassadors (full_name, display_name, status, show_publicly, published, application_id, listed_at, email, guardian_email) values
    ('Li Signed', 'Li S.',   'completed', true,  null,  '00000000-0000-0000-0000-000000000001', '2026-10-01', 'a@x.co', 'p@x.co'),
    ('No Li',     'No L.',   'completed', true,  null,  '00000000-0000-0000-0000-000000000002', '2026-10-02', 'b@x.co', null),
    ('Evil Link', 'Evil L.', 'completed', true,  null,  '00000000-0000-0000-0000-000000000003', '2026-10-03', 'c@x.co', null),
    ('Unticked',  'Un T.',   'completed', false, null,  null,                                   '2026-10-04', 'd@x.co', null),
    ('Hidden',    'Hid D.',  'completed', true,  false, null,                                   '2026-10-05', 'e@x.co', null),
    ('Invite',    'Inv I.',  'completed', true,  null,  null,                                   '2026-10-06', 'f@x.co', null);
`);

await db.exec(SQL);
const once = (await db.query(`select display_name, photo_url from public.ambassadors order by display_name`)).rows;
await db.exec(SQL); // a second run must change nothing
assert.deepEqual((await db.query(`select display_name, photo_url from public.ambassadors order by display_name`)).rows, once, "idempotent");

const res = await db.query(`select * from public.list_ambassadors()`);
assert.deepEqual(res.fields.map(f => f.name), ["display_name", "school", "city", "grad_year", "focus", "photo_url"],
  "only card fields — never email, guardian or token");
const by = Object.fromEntries(res.rows.map(r => [r.display_name, r]));
assert.equal(res.rows.length, 4, "same gates as before");
assert.ok(!by["Un T."], "no tick, no card, no photo");
assert.ok(!by["Hid D."], "published = false hides card and photo");
assert.equal(by["Li S."].photo_url, LI, "backfilled from the application's LinkedIn sign-in");
assert.equal(by["No L."].photo_url, null);
assert.equal(by["Evil L."].photo_url, null, "only LinkedIn image links are ever copied");
assert.equal(by["Inv I."].photo_url, null, "invite signups have no photo until one is added");
assert.equal(res.rows[0].display_name, "Inv I.", "newest first, as before");

// approve_ambassador() inserts with application_id → the trigger copies the photo
await db.exec(`insert into public.ambassadors (full_name, display_name, status, show_publicly, application_id, listed_at)
               values ('Later', 'Lat E.', 'completed', true, '00000000-0000-0000-0000-000000000004', now())`);
assert.equal((await db.query(`select photo_url from public.list_ambassadors() where display_name = 'Lat E.'`)).rows[0].photo_url, LI);
// a hand-set bad link is refused on insert too
await db.exec(`insert into public.ambassadors (full_name, display_name, status, show_publicly, photo_url)
               values ('Hand', 'Han D.', 'completed', true, 'javascript:alert(1)')`);
assert.equal((await db.query(`select photo_url from public.ambassadors where full_name = 'Hand'`)).rows[0].photo_url, null);

// exactly one list_ambassadors(), callable by the public key; the table and helpers are not
assert.equal((await db.query(`select count(*)::int n from pg_proc where proname = 'list_ambassadors'`)).rows[0].n, 1);
assert.equal((await db.query(`select has_function_privilege('anon', 'public.list_ambassadors()', 'execute') ok`)).rows[0].ok, true);
assert.equal((await db.query(`select has_table_privilege('anon', 'public.ambassadors', 'select') ok`)).rows[0].ok, false);
assert.equal((await db.query(`select has_function_privilege('anon', 'private.licdn_photo(text)', 'execute') ok`)).rows[0].ok, false);

console.log(`ambassador-photos.sql: all checks passed (${res.rows.length} ambassadors listed)`);
