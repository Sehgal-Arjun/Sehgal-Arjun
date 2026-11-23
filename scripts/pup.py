"""The typing character, as SVG markup that can be dropped into a bigger SVG.

The art lives in assets/ascii-art-typing.txt. Animation is pure CSS so it plays
inside a GitHub README <img>:
  - intro: the art "prints" in row by row
  - loop: the hands take turns tapping the keyboard, each tap presses a key,
    and green text types onto the laptop screen, holds, then clears

All class and keyframe names are prefixed so the CSS can't clash with the
SVG it gets embedded in.
"""
import random
from html import escape
from pathlib import Path

ART = Path(__file__).resolve().parent.parent / "assets" / "ascii-art-typing.txt"

CW, CH, FS = 8.4, 15, 14   # char width, row height, font size (px, in art units)
ROW_DELAY = 38             # ms between rows during the intro
CYCLE = 8000               # ms per typing loop
TYPE_FOR = 5000            # ms spent typing per loop; the rest is a pause
HOLD = 0.8                 # fraction of the cycle each typed char stays visible
PAD = 12

# Laptop screen is a slanted parallelogram; these are its inner edges (0-indexed cols).
def _in_screen(r, c):
    left = 79 - (r - 26) * 7 / 21
    right = 94 - (r - 26) * 9 / 21
    return 26 <= r <= 47 and left + 1 < c < right - 1

# Hand boxes (row0, row1, col0, col1), inclusive: the two hands on the keyboard.
HAND_BOXES = {"handA": (37, 43, 53, 60), "handB": (37, 42, 61, 66)}

def _region(r, c, ch):
    for name, (r0, r1, c0, c1) in HAND_BOXES.items():
        if r0 <= r <= r1 and c0 <= c <= c1:
            return name
    if _in_screen(r, c):
        return "screen"
    if 44 <= r <= 48 and 52 <= c <= 72 and ch == "#":
        return "key"
    return "body"


def build(ink, screen_ink, p="pp"):
    """Return {"css", "markup", "w", "h"} for the character in the given colours.

    `p` prefixes every class and keyframe name. Wrap `markup` in
    <g class="{p}"> (already done) and position/scale it with a transform.
    """
    rows = ART.read_text().rstrip("\n").split("\n")
    intro = len(rows) * ROW_DELAY + 400
    rng = random.Random(7)  # fixed seed: same output every build

    body, screen, keys = [], [], []
    hands = {"handA": [], "handB": []}
    for r, line in enumerate(rows):
        c = 0
        while c < len(line):
            ch = line[c]
            if ch == " ":
                c += 1
                continue
            reg = _region(r, c, ch)
            if reg == "body" or reg in hands:
                start = c
                while c < len(line) and line[c] != " " and _region(r, c, line[c]) == reg:
                    c += 1
                (body if reg == "body" else hands[reg]).append((r, start, line[start:c]))
            else:
                (screen if reg == "screen" else keys).append((r, c, ch))
                c += 1

    everything = body + screen + keys + hands["handA"] + hands["handB"]
    min_c = min(s for _, s, _ in everything)
    max_c = max(s + len(t) for _, s, t in everything)
    min_r = min(r for r, _, _ in everything)
    max_r = max(r for r, _, _ in everything)
    X = lambda c: round((c - min_c) * CW + PAD, 1)
    Y = lambda r: round((r - min_r) * CH + PAD + FS, 1)
    w = round((max_c - min_c) * CW + PAD * 2)
    h = round((max_r - min_r + 1) * CH + PAD * 2)

    def text(r, c, t, cls, delay):
        return f'<text class="{cls}" x="{X(c)}" y="{Y(r)}" style="animation-delay:{delay}ms">{escape(t)}</text>'

    out = [text(r, c, t, f"{p}-c", r * ROW_DELAY) for r, c, t in body]

    screen.sort()
    step = TYPE_FOR / len(screen)
    type_times = [i * step for i in range(len(screen))]
    out += [text(r, c, t, f"{p}-s", round(intro + type_times[i])) for i, (r, c, t) in enumerate(screen)]

    presses = {i: [] for i in range(len(keys))}
    hand_taps = {"handA": [], "handB": []}
    for n, t in enumerate(type_times):
        presses[rng.randrange(len(keys))].append(t)
        hand_taps["handA" if n % 2 == 0 else "handB"].append(t)

    css = []
    for name, taps in hand_taps.items():
        frames = []
        for t0 in taps:
            a, b, e = ((t0 - 40) / CYCLE * 100, t0 / CYCLE * 100, (t0 + 110) / CYCLE * 100)
            frames.append(f"{max(a, 0):.2f}%{{transform:none}}"
                          f"{b:.2f}%{{transform:translate(0,2px)}}"
                          f"{e:.2f}%{{transform:none}}")
        css.append(f"@keyframes {p}-{name}{{{''.join(frames)}}}"
                   f".{p}-{name}{{animation:{p}-{name} {CYCLE}ms ease-in-out {intro}ms infinite}}")
        out.append(f'<g class="{p}-{name}">')
        out += [text(r, c, t, f"{p}-c", r * ROW_DELAY) for r, c, t in hands[name]]
        out.append("</g>")

    for i, (r, c, t) in enumerate(keys):
        out.append(f'<text class="{p}-k {p}-k{i}" x="{X(c)}" y="{Y(r)}">{escape(t)}</text>')
        if not presses[i]:
            continue
        frames = []
        for t0 in presses[i]:
            a, b, e = (t0 / CYCLE * 100, (t0 + 60) / CYCLE * 100, (t0 + 160) / CYCLE * 100)
            frames.append(f"{a:.2f}%{{transform:none;opacity:1}}"
                          f"{b:.2f}%{{transform:translateY(1px);opacity:.55}}"
                          f"{e:.2f}%{{transform:none;opacity:1}}")
        css.append(f"@keyframes {p}-p{i}{{{''.join(frames)}}}"
                   f".{p}-k{i}{{animation:{p}-print .35s ease-out {r * ROW_DELAY}ms forwards,"
                   f"{p}-p{i} {CYCLE}ms linear {intro}ms infinite}}")

    base = f"""
.{p} text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS}px;font-weight:700;white-space:pre}}
.{p}-c,.{p}-k{{fill:{ink};opacity:0;animation:{p}-print .35s ease-out forwards}}
@keyframes {p}-print{{from{{opacity:0;transform:translateY(-4px)}}to{{opacity:1;transform:none}}}}
.{p}-k{{transform-box:fill-box}}
.{p}-s{{fill:{screen_ink};opacity:0;animation:{p}-type {CYCLE}ms steps(1) infinite}}
@keyframes {p}-type{{0%{{opacity:1}}{HOLD * 100:.0f}%{{opacity:0}}}}
"""
    reduced = (f"@media (prefers-reduced-motion: reduce){{.{p}-c,.{p}-k,.{p}-s{{animation:none;opacity:1}}"
               f".{p}-handA,.{p}-handB{{animation:none}}}}")
    return {
        "css": base + "\n".join(css) + "\n" + reduced,
        "markup": f'<g class="{p}">\n' + "\n".join(out) + "\n</g>",
        "w": w,
        "h": h,
    }
