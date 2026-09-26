/* Batch Zero — /mentors/: the public roster, straight from the mentor_invites table
   through list_mentors(), which only ever returns name, title, company, areas and photo. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const grid = $("[data-mentor-grid]");
  if (!grid || !window.B0) return;

  const loading = $("[data-mentor-loading]"), empty = $("[data-mentor-empty]");
  const error = $("[data-mentor-error]"), count = $("[data-mentor-count]");
  const make = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const initials = (name) => (name || "").trim().split(/\s+/).slice(0, 2).map(w => w[0] || "").join("").toUpperCase() || "—";

  function card(m) {
    const el = make("article", "mentor-card");
    const photo = make("div", "m-photo");
    if (m.photo_url) {
      const img = document.createElement("img");
      img.src = m.photo_url; img.alt = ""; img.loading = "lazy"; img.referrerPolicy = "no-referrer";
      // LinkedIn photo links expire — fall back to initials rather than a broken image
      img.addEventListener("error", () => { photo.textContent = initials(m.full_name); });
      photo.appendChild(img);
    } else {
      photo.textContent = initials(m.full_name);
    }
    el.appendChild(photo);

    el.appendChild(make("h3", "m-name", m.full_name || "—"));
    const role = [m.title, m.company].filter(Boolean).join(" · ");
    if (role) el.appendChild(make("p", "m-role", role));

    const areas = (m.areas_of_expertise || "").split(/[,;]/).map(a => a.trim()).filter(Boolean).slice(0, 4);
    if (areas.length) {
      const tags = make("div", "m-tags");
      areas.forEach(a => tags.appendChild(make("span", "m-tag", a)));
      el.appendChild(tags);
    }
    return el;
  }

  window.B0.rpc("list_mentors").then(rows => {
    loading.hidden = true;
    const list = Array.isArray(rows) ? rows : [];
    if (!list.length) { empty.hidden = false; return; }
    list.forEach(m => grid.appendChild(card(m)));
    grid.hidden = false;
    count.textContent = `// ${list.length} mentor${list.length === 1 ? "" : "s"} confirmed so far`;
    count.hidden = false;
  }).catch(err => {
    console.error("[B0] roster failed to load", err);
    loading.hidden = true;
    error.hidden = false;
  });
})();
