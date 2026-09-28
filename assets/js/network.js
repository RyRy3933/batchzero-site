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

  /* One card. photo is optional and only ever used for mentors — ambassador cards are
     initials by design: they're high-school students and their faces don't go on the web.

     The initials are ALWAYS in the tile, with the photo layered on top of them. A LinkedIn
     photo URL can expire, 403, or — as seen live — hang forever without ever firing `error`,
     and an onerror handler alone leaves an empty circle in that last case. Layering means the
     tile is never blank: if the image never paints, the initials are simply still showing. */
  function card({ name, role, tags, photo }) {
    const el = make("article", "mentor-card");
    const tile = make("div", "m-photo");
    tile.appendChild(make("span", "m-ini", initials(name)));
    if (photo) {
      const img = document.createElement("img");
      img.src = photo; img.alt = ""; img.loading = "lazy"; img.referrerPolicy = "no-referrer";
      // a failed image would otherwise show a broken-image icon on top of the initials
      img.addEventListener("error", () => img.remove());
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
  function roster({ fn, prefix, toCard, label }) {
    const grid = $(`[data-${prefix}-grid]`);
    if (!grid) return;
    const loading = $(`[data-${prefix}-loading]`),
          empty   = $(`[data-${prefix}-empty]`),
          error   = $(`[data-${prefix}-error]`),
          count   = $(`[data-${prefix}-count]`);
    const hide = (el) => { if (el) el.hidden = true; };
    const showEl = (el) => { if (el) el.hidden = false; };

    window.B0.rpc(fn).then(rows => {
      hide(loading);
      const list = Array.isArray(rows) ? rows : [];
      if (!list.length) { showEl(empty); return; }
      const frag = document.createDocumentFragment();
      list.forEach(r => frag.appendChild(card(toCard(r))));
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
    toCard: (m) => ({
      name: m.full_name,
      role: [m.title, m.company].filter(Boolean).join(" · "),
      tags: split(m.areas_of_expertise),
      photo: m.photo_url,
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
