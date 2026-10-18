# batchzero.co — website

Static site. No framework, no build step required to serve it — every file in this folder is what the browser gets.

```
index.html                 home (hero with the "Mentors:" strip, how it works, two doors, demo day, schedule, FAQ)
program/                   week-by-week program + selection rubric
about/
partners/                  "Which one are you?" chooser: investors / sponsor companies / mentors
apply/founders|mentors|investors|sponsors/   application forms → Supabase (see below); mentors is a 5-step flow with review + autosaved draft (details in AGENTS.md)
apply/companies/           redirect to /apply/sponsors/
supabase/schema.sql        the `applications` table + insert-only RLS policy
privacy/  terms/           placeholder legal pages
assets/css/site.css        all styling (design tokens at the top)
assets/js/config.js        Supabase URL + anon key (fill these in)
assets/js/site.js          nav, reveal-on-scroll, countdown, counters, form validation + Supabase submit
assets/js/roster.js        the public mentor roster (list_mentors()), shared by /network/ and the homepage
assets/js/home.js          the homepage "Mentors:" strip (slow drift, pause on hover)
assets/media/              hero-intro.webm / .mp4 (plays once on load), hero-poster.jpg
assets/img/                logo SVGs
favicon.*, og-image.png, site.webmanifest, robots.txt, sitemap.xml
Dockerfile + Caddyfile     how Railway serves it
tools/                     build.py + pages.py — regenerate the HTML after editing copy; test_*.py / *.mjs — tests
```

## Editing copy

The HTML pages are generated from `tools/pages.py` (one Python string per page, shared nav/footer in `tools/build.py`). Edit there and run `python3 tools/build.py`, or just edit the HTML files directly if you'd rather — both work, but the generator will overwrite direct edits next time it runs.

## Things to change before launch

- **Cohort deadline** — `CONFIG.cohortDeadline` at the top of `assets/js/site.js` drives the countdown; the schedule table on the home page and the "closes October 31" lines are plain text in `pages.py`.
- **Forms → Supabase** — three steps:
  1. In your Supabase project, open **SQL Editor** and run `supabase/schema.sql`. It creates `public.applications` with Row Level Security so the public key can only INSERT (never read).
  2. Copy **Project Settings → API → Project URL** and **anon public** key into `assets/js/config.js`.
  3. Push. Until the config is filled in, forms still show the confirmation but log `Supabase not configured` to the console and store nothing.
  Every submission lands as one row: `type` (founder / mentor / investor / sponsor), `name`, `email`, `payload` (all fields as JSON), `status` (new). Read them in the Supabase Table Editor, or build an admin view later.
- **Privacy / terms** — drafted in plain English for the pre-incorporation stage; have a lawyer review before the first cohort starts, and update the "who we are" sections when the company is formed.
- **Email** — `hello@batchzero.co` is used throughout; set up the mailbox (Namecheap Private Email, Google Workspace, or forwarding).

## Running locally

```
python3 -m http.server 8080
# → http://localhost:8080
```

## Tests

`.github/workflows/tests.yml` runs all of these on every push. Locally, from this folder:

```
python3 -m unittest tools/test_archive_mentor_photos.py tools/test_roster_js.py     # needs node for some
pip install playwright && python3 -m playwright install chromium                    # once
python3 -m unittest tools/test_home_strip.py                                        # homepage + /network/ in a real browser
npm i --prefix /tmp/pglite @electric-sql/pglite                                     # once
PGLITE=/tmp/pglite/node_modules/@electric-sql/pglite/dist/index.js node tools/test_mentor_roster_sql.mjs
```

## Deploying

Railway (Dockerfile → Caddy static server): push this folder to a repo connected to the Railway service, or `railway up` from this folder with the Railway CLI. Caddy serves on `$PORT`, with clean URLs and long-cache headers for `/assets/`.

Any other static host works too (Vercel, Netlify, Cloudflare Pages): point it at this folder, no build command, output directory `.`.
