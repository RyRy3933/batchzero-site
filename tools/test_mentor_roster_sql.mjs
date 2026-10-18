// Runs supabase/mentor-roster.sql against real Postgres (PGlite, Postgres compiled to WASM) on a
// copy of public.mentors, and checks exactly what list_mentors() hands the public key.
//
//   npm i --prefix /tmp/pglite @electric-sql/pglite          # once, anywhere outside the repo
//   PGLITE=/tmp/pglite/node_modules/@electric-sql/pglite/dist/index.js node tools/test_mentor_roster_sql.mjs
//
// The repo deliberately has no package.json (see AGENTS.md), so PGlite is loaded from $PGLITE.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const { PGlite } = await import(process.env.PGLITE || "@electric-sql/pglite");
const ROOT = fileURLToPath(new URL("..", import.meta.url));
const SQL = readFileSync(ROOT + "supabase/mentor-roster.sql", "utf8");
const db = new PGlite();

await db.exec(`
  create role anon; create role authenticated;
  -- the live table, as recorded in supabase/mentor-invites.sql
  create table public.mentors (
    id uuid primary key default gen_random_uuid(), invite_token uuid unique not null default gen_random_uuid(),
    created_at timestamptz not null default now(), full_name text not null, linkedin_url text, title text, company text,
    bio text, email text, areas_of_expertise text, status text not null default 'pending',
    agreed_terms_at timestamptz, completed_at timestamptz, photo_url text, published boolean, listed_at timestamptz);
  alter table public.mentors enable row level security;
  -- the live list_mentors() before this change (5 columns), so the upgrade path is what's tested
  create function public.list_mentors()
  returns table (full_name text, title text, company text, areas_of_expertise text, photo_url text)
  language sql security definer set search_path = public stable as $$
    select m.full_name, m.title, m.company, m.areas_of_expertise, m.photo_url from public.mentors m $$;
  insert into public.mentors (full_name, title, company, areas_of_expertise, email, bio, linkedin_url, listed_at) values
    ('Ok Https',    'CEO', 'A', 'Sales, Product', 'a@x.co', '  Builds   things. ', 'https://www.linkedin.com/in/ok-https/', '2026-10-01'),
    ('No Scheme',   'CTO', 'B', 'Engineering',    'b@x.co', null,                  'linkedin.com/in/no-scheme',            null),
    ('Country Sub', 'VP',  'C', 'Design',         'c@x.co', '',                    'https://uk.linkedin.com/in/country',   null),
    ('JS Link',     'X',   'D', 'Ops',            'd@x.co', 'bio',                 'javascript:alert(1)',                  null),
    ('Lookalike',   'X',   'E', 'Ops',            'e@x.co', 'bio',                 'https://linkedin.com.evil.net/in/x',   null),
    ('Company Pg',  'X',   'F', 'Ops',            'f@x.co', 'bio',                 'https://www.linkedin.com/company/foo', null),
    ('Quote Inj',   'X',   'G', 'Ops',            'g@x.co', 'bio',                 'https://www.linkedin.com/in/a"onmouseover="x', null),
    ('Long Bio',    'X',   'H', 'Ops',            'h@x.co', repeat('word ', 300),  'HTTP://LINKEDIN.COM/in/Caps',          null),
    ('Pending',     'X',   'I', null,             'i@x.co', 'not signed up',       'https://www.linkedin.com/in/pending',  null),
    ('Hidden',      'X',   'J', 'Ops',            'j@x.co', 'taken down',          'https://www.linkedin.com/in/hidden',   null);
  update public.mentors set published = false where full_name = 'Hidden';
`);

await db.exec(SQL);
const stamps = (await db.query(`select full_name, listed_at from public.mentors order by full_name`)).rows;
await db.exec(SQL); // a second run must change nothing
assert.deepEqual((await db.query(`select full_name, listed_at from public.mentors order by full_name`)).rows, stamps, "idempotent");

const res = await db.query(`select * from public.list_mentors()`);
const cols = res.fields.map(f => f.name);
assert.deepEqual(cols, ["full_name", "title", "company", "areas_of_expertise", "photo_url", "bio", "linkedin_url"]);
const by = Object.fromEntries(res.rows.map(r => [r.full_name, r]));
assert.equal(res.rows.length, 8);
assert.ok(!by.Pending, "unfinished signups stay off");
assert.ok(!by.Hidden, "published = false stays off");
assert.equal(res.rows.at(-1).full_name, "Ok Https", "newest signup leads; the one stamped earlier comes last");
assert.equal(by["Ok Https"].linkedin_url, "https://www.linkedin.com/in/ok-https/");
assert.equal(by["No Scheme"].linkedin_url, "linkedin.com/in/no-scheme");
assert.equal(by["Country Sub"].linkedin_url, "https://uk.linkedin.com/in/country");
assert.equal(by["Long Bio"].linkedin_url, "HTTP://LINKEDIN.COM/in/Caps");
for (const bad of ["JS Link", "Lookalike", "Company Pg", "Quote Inj"]) assert.equal(by[bad].linkedin_url, null, bad);
assert.equal(by["Ok Https"].bio, "Builds   things.");
assert.equal(by["No Scheme"].bio, null);
assert.equal(by["Country Sub"].bio, null, "empty bio → null");
assert.ok(by["Long Bio"].bio.length <= 600);

// the listed_at trigger survived the cascade drop and still stamps a new signup
await db.exec(`update public.mentors set areas_of_expertise = 'Product' where full_name = 'Pending'`);
assert.ok((await db.query(`select listed_at from public.mentors where full_name = 'Pending'`)).rows[0].listed_at);
// exactly one list_mentors() (two overloads make PostgREST refuse the call), callable by the public key
assert.equal((await db.query(`select count(*)::int n from pg_proc where proname = 'list_mentors'`)).rows[0].n, 1);
assert.equal((await db.query(`select has_function_privilege('anon', 'public.list_mentors()', 'execute') ok`)).rows[0].ok, true);
// and the public key still can't read the table itself
assert.equal((await db.query(`select has_table_privilege('anon', 'public.mentors', 'select') ok`)).rows[0].ok, false);

console.log(`mentor-roster.sql: all checks passed (${res.rows.length} mentors listed)`);
