#!/usr/bin/env python3
"""Keep a self-hosted copy of every photo on /network/ — mentors and student ambassadors.

Why: the photo LinkedIn hands back at sign-in (mentors at /mentor-invite/, ambassadors on the
application form) is a signed media.licdn.com link that stops working after a few weeks.
Hotlinking it means the roster quietly turns into initials. This script copies each photo
into assets/img/mentors/ or assets/img/ambassadors/ while the link still works and records it
in that folder's photos.json, which assets/js/roster.js reads first. It runs every day from
.github/workflows/mentor-photos.yml, so a new person's photo is saved before their link expires.

What it does, every run, for each roster (list_mentors() by full_name, list_ambassadors() by
display_name — the name on the card):
  1. Calls the roster function with the public anon key from assets/js/config.js — the same
     call the /network/ page makes, so it only ever sees what the page already shows.
  2. Downloads the photo of anyone listed who doesn't have a saved copy yet.
  3. Deletes saved photos of anyone no longer listed (hidden with published = false, unticked,
     or removed), so taking someone off the site takes their photo off the site too.

Run it by hand from the site root:
  python3 tools/archive_mentor_photos.py                     # the daily sync
  python3 tools/archive_mentor_photos.py --dry-run           # say what would change
  python3 tools/archive_mentor_photos.py --add "Greg Nagy" "https://media.licdn.com/…"
  python3 tools/archive_mentor_photos.py --add "Maya R." ~/Downloads/maya.jpg
      # save a photo for one listed mentor or ambassador from a fresh LinkedIn link OR a local
      # JPEG/PNG/WebP file (their link expired, or they never had one). The name must match
      # their card exactly. Replaces any copy already saved.

Never silent: anyone listed who still has no saved photo after the run is printed under
"NEEDS A PHOTO", written to the GitHub run summary, and counted in the `missing` step output —
the workflow turns red on it (after committing whatever it did save), so GitHub emails you
the day it happens instead of the roster quietly turning into initials.

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
AMB_PHOTO_DIR = ROOT / "assets" / "img" / "ambassadors"

MAX_BYTES = 5 * 1024 * 1024           # a LinkedIn profile photo is ~10-200 KB
TIMEOUT = 20
USER_AGENT = "batchzero-photo-archiver/1.0 (+https://batchzero.co)"
FILE_RE = re.compile(r"^[a-z0-9-]+\.(jpe?g|png|webp)$")   # same rule roster.js enforces

# LinkedIn photos only — the same rule save_mentor_photo() applies in the database
LICDN_RE = re.compile(r"^https://([a-z0-9-]+\.)+licdn\.com/[^\s\"'<>]+$")


def slug(name: str) -> str:
    """Must stay identical to slug() in assets/js/roster.js."""
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


def _rpc_list(fn: str, url: str, key: str) -> list[dict]:
    req = urllib.request.Request(
        f"{url}/rest/v1/rpc/{fn}",
        data=b"{}",
        method="POST",
        headers={"apikey": key, "Authorization": f"Bearer {key}",
                 "Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        rows = json.load(r)
    if not isinstance(rows, list):
        raise ValueError(f"{fn} returned {type(rows).__name__}, expected a list")
    return rows


def list_mentors(url: str, key: str) -> list[dict]:
    return _rpc_list("list_mentors", url, key)


def list_ambassadors(url: str, key: str) -> list[dict]:
    return _rpc_list("list_ambassadors", url, key)


def rosters() -> list[tuple[str, str, Path, Path]]:
    """(label, name field, photo folder, manifest) per roster. Built per call so tests can
    point the folders somewhere else."""
    return [
        ("mentor", "full_name", PHOTO_DIR, MANIFEST),
        ("ambassador", "display_name", AMB_PHOTO_DIR, AMB_PHOTO_DIR / "photos.json"),
    ]


def fetch_roster(label: str, url: str, key: str) -> list[dict]:
    return (list_mentors if label == "mentor" else list_ambassadors)(url, key)


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


def read_local(path: str) -> tuple[bytes, str]:
    """A headshot from disk, for --add. Same checks as a download: real image, under 5 MB."""
    f = Path(path).expanduser()
    if not f.is_file():
        raise ValueError(f"no such file: {path}")
    if f.stat().st_size > MAX_BYTES:
        raise ValueError("bigger than 5 MB")
    data = f.read_bytes()
    ext = sniff(data)
    if not ext:
        raise ValueError("not a JPEG, PNG or WebP image")
    return data, ext


def fetch_source(source: str) -> tuple[bytes, str]:
    """--add takes either a LinkedIn image link or a path to an image file."""
    return download(source) if source.startswith(("http://", "https://")) else read_local(source)


def missing_photos(people: list[dict], manifest: dict[str, str], check_disk: bool = True,
                   name_key: str = "full_name", photo_dir: Path | None = None) -> list[str]:
    """Listed people whose card would show initials: no saved copy. A dry run writes no files,
    so it goes by the manifest alone (store() still records what it would have saved)."""
    photo_dir = photo_dir or PHOTO_DIR
    out = []
    for m in people:
        name = (m or {}).get(name_key) or ""
        key = slug(name)
        have = manifest.get(key)
        if key and not (have and (not check_disk or (photo_dir / have).is_file())):
            out.append(name)
    return out


def report(missing: list[tuple[str, str]], problems: list[str]) -> None:
    """Make a missing photo impossible to miss: stdout, the run summary, and a step output.
    `missing` is (roster label, name on the card) pairs."""
    why = {line.split(": ", 1)[0]: line.split(": ", 1)[1] for line in problems if ": " in line}
    lines = [f"{n} ({label}) — {why.get(n, 'no LinkedIn photo on file')}" for label, n in missing]
    for line in lines:
        print(f"NEEDS A PHOTO  {line}")
    if lines:
        print('  fix: python3 tools/archive_mentor_photos.py --add "Name" <fresh LinkedIn image link or image file>')
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary and lines:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("### Showing initials instead of a photo\n\n")
            f.write("".join(f"- {line}\n" for line in lines))
            f.write("\nFix: Actions → *Archive mentor photos* → Run workflow with their name (as on the card) and a "
                    "LinkedIn image link — or locally "
                    '`python3 tools/archive_mentor_photos.py --add "Name" <image link or file>`, '
                    "then commit `assets/img/`.\n")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"missing={len(lines)}\n")


def load_manifest(path: Path | None = None) -> dict[str, str]:
    path = path or MANIFEST
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("archive: photos.json was unreadable, starting a fresh one", file=sys.stderr)
        return {}
    return {k: v for k, v in m.items() if isinstance(k, str) and isinstance(v, str) and FILE_RE.match(v)} \
        if isinstance(m, dict) else {}


def save_manifest(m: dict[str, str], path: Path | None = None) -> None:
    path = path or MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(sorted(m.items())), indent=2) + "\n", encoding="utf-8")


def store(manifest: dict[str, str], key: str, data: bytes, ext: str, dry: bool,
          photo_dir: Path | None = None) -> str:
    photo_dir = photo_dir or PHOTO_DIR
    name = f"{key}.{ext}"
    if not dry:
        photo_dir.mkdir(parents=True, exist_ok=True)
        old = manifest.get(key)
        if old and old != name:
            (photo_dir / old).unlink(missing_ok=True)
        (photo_dir / name).write_bytes(data)
    manifest[key] = name
    return name


def sync(people: list[dict], manifest: dict[str, str], dry: bool, fetch=None,
         name_key: str = "full_name", photo_dir: Path | None = None) -> tuple[list[str], list[str], list[str]]:
    """The daily pass for one roster. Returns (saved, removed, problems) as readable lines."""
    fetch = fetch or download                         # looked up per call, so tests can stub it
    photo_dir = photo_dir or PHOTO_DIR
    saved, removed, problems = [], [], []
    listed = {}
    for m in people:
        name = (m or {}).get(name_key) or ""
        key = slug(name)
        if key:
            listed[key] = (name, (m or {}).get("photo_url") or "")

    for key, (name, url) in listed.items():
        have = manifest.get(key)
        if have and (photo_dir / have).is_file():
            continue
        if not url:
            continue                                  # no photo to keep; initials it is
        try:
            data, ext = fetch(url)
        except ValueError as e:
            problems.append(f"{name}: {e}")
            continue
        saved.append(f"{name} -> {store(manifest, key, data, ext, dry, photo_dir)}")

    for key in sorted(set(manifest) - set(listed)):
        removed.append(f"{key} ({manifest[key]})")
        if not dry:
            (photo_dir / manifest[key]).unlink(missing_ok=True)
        del manifest[key]

    return saved, removed, problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    p.add_argument("--add", nargs=2, action="append", metavar=("NAME", "SOURCE"), default=[],
                   help="save a photo for this listed mentor or ambassador (the name on their card) "
                        "from a LinkedIn image link or a local JPEG/PNG/WebP file (repeatable)")
    a = p.parse_args(argv)

    url, key = read_config()
    groups = []                                       # (label, name_key, dir, manifest_path, people, manifest)
    for label, name_key, photo_dir, manifest_path in rosters():
        try:
            people = fetch_roster(label, url, key)
        except Exception as e:                        # noqa: BLE001 — any failure means "stop, change nothing"
            print(f"archive: list_{label}s failed, nothing changed: {e}", file=sys.stderr)
            return 1
        groups.append((label, name_key, photo_dir, manifest_path, people, load_manifest(manifest_path)))

    failed = False
    for name, source in a.add:
        k = slug(name)
        hits = [g for g in groups if any(slug((m or {}).get(g[1]) or "") == k for m in g[4])]
        if len(hits) != 1:
            listed = "; ".join(f"{g[0]}s: " + ", ".join(filter(None, ((m or {}).get(g[1]) for m in g[4])))
                               for g in groups)
            why = "matches more than one card" if hits else "isn't on the site"
            print(f"archive: {name!r} {why} (listed — {listed})", file=sys.stderr)
            failed = True
            continue
        label, name_key, photo_dir, _, people, manifest = hits[0]
        shown = next((m or {}).get(name_key) for m in people if slug((m or {}).get(name_key) or "") == k)
        try:
            data, ext = fetch_source(source)
        except ValueError as e:
            print(f"archive: {name}: {e}", file=sys.stderr)
            failed = True
            continue
        print(f"added    {shown} ({label}) -> {store(manifest, k, data, ext, a.dry_run, photo_dir)}")

    missing, all_problems, changed, total = [], [], False, 0
    for label, name_key, photo_dir, manifest_path, people, manifest in groups:
        saved, removed, problems = sync(people, manifest, a.dry_run, name_key=name_key, photo_dir=photo_dir)
        for line in saved:
            print(f"saved    {line} ({label})")
        for line in removed:
            print(f"removed  {line} ({label}, no longer on the site)")
        for line in problems:
            print(f"skipped  {line} ({label})")
        if not a.dry_run:
            save_manifest(manifest, manifest_path)
        missing += [(label, n) for n in
                    missing_photos(people, manifest, not a.dry_run, name_key=name_key, photo_dir=photo_dir)]
        all_problems += problems
        changed = changed or bool(saved or removed or problems)
        total += len(people)

    report(missing, all_problems)
    if not (a.add or changed or missing):
        print(f"archive: all {total} people on the site have a saved photo")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
