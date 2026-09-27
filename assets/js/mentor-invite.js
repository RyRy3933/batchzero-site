/* Batch Zero — the invited-mentor signup at /mentor-invite/.
   Loads the invite by its token, lets the mentor confirm their details, and calls the
   submit_mentor_signup() Postgres function. No SDK: window.B0.rpc() does the talking. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const form = $("#mentor-form");
  if (!form || !window.B0) return;

  const show = (id) => document.querySelectorAll(".state").forEach(el => el.classList.toggle("active", el.id === id));
  const setText = (sel, text) => { const el = $(sel); if (el) el.textContent = text; };
  const initials = (name) => !name ? "–" : name.trim().split(/\s+/).slice(0, 2).map(w => w[0].toUpperCase()).join("");

  // the token rides in the URL; keep a copy because the LinkedIn round trip can drop the query string
  const params = new URLSearchParams(location.search);
  let token = params.get("token");
  try {
    if (token) sessionStorage.setItem("b0-invite-token", token);
    else token = sessionStorage.getItem("b0-invite-token");
  } catch (e) {}

  const msg = $("#form-msg");
  // the LinkedIn round trip and the invite lookup race each other; whoever wins, the
  // verified identity is the one that should end up on the card
  let verified = false;
  let photoUrl = "";
  const fail = (text) => { msg.textContent = text; msg.style.display = "block"; };

  // LinkedIn sign-in (shared with /apply/mentors/) confirms who they are and locks the email
  form.addEventListener("b0:linkedin", (e) => {
    const d = e.detail, email = $("[name=email]", form);
    verified = !!d.verified;
    photoUrl = d.verified ? (d.photo || "") : "";
    if (d.verified) {
      if (d.email && email) { email.value = d.email; email.readOnly = true; }
      if (d.name) setText("#p-name", d.name);
      if (d.photo) {
        const av = $("#avatar");
        av.textContent = "";
        const img = document.createElement("img");
        img.src = d.photo; img.alt = ""; img.referrerPolicy = "no-referrer";
        av.appendChild(img);
      }
    } else if (email) {
      email.readOnly = false;
    }
  });

  // areas are stored as one comma-separated string; the form shows them as chips + "Other"
  function setAreas(value) {
    const wanted = String(value || "").split(/[,;]/).map(a => a.trim()).filter(Boolean);
    if (!wanted.length) return;
    const boxes = Array.from(form.querySelectorAll('input[type=checkbox][name="areas"]'));
    const known = new Set(boxes.map(b => b.value.toLowerCase()));
    const leftovers = [];
    wanted.forEach(a => {
      const hit = boxes.find(b => b.value.toLowerCase() === a.toLowerCase());
      if (hit) { hit.checked = true; hit.dispatchEvent(new Event("change", { bubbles: true })); }
      else leftovers.push(a);
    });
    if (leftovers.length) {
      const other = boxes.find(b => b.value === "Other");
      if (other) { other.checked = true; other.dispatchEvent(new Event("change", { bubbles: true })); }
      const text = $('[name="areas_other"]', form);
      if (text) text.value = leftovers.join(", ");
    }
  }
  function getAreas() {
    const picked = Array.from(form.querySelectorAll('input[type=checkbox][name="areas"]:checked')).map(b => b.value);
    const extra = ($('[name="areas_other"]', form) || {}).value || "";
    return picked.filter(v => v !== "Other").concat(extra.split(/[,;]/).map(a => a.trim()).filter(Boolean)).join(", ");
  }

  async function load() {
    if (!token) { show("state-invalid"); return; }
    let rows;
    try {
      rows = await window.B0.rpc("get_mentor_invite", { p_token: token });
    } catch (err) {
      console.error("[B0] invite lookup failed", err);
      show("state-invalid");
      return;
    }
    const invite = Array.isArray(rows) ? rows[0] : rows;
    if (!invite) { show("state-invalid"); return; }

    if (invite.status === "completed") {
      setText("#done-msg", `You already confirmed as a Batch Zero mentor${invite.email ? ` (${invite.email})` : ""}. Thanks — we'll be in touch.`);
      show("state-done");
      return;
    }

    if (!verified) {
      setText("#avatar", initials(invite.full_name));
      setText("#p-name", invite.full_name || "—");
    }
    const role = [invite.title, invite.company].filter(Boolean).join(" · ");
    const roleEl = $("#p-role");
    roleEl.textContent = role;
    roleEl.hidden = !role;
    const link = $("#p-linkedin");
    if (invite.linkedin_url) { link.href = invite.linkedin_url; link.hidden = false; } else { link.hidden = true; }

    setAreas(invite.areas_of_expertise);
    const prefill = { email: invite.email, title: invite.title, company: invite.company, bio: invite.bio };
    Object.keys(prefill).forEach(name => {
      const el = $(`[name="${name}"]`, form);
      if (!el || !prefill[name]) return;
      if (el.readOnly) return;                    // LinkedIn already confirmed this one
      el.value = prefill[name];
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    show("state-form");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";
    if (!window.B0.validate(form)) return;
    const agree = $("[name=agree]", form);
    if (!agree.checked) { agree.closest(".check").classList.add("err"); agree.focus(); return; }

    const btn = $("#submit-btn");
    const label = btn.innerHTML;
    btn.disabled = true; btn.textContent = "Confirming…";
    const v = (n) => { const el = $(`[name="${n}"]`, form); return el ? el.value.trim() : ""; };
    try {
      await window.B0.rpc("submit_mentor_signup", {
        p_token: token, p_email: v("email"), p_title: v("title"),
        p_company: v("company"), p_bio: v("bio"), p_areas: getAreas(), p_agree: true,
      });
      // put their face on /mentors/ — best effort, never blocks the confirmation
      if (photoUrl) {
        window.B0.rpc("save_mentor_photo", { p_token: token, p_photo_url: photoUrl })
          .catch(err => console.warn("[B0] couldn't save the profile photo", err));
      }
      try { sessionStorage.removeItem("b0-invite-token"); } catch (err) {}
      show("state-done");
    } catch (err) {
      console.error("[B0] mentor signup failed", err);
      fail(err.message || "Something went wrong — try again, or email hello@batchzero.co.");
      btn.disabled = false; btn.innerHTML = label;
    }
  });

  load();
})();
