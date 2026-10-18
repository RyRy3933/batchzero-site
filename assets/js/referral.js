/* Batch Zero — referrals.
 *
 * Two pages load this file:
 *   /apply/founders/  reads ?ref=<code> (or the code this browser remembered) into the hidden
 *                     `ref` input, so the application carries who sent the founder.
 *   /refer/           the "get your referral link" form: stores the referrer as an application
 *                     of type 'referrer', then shows their link, a QR code and a print-ready flyer.
 *   /refer/flyer/     renders the flyer with the referrer's own QR code.
 *
 * The pure helpers at the top have no DOM and are exported for tools/test_referrals.py (via node).
 * Payout rule the code follows (also printed on /refer/): one $100 bonus per accepted startup,
 * to the referrer whose code is on the application; with no code, to the person the founder
 * names under "Who sent you?".
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.B0Referral = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const STORE_KEY = "b0-ref";
  const TTL_MS = 60 * 24 * 60 * 60 * 1000;            // a remembered code lasts 60 days
  const CODE_RE = /^[a-z0-9](?:[a-z0-9-]{0,46}[a-z0-9])?$/;
  const ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789";  // no 0/o, 1/l/i: codes get read off paper
  const SITE = "https://batchzero.co";

  /** A code from a URL or storage, normalised — or "" if it isn't one we could have issued. */
  function cleanRef(value) {
    const s = String(value == null ? "" : value).trim().toLowerCase();
    return CODE_RE.test(s) ? s : "";
  }

  /** "Maya Rodríguez" → "maya-r". Letters and digits only; "" when nothing usable is left. */
  function slugName(name) {
    const parts = String(name == null ? "" : name)
      .normalize("NFKD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().split(/\s+/)
      .map((p) => p.replace(/[^a-z0-9]/g, ""))
      .filter(Boolean);
    if (!parts.length) return "";
    const first = parts[0].slice(0, 20);
    const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
    return last ? `${first}-${last}` : first;
  }

  /** Four characters from ALPHABET. `bytes` is injectable so tests are deterministic. */
  function randomTail(bytes) {
    let b = bytes;
    if (!b) {
      b = new Uint8Array(4);
      (globalThis.crypto || require("crypto").webcrypto).getRandomValues(b);
    }
    let out = "";
    for (let i = 0; i < 4; i++) out += ALPHABET[b[i] % ALPHABET.length];
    return out;
  }

  /** "Maya Rodríguez" → "maya-r-7k2f". Always passes cleanRef(). */
  function makeCode(name, bytes) {
    return `${slugName(name) || "friend"}-${randomTail(bytes)}`;
  }

  function referralLink(code, base) {
    return `${base == null ? SITE : base}/apply/founders/?ref=${encodeURIComponent(cleanRef(code))}`;
  }

  function flyerLink(code, base) {
    return `${base == null ? SITE : base}/refer/flyer/?ref=${encodeURIComponent(cleanRef(code))}`;
  }

  /** The code in a query string, if any. */
  function refFromSearch(search) {
    try { return cleanRef(new URLSearchParams(search || "").get("ref")); } catch (e) { return ""; }
  }

  /** The code remembered in `storage`, if it's still fresh. Never throws. */
  function readStored(storage, now) {
    try {
      const raw = storage && storage.getItem(STORE_KEY);
      if (!raw) return "";
      const v = JSON.parse(raw);
      if (!v || typeof v !== "object" || now - Number(v.at) > TTL_MS) return "";
      return cleanRef(v.ref);
    } catch (e) { return ""; }
  }

  function remember(storage, ref, now) {
    const r = cleanRef(ref);
    if (!r) return;
    try { storage && storage.setItem(STORE_KEY, JSON.stringify({ ref: r, at: now })); } catch (e) { /* private mode */ }
  }

  /** The code a founder application should carry: the link they arrived on beats a remembered one. */
  function resolveRef(search, storage, now) {
    const fromUrl = refFromSearch(search);
    if (fromUrl) { remember(storage, fromUrl, now); return fromUrl; }
    return readStored(storage, now);
  }

  /** Text an ambassador or club leader can paste into a group chat. */
  function shareText(code) {
    return "Building something? Batch Zero is a free, online accelerator for high-school founders: " +
      "5 startups, 2 mentors each, 8 weeks, Demo Day in front of investors. Applications close Oct 31. " +
      `Apply here: ${referralLink(code)}`;
  }

  /** QR modules → one SVG path ("M x y h1 v1 h-1 z" per dark cell, merged by rows). */
  function qrPath(qr) {
    const n = qr.getModuleCount();
    let d = "";
    for (let y = 0; y < n; y++) {
      let x = 0;
      while (x < n) {
        if (!qr.isDark(y, x)) { x++; continue; }
        let run = 1;
        while (x + run < n && qr.isDark(y, x + run)) run++;
        d += `M${x} ${y}h${run}v1h-${run}z`;
        x += run;
      }
    }
    return { size: n, d };
  }

  return { STORE_KEY, TTL_MS, cleanRef, slugName, randomTail, makeCode, referralLink, flyerLink,
           refFromSearch, readStored, remember, resolveRef, shareText, qrPath };
});

/* ------------------------------------------------------------------ the pages */
(function () {
  "use strict";
  if (typeof document === "undefined") return;
  const R = window.B0Referral;
  const $ = (s, el) => (el || document).querySelector(s);
  const now = () => Date.now();
  let storage = null;
  try { storage = window.localStorage; } catch (e) { storage = null; }

  /** Draw a QR code for `text` into <svg data-qr>. Needs assets/js/vendor/qrcode.js. */
  function drawQR(svg, text) {
    if (!svg || typeof window.qrcode !== "function") return false;
    const qr = window.qrcode(0, "M");
    qr.addData(text);
    qr.make();
    const { size, d } = R.qrPath(qr);
    const NS = "http://www.w3.org/2000/svg";
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", `-2 -2 ${size + 4} ${size + 4}`);
    svg.setAttribute("shape-rendering", "crispEdges");
    const bg = document.createElementNS(NS, "rect");
    bg.setAttribute("x", "-2"); bg.setAttribute("y", "-2");
    bg.setAttribute("width", String(size + 4)); bg.setAttribute("height", String(size + 4));
    bg.setAttribute("fill", "#ffffff");
    const p = document.createElementNS(NS, "path");
    p.setAttribute("d", d); p.setAttribute("fill", "#0b0b0c");
    svg.appendChild(bg); svg.appendChild(p);
    return true;
  }

  async function copy(text, btn) {
    const was = btn.textContent;
    try { await navigator.clipboard.writeText(text); btn.textContent = "Copied"; }
    catch (e) { btn.textContent = "Select and copy it"; }
    setTimeout(() => { btn.textContent = was; }, 1800);
  }

  /* /apply/founders/ — attach the code to the application */
  const refInput = $("form.app input[name=ref]");
  if (refInput) {
    const code = R.resolveRef(location.search, storage, now());
    if (code) {
      refInput.value = code;
      const note = $("[data-ref-note]");
      if (note) { note.textContent = `// referral code ${code} is attached to your application`; note.hidden = false; }
    }
  }

  /* /refer/ — sign up as a referrer, get a link */
  const form = $("form[data-refer]");
  if (form) {
    const done = $("[data-refer-done]");
    const err = $(".form-error", form) || form.appendChild(Object.assign(document.createElement("div"), { className: "form-error" }));
    err.textContent = "// couldn't save that — check your connection and try again, or email hello@batchzero.co";

    const show = (code, name) => {
      const link = R.referralLink(code);
      $("[data-ref-link]", done).textContent = link;
      $("[data-ref-link]", done).href = link;
      $("[data-ref-code]", done).textContent = code;
      $("[data-ref-who]", done).textContent = name ? `${name.split(/\s+/)[0]}, here's your link.` : "Here's your link.";
      $("[data-ref-flyer]", done).href = R.flyerLink(code, "");
      $("[data-ref-share]", done).value = R.shareText(code);
      drawQR($("svg[data-qr]", done), link);
      form.hidden = true;
      done.hidden = false;
      done.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    $("[data-copy-link]", done).addEventListener("click", (e) => copy($("[data-ref-link]", done).textContent, e.currentTarget));
    $("[data-copy-share]", done).addEventListener("click", (e) => copy($("[data-ref-share]", done).value, e.currentTarget));

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (form.classList.contains("busy")) return;
      if (!window.B0.validate(form)) return;
      const agree = $("input[name=consent]", form);
      if (agree && !agree.checked) { agree.closest(".check").classList.add("err"); agree.focus(); return; }
      const fd = new FormData(form), data = {};
      fd.forEach((v, k) => { data[k] = typeof v === "string" ? v.trim() : v; });
      data.code = R.makeCode(data.name);
      data.form_version = "referrer-v1";
      form.classList.remove("failed");
      form.classList.add("busy");
      try {
        await window.B0.submit("referrer", data);
      } catch (first) {
        // supabase/referrals.sql not run yet → the type is rejected. Keep the signup anyway.
        try { await window.B0.submit("unknown", Object.assign({ kind: "referrer" }, data)); }
        catch (second) { console.error("[B0] referrer signup failed", first, second); form.classList.add("failed"); form.classList.remove("busy"); return; }
      }
      form.classList.remove("busy");
      show(data.code, data.name);
    });
  }

  /* /refer/flyer/ — the flyer with this referrer's QR */
  const flyerQR = $("svg[data-flyer-qr]");
  if (flyerQR) {
    const code = R.refFromSearch(location.search);
    const link = code ? R.referralLink(code) : `https://batchzero.co/apply/founders/`;
    drawQR(flyerQR, link);
    const tag = $("[data-flyer-code]");
    if (tag && code) tag.textContent = `ref · ${code}`;
    const missing = $("[data-flyer-missing]");
    if (missing) missing.hidden = !!code;
    const printBtn = $("[data-print]");
    if (printBtn) printBtn.addEventListener("click", () => window.print());
  }
})();
