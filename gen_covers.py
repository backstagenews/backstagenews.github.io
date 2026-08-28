#!/usr/bin/env python3
"""
Generate a unique SVG cover for every article in _data/articles.json.

Output:  covers/<slug>.svg   (16:9, headline + category + date on the
Backstage curtain motif).  These are DESIGNED GRAPHICS, not photographs.

rebuild.py uses them automatically for any story that has no real photo
in photos/.  Run:  python3 gen_covers.py  then  python3 rebuild.py
"""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
arts = json.load(open(os.path.join(HERE, "_data", "articles.json"), encoding="utf-8"))
os.makedirs(os.path.join(HERE, "covers"), exist_ok=True)

W, H = 1200, 600
PAL = {
    "news":          ("#7D1226", "#4c0a17", "#f3d9b0"),
    "entertainment": ("#B9832A", "#7d5717", "#fbeccb"),
    "sports":        ("#1C2740", "#0f1626", "#e6c893"),
    "business":      ("#3B2A2F", "#241a1d", "#e9c48f"),
}
GLYPH = {"news": "◆", "entertainment": "♫", "sports": "⚽", "business": "₦"}


def wrap(text, max_chars):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def esc(s):
    return html.escape(s, quote=True)


made = 0
for fn, a in arts.items():
    slug = fn[:-5]
    cat = a["cat"] if a["cat"] in PAL else "news"
    c1, c2, ink = PAL[cat]

    title = html.unescape(a["title"])
    size = 60 if len(title) < 60 else (52 if len(title) < 95 else 44)
    per_line = int(W * 0.80 / (size * 0.57))
    lines = wrap(title, per_line)[:5]
    lh = size * 1.14
    block_h = lh * len(lines)
    y0 = (H * 0.54) - block_h / 2 + size

    tspans = "".join(
        '<tspan x="70" y="%.0f">%s</tspan>' % (y0 + i * lh, esc(ln)) for i, ln in enumerate(lines)
    )

    # curtain scallop motif along the top
    scallops = "".join(
        '<path d="M %d 0 Q %d 46 %d 0 Z" fill="%s" opacity="0.35"/>' % (x, x + 30, x + 60, c2)
        for x in range(0, W, 60)
    )

    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Georgia, 'Roboto Slab', serif">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#g)"/>
  {scallops}
  <text x="{gx}" y="{gy}" font-size="520" fill="{ink}" opacity="0.06" text-anchor="middle" dominant-baseline="middle">{glyph}</text>
  <text x="70" y="86" font-size="22" letter-spacing="8" fill="{ink}" font-weight="bold">BACKSTAGE</text>
  <text x="70" y="112" font-size="14" letter-spacing="4" fill="{ink}" opacity="0.8">WHAT'S RUNNING, RIGHT NOW</text>
  <text font-size="{size}" font-weight="bold" fill="#faf7f0">{tspans}</text>
  <rect x="70" y="{by}" width="{cw}" height="34" rx="4" fill="{ink}"/>
  <text x="86" y="{bty}" font-size="16" letter-spacing="4" fill="{c2}" font-weight="bold">{CAT}</text>
  <text x="{W2}" y="{bty}" font-size="18" fill="{ink}" text-anchor="end" opacity="0.9">{date}</text>
  <rect x="0" y="{H1}" width="{W}" height="6" fill="{ink}" opacity="0.9"/>
</svg>'''.format(
        W=W, H=H, W2=W - 70, H1=H - 6, c1=c1, c2=c2, ink=ink,
        scallops=scallops, glyph=GLYPH[cat], gx=W - 175, gy=H - 130,
        size=size, tspans=tspans,
        by=H - 96, bty=H - 73, cw=len(cat) * 14 + 36, CAT=cat.upper(),
        date=esc(html.unescape(a.get("date_str") or "")),
    )
    open(os.path.join(HERE, "covers", slug + ".svg"), "w", encoding="utf-8").write(svg)
    made += 1

print("generated %d covers in covers/" % made)
