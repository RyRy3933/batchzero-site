/* Batch Zero — /network/: the two public rosters.
   Mentors come from list_mentors(), ambassadors from list_ambassadors(). Both functions return
   only what the card shows — no email, no token, nothing private — so there is nothing here to
   leak. Every value goes in through textContent, never innerHTML. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  if (!window.B0) return;

  const make = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const initials = (name) =>
    (name || "").trim().split(/\s+/).slice(0, 2).map(w => w[0] || "").join("").toUpperCase() || "—";
  const split = (s) => String(s || "").split(/[,;]/).map(a => a.trim()).filter(Boolean);

  /* Self-hosted mentor photos. LinkedIn photo links expire after a few weeks, so a daily
     GitHub Action (.github/workflows/mentor-photos.yml → tools/archive_mentor_photos.py)
     copies each mentor's photo into assets/img/mentors/ while the link is still fresh and
     lists it in photos.json, keyed by slug(full_name). The card uses that copy first and
     only falls back to the LinkedIn link for someone the Action hasn't caught yet.
     slug() must stay identical to slug() in tools/archive_mentor_photos.py. */
  const PHOTO_DIR = "/assets/img/mentors/";
  const slug = (name) =>
    String(name || "").normalize("NFKD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  // never rejects: a missing or broken manifest just means "no local photos yet"
  const localPhotos = fetch(PHOTO_DIR + "photos.json", { cache: "no-cache" })
    .then(r => (r.ok ? r.json() : {}))
    .then(m => (m && typeof m === "object" && !Array.isArray(m) ? m : {}))
    .catch(() => ({}));
  const localPhoto = (manifest, name) => {
    const file = manifest[slug(name)];
    // a bare file name only — the manifest can't point the page anywhere else
    return typeof file === "string" && /^[a-z0-9-]+\.(jpe?g|png|webp)$/.test(file) ? PHOTO_DIR + file : "";
  };

  /* One card. photo is optional and only ever used for mentors — ambassador cards are
     initials by design: they're high-school students and their faces don't go on the web.

     The initials are ALWAYS in the tile, with the photo layered on top of them. A LinkedIn
     photo URL can expire, 403, or — as seen live — hang forever without ever firing `error`,
     and an onerror handler alone leaves an empty circle in that last case. Layering means the
     tile is never blank: if the image never paints, the initials are simply still showing. */
  function card({ name, role, tags, photos }) {
    const el = make("article", "mentor-card");
    const tile = make("div", "m-photo");
    tile.appendChild(make("span", "m-ini", initials(name)));
    const queue = (photos || []).filter(Boolean);
    if (queue.length) {
      const img = document.createElement("img");
      img.alt = ""; img.loading = "lazy"; img.referrerPolicy = "no-referrer";
      // try each source in order (our copy, then LinkedIn); when the last one fails, remove
      // the img so there's no broken-image icon on top of the initials
      img.addEventListener("error", () => {
        if (queue.length) img.src = queue.shift(); else img.remove();
      });
      img.src = queue.shift();
      tile.appendChild(img);
    }
    el.appendChild(tile);
    el.appendChild(make("h3", "m-name", name || "—"));
    if (role) el.appendChild(make("p", "m-role", role));
    const list = (tags || []).filter(Boolean).slice(0, 4);
    if (list.length) {
      const wrap = make("div", "m-tags");
      list.forEach(t => wrap.appendChild(make("span", "m-tag", t)));
      el.appendChild(wrap);
    }
    return el;
  }

  /* Wire one roster: call the function, fill the grid, or say why it's empty. */
  function roster({ fn, prefix, toCard, label, before = Promise.resolve(null) }) {
    const grid = $(`[data-${prefix}-grid]`);
    if (!grid) return;
    const loading = $(`[data-${prefix}-loading]`),
          empty   = $(`[data-${prefix}-empty]`),
          error   = $(`[data-${prefix}-error]`),
          count   = $(`[data-${prefix}-count]`);
    const hide = (el) => { if (el) el.hidden = true; };
    const showEl = (el) => { if (el) el.hidden = false; };

    Promise.all([window.B0.rpc(fn), before]).then(([rows, extra]) => {
      hide(loading);
      const list = Array.isArray(rows) ? rows : [];
      if (!list.length) { showEl(empty); return; }
      const frag = document.createDocumentFragment();
      list.forEach(r => frag.appendChild(card(toCard(r, extra))));
      grid.appendChild(frag);
      grid.hidden = false;
      if (count) {
        count.textContent = `// ${list.length} ${label}${list.length === 1 ? "" : "s"} confirmed so far`;
        count.hidden = false;
      }
    }).catch(err => {
      console.error(`[B0] ${fn} failed`, err);
      hide(loading);
      showEl(error);
    });
  }

  roster({
    fn: "list_mentors", prefix: "mentor", label: "mentor",
    before: localPhotos,
    toCard: (m, manifest) => ({
      name: m.full_name,
      role: [m.title, m.company].filter(Boolean).join(" · "),
      tags: split(m.areas_of_expertise),
      photos: [localPhoto(manifest || {}, m.full_name), m.photo_url],
    }),
  });

  roster({
    fn: "list_ambassadors", prefix: "amb", label: "ambassador",
    toCard: (a) => ({
      name: a.display_name,
      role: [a.school, a.city].filter(Boolean).join(" · "),
      tags: (a.grad_year ? [`Class of ${a.grad_year}`] : []).concat(split(a.focus)),
    }),
  });
})();
