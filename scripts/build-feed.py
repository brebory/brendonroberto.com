"""Rebuild blog/feed.xml (RSS) and sitemap.xml from the post list in blog/index.html.

Run from the repo root after adding or editing a post:

    python scripts/build-feed.py

There is no build step for the site itself; this only regenerates two static files.
"""
import html
import os
import re
from datetime import datetime, timezone

SITE = "https://brendonroberto.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


index = read("blog/index.html")
entries = re.findall(
    r'<dt><a href="(/blog/[^"]+/)">(.*?)</a></dt>\s*<dd><time datetime="([\d-]+)">.*?</time>\.\s*(.*?)</dd>',
    index,
    flags=re.S,
)

items = []
for path, title, date, summary in entries:
    when = datetime.strptime(date, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
    title = html.unescape(re.sub(r"<[^>]+>", "", title))
    summary = html.unescape(re.sub(r"<[^>]+>", "", summary)).strip()
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
