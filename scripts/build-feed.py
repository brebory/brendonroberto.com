"""Rebuild blog/feed.xml (RSS) and sitemap.xml from the post list in blog/index.html.

Run from the repo root after adding or editing a post:

    python scripts/build-feed.py

There is no build step for the site itself; this only regenerates two static files.

Each post in blog/index.html is a <div class="entry"> holding a <dt> with the
post link, a thumbnail <dd>, and a <dd> that starts with <time datetime="...">.
If any entry can't be read, the script names it and exits without writing, so a
post can never silently drop out of the feed.
"""
import html
import os
import re
import sys
from datetime import datetime, timezone

SITE = "https://brendonroberto.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def text_of(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def parse_entries(index):
    """Return [(path, title, date, summary)], or exit naming every entry that doesn't parse."""
    blocks = re.findall(r'<div class="entry">(.*?)</div>', index, flags=re.S)
    if not blocks:
        sys.exit("No <div class=\"entry\"> blocks found in blog/index.html")
    entries, problems = [], []
    for n, block in enumerate(blocks, 1):
        link = re.search(r'<dt>\s*<a\b[^>]*\bhref="(/blog/[^"]+/)"[^>]*>(.*?)</a>\s*</dt>', block, flags=re.S)
        dated = re.search(r'<dd>\s*<time\b[^>]*\bdatetime="(\d{4}-\d{2}-\d{2})"[^>]*>.*?</time>\.?\s*(.*?)</dd>', block, flags=re.S)
        if not link or not dated:
            missing = " and ".join(x for x, ok in (("the <dt> post link", link), ("the <time> summary", dated)) if not ok)
            snippet = " ".join(text_of(block).split())[:70]
            problems.append(f"  entry {n} ({snippet!r}): couldn't find {missing}")
            continue
        entries.append((link.group(1), text_of(link.group(2)), dated.group(1), text_of(dated.group(2))))
    if problems:
        sys.exit("Couldn't read these entries in blog/index.html; nothing was written:\n" + "\n".join(problems))
    return entries


entries = parse_entries(read("blog/index.html"))
paths = [e[0] for e in entries]
if len(set(paths)) != len(paths):
    sys.exit("Duplicate post links in blog/index.html: " + ", ".join(sorted({p for p in paths if paths.count(p) > 1})))

items = []
for path, title, date, summary in entries:
    when = datetime.strptime(date, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
    url = SITE + path
    items.append(
        "    <item>\n"
        f"      <title>{html.escape(title)}</title>\n"
        f"      <link>{url}</link>\n"
        f'      <guid isPermaLink="true">{url}</guid>\n'
        f"      <pubDate>{when.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>\n"
        f"      <description>{html.escape(summary)}</description>\n"
        "    </item>\n"
    )

latest = max(e[2] for e in entries)
build = datetime.strptime(latest, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
feed = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
    "  <channel>\n"
    "    <title>Brendon Roberto</title>\n"
    f"    <link>{SITE}/blog/</link>\n"
    f'    <atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>\n'
    "    <description>Game development deep dives, Fiber dev logs, art and experiments.</description>\n"
    "    <language>en-us</language>\n"
    f"    <lastBuildDate>{build.strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>\n"
    + "".join(items)
    + "  </channel>\n</rss>\n"
)
write("blog/feed.xml", feed)

urls = [(SITE + "/", latest), (SITE + "/blog/", latest)] + [(SITE + p, d) for p, _, d, _ in entries]
sitemap = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    + "</urlset>\n"
)
write("sitemap.xml", sitemap)
print(f"{len(entries)} posts -> blog/feed.xml, sitemap.xml")
