"""Add share-preview tags and a 1200x630 share image to any page that lacks them.

Run from anywhere after adding a page:

    python scripts/share-tags.py

For each page without an og:title tag it:
- makes img/og/<slug>.jpg by cropping the page's first image or video poster,
  or draws a blue title card if the page has neither
- inserts Open Graph and Twitter tags, a canonical URL and the RSS link after
  the page's <title> (or its meta description, if it has one)

It also makes each post's blog list thumbnail, img/thumbs/<slug>.webp, from its
share image if the thumbnail is missing. Pages that already have tags are
otherwise left alone. To change a share image, replace its file in img/og/ and
delete the matching thumbnail so it's remade. Needs Pillow (pip install pillow).

Pages are edited in LF and written back with their own line endings, so files
checked out with CRLF (core.autocrlf) work too.
"""
import glob
import html
import os
import re

from PIL import Image, ImageDraw, ImageFont

SITE = "https://brendonroberto.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
W, H = 1200, 630
LF, CRLF = "\n", "\r\n"


def font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS, name), size)
    except OSError:
        return ImageFont.load_default(size)


def cover(src, dst):
    im = Image.open(src).convert("RGB")
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    left, top = (im.width - W) // 2, (im.height - H) // 2
    im.crop((left, top, left + W, top + H)).save(dst, quality=85)


def card(title, dst):
    im = Image.new("RGB", (W, H), "#1E81FA")
    d = ImageDraw.Draw(im)
    for x in range(-H, W, 28):
        d.line([(x, 0), (x + H, H)], fill="#2a89fb", width=10)
    d.rectangle((60, 60, W - 60, H - 60), fill="#0054FF")
    big, small = font("georgiab.ttf", 72), font("segoeui.ttf", 34)
    lines, cur = [], ""
    for word in title.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=big) > W - 220:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    y = H / 2 - len(lines) * 45 - 20
    for line in lines:
        d.text((110, y), line, font=big, fill="white")
        y += 90
    d.text((110, H - 140), "brendonroberto.com", font=small, fill="#C2F1FF")
    im.save(dst, quality=88)


def make_thumb(page):
    """Make the blog list thumbnail (img/thumbs/<slug>.webp) from a post's share image."""
    if page.count("/") != 2:
        return
    slug = page.split("/")[1]
    src, dst = f"img/og/{slug}.jpg", f"img/thumbs/{slug}.webp"
    if os.path.exists(src) and not os.path.exists(dst):
        Image.open(src).convert("RGB").resize((480, 252), Image.LANCZOS).save(dst, "WEBP", quality=80)
        print(f"{page} -> {dst}")


def page_info(page):
    """Return (slug, canonical URL, og:type) for a page path like blog/<slug>/index.html."""
    if page == "index.html":
        return "home", f"{SITE}/", "website"
    if page == "blog/index.html":
        return "blog", f"{SITE}/blog/", "website"
    return page.split("/")[1], f"{SITE}/{os.path.dirname(page)}/", "article"


def first_image(page, s):
    m = re.search(r'<main.*?(?:<img[^>]*?\bsrc="([^"]+)"|poster="([^"]+)")', s, flags=re.S)
    if not m:
        return None
    u = m.group(1) or m.group(2)
    src = u.lstrip("/") if u.startswith("/") else os.path.join(os.path.dirname(page), u)
    return src if os.path.exists(src) and not src.endswith(".gif") else None


os.chdir(ROOT)
os.makedirs("img/og", exist_ok=True)
os.makedirs("img/thumbs", exist_ok=True)
for page in ["index.html", "blog/index.html"] + sorted(glob.glob("blog/*/index.html")):
    page = page.replace(os.sep, "/")
    with open(page, encoding="utf-8", newline="") as f:
        raw = f.read()
    eol = CRLF if CRLF in raw else LF
    s = raw.replace(CRLF, LF)
    if "og:title" in s:
        make_thumb(page)
        continue
    tm = re.search(r"([ \t]*)<title>(.*?)</title>\n", s)
    if not tm:
        print(f"SKIPPED {page}: no <title> on a line of its own")
        continue
    clean = html.unescape(tm.group(2)).strip().replace(" · Brendon Roberto", "")
    dm = re.search(r'<meta name="description" content="(.*?)">\n', s)
    desc = html.unescape(dm.group(1)) if dm else clean
    slug, url, kind = page_info(page)
    dst = f"img/og/{slug}.jpg"
    if not os.path.exists(dst):
        src = first_image(page, s)
        if src:
            cover(src, dst)
        else:
            card(clean, dst)
    tags = [] if dm else [f'<meta name="description" content="{html.escape(desc)}">']
    tags += [
        f'<meta property="og:type" content="{kind}">',
        '<meta property="og:site_name" content="Brendon Roberto">',
        f'<meta property="og:title" content="{html.escape(clean)}">',
        f'<meta property="og:description" content="{html.escape(desc)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{SITE}/{dst}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<link rel="canonical" href="{url}">',
        '<link rel="alternate" type="application/rss+xml" title="Brendon Roberto’s blog" href="/blog/feed.xml">',
    ]
    anchor_end = (dm or tm).end()
    s = s[:anchor_end] + "".join(tm.group(1) + t + LF for t in tags) + s[anchor_end:]
    with open(page, "w", encoding="utf-8", newline="") as f:
        f.write(s.replace(LF, eol))
    print(f"{page} -> {dst}")
    make_thumb(page)
