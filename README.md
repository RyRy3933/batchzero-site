# batchzero.co — website

Static site. No framework, no build step required to serve it — every file in this folder is what the browser gets.

```
index.html                 home (video hero, how it works, four doors, demo day, schedule, FAQ)
program/                   week-by-week program + selection rubric
about/
apply/founders|mentors|investors|companies/   application forms (UI only — see below)
privacy/  terms/           placeholder legal pages
assets/css/site.css        all styling (design tokens at the top)
assets/js/site.js          nav, reveal-on-scroll, countdown, counters, form validation
assets/media/              hero-loop.webm / .mp4 (8-second seamless ping-pong loop), hero-poster.jpg
assets/img/                logo SVGs
favicon.*, og-image.png, site.webmanifest, robots.txt, sitemap.xml
Dockerfile + Caddyfile     how Railway serves it
tools/                     build.py + pages.py — regenerate the HTML after editing copy
```

## Editing copy

The HTML pages are generated from `tools/pages.py` (one Python string per page, shared nav/footer in `tools/build.py`). Edit there and run `python3 tools/build.py`, or just edit the HTML files directly if you'd rather — both work, but the generator will overwrite direct edits next time it runs.

## Things to change before launch

- **Cohort deadline** — `CONFIG.cohortDeadline` at the top of `assets/js/site.js` drives the countdown; the schedule table on the home page and the "closes October 31" lines are plain text in `pages.py`.
- **Forms** — currently UI-only. On submit they validate, log the data to the console, and show the confirmation state. Wire them up in `site.js` (look for `TODO: wire to backend`) — a Supabase insert or a form endpoint is a ~10-line change.
- **Privacy / terms** — placeholders. Replace before processing applications from minors.
- **Email** — `hello@batchzero.co` is used throughout; set up the mailbox (Namecheap Private Email, Google Workspace, or forwarding).

## Running locally

```
python3 -m http.server 8080
# → http://localhost:8080
```

## Deploying

Railway (Dockerfile → Caddy static server): push this folder to a repo connected to the Railway service, or `railway up` from this folder with the Railway CLI. Caddy serves on `$PORT`, with clean URLs and long-cache headers for `/assets/`.

Any other static host works too (Vercel, Netlify, Cloudflare Pages): point it at this folder, no build command, output directory `.`.
