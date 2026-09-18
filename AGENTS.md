# AGENTS.md — batchzero.co

Instructions for any AI agent (or human) working in this folder. Read this before changing anything.

## What this is

The public marketing site for **Batch Zero**, an online accelerator for high-school founders (five startups per cohort, two mentors each, eight weeks, online Demo Day). Owner: Rayan (GitHub `RyRy3933`). Static HTML/CSS/JS — no framework, no package.json, no build server.

## Deploy — this is the important part

- **Repo:** `github.com/RyRy3933/batchzero-site` (branch `main`).
- **Hosting:** GitHub Pages, serving the repo root. **Every push to `main` redeploys automatically** (usually live within a minute). There is no staging environment — `main` is production.
- **Domain:** `batchzero.co` via the `CNAME` file in the repo root + A/CNAME records at Namecheap pointing to GitHub Pages. Do not delete or edit `CNAME`.
- `Dockerfile` / `Caddyfile` are an alternative self-hosted setup (Railway etc.). GitHub Pages ignores them; leave them in place.
- The `.git` folder in this local copy may be stale or absent. To publish, clone the repo fresh, copy changes in, commit, push:
  ```
  git clone https://github.com/RyRy3933/batchzero-site.git
  # copy your changed files in, then
  git add -A && git commit -m "describe the change" && git push origin main
  ```
- Never commit tokens, `.env` files, or anything under `_previews/` (it's gitignored).

## Layout

```
index.html                       home
program/  about/  privacy/  terms/   inner pages (each is <dir>/index.html)
partners/                        chooser page: investor / sponsor company / mentor
apply/{founders,mentors,investors,sponsors}/   application forms (companies/ is a redirect to sponsors/)
supabase/schema.sql              applications table + RLS (anon = insert only)
404.html                         GitHub Pages 404
assets/css/site.css              all styling; design tokens in :root at the top
assets/js/config.js              Supabase URL + anon key (public by design; the DB only allows inserts)
assets/js/site.js                nav, reveal-on-scroll, countdown, counters, form validation, step-by-step forms, drafts, Supabase submit
assets/media/                    hero-loop.webm/.mp4 (seamless loop), hero-poster.jpg
assets/img/                      logo SVGs (final approved [B0] mark — do not redesign)
tools/build.py, tools/pages.py   HTML generator (see below)
favicon.*, og-image.png, site.webmanifest, robots.txt, sitemap.xml, CNAME, .nojekyll
```

## How to edit content

The HTML files are **generated**. Shared `<head>`, nav and footer live in `tools/build.py`; each page body is a Python string in `tools/pages.py`; forms are built with the `field()` / `chips()` / `choice_cards()` / `optin()` / `consent()` helpers there, and step-by-step forms with `step()` / `review_step()` + `form_page(..., steps=True)`.

`tools/build.py` must keep running on **Python 3.10** (the Mac's default here): don't nest an `f"""` string inside another `f"""` — build each step body as its own string first, like `_MENTOR_STEP_1` in `pages.py`.

1. Edit `tools/pages.py` (copy) or `tools/build.py` (nav/footer/meta).
2. Run `python3 tools/build.py` from the site root — it rewrites every `index.html`, `404.html`, `sitemap.xml`, `robots.txt`, `site.webmanifest`.
3. Preview: `python3 -m http.server 8080` → http://localhost:8080 (root-relative links need a server, not `file://`).
4. Commit and push.

Editing the generated HTML directly works for a quick fix but will be overwritten the next time the generator runs — prefer `pages.py`.

## Site structure

Two primary CTAs everywhere (nav, hero, home "Which one are you?", bottom band): **I'm a founder** → `/apply/founders/` and **I'm a business partner** → `/partners/`, which fans out to investors / sponsor companies / mentors. Keep that split; don't add a fourth top-level audience without asking.

The founder application is deliberately short (nine questions, YC-style, for high-schoolers). Don't add fields without a strong reason.

## Mentor application (step-by-step)

`/apply/mentors/` is deliberately in depth (about 15 minutes) because mentors work directly with minors and we match two to every team. It is a five-step flow plus a review screen:

| Step | What it asks (payload keys) |
|---|---|
| 01 You | `first_name` `last_name` `email` `linkedin` `title` `company` `location` `timezone` `other_links`* |
| 02 Track record | `years_experience` `furthest_stage` `background`[] `shipped` `didnt_work` |
| 03 Where you help | `mentor_type` (Domain expert / Generalist / Either — the program pairs one of each per team) `expertise`[] `top_skill` `stages`[] `markets`[]* |
| 04 How you mentor | `mentored_before` `mentored_where`* `teen_experience` `style`[] (max 3) `scenario` `why` |
| 05 Commitment | `hours` `teams` `cohorts`[] `session_times`[] + opt-ins `judge_demo_day` `open_to_invest` `guest_session` `make_intros` ("yes"/"no") `heard_from`* `anything_else`* |
| 06 Review | every answer with Edit links, then `consent` |

`*` optional · `[]` always a JSON array (empty if nothing picked). Every mentor row also has `form_version: "mentor-v2"`; rows without it came from the older one-page form (which used a single `role` field instead of `title` + `company`).

How the flow works (all in `site.js`, no dependencies): a `form.app[data-steps]` shows one `[data-step]` panel at a time with Back / Continue, validates each step before moving on (required text, email/URL format, `data-required` chip and radio groups, `data-max` chip limits), keeps browser Back/Forward in step with `#step-N`, and builds the review screen from the live form. `data-autosave` saves an unfinished draft to `localStorage` (`b0-draft:/apply/mentors/`; never the consent box) and offers "Start over" — it's disclosed in the privacy policy, section 2. Without JavaScript every step renders as one long page.

Limits: the database rejects payloads over 20 KB (`supabase/schema.sql`). Long answers have `maxlength` (the whole form at max length is ~7.4 KB) and `site.js` refuses to send anything over 18 KB with a friendly message, so nobody hits a silent RLS error.

To make another form step-by-step or give it drafts: wrap its sections in `step()`, add a `review_step()`, and pass `steps=True` to `form_page` (drafts come with it). Keep the founder form short either way.

## Design rules

- Dark instrument-panel aesthetic: ink `#07080a` background, paper `#f5f5f0` text, accent blue `#3b6cff` (`--accent-2 #7aa0ff` for text on dark). **No green/lime anywhere** — the founder rejected it.
- Fonts: Space Grotesk (headings/body), JetBrains Mono (labels, numbers, `[bracketed]` tags). Loaded from Google Fonts.
- The `[B0]` logo is final and approved. Use the SVGs in `assets/img/`; never redraw, recolour beyond ink/paper/blue, or add effects. Full brand kit: `../batch-zero-logo/final/` (README inside).
- The hero video is the founder's own animation. Keep it muted, autoplay, looping, with the poster fallback.
- Keep the voice: direct, short sentences, no startup buzzwords, founders are addressed as "you".

## Things that are intentionally unfinished

- **Forms submit to Supabase** via plain `fetch` to the REST endpoint (`submitApplication()` in `site.js`), one row per submission in `public.applications` (`type`, `name`, `email`, `payload` jsonb, `status`). If `assets/js/config.js` has an empty URL/key the form shows the confirmation but stores nothing — check the console. Never add a SELECT policy for `anon`; applications from minors must not be publicly readable.
- **Cohort dates** are placeholders: countdown target `CONFIG.cohortDeadline` in `site.js`; the schedule table and "closes October 31" lines are text in `pages.py`. Keep them consistent when you change one.
- **Privacy / Terms** are real drafts (plain-English, pre-incorporation wording: "operated by its founder, no company yet"). Update section 1 of both when an entity is formed; keep the "last updated" date current; don't remove the not-yet-lawyer-reviewed note until a lawyer has reviewed them.
- `hello@batchzero.co` is referenced but the mailbox may not exist yet.

## Don'ts

- Don't add a build toolchain (npm, bundlers, frameworks) — the whole point is that the folder is the site.
- Don't add analytics, trackers, or third-party scripts without asking; the site is aimed at minors.
- Don't change the domain, `CNAME`, or Pages settings without confirming with Rayan.
- Don't remove the accessibility basics already there (reduced-motion fallbacks, labels on inputs, aria-current on nav).
