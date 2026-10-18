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


if __name__ == "__main__":
    unittest.main()
