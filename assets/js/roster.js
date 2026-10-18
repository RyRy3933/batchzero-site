/* Batch Zero — the public mentor roster, shared by every page that shows mentors.
   /network/ (network.js) and the homepage strip (home.js) both read mentors through here, so the
   photo fallbacks, the LinkedIn link check and the one list_mentors() call live in one place.

   list_mentors() returns only what a card is allowed to show (see supabase/mentor-roster.sql):
   full_name, title, company, areas_of_expertise, photo_url, bio, linkedin_url. No email, no token.
   Every value goes into the page through textContent or a checked href — never innerHTML.

   Load order: config.js → site.js (defines window.B0) → roster.js → the page script. */
(function () {
  "use strict";

  const make = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const initials = (name) =>
    (name || "").trim().split(/\s+/).slice(0, 2).map(w => w[0] || "").join("").toUpperCase() || "—";
  const split = (s) => String(s || "").split(/[,;]/).map(a => a.trim()).filter(Boolean);
  const clean = (s, max) => {
    const t = String(s == null ? "" : s).replace(/\s+/g, " ").trim();
    return max && t.length > max ? t.slice(0, max - 1).trimEnd() + "…" : t;
  };

  /* Self-hosted mentor photos. LinkedIn photo links expire after a few weeks, so a daily
     GitHub Action (.github/workflows/mentor-photos.yml → tools/archive_mentor_photos.py)
     copies each mentor's photo into assets/img/mentors/ while the link is still fresh and
     lists it in photos.json, keyed by slug(full_name). Cards use that copy first and only
     fall back to the LinkedIn link for someone the Action hasn't caught yet.
     slug() must stay identical to slug() in tools/archive_mentor_photos.py (a test checks). */
  const PHOTO_DIR = "/assets/img/mentors/";
  const slug = (name) =>
    String(name || "").normalize("NFKD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  let manifestP = null;
  // never rejects: a missing or broken manifest just means "no local photos yet"
  const localPhotos = () => manifestP || (manifestP =
    fetch(PHOTO_DIR + "photos.json", { cache: "no-cache" })
      .then(r => (r.ok ? r.json() : {}))
      .then(m => (m && typeof m === "object" && !Array.isArray(m) ? m : {}))
      .catch(() => ({})));
  const localPhoto = (manifest, name) => {
    const file = (manifest || {})[slug(name)];
    // a bare file name only — the manifest can't point the page anywhere else
    return typeof file === "string" && /^[a-z0-9-]+\.(jpe?g|png|webp)$/.test(file) ? PHOTO_DIR + file : "";
  };

  /* A LinkedIn profile link, or "" if it isn't one. The database already filters these
     (mentor-roster.sql); this is the second lock, because an href is the one place a bad value
     could do harm. Accepts linkedin.com and its country subdomains, /in/ and /pub/ profile
     paths only, and always hands back a clean https URL with no query, hash or credentials. */
  function linkedInUrl(raw) {
    let s = String(raw == null ? "" : raw).trim();
    if (!s || /\s/.test(s) || s.length > 300) return "";
    if (!/^[a-z][a-z0-9+.-]*:/i.test(s)) s = "https://" + s.replace(/^\/+/, "");
    let u;
    try { u = new URL(s); } catch (e) { return ""; }
    if (u.protocol !== "https:" && u.protocol !== "http:") return "";
    if (u.username || u.password || u.port) return "";
    const host = u.hostname.toLowerCase();
    if (host !== "linkedin.com" && !host.endsWith(".linkedin.com")) return "";
    if (!/^\/(in|pub)\/[^/]+/i.test(u.pathname)) return "";
    return "https://" + host + u.pathname;
  }

  /* The round portrait. The initials are ALWAYS in the tile, with the photo layered on top. A
     LinkedIn photo URL can expire, 403, or — as seen live — hang forever without ever firing
     `error`, and an onerror handler alone leaves an empty circle in that last case. Layering
     means the tile is never blank: if the image never paints, the initials are still showing.
     Sources are tried in order (our copy, then LinkedIn); after the last one fails the <img>
     is removed so there's no broken-image icon on top of the initials. */
  function photoTile(name, sources, cls) {
    const tile = make("div", cls || "m-photo");
    tile.appendChild(make("span", "m-ini", initials(name)));
    const queue = (sources || []).filter(Boolean);
    if (queue.length) {
      const img = document.createElement("img");
      img.alt = ""; img.loading = "lazy"; img.decoding = "async"; img.referrerPolicy = "no-referrer";
      img.addEventListener("error", () => {
        if (queue.length) img.src = queue.shift(); else img.remove();
      });
      img.src = queue.shift();
      tile.appendChild(img);
    }
    return tile;
  }

  /* One list_mentors() row → what a card needs. */
  function normalize(r, manifest) {
    const m = r || {};
    const name = clean(m.full_name, 120);
    const title = clean(m.title, 120), company = clean(m.company, 120);
    return {
      name,
      title,
      company,
      role: [title, company].filter(Boolean).join(" · "),
      areas: split(m.areas_of_expertise),
      bio: clean(m.bio, 600),
      linkedin: linkedInUrl(m.linkedin_url),
      photos: [localPhoto(manifest, name), m.photo_url].filter(Boolean),
    };
  }

  /* Every listed mentor, newest first (the database orders them). One request per page load,
     however many scripts ask. Rejects if the call fails, so each page can show its own error. */
  let mentorsP = null;
  function mentors() {
    if (!mentorsP) {
      if (!window.B0 || typeof window.B0.rpc !== "function") return Promise.reject(new Error("site.js not loaded"));
      mentorsP = Promise.all([window.B0.rpc("list_mentors"), localPhotos()])
        .then(([rows, manifest]) => (Array.isArray(rows) ? rows : []).map(r => normalize(r, manifest)).filter(m => m.name))
        .catch(err => { mentorsP = null; throw err; });
    }
    return mentorsP;
  }

  window.B0Roster = { make, initials, split, clean, slug, localPhoto, localPhotos, linkedInUrl, photoTile, normalize, mentors };
})();
