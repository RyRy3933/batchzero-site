"""Browser tests for the homepage hero and its "Mentors:" strip (assets/js/home.js), plus a
regression check that /network/ still renders the roster through the shared roster.js.

Run from the site root:

    pip install playwright && python3 -m playwright install chromium     # once
    python3 -m unittest tools/test_home_strip.py

Skipped when Playwright isn't installed. The page is served from this folder and the database is
faked, so nothing here touches Supabase. Set B0_FONTS_DIR to a folder of the site's .woff2 files
(Fontsource names, e.g. space-grotesk-latin-700-normal.woff2) if the machine can't reach Google
Fonts — the above-the-fold checks depend on real font metrics.
"""
import functools
import http.server
import json
import os
import socketserver
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUPABASE = "https://lzinyfukedgytwvgszna.supabase.co/rest/v1/rpc/"

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

# Test data only — these bios are not real mentors' bios.
MENTORS = [
    {"full_name": "Ada One", "title": "CEO", "company": "Alpha", "areas_of_expertise": "Sales, Product", "photo_url": None,
     "bio": "Long test bio. " * 20, "linkedin_url": "https://www.linkedin.com/in/ada-one/"},
    {"full_name": "Ben Two", "title": "CTO", "company": "Beta", "areas_of_expertise": "Engineering", "photo_url": None,
     "bio": "Short bio.", "linkedin_url": "linkedin.com/in/ben-two"},
    {"full_name": "Cy Three", "title": "COO", "company": "Gamma", "areas_of_expertise": "Operations", "photo_url": None,
     "bio": None, "linkedin_url": None},
    {"full_name": "Di Four", "title": "Founder", "company": "Delta", "areas_of_expertise": "Design", "photo_url": None,
     "bio": "Has a bad link.", "linkedin_url": "javascript:alert(1)"},
]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _font_css(fonts_dir):
    rules = []
    for fam in ("Space Grotesk", "JetBrains Mono"):
        stem = fam.lower().replace(" ", "-")
        for w in (400, 500, 600, 700):
            rules.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:block;"
                         f"src:url(/__fonts/{stem}-latin-{w}-normal.woff2) format('woff2')}}")
    return "\n".join(rules)


@unittest.skipIf(sync_playwright is None, "playwright not installed")
class HomeStrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(_Quiet, directory=str(ROOT))
        cls.srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
        cls.srv.daemon_threads = True
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()
        cls.fonts = os.environ.get("B0_FONTS_DIR")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.srv.shutdown()

    # ---------- helpers ----------
    def open(self, path="/", mentors=MENTORS, status=200, w=1440, h=900, reduced=False, delay=0, ambassadors=()):
        ctx = self.browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce" if reduced else "no-preference")
        page = ctx.new_page()
        self.addCleanup(ctx.close)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        if self.fonts:
            css = _font_css(self.fonts)
            page.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=css))
            page.route("**/__fonts/**", lambda r: r.fulfill(path=str(Path(self.fonts) / r.request.url.rsplit("/", 1)[1]), content_type="font/woff2"))

        def rpc(route):
            if delay:
                page.wait_for_timeout(delay)
            name = route.request.url.rsplit("/", 1)[1]
            if status != 200:
                return route.fulfill(status=status, content_type="application/json", body='{"message":"test failure"}')
            body = mentors if name == "list_mentors" else list(ambassadors) if name == "list_ambassadors" else []
            route.fulfill(status=200, content_type="application/json", body=json.dumps(body))
        page.route(SUPABASE + "**", rpc)
        page.route("https://*.licdn.com/**", lambda r: r.abort())
        page.goto(self.base + path, wait_until="domcontentloaded")
        page.evaluate("document.fonts.ready")
        return page, errors

    def ready(self, page):
        page.wait_for_selector(".mentor-strip.is-ready", timeout=5000)
        # and let the site's fade-up reveal (.rv → .in, 0.7s) finish, so boxes are where they'll stay
        page.wait_for_function("document.querySelector('.mentor-strip').classList.contains('in')", timeout=5000)
        page.wait_for_timeout(1100)

    def state(self, page):
        return page.evaluate("(() => { const s = document.querySelector('[data-mentor-strip]').__ms; return {x: s.x, setW: s.setW, animated: s.animated, paused: s.paused}; })()")

    # ---------- hero copy ----------
    def test_hero_copy(self):
        page, errors = self.open()
        self.assertEqual(page.inner_text(".hero h1").replace(" ", " "), "The Startup Accelerator for High School Founders.")
        lede = page.inner_text(".hero .lede")
        for must in ("8-week", "online", "two dedicated mentors", "online Demo Day"):
            self.assertIn(must, lede)
        self.assertIn("startup accelerator for high-school founders", page.title().lower())
        self.assertEqual(errors, [])

    # ---------- rendering ----------
    def test_cards_render_with_bio_portrait_and_safe_links(self):
        page, errors = self.open()
        self.ready(page)
        self.assertEqual(page.inner_text(".ms-label"), "MENTORS:")  # "Mentors:" in the label style
        cards = page.locator(".ms-card:not([data-clone])")
        self.assertEqual(cards.count(), 4)
        self.assertEqual(cards.locator(".ms-name").all_inner_texts(), ["Ada One", "Ben Two", "Cy Three", "Di Four"])
        self.assertEqual(page.locator(".ms-skel").count(), 0, "skeleton replaced")
        self.assertEqual(cards.locator(".ms-photo .m-ini").count(), 4, "every card has a portrait tile")
        # no bio → falls back to title · company
        self.assertEqual(cards.nth(2).locator(".ms-bio").inner_text(), "COO · Gamma")
        # links: only the two real profiles, cleaned, opening safely in a new tab
        links = cards.locator("a.ms-link")
        self.assertEqual(links.count(), 2)
        self.assertEqual([links.nth(i).get_attribute("href") for i in range(2)],
                         ["https://www.linkedin.com/in/ada-one/", "https://linkedin.com/in/ben-two"])
        for i in range(2):
            self.assertEqual(links.nth(i).get_attribute("target"), "_blank")
            self.assertEqual(links.nth(i).get_attribute("rel"), "noopener noreferrer")
            self.assertTrue(links.nth(i).inner_text().startswith("VIEW ON LINKEDIN"))
        self.assertEqual(page.locator("a[href^='javascript']").count(), 0)
        self.assertEqual(errors, [])

    def test_bio_is_clamped_to_three_lines_and_cards_line_up(self):
        page, _ = self.open()
        self.ready(page)
        r = page.evaluate("""() => {
          const bio = document.querySelector('.ms-card:not([data-clone]) .ms-bio');
          const lh = parseFloat(getComputedStyle(bio).lineHeight);
          const cards = [...document.querySelectorAll('.ms-card:not([data-clone])')].map(c => c.getBoundingClientRect().height);
          const links = [...document.querySelectorAll('.ms-card:not([data-clone]) .ms-link')].map(a => Math.round(a.getBoundingClientRect().bottom - a.closest('.ms-card').getBoundingClientRect().top));
          const overflow = [...document.querySelectorAll('.ms-card:not([data-clone]) .ms-body')].some(b => b.scrollHeight > b.clientHeight + 1);
          return {lines: bio.clientHeight / lh, scrollH: bio.scrollHeight, clientH: bio.clientHeight, cards, links, overflow};
        }""")
        self.assertLessEqual(r["lines"], 3.05)
        self.assertGreater(r["scrollH"], r["clientH"], "the long bio really is cut off")
        self.assertEqual(len(set(r["cards"])), 1, "all cards the same height")
        self.assertEqual(len(set(r["links"])), 1, "links sit on the same baseline")
        self.assertFalse(r["overflow"], "nothing spills out of a card")

    def test_copies_are_hidden_from_assistive_tech_and_keyboard(self):
        page, _ = self.open()
        self.ready(page)
        r = page.evaluate("""() => {
          const clones = [...document.querySelectorAll('.ms-card[data-clone]')];
          return {n: clones.length,
                  allHidden: clones.every(c => c.getAttribute('aria-hidden') === 'true' && c.hasAttribute('inert')),
                  linksOut: [...document.querySelectorAll('.ms-card[data-clone] a')].every(a => a.tabIndex === -1),
                  listitems: document.querySelectorAll('[data-ms-track] > [role=listitem]:not([data-clone])').length};
        }""")
        self.assertGreaterEqual(r["n"], 4)
        self.assertTrue(r["allHidden"])
        self.assertTrue(r["linksOut"])
        self.assertEqual(r["listitems"], 4)
        tree = page.locator("[data-mentor-strip]").aria_snapshot()
        self.assertEqual(tree.count("Ada One"), 2, "each mentor announced once (name + link label):\n" + tree)
        self.assertEqual(tree.count("listitem"), 4, tree)

    # ---------- motion ----------
    def test_drifts_slowly_and_wraps(self):
        page, _ = self.open()
        self.ready(page)
        a = self.state(page)
        page.wait_for_timeout(1000)
        b = self.state(page)
        self.assertTrue(b["animated"])
        speed = (b["x"] - a["x"]) % b["setW"]
        self.assertGreater(speed, 12, "it moves")
        self.assertLess(speed, 40, "slowly — under 40px/s")
        self.assertEqual(b["setW"], 4 * (272 + 12))
        # a full set's worth of travel lands back where it started, with no gap
        track_right = page.evaluate("document.querySelector('[data-ms-track]').scrollWidth")
        vw = page.evaluate("document.querySelector('[data-ms-viewport]').clientWidth")
        self.assertGreaterEqual(track_right - b["setW"], vw, "copies always cover the viewport")

    def test_pauses_on_hover_and_resumes_on_leave(self):
        page, _ = self.open()
        self.ready(page)
        box = page.locator("[data-ms-viewport]").bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(100)
        a = self.state(page)
        page.wait_for_timeout(700)
        b = self.state(page)
        self.assertIn("hover", b["paused"])
        self.assertAlmostEqual(a["x"], b["x"], places=3)
        page.mouse.move(5, 5)
        page.wait_for_timeout(600)
        c = self.state(page)
        self.assertEqual(c["paused"], [])
        self.assertGreater((c["x"] - b["x"]) % c["setW"], 5)

    def test_keyboard_focus_pauses_and_shows_the_card(self):
        page, _ = self.open()
        self.ready(page)
        page.wait_for_timeout(2500)  # let it drift so the first card is partly off the left edge
        page.focus(".ms-card:not([data-clone]) a.ms-link")
        page.wait_for_timeout(300)
        s = self.state(page)
        self.assertIn("focus", s["paused"])
        r = page.evaluate("""() => { const v = document.querySelector('[data-ms-viewport]').getBoundingClientRect();
                                       const c = document.activeElement.closest('.ms-card').getBoundingClientRect();
                                       return {inside: c.left >= v.left - 1 && c.right <= v.right + 1, scroll: document.querySelector('[data-ms-viewport]').scrollLeft}; }""")
        self.assertTrue(r["inside"], "focused card is fully visible")
        self.assertEqual(r["scroll"], 0)
        page.keyboard.press("Shift+Tab")  # → the strip's own "See all" link: still inside, still paused
        page.wait_for_timeout(100)
        self.assertEqual(page.evaluate("document.activeElement.className"), "ms-all")
        self.assertIn("focus", self.state(page)["paused"])
        page.keyboard.press("Shift+Tab")  # → out of the strip: moving again
        page.wait_for_timeout(100)
        self.assertFalse(page.evaluate("document.querySelector('[data-mentor-strip]').contains(document.activeElement)"))
        self.assertNotIn("focus", self.state(page)["paused"])

    def test_touch_drag_scrubs_and_does_not_click(self):
        page, _ = self.open(w=390, h=844)
        self.ready(page)
        r = page.evaluate("""async () => {
          const v = document.querySelector('[data-ms-viewport]'), s = document.querySelector('[data-mentor-strip]').__ms;
          const link = document.querySelector('.ms-card:not([data-clone]) a.ms-link');
          let clicked = false; link.addEventListener('click', e => { clicked = !e.defaultPrevented; e.preventDefault(); });
          const at = (type, x) => link.dispatchEvent(new PointerEvent(type, {bubbles: true, pointerId: 7, pointerType: 'touch', clientX: x, clientY: 600, isPrimary: true}));
          at('pointerdown', 200); const x0 = s.x;
          at('pointermove', 180); at('pointermove', 120);
          const during = {x: s.x, paused: s.paused.slice()};
          at('pointerup', 120); link.click();
          return {x0, during, clicked, setW: s.setW};
        }""")
        moved = (r["during"]["x"] - r["x0"]) % r["setW"]
        self.assertAlmostEqual(moved, 80, delta=1.5, msg="content follows the finger")
        self.assertIn("drag", r["during"]["paused"])
        self.assertFalse(r["clicked"], "a drag that ends on a link is not a tap")

    def test_reduced_motion_holds_still_and_scrolls(self):
        page, _ = self.open(reduced=True)
        self.ready(page)
        page.wait_for_timeout(700)
        s = self.state(page)
        self.assertFalse(s["animated"])
        self.assertEqual(s["x"], 0)
        self.assertEqual(page.locator(".ms-card[data-clone]").count(), 0)
        self.assertEqual(page.evaluate("getComputedStyle(document.querySelector('[data-ms-viewport]')).overflowX"), "auto")
        self.assertIn("is-still", page.get_attribute("[data-mentor-strip]", "class"))

    def test_too_few_mentors_to_loop(self):
        page, _ = self.open(mentors=MENTORS[:2])
        self.ready(page)
        self.assertFalse(self.state(page)["animated"])
        self.assertEqual(page.locator(".ms-card").count(), 2)

    # ---------- empty / failure ----------
    def test_no_mentors_removes_the_strip(self):
        page, errors = self.open(mentors=[])
        page.wait_for_function("!document.querySelector('[data-mentor-strip]')")
        self.assertIn("no-mentor-strip", page.get_attribute("html", "class"))
        self.assertEqual(errors, [])

    def test_failed_call_removes_the_strip_quietly(self):
        page, errors = self.open(status=500)
        page.wait_for_function("!document.querySelector('[data-mentor-strip]')")
        self.assertEqual([e for e in errors if "mentor strip" not in e and "500" not in e], [])
        self.assertEqual(page.locator(".hero h1").count(), 1, "the hero is fine without it")

    def test_skeleton_reserves_the_space(self):
        page, _ = self.open(delay=1500)
        box = "(() => { const s = document.querySelector('[data-mentor-strip]'); const h = document.querySelector('.hero h1'); return [s.offsetTop, s.offsetHeight, h.offsetTop]; })()"
        page.wait_for_timeout(300)
        before = page.evaluate(box)
        self.assertEqual(page.locator(".ms-skel").count(), 4)
        self.ready(page)
        self.assertEqual(page.locator(".ms-skel").count(), 0)
        self.assertEqual(before, page.evaluate(box), "neither the strip nor the headline moved when the data arrived")

    # ---------- above the fold, every size ----------
    def test_strip_is_on_the_first_screen(self):
        # (width, height, how much of the strip must show). Real browser viewports, not screen sizes.
        sizes = [(1920, 1080, "all"), (1536, 864, "all"), (1440, 900, "all"), (1470, 830, "all"),
                 (1366, 768, "all"), (1280, 720, "all"), (1366, 650, "all"), (1024, 768, "all"),
                 (768, 1024, "all"), (390, 844, "all"), (360, 740, "all"), (390, 664, "top")]
        for w, h, need in sizes:
            with self.subTest(size=f"{w}x{h}"):
                page, _ = self.open(w=w, h=h)
                self.ready(page)
                r = page.locator("[data-mentor-strip]").bounding_box()
                if need == "all":
                    self.assertLessEqual(r["y"] + r["height"], h + 0.5)
                else:
                    self.assertLess(r["y"] + 60, h, "label and the top of the cards show")
                no_scroll_x = page.evaluate("document.scrollingElement.scrollWidth <= innerWidth")
                self.assertTrue(no_scroll_x, "no sideways page scroll")
                page.context.close()

    def test_strip_does_not_overpower_the_hero(self):
        page, _ = self.open()
        self.ready(page)
        strip = page.locator("[data-mentor-strip]").bounding_box()
        h1 = page.locator(".hero h1").bounding_box()
        self.assertLess(strip["height"], 0.2 * 900)
        self.assertLess(strip["height"], h1["height"])
        self.assertGreater(page.evaluate("parseFloat(getComputedStyle(document.querySelector('.hero h1')).fontSize)"),
                           3 * page.evaluate("parseFloat(getComputedStyle(document.querySelector('.ms-name')).fontSize)"))

    # ---------- /network/ still works on the shared module ----------
    def test_network_page_still_renders_the_roster(self):
        page, errors = self.open("/network/")
        page.wait_for_selector("[data-mentor-grid]:not([hidden]) .mentor-card")
        self.assertEqual(page.locator("[data-mentor-grid] .mentor-card").count(), 4)
        self.assertEqual(page.inner_text("[data-mentor-count]"), "// 4 mentors confirmed so far")
        self.assertEqual(page.locator("[data-mentor-grid] .m-role").first.inner_text(), "CEO · Alpha")
        self.assertEqual(page.locator("[data-mentor-grid] .m-tag").first.inner_text(), "Sales")
        self.assertEqual(errors, [])

    def test_network_page_shows_ambassador_photos(self):
        # "Rayan S." has a committed photo in assets/img/ambassadors/; "Nobody Y." has nothing
        ambassadors = [
            {"display_name": "Rayan S.", "school": "Monte Vista High School", "city": "Danville CA",
             "grad_year": "2027", "focus": "Clubs you're in, Local events", "photo_url": None},
            {"display_name": "Nobody Y.", "school": "Somewhere High", "city": None, "grad_year": "2028",
             "focus": None, "photo_url": "https://media.licdn.com/expired"},
        ]
        page, errors = self.open("/network/", ambassadors=ambassadors)
        page.wait_for_selector("[data-amb-grid]:not([hidden]) .mentor-card")
        cards = page.locator("[data-amb-grid] .mentor-card")
        self.assertEqual(cards.count(), 2)
        self.assertEqual(page.inner_text("[data-amb-count]"), "// 2 ambassadors confirmed so far")
        page.wait_for_function("""() => { const i = document.querySelector('[data-amb-grid] .mentor-card img');
                                          return i && i.complete && i.naturalWidth > 0; }""", timeout=5000)
        first = cards.nth(0)
        self.assertTrue(first.locator("img").get_attribute("src").endswith("/assets/img/ambassadors/rayan-s.jpg"))
        self.assertEqual(first.locator(".m-ini").inner_text(), "RS")         # initials stay underneath
        self.assertEqual(first.locator(".m-role").inner_text(), "Monte Vista High School · Danville CA")
        self.assertEqual(first.locator(".m-tag").all_inner_texts(), ["Class of 2027", "Clubs you're in", "Local events"])
        # no saved copy and a dead LinkedIn link: the <img> goes away, the initials show, no broken icon
        page.wait_for_function("() => !document.querySelectorAll('[data-amb-grid] .mentor-card')[1].querySelector('img')",
                               timeout=5000)
        self.assertEqual(cards.nth(1).locator(".m-ini").inner_text(), "NY")
        self.assertEqual([e for e in errors if "licdn" not in e and "ERR_FAILED" not in e], [])


if __name__ == "__main__":
    unittest.main()
