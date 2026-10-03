/* Batch Zero — /review/: the review desk.
   Reads applications and outstanding invites with the admin key, and turns a yes into an
   invite link without retyping anything. The key lives in this page's memory only — it is
   never stored, never put in a URL, and every call checks it again inside Postgres. */
(function () {
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const gate = $("#key-form");
  if (!gate || !window.B0) return;

  let KEY = null;
  const make = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const say = (sel, text) => { const el = $(sel); if (!el) return; el.textContent = text; el.style.display = text ? "block" : "none"; };
  const when = (iso) => { try { return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" }); } catch (e) { return ""; } };

  /* payload keys are form field names — make them readable without hard-coding a list,
     so a new question on any form shows up here automatically */
  const label = (k) => k.replace(/_/g, " ").replace(/^./, c => c.toUpperCase());
  const SKIP = new Set(["consent", "agree", "linkedin_verified", "linkedin_id", "linkedin_name",
                        "linkedin_email", "photo_url", "name", "email"]);

  function answers(payload) {
    const wrap = make("dl", "rv-answers");
    Object.keys(payload || {}).forEach(k => {
      if (SKIP.has(k)) return;
      let v = payload[k];
      if (Array.isArray(v)) v = v.join(", ");
      if (v == null || String(v).trim() === "") return;
      wrap.appendChild(make("dt", null, label(k)));
      wrap.appendChild(make("dd", null, String(v)));
    });
    return wrap;
  }

  function linkBox(link) {
    const box = make("div", "rv-link");
    box.appendChild(make("code", null, link));
    const copy = make("button", "btn btn-ghost btn-sm", "Copy link");
    copy.type = "button";
    copy.onclick = () => navigator.clipboard.writeText(link).then(
      () => { copy.textContent = "Copied"; setTimeout(() => { copy.textContent = "Copy link"; }, 1500); },
      () => { copy.textContent = "Select it and copy"; });
    box.appendChild(copy);
    return box;
  }

  /* ── one application ─────────────────────────────────────────────────── */
  function applicationCard(app, onChanged) {
    const el = make("article", "rv-card");
    const head = make("div", "rv-head");
    head.appendChild(make("h3", null, app.name || "(no name)"));
    head.appendChild(make("span", "rv-pill", app.type));
    head.appendChild(make("span", "rv-when", when(app.created_at)));
    if (app.status && app.status !== "new") head.appendChild(make("span", "rv-pill rv-status", app.status));
    el.appendChild(head);
    if (app.email) el.appendChild(make("p", "rv-email", app.email));
    el.appendChild(answers(app.payload));
    if (app.notes) el.appendChild(make("p", "rv-note", `Note: ${app.notes}`));

    const msg = make("p", "rv-msg");
    const acts = make("div", "rv-acts");

    const mark = (status, text) => {
      const b = make("button", "btn btn-ghost btn-sm", text);
      b.type = "button";
      b.onclick = async () => {
        b.disabled = true;
        try {
          await window.B0.rpc("set_application_status", { p_admin_key: KEY, p_id: app.id, p_status: status });
          onChanged();
        } catch (err) { msg.textContent = err.message || "Couldn't save that."; b.disabled = false; }
      };
      return b;
    };

    if (app.type === "ambassador") {
      const invite = make("button", "btn btn-primary btn-sm btn-bracket", "Approve → create signup link");
      invite.type = "button";
      invite.onclick = async () => {
        invite.disabled = true; invite.textContent = "Creating…";
        try {
          const p = app.payload || {};
          // "Monte Vista High, Danville CA" → school and city, if they wrote it that way
          const where = String(p.school || "").split(",");
          const token = await window.B0.rpc("create_ambassador_invite", {
            p_admin_key: KEY,
            p_full_name: app.name,
            p_email: app.email || null,
            p_school: (where[0] || "").trim() || null,
            p_city: (where[1] || "").trim() || null,
            p_grad_year: p.grad_year || null,
          });
          await window.B0.rpc("set_application_status", { p_admin_key: KEY, p_id: app.id, p_status: "accepted" });
          el.appendChild(linkBox(`${location.origin}/ambassador-invite/?token=${encodeURIComponent(token)}`));
          invite.remove();
          msg.textContent = "Send them this link. Their card goes up when they fill it in.";
        } catch (err) {
          msg.textContent = err.message || "Couldn't create the link.";
          invite.disabled = false; invite.textContent = "Approve → create signup link";
        }
      };
      acts.appendChild(invite);
    }
    acts.appendChild(mark("rejected", "Not a fit"));
    acts.appendChild(mark("archived", "Archive"));
    el.appendChild(acts);
    el.appendChild(msg);
    return el;
  }

  /* ── load everything ─────────────────────────────────────────────────── */
  async function load() {
    const type = $("#type-filter").value || null;
    const status = $("#status-filter").value || null;
    const list = $("#app-list"), chase = $("#chase-list");
    list.textContent = ""; chase.textContent = "";
    say("#rv-error", "");

    let apps, invites;
    try {
      [apps, invites] = await Promise.all([
        window.B0.rpc("list_applications", { p_admin_key: KEY, p_type: type, p_status: status }),
        window.B0.rpc("list_outstanding_invites", { p_admin_key: KEY }),
      ]);
    } catch (err) {
      say("#rv-error", err.message === "Not authorised"
        ? "That key wasn't right."
        : (err.message || "Couldn't load. Have you run supabase/review.sql?"));
      $("#desk").hidden = true; $("#gate").hidden = false;
      return;
    }

    $("#gate").hidden = true; $("#desk").hidden = false;

    apps = Array.isArray(apps) ? apps : [];
    $("#app-count").textContent = `// ${apps.length} application${apps.length === 1 ? "" : "s"}`;
    if (!apps.length) list.appendChild(make("p", "rv-empty", "// nothing here right now."));
    apps.forEach(a => list.appendChild(applicationCard(a, load)));

    invites = Array.isArray(invites) ? invites : [];
    $("#chase-count").textContent = `// ${invites.length} link${invites.length === 1 ? "" : "s"} sent but not used yet`;
    if (!invites.length) chase.appendChild(make("p", "rv-empty", "// everyone who got a link has used it."));
    invites.forEach(i => {
      const el = make("article", "rv-card rv-slim");
      const head = make("div", "rv-head");
      head.appendChild(make("h3", null, i.full_name));
      head.appendChild(make("span", "rv-pill", i.kind));
      if (i.extra) head.appendChild(make("span", "rv-when", i.extra));
      el.appendChild(head);
      if (i.email) el.appendChild(make("p", "rv-email", i.email));
      const base = i.kind === "mentor" ? "/mentor-invite/" : "/ambassador-invite/";
      el.appendChild(linkBox(`${location.origin}${base}?token=${encodeURIComponent(i.invite_token)}`));
      chase.appendChild(el);
    });
  }

  gate.addEventListener("submit", (e) => {
    e.preventDefault();
    KEY = $("[name=admin_key]", gate).value.trim();
    if (!KEY) return;
    load();
  });
  $("#type-filter").addEventListener("change", () => KEY && load());
  $("#status-filter").addEventListener("change", () => KEY && load());
  $("#reload").addEventListener("click", () => KEY && load());
})();
