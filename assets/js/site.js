/* Batch Zero — site.js (vanilla, no dependencies) */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  /* ---- config: edit these ---- */
  const CONFIG = {
    cohortDeadline: "2026-10-31T23:59:00-07:00",   // Cohort 01 application deadline (Pacific)
  };

  /* ---- nav ---- */
  const nav = $(".nav");
  const onScroll = () => nav && nav.classList.toggle("scrolled", window.scrollY > 12);
  onScroll(); window.addEventListener("scroll", onScroll, { passive: true });
  const burger = $(".burger");
  if (burger) burger.addEventListener("click", () => document.body.classList.toggle("menu-open"));
  $$(".mobile-menu a").forEach(a => a.addEventListener("click", () => document.body.classList.remove("menu-open")));

  /* ---- current page highlight ---- */
  const here = location.pathname.replace(/index\.html$/, "");
  $$(".nav-links a").forEach(a => {
    const p = a.getAttribute("href");
    if (p && p !== "/" && here.startsWith(p)) a.setAttribute("aria-current", "page");
    if (p === "/" && (here === "/" || here === "")) a.setAttribute("aria-current", "page");
  });

  /* ---- cursor spotlight + card glow ---- */
  const spot = $(".spot");
  let hasMouse = false;
  window.addEventListener("pointermove", (e) => {
    if (e.pointerType !== "mouse") return;
    if (!hasMouse) { hasMouse = true; document.body.classList.add("has-mouse"); }
    if (spot) { spot.style.left = e.clientX + "px"; spot.style.top = e.clientY + "px"; }
  }, { passive: true });
  $$(".card").forEach(card => {
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty("--mx", ((e.clientX - r.left) / r.width * 100) + "%");
      card.style.setProperty("--my", ((e.clientY - r.top) / r.height * 100) + "%");
    });
  });

  /* ---- reveal on scroll ---- */
  const io = new IntersectionObserver((entries) => {
    entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  $$(".rv, .scorecard").forEach(el => io.observe(el));

  /* ---- counters ---- */
  const cio = new IntersectionObserver((entries) => {
    entries.forEach(en => {
      if (!en.isIntersecting) return;
      const el = en.target, target = parseFloat(el.dataset.count), suffix = el.dataset.suffix || "";
      const t0 = performance.now(), dur = 1400;
      const tick = (t) => {
        const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
        el.textContent = Math.round(target * e) + suffix;
        if (k < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick); cio.unobserve(el);
    });
  }, { threshold: 0.5 });
  $$("[data-count]").forEach(el => cio.observe(el));

  /* ---- countdown ---- */
  const cd = $("[data-countdown]");
  if (cd) {
    const end = new Date(CONFIG.cohortDeadline).getTime();
    const cells = { d: $("[data-d]", cd), h: $("[data-h]", cd), m: $("[data-m]", cd), s: $("[data-s]", cd) };
    const pad = (n) => String(n).padStart(2, "0");
    const upd = () => {
      let diff = Math.max(0, end - Date.now()) / 1000;
      const d = Math.floor(diff / 86400); diff -= d * 86400;
      const h = Math.floor(diff / 3600); diff -= h * 3600;
      const m = Math.floor(diff / 60); const s = Math.floor(diff - m * 60);
      cells.d.textContent = pad(d); cells.h.textContent = pad(h); cells.m.textContent = pad(m); cells.s.textContent = pad(s);
    };
    upd(); setInterval(upd, 1000);
  }

  /* ---- hero video: plays once on page load, then holds on the final frame ---- */
  $$("video[autoplay]").forEach(v => {
    v.muted = true; v.loop = false;
    const p = v.play(); if (p && p.catch) p.catch(() => {});
    v.addEventListener("ended", () => { v.pause(); v.currentTime = Math.max(0, v.duration - 0.05); });
  });

  /* ---- forms → Supabase ---- */
  const CFG = window.B0_CONFIG || {};
  // The database refuses payloads over 20 KB (supabase/schema.sql); stop a little short with a friendly message.
  const MAX_PAYLOAD_BYTES = 18000;
  const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  const URL_RE = /^https?:\/\/[^\s/.]+\.[^\s]+$/;
  const reduceMotion = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const pad2 = (n) => String(n).padStart(2, "0");
  const make = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };

  const formType = () => {
    const m = location.pathname.match(/\/apply\/(founders|mentors|investors|sponsors|companies)\//);
    return m ? { founders: "founder", mentors: "mentor", investors: "investor", sponsors: "sponsor", companies: "sponsor" }[m[1]] : "unknown";
  };
  async function submitApplication(type, data) {
    if (!CFG.SUPABASE_URL || !CFG.SUPABASE_ANON_KEY) {
      console.warn("[B0] Supabase not configured — application not stored:", data);
      return { ok: true, stored: false };
    }
    const row = {
      type,
      name: data.name || [data.first_name, data.last_name].filter(Boolean).join(" ") || null,
      email: data.email || null,
      payload: data,
      source: location.pathname,
      user_agent: navigator.userAgent.slice(0, 200),
    };
    const res = await fetch(`${CFG.SUPABASE_URL}/rest/v1/${CFG.TABLE || "applications"}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "apikey": CFG.SUPABASE_ANON_KEY, "Authorization": `Bearer ${CFG.SUPABASE_ANON_KEY}`, "Prefer": "return=minimal" },
      body: JSON.stringify(row),
    });
    if (!res.ok) throw new Error(`Supabase ${res.status}: ${await res.text()}`);
    return { ok: true, stored: true };
  }

  /* validation — one rule set for every form. A .field holds one text/select control, or a group of
     checkboxes/radios (data-required → at least one, data-max → at most N). Returns "" when fine. */
  const controls = (f) => $$("input:not([type=hidden]), textarea, select", f);
  function fieldProblem(f) {
    const inputs = controls(f), first = inputs[0];
    if (!first) return "";
    if (first.type === "checkbox" || first.type === "radio") {
      const n = inputs.filter(i => i.checked).length, max = parseInt(f.dataset.max || "0", 10);
      if (f.hasAttribute("data-required") && n === 0) return first.type === "radio" ? "// pick one" : "// pick at least one";
      if (max && n > max) return `// pick up to ${max}`;
      return "";
    }
    const v = first.value.trim();
    if (first.required && !v) return "// required — please fill this in";
    if (v && first.type === "email" && !EMAIL_RE.test(v)) return "// that email doesn't look right";
    if (v && first.type === "url" && !URL_RE.test(v)) return "// paste the full link, starting with https://";
    return "";
  }
  function showProblem(f, problem) {
    const msg = $(".msg", f);
    if (msg && problem) msg.textContent = problem;
    f.classList.toggle("err", !!problem);
  }
  function validateField(f) { const p = fieldProblem(f); showProblem(f, p); return !p; }
  function validateScope(root) {
    let firstBad = null;
    $$(".field", root).forEach(f => { if (!validateField(f) && !firstBad) firstBad = f; });
    return firstBad;
  }
  function focusField(f) {
    f.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
    const c = controls(f)[0];
    if (c) c.focus({ preventScroll: true });
  }

  /* values — checkbox groups (several boxes sharing a name) are lists; a lone checkbox is yes/no */
  function groupNames(form) {
    const count = {};
    $$("input[type=checkbox][name]", form).forEach(cb => { count[cb.name] = (count[cb.name] || 0) + 1; });
    return new Set(Object.keys(count).filter(k => count[k] > 1));
  }
  function collect(form) {
    const groups = groupNames(form), data = {};
    new FormData(form).forEach((v, k) => {
      if (typeof v === "string") v = v.trim();
      if (groups.has(k)) { (data[k] = data[k] || []).push(v); }
      else if (k in data) { data[k] = [].concat(data[k], v); }
      else { data[k] = v; }
    });
    $$("input[type=checkbox][name]", form).forEach(cb => {
      if (!(cb.name in data)) data[cb.name] = groups.has(cb.name) ? [] : "no";
    });
    // hidden fields we only fill sometimes (the LinkedIn identity) — leave them out when empty
    $$("input[type=hidden][data-draft]", form).forEach(h => { if (!data[h.name]) delete data[h.name]; });
    // only record a "no" when the sign-in was actually on offer
    if ($("[data-linkedin]:not([hidden])", form) && !data.linkedin_verified) data.linkedin_verified = "no";
    return data;
  }

  /* drafts (forms with data-autosave) — kept only in this browser, never sent until submit */
  function draftStore() {
    const key = "b0-draft:" + location.pathname;
    return {
      load() { try { const d = JSON.parse(localStorage.getItem(key) || "null"); return d && d.v === 1 && d.values ? d : null; } catch (e) { return null; } },
      save(d) { try { localStorage.setItem(key, JSON.stringify(d)); return true; } catch (e) { return false; } },
      clear() { try { localStorage.removeItem(key); } catch (e) {} },
    };
  }
  function snapshot(form) {
    const groups = groupNames(form), values = {};
    $$("input[name], textarea[name], select[name]", form).forEach(el => {
      if ((el.type === "hidden" && !el.hasAttribute("data-draft")) || el.name === "consent") return;
      if (el.type === "checkbox") {
        if (groups.has(el.name)) { values[el.name] = values[el.name] || []; if (el.checked) values[el.name].push(el.value); }
        else values[el.name] = el.checked;
      } else if (el.type === "radio") {
        if (el.checked) values[el.name] = el.value; else if (!(el.name in values)) values[el.name] = "";
      } else values[el.name] = el.value;
    });
    return values;
  }
  function restore(form, values) {
    $$("input[name], textarea[name], select[name]", form).forEach(el => {
      if ((el.type === "hidden" && !el.hasAttribute("data-draft")) || el.name === "consent" || !(el.name in values)) return;
      const v = values[el.name];
      if (el.type === "checkbox") el.checked = Array.isArray(v) ? v.includes(el.value) : v === true;
      else if (el.type === "radio") el.checked = v === el.value;
      else if (el.tagName === "SELECT") { if (Array.from(el.options).some(o => o.value === v)) el.value = v; }
      else if (typeof v === "string") el.value = el.maxLength > 0 ? v.slice(0, el.maxLength) : v;
    });
  }
  // "has the person actually answered anything?" — ignores values we pre-filled ourselves (auto)
  const hasContent = (values, auto) => Object.keys(values).some(k => {
    const v = values[k];
    if (auto && k in auto && auto[k] === v) return false;
    return Array.isArray(v) ? v.length > 0 : (v === true || (typeof v === "string" && v.trim() !== ""));
  });
  const when = (ts) => {
    const d = new Date(ts), today = new Date().toDateString() === d.toDateString();
    const time = d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    return today ? `today, ${time}` : `${d.toLocaleDateString([], { month: "short", day: "numeric" })}, ${time}`;
  };

  /* best guess at the mentor's time zone, only used to pre-select an empty dropdown */
  function guessZone() {
    let z = "";
    try { z = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
    if (/^America\/(Los_Angeles|Vancouver|Tijuana)$/.test(z)) return "Pacific (PT)";
    if (/^America\/(Denver|Phoenix|Boise|Edmonton|Chihuahua)$/.test(z)) return "Mountain (MT)";
    if (/^America\/(Chicago|Winnipeg|Mexico_City|Regina)$/.test(z)) return "Central (CT)";
    if (/^America\/(New_York|Toronto|Detroit|Montreal|Indiana\/)/.test(z)) return "Eastern (ET)";
    if (/^Europe\/(London|Dublin)$/.test(z)) return "UK / Ireland";
    if (/^Europe\//.test(z)) return "Europe (CET)";
    if (/^Asia\/(Kolkata|Calcutta)$/.test(z)) return "India (IST)";
    if (/^(Asia|Australia)\//.test(z) || z === "Pacific/Auckland") return "Asia-Pacific";
    return "";
  }

  /* Optional "Continue with LinkedIn" — Supabase's linkedin_oidc provider, no SDK.
     LinkedIn's sign-in returns name, email and photo only (no headline, no profile URL), so it
     fills those three and the rest is still typed. The access token is used once, never stored,
     and the session is closed straight after. Applications are still inserted with the anon key. */
  const LI_HIDDEN = ["linkedin_verified", "linkedin_id", "linkedin_name", "linkedin_email", "photo_url"];
  function setupLinkedIn(form, block, onChange) {
    const enabled = !!(CFG.LINKEDIN_SIGNIN && CFG.SUPABASE_URL && CFG.SUPABASE_ANON_KEY);
    if (!enabled) { block.hidden = true; return null; }
    const startBox = $(".li-start", block), doneBox = $(".li-done", block), note = $("[data-linkedin-note]", block);
    const orLine = $("[data-linkedin-or]", form), img = $("[data-linkedin-photo]", block);
    const hid = (n) => $(`input[name="${n}"]`, block);
    const val = (n) => (hid(n) ? hid(n).value : "");
    const setNote = (t) => { note.textContent = t || ""; note.hidden = !t; };
    const signed = () => val("linkedin_verified") === "yes";
    block.hidden = false;

    function refresh() {
      const on = signed();
      startBox.hidden = on; doneBox.hidden = !on;
      if (orLine) orLine.hidden = on;
      $$(".field.verified", form).forEach(f => f.classList.remove("verified"));
      if (!on) { img.removeAttribute("src"); return; }
      $("[data-linkedin-who]", block).textContent = [val("linkedin_name"), val("linkedin_email")].filter(Boolean).join(" · ");
      const photo = val("photo_url");
      img.hidden = !photo;
      if (photo) { img.src = photo; img.alt = val("linkedin_name") ? `${val("linkedin_name")} on LinkedIn` : ""; }
      ["first_name", "last_name", "email"].forEach(n => {
        const el = $(`[name="${n}"]`, form);
        if (el && el.value.trim()) el.closest(".field").classList.add("verified");
      });
    }
    function clear() { LI_HIDDEN.forEach(n => { if (hid(n)) hid(n).value = ""; }); setNote(""); refresh(); onChange(); }
    function fillIfEmpty(name, value) {
      const el = $(`[name="${name}"]`, form);
      if (el && value && !el.value.trim()) { el.value = value; el.dispatchEvent(new Event("input", { bubbles: true })); }
    }
    $("[data-linkedin-start]", block).addEventListener("click", () => {
      onChange();  // keep whatever they already typed before we leave the page
      const back = location.origin + location.pathname;
      location.href = `${CFG.SUPABASE_URL}/auth/v1/authorize?provider=linkedin_oidc&redirect_to=${encodeURIComponent(back)}`;
    });
    $("[data-linkedin-clear]", block).addEventListener("click", clear);

    async function fromRedirect() {
      const h = new URLSearchParams(location.hash.replace(/^#/, ""));
      const token = h.get("access_token"), err = h.get("error_description") || h.get("error");
      if (!token && !err) return;
      try { history.replaceState(history.state, "", location.pathname + location.search); } catch (e) {}
      if (!token) { setNote("// LinkedIn sign-in didn't finish — no problem, fill this in yourself."); return; }
      try {
        const res = await fetch(`${CFG.SUPABASE_URL}/auth/v1/user`, {
          headers: { apikey: CFG.SUPABASE_ANON_KEY, Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`auth ${res.status}`);
        const user = await res.json(), m = user.user_metadata || {};
        const full = m.name || "", first = m.given_name || full.split(" ")[0] || "";
        const lastName = m.family_name || full.split(" ").slice(1).join(" ");
        const email = user.email || m.email || "";
        if (hid("linkedin_verified")) hid("linkedin_verified").value = "yes";
        if (hid("linkedin_id")) hid("linkedin_id").value = user.id || m.sub || "";
        if (hid("linkedin_name")) hid("linkedin_name").value = full || [first, lastName].filter(Boolean).join(" ");
        if (hid("linkedin_email")) hid("linkedin_email").value = email;
        if (hid("photo_url")) hid("photo_url").value = m.picture || m.avatar_url || "";
        fillIfEmpty("first_name", first); fillIfEmpty("last_name", lastName); fillIfEmpty("email", email);
        refresh(); onChange();
      } catch (e) {
        console.error("[B0] LinkedIn sign-in failed", e);
        setNote("// couldn't read your LinkedIn profile — fill this in yourself and we'll manage.");
      } finally {
        // we only needed the profile once; don't leave a session behind
        try { fetch(`${CFG.SUPABASE_URL}/auth/v1/logout?scope=global`, { method: "POST", keepalive: true, headers: { apikey: CFG.SUPABASE_ANON_KEY, Authorization: `Bearer ${token}` } }).catch(() => {}); } catch (e) {}
      }
    }
    return { refresh, signed, fromRedirect };
  }

  /* step-by-step forms (form[data-steps]): each [data-step] panel is one screen */
  function makeStepper(form, hooks) {
    const panels = $$("[data-step]", form);
    if (panels.length < 2) return null;
    const last = panels.length - 1;
    const back = $("[data-step-back]", form), next = $("[data-step-next]", form), submit = $("button[type=submit]", form);
    let cur = 0, reached = 0;
    form.classList.add("stepper");

    const bar = make("div", "stepbar");
    const top = make("div", "sb-top"), count = make("span", "sb-count"), upcoming = make("span", "sb-next");
    const track = make("div", "sb-track"), live = make("p", "sr-only");
    live.setAttribute("aria-live", "polite");
    panels.forEach(() => track.appendChild(make("i")));
    top.append(count, upcoming); bar.append(top, track, live);
    form.insertBefore(bar, form.firstChild);

    const nav = $("[data-step-nav]");
    const navItems = [];
    if (nav) {
      nav.hidden = false;
      const ol = make("ol");
      panels.forEach((p, i) => {
        const li = make("li"), b = make("button");
        b.type = "button";
        b.append(make("span", "sn", pad2(i + 1)), make("span", "st", p.dataset.title));
        b.addEventListener("click", () => go(i));
        li.appendChild(b); ol.appendChild(li); navItems.push(li);
      });
      nav.textContent = "";
      nav.append(make("span", "label plain", "Your application"), ol);
    }
    const stepOk = (i) => $$(".field", panels[i]).every(f => !fieldProblem(f));
    function refreshNav() {
      navItems.forEach((li, k) => {
        const b = $("button", li);
        li.classList.toggle("is-current", k === cur);
        li.classList.toggle("is-done", k !== cur && k <= reached && stepOk(k));
        b.disabled = k > reached;
        if (k === cur) b.setAttribute("aria-current", "step"); else b.removeAttribute("aria-current");
      });
    }
    function show(i, opts) {
      const o = Object.assign({ push: true, focus: true }, opts);
      i = Math.max(0, Math.min(last, i));
      const changed = i !== cur;
      cur = i; reached = Math.max(reached, i);
      panels.forEach((p, k) => p.classList.toggle("active", k === i));
      count.textContent = `Step ${pad2(i + 1)} / ${pad2(panels.length)}`;
      upcoming.textContent = i < last ? `next: ${panels[i + 1].dataset.title}` : "last step";
      $$("i", track).forEach((seg, k) => seg.classList.toggle("on", k <= i));
      if (back) back.hidden = i === 0;
      if (next) next.hidden = i === last;
      if (submit) submit.hidden = i !== last;
      if (panels[i].hasAttribute("data-review")) renderReview();
      refreshNav();
      if (changed && o.announce !== false) {
        live.textContent = `Step ${i + 1} of ${panels.length}: ${panels[i].dataset.title}`;
        if (o.push) { try { history.pushState({ b0step: i }, "", `#step-${i + 1}`); } catch (e) {} }
        if (o.focus) {
          const y = form.getBoundingClientRect().top + window.scrollY - 92;
          if (window.scrollY > y) window.scrollTo({ top: y, behavior: reduceMotion ? "auto" : "smooth" });
          const h = $(".step-title", panels[i]);
          if (h) h.focus({ preventScroll: true });
        }
        hooks.onStep();
      }
    }
    // moving forward checks every step on the way; moving back never does
    function go(i) {
      i = Math.max(0, Math.min(last, i));
      for (let k = cur; k < i; k++) {
        const bad = validateScope(panels[k]);
        if (bad) { if (k !== cur) show(k, { focus: false }); refreshNav(); focusField(bad); return false; }
      }
      show(i);
      return true;
    }
    function renderReview() {
      const body = $("[data-review-body]", form);
      if (!body) return;
      body.textContent = "";
      panels.forEach((p, i) => {
        if (p.hasAttribute("data-review")) return;
        const block = make("div", "rev-block"), hd = make("div", "rev-hd"), dl = make("dl");
        const edit = make("button", "rev-edit", "Edit");
        edit.type = "button";
        edit.setAttribute("aria-label", `Edit ${p.dataset.title}`);
        edit.addEventListener("click", () => show(i));
        hd.append(make("span", "label plain", `${pad2(i + 1)} · ${p.dataset.title}`), edit);
        let missing = false;
        $$(".field, .optin-group:not([role])", p).forEach(node => {
          const row = make("div", "rev-row");
          if (node.classList.contains("optin-group")) {
            const picked = $$("label.optin", node).filter(l => $("input", l).checked)
              .map(l => $("b", l).textContent.replace(/^I'm open to /, "").replace(/^./, c => c.toUpperCase()));
            row.append(make("dt", "", "Also open to"), make("dd", "", picked.length ? picked.join(" · ") : "—"));
            dl.appendChild(row);
            return;
          }
          const label = node.querySelector(":scope > label");
          if (!label) return;
          const name = label.cloneNode(true);
          $$("b", name).forEach(b => b.remove());
          const inputs = controls(node), first = inputs[0];
          if (!first) return;
          const value = (first.type === "checkbox" || first.type === "radio")
            ? inputs.filter(x => x.checked).map(x => x.value).join(" · ")
            : first.value.trim();
          const problem = fieldProblem(node);
          if (!value && !problem) return;               // unanswered optional question
          if (problem) { row.classList.add("missing"); missing = true; }
          row.append(make("dt", "", label.dataset.short || name.textContent.trim()), make("dd", "", problem && !value ? "// missing" : (problem ? `${value}  ${problem}` : value)));
          dl.appendChild(row);
        });
        const liB = $("[data-linkedin]", p);
        if (liB && $('input[name="linkedin_verified"]', liB) && $('input[name="linkedin_verified"]', liB).value === "yes") {
          const row = make("div", "rev-row"), dd = make("dd");
          const photo = $('input[name="photo_url"]', liB).value;
          if (photo) { const t = make("img", "rev-photo"); t.src = photo; t.alt = ""; t.referrerPolicy = "no-referrer"; dd.appendChild(t); }
          dd.appendChild(make("span", "", `Verified · ${$('input[name="linkedin_name"]', liB).value}`));
          row.append(make("dt", "", "LinkedIn"), dd);
          dl.insertBefore(row, dl.firstChild);
        }
        if (missing) { block.classList.add("has-missing"); hd.insertBefore(make("span", "rev-flag", "needs a look"), edit); }
        block.append(hd, dl);
        body.appendChild(block);
      });
    }

    if (back) back.addEventListener("click", () => show(cur - 1));
    if (next) next.addEventListener("click", () => go(cur + 1));
    form.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" || e.isComposing || cur === last) return;
      const t = e.target;
      if (t.tagName === "TEXTAREA" || t.tagName === "BUTTON" || t.tagName === "A") return;
      e.preventDefault();
      go(cur + 1);
    });
    window.addEventListener("popstate", (e) => {
      if (form.classList.contains("sent")) return;
      const s = e.state && typeof e.state.b0step === "number" ? e.state.b0step : 0;
      show(Math.min(s, reached), { push: false });
    });

    return {
      get current() { return cur; }, get reached() { return reached; }, last,
      start(i, r) { reached = Math.max(0, Math.min(last, r || 0)); cur = -1; show(Math.min(i, reached), { push: false, focus: false, announce: false });
        try { history.replaceState({ b0step: cur }, "", cur ? `#step-${cur + 1}` : location.pathname + location.search); } catch (e) {} },
      next() { return go(cur + 1); },
      showField(f) { const i = panels.findIndex(p => p.contains(f)); if (i >= 0 && i !== cur) show(i, { focus: false }); refreshNav(); },
      refreshNav, renderReview,
      reset() { reached = 0; show(0); },
      hideNav() { if (nav) nav.hidden = true; },
    };
  }

  $$("form.app").forEach(form => {
    form.setAttribute("novalidate", "");
    let errBox = $(".form-error", form);
    if (!errBox) { errBox = make("div", "form-error"); form.appendChild(errBox); }
    const ERR_DEFAULT = "// couldn't send — check your connection and try again, or email hello@batchzero.co";
    errBox.textContent = ERR_DEFAULT;

    const refreshers = [];
    const refreshAll = () => refreshers.forEach(fn => fn());

    // character counters on long answers
    $$("textarea[maxlength]", form).forEach(t => {
      const max = parseInt(t.getAttribute("maxlength"), 10), c = make("span", "count");
      c.setAttribute("aria-hidden", "true");
      const upd = () => { const n = t.value.length; c.textContent = `${n} / ${max}`; c.classList.toggle("near", n >= max * 0.9); };
      t.insertAdjacentElement("afterend", c);
      t.addEventListener("input", upd); refreshers.push(upd); upd();
    });
    // "pick up to N" chip groups
    $$(".field[data-max]", form).forEach(f => {
      const max = parseInt(f.dataset.max, 10), boxes = $$("input[type=checkbox]", f);
      const sync = () => f.classList.toggle("maxed", boxes.filter(b => b.checked).length >= max);
      boxes.forEach(b => b.addEventListener("change", () => {
        if (b.checked && boxes.filter(x => x.checked).length > max) { b.checked = false; showProblem(f, `// pick up to ${max} — untick one first`); }
        sync();
      }));
      refreshers.push(sync); sync();
    });
    // "linkedin.com/in/you" → "https://linkedin.com/in/you"
    $$("input[type=url]", form).forEach(i => i.addEventListener("blur", () => {
      const v = i.value.trim();
      if (v && !/^[a-z][a-z0-9+.-]*:/i.test(v) && v.includes(".")) { i.value = "https://" + v.replace(/^\/+/, ""); i.dispatchEvent(new Event("input", { bubbles: true })); }
    }));
    $$("input, textarea, select", form).forEach(i => i.addEventListener("input", () => {
      const f = i.closest(".field"); if (f) f.classList.remove("err");
      const chk = i.closest(".check"); if (chk) chk.classList.remove("err");
    }));

    // drafts
    const store = form.hasAttribute("data-autosave") ? draftStore() : null;
    const note = $("[data-note]", form), noteDefault = note ? note.textContent : "";
    let saveTimer = null, stepper = null;
    const auto = {};
    const saveDraft = () => {
      if (!store) return;
      clearTimeout(saveTimer);
      saveTimer = setTimeout(() => {
        if (form.classList.contains("sent")) return;
        const values = snapshot(form);
        if (!hasContent(values, auto)) { store.clear(); if (note) note.textContent = noteDefault; return; }
        const ok = store.save({ v: 1, savedAt: Date.now(), step: stepper ? stepper.current : 0, reached: stepper ? stepper.reached : 0, values });
        if (ok && note) note.textContent = `// draft saved on this device · ${when(Date.now())}`;
      }, 400);
    };
    if (form.hasAttribute("data-steps")) stepper = makeStepper(form, { onStep: saveDraft });

    const draft = store && store.load();
    let startStep = 0, startReached = 0;
    if (draft && hasContent(draft.values)) {  // restored before any time-zone guess, so the draft wins
      restore(form, draft.values);
      startStep = draft.step || 0; startReached = Math.max(draft.reached || 0, startStep);
      const m = location.hash.match(/^#step-(\d+)$/);
      if (m && +m[1] - 1 <= startReached) startStep = +m[1] - 1;
      const bn = make("div", "draft-note"), txt = make("span", "", `// picked up where you left off · saved ${when(draft.savedAt)}`), clr = make("button", "", "Start over");
      clr.type = "button";
      let armed = null;
      clr.addEventListener("click", () => {
        if (!armed) { clr.textContent = "Clear every answer?"; clr.classList.add("armed"); armed = setTimeout(() => { armed = null; clr.textContent = "Start over"; clr.classList.remove("armed"); }, 4000); return; }
        clearTimeout(armed);
        form.reset(); store.clear(); bn.remove();
        $$(".field.err", form).forEach(f => f.classList.remove("err"));
        refreshAll();
        if (note) note.textContent = noteDefault;
        const tzSel = $("select[name=timezone]", form); if (tzSel && !tzSel.value) tzSel.value = auto.timezone = guessZone();
        if (li) li.refresh();
        if (stepper) stepper.reset();
      });
      bn.append(txt, clr);
      const bar = $(".stepbar", form);
      if (bar) bar.insertAdjacentElement("afterend", bn); else form.insertBefore(bn, form.firstChild);
      if (note) note.textContent = `// draft saved on this device · ${when(draft.savedAt)}`;
    }
    const liBlock = $("[data-linkedin]", form);
    const li = liBlock ? setupLinkedIn(form, liBlock, saveDraft) : null;
    if (li) { li.refresh(); li.fromRedirect(); }

    const tz = $("select[name=timezone]", form);
    if (tz && !tz.value) tz.value = auto.timezone = guessZone();
    refreshAll();
    if (stepper) stepper.start(startStep, startReached);
    if (store) { form.addEventListener("input", saveDraft); form.addEventListener("change", saveDraft); }
    if (stepper) { let navT = null; form.addEventListener("input", () => { clearTimeout(navT); navT = setTimeout(stepper.refreshNav, 250); }); }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (form.classList.contains("busy")) return;
      if (stepper && stepper.current < stepper.last) { stepper.next(); return; }
      const bad = validateScope(form);
      if (bad) { if (stepper) stepper.showField(bad); focusField(bad); return; }
      const consent = $("input[name=consent]", form);
      if (consent && !consent.checked) { consent.closest(".check").classList.add("err"); consent.focus(); return; }
      const data = collect(form);
      form.classList.remove("failed");
      if (new Blob([JSON.stringify(data)]).size > MAX_PAYLOAD_BYTES) {
        errBox.textContent = "// that's a little too long to send — trim your longest answers and try again";
        form.classList.add("failed");
        return;
      }
      errBox.textContent = ERR_DEFAULT;
      form.classList.add("busy");
      try {
        await submitApplication(formType(), data);
        form.classList.add("sent");
        if (store) { clearTimeout(saveTimer); store.clear(); }
        if (stepper) { stepper.hideNav(); try { history.replaceState(null, "", location.pathname + location.search); } catch (err) {} }
        const done = form.nextElementSibling && form.nextElementSibling.classList.contains("form-done") ? form.nextElementSibling : form.parentElement;
        window.scrollTo({ top: done.getBoundingClientRect().top + window.scrollY - 120, behavior: reduceMotion ? "auto" : "smooth" });
      } catch (err) {
        console.error("[B0] submit failed", err);
        form.classList.add("failed");
      } finally { form.classList.remove("busy"); }
    });
  });

  /* ---- footer year ---- */
  $$("[data-year]").forEach(el => el.textContent = new Date().getFullYear());
})();
