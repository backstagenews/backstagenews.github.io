#!/usr/bin/env python3
"""
Backstage site builder.

Run from this folder:   python3 rebuild.py

It regenerates every page from _data/articles.json in the "Editorial" style.

ADDING A PHOTO TO A STORY
-------------------------
Drop an image into  photos/<article-slug>.jpg   (or .png / .jpeg / .webp)
where <article-slug> is the article's filename without ".html"
e.g.  photos/davido-trump-osun-election.jpg
Then run  python3 rebuild.py  again. That story now uses your photo
everywhere (hero, homepage card, related, search); stories with no photo
fall back to the category image automatically.

Optional caption: add  "<slug>": "Your caption"  to _data/captions.json
"""
import json, os, re, html as ih

HERE = os.path.dirname(os.path.abspath(__file__))
arts = json.load(open(os.path.join(HERE, "_data", "articles.json"), encoding="utf-8"))
try:
    CAPS = json.load(open(os.path.join(HERE, "_data", "captions.json"), encoding="utf-8"))
except Exception:
    CAPS = {}

# ---- Merge hand-written stories from _data/new/*.json ----
# Each file is one article, e.g. _data/new/tinubu-budget-2027.json :
#   {"slug":"tinubu-budget-2027","title":"...","cat":"news",
#    "byline":"By Staff Reporter","date":"August 28, 2026",
#    "excerpt":"one sentence","paras":["para 1","para 2"]}
import datetime as _dt
_newdir = os.path.join(HERE, "_data", "new")
if os.path.isdir(_newdir):
    for _f in sorted(os.listdir(_newdir)):
        if not _f.endswith(".json") or _f.startswith("_"):
            continue
        _n = json.load(open(os.path.join(_newdir, _f), encoding="utf-8"))
        _slug = _n.get("slug") or _f[:-5]
        _cat = _n.get("cat", "news").lower()
        if _cat not in ("news", "entertainment", "sports", "business"):
            _cat = "news"
        _date = _n.get("date", "").strip()
        try:
            _iso = _dt.datetime.strptime(_date, "%B %d, %Y").isoformat()
        except Exception:
            _iso = _dt.datetime.now().replace(microsecond=0).isoformat()
            _date = _dt.datetime.now().strftime("%B %-d, %Y")
        _byline = _n.get("byline", "By Staff Reporter")
        arts[_slug + ".html"] = {
            "title": _n["title"], "cat": _cat,
            "meta": "%s &middot; %s" % (_byline, _date) if _date else _byline,
            "excerpt": _n.get("excerpt", ""),
            "caption": _n.get("caption", ""),
            "paras": _n.get("paras", []),
            "date_iso": _iso, "date_str": _date,
        }
        print("  + new story:", _slug)

# Normalise any HTML entities that were captured verbatim from the source
# repo (e.g. &quot; &#x27; &amp;) so esc() below escapes exactly once.
for _a in arts.values():
    for _k in ("title", "excerpt", "meta", "caption", "date_str"):
        if isinstance(_a.get(_k), str):
            _a[_k] = ih.unescape(_a[_k])
    if isinstance(_a.get("paras"), list):
        _a["paras"] = [ih.unescape(p) for p in _a["paras"]]
CAPS = {k: ih.unescape(v) for k, v in CAPS.items()}

EMAIL = "backstagenewsng@gmail.com"
CANON = "https://backstagenews.github.io/"
COLOR = {"news": "#7D1226", "entertainment": "#C9962E", "sports": "#1C2740", "business": "#7D1226"}
SECT  = {"news": "news.html", "entertainment": "entertainment.html", "sports": "sports.html", "business": "business.html"}
PER_PAGE = 14
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".avif")


def esc(s):
    return ih.escape(s or "", quote=True)


def find_photo(slug):
    for e in EXTS:
        if os.path.exists(os.path.join(HERE, "photos", slug + e)):
            return "photos/" + slug + e
    return None


PHOTOS = {slug[:-5]: find_photo(slug[:-5]) for slug in arts}
PHOTOS = {k: v for k, v in PHOTOS.items() if v}


def cover(slug):
    """Designed SVG cover for a story that has no real photo."""
    if os.path.exists(os.path.join(HERE, "covers", slug + ".svg")):
        return "covers/" + slug + ".svg"
    return None


def art_image(slug, cat):
    """Best available image for a story: real photo > designed cover > category art."""
    return PHOTOS.get(slug) or cover(slug) or ("category-%s.png" % cat)


def hero(slug, cat):
    """Return (img_tag, caption_html) for the big lead image."""
    src = art_image(slug, cat)
    fallback = "category-%s.png" % cat
    cap_html = ""
    if PHOTOS.get(slug):
        cap = CAPS.get(slug, "")
        if cap:
            cap_html = '<span class="article-caption">%s</span>' % esc(cap)
    return ('<img src="%s" alt="%s" onerror="this.onerror=null;this.src=\'%s\'" />'
            % (src, esc(arts[slug + ".html"]["title"]), fallback), cap_html)


def thumb(slug, cat):
    return art_image(slug, cat)


order = sorted(arts.items(), key=lambda kv: kv[1]["date_iso"], reverse=True)
by_cat = {c: [(f, a) for f, a in order if a["cat"] == c] for c in COLOR}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
 '\t\t<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Open+Sans:400,600,400italic,600italic|Roboto+Slab:400,700" />\n'
 '\t\t<link rel="stylesheet" href="assets/css/fontawesome-all.min.css" />\n'
 '\t\t<link rel="stylesheet" href="assets/css/main.css" />\n'
 '\t\t<link rel="stylesheet" href="assets/css/backstage.css" />')
SCRIPTS = ('<script src="assets/js/jquery.min.js"></script>\n'
 '\t\t\t<script src="assets/js/browser.min.js"></script>\n'
 '\t\t\t<script src="assets/js/breakpoints.min.js"></script>\n'
 '\t\t\t<script src="assets/js/util.js"></script>\n'
 '\t\t\t<script src="assets/js/main.js"></script>\n'
 '\t\t\t<script src="assets/js/backstage.js"></script>')

EDITION = '''\t\t\t\t\t<div class="edition-bar"><div class="inner">
\t\t\t\t\t\t<span class="live">Live &middot; <span id="today">Today's edition</span></span>
\t\t\t\t\t\t<button class="theme-toggle" type="button" aria-label="Toggle dark mode">&#9790;</button>
\t\t\t\t\t</div></div>'''

HEADER = '''\t\t\t\t\t<header id="header">
\t\t\t\t\t\t<a href="index.html" class="logo"><strong>Backstage</strong> &mdash; what's running, right now</a>
\t\t\t\t\t\t<ul class="icons">
\t\t\t\t\t\t\t<li><a href="https://facebook.com/backstagenewsng" class="icon brands fa-facebook-f"><span class="label">Facebook</span></a></li>
\t\t\t\t\t\t\t<li><a href="https://twitter.com/backstagenewsng" class="icon brands fa-x-twitter"><span class="label">X</span></a></li>
\t\t\t\t\t\t\t<li><a href="https://instagram.com/backstagenewsng" class="icon brands fa-instagram"><span class="label">Instagram</span></a></li>
\t\t\t\t\t\t\t<li><a href="mailto:%s" class="icon solid fa-envelope"><span class="label">Email</span></a></li>
\t\t\t\t\t\t</ul>
\t\t\t\t\t</header>''' % EMAIL

SECTION_NAV = ('\t\t\t\t\t<nav class="section-nav">\n'
 '\t\t\t\t\t\t<a href="index.html">All</a>\n'
 '\t\t\t\t\t\t<a href="news.html">News</a>\n'
 '\t\t\t\t\t\t<a href="entertainment.html">Entertainment</a>\n'
 '\t\t\t\t\t\t<a href="sports.html">Sports</a>\n'
 '\t\t\t\t\t\t<a href="business.html">Business</a>\n'
 '\t\t\t\t\t\t<a href="quiz.html">Daily Quiz</a>\n'
 '\t\t\t\t\t</nav>')

FOOTER = '''\t\t\t\t\t<footer id="footer">
\t\t\t\t\t\t<section class="newsletter">
\t\t\t\t\t\t\t<h3>Get the Backstage brief</h3>
\t\t\t\t\t\t\t<form method="post" action="mailto:%s?subject=Newsletter%%20signup">
\t\t\t\t\t\t\t\t<input type="email" name="email" placeholder="you@example.com" required />
\t\t\t\t\t\t\t\t<input type="submit" value="Subscribe" class="primary" />
\t\t\t\t\t\t\t</form>
\t\t\t\t\t\t\t<p class="note">A short daily email of what's running. No spam &mdash; unsubscribe any time.</p>
\t\t\t\t\t\t</section>
\t\t\t\t\t\t<hr />
\t\t\t\t\t\t<div class="row">
\t\t\t\t\t\t\t<div class="col-6 col-12-small">
\t\t\t\t\t\t\t\t<h3>Sections</h3>
\t\t\t\t\t\t\t\t<ul class="alt">
\t\t\t\t\t\t\t\t\t<li><a href="news.html">News</a></li>
\t\t\t\t\t\t\t\t\t<li><a href="entertainment.html">Entertainment</a></li>
\t\t\t\t\t\t\t\t\t<li><a href="sports.html">Sports</a></li>
\t\t\t\t\t\t\t\t\t<li><a href="business.html">Business</a></li>
\t\t\t\t\t\t\t\t\t<li><a href="quiz.html">Daily Quiz</a></li>
\t\t\t\t\t\t\t\t</ul>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="col-6 col-12-small">
\t\t\t\t\t\t\t\t<h3>Backstage</h3>
\t\t\t\t\t\t\t\t<ul class="alt">
\t\t\t\t\t\t\t\t\t<li><a href="about.html">About</a></li>
\t\t\t\t\t\t\t\t\t<li><a href="contact.html">Contact &amp; tips</a></li>
\t\t\t\t\t\t\t\t\t<li><a href="privacy.html">Privacy Policy</a></li>
\t\t\t\t\t\t\t\t\t<li><a href="terms.html">Terms of Service</a></li>
\t\t\t\t\t\t\t\t</ul>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<ul class="icons">
\t\t\t\t\t\t\t<li><a href="https://facebook.com/backstagenewsng" class="icon brands fa-facebook-f"><span class="label">Facebook</span></a></li>
\t\t\t\t\t\t\t<li><a href="https://twitter.com/backstagenewsng" class="icon brands fa-x-twitter"><span class="label">X</span></a></li>
\t\t\t\t\t\t\t<li><a href="https://instagram.com/backstagenewsng" class="icon brands fa-instagram"><span class="label">Instagram</span></a></li>
\t\t\t\t\t\t\t<li><a href="mailto:%s" class="icon solid fa-envelope"><span class="label">Email</span></a></li>
\t\t\t\t\t\t</ul>
\t\t\t\t\t\t<p class="copyright">&copy; <span data-year>2026</span> Backstage &middot; <a href="mailto:%s">%s</a><br />
\t\t\t\t\t\tWhat's running, right now &middot; est. 2026 &middot; Design: <a href="https://html5up.net">HTML5 UP</a>.</p>
\t\t\t\t\t</footer>''' % (EMAIL, EMAIL, EMAIL, EMAIL)

top12 = [k for k, _ in order[:12]]
HL = "\n".join('\t\t\t\t\t\t\t<li><a href="%s">%s</a></li>' % (h, esc(arts[h]["title"])) for h in top12)
trending = order[1:6]
MINI = "\n".join('''\t\t\t\t\t\t\t<article>
\t\t\t\t\t\t\t\t<a href="%s" class="image"><img src="%s" alt="Backstage %s" /></a>
\t\t\t\t\t\t\t\t<p><a href="%s">%s</a><br /><span class="mini-meta">%s &middot; %s</span></p>
\t\t\t\t\t\t\t</article>''' % (fn, thumb(fn[:-5], a["cat"]), a["cat"], fn, esc(a["title"]), a["cat"], esc(a["date_str"]))
    for fn, a in trending)


def sidebar(newsletter=True):
    nl = ''
    if newsletter:
        nl = '''\t\t\t\t\t<section class="newsletter">
\t\t\t\t\t\t<header class="major"><h2>Newsletter</h2></header>
\t\t\t\t\t\t<form method="post" action="mailto:%s?subject=Newsletter%%20signup">
\t\t\t\t\t\t\t<input type="email" name="email" placeholder="you@example.com" required />
\t\t\t\t\t\t\t<input type="submit" value="Join" class="primary" />
\t\t\t\t\t\t</form>
\t\t\t\t\t\t<p class="note">What's running, right now &mdash; in your inbox.</p>
\t\t\t\t\t</section>
''' % EMAIL
    return '''\t\t\t<div id="sidebar">
\t\t\t\t<div class="inner">
\t\t\t\t\t<section id="search" class="alt">
\t\t\t\t\t\t<form method="get" action="search.html"><input type="text" name="q" id="query" placeholder="Search headlines&hellip;" /></form>
\t\t\t\t\t</section>
\t\t\t\t\t<nav id="menu">
\t\t\t\t\t\t<header class="major"><h2>Menu</h2></header>
\t\t\t\t\t\t<ul>
\t\t\t\t\t\t\t<li><a href="index.html">Homepage</a></li>
\t\t\t\t\t\t\t<li><a href="news.html">News</a></li>
\t\t\t\t\t\t\t<li><a href="entertainment.html">Entertainment</a></li>
\t\t\t\t\t\t\t<li><a href="sports.html">Sports</a></li>
\t\t\t\t\t\t\t<li><a href="business.html">Business</a></li>
\t\t\t\t\t\t\t<li><a href="quiz.html">Daily Quiz</a></li>
\t\t\t\t\t\t\t<li><span class="opener">More</span><ul>
\t\t\t\t\t\t\t\t<li><a href="about.html">About</a></li>
\t\t\t\t\t\t\t\t<li><a href="contact.html">Contact</a></li>
\t\t\t\t\t\t\t\t<li><a href="search.html">Search</a></li>
\t\t\t\t\t\t\t\t<li><a href="privacy.html">Privacy</a></li>
\t\t\t\t\t\t\t\t<li><a href="terms.html">Terms</a></li>
\t\t\t\t\t\t\t</ul></li>
\t\t\t\t\t\t</ul>
\t\t\t\t\t</nav>
''' + nl + '''\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="major"><h2>Trending</h2></header>
\t\t\t\t\t\t<div class="mini-posts">
''' + MINI + '''
\t\t\t\t\t\t</div>
\t\t\t\t\t</section>
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="major"><h2>Latest headlines</h2></header>
\t\t\t\t\t\t<ul class="alt">
''' + HL + '''
\t\t\t\t\t\t</ul>
\t\t\t\t\t\t<ul class="actions"><li><a href="news.html" class="button">All headlines</a></li></ul>
\t\t\t\t\t</section>
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="major"><h2>Get in touch</h2></header>
\t\t\t\t\t\t<p>Story tip or correction? Reach the Backstage desk.</p>
\t\t\t\t\t\t<ul class="contact">
\t\t\t\t\t\t\t<li class="icon solid fa-envelope"><a href="mailto:''' + EMAIL + '''">''' + EMAIL + '''</a></li>
\t\t\t\t\t\t\t<li class="icon solid fa-pen-nib"><a href="contact.html">Submit a tip</a></li>
\t\t\t\t\t\t</ul>
\t\t\t\t\t</section>
''' + FOOTER + '''
\t\t\t\t</div>
\t\t\t</div>'''


SIDEBAR = sidebar(True)
SIDEBAR_NONL = sidebar(False)


def shell(title, desc, inner, sidebar_html=SIDEBAR, canon=None, og_type="website", og_image=None, head_extra=""):
    canon_tag = ('\t\t<link rel="canonical" href="%s" />\n' % canon) if canon else ""
    ogimg = ('\t\t<meta property="og:image" content="%s%s" />\n' % (CANON, og_image)) if og_image else ""
    head_extra = ('\t\t<link rel="alternate" type="application/rss+xml" title="Backstage" href="feed.xml" />\n' + head_extra)
    return '''<!DOCTYPE HTML>
<!-- Backstage — styled with "Editorial" by HTML5 UP (html5up.net) -->
<html lang="en">
\t<head>
\t\t<title>%s</title>
\t\t<meta charset="utf-8" />
\t\t<meta name="viewport" content="width=device-width, initial-scale=1" />
\t\t<meta name="description" content="%s" />
\t\t<meta property="og:title" content="%s" />
\t\t<meta property="og:description" content="%s" />
\t\t<meta property="og:type" content="%s" />
\t\t<meta property="og:site_name" content="Backstage" />
%s%s\t\t%s
\t\t<link rel="manifest" href="manifest.json" />
\t\t<meta name="theme-color" content="#7D1226" />
\t\t<link rel="apple-touch-icon" href="icons/icon-180.png" />
\t\t<link rel="icon" href="icons/icon-32.png" sizes="32x32" />
%s\t</head>
\t<body class="is-preload">
\t\t<div id="wrapper">
\t\t\t<div id="main">
\t\t\t\t<div class="inner">
%s
%s
%s
\t\t\t\t</div>
\t\t\t</div>
%s
\t\t</div>
\t\t<button id="backtotop" type="button" aria-label="Back to top">&#8593;</button>
\t\t%s
\t</body>
</html>
''' % (esc(title), esc(desc), esc(title), esc(desc), og_type, canon_tag, ogimg, FONTS,
       head_extra, EDITION, HEADER, inner, sidebar_html, SCRIPTS)


def card(fn, a):
    slug = fn[:-5]
    blurb = a["excerpt"] or (a["paras"][0][:180] if a["paras"] else "")
    return '''\t\t\t\t\t\t\t<article>
\t\t\t\t\t\t\t\t<a href="%s" class="image fit"><img src="%s" alt="Backstage %s" onerror="this.onerror=null;this.src='category-%s.png'" /></a>
\t\t\t\t\t\t\t\t<p class="cat-tag" style="background:%s">%s</p>
\t\t\t\t\t\t\t\t<h3><a href="%s">%s</a></h3>
\t\t\t\t\t\t\t\t<p>%s</p>
\t\t\t\t\t\t\t\t<p class="byline">%s</p>
\t\t\t\t\t\t\t\t<ul class="actions"><li><a href="%s" class="button">Read more</a></li></ul>
\t\t\t\t\t\t\t</article>''' % (fn, thumb(slug, a["cat"]), a["cat"], a["cat"], COLOR[a["cat"]], a["cat"], fn,
       esc(a["title"]), esc(blurb), esc(a["meta"]), fn)


def pager(cur, npages, name):
    def pf(n):
        if n == 1:
            return name
        return "%s-%d.html" % (name[:-5], n)
    li = ['<li><a href="%s" class="button small">&larr; Newer</a></li>' % pf(cur - 1) if cur > 1
          else '<li><span class="button small disabled">&larr; Newer</span></li>']
    for n in range(1, npages + 1):
        li.append('<li><a href="%s" class="%s">%d</a></li>' % (pf(n), "page active" if n == cur else "page", n))
    li.append('<li><a href="%s" class="button small">Older &rarr;</a></li>' % pf(cur + 1) if cur < npages
              else '<li><span class="button small disabled">Older &rarr;</span></li>')
    return '<ul class="pagination">\n\t\t\t\t\t\t\t' + "\n\t\t\t\t\t\t\t".join(li) + '\n\t\t\t\t\t\t</ul>'


def reading_time(a):
    w = sum(len(p.split()) for p in a["paras"])
    return max(1, round(w / 220))


# ============================ ARTICLE PAGES ============================
n_photo = 0
for fn, a in arts.items():
    slug = fn[:-5]
    rt = reading_time(a)
    cat = a["cat"]
    img_tag, cap = hero(slug, cat)
    if PHOTOS.get(slug):
        n_photo += 1
    lead = '\t\t\t\t\t\t<p class="lead">%s</p>\n\t\t\t\t\t\t<hr />' % esc(a["excerpt"]) if a["excerpt"] else ""
    body = "\n".join('\t\t\t\t\t\t<p>%s</p>' % esc(p) for p in a["paras"])
    url = CANON + fn
    share = '''\t\t\t\t\t\t<div class="share-row">
\t\t\t\t\t\t\t<span class="label">Share</span>
\t\t\t\t\t\t\t<a href="https://twitter.com/intent/tweet?url=%s&text=%s" class="icon brands fa-x-twitter" target="_blank" rel="noopener"><span class="label">X</span></a>
\t\t\t\t\t\t\t<a href="https://www.facebook.com/sharer/sharer.php?u=%s" class="icon brands fa-facebook-f" target="_blank" rel="noopener"><span class="label">Facebook</span></a>
\t\t\t\t\t\t\t<a href="https://api.whatsapp.com/send?text=%s%%20%s" class="icon brands fa-whatsapp" target="_blank" rel="noopener"><span class="label">WhatsApp</span></a>
\t\t\t\t\t\t\t<button type="button" class="copy icon solid fa-link" data-url="%s"><span class="label">Copy link</span></button>
\t\t\t\t\t\t</div>''' % (url, ih.escape(a["title"]), url, ih.escape(a["title"]), url, url)
    rel = [x for x in by_cat[cat] if x[0] != fn][:3]
    rel_html = ""
    if rel:
        cs = "\n".join('''\t\t\t\t\t\t\t<article>
\t\t\t\t\t\t\t\t<a href="%s" class="thumb"><img src="%s" alt="Backstage %s" onerror="this.onerror=null;this.src='category-%s.png'" /></a>
\t\t\t\t\t\t\t\t<div class="body"><h3><a href="%s">%s</a></h3></div>
\t\t\t\t\t\t\t</article>''' % (rf, thumb(rf[:-5], ra["cat"]), ra["cat"], ra["cat"], rf, esc(ra["title"]))
            for rf, ra in rel)
        rel_html = '''\t\t\t\t\t<section class="related">
\t\t\t\t\t\t<header class="major"><h2>More %s</h2></header>
\t\t\t\t\t\t<div class="related-list">
%s
\t\t\t\t\t\t</div>
\t\t\t\t\t</section>''' % (cat, cs)
    inner = '''
\t\t\t\t\t<section>
\t\t\t\t\t\t<p><a href="index.html">&larr; All stories</a></p>
\t\t\t\t\t\t<header class="main"><h1>%s</h1></header>
\t\t\t\t\t\t<p class="cat-tag" style="background:%s">%s</p>
\t\t\t\t\t\t<p class="byline">%s <span class="dot">&middot;</span> %d min read</p>
\t\t\t\t\t\t<span class="image main">%s%s</span>
%s
%s
%s
\t\t\t\t\t\t<ul class="actions">
\t\t\t\t\t\t\t<li><a href="index.html" class="button">Homepage</a></li>
\t\t\t\t\t\t\t<li><a href="%s" class="button">More %s</a></li>
\t\t\t\t\t\t</ul>
\t\t\t\t\t</section>
%s''' % (esc(a["title"]), COLOR[cat], cat, esc(a["meta"]), rt, img_tag, cap,
         lead, body, share, SECT[cat], cat, rel_html)
    desc = (a["excerpt"] or a["title"])[:180]
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": a["title"], "datePublished": a["date_iso"],
        "articleSection": cat.capitalize(),
        "author": {"@type": "Organization", "name": "Backstage"},
        "publisher": {"@type": "Organization", "name": "Backstage"},
        "mainEntityOfPage": url,
        "image": CANON + art_image(slug, cat),
        "description": desc,
    }, ensure_ascii=False)
    jsonld = '\t\t<script type="application/ld+json">%s</script>\n' % ld
    open(os.path.join(HERE, fn), "w", encoding="utf-8").write(
        shell(a["title"] + " — Backstage", desc, inner, canon=url, og_type="article",
              og_image=art_image(slug, cat), head_extra=jsonld))

# ============================ HOME + LATEST ============================
allpages = [order[i:i + PER_PAGE] for i in range(0, len(order), PER_PAGE)]
NP = len(allpages)
lead_fn, lead_a = order[0]
ticker = "".join('<span><a href="%s">%s</a></span>' % (fn, esc(a["title"])) for fn, a in order)


def latest_name(n):
    return "index.html" if n == 1 else "latest-%d.html" % n


def latest_pager(cur):
    li = ['<li><a href="%s" class="button small">&larr; Newer</a></li>' % latest_name(cur - 1) if cur > 1
          else '<li><span class="button small disabled">&larr; Newer</span></li>']
    for n in range(1, NP + 1):
        li.append('<li><a href="%s" class="%s">%d</a></li>' % (latest_name(n), "page active" if n == cur else "page", n))
    li.append('<li><a href="%s" class="button small">Older &rarr;</a></li>' % latest_name(cur + 1) if cur < NP
              else '<li><span class="button small disabled">Older &rarr;</span></li>')
    return '<ul class="pagination">\n\t\t\t\t\t\t\t' + "\n\t\t\t\t\t\t\t".join(li) + '\n\t\t\t\t\t\t</ul>'


lead_img, lead_cap = hero(lead_fn[:-5], lead_a["cat"])
p1 = "\n".join(card(fn, a) for fn, a in allpages[0])
inner1 = '''
\t\t\t\t\t<div class="ticker">
\t\t\t\t\t\t<div class="ticker-label">Headlines</div>
\t\t\t\t\t\t<div class="ticker-viewport"><div class="ticker-track">%s%s</div></div>
\t\t\t\t\t</div>
%s
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="main"><h1>Spotlight</h1></header>
\t\t\t\t\t\t<a href="%s" class="image main">%s</a>%s
\t\t\t\t\t\t<p class="cat-tag" style="background:%s">%s</p>
\t\t\t\t\t\t<h2><a href="%s">%s</a></h2>
\t\t\t\t\t\t<p class="spotlight-excerpt">%s</p>
\t\t\t\t\t\t<p class="byline">%s</p>
\t\t\t\t\t</section>
\t\t\t\t\t<hr class="major" />
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="major"><h2>Latest <span style="font-weight:400;color:#9fa3a6;font-size:.5em;letter-spacing:.1em;">PAGE 1 OF %d</span></h2></header>
\t\t\t\t\t\t<div class="posts">
%s
\t\t\t\t\t\t</div>
\t\t\t\t\t\t%s
\t\t\t\t\t</section>''' % (ticker, ticker, SECTION_NAV, lead_fn, lead_img, (" " + lead_cap if lead_cap else ""),
     COLOR[lead_a["cat"]], lead_a["cat"], lead_fn, esc(lead_a["title"]),
     esc(lead_a["excerpt"]), esc(lead_a["meta"]), NP, p1, latest_pager(1))
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(
    shell("Backstage — what's running, right now",
          "The latest Nigerian news, entertainment, sports and business.", inner1, canon=CANON))
open(os.path.join(HERE, "backstage-editorial.html"), "w", encoding="utf-8").write(
    open(os.path.join(HERE, "index.html"), encoding="utf-8").read())

for n in range(2, NP + 1):
    cards = "\n".join(card(fn, a) for fn, a in allpages[n - 1])
    inner = '''
%s
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="main"><h1>Latest &mdash; page %d of %d</h1></header>
\t\t\t\t\t\t<div class="posts">
%s
\t\t\t\t\t\t</div>
\t\t\t\t\t\t%s
\t\t\t\t\t</section>''' % (SECTION_NAV, n, NP, cards, latest_pager(n))
    open(os.path.join(HERE, "latest-%d.html" % n), "w", encoding="utf-8").write(
        shell("Latest, page %d — Backstage" % n, "Backstage latest stories, page %d." % n, inner,
              canon=CANON + "latest-%d.html" % n))

# ============================ SECTION PAGES ============================
LABEL = {"news": "News", "entertainment": "Entertainment", "sports": "Sports", "business": "Business"}
section_files = []
for c, items in by_cat.items():
    pages = [items[i:i + PER_PAGE] for i in range(0, len(items), PER_PAGE)] or [[]]
    npc = len(pages)
    for n in range(1, npc + 1):
        name = "%s.html" % c if n == 1 else "%s-%d.html" % (c, n)
        section_files.append(name)
        cards = "\n".join(card(fn, a) for fn, a in pages[n - 1])
        head = '''\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="main"><h1>%s</h1></header>
\t\t\t\t\t\t<p class="byline">%d stories%s</p>
\t\t\t\t\t\t<div class="posts">
%s
\t\t\t\t\t\t</div>
\t\t\t\t\t\t%s
\t\t\t\t\t</section>''' % (LABEL[c], len(items),
            (" &middot; page %d of %d" % (n, npc)) if npc > 1 else "", cards, pager(n, npc, "%s.html" % c))
        inner = "\n" + SECTION_NAV + "\n" + head
        open(os.path.join(HERE, name), "w", encoding="utf-8").write(
            shell("%s — Backstage" % LABEL[c], "The latest %s stories from Backstage." % LABEL[c].lower(),
                  inner, canon=CANON + name))

# ============================ SEARCH ============================
search_data = [{"t": a["title"], "f": fn, "c": a["cat"],
                "i": thumb(fn[:-5], a["cat"]),
                "e": a["excerpt"] or (a["paras"][0][:160] if a["paras"] else "")}
               for fn, a in order]
search_json = json.dumps(search_data, ensure_ascii=False)
search_inner = '''
%s
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="main"><h1>Search</h1></header>
\t\t\t\t\t\t<form method="get" action="search.html" style="margin-bottom:1.5em;">
\t\t\t\t\t\t\t<input type="text" name="q" id="q" placeholder="Search %d headlines&hellip;" />
\t\t\t\t\t\t</form>
\t\t\t\t\t\t<p class="byline" id="count"></p>
\t\t\t\t\t\t<div class="search-results-list" id="results"></div>
\t\t\t\t\t</section>
\t\t\t\t\t<script>
\t\t\t\t\tvar DATA = %s;
\t\t\t\t\tvar COLORS = {"news":"#7D1226","entertainment":"#C9962E","sports":"#1C2740","business":"#7D1226"};
\t\t\t\t\tfunction esc(s){var d=document.createElement("div");d.textContent=s;return d.innerHTML;}
\t\t\t\t\tfunction run(){
\t\t\t\t\t\tvar q=(new URLSearchParams(location.search).get("q")||"").trim().toLowerCase();
\t\t\t\t\t\tvar input=document.getElementById("q"); if(q) input.value=q;
\t\t\t\t\t\tvar out=document.getElementById("results"), cnt=document.getElementById("count");
\t\t\t\t\t\tif(!q){ cnt.textContent="Type a word and press Enter."; out.innerHTML=""; return; }
\t\t\t\t\t\tvar m=DATA.filter(function(a){return (a.t+" "+a.e).toLowerCase().indexOf(q)>-1;});
\t\t\t\t\t\tcnt.textContent=m.length+' result'+(m.length===1?'':'s')+' for \\u201c'+q+'\\u201d';
\t\t\t\t\t\tif(!m.length){ out.innerHTML='<p class="search-empty">No stories match that search.</p>'; return; }
\t\t\t\t\t\tout.innerHTML=m.map(function(a){return '<article><a href="'+a.f+'" class="thumb"><img src="'+a.i+'" alt="" onerror="this.onerror=null;this.src=\\'category-'+a.c+'.png\\'"></a>'+
\t\t\t\t\t\t\t'<div class="body"><p class="cat-tag" style="background:'+(COLORS[a.c]||"#7D1226")+'">'+esc(a.c)+'</p>'+
\t\t\t\t\t\t\t'<h3><a href="'+a.f+'">'+esc(a.t)+'</a></h3><p>'+esc(a.e)+'</p></div></article>';}).join("");
\t\t\t\t\t}
\t\t\t\t\trun();
\t\t\t\t\t</script>''' % (SECTION_NAV, len(search_data), search_json)
open(os.path.join(HERE, "search.html"), "w", encoding="utf-8").write(
    shell("Search — Backstage", "Search Backstage headlines.", search_inner,
          sidebar_html=SIDEBAR_NONL, canon=CANON + "search.html"))

# ============================ QUIZ ============================
QUIZ = [
 {"q": "What record does Davido hold on TurnTable Charts?", "options": ["Most streamed Nigerian song ever", "A No.1 single every year since chart tracking began", "First Nigerian Grammy win", "Longest-running No.1 single"], "correct": 1},
 {"q": "Which club scored a stunning second-half comeback against Manchester United in pre-season?", "options": ["Juventus", "AC Milan", "Inter Milan", "Napoli"], "correct": 1},
 {"q": "Which team eliminated Nigeria's Super Falcons from 2027 World Cup qualification?", "options": ["Cameroon", "Morocco", "South Africa", "Ghana"], "correct": 2},
 {"q": "What bill did President Tinubu sign to create a dedicated ports regulator?", "options": ["NIMASA Reform Act", "NPERA Bill", "Ports Authority Act", "Maritime Trade Bill"], "correct": 1},
 {"q": "Who did INEC declare winner of the Osun governorship election?", "options": ["Bola Oyebamiji", "Ademola Adeleke", "Najeem Salaam", "Gboyega Oyetola"], "correct": 1},
]
quiz_inner = '''
%s
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="main"><h1>Backstage Daily Quiz</h1></header>
\t\t\t\t\t\t<p class="byline">5 questions &middot; based on real Backstage stories</p>
\t\t\t\t\t\t<div class="quiz-card"><div id="quiz-body"></div></div>
\t\t\t\t\t</section>
\t\t\t\t\t<script>
\t\t\t\t\tvar Q=%s, cur=0, score=0, answered=false;
\t\t\t\t\tfunction render(){
\t\t\t\t\t\tvar b=document.getElementById("quiz-body");
\t\t\t\t\t\tif(cur>=Q.length){return result();}
\t\t\t\t\t\tanswered=false; var it=Q[cur];
\t\t\t\t\t\tb.innerHTML='<div class="quiz-progress">Question '+(cur+1)+' of '+Q.length+' &middot; Score '+score+'</div>'+
\t\t\t\t\t\t\t'<div class="quiz-question">'+it.q+'</div><div class="quiz-options">'+
\t\t\t\t\t\t\tit.options.map(function(o,i){return '<button class="quiz-option" data-i="'+i+'">'+o+'</button>';}).join("")+'</div>';
\t\t\t\t\t\tArray.prototype.forEach.call(document.querySelectorAll(".quiz-option"),function(btn){
\t\t\t\t\t\t\tbtn.addEventListener("click",function(){
\t\t\t\t\t\t\t\tif(answered)return; answered=true;
\t\t\t\t\t\t\t\tvar chosen=+btn.getAttribute("data-i");
\t\t\t\t\t\t\t\tvar all=document.querySelectorAll(".quiz-option");
\t\t\t\t\t\t\t\tall.forEach(function(x){x.disabled=true;});
\t\t\t\t\t\t\t\tif(chosen===it.correct){btn.classList.add("correct");score++;}
\t\t\t\t\t\t\t\telse{btn.classList.add("wrong");all[it.correct].classList.add("correct");}
\t\t\t\t\t\t\t\tvar n=document.createElement("button"); n.className="quiz-next-btn";
\t\t\t\t\t\t\t\tn.textContent=(cur+1<Q.length)?"Next question":"See results";
\t\t\t\t\t\t\t\tn.addEventListener("click",function(){cur++;render();});
\t\t\t\t\t\t\t\tdocument.getElementById("quiz-body").appendChild(n);
\t\t\t\t\t\t\t});
\t\t\t\t\t\t});
\t\t\t\t\t}
\t\t\t\t\tfunction result(){
\t\t\t\t\t\tvar msg = score===Q.length?"Perfect score. You really read the news.":
\t\t\t\t\t\t\tscore>=Q.length-1?"So close to perfect.":
\t\t\t\t\t\t\tscore>=Q.length/2?"Solid. Catch up on today's stories for full marks.":
\t\t\t\t\t\t\t"Worth a scroll through the homepage.";
\t\t\t\t\t\tdocument.getElementById("quiz-body").innerHTML=
\t\t\t\t\t\t\t'<div class="quiz-result"><div class="quiz-progress">Your score</div>'+
\t\t\t\t\t\t\t'<div class="score">'+score+'/'+Q.length+'</div><p>'+msg+'</p>'+
\t\t\t\t\t\t\t'<button class="quiz-next-btn" onclick="cur=0;score=0;render()">Play again</button></div>';
\t\t\t\t\t}
\t\t\t\t\trender();
\t\t\t\t\t</script>''' % (SECTION_NAV, json.dumps(QUIZ, ensure_ascii=False))
open(os.path.join(HERE, "quiz.html"), "w", encoding="utf-8").write(
    shell("Daily Quiz — Backstage", "Five questions from today's Backstage stories.", quiz_inner,
          sidebar_html=SIDEBAR_NONL, canon=CANON + "quiz.html"))

# ============================ STATIC PAGES ============================
STATIC = {
 "about.html": ("About Backstage", '''\t\t\t\t\t\t<p>Backstage is an independent news and entertainment publication covering the stories shaping Nigeria &mdash; politics, security, business, sport, and culture &mdash; alongside the entertainment world that keeps the conversation going.</p>
\t\t\t\t\t\t<p>We publish real, sourced reporting rather than filler. Every article on this site is written from verified news reports, official statements, or primary sources, and updated as stories develop.</p>
\t\t\t\t\t\t<p>Backstage is run independently and is still growing &mdash; new stories are added regularly, and the site itself keeps evolving alongside them.</p>
\t\t\t\t\t\t<h2>Editorial guidelines</h2>
\t\t\t\t\t\t<p>Facts first, sourced and datelined. Corrections are made openly and promptly. Opinion is labelled as opinion. Tips and story leads are always welcome at <a href="mailto:%s">%s</a>.</p>''' % (EMAIL, EMAIL)),
 "privacy.html": ("Privacy Policy", '''\t\t\t\t\t\t<p><em>Last updated: August 2026</em></p>
\t\t\t\t\t\t<p>Backstage is a simple, independently run publication. Here's a straightforward account of what happens with your information when you visit.</p>
\t\t\t\t\t\t<h2>What we collect</h2>
\t\t\t\t\t\t<p>This site does not use tracking cookies or third-party analytics. If you email us (a tip, correction, or inquiry) we'll have your address and whatever you include &mdash; nothing more.</p>
\t\t\t\t\t\t<h2>How we use it</h2>
\t\t\t\t\t\t<p>Anything you send us directly is used only to respond to you or follow up on a story tip. We don't sell, share, or rent contact information.</p>
\t\t\t\t\t\t<h2>Newsletter</h2>
\t\t\t\t\t\t<p>Any email address submitted to the newsletter is used only to send Backstage updates, and you can unsubscribe at any time.</p>
\t\t\t\t\t\t<h2>Questions</h2>
\t\t\t\t\t\t<p>Reach out via the <a href="contact.html">Contact page</a> or <a href="mailto:%s">%s</a>.</p>''' % (EMAIL, EMAIL)),
 "terms.html": ("Terms of Service", '''\t\t\t\t\t\t<p><em>Last updated: August 2026</em></p>
\t\t\t\t\t\t<p>By reading and using Backstage, you agree to the following plain-language terms.</p>
\t\t\t\t\t\t<h2>Content</h2>
\t\t\t\t\t\t<p>Articles are written and published in good faith, based on publicly available reporting and verified sources at the time of publication. We update or correct articles when new information comes to light.</p>
\t\t\t\t\t\t<h2>Use of this site</h2>
\t\t\t\t\t\t<p>You're welcome to read, share, and link to articles. Please don't republish full articles elsewhere without permission &mdash; link back to the original story instead.</p>
\t\t\t\t\t\t<h2>No warranty</h2>
\t\t\t\t\t\t<p>Backstage is provided as-is. We take care to verify what we publish but can't guarantee the site will always be available or error-free.</p>'''),
}
for name, (title, prose) in STATIC.items():
    inner = '''
%s
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="main"><h1>%s</h1></header>
\t\t\t\t\t\t<div class="prose">
%s
\t\t\t\t\t\t</div>
\t\t\t\t\t</section>''' % (SECTION_NAV, title, prose)
    open(os.path.join(HERE, name), "w", encoding="utf-8").write(
        shell("%s — Backstage" % title, title + " — Backstage.", inner, canon=CANON + name))

contact_inner = '''
%s
\t\t\t\t\t<section>
\t\t\t\t\t\t<header class="main"><h1>Contact &amp; tips</h1></header>
\t\t\t\t\t\t<div class="prose">
\t\t\t\t\t\t\t<p>Have a story tip, a correction, or a question about something we've published? We'd like to hear from you. We read every message and try to respond within a day or two.</p>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="box">
\t\t\t\t\t\t\t<p><strong>General inquiries &amp; tips</strong><br />
\t\t\t\t\t\t\t<a href="mailto:%s">%s</a></p>
\t\t\t\t\t\t\t<p><strong>Advertise with us</strong><br />
\t\t\t\t\t\t\t<a href="mailto:%s?subject=Advertising">%s</a></p>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<h2>Send a message</h2>
\t\t\t\t\t\t<form method="post" action="mailto:%s" enctype="text/plain">
\t\t\t\t\t\t\t<div class="row gtr-uniform">
\t\t\t\t\t\t\t\t<div class="col-6 col-12-xsmall"><input type="text" name="name" placeholder="Your name" required /></div>
\t\t\t\t\t\t\t\t<div class="col-6 col-12-xsmall"><input type="email" name="email" placeholder="Your email" required /></div>
\t\t\t\t\t\t\t\t<div class="col-12"><textarea name="message" placeholder="Your message" rows="6" required></textarea></div>
\t\t\t\t\t\t\t\t<div class="col-12"><ul class="actions"><li><input type="submit" value="Send message" class="primary" /></li></ul></div>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</form>
\t\t\t\t\t</section>''' % (SECTION_NAV, EMAIL, EMAIL, EMAIL, EMAIL, EMAIL)
open(os.path.join(HERE, "contact.html"), "w", encoding="utf-8").write(
    shell("Contact — Backstage", "Send a story tip or correction to Backstage.", contact_inner, canon=CANON + "contact.html"))

# ============================ SEO / INFRA ============================
all_urls = ["index.html"] + ["latest-%d.html" % n for n in range(2, NP + 1)] + section_files + \
           ["search.html", "quiz.html", "about.html", "contact.html", "privacy.html", "terms.html"] + list(arts.keys())
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in all_urls:
    sm.append("  <url><loc>%s%s</loc></url>" % (CANON, u))
sm.append("</urlset>")
open(os.path.join(HERE, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(HERE, "robots.txt"), "w").write("User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % CANON)
open(os.path.join(HERE, "manifest.json"), "w").write(json.dumps({
    "name": "Backstage", "short_name": "Backstage",
    "description": "What's running, right now — Nigerian news, entertainment, sports, and business.",
    "start_url": "index.html", "scope": "./", "display": "standalone",
    "background_color": "#FBFAF6", "theme_color": "#7D1226",
    "icons": [
        {"src": "icons/icon-32.png", "sizes": "32x32", "type": "image/png"},
        {"src": "icons/icon-180.png", "sizes": "180x180", "type": "image/png"},
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}, indent=2) + "\n")

# ---- RSS feed (latest 40) ----
def rss_esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

items = []
for fn, a in order[:40]:
    items.append(
        "    <item>\n"
        "      <title>%s</title>\n"
        "      <link>%s%s</link>\n"
        "      <guid>%s%s</guid>\n"
        "      <category>%s</category>\n"
        "      <description>%s</description>\n"
        "    </item>" % (
            rss_esc(a["title"]), CANON, fn, CANON, fn, a["cat"].capitalize(),
            rss_esc((a["excerpt"] or (a["paras"][0] if a["paras"] else ""))[:400])))
feed = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>\n'
        '  <title>Backstage</title>\n'
        '  <link>%s</link>\n'
        '  <description>What\'s running, right now — Nigerian news, entertainment, sports and business.</description>\n'
        '  <language>en-ng</language>\n%s\n</channel></rss>\n' % (CANON, "\n".join(items)))
open(os.path.join(HERE, "feed.xml"), "w", encoding="utf-8").write(feed)

# ---- 404 page ----
_404 = '''
\t\t\t\t\t<section style="text-align:center;padding:3em 0;">
\t\t\t\t\t\t<header class="main"><h1>Page not found</h1></header>
\t\t\t\t\t\t<p>That story may have moved, or the link is broken.</p>
\t\t\t\t\t\t<ul class="actions" style="justify-content:center;">
\t\t\t\t\t\t\t<li><a href="index.html" class="button primary">Back to the homepage</a></li>
\t\t\t\t\t\t\t<li><a href="search.html" class="button">Search</a></li>
\t\t\t\t\t\t</ul>
\t\t\t\t\t</section>'''
open(os.path.join(HERE, "404.html"), "w", encoding="utf-8").write(
    shell("Page not found — Backstage", "Page not found.", _404, canon=None))

print("Backstage rebuilt.")
print("  %d articles  (%d with a real photo, %d on category art)" % (len(arts), n_photo, len(arts) - n_photo))
print("  index + latest-2..%d  |  %d section pages  |  search, quiz, about, contact, privacy, terms" % (NP, len(section_files)))
print("  sitemap.xml (%d urls), feed.xml, robots.txt, manifest.json, 404.html" % len(all_urls))
print("  images: %d real photos, %d designed covers" % (n_photo, sum(1 for s in arts if cover(s[:-5]) and not PHOTOS.get(s[:-5]))))
if len(arts) - n_photo:
    print("\n  To swap in a real photo: drop  photos/<slug>.jpg  then run  python3 rebuild.py")
