"""Tests for tools/archive_mentor_photos.py.  Run from the site root:

    python3 -m unittest tools/test_archive_mentor_photos.py

Standard library only. The slug-parity test also runs roster.js's slug() under Node when
Node is installed, and is skipped otherwise.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import archive_mentor_photos as amp  # noqa: E402

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64
NAMES = ["Greg Nagy", "Arash Sohrabian", "  José  Núñez-O'Brien ", "Wendy C.", "", "李 Lee"]


class Slug(unittest.TestCase):
    def test_examples(self):
        self.assertEqual(amp.slug("Greg Nagy"), "greg-nagy")
        self.assertEqual(amp.slug("  José  Núñez-O'Brien "), "jose-nunez-o-brien")
        self.assertEqual(amp.slug("Wendy C."), "wendy-c")
        self.assertEqual(amp.slug(""), "")
        self.assertEqual(amp.slug(None), "")

    def test_matches_roster_js(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        src = (amp.ROOT / "assets" / "js" / "roster.js").read_text(encoding="utf-8")
        m = re.search(r"const slug = \(name\) =>([\s\S]*?);\n", src)
        self.assertIsNotNone(m, "slug() not found in roster.js")
        js = f"const slug = (name) =>{m.group(1)};\nconsole.log(JSON.stringify({json.dumps(NAMES)}.map(slug)));"
        out = subprocess.run([node, "-e", js], capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(out), [amp.slug(n) for n in NAMES])


class Sniff(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(amp.sniff(JPEG), "jpg")
        self.assertEqual(amp.sniff(PNG), "png")
        self.assertEqual(amp.sniff(WEBP), "webp")
        self.assertIsNone(amp.sniff(b"<html>nope</html>"))
        self.assertIsNone(amp.sniff(b""))


class Download(unittest.TestCase):
    def test_rejects_non_linkedin_urls_without_fetching(self):
        for bad in ["http://media.licdn.com/a.jpg", "https://evil.com/a.jpg",
                    "https://notlicdn.com/a.jpg", "https://media.licdn.com.evil.net/a.jpg",
                    "https://media.licdn.com/a b.jpg", ""]:
            with self.assertRaises(ValueError, msg=bad):
                amp.download(bad)


class Sync(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._dir = amp.PHOTO_DIR
        amp.PHOTO_DIR = self.tmp
        self.fetched = []

    def tearDown(self):
        amp.PHOTO_DIR = self._dir
        shutil.rmtree(self.tmp)

    def fetch(self, url):
        self.fetched.append(url)
        if "expired" in url:
            raise ValueError("LinkedIn answered 403 (the link has probably expired)")
        return (PNG, "png") if "png" in url else (JPEG, "jpg")

    def test_saves_new_skips_existing_removes_unlisted(self):
        (self.tmp / "greg-nagy.jpg").write_bytes(JPEG)
        (self.tmp / "gone-mentor.jpg").write_bytes(JPEG)
        manifest = {"greg-nagy": "greg-nagy.jpg", "gone-mentor": "gone-mentor.jpg"}
        mentors = [
            {"full_name": "Greg Nagy", "photo_url": "https://media.licdn.com/greg"},
            {"full_name": "New Person", "photo_url": "https://media.licdn.com/new-png"},
            {"full_name": "Wendy Chan", "photo_url": None},
            {"full_name": "Old Link", "photo_url": "https://media.licdn.com/expired"},
        ]
        saved, removed, problems = amp.sync(mentors, manifest, dry=False, fetch=self.fetch)

        self.assertEqual(saved, ["New Person -> new-person.png"])
        self.assertEqual(removed, ["gone-mentor (gone-mentor.jpg)"])
        self.assertEqual(len(problems), 1)
        self.assertIn("Old Link", problems[0])
        self.assertEqual(manifest, {"greg-nagy": "greg-nagy.jpg", "new-person": "new-person.png"})
        self.assertTrue((self.tmp / "new-person.png").is_file())
        self.assertFalse((self.tmp / "gone-mentor.jpg").exists())
        # already-saved photos are never re-downloaded
        self.assertNotIn("https://media.licdn.com/greg", self.fetched)

    def test_refetches_when_listed_file_went_missing(self):
        manifest = {"greg-nagy": "greg-nagy.jpg"}            # listed, but the file is gone
        mentors = [{"full_name": "Greg Nagy", "photo_url": "https://media.licdn.com/greg"}]
        saved, _, _ = amp.sync(mentors, manifest, dry=False, fetch=self.fetch)
        self.assertEqual(saved, ["Greg Nagy -> greg-nagy.jpg"])
        self.assertTrue((self.tmp / "greg-nagy.jpg").is_file())

    def test_dry_run_writes_nothing(self):
        (self.tmp / "gone.jpg").write_bytes(JPEG)
        manifest = {"gone": "gone.jpg"}
        mentors = [{"full_name": "New Person", "photo_url": "https://media.licdn.com/x"}]
        amp.sync(mentors, manifest, dry=True, fetch=self.fetch)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["gone.jpg"])

    def test_store_replaces_old_extension(self):
        (self.tmp / "greg-nagy.jpg").write_bytes(JPEG)
        manifest = {"greg-nagy": "greg-nagy.jpg"}
        amp.store(manifest, "greg-nagy", PNG, "png", dry=False)
        self.assertEqual(manifest["greg-nagy"], "greg-nagy.png")
        self.assertFalse((self.tmp / "greg-nagy.jpg").exists())

    def test_manifest_roundtrip_drops_bad_entries(self):
        amp.MANIFEST, saved_manifest = self.tmp / "photos.json", amp.MANIFEST
        try:
            amp.MANIFEST.write_text(json.dumps({"ok": "ok.jpg", "bad": "../../etc/passwd", "x": 3}))
            self.assertEqual(amp.load_manifest(), {"ok": "ok.jpg"})
            amp.MANIFEST.write_text("{not json")
            self.assertEqual(amp.load_manifest(), {})
        finally:
            amp.MANIFEST = saved_manifest


class NeverSilent(unittest.TestCase):
    """Anyone showing initials must surface — stdout, run summary, step output — every run."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.photos = self.tmp / "mentors"
        self.amb = self.tmp / "ambassadors"
        self.photos.mkdir()
        self._saved = (amp.PHOTO_DIR, amp.MANIFEST, amp.AMB_PHOTO_DIR, amp.list_mentors,
                       amp.list_ambassadors, amp.download, amp.read_config)
        amp.PHOTO_DIR, amp.MANIFEST, amp.AMB_PHOTO_DIR = self.photos, self.photos / "photos.json", self.amb
        amp.read_config = lambda: ("https://example.supabase.co", "anon")
        self.roster = [
            {"full_name": "Pouria Sanae", "photo_url": "https://media.licdn.com/pouria"},
            {"full_name": "Wendy Chan", "photo_url": None},
            {"full_name": "Greg Nagy", "photo_url": "https://media.licdn.com/expired-greg"},
        ]
        self.ambassadors = []
        amp.list_mentors = lambda url, key: self.roster
        amp.list_ambassadors = lambda url, key: self.ambassadors

        def fake_download(url):
            if "expired" in url:
                raise ValueError("LinkedIn answered 403 (the link has probably expired)")
            return JPEG, "jpg"
        amp.download = fake_download
        self.summary, self.output = self.tmp / "summary.md", self.tmp / "output.txt"
        self.env = {"GITHUB_STEP_SUMMARY": str(self.summary), "GITHUB_OUTPUT": str(self.output)}

    def tearDown(self):
        (amp.PHOTO_DIR, amp.MANIFEST, amp.AMB_PHOTO_DIR, amp.list_mentors,
         amp.list_ambassadors, amp.download, amp.read_config) = self._saved
        shutil.rmtree(self.tmp)

    def run_main(self, *args):
        import contextlib, io, os
        from unittest import mock
        buf = io.StringIO()
        if self.output.exists():
            self.output.unlink()
        with mock.patch.dict(os.environ, self.env), contextlib.redirect_stdout(buf), \
                contextlib.redirect_stderr(io.StringIO()):
            code = amp.main(list(args))
        return code, buf.getvalue()

    def test_missing_photos_are_reported_everywhere(self):
        code, out = self.run_main()
        self.assertEqual(code, 0)                       # still saves what it can, then reports
        self.assertIn("saved    Pouria Sanae", out)
        self.assertIn("NEEDS A PHOTO  Wendy Chan (mentor) — no LinkedIn photo on file", out)
        self.assertIn("NEEDS A PHOTO  Greg Nagy (mentor) — LinkedIn answered 403", out)
        self.assertNotIn("NEEDS A PHOTO  Pouria", out)
        summary = self.summary.read_text()
        self.assertIn("Wendy Chan", summary)
        self.assertIn("Greg Nagy", summary)
        self.assertIn("missing=2", self.output.read_text())   # the workflow fails on this

    def test_all_saved_reports_zero(self):
        self.roster = self.roster[:1]
        self.run_main()
        self.assertIn("missing=0", self.output.read_text())
        self.assertFalse(self.summary.exists())
        _, out = self.run_main()
        self.assertIn("all 1 people on the site have a saved photo", out)

    def test_add_from_local_file_fixes_a_mentor_with_no_link(self):
        headshot = self.tmp / "wendy.png"
        headshot.write_bytes(PNG)
        code, out = self.run_main("--add", "Wendy Chan", str(headshot))
        self.assertEqual(code, 0)
        self.assertIn("added    Wendy Chan (mentor) -> wendy-chan.png", out)
        self.assertTrue((self.photos / "wendy-chan.png").is_file())
        self.assertEqual(json.loads(amp.MANIFEST.read_text())["wendy-chan"], "wendy-chan.png")
        self.assertNotIn("NEEDS A PHOTO  Wendy", out)
        self.assertIn("missing=1", self.output.read_text())   # only Greg left

    def test_add_rejects_bad_input(self):
        not_image = self.tmp / "notes.jpg"
        not_image.write_bytes(b"hello, not a jpeg")
        self.assertEqual(self.run_main("--add", "Wendy Chan", str(not_image))[0], 1)
        self.assertEqual(self.run_main("--add", "Wendy Chan", str(self.tmp / "nope.jpg"))[0], 1)
        self.assertEqual(self.run_main("--add", "Not A Mentor", str(not_image))[0], 1)
        self.assertFalse((self.photos / "wendy-chan.jpg").exists())

    def test_add_still_takes_linkedin_links(self):
        code, out = self.run_main("--add", "Greg Nagy", "https://media.licdn.com/fresh-greg")
        self.assertEqual(code, 0)
        self.assertIn("added    Greg Nagy (mentor) -> greg-nagy.jpg", out)
        self.assertIn("missing=1", self.output.read_text())   # Wendy

    def test_dry_run_reports_without_writing(self):
        code, out = self.run_main("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("NEEDS A PHOTO  Wendy Chan", out)
        self.assertNotIn("NEEDS A PHOTO  Pouria", out)        # would be saved
        self.assertEqual(list(self.photos.iterdir()), [])

    # ---------- ambassadors ----------
    def test_ambassadors_are_archived_into_their_own_folder(self):
        self.roster = self.roster[:1]
        self.ambassadors = [
            {"display_name": "Maya R.", "school": "Monte Vista", "photo_url": "https://media.licdn.com/maya"},
            {"display_name": "Sam K.", "school": "Dougherty Valley", "photo_url": None},
        ]
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("saved    Maya R. -> maya-r.jpg (ambassador)", out)
        self.assertTrue((self.amb / "maya-r.jpg").is_file())
        self.assertEqual(json.loads((self.amb / "photos.json").read_text()), {"maya-r": "maya-r.jpg"})
        self.assertFalse((self.photos / "maya-r.jpg").exists())       # never mixed with mentors
        self.assertIn("NEEDS A PHOTO  Sam K. (ambassador) — no LinkedIn photo on file", out)
        self.assertIn("Sam K.", self.summary.read_text())
        self.assertIn("missing=1", self.output.read_text())

    def test_add_finds_an_ambassador_by_card_name(self):
        self.ambassadors = [{"display_name": "Sam K.", "photo_url": None}]
        headshot = self.tmp / "sam.jpg"
        headshot.write_bytes(JPEG)
        code, out = self.run_main("--add", "Sam K.", str(headshot))
        self.assertEqual(code, 0)
        self.assertIn("added    Sam K. (ambassador) -> sam-k.jpg", out)
        self.assertTrue((self.amb / "sam-k.jpg").is_file())

    def test_unlisted_ambassador_loses_their_photo(self):
        # unticking "show me", published = false or removal all mean: off the site, photo too
        self.amb.mkdir()
        (self.amb / "gone-s.jpg").write_bytes(JPEG)
        (self.amb / "photos.json").write_text(json.dumps({"gone-s": "gone-s.jpg"}))
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("removed  gone-s (gone-s.jpg) (ambassador, no longer on the site)", out)
        self.assertFalse((self.amb / "gone-s.jpg").exists())
        self.assertEqual(json.loads((self.amb / "photos.json").read_text()), {})

    def test_same_name_on_both_rosters_is_refused(self):
        self.ambassadors = [{"display_name": "Wendy Chan", "photo_url": None}]
        headshot = self.tmp / "w.jpg"
        headshot.write_bytes(JPEG)
        code, _ = self.run_main("--add", "Wendy Chan", str(headshot))
        self.assertEqual(code, 1)

    def test_a_failing_roster_changes_nothing(self):
        def boom(url, key):
            raise OSError("down")
        amp.list_ambassadors = boom
        code, _ = self.run_main()
        self.assertEqual(code, 1)
        self.assertEqual(list(self.photos.iterdir()), [])              # mentors untouched too


class RepoPhotos(unittest.TestCase):
    """The committed photos themselves: every manifest entry is a real, reasonable image."""

    def test_manifest_entries_are_real_images(self):
        for folder in (amp.PHOTO_DIR, amp.AMB_PHOTO_DIR):
            with self.subTest(folder=folder.name):
                manifest = json.loads((folder / "photos.json").read_text())
                self.assertTrue(manifest)
                for key, file in manifest.items():
                    self.assertRegex(file, amp.FILE_RE)
                    self.assertEqual(file.split(".")[0], key)
                    data = (folder / file).read_bytes()
                    self.assertIsNotNone(amp.sniff(data), file)
                    self.assertLess(len(data), 200_000, f"{file} is heavy for a 72px avatar")
                on_disk = {p.name for p in folder.iterdir() if p.name != "photos.json"}
                self.assertEqual(on_disk, set(manifest.values()), "orphan or missing photo files")


if __name__ == "__main__":
    unittest.main()
