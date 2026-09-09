#!/usr/bin/env python3
"""Assemble the Batch Zero static site from partials + page bodies. Run: python3 build.py"""
import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

SITE_URL = "https://batchzero.co"

def head(title, desc, path):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE_URL}{path}">
<meta name="theme-color" content="#07080a">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon-180.png">
<link rel="manifest" href="/site.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Batch Zero">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{SITE_URL}{path}">
<meta property="og:image" content="{SITE_URL}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<div class="grid-bg"></div><div class="noise"></div><div class="spot"></div>
"""

NAV = """<header class="nav">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Batch Zero home"><img src="/assets/img/b0-mark-paper.svg" alt="[B0]" width="84" height="26"><span>BATCH ZERO</span></a>
    <nav class="nav-links" aria-label="Primary">
      <a href="/program/">Program</a>
      <a href="/#how">How it works</a>
      <a href="/#demo-day">Demo Day</a>
      <a href="/apply/mentors/">Mentors</a>
      <a href="/apply/investors/">Investors</a>
      <a href="/apply/companies/">Companies</a>
      <a href="/about/">About</a>
    </nav>
    <div class="nav-cta">
      <a class="btn btn-ghost btn-sm" href="/#doors">Get involved</a>
      <a class="btn btn-primary btn-sm btn-bracket" href="/apply/founders/">Apply as a founder</a>
      <button class="burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<div class="mobile-menu">
  <a href="/program/">Program</a><a href="/#how">How it works</a><a href="/#demo-day">Demo Day</a>
  <a href="/apply/founders/">Apply as a founder</a><a href="/apply/mentors/">Become a mentor</a>
  <a href="/apply/investors/">Investor access</a><a href="/apply/companies/">Hire from the cohort</a><a href="/about/">About</a>
</div>
"""

FOOTER = """<footer>
  <div class="wrap">
    <div class="foot">
      <div>
        <a class="brand" href="/"><img src="/assets/img/b0-mark-paper.svg" alt="[B0]" width="84" height="26"><span>BATCH ZERO</span></a>
        <p style="margin-top:16px;max-width:34ch">The accelerator for founders who haven't graduated yet. Five startups per cohort, eight weeks, one Demo Day.</p>
      </div>
      <div><h4>Program</h4><a href="/program/">How it works</a><a href="/program/#timeline">8-week timeline</a><a href="/#demo-day">Demo Day</a><a href="/#faq">FAQ</a></div>
      <div><h4>Get involved</h4><a href="/apply/founders/">Founders</a><a href="/apply/mentors/">Mentors</a><a href="/apply/investors/">Investors</a><a href="/apply/companies/">Companies</a></div>
      <div><h4>Company</h4><a href="/about/">About</a><a href="mailto:hello@batchzero.co">hello@batchzero.co</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></div>
    </div>
    <div class="foot-bottom">
      <span>© <span data-year></span> Batch Zero. Built by a high-school founder, for high-school founders.</span>
      <span>batchzero.co · cohort_00</span>
    </div>
  </div>
</footer>
<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""

def page(out_path, title, desc, body, canonical):
    html = head(title, desc, canonical) + NAV + body + FOOTER
    full = os.path.join(SITE, out_path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(html)
    print("wrote", out_path)

if __name__ == "__main__":
    import pages
    for p in pages.PAGES:
        page(*p)
    # manifest
    with open(os.path.join(SITE, "site.webmanifest"), "w") as f:
        f.write('''{
  "name": "Batch Zero", "short_name": "Batch Zero",
  "icons": [
    { "src": "/android-chrome-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/android-chrome-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "theme_color": "#07080a", "background_color": "#07080a", "display": "standalone", "start_url": "/"
}''')
    with open(os.path.join(SITE, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    with open(os.path.join(SITE, "sitemap.xml"), "w") as f:
        urls = "".join(f"<url><loc>{SITE_URL}{p[4]}</loc></url>" for p in pages.PAGES if not p[0].startswith("404"))
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
