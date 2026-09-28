/* Batch Zero — /ambassador-invite/: the invited-ambassador signup.
   Loads the invite by its token, then calls submit_ambassador_signup(). No LinkedIn here:
   ambassadors are high-school students, and no photo of theirs goes on the site. */
(function () {
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const form = $("#amb-form");
  if (!form || !window.B0) return;

  const show = (id) => $$(".state").forEach(el => el.classList.toggle("active", el.id === id));
  const setText = (sel, text) => { const el = $(sel); if (el) el.textContent = text; };
  const val = (n) => { const el = $(`[name="${n}"]`, form); return el ? el.value.trim() : ""; };
  const msg = $("#form-msg");
  const fail = (text) => { msg.textContent = text; msg.style.display = "block"; };

  // the token rides in the URL; keep a copy in case the page is reloaded without it
  const params = new URLSearchParams(location.search);
  let token = params.get("token");
  try {
    if (token) sessionStorage.setItem("b0-amb-token", token);
    else token = sessionStorage.getItem("b0-amb-token");
  } catch (e) {}

  /* "Maya Rivera" → "Maya R." — what we suggest for the card, so a student isn't
     publishing their full legal name unless they decide to. */
  function shortName(full) {
    const parts = String(full || "").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return "";
    if (parts.length === 1) return parts[0];
    return `${parts[0]} ${parts[parts.length - 1][0].toUpperCase()}.`;
  }

  // Under 18 → a parent or guardian has to be on record before anything goes public.
  const guardian = $("#guardian-box");
  function syncGuardian() {
    const picked = $("input[name=age_band]:checked", form);
    const under = !picked || picked.value === "under18";
    guardian.hidden = !under;
    $$("input", guardian).forEach(el => {
      el.required = under;
      if (!under) { el.value = ""; el.closest(".field").classList.remove("err"); }
    });
  }
  $$("input[name=age_band]", form).forEach(r => r.addEventListener("change", syncGuardian));

  function getFocus() {
    const picked = $$('input[type=checkbox][name="focus"]:checked', form).map(b => b.value);
    const extra = ($('[name="focus_other"]', form) || {}).value || "";
    return picked.filter(v => v !== "Other")
                 .concat(extra.split(/[,;]/).map(a => a.trim()).filter(Boolean))
                 .join(", ");
  }
  function setFocus(value) {
    const wanted = String(value || "").split(/[,;]/).map(a => a.trim()).filter(Boolean);
    if (!wanted.length) return;
    const boxes = $$('input[type=checkbox][name="focus"]', form);
    const leftovers = [];
    wanted.forEach(a => {
      const hit = boxes.find(b => b.value.toLowerCase() === a.toLowerCase());
      if (hit) { hit.checked = true; hit.dispatchEvent(new Event("change", { bubbles: true })); }
      else leftovers.push(a);
    });
    if (leftovers.length) {
      const other = boxes.find(b => b.value === "Other");
      if (other) { other.checked = true; other.dispatchEvent(new Event("change", { bubbles: true })); }
      const text = $('[name="focus_other"]', form);
      if (text) text.value = leftovers.join(", ");
    }
  }

  async function load() {
    if (!token) { show("state-invalid"); return; }
    let rows;
    try {
      rows = await window.B0.rpc("get_ambassador_invite", { p_token: token });
    } catch (err) {
      console.error("[B0] ambassador invite lookup failed", err);
      show("state-invalid");
      return;
    }
    const invite = Array.isArray(rows) ? rows[0] : rows;
    if (!invite) { show("state-invalid"); return; }

    if (invite.status !== "pending") {
      setText("#done-msg", invite.status === "completed"
        ? "You've already signed up as a Batch Zero ambassador. Nothing else to do — we'll be in touch."
        : "This invite is no longer active. Email hello@batchzero.co and we'll sort it out.");
      show("state-done");
      return;
    }

    setText("#hi-name", (invite.full_name || "there").split(/\s+/)[0]);
    setText("#avatar", (invite.full_name || "—").trim().split(/\s+/).slice(0, 2)
      .map(w => w[0] || "").join("").toUpperCase() || "—");
    setText("#p-name", invite.full_name || "—");
    const where = [invite.school, invite.city].filter(Boolean).join(" · ");
    const roleEl = $("#p-role");
    roleEl.textContent = where;
    roleEl.hidden = !where;

    const prefill = {
      email: invite.email, school: invite.school, city: invite.city,
      grad_year: invite.grad_year,
      display_name: invite.display_name || shortName(invite.full_name),
    };
    Object.keys(prefill).forEach(name => {
      const el = $(`[name="${name}"]`, form);
      if (!el || !prefill[name]) return;
      el.value = prefill[name];
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    setFocus(invite.focus);
    syncGuardian();
    show("state-form");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";
    if (!window.B0.validate(form)) return;
    const agree = $("[name=agree]", form);
    if (!agree.checked) { agree.closest(".check").classList.add("err"); agree.focus(); return; }

    const picked = $("input[name=age_band]:checked", form);
    const isAdult = !!picked && picked.value === "18plus";

    const btn = $("#submit-btn"), label = btn.innerHTML;
    btn.disabled = true; btn.textContent = "Signing you up…";
    try {
      await window.B0.rpc("submit_ambassador_signup", {
        p_token: token,
        p_email: val("email"),
        p_school: val("school"),
        p_city: val("city") || null,
        p_grad_year: val("grad_year") || null,
        p_display_name: val("display_name"),
        p_focus: getFocus() || null,
        p_is_adult: isAdult,
        p_guardian_name: isAdult ? null : (val("guardian_name") || null),
        p_guardian_email: isAdult ? null : (val("guardian_email") || null),
        p_show_publicly: !!$("[name=show_publicly]", form).checked,
        p_agree: true,
      });
      try { sessionStorage.removeItem("b0-amb-token"); } catch (err) {}
      setText("#done-msg", $("[name=show_publicly]", form).checked
        ? "You're on the ambassador roster — your card is on the network page now."
        : "You're on the team. We've kept you off the public page, as you asked — email us any time to change that.");
      show("state-done");
    } catch (err) {
      console.error("[B0] ambassador signup failed", err);
      fail(err.message || "Something went wrong — try again, or email hello@batchzero.co.");
      btn.disabled = false; btn.innerHTML = label;
    }
  });

  load();
})();
