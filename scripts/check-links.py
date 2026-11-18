"""Check that every local link and asset on the site points at a file that exists.

Run from anywhere:

    python scripts/check-links.py

Vite's dev server answers 200 for missing pages (it falls back to index.html),
so an HTTP check isn't enough. This reads the files on disk instead. It also
lists site files that no page references, and pages missing share tags.
Exits with status 1 if any link is broken.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://brendonroberto.com/"
ASSET = re.compile(r"\.(html|css|js|webp|png|jpe?g|gif|mp4|pdf|xml|svg|ico|webmanifest|txt)$|/$")
SKIP_DIRS = {"node_modules", ".git", "scripts", ".vite"}
SKIP_UNUSED = (".html", ".css", ".md", ".json", ".gitignore", ".webmanifest", ".ico", ".txt", ".xml", ".py")

os.chdir(ROOT)
pages = ["index.html", "404.html"] + glob.glob("blog/**/*.html", recursive=True)
missing = 0
text = ""
for page in pages:
    with open(page, encoding="utf-8") as f:
        html = f.read()
    text += html
    base = os.path.dirname(page)
    if "og:image" not in html:
        print(f"NO SHARE TAGS  {page}")
    for url in re.findall(r'(?:href|src|poster|content)="([^"]+)"', html):
        if url.startswith(SITE):
            url = "/" + url[len(SITE):]
        elif re.match(r"(https?:|mailto:|#|data:)", url):
            continue
        url = url.split("#")[0].split("?")[0]
        if not url or not ASSET.search(url):
            continue
        path = url.lstrip("/") if url.startswith("/") else os.path.normpath(os.path.join(base, url))
        if path == "" or os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if not os.path.exists(path):
            print(f"MISSING        {page} -> {url}")
            missing += 1

for css in glob.glob("css/*.css") + ["site.webmanifest", "js/lightbox.js"]:
    with open(css, encoding="utf-8") as f:
        text += f.read()
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for name in files:
        if not name.endswith(SKIP_UNUSED) and name not in text:
            print(f"UNUSED         {os.path.join(root, name)}")

print(f"{len(pages)} pages checked, {missing} missing")
sys.exit(1 if missing else 0)
