/* Batch Zero — /network/: the two public rosters.
   Mentors come from list_mentors() through roster.js (shared with the homepage strip),
   ambassadors from list_ambassadors(). Both functions return only what a card may show — no
   email, no token, nothing private — so there is nothing here to leak. Every value goes in
   through textContent, never innerHTML. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const R = window.B0Roster;
  if (!window.B0 || !R) return;
  const { make } = R;

  /* One card, mentor or ambassador: photo (initials underneath until it paints), name, role, tags.
     Ambassadors only reach this page if they ticked "show me on the network page", which covers
     their photo (supabase/ambassador-photos.sql). */
  function card({ name, role, tags, photos }) {
    const el = make("article", "mentor-card");
    el.appendChild(R.photoTile(name, photos));
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

  /* Wire one roster: load the rows, fill the grid, or say why it's empty. */
  function roster({ load, prefix, toCard, label }) {
    const grid = $(`[data-${prefix}-grid]`);
    if (!grid) return;
    const loading = $(`[data-${prefix}-loading]`),
          empty   = $(`[data-${prefix}-empty]`),
          error   = $(`[data-${prefix}-error]`),
          count   = $(`[data-${prefix}-count]`);
    const hide = (el) => { if (el) el.hidden = true; };
    const showEl = (el) => { if (el) el.hidden = false; };

    load().then((rows) => {
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
      console.error(`[B0] ${label} roster failed`, err);
      hide(loading);
      showEl(error);
    });
  }

  roster({
    load: R.mentors, prefix: "mentor", label: "mentor",
    toCard: (m) => ({ name: m.name, role: m.role, tags: m.areas, photos: m.photos }),
  });

  roster({
    load: R.ambassadors, prefix: "amb", label: "ambassador",
    toCard: (a) => ({
      name: a.name,
      role: [a.school, a.city].filter(Boolean).join(" · "),
      tags: (a.grad_year ? [`Class of ${a.grad_year}`] : []).concat(a.focus),
      photos: a.photos,
    }),
  });
})();
