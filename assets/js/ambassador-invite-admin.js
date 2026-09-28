/* Batch Zero — /ambassador-invite/admin/: create a signup link for one ambassador.
   The admin key is checked inside create_ambassador_invite() in Postgres; this page only
   passes it through and never stores it. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const form = $("#invite-form");
  if (!form || !window.B0) return;
  const msg = $("#form-msg");
  const say = (text) => { msg.textContent = text; msg.style.display = "block"; };
  const v = (n) => { const el = $(`[name="${n}"]`, form); return el ? el.value.trim() : ""; };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";
    if (!window.B0.validate(form)) return;

    const btn = $("#create-btn"), label = btn.innerHTML;
    btn.disabled = true; btn.textContent = "Creating…";
    try {
      const token = await window.B0.rpc("create_ambassador_invite", {
        p_admin_key: v("admin_key"),
        p_full_name: v("full_name"),
        p_email: v("email") || null,
        p_school: v("school") || null,
        p_city: v("city") || null,
        p_grad_year: v("grad_year") || null,
      });
      const link = `${location.origin}/ambassador-invite/?token=${encodeURIComponent(token)}`;
      $("#link-box").textContent = link;
      $("#result-box").hidden = false;

      $("#copy-btn").onclick = () => {
        navigator.clipboard.writeText(link).then(
          () => say("Link copied."),
          () => say("Couldn't copy — select the link and copy it."));
      };
      $("#mail-btn").onclick = () => {
        const first = v("full_name").split(" ")[0];
        const subject = "You're in — Batch Zero student ambassador";
        const body = `Hi ${first},\n\nWelcome aboard as a Batch Zero student ambassador. You'll run Batch Zero at your school: find the students already building something, get them to apply, and get the credit for it.\n\nHere's your signup link — it takes about two minutes, and your details are already filled in:\n${link}\n\nIf you're under 18 it'll ask for a parent or guardian's email. That's so we have their say-so before your name goes on the site.\n\nAny questions, just reply.\n\nRayan`;
        location.href = `mailto:${encodeURIComponent(v("email"))}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      };
    } catch (err) {
      console.error("[B0] ambassador invite creation failed", err);
      say(err.message || "Something went wrong.");
    } finally {
      btn.disabled = false; btn.innerHTML = label;
    }
  });
})();
