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

  /* ---- forms (UI only for now) ---- */
  $$("form.app").forEach(form => {
    form.setAttribute("novalidate", "");
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      let ok = true;
      $$(".field", form).forEach(f => {
        const input = $("input, textarea, select", f);
        if (!input) return;
        let valid = true;
        if (input.required && !input.value.trim()) valid = false;
        if (valid && input.type === "email" && input.value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(input.value)) valid = false;
        if (valid && input.type === "url" && input.value && !/^https?:\/\/.+\..+/.test(input.value)) valid = false;
        f.classList.toggle("err", !valid);
        if (!valid) ok = false;
      });
      const consent = $("input[name=consent]", form);
      if (consent && !consent.checked) { ok = false; consent.focus(); consent.parentElement.style.color = "#ff8a95"; }
      if (!ok) { const first = $(".field.err", form); if (first) first.scrollIntoView({ behavior: "smooth", block: "center" }); return; }
      // TODO: wire to backend (Supabase / form endpoint). For now, show the confirmation state.
      const data = Object.fromEntries(new FormData(form).entries());
      console.log("[B0] application (not sent yet):", data);
      form.classList.add("sent");
      window.scrollTo({ top: form.getBoundingClientRect().top + window.scrollY - 120, behavior: "smooth" });
    });
    $$("input, textarea, select", form).forEach(i => i.addEventListener("input", () => i.closest(".field") && i.closest(".field").classList.remove("err")));
  });

  /* ---- footer year ---- */
  $$("[data-year]").forEach(el => el.textContent = new Date().getFullYear());
})();
