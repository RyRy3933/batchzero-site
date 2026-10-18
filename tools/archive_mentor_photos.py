#!/usr/bin/env python3
"""Keep a self-hosted copy of every mentor photo shown on /network/.

Why: mentors sign in with LinkedIn at /mentor-invite/, and the photo LinkedIn hands back is a
signed media.licdn.com link that stops working after a few weeks. Hotlinking it means the
roster quietly turns into initials. This script copies each photo into assets/img/mentors/
while the link still works and records it in photos.json, which assets/js/network.js reads
first. It runs every day from .github/workflows/mentor-photos.yml, so a new mentor's photo is
saved well before their link expires.

What it does, every run:
  1. Calls list_mentors() with the public anon key from assets/js/config.js — the same call
     the /network/ page makes, so it only ever sees what the page already shows.
  2. Downloads the photo of any listed mentor who doesn't have a saved copy yet.
  3. Deletes saved photos of anyone no longer listed (hidden with published = false, or
     removed), so taking someone off the site takes their photo off the site too.

Run it by hand from the site root:
  python3 tools/archive_mentor_photos.py                     # the daily sync
  python3 tools/archive_mentor_photos.py --dry-run           # say what would change
  python3 tools/archive_mentor_photos.py --add "Greg Nagy" "https://media.licdn.com/…"
      # save a fresh photo for one mentor (e.g. after their stored link already expired);
      # the name must match their card exactly. Replaces any copy already saved.

Standard library only; Python 3.10+. No tokens: the anon key is public by design.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CONFIG_JS = ROOT / "assets" / "js" / "config.js"
PHOTO_DIR = ROOT / "assets" / "img" / "mentors"
MANIFEST = PHOTO_DIR / "photos.json"

MAX_BYTES = 5 * 1024 * 1024           # a LinkedIn profile photo is ~10-200 KB
TIMEOUT = 20
USER_AGENT = "batchzero-photo-archiver/1.0 (+https://batchzero.co)"
FILE_RE = re.compile(r"^[a-z0-9-]+\.(jpe?g|png|webp)$")   # same rule network.js enforces

# LinkedIn photos only — the same rule save_mentor_photo() applies in the database
LICDN_RE = re.compile(r"^https://([a-z0-9-]+\.)+licdn\.com/[^\s\"'<>]+$")


def slug(name: str) -> str:
    """Must stay identical to slug() in assets/js/network.js."""
    s = unicodedata.normalize("NFKD", str(name or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s.lower())
    return s.strip("-")


def sniff(data: bytes) -> str | None:
    """File extension from the image's magic bytes, or None if it isn't a JPEG/PNG/WebP."""
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def read_config() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not (url and key):
        text = CONFIG_JS.read_text(encoding="utf-8")
        m_url = re.search(r'SUPABASE_URL:\s*"([^"]+)"', text)
        m_key = re.search(r'SUPABASE_ANON_KEY:\s*"([^"]+)"', text)
        url = url or (m_url.group(1) if m_url else "")
        key = key or (m_key.group(1) if m_key else "")
    if not (url.startswith("https://") and key):
        sys.exit("archive: no Supabase URL / anon key in assets/js/config.js or the environment")
    return url.rstrip("/"), key


def list_mentors(url: str, key: str) -> list[dict]:
    req = urllib.request.Request(
        f"{url}/rest/v1/rpc/list_mentors",
        data=b"{}",
        method="POST",
        headers={"apikey": key, "Authorization": f"Bearer {key}",
                 "Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        rows = json.load(r)
    if not isinstance(rows, list):
        raise ValueError(f"list_mentors returned {type(rows).__name__}, expected a list")
    return rows


def download(photo_url: str) -> tuple[bytes, str]:
    """Fetch a LinkedIn photo. Raises ValueError with a readable reason on anything off."""
    if not LICDN_RE.match(photo_url or "") or len(photo_url) > 2000:
        raise ValueError("not a LinkedIn image URL")
    req = urllib.request.Request(photo_url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            # a redirect off LinkedIn's CDN is not something we follow into the repo
            if not LICDN_RE.match(r.geturl()):
                raise ValueError("redirected away from LinkedIn")
            data = r.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        raise ValueError(f"LinkedIn answered {e.code} (the link has probably expired)") from None
    except urllib.error.URLError as e:
        raise ValueError(f"couldn't reach LinkedIn ({e.reason})") from None
    if len(data) > MAX_BYTES:
        raise ValueError("bigger than 5 MB")
    ext = sniff(data)
    if not ext:
        raise ValueError("not a JPEG, PNG or WebP image")
    return data, ext


def load_manifest() -> dict[str, str]:
    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("archive: photos.json was unreadable, starting a fresh one", file=sys.stderr)
        return {}
    return {k: v for k, v in m.items() if isinstance(k, str) and isinstance(v, str) and FILE_RE.match(v)} \
        if isinstance(m, dict) else {}


def save_manifest(m: dict[str, str]) -> None:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(dict(sorted(m.items())), indent=2) + "\n", encoding="utf-8")


def store(manifest: dict[str, str], key: str, data: bytes, ext: str, dry: bool) -> str:
    name = f"{key}.{ext}"
    if not dry:
        PHOTO_DIR.mkdir(parents=True, exist_ok=True)
        old = manifest.get(key)
        if old and old != name:
            (PHOTO_DIR / old).unlink(missing_ok=True)
        (PHOTO_DIR / name).write_bytes(data)
    manifest[key] = name
    return name


def sync(mentors: list[dict], manifest: dict[str, str], dry: bool,
         fetch=download) -> tuple[list[str], list[str], list[str]]:
    """The daily pass. Returns (saved, removed, problems) as human-readable lines."""
    saved, removed, problems = [], [], []
    listed = {}
    for m in mentors:
        name = (m or {}).get("full_name") or ""
        key = slug(name)
        if key:
            listed[key] = (name, (m or {}).get("photo_url") or "")

    for key, (name, url) in listed.items():
        have = manifest.get(key)
        if have and (PHOTO_DIR / have).is_file():
            continue
        if not url:
            continue                                  # no photo to keep; initials it is
        try:
            data, ext = fetch(url)
        except ValueError as e:
            problems.append(f"{name}: {e}")
            continue
        saved.append(f"{name} -> {store(manifest, key, data, ext, dry)}")

    for key in sorted(set(manifest) - set(listed)):
        removed.append(f"{key} ({manifest[key]})")
        if not dry:
            (PHOTO_DIR / manifest[key]).unlink(missing_ok=True)
        del manifest[key]

    return saved, removed, problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    p.add_argument("--add", nargs=2, action="append", metavar=("NAME", "PHOTO_URL"), default=[],
                   help="save this LinkedIn photo for this listed mentor (repeatable)")
    a = p.parse_args(argv)

    url, key = read_config()
    try:
        mentors = list_mentors(url, key)
    except Exception as e:                            # noqa: BLE001 — any failure means "stop, change nothing"
        print(f"archive: list_mentors failed, nothing changed: {e}", file=sys.stderr)
        return 1

    manifest = load_manifest()
    names = {slug(m.get("full_name") or ""): m.get("full_name") for m in mentors}
    failed = False

    for name, photo_url in a.add:
        k = slug(name)
        if k not in names:
            print(f"archive: {name!r} isn't on the roster (listed: {', '.join(filter(None, names.values()))})",
                  file=sys.stderr)
            failed = True
            continue
        try:
            data, ext = download(photo_url)
        except ValueError as e:
            print(f"archive: {name}: {e}", file=sys.stderr)
            failed = True
            continue
        print(f"added    {names[k]} -> {store(manifest, k, data, ext, a.dry_run)}")

    saved, removed, problems = sync(mentors, manifest, a.dry_run)
    for line in saved:
        print(f"saved    {line}")
    for line in removed:
        print(f"removed  {line} (no longer on the roster)")
    for line in problems:
        print(f"skipped  {line}")
    if not a.dry_run:
        save_manifest(manifest)
    if not (a.add or saved or removed or problems):
        print(f"archive: all {len(mentors)} mentor(s) up to date")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
