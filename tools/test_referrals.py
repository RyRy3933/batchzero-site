"""Tests for the referral program: assets/js/referral.js, the pages it runs on, and supabase/referrals.sql.

Run from the site root:  python3 -m unittest tools/test_referrals.py

The JavaScript helpers are exercised through node (skipped if node isn't installed). The QR test
decodes the code referral.js draws with OpenCV when it's available, so a QR that looks right but
scans wrong fails here instead of on a printed flyer.
"""
import json, os, re, shutil, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, ".."))
NODE = shutil.which("node")


def read(rel):
    with open(os.path.join(SITE, rel), encoding="utf-8") as f:
        return f.read()


def node(script):
    """Run a node snippet with `R` = referral.js and `qrcode` = the vendored library; returns parsed JSON."""
    prelude = (
        f"const R = require({json.dumps(os.path.join(SITE, 'assets/js/referral.js'))});\n"
        f"const qrcode = require({json.dumps(os.path.join(SITE, 'assets/js/vendor/qrcode.js'))});\n"
    )
    out = subprocess.run([NODE, "-e", prelude + script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


class FakeStorageMixin:
    STORAGE_JS = """
      function store(init) { const m = new Map(Object.entries(init || {}));
        return { getItem: k => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, String(v)), _m: m }; }
      const broken = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); } };
    """


@unittest.skipUnless(NODE, "node not installed")
class ReferralHelpers(unittest.TestCase, FakeStorageMixin):
    def test_clean_ref_accepts_issued_codes_only(self):
        r = node("""console.log(JSON.stringify([
          R.cleanRef('maya-r-7k2f'), R.cleanRef('  MAYA-R-7K2F '), R.cleanRef('flyer'),
          R.cleanRef(''), R.cleanRef(null), R.cleanRef('-maya'), R.cleanRef('maya-'),
          R.cleanRef('a b'), R.cleanRef('<script>'), R.cleanRef('x'.repeat(49)), R.cleanRef('x'.repeat(48))]))""")
        self.assertEqual(r[:3], ["maya-r-7k2f", "maya-r-7k2f", "flyer"])
        self.assertEqual(r[3:10], [""] * 7)
        self.assertEqual(r[10], "x" * 48)

    def test_slug_name(self):
        r = node("""console.log(JSON.stringify([R.slugName('Maya Rodríguez'), R.slugName('  jo  '),
          R.slugName('Mary Anne de la Cruz'), R.slugName('李 雷'), R.slugName(''), R.slugName("D'Angelo O'Neil")]))""")
        self.assertEqual(r, ["maya-r", "jo", "mary-c", "", "", "dangelo-o"])

    def test_make_code_is_deterministic_with_bytes_and_always_clean(self):
        r = node("""
          const fixed = R.makeCode('Maya Rodríguez', new Uint8Array([0, 1, 2, 30]));
          const fallback = R.makeCode('', new Uint8Array([0, 0, 0, 0]));
          const many = Array.from({length: 500}, (_, i) => R.makeCode(['Ana B', 'Zoë', '', '李 雷', 'x'.repeat(80)][i % 5]));
          console.log(JSON.stringify({fixed, fallback, allClean: many.every(c => R.cleanRef(c) === c),
                                      unique: new Set(many).size}))""")
        self.assertEqual(r["fixed"], "maya-r-abc9")
        self.assertEqual(r["fallback"], "friend-aaaa")
        self.assertTrue(r["allClean"])
        self.assertGreater(r["unique"], 480)   # 31^4 tails: collisions in 500 draws should be rare

    def test_codes_avoid_lookalike_characters(self):
        r = node("""const s = Array.from({length: 2000}, () => R.randomTail()).join('');
                    console.log(JSON.stringify(/[01ilo]/.test(s)))""")
        self.assertFalse(r)

    def test_links(self):
        r = node("""console.log(JSON.stringify([R.referralLink('maya-r-7k2f'), R.flyerLink('maya-r-7k2f', ''),
                    R.referralLink('bad code'), R.shareText('maya-r-7k2f')]))""")
        self.assertEqual(r[0], "https://batchzero.co/apply/founders/?ref=maya-r-7k2f")
        self.assertEqual(r[1], "/refer/flyer/?ref=maya-r-7k2f")
        self.assertEqual(r[2], "https://batchzero.co/apply/founders/?ref=")
        self.assertIn("Oct 31", r[3]); self.assertTrue(r[3].endswith(r[0]))

    def test_resolve_ref_url_wins_and_is_remembered(self):
        r = node(self.STORAGE_JS + """
          const s = store();
          const a = R.resolveRef('?ref=Maya-R-7K2F&utm=x', s, 1000);
          const b = R.resolveRef('', s, 2000);                         // came back without the link
          const c = R.resolveRef('?ref=flyer', s, 3000);               // a newer link replaces it
          const d = R.resolveRef('', s, 3000 + R.TTL_MS + 1);          // 60 days later: forgotten
          const e = R.resolveRef('?ref=%3Cscript%3E', store(), 1);     // junk is ignored
          console.log(JSON.stringify({a, b, c, d, e}))""")
        self.assertEqual(r, {"a": "maya-r-7k2f", "b": "maya-r-7k2f", "c": "flyer", "d": "", "e": ""})

    def test_storage_failures_never_throw(self):
        r = node(self.STORAGE_JS + """
          const tampered = store({'b0-ref': '{"ref":"<x>","at":1}'});
          const garbage = store({'b0-ref': 'not json'});
          console.log(JSON.stringify([R.resolveRef('?ref=maya-r-7k2f', broken, 1), R.resolveRef('', broken, 1),
            R.readStored(tampered, 2), R.readStored(garbage, 2), R.readStored(null, 2)]))""")
        self.assertEqual(r, ["maya-r-7k2f", "", "", "", ""])

    def test_qr_path_covers_exactly_the_dark_modules(self):
        r = node("""
          const q = qrcode(0, 'M'); q.addData(R.referralLink('maya-r-7k2f')); q.make();
          const {size, d} = R.qrPath(q);
          let dark = 0; for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) if (q.isDark(y, x)) dark++;
          let painted = 0; for (const m of d.matchAll(/M(\\d+) (\\d+)h(\\d+)v1h-(\\d+)z/g)) painted += +m[3];
          console.log(JSON.stringify({size, dark, painted}))""")
        self.assertEqual(r["dark"], r["painted"])
        self.assertGreaterEqual(r["size"], 25)

    def test_qr_scans_back_to_the_link(self):
        try:
            import cv2, numpy as np
        except ImportError:
            self.skipTest("opencv not installed")
        link = "https://batchzero.co/apply/founders/?ref=maya-r-7k2f"
        r = node(f"""
          const q = qrcode(0, 'M'); q.addData({json.dumps(link)}); q.make();
          const n = q.getModuleCount(), rows = [];
          for (let y = 0; y < n; y++) {{ let row = ''; for (let x = 0; x < n; x++) row += q.isDark(y, x) ? '1' : '0'; rows.push(row); }}
          const {{d}} = R.qrPath(q);
          console.log(JSON.stringify({{rows, d}}))""")
        # rasterise referral.js's own path (not the library's matrix) so the test covers qrPath
        n = len(r["rows"]); scale, quiet = 10, 4
        img = np.full(((n + 2 * quiet) * scale,) * 2, 255, np.uint8)
        for m in re.finditer(r"M(\d+) (\d+)h(\d+)v1h-\d+z", r["d"]):
            x, y, w = map(int, m.groups())
            img[(y + quiet) * scale:(y + quiet + 1) * scale, (x + quiet) * scale:(x + quiet + w) * scale] = 0
        text, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        self.assertEqual(text, link)


class BuiltPages(unittest.TestCase):
    """The generated HTML. Rebuild first (python3 tools/build.py) — CI and the deploy steps both do."""

    def test_founder_form_carries_referral_fields(self):
        html = read("apply/founders/index.html")
        self.assertIn('name="referred_by"', html)
        self.assertRegex(html, r'<input type="hidden" name="ref" value="" data-draft>')
        self.assertIn("data-ref-note", html)
        self.assertNotRegex(html, r'id="referred_by"[^>]*required')            # optional
        self.assertIn('src="/assets/js/referral.js"', html)
        self.assertLess(html.index("/assets/js/site.js"), html.index("/assets/js/referral.js"))

    def test_refer_page(self):
        html = read("refer/index.html")
        self.assertIn("data-refer data-custom-submit", html)
        for name in ("name", "email", "role", "school", "club", "consent"):
            self.assertIn(f'name="{name}"', html)
        self.assertIn("$100", html)
        self.assertIn("One bonus per accepted startup", html)
        self.assertNotIn('name="robots" content="noindex"', html)
        js = [m for m in re.findall(r'<script src="([^"]+)"', html)]
        self.assertEqual(js[-3:], ["/assets/js/site.js", "/assets/js/vendor/qrcode.js", "/assets/js/referral.js"])

    def test_flyer_page_is_private_and_printable(self):
        html = read("refer/flyer/index.html")
        self.assertIn('name="robots" content="noindex"', html)
        self.assertIn("data-flyer-qr", html)
        self.assertIn("Already building something?", html)
        self.assertNotIn("/refer/flyer/", read("sitemap.xml"))
        self.assertIn("Disallow: /refer/flyer/", read("robots.txt"))
        self.assertIn("/refer/", read("sitemap.xml"))
        self.assertIn("@page { size: letter; margin: 0; }", read("assets/css/site.css"))

    def test_every_page_links_the_program_in_its_footer(self):
        for root, _, files in os.walk(SITE):
            if any(p in root for p in (".git", "node_modules", "_previews")):
                continue
            for f in files:
                if f.endswith(".html"):
                    self.assertIn('href="/refer/"', read(os.path.relpath(os.path.join(root, f), SITE)), f"{root}/{f}")

    def test_review_desk_can_filter_referrers(self):
        self.assertIn('<option value="referrer">Referrers</option>', read("review/index.html"))

    def test_site_js_exposes_submit(self):
        self.assertRegex(read("assets/js/site.js"), r"submit: submitApplication")

    def test_privacy_policy_discloses_the_stored_code(self):
        html = read("privacy/index.html")
        self.assertIn("<strong>Referrals.</strong>", html)
        self.assertIn("60 days", html)


class Migration(unittest.TestCase):
    sql = read("supabase/referrals.sql")

    def test_type_added_in_both_places(self):
        # ambassadors.sql's lesson: the CHECK and the insert policy each list the types
        self.assertEqual(len(re.findall(r"'ambassador','referrer','unknown'", self.sql)), 2)

    def test_report_is_key_gated_and_never_exposes_more_than_it_needs(self):
        self.assertIn("perform private.check_admin_key(p_admin_key);", self.sql)
        self.assertIn("security definer", self.sql)
        self.assertNotIn("grant select", self.sql.lower())

    def test_matches_referral_js_field_names(self):
        js = read("assets/js/referral.js")
        self.assertIn("data.code = R.makeCode", js)        # referrer rows carry payload.code
        self.assertIn("payload->>'code'", self.sql)
        self.assertIn('name="ref"', read("apply/founders/index.html"))   # founder rows carry payload.ref
        self.assertIn("payload->>'ref'", self.sql)
        self.assertIn("payload->>'kind' = 'referrer'", self.sql)      # backfills the JS fallback
        self.assertIn('kind: "referrer"', js)


if __name__ == "__main__":
    unittest.main()
