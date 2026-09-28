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
apply/{founders,mentors,investors,sponsors,ambassadors}/   application forms (companies/ is a redirect to sponsors/)
network/                         public hub: the mentor roster (rendered from the database) + what ambassadors do
mentors/                         redirect to /network/#mentors (the roster used to live here)
mentor-invite/                   invited-mentor signup, /admin/ to create a link, /terms/ (mentor ToS) — noindex
supabase/schema.sql              applications table + RLS (anon = insert only)
supabase/mentor-invites.sql      mentor_invites table + the three RPCs — READ ITS HEADER FIRST
supabase/mentor-roster.sql       adds photo_url/published/listed_at + list_mentors() and save_mentor_photo()
supabase/ambassadors.sql         lets applications accept type 'ambassador' (constraint + insert policy)
404.html                         GitHub Pages 404
assets/css/site.css              all styling; design tokens in :root at the top
assets/js/config.js              Supabase URL + anon key (public by design; the DB only allows inserts)
assets/js/site.js                nav, reveal-on-scroll, countdown, counters, form validation, step-by-step forms, drafts, LinkedIn sign-in, Supabase submit
assets/js/mentor-invite.js       /mentor-invite/ page script (loads the invite, submits it)
assets/js/mentor-invite-admin.js /mentor-invite/admin/ page script (creates an invite link)
assets/js/mentors.js             /mentors/ page script (renders the roster)
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
| 01 You | `first_name` `last_name` `email` `linkedin` `title` `company` `location` `timezone` `other_links`* + LinkedIn sign-in (below) |
| 02 Track record | `years_experience` `furthest_stage` `background`[] `shipped` `didnt_work` |
| 03 Where you help | `mentor_type` (Domain expert / Generalist / Either — the program pairs one of each per team) `expertise`[] `top_skill` `stages`[] `markets`[]* |
| 04 How you mentor | `mentored_before` `mentored_where`* `teen_experience` `style`[] (max 3) `scenario` `why` |
| 05 Commitment | `hours` `teams` `cohorts`[] `session_times`[] + opt-ins `judge_demo_day` `open_to_invest` `guest_session` `make_intros` ("yes"/"no") `heard_from`* `anything_else`* |
| 06 Review | every answer with Edit links, then `consent` |

`*` optional · `[]` always a JSON array (empty if nothing picked). Every mentor row also has `form_version: "mentor-v2"`; rows without it came from the older one-page form (which used a single `role` field instead of `title` + `company`).

How the flow works (all in `site.js`, no dependencies): a `form.app[data-steps]` shows one `[data-step]` panel at a time with Back / Continue, validates each step before moving on (required text, email/URL format, `data-required` chip and radio groups, `data-max` chip limits), keeps browser Back/Forward in step with `#step-N`, and builds the review screen from the live form. `data-autosave` saves an unfinished draft to `localStorage` (`b0-draft:/apply/mentors/`; never the consent box) and offers "Start over" — it's disclosed in the privacy policy, section 2. Without JavaScript every step renders as one long page.

Limits: the database rejects payloads over 20 KB (`supabase/schema.sql`). Long answers have `maxlength` (the whole form at max length is ~7.4 KB) and `site.js` refuses to send anything over 18 KB with a friendly message, so nobody hits a silent RLS error.

### "Continue with LinkedIn" (optional, off by default)

`LINKEDIN_SIGNIN` in `assets/js/config.js` turns it on. It uses Supabase's own `linkedin_oidc` provider with plain `fetch` — no SDK, no server, no secret in the repo:

1. The button sends the mentor to `<SUPABASE_URL>/auth/v1/authorize?provider=linkedin_oidc&redirect_to=<this page>`.
2. They come back with a token in the URL fragment. `site.js` reads `/auth/v1/user` once, fills `first_name`, `last_name` and `email` **only where they're still empty**, shows the photo, then calls `/auth/v1/logout`. The token is never stored and the fragment is wiped from the URL.
3. The identity rides along in hidden `data-draft` inputs, so it survives the draft and lands in the payload: `linkedin_verified` (`yes`/`no`), `linkedin_id`, `linkedin_name`, `linkedin_email`, `photo_url`. When the button isn't shown, none of these are sent.

Things that will bite whoever touches this next:

- **LinkedIn's sign-in only returns name, email, photo and locale** — no headline, no work history, no profile URL. That's why role, company and the LinkedIn link are still typed, and why the `linkedin` field stays required.
- **`photo_url` is a LinkedIn CDN link and expires.** Download the image when you approve a mentor; don't hotlink it from a public page months later.
- **Applications are still inserted with the anon key**, never the signed-in user's token — the RLS policy only grants `insert` to `anon`, so sending the user token instead would fail.
- Turning the flag on without configuring the provider would send mentors to a Supabase error page, so keep it off until setup is done.

Setup, once: create a Batch Zero LinkedIn Page → [linkedin.com/developers](https://www.linkedin.com/developers/) → create an app against that page → Products → request **Sign In with LinkedIn using OpenID Connect** (self-serve, instant) → Auth → add redirect URL `https://lzinyfukedgytwvgszna.supabase.co/auth/v1/callback` → copy Client ID + Secret into Supabase → Authentication → Providers → LinkedIn (OIDC) → in Supabase → Authentication → URL Configuration add `https://batchzero.co/**` to the redirect allow-list → set `LINKEDIN_SIGNIN: true` and push. If you ever want their full work history, that's partner-only on LinkedIn's side — enrich from their profile URL at review time instead.

## The mentor pipeline — two doors, one roster

```
/apply/mentors/      public application  → public.applications (type 'mentor')   ← anyone can apply
        ↓ you review in the Supabase table editor
/mentor-invite/admin/  you create an invite link with their details prefilled    ← admin key
        ↓ you email them the link
/mentor-invite/?token=…  they verify with LinkedIn, confirm details, accept the mentor ToS
        ↓
public.mentors (status 'completed', areas filled in)  → the roster you match teams from
        ↓ instantly, no approval step
/network/#mentors  public page: photo, name, role · company, top three areas
```

**The table is `public.mentors`, keyed by `invite_token` (uuid).** Not `mentor_invites` — an earlier
version of `supabase/mentor-invites.sql` said that and it cost an afternoon of debugging. See the
header of that file for everything that is actually live, read out of the catalog.

### Student ambassadors

Ambassadors have the same two doors as mentors, and for the same reason: the application is how
strangers reach you, the invite is how someone you've decided on gets onto the roster.

```
/apply/ambassadors/       public application → public.applications (type 'ambassador')
        ↓ you review
/ambassador-invite/admin/ you create a signup link with their details prefilled   ← same admin key
        ↓ you email them the link
/ambassador-invite/?token=…  they confirm, choose their public name, give consent
        ↓ instantly
public.ambassadors → /network/#ambassadors
```

`supabase/ambassadors.sql` has to be run once for the *application* form to work at all: **two places
list the allowed types** (the column CHECK and the insert policy) and both must know `'ambassador'`,
or every application is rejected by the database. `formType()` in `site.js` maps the URL to the type.
`supabase/ambassador-roster.sql` builds the table, the three invite functions and `list_ambassadors()`.

**Ambassadors are minors, so this flow is deliberately not the mentor flow:**

- **No photos, ever.** There is no photo column. Cards are initials tiles. Don't add one.
- **Nothing is public unless they tick the box** (`show_publicly`). Leave it off and they're still an
  ambassador — they're just not listed.
- **Under 18 → a parent or guardian name and email are required** before the card can appear.
  `list_ambassadors()` enforces this in SQL, not just in the form: drop the guardian email and the
  card drops off the page.
- **They choose the name that shows.** The form suggests first name + last initial ("Maya R.");
  they can make it their full name, but that's their call, not the default.
- The card shows chosen name, school, city, class year and up to three tags. Email and guardian
  contact are never in `list_ambassadors()`'s result — keep it that way.

The admin key is shared with mentor invites. It lives as a constant inside `create_mentor_invite()`
and, since `ambassador-roster.sql` ran, also in `private.settings` under `'ambassador_admin_key'`.
Rotate both together.

### The public roster

`/network/` renders both rosters from `assets/js/network.js`: `list_mentors()` and
`list_ambassadors()`. Each returns **only** the fields the card shows. Email, token and guardian
contact are never in either result — keep it that way if you extend them. The two calls are
independent, so one failing still renders the other.

`list_mentors()` returns `full_name, title, company, areas_of_expertise, photo_url`.

- **A mentor counts as signed up when `areas_of_expertise` is non-empty.** `create_mentor_invite()`
  never sets it; `submit_mentor_signup()` always does, because the form makes them pick three. That
  is the whole publishing rule — there is no approval step and no status to flip.
- Publishing is immediate and consented: the mentor ticks the mentor ToS, which says their name,
  photo, title, company and bio may be shown on the site. To take someone down:
  `update public.mentors set published = false where full_name = '…';` — no code change, the page
  picks it up on next load. `published` is null by default, which means visible.
- `save_mentor_photo(p_token, p_photo_url)` is called by `/mentor-invite/` right after a mentor confirms, when they signed in with LinkedIn. It only accepts `*.licdn.com` URLs and only touches the row whose token is passed.
- **Those photo URLs expire.** The card falls back to the mentor's initials when the image 404s, so the page never looks broken — but for anyone you want to keep on the page long-term, download the image, host it yourself and update `photo_url`.
- `mentors.listed_at` is stamped by a trigger the first time areas are filled in, so the newest mentor leads the page. Later edits don't move it.
- The roster lives on `/network/`; `/mentors/` is a redirect kept for old links. The page is client-rendered, so search engines mostly see the empty state. That's fine for a roster; don't build anything SEO-critical this way.

The two are deliberately separate: the application is how strangers reach you, the invite is how someone you've decided on gets onto the roster. An invite link works once and is the only thing protecting that row, so treat it like a password — never post one publicly.

Every page flagged `noindex` in `PAGES` is kept out of `sitemap.xml` and added to `robots.txt`
automatically by `build.py` — so a new invite or admin page can't be indexed by being forgotten.
Flag private pages `noindex` and that's all you have to do.

### Shared plumbing (learn this before touching a form)

- `window.B0.rpc(name, args)` calls a Postgres function with the anon key. **Page scripts use this instead of pulling supabase-js from a CDN** — the SDK was removed from these pages on purpose. `window.B0.validate(form)` runs the same validation the built-in forms use.
- **Every `form.app` gets the generic submit handler that inserts into `applications`.** A form that submits itself must carry `data-custom-submit` or it will write a junk row on every submit — that exact bug was live for a day when the invite form was added with `class="app"` and its own handler. It keeps the shared validation, chips, counters and LinkedIn wiring either way.
- The LinkedIn block (`linkedin_block()` in `pages.py`) works on any form: it fills `first_name`, `last_name` and `email` when those fields exist, and fires a `b0:linkedin` event on the form with `{verified, name, email, photo}` so a page script can react — the invite page uses it to lock the email field and swap in the profile photo.
- The invite token is kept in `sessionStorage` (`b0-invite-token` for mentors, `b0-amb-token` for ambassadors), because the LinkedIn round trip comes back without the query string and people reload.

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
- **The guardian email is collected but nothing emails them yet.** The ambassador signup records the
  parent/guardian name and address and the card won't appear without one, but sending them the note
  the form promises is still a manual job. Do that before the first under-18 ambassador goes live.
- **There is no ambassador agreement page.** The signup links `/terms/` and `/privacy/`; mentors get
  `/mentor-invite/terms/` and `/conduct/`. Ambassadors should get their own short agreement.

## Don'ts

- Don't add a build toolchain (npm, bundlers, frameworks) — the whole point is that the folder is the site.
- Don't add analytics, trackers, or third-party scripts without asking; the site is aimed at minors.
- Don't change the domain, `CNAME`, or Pages settings without confirming with Rayan.
- Don't remove the accessibility basics already there (reduced-motion fallbacks, labels on inputs, aria-current on nav).
