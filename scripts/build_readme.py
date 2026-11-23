#!/usr/bin/env python3
"""Build the README's intro card and link chips as SVGs.

Writes:
  assets/card/desktop-light.svg, desktop-dark.svg   (side by side, 840 wide)
  assets/card/phone-light.svg,   phone-dark.svg     (stacked, 358 wide)
  assets/photos/header-*.svg                        ("$ open ~/photos · see all" row, linked in the README)
  assets/links/<name>-light.svg, <name>-dark.svg    (pill-shaped link chips)

Edit the copy in CONTENT below, then run:  python3 scripts/build_readme.py
Needs Pillow (pip install pillow) to measure text so it wraps cleanly.
"""
from html import escape
from pathlib import Path

from PIL import ImageFont

import pup

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- content
# Each line is a list of (text, style) runs. style: "" | "b" (bold) | "link".
CONTENT = {
    "heading": "Hi! I'm Arjun",
    "about": "I'm a passionate developer with a keen interest in open-source projects and community building.",
    "bullets": [
        [("Using Swift to develop ", ""), ("Resolve", "b")],
        [("Taking courses in software engineering, algorithms, testing, and user interfaces", "")],
        [("Looking to collaborate on open-source projects in software development and AI", "")],
        [("Fun fact: I love photography! Take a look at some of ", ""), ("my photos", "link"), (" ;)", "")],
    ],
    "now": [
        [("Exchange semester at the ", ""), ("Technical University of Munich", "b")],
        [("Software Engineer at ", ""), ("Ivo AI", "b"), (" in San Francisco", "")],
    ],
    "tools": ["Swift", "SwiftUI", "TypeScript", "React", "Next.js", "Node.js", "Tailwind CSS",
              "Python", "Supabase", "Firebase", "PostgreSQL", "Docker", "Git", "Figma",
              "JavaScript", "Java", "C++", "GitHub"],
}

LINKS = ["instagram", "linkedin", "email", "website", "photos"]

THEMES = {
    "light": dict(card="#f6f8fa", line="#d8dee4", ink="#0d1117", muted="#59636e",
                  accent="#1a7f37", pup="#000000", screen="#1a7f37", chip_arrow="#8c959f"),
    "dark": dict(card="#151b23", line="#2a313c", ink="#f0f6fc", muted="#9198a1",
                 accent="#3fb950", pup="#ffffff", screen="#3fb950", chip_arrow="#656c76"),
}

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# ---------------------------------------------------------------- measuring
_FONT_FILES = {
    "": ["/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"],
    "b": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/SFNS.ttf"],
}
_cache = {}

def text_width(s, size, bold=False):
    """Widest of the fonts we can find (different OSes use different sans fonts)."""
    key = (s, size, bold)
    if key not in _cache:
        widths = []
        for f in _FONT_FILES["b" if bold else ""]:
            try:
                widths.append(ImageFont.truetype(f, size).getlength(s) * (1.06 if bold and "SFNS" in f else 1))
            except OSError:
                pass
        _cache[key] = max(widths) if widths else len(s) * size * (0.6 if bold else 0.55)
    return _cache[key]

def wrap(runs, size, width):
    """Greedy word wrap of styled runs. Returns a list of lines, each a list of runs."""
    words = []
    for text, style in runs:
        parts = text.split(" ")
        for i, w in enumerate(parts):
            if w:
                words.append([w, style, i < len(parts) - 1 or text.endswith(" ")])
            if i < len(parts) - 1 and words:
                words[-1][2] = True
    lines, cur, cur_w = [], [], 0.0
    limit = width * 0.95
    for w, style, space_after in words:
        ww = text_width(w, size, style == "b")
        sp = text_width(" ", size)
        if cur and cur_w + ww > limit:
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur.append((w, style, space_after))
        cur_w += ww + (sp if space_after else 0)
    if cur:
        lines.append(cur)
    out = []
    for line in lines:
        runs_out = []
        for i, (w, style, space_after) in enumerate(line):
            pieces = [(w, style)]
            if space_after and i < len(line) - 1:
                # keep spaces out of underlined links
                inside = line[i + 1][1] == style
                pieces.append((" ", style if (style != "link" or inside) else ""))
            for piece, st in pieces:
                if runs_out and runs_out[-1][1] == st:
                    runs_out[-1] = (runs_out[-1][0] + piece, st)
                else:
                    runs_out.append((piece, st))
        out.append(runs_out)
    return out

# ---------------------------------------------------------------- drawing
def baseline(top, lh, size):
    return round(top + lh / 2 + size * 0.35, 1)

def line_svg(x, y, runs, cls):
    spans = []
    for text, style in runs:
        t = escape(text)
        if style == "b":
            spans.append(f'<tspan class="b">{t}</tspan>')
        elif style == "link":
            spans.append(f'<tspan class="lnk">{t}</tspan>')
        else:
            spans.append(t)
    return f'<text class="{cls}" x="{x}" y="{y}">{"".join(spans)}</text>'


class Flow:
    """Tiny top-to-bottom layout helper."""

    def __init__(self, y=0):
        self.y = y
        self.out = []

    def mono(self, x, s, size, lh, cls="cmd", anchor=None):
        a = f' text-anchor="{anchor}"' if anchor else ""
        self.out.append(f'<text class="{cls}" x="{x}" y="{baseline(self.y, lh, size)}" '
                        f'font-size="{size}"{a}>{escape(s)}</text>')

    def para(self, x, width, runs, size, lh, cls):
        for line in wrap(runs, size, width):
            self.out.append(line_svg(x, baseline(self.y, lh, size), line, cls))
            self.y += lh

    def bullets(self, x, width, items, size, lh, gap, marker_w):
        for i, runs in enumerate(items):
            self.out.append(f'<text class="mk" x="{x}" y="{baseline(self.y, lh, size)}" '
                            f'font-size="{size}">›</text>')
            self.para(x + marker_w, width - marker_w, runs, size, lh, "t")
            if i < len(items) - 1:
                self.y += gap

    def gap(self, n):
        self.y += n


def ticker(x, y, width, size, lh, tid):
    """Endless left-scrolling line of tools, faded at both edges."""
    sep = " ✳ "
    natural = sum(text_width(t, size) for t in CONTENT["tools"]) + len(CONTENT["tools"]) * (text_width("✳", size) + 2 * size)
    length = round(natural * 1.04)
    period = length + size  # copy length + the em space before the next copy
    spans = sep.join(escape(t) for t in CONTENT["tools"]).split("✳")
    inner = '<tspan class="mk">✳</tspan>'.join(spans) + " " + '<tspan class="mk">✳</tspan>'
    by = baseline(y, lh, size)
    copies = "".join(
        f'<text class="t" x="{x + i * period}" y="{by}" textLength="{length}" lengthAdjust="spacing">{inner}</text>'
        for i in range(3))
    dur = round(period / 22, 1)  # ~22px per second
    css = (f"@keyframes {tid}{{from{{transform:translateX(0)}}to{{transform:translateX(-{period}px)}}}}"
           f".{tid}{{animation:{tid} {dur}s linear infinite}}"
           f"@media (prefers-reduced-motion: reduce){{.{tid}{{animation:none}}}}")
    defs = (f'<linearGradient id="{tid}-g" x1="0" x2="1" y1="0" y2="0">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".1" stop-color="#fff"/>'
            f'<stop offset=".9" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="{tid}-m" maskUnits="userSpaceOnUse" x="{x}" y="{y - 4}" width="{width}" height="{lh + 8}">'
            f'<rect x="{x}" y="{y - 4}" width="{width}" height="{lh + 8}" fill="url(#{tid}-g)"/></mask>')
    markup = f'<g mask="url(#{tid}-m)"><g class="{tid}">{copies}</g></g>'
    return defs, css, markup


def card(theme, layout):
    c = THEMES[theme]
    P = pup.build(c["pup"], c["screen"])
    desktop = layout == "desktop"

    if desktop:
        W, pad_t, pad_x, pad_b = 840, 40, 44, 36
        pup_w = 290
        col_x = pad_x + pup_w + 44
        col_w = W - pad_x - col_x
        sz, lh, cmd_sz, cmd_lh, h_sz = 15, 22.5, 13, 18, 32
    else:
        W, pad_t, pad_x, pad_b = 358, 24, 20, 24
        pup_w = 230
        col_x = pad_x
        col_w = W - 2 * pad_x
        sz, lh, cmd_sz, cmd_lh, h_sz = 14.5, 21.75, 12, 16, 26
    inner_w = W - 2 * pad_x
    pup_h = round(P["h"] * pup_w / P["w"], 1)
    marker_w = 22 if desktop else 20

    # --- intro column
    col = Flow()
    col.mono(col_x, "$ whoami", cmd_sz, cmd_lh)
    col.gap(cmd_lh + (18 if desktop else 12))
    col.out.append(f'<text class="h" x="{col_x}" y="{baseline(col.y, h_sz * 1.12, h_sz)}" '
                   f'font-size="{h_sz}">{escape(CONTENT["heading"])}</text>')
    col.gap(h_sz * 1.12 + (10 if desktop else 12))
    col.para(col_x, col_w, [(CONTENT["about"], "")], sz, sz * 1.55, "m")
    col.gap(18)
    col.bullets(col_x, col_w, CONTENT["bullets"], sz, lh, 10, marker_w)
    col_h = col.y

    parts = []
    if desktop:
        top_h = max(col_h, pup_h)
        pup_y = pad_t + (top_h - pup_h) / 2
        col_dy = pad_t + (top_h - col_h) / 2
        pup_x = pad_x
        y = pad_t + top_h
    else:
        pup_y = pad_t
        pup_x = (W - pup_w) / 2
        col_dy = pad_t + pup_h + 20
        y = col_dy + col_h
    parts.append(f'<g transform="translate({pup_x} {round(pup_y, 1)}) scale({round(pup_w / P["w"], 5)})">{P["markup"]}</g>')
    parts.append(f'<g transform="translate(0 {round(col_dy, 1)})">{"".join(col.out)}</g>')

    # --- divider + now + tools
    y += 36 if desktop else 20
    parts.append(f'<line class="rule" x1="{pad_x}" x2="{W - pad_x}" y1="{y}" y2="{y}"/>')
    low = Flow(y + (28 if desktop else 20))
    low.mono(pad_x, "$ cat ~/now.txt", cmd_sz, cmd_lh)
    low.gap(cmd_lh + (16 if desktop else 12))
    low.bullets(pad_x, inner_w, CONTENT["now"], sz, lh, 6, marker_w)
    low.gap(28 if desktop else 20)
    low.mono(pad_x, "$ ls ~/tools-and-technologies", cmd_sz, cmd_lh)
    low.gap(cmd_lh + (16 if desktop else 12))
    t_defs, t_css, t_markup = ticker(pad_x, low.y, inner_w, sz, lh, "tk")
    low.gap(lh)
    parts += low.out
    parts.append(t_markup)
    card_h = round(low.y + pad_b)
    H = card_h

    css = f"""
text{{white-space:pre}}
.t,.m,.h{{font-family:{SANS}}}
.t{{fill:{c["ink"]};font-size:{sz}px}}
.m{{fill:{c["muted"]};font-size:{sz}px}}
.h{{fill:{c["ink"]};font-weight:700;letter-spacing:-0.02em}}
.b{{font-weight:700}}
.lnk{{fill:{c["accent"]}}}
.cmd,.cmdm,.mk{{font-family:{MONO}}}
.cmd,.mk{{fill:{c["accent"]}}}
.cmdm{{fill:{c["muted"]}}}
.rule{{stroke:{c["line"]};stroke-width:1}}
{t_css}
{P["css"]}
"""
    label = (f"Hi! I'm Arjun. {CONTENT['about']} "
             + " ".join("".join(t for t, _ in b) + "." for b in CONTENT["bullets"])
             + " Now: " + "; ".join("".join(t for t, _ in b) for b in CONTENT["now"])
             + ". Tools: " + ", ".join(CONTENT["tools"]) + ".")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(label)}">
<style>{css}</style>
<defs>{t_defs}</defs>
<rect x="0.5" y="0.5" width="{W - 1}" height="{card_h - 1}" rx="{16 if desktop else 14}" fill="{c["card"]}" stroke="{c["line"]}"/>
{chr(10).join(parts)}
</svg>
"""


def photos_header(theme, layout):
    """The "$ open ~/photos · see all ↗" row. Its own image so the README can wrap it in a link."""
    c = THEMES[theme]
    desktop = layout == "desktop"
    W = 840 if desktop else 358
    size = 13 if desktop else 12
    H = 28
    y = baseline(4, 20, size)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Open my photo gallery">
<text x="0" y="{y}" font-family="{MONO}" font-size="{size}" fill="{c["accent"]}" style="white-space:pre">$ open ~/photos</text>
<text x="{W}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="{size}" fill="{c["muted"]}" style="white-space:pre">see all ↗</text>
</svg>
"""


def chip(name, theme):
    c = THEMES[theme]
    label = name
    size, h, pad = 13, 36, 14
    char = 7.9  # monospace advance at 13px
    w = round(pad * 2 + (2 + 1 + len(label) + 1 + 1) * char + 4)
    y = h / 2 + size * 0.35
    x = pad
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{name}">
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{h / 2}" fill="{c["card"]}" stroke="{c["line"]}"/>
<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{c["ink"]}" style="white-space:pre"><tspan fill="{c["accent"]}">~/</tspan> {label} <tspan fill="{c["chip_arrow"]}">↗</tspan></text>
</svg>
"""


def main():
    (ROOT / "assets/card").mkdir(parents=True, exist_ok=True)
    (ROOT / "assets/links").mkdir(parents=True, exist_ok=True)
    for layout in ("desktop", "phone"):
        for theme in THEMES:
            path = ROOT / f"assets/card/{layout}-{theme}.svg"
            path.write_text(card(theme, layout))
            print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")
            (ROOT / f"assets/photos/header-{layout}-{theme}.svg").write_text(photos_header(theme, layout))
    for name in LINKS:
        for theme in THEMES:
            (ROOT / f"assets/links/{name}-{theme}.svg").write_text(chip(name, theme))
    print(f"wrote {len(LINKS) * len(THEMES)} link chips in assets/links/")


if __name__ == "__main__":
    main()
