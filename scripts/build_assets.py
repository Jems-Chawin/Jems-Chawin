"""Pixel-art versions of the six animations on the profile README.

Artwork sits on a 2px grid. Small text is drawn at 1px resolution from a real
bitmap-style font (rasterised here with no anti-aliasing), because an SVG loaded
as an image cannot load a web font and 2px text was too coarse to read.
Motion is stepped (discrete SMIL or CSS steps) so nothing glides between cells.

Run on macOS (the fonts below ship with it; Pillow is the only dependency):
    uv run --with pillow python scripts/build_assets.py
Writes assets/<name>-light.svg and assets/<name>-dark.svg for:
  hero    the name being "detected", with a typed line
  vision  three tracked people, each with an id and a confidence score
  eval    two precision/recall curves being drawn
  agent   an agent loop in a terminal
  sim     a wireframe greenhouse with a robot driving the aisles
  merge   two sets of model weights averaged into one

The output is plain SVG with CSS and SMIL animation, so GitHub can show it as
an image. No scripts, no external fonts, no network requests.
"""
import functools
import math
import pathlib
import random
import re

from PIL import Image, ImageDraw, ImageFont

C = 2  # artwork cell size in px
TW, TH = 206, 118  # small tile, in cells (412 x 236 px)

THEMES = {
    "dark": dict(bg="#151b23", line="#3d444d", fg="#f0f6fc", mute="#9198a1",
                 blue="#4493f8", purple="#ab7df8", orange="#f0883e", green="#3fb950"),
    "light": dict(bg="#f6f8fa", line="#d1d9e0", fg="#1f2328", mute="#59636e",
                  blue="#1f6feb", purple="#8250df", orange="#bf5b04", green="#1a7f37"),
}

SYS = "/System/Library/Fonts/"
FONTS = {  # name -> (file, pixel size). Only the rasterised pixels end up in the SVG.
    "mono": (SYS + "Monaco.ttf", 10),
    "sub": (SYS + "Supplemental/Verdana.ttf", 14),
    "head": (SYS + "Supplemental/Arial Bold.ttf", 23),
}
CHECK = ["......##", ".....##.", "#...##..", "##.##...", ".###....", "..#....."]  # the fonts have no tick


# ---- drawing primitives -------------------------------------------------

def rnd(v):
    return math.floor(v + .5)  # round half up, so 2:1 slopes step evenly


def px(cells, fill, extra="", u=C):
    """Cells -> one <path>; every horizontal run is a stroke one unit thick (u = unit size in px)."""
    cells = sorted(set(cells), key=lambda p: (p[1], p[0]))
    d, i = [], 0
    while i < len(cells):
        x, y = cells[i]
        n = 1
        while i + n < len(cells) and cells[i + n] == (x + n, y):
            n += 1
        d.append(f"M{x*u} {y*u + u/2:g}h{n*u}")
        i += n
    return f'<path d="{"".join(d)}" stroke="{fill}" stroke-width="{u}" fill="none"{extra}/>' if d else ""


def block(x0, y0, w, h):
    return [(x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h)]


def line(p, q):
    (x0, y0), (x1, y1) = p, q
    n = max(abs(x1 - x0), abs(y1 - y0)) or 1
    return [(rnd(x0 + (x1 - x0) * i / n), rnd(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]


def trace(points):
    """Join sampled points into a gap-free run of cells, in order, without repeats."""
    cells = []
    for a, b in zip(points, points[1:]):
        for c in line((rnd(a[0]), rnd(a[1])), (rnd(b[0]), rnd(b[1]))):
            if not cells or cells[-1] != c:
                cells.append(c)
    return cells


def bezier(p0, p1, p2, p3, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d
                         for a, b, c, d in zip(p0, p1, p2, p3)))
    return trace(pts)


def sprite(rows, x, y, key="#"):
    return [(x + c, y + r) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch in key]


# ---- text ----------------------------------------------------------------

@functools.lru_cache(None)
def _font(name):
    path, size = FONTS[name]
    return ImageFont.truetype(path, size)


@functools.lru_cache(None)
def _bits(s, name):
    """Lit pixels of `s` drawn with no anti-aliasing, as (x, y) from the top-left of the line box."""
    f = _font(name)
    im = Image.new("1", (int(f.getlength(s)) + 6, sum(f.getmetrics()) + 6), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((0, 0), s, fill=1, font=f)
    got = im.load()
    return tuple((x, y) for y in range(im.size[1]) for x in range(im.size[0]) if got[x, y])


@functools.lru_cache(None)
def cap(name):
    """(top row, height) of a capital letter in this font."""
    ys = [y for _, y in _bits("H", name)]
    return min(ys), max(ys) - min(ys) + 1


@functools.lru_cache(None)
def raster(s, font="mono", bold=False):
    """-> (pixels relative to the left edge and the cap top, advance in px)."""
    out, x = [], 0
    for part in re.split("(✓)", s):
        if part == "✓":
            out += [(x + c, 1 + r) for r, row in enumerate(CHECK) for c, ch in enumerate(row) if ch == "#"]
            x += 9
        elif part:
            out += [(x + a, b - cap(font)[0]) for a, b in _bits(part, font)]
            x += rnd(_font(font).getlength(part))
    if bold:
        out += [(a + 1, b) for a, b in out]
    return tuple(out), x


def width(s, font="mono", k=1):
    """Width in cells."""
    return -(-raster(s, font)[1] * k // C)


def ink(s, x, y, font="mono", bold=False, k=1, right=False, center=False):
    """Pixels of a string placed at cell (x, y). k=1: 1px units, cap top centred in a 5-cell band.
    k=2: one font pixel per cell, cap top on row y. Returns (points, unit)."""
    pts, adv = raster(s, font, bold)
    if k == 2:
        off = adv if right else adv // 2 if center else 0
        return [(x - off + a, y + b) for a, b in pts], C
    off = adv if right else adv // 2 if center else 0
    return [(x * C - off + a, y * C + 1 + b) for a, b in pts], 1


def text(s, x, y, fill, **kw):
    pts, u = ink(s, x, y, **kw)
    return px(pts, fill, u=u)


def covered(s, x, y, **kw):
    """Cells a string touches, for collision checks."""
    pts, u = ink(s, x, y, **kw)
    return {(a * u // C, b * u // C) for a, b in pts}


# ---- animation helpers --------------------------------------------------

def anim(attr, pairs, dur, begin=0):
    """Discrete SMIL animation from [(keyTime, value), ...]; the first keyTime must be 0."""
    assert pairs[0][0] == 0 and all(a[0] <= b[0] for a, b in zip(pairs, pairs[1:])), pairs[:3]
    vals = ";".join(str(v) for _, v in pairs)
    kts = ";".join(f"{k:.4g}" for k, _ in pairs)
    b = f' begin="{begin}s"' if begin else ""
    return (f'<animate attributeName="{attr}" values="{vals}" keyTimes="{kts}" dur="{dur}s"{b} '
            f'calcMode="discrete" repeatCount="indefinite"/>')


def shown(inner, on, off, dur):
    """A group that is visible from fraction `on` to fraction `off` of every loop."""
    pairs = [(0, 1), (off, 0)] if on == 0 else [(0, 0), (on, 1), (off, 0)]
    return f'<g opacity="{pairs[0][1]}">{inner}{anim("opacity", pairs, dur)}</g>'


def moved(inner, pairs, dur):
    """A group stepped through translate positions given in cells: [(keyTime, (x, y)), ...]."""
    assert pairs[0][0] == 0
    vals = ";".join(f"{x*C} {y*C}" for _, (x, y) in pairs)
    kts = ";".join(f"{k:.4g}" for k, _ in pairs)
    return (f'<g>{inner}<animateTransform attributeName="transform" type="translate" values="{vals}" '
            f'keyTimes="{kts}" dur="{dur}s" calcMode="discrete" repeatCount="indefinite"/></g>')


def jitter(conf, n, seed):
    """A seeded random walk around `conf` that stays in the 90s, so only the last digit changes."""
    rng, v, out = random.Random(seed), conf, []
    lo, hi = max(90, conf - 3), min(99, conf + 2)
    for _ in range(n):
        out.append(v)
        v = min(hi, max(lo, v + rng.choice((-1, 0, 0, 1)) + (v < conf) - (v > conf) * rng.choice((0, 1))))
    assert len(set(out)) >= 3 and all(90 <= x <= 99 for x in out), out
    return out


def chips(t, name, conf, frames, seed, x, y):
    """A blue name chip, then a grey confidence chip whose last digit flickers every half second.
    Seven rows tall from (x, y). Returns (svg, total width in cells)."""
    assert raster("0")[1] == 3 * C  # the digit slots below rely on a 6px monospace advance
    name_w = width(name) + 3
    cx0 = x + name_w + 1
    conf_w = 12
    out = px(block(x, y, name_w, 7), t["blue"]) + text(name, x + 1, y + 1, t["bg"], bold=True)
    out += px(block(cx0, y, conf_w, 7), t["mute"])
    out += text("9", cx0 + 1, y + 1, t["bg"], bold=True) + text("%", cx0 + 7, y + 1, t["bg"], bold=True)
    seq = jitter(conf, frames, seed)
    for d in sorted({v % 10 for v in seq}):
        on = ";".join("1" if v % 10 == d else "0" for v in seq)
        out += (f'<g opacity="{on[0]}">{text(str(d), cx0 + 4, y + 1, t["bg"], bold=True)}'
                f'<animate attributeName="opacity" values="{on}" dur="{frames * .5}s" calcMode="discrete" '
                f'repeatCount="indefinite"/></g>')
    return out, name_w + 1 + conf_w


# ---- shared tile chrome -------------------------------------------------

def frame(t, W, H, title, pager, icons):
    """Background with stepped corners, border, header rule, colour icon(s), title and pager."""
    edge = [(x, y) for x in range(3, W - 3) for y in (0, H - 1)] + [(x, y) for y in range(3, H - 3) for x in (0, W - 1)]
    edge += [(x, y) for x in (1, W - 2) for y in (2, H - 3)] + [(x, y) for x in (2, W - 3) for y in (1, H - 2)]
    bg = "".join(  # four overlapping rects make the stepped corners
        f'<rect x="{x*C}" y="{y*C}" width="{(W-2*x)*C}" height="{(H-2*y)*C}" fill="{t["bg"]}"/>'
        for x, y in ((3, 0), (0, 3), (1, 2), (2, 1)))
    out = bg + px(edge + [(x, 18) for x in range(1, W - 1)], t["line"])
    for i, colour in enumerate(icons):
        out += px(block(8 + 4 * i, 7, 5, 5), colour)
    out += text(title, 13 + 4 * len(icons), 7, t["fg"], bold=True) + text(pager, W - 8, 7, t["mute"], right=True)
    return out


def svg(W, H, label, css, body, reduced=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W*C} {H*C}" width="{W*C}" height="{H*C}" '
            f'shape-rendering="crispEdges" role="img" aria-label="{label}"><style>{css}'
            f'@keyframes bl{{50%{{opacity:0}}}}.bl{{animation:bl 1s steps(1) infinite}}'
            f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}{reduced}}}</style>{body}</svg>\n')


# ---- 01 computer vision -------------------------------------------------

BODY = ["..####..", ".######.", ".######.", ".######.", "..####..", "...##...", ".######.",
        "########", "########", "########", ".######.", ".######."]
PERSON = [  # two walk frames, 8 x 15 cells: one foot lifts at a time
    BODY + [".##..##.", ".##..##.", ".##....."],
    BODY + [".##..##.", ".##..##.", ".....##."],
]
BW, BH, TAG = 14, 21, 8  # bbox size and how far the id chips reach above it


def walk(points, step=2):
    """Grid positions along a polyline, `step` cells at a time, there and back."""
    path = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0)) // step
        path += [(round((x0 + (x1 - x0) * i / n) / step) * step, round((y0 + (y1 - y0) * i / n) / step) * step)
                 for i in range(n)]
    path.append(points[-1])
    return path + path[-2::-1]


def tracked(t, pid, conf, points, dur, frames):
    """One walking person with corner brackets and chips, origin at the bbox top-left."""
    path = walk(points)
    label, tag_w = chips(t, f"ID {pid}", conf, frames, int(pid), 0, -TAG)
    for x, y in path:  # self-check: sprite and chips stay inside the scene, above the footer
        assert 2 <= x and x + max(BW, tag_w) <= TW - 2 and 20 <= y - TAG and y + BH <= 107, (pid, x, y)
    values = ";".join(f"{x*C} {y*C}" for x, y in path)
    corners = []
    for cx, sx in ((0, 1), (BW - 1, -1)):
        for cy, sy in ((0, 1), (BH - 1, -1)):
            corners += [(cx + sx * i, cy) for i in range(4)] + [(cx, cy + sy * i) for i in range(4)]
    move = (f'<animateTransform attributeName="transform" type="translate" values="{values}" '
            f'dur="{dur}s" calcMode="discrete" repeatCount="indefinite"/>')
    body = f'<g>{move}<use href="#p0" class="f0"/><use href="#p1" class="f1"/>{px(corners, t["blue"])}</g>'
    return body, f"<g>{move}{label}</g>"  # labels go in a later layer so a passing person never hides them


def vision(t):
    W, H = TW, TH
    dots = [(x, y) for x in range(15, W - 2, 15) for y in range(34, 105, 15)]
    parts = [  # 03 and 07 keep to separate bands, so only 12 ever crosses another person
        tracked(t, "03", 97, [(8, 38), (68, 30), (138, 40), (168, 32)], 13, 14),
        tracked(t, "07", 94, [(168, 74), (118, 84), (54, 72), (14, 84)], 16, 17),
        tracked(t, "12", 91, [(94, 28), (114, 52), (84, 82)], 11, 15),
    ]
    people = "".join(b for b, _ in parts) + "".join(lab for _, lab in parts)
    defs = "".join(
        f'<g id="p{i}">{px(sprite(rows[:5], 3, 3), t["fg"])}{px(sprite(rows[5:], 3, 8), t["mute"])}</g>'
        for i, rows in enumerate(PERSON))
    css = (f".sw{{animation:sw 6s steps({W - 2}) infinite}}@keyframes sw{{to{{transform:translateX({(W - 2) * C}px)}}}}"
           f".f0{{animation:f .5s steps(1) infinite}}.f1{{animation:f .5s steps(1) -.25s infinite}}"
           f"@keyframes f{{50%{{opacity:0}}}}")
    body = (f"<defs>{defs}</defs>" + frame(t, W, H, "computer vision", "01 / 04", [t["blue"]]) + px(dots, t["line"])
            + f'<rect class="sw" x="{C}" y="{19*C}" width="{C}" height="{(H-20)*C}" fill="{t["blue"]}" opacity=".35"/>'
            + people + text("detect → track → count", 8, 109, t["mute"]))
    return svg(W, H, "Computer vision: three people being detected and tracked, each with an id and a confidence score.",
               css, body, ".f1{opacity:0}")


# ---- 02 data & evaluation -----------------------------------------------

def reveal(cid, inner, x, y, w, h, start, end, off, dur, begin=0, step=2):
    """Draw `inner` left to right in `step`-cell jumps between fractions start and end, clear at `off`."""
    n = w // step
    pairs = ([(0, 0)] if start else []) + [(start + (end - start) * i / n, i * step * C) for i in range(n + 1)] + [(off, 0)]
    return (f'<clipPath id="{cid}"><rect x="{x*C}" y="{y*C}" width="0" height="{h*C}">'
            f'{anim("width", pairs, dur, begin)}</rect></clipPath><g clip-path="url(#{cid})">{inner}</g>')


def evaluation(t):
    W, H, acc = TW, TH, t["purple"]
    axes = [(23, y) for y in range(31, 100)] + [(x, 99) for x in range(23, 195)]
    grey = bezier((23, 42), (75, 43), (125, 50), (155, 69)) + bezier((155, 69), (185, 88), (186, 90), (194, 99))
    top = bezier((23, 35), (90, 35), (150, 39), (170, 56)) + bezier((170, 56), (190, 73), (190, 80), (194, 99))
    thick = top + [(x, y + 1) for x, y in top if y < 98]
    curves = set(grey) | set(thick)
    assert all(23 <= x <= 194 and 31 <= y <= 99 for x, y in curves)
    dots = [(x, y) for y in (48, 65, 82) for x in range(26, 195, 3) if (x, y) not in curves]
    mx, my = next(p for p in top if p[0] == 164)  # the operating point sits on the purple curve
    marker = [(mx + i, my + j) for i in range(-2, 3) for j in range(-2, 3) if abs(i) + abs(j) < 4]
    note = "clean test set ✓"
    cw = width(note) + 5
    chip = px(block(148 - cw, my + 5, cw, 9), acc) + text(note, 150 - cw, my + 7, t["bg"], bold=True)
    foot = "no leaks · hand-checked · reproducible"
    assert not covered(foot, 29, 89) & curves, "footer text collides with a curve"
    body = (frame(t, W, H, "data & evaluation", "02 / 04", [acc]) + px(dots, t["line"]) + px(axes, t["mute"])
            + text("precision", 23, 23, t["mute"]) + text("recall", 195, 103, t["mute"], right=True)
            + text(foot, 29, 89, t["mute"])
            + reveal("cg", px(grey, t["mute"]), 23, 30, 172, 71, 0, .45, .95, 8, begin=.6)
            + reveal("cp", px(thick, acc), 23, 30, 172, 71, 0, .45, .95, 8)
            + shown(px(marker, acc) + chip, .53, .95, 8))
    return svg(W, H, "Data and evaluation: two precision/recall curves drawn on a clean test set.", "", body)


# ---- 03 llm & agents ----------------------------------------------------

BOT = [
    "..........a..........",
    "..........#..........",
    "..........#..........",
    "...###############...",
    "..#################..",
    "..##.............##..",
    "..##..oo.....oo..##..",
    "..##..oo.....oo..##..",
    "..##..oo.....oo..##..",
    "..##.............##..",
    "..##...mmmmmmm...##..",
    "..##.............##..",
    "..#################..",
    "...###############...",
    ".......##...##.......",
    "....#############....",
    "...###############...",
    "...##.#########.##...",
    "...##.#########.##...",
    "......###...###......",
]


def agent(t):
    W, H, acc = TW, TH, t["orange"]
    tick_x = 39 + width("sources match, no guesses") + 6
    rows = [  # (top row, colour, bold, [(x, text), ...])
        (30, t["fg"], False, [(9, "> what did the team ship this week?")]),
        (42, t["mute"], False, [(15, "plan"), (39, "search → read → summarise")]),
        (54, t["mute"], False, [(15, "tool"), (39, 'search_chat("shipped")'), (tick_x, "✓")]),
        (66, t["mute"], False, [(15, "tool"), (39, "read_thread(3)"), (tick_x, "✓")]),
        (78, t["mute"], False, [(15, "check"), (39, "sources match, no guesses"), (tick_x, "✓")]),
        (90, acc, True, [(9, "< 3 releases, 1 blocker. Details sent.")]),
    ]
    bx, by = 170, 46
    lines = ""
    for i, (y, colour, bold, parts) in enumerate(rows):
        inner = ""
        for x, s in parts:
            assert x + width(s) < bx - 2, s  # text never runs into the robot
            inner += text(s, x, y, t["green"], bold=True) if s == "✓" else text(s, x, y, colour, bold=bold)
        lines += shown(inner, .05 + .11 * i, .96, 10)
    bot = (px(sprite(BOT, bx, by), t["mute"]) + px(sprite(BOT, bx, by, "m"), t["fg"])
           + f'<g class="ey">{px(sprite(BOT, bx, by, "o"), acc)}</g>'
           + f'<g class="bl">{px(sprite(BOT, bx, by, "a"), acc)}</g>')
    css = ".ey{animation:ey 4s steps(1) infinite}@keyframes ey{0%,93%{opacity:1}94%,100%{opacity:0}}"
    body = (frame(t, W, H, "llm & agents", "03 / 04", [acc]) + lines + bot
            + f'<g class="bl">{px(block(9, 102, 3, 6), acc)}</g>')
    return svg(W, H, "LLM agents: an agent plans, calls tools, checks its sources and answers.", css, body)


# ---- 04 robotics & simulation -------------------------------------------

def simulation(t):
    W, H, acc = TW, TH, t["green"]

    def P(u, v):  # isometric floor grid, 2:1 pixel slope
        return (96 + 6 * u - 6 * v, 42 + 3 * u + 3 * v)

    grid = [c for v in range(10) for c in line(P(0, v), P(12, v))] + [c for u in range(13) for c in line(P(u, 0), P(u, 9))]
    build, n = "", 0
    for j in range(3):  # three greenhouse bays, five hoops each
        hoops = []
        for k in range(5):
            sx, sy = 96 + 24 * j - 12 * k, 45 + 12 * j + 6 * k
            hoop = trace([(sx + 18 * i / 40, sy + 9 * i / 40 - 60 * (i / 40) * (1 - i / 40)) for i in range(41)])
            assert all(y >= 31 for _, y in hoop)
            hoops.append(hoop)
            build += shown(px(hoop, acc), .02 + .02 * n, .95, 12)
            n += 1
        rails = [c for i in (0, len(hoops[0]) // 2, -1) for c in line(hoops[0][i], hoops[4][i])]
        build += shown(px(rails, acc, ' opacity=".55"'), .02 + .02 * (n - 1), .95, 12)
    loop = trace([P(4, 9), P(4, 0), P(8, 0), P(8, 9), P(4, 9)])
    assert all(2 <= x <= W - 3 and 20 <= y <= H - 3 for x, y in grid + loop)
    rover = [(i, j) for i in range(-2, 3) for j in range(-2, 3) if abs(i) + abs(j) < 4]

    def ring(r):
        return [(i, j) for i in range(-r, r + 1) for j in range(-r, r + 1)
                if max(abs(i), abs(j)) == r and abs(i) + abs(j) < 2 * r]

    bot = ('<g class="bl">' + px(ring(4), t["fg"], ' opacity=".7"') + '</g><g class="b2">'
           + px(ring(6), t["fg"], ' opacity=".4"') + "</g>" + px(rover, t["fg"]))
    steps = loop[:-1]
    drive = moved(bot, [(i / len(steps), p) for i, p in enumerate(steps)], 14)
    css = ".b2{animation:bl 1s steps(1) -.5s infinite}"
    body = (frame(t, W, H, "robotics & simulation", "04 / 04", [acc]) + px(grid, t["line"]) + build
            + px(loop[::3], t["fg"], ' opacity=".35"') + drive
            + text("digital twin → synthetic data → navigation", 8, 24, t["mute"]))
    return svg(W, H, "Robotics and simulation: a wireframe greenhouse with a robot driving the aisles.", css, body)


# ---- model merging (wide) -----------------------------------------------

WA = [.35, .61, .46, .66, .68, .21, .16, .86, .37, .35, 1, .55, .86, .55,
      .69, .28, .69, .89, .59, .78, .72, .20, .79, .65, .41, .18, .89, .55]
WB = [.76, .90, .76, .93, .49, .83, .53, .95, .90, .23, .27, .33, .97, .52,
      .68, .41, .58, .48, .45, .65, .65, .92, .73, .94, .88, .99, .72, .29]


def merge(t):
    W, H = 420, 95
    x0, y0, pitch, size = 172, 31, 11, 9

    def matrix(weights, colour):
        return "".join(
            f'<rect x="{(x0 + pitch * (i % 7))*C}" y="{(y0 + pitch * (i // 7))*C}" width="{size*C}" height="{size*C}" '
            f'fill="{colour}" fill-opacity="{w:.2f}"/>' for i, w in enumerate(weights))

    def slide(inner, sign):  # wait apart, step together, vanish into the merged grid, reappear apart
        far = 115 * sign
        hops = [(.12 + .3 * i / 23, (far - 5 * sign * i, 0)) for i in range(1, 24)]
        g = moved(inner, [(0, (far, 0))] + hops + [(.94, (far, 0))], 10)
        return f'<g opacity="1">{g}{anim("opacity", [(0, 1), (.46, 0), (.94, 1)], 10)}</g>'

    a = slide(matrix(WA, t["blue"]) + text("fine-tune A", 210, 80, t["mute"], center=True), -1)
    b = slide(matrix(WB, t["orange"]) + text("fine-tune B", 210, 80, t["mute"], center=True), 1)
    plus = shown(px(block(206, 49, 8, 2) + block(209, 46, 2, 8), t["fg"]), 0, .2, 10)
    merged = shown(matrix([(p + q) / 2 for p, q in zip(WA, WB)], t["purple"]), .46, .94, 10)
    notes = shown(
        text("merged = 0.5·A + 0.5·B", 210, 80, t["fg"], bold=True, center=True)
        + text("same architecture", 160, 44, t["mute"], right=True) + text("same starting point", 160, 54, t["mute"], right=True)
        + text("no new data", 261, 44, t["mute"]) + text("no extra training", 261, 54, t["mute"]), .5, .94, 10)
    body = frame(t, W, H, "model merging", "lately", [t["blue"], t["orange"]]) + a + b + plus + merged + notes
    return svg(W, H, "Model merging: the weights of two fine-tuned models slide together and are averaged into one.",
               "", body)


# ---- hero (wide, no frame) ----------------------------------------------

def hero(t):
    W, H, acc = 420, 100, t["blue"]
    title = "Hi, I'm Jems."
    hx, hy = 20, 32
    hw, hh = raster(title, "head")[1], cap("head")[1]  # heading size in cells (one font pixel per cell)
    bx0, by0, bx1, by1 = hx - 7, hy - 9, hx + hw + 6, hy + hh + 8  # detection box around the heading

    def brackets(e):  # corner brackets pushed out by e cells
        cells = []
        for cx, sx in ((bx0 - e, 1), (bx1 + e, -1)):
            for cy, sy in ((by0 - e, 1), (by1 + e, -1)):
                cells += block(min(cx, cx + sx * 9), min(cy, cy + sy), 10, 2) + block(min(cx, cx + sx), min(cy, cy + sy * 9), 2, 10)
        return px(cells, acc)

    fill = (f'<rect x="{bx0*C}" y="{by0*C}" width="{(bx1 - bx0 + 1)*C}" height="{(by1 - by0 + 1)*C}" '
            f'fill="{acc}" fill-opacity=".06"/>')
    lock = shown(brackets(8), 0, .03, 9) + shown(brackets(4), .03, .06, 9) + shown(fill + brackets(0), .06, .94, 9)
    label, _ = chips(t, "person: jems", 98, 13, 5, bx0, by0 - 9)
    scan = f'<rect class="sc" x="0" y="0" width="{W*C}" height="{C}" fill="{acc}"/>'

    X, step = 216, raster("m")[1]  # tagline: one font pixel per cell, so each character advances `step` cells
    lines = ["I teach cameras to notice things.", "Lately, also agents and robots."]
    ys, spans = [35, 48], [(0, .22), (.24, .42)]
    typed, cur_x = "", [(0, X)]
    for i, (s, y, (t0, t1)) in enumerate(zip(lines, ys, spans)):
        assert X + step * len(s) <= W - 2 and raster(s)[1] == step * len(s), s
        pairs = [(0, 0)] + [(t0 + (t1 - t0) * j / len(s), step * j * C) for j in range(1, len(s) + 1)]
        typed += (f'<clipPath id="t{i}"><rect x="{X*C}" y="{(y - 3)*C}" width="0" height="{13*C}">'
                  f'{anim("width", pairs, 9, .8)}</rect></clipPath>'
                  f'<g clip-path="url(#t{i})">{text(s, X, y, t["fg"], k=2)}</g>')
        cur_x += ([(t0, X)] if t0 else []) + [(t0 + (t1 - t0) * j / len(s), X + step * j + 1) for j in range(1, len(s) + 1)]
    cursor = (f'<rect class="bl" x="{X*C}" y="{(ys[0] - 1)*C}" width="{4*C}" height="{9*C}" fill="{t["fg"]}">'
              f'{anim("x", [(k_, v * C) for k_, v in cur_x], 9, .8)}'
              f'{anim("y", [(0, (ys[0] - 1) * C), (.24, (ys[1] - 1) * C)], 9, .8)}</rect>')
    tags = "computer vision · evaluation · agents · simulation"
    assert X + width(tags) <= W - 2 and bx1 + 8 < X, (X + width(tags), bx1)
    css = (".sc{animation:sc 9s steps(45) infinite}@keyframes sc{0%{transform:translateY(0);opacity:.7}"
           f"40%{{transform:translateY({(H - 5)*C}px);opacity:.7}}41%,100%{{transform:translateY({(H - 5)*C}px);opacity:0}}}}")
    body = (scan + text(title, hx, hy, t["fg"], font="head", k=2) + lock + shown(label, .08, .94, 9)
            + text("Chawin Sriviset · AI Engineer · Thailand", hx, 67, t["mute"], font="sub")
            + text("$ whoami", X, 25, t["mute"]) + typed + cursor + text(tags, X, 68, t["mute"]))
    return svg(W, H, "Hi, I'm Jems. Chawin Sriviset, AI Engineer in Thailand. I teach cameras to notice things. "
               "Lately, also agents and robots.", css, body, ".sc{opacity:0}")


TILES = dict(hero=hero, vision=vision, eval=evaluation, agent=agent, sim=simulation, merge=merge)

if __name__ == "__main__":
    out = pathlib.Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for name, make in TILES.items():
        for theme, t in THEMES.items():
            data = make(t)
            (out / f"{name}-{theme}.svg").write_text(data)
        print(f"{name:7} {len(data):6} bytes")
