/* Batch Zero — /mentor-invite/admin/: create an invite link for one mentor.
   The admin key is checked inside the create_mentor_invite() function in Postgres; this page
   only passes it through and never stores it. */
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
      const token = await window.B0.rpc("create_mentor_invite", {
        p_admin_key: v("admin_key"),
        p_full_name: v("full_name"),
        p_linkedin_url: v("linkedin_url") || null,
        p_title: v("title") || null,
        p_company: v("company") || null,
        p_bio: v("bio") || null,
      });
      const link = `${location.origin}/mentor-invite/?token=${encodeURIComponent(token)}`;
      $("#link-box").textContent = link;
      $("#result-box").hidden = false;

      $("#copy-btn").onclick = () => {
        navigator.clipboard.writeText(link).then(() => say("Link copied."), () => say("Couldn't copy — select the link and copy it."));
      };
      $("#mail-btn").onclick = () => {
        const name = v("full_name"), first = name.split(" ")[0];
        const subject = "You're invited to mentor for Batch Zero";
        const body = `Hi ${first},\n\nI'd love to have you as a mentor for Batch Zero's upcoming cohort — about 1–2 hours a week, one session with a founder team plus light prep.\n\nHere's your signup link, with your details already filled in:\n${link}\n\nLet me know if you have any questions.\n\nRayan`;
        location.href = `mailto:${encodeURIComponent(v("email"))}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      };
    } catch (err) {
      console.error("[B0] invite creation failed", err);
      say(err.message || "Something went wrong.");
    } finally {
      btn.disabled = false; btn.innerHTML = label;
    }
  });
})();
