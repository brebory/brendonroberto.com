"""Check that every local link and asset on the site points at a file that exists.

Run from anywhere:

    python scripts/check-links.py

Vite's dev server answers 200 for missing pages (it falls back to index.html),
so an HTTP check isn't enough. This reads the files on disk instead:

- every href, src, srcset, poster and content URL in the HTML pages
- every url(...) in the stylesheets and in inline <style> blocks
- the icons listed in site.webmanifest

URLs are percent-decoded and resolved to full paths, so files are compared by
path, not just by name. It also lists files nothing references, and pages
missing share tags. Exits with status 1 if any reference is broken.
"""
import glob
import json
import os
import re
import sys
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://brendonroberto.com/"
SKIP_DIRS = {"node_modules", ".git", "scripts", ".vite"}
# Files that are fine to have without an explicit reference.
NEVER_UNUSED = (".html", ".css", ".js", ".md", ".json", ".gitignore", ".webmanifest", ".txt", ".xml", ".py")
IMPLICIT = {"favicon.ico"}

os.chdir(ROOT)
missing = 0
referenced = set()


def resolve(url, base):
    """Turn a URL found in a file under `base` into a repo path, or None if it isn't local."""
    url = url.strip()
    if url.startswith(SITE):
        url = "/" + url[len(SITE):]
    elif re.match(r"(https?:|mailto:|tel:|data:|javascript:|#|//)", url) or not url:
        return None
    url = unquote(url.split("#")[0].split("?")[0])
    if not url:
        return None
    path = url.lstrip("/") if url.startswith("/") else os.path.join(base, url)
    path = os.path.normpath(path)
    if os.path.isdir(path):
        path = os.path.join(path, "index.html")
    return path.replace(os.sep, "/")


def check(url, base, source):
    global missing
    path = resolve(url, base)
    if path is None:
        return
    if path.endswith("/") or (not os.path.splitext(path)[1] and not os.path.exists(path)):
        path = path.rstrip("/") + "/index.html"
    referenced.add(path)
    if not os.path.exists(path):
        print(f"MISSING        {source} -> {url}")
        missing += 1


def css_urls(text):
    return re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", text)


pages = ["index.html", "404.html"] + glob.glob("blog/**/*.html", recursive=True)
for page in pages:
    page = page.replace(os.sep, "/")
    with open(page, encoding="utf-8") as f:
        text = f.read()
    base = os.path.dirname(page)
    if "og:image" not in text:
        print(f"NO SHARE TAGS  {page}")
    for attr, value in re.findall(r'\b(href|src|poster|content|srcset)="([^"]*)"', text):
        if attr == "srcset":
            for candidate in value.split(","):
                if candidate.strip():
                    check(candidate.strip().split()[0], base, page)
        elif attr == "content":
            if value.startswith(SITE) or value.startswith("/"):
                check(value, base, page)
        else:
            check(value, base, page)
    for style in re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S):
        for url in css_urls(style):
            check(url, base, page)

for css in glob.glob("css/*.css"):
    with open(css, encoding="utf-8") as f:
        for url in css_urls(f.read()):
            check(url, os.path.dirname(css), css)

if os.path.exists("site.webmanifest"):
    with open("site.webmanifest", encoding="utf-8") as f:
        for icon in json.load(f).get("icons", []):
            check(icon.get("src", ""), "", "site.webmanifest")

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for name in files:
        path = os.path.normpath(os.path.join(root, name)).replace(os.sep, "/")
        if name.endswith(NEVER_UNUSED) or name in IMPLICIT or path in referenced:
            continue
        print(f"UNUSED         {path}")

print(f"{len(pages)} pages checked, {missing} missing")
sys.exit(1 if missing else 0)
