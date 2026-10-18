"""Unit tests for assets/js/roster.js — the mentor data layer behind /network/ and the homepage
"Mentors:" strip. Run from the site root:

    python3 -m unittest tools/test_roster_js.py

Standard library only; runs roster.js under Node with a tiny window/document stand-in, and is
skipped when Node isn't installed. The browser behaviour (motion, hover, focus) is covered by
tools/test_home_strip.py.
"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROSTER = ROOT / "assets" / "js" / "roster.js"

HARNESS = r"""
const window = globalThis;
globalThis.window = window;
globalThis.document = { createElement: () => ({}) };
const calls = { rpc: 0 };
const ROWS = JSON.parse(process.env.ROWS || "[]");
const MANIFEST = JSON.parse(process.env.MANIFEST || "{}");
globalThis.fetch = async (url) => ({ ok: true, json: async () => MANIFEST });
window.B0 = { rpc: async (name) => { calls.rpc++; if (process.env.FAIL) throw new Error("boom"); return ROWS; } };
require(process.env.ROSTER);
const R = window.B0Roster;
(async () => {
  const out = { linkedin: {}, calls };
  for (const u of JSON.parse(process.env.URLS || "[]")) out.linkedin[u] = R.linkedInUrl(u);
  try {
    const [a, b] = await Promise.all([R.mentors(), R.mentors()]);
    out.mentors = a; out.same = a === b;
  } catch (e) { out.error = e.message; }
  out.clean = R.clean("  a \n\t b  ", 0);
  out.cleanCap = R.clean("x".repeat(50), 10);
  out.initials = [R.initials("Greg Nagy"), R.initials("cher"), R.initials("  ")];
  console.log(JSON.stringify(out));
})();
"""


def run(**env):
    node = shutil.which("node")
    full = {"ROSTER": str(ROSTER), "PATH": "/usr/bin:/bin"}
    for k, v in env.items():
        full[k] = v if isinstance(v, str) else json.dumps(v)
    out = subprocess.run([node, "-e", HARNESS], capture_output=True, text=True, env=full, check=True)
    return json.loads(out.stdout)


@unittest.skipUnless(shutil.which("node"), "node not installed")
class LinkedInUrl(unittest.TestCase):
    GOOD = {
        "https://www.linkedin.com/in/greg-nagy/": "https://www.linkedin.com/in/greg-nagy/",
        "https://linkedin.com/in/a": "https://linkedin.com/in/a",
        "http://www.linkedin.com/in/a": "https://www.linkedin.com/in/a",          # upgraded
        "linkedin.com/in/no-scheme": "https://linkedin.com/in/no-scheme",
        "www.linkedin.com/in/x": "https://www.linkedin.com/in/x",
        "HTTPS://WWW.LINKEDIN.COM/in/Caps": "https://www.linkedin.com/in/Caps",   # host lower-cased
        "https://uk.linkedin.com/in/country": "https://uk.linkedin.com/in/country",
        "https://www.linkedin.com/pub/old-style/1/2/3": "https://www.linkedin.com/pub/old-style/1/2/3",
        "https://www.linkedin.com/in/a?trk=x#top": "https://www.linkedin.com/in/a",  # tracking dropped
        "  https://www.linkedin.com/in/padded  ": "https://www.linkedin.com/in/padded",
    }
    BAD = [
        "", "   ", "javascript:alert(1)", "JavaScript:alert(1)//linkedin.com/in/x",
        "data:text/html,linkedin.com/in/x", "https://linkedin.com.evil.net/in/x",
        "https://evil.com/linkedin.com/in/x", "https://notlinkedin.com/in/x",
        "https://www.linkedin.com/company/foo", "https://www.linkedin.com/", "https://www.linkedin.com/in/",
        "https://user:pw@www.linkedin.com/in/x", "https://www.linkedin.com:8443/in/x",
        "https://www.linkedin.com/in/a b", "ftp://www.linkedin.com/in/x",
        "https://www.linkedin.com/in/" + "x" * 300,
    ]

    def test_accepts_profile_links_and_cleans_them(self):
        out = run(URLS=list(self.GOOD))["linkedin"]
        for raw, want in self.GOOD.items():
            self.assertEqual(out[raw], want, raw)

    def test_rejects_everything_else(self):
        out = run(URLS=self.BAD)["linkedin"]
        for raw in self.BAD:
            self.assertEqual(out[raw], "", raw)


@unittest.skipUnless(shutil.which("node"), "node not installed")
class Mentors(unittest.TestCase):
    ROWS = [
        {"full_name": "Greg Nagy", "title": "COO", "company": "MDisrupt", "areas_of_expertise": "Product, Growth / marketing; Operations",
         "photo_url": "https://media.licdn.com/dms/image/p.jpg", "bio": "  Built   and ran\nops. ", "linkedin_url": "linkedin.com/in/greg"},
        {"full_name": "Wendy Chan", "title": "Founder", "company": None, "areas_of_expertise": "Community",
         "photo_url": None, "bio": None, "linkedin_url": "javascript:alert(1)"},
        {"full_name": "   ", "title": "Ghost"},                       # no name → dropped
        # an older list_mentors() (before bio/linkedin_url existed) must still work
        {"full_name": "Pouria Sanae", "title": "CEO", "company": "ixlayer", "areas_of_expertise": "Sales", "photo_url": None},
    ]

    def test_normalizes_rows(self):
        out = run(ROWS=self.ROWS, MANIFEST={"greg-nagy": "greg-nagy.jpg", "wendy-chan": "../../evil.jpg"})
        m = out["mentors"]
        self.assertEqual([x["name"] for x in m], ["Greg Nagy", "Wendy Chan", "Pouria Sanae"])
        g, w, p = m
        self.assertEqual(g["role"], "COO · MDisrupt")
        self.assertEqual(g["areas"], ["Product", "Growth / marketing", "Operations"])
        self.assertEqual(g["bio"], "Built and ran ops.")
        self.assertEqual(g["linkedin"], "https://linkedin.com/in/greg")
        # our archived copy first, then LinkedIn's link
        self.assertEqual(g["photos"], ["/assets/img/mentors/greg-nagy.jpg", "https://media.licdn.com/dms/image/p.jpg"])
        self.assertEqual(w["role"], "Founder")
        self.assertEqual(w["bio"], "")
        self.assertEqual(w["linkedin"], "", "a bad link never becomes an href")
        self.assertEqual(w["photos"], [], "a manifest entry with a path in it is ignored")
        self.assertEqual((p["bio"], p["linkedin"]), ("", ""))

    def test_one_request_however_many_callers(self):
        out = run(ROWS=self.ROWS)
        self.assertTrue(out["same"])
        self.assertEqual(out["calls"]["rpc"], 1)

    def test_failure_rejects_so_pages_can_show_their_error(self):
        out = run(ROWS=self.ROWS, FAIL="1")
        self.assertEqual(out["error"], "boom")

    def test_long_bio_is_capped(self):
        out = run(ROWS=[{"full_name": "A B", "bio": "word " * 400}])
        self.assertLessEqual(len(out["mentors"][0]["bio"]), 600)
        self.assertTrue(out["mentors"][0]["bio"].endswith("…"))

    def test_helpers(self):
        out = run()
        self.assertEqual(out["clean"], "a b")
        self.assertEqual(len(out["cleanCap"]), 10)
        self.assertEqual(out["initials"], ["GN", "C", "—"])


if __name__ == "__main__":
    unittest.main()
