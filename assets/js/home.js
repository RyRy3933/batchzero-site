/* Batch Zero — homepage: the "Mentors:" strip at the bottom of the hero.

   What it does
   - Loads the mentor roster (roster.js → list_mentors()) and renders one compact card per mentor:
     portrait, name, bio (CSS clamps it to 3 lines), "View on LinkedIn".
   - Drifts slowly and continuously to the left. Pauses while a mouse is over it and resumes when
     the mouse leaves; also pauses while a link inside has keyboard focus, while a finger drags
     it, while it's scrolled off screen, and while the tab is hidden.
   - Seamless loop: the set of cards is followed by inert, aria-hidden copies, and the offset
     wraps every time one full set has gone by. Screen readers and the Tab key only meet each
     mentor once.

   When it doesn't move
   - prefers-reduced-motion, or fewer than MIN_TO_LOOP mentors (a loop of one or two people
     looks like a glitch). The row is then a plain, swipeable/scrollable list.

   When it isn't there
   - The HTML ships four skeleton cards so the hero is laid out at its final height before the
     data arrives (no jump). If the call fails or nobody is listed yet, the whole strip is
     removed: an empty "Mentors:" row in the hero is worse than none. Without JavaScript a
     <noscript> rule hides it. */
(function () {
  "use strict";
  const strip = document.querySelector("[data-mentor-strip]");
  const R = window.B0Roster;
  if (!strip) return;
  const viewport = strip.querySelector("[data-ms-viewport]");
  const track = strip.querySelector("[data-ms-track]");
  if (!R || !viewport || !track) { strip.remove(); return; }

  const SPEED = 26;          // px per second — slow enough to read a name as it passes
  const MIN_TO_LOOP = 3;     // fewer than this and the row stays still
  const DRAG_SLOP = 6;       // px a finger must travel before a touch counts as a drag
  const RESUME_AFTER_TOUCH = 1800;

  const reduce = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  const { make } = R;

  /* ---------- cards ---------- */
  function card(m) {
    const el = make("article", "ms-card");
    el.setAttribute("role", "listitem");
    el.appendChild(R.photoTile(m.name, m.photos, "m-photo ms-photo"));
    const body = make("div", "ms-body");
    body.appendChild(make("h3", "ms-name", m.name));
    // a mentor who hasn't written a bio still says who they are
    const bio = m.bio || m.role;
    if (bio) body.appendChild(make("p", "ms-bio", bio));
    if (m.linkedin) {
      const a = make("a", "ms-link");
      a.href = m.linkedin;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.setAttribute("aria-label", `View ${m.name} on LinkedIn (opens in a new tab)`);
      a.append("View on LinkedIn ");
      const arr = make("span", "ms-arr", "↗");
      arr.setAttribute("aria-hidden", "true");
      a.appendChild(arr);
      body.appendChild(a);
    }
    el.appendChild(body);
    return el;
  }

  function gone(why, err) {
    if (err) console.error(`[B0] mentor strip: ${why}`, err);
    stop();
    strip.remove();
    document.documentElement.classList.add("no-mentor-strip");
  }

  /* ---------- motion ---------- */
  let originals = [];      // the real cards (focusable, announced)
  let setW = 0;            // width of one full set including the trailing gap
  let x = 0;               // current offset into the loop, 0 ≤ x < setW
  let raf = 0, last = 0;
  let animated = false;
  const paused = new Set(); // reasons: hover, focus, drag, offscreen, hidden

  const wrap = (v) => (setW > 0 ? ((v % setW) + setW) % setW : 0);
  const apply = () => { track.style.transform = animated ? `translate3d(${-x}px,0,0)` : ""; };

  function frame(t) {
    raf = 0;
    if (!animated || paused.size) return;
    // real time, so a slow machine sees the same speed at fewer frames; the clamp only stops a
    // leap after a long stall (switching tabs pauses it outright, see visibilitychange below)
    const dt = last ? Math.min(0.25, (t - last) / 1000) : 0;
    last = t;
    x = wrap(x + SPEED * dt);
    apply();
    raf = requestAnimationFrame(frame);
  }
  function start() { if (animated && !paused.size && !raf) { last = 0; raf = requestAnimationFrame(frame); } }
  function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
  function pause(why) { paused.add(why); stop(); strip.classList.add("is-paused"); }
  function resume(why) {
    paused.delete(why);
    if (!paused.size) { strip.classList.remove("is-paused"); start(); }
  }

  function clearClones() { track.querySelectorAll("[data-clone]").forEach(n => n.remove()); }

  /* Decide moving vs still for the current width and motion setting, and lay the track out. */
  function layout() {
    const shouldMove = !reduce.matches && originals.length >= MIN_TO_LOOP;
    clearClones();
    if (!shouldMove) {
      animated = false; stop(); x = 0; apply();
      strip.classList.remove("is-moving");
      strip.classList.add("is-still");
      return;
    }
    strip.classList.remove("is-still");
    strip.classList.add("is-moving");
    const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    const first = originals[0], lastCard = originals[originals.length - 1];
    setW = lastCard.offsetLeft + lastCard.offsetWidth + gap - first.offsetLeft;
    if (!(setW > 0)) { animated = false; return; }
    // enough copies that the viewport is always covered, even at the very end of a set
    const copies = Math.max(1, Math.ceil(viewport.clientWidth / setW));
    const frag = document.createDocumentFragment();
    for (let c = 0; c < copies; c++) {
      originals.forEach(o => {
        const n = o.cloneNode(true);
        n.setAttribute("data-clone", "");
        n.setAttribute("aria-hidden", "true");
        n.setAttribute("inert", "");
        n.querySelectorAll("a").forEach(a => a.setAttribute("tabindex", "-1"));
        frag.appendChild(n);
      });
    }
    track.appendChild(frag);
    animated = true;
    x = wrap(x);
    apply();
    start();
  }

  /* ---------- input ---------- */
  // mouse: pause while over the cards, resume on leave
  viewport.addEventListener("pointerenter", (e) => { if (e.pointerType !== "touch") pause("hover"); });
  viewport.addEventListener("pointerleave", (e) => { if (e.pointerType !== "touch") resume("hover"); });

  // keyboard: hold still while a link has focus, and slide that card clear of the faded edges
  const fade = (side) => parseFloat(getComputedStyle(strip).getPropertyValue(`--ms-fade-${side}`)) || 0;
  strip.addEventListener("focusin", (e) => {
    pause("focus");
    viewport.scrollLeft = 0; // a focused element can scroll even a clipped box; undo that
    const c = e.target.closest(".ms-card");
    if (!c || !animated) return;
    const v = viewport.getBoundingClientRect(), r = c.getBoundingClientRect();
    const minLeft = v.left + fade("l"), maxRight = v.right - fade("r");
    let shift = 0;
    if (r.left < minLeft) shift = r.left - minLeft;
    else if (r.right > maxRight) shift = r.right - maxRight;
    if (!shift) return;
    // Don't wrap here: wrapping would jump a lap and leave the real (focusable) card off screen
    // while an identical inert copy sits in its place. Stay within the track instead; the loop
    // wraps x again on resume, and the copies make that seamless.
    x = Math.min(Math.max(x + shift, -fade("l")), track.scrollWidth - viewport.clientWidth);
    apply();
  });
  strip.addEventListener("focusout", (e) => { if (!strip.contains(e.relatedTarget)) resume("focus"); });

  // touch: drag sideways to scrub (vertical swipes still scroll the page — touch-action: pan-y)
  let touch = null, resumeTimer = 0, swallowClick = false;
  viewport.addEventListener("pointerdown", (e) => {
    if (e.pointerType !== "touch" || !animated) return;
    touch = { id: e.pointerId, x0: e.clientX, y0: e.clientY, from: x, dragging: false };
  });
  viewport.addEventListener("pointermove", (e) => {
    if (!touch || e.pointerId !== touch.id) return;
    const dx = e.clientX - touch.x0, dy = e.clientY - touch.y0;
    if (!touch.dragging) {
      if (Math.abs(dx) < DRAG_SLOP || Math.abs(dx) < Math.abs(dy)) return;
      touch.dragging = true;
      clearTimeout(resumeTimer);
      pause("drag");
      try { viewport.setPointerCapture(e.pointerId); } catch (err) { /* already released */ }
    }
    x = wrap(touch.from - dx);
    apply();
  });
  const endTouch = (e) => {
    if (!touch || (e && e.pointerId !== touch.id)) return;
    if (touch.dragging) {
      swallowClick = true;
      setTimeout(() => { swallowClick = false; }, 0);
      clearTimeout(resumeTimer);
      resumeTimer = setTimeout(() => resume("drag"), RESUME_AFTER_TOUCH);
    }
    touch = null;
  };
  viewport.addEventListener("pointerup", endTouch);
  viewport.addEventListener("pointercancel", endTouch);
  // a drag that ends on a link is not a tap on it
  viewport.addEventListener("click", (e) => { if (swallowClick) { e.preventDefault(); e.stopPropagation(); } }, true);

  // don't burn frames off screen or in a background tab
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((entries) => {
      entries.forEach(en => (en.isIntersecting ? resume("offscreen") : pause("offscreen")));
    }).observe(strip);
  }
  document.addEventListener("visibilitychange", () => (document.hidden ? pause("hidden") : resume("hidden")));

  // the number of copies depends on the width; recompute when it changes
  let lastW = 0, relayout = 0;
  const onResize = () => {
    const w = viewport.clientWidth;
    if (!originals.length || w === lastW) return;
    lastW = w;
    cancelAnimationFrame(relayout);
    relayout = requestAnimationFrame(layout);
  };
  if ("ResizeObserver" in window) new ResizeObserver(onResize).observe(viewport);
  else window.addEventListener("resize", onResize);
  if (reduce.addEventListener) reduce.addEventListener("change", layout);

  /* ---------- go ---------- */
  R.mentors().then((list) => {
    if (!list.length) return gone("no mentors listed yet");
    const frag = document.createDocumentFragment();
    originals = list.map(card);
    originals.forEach(c => frag.appendChild(c));
    track.replaceChildren(frag);
    strip.setAttribute("aria-busy", "false");
    strip.classList.add("is-ready");
    lastW = viewport.clientWidth;
    layout();
    // test hook: lets tests read and drive the strip without waiting on real time
    strip.__ms = { get x() { return x; }, get setW() { return setW; }, get animated() { return animated; }, get paused() { return [...paused]; } };
  }).catch(err => gone("couldn't load the roster", err));
})();
