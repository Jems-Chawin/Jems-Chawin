"""Build the animated SVGs for the profile README.

Run:  python3 scripts/build_assets.py
Writes assets/<name>-light.svg and assets/<name>-dark.svg for:
  hero    the name being "detected", with a typed line
  vision  three tracked objects
  eval    two precision/recall curves being drawn
  agent   an agent loop in a terminal
  sim     a wireframe greenhouse with a robot driving the aisle

Everything is plain SVG with CSS and SMIL animation, so GitHub can show it as
an image. No scripts, no external fonts, no network requests.
"""
import math
from html import escape
from pathlib import Path

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

THEMES = {
    "light": dict(fg="#1f2328", muted="#59636e", edge="#d1d9e0", soft="#f6f8fa",
                  cv="#1f6feb", ev="#8250df", ag="#bf5b04", sim="#1a7f37"),
    "dark": dict(fg="#f0f6fc", muted="#9198a1", edge="#3d444d", soft="#151b23",
                 cv="#4493f8", ev="#ab7df8", ag="#f0883e", sim="#3fb950"),
}

TW, TH = 412, 236  # tile size


def svg(w, h, label, style, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{label}">\n<style>{style}'
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
            f"</style>\n{body}\n</svg>\n")


def tile(t, colour, number, title, label, style, body):
    base = (f".k{{font:600 12px {MONO};fill:{t['fg']};letter-spacing:.04em}}"
            f".q{{font:400 11px {MONO};fill:{t['muted']}}}")
    frame = (f'<rect x=".5" y=".5" width="{TW - 1}" height="{TH - 1}" rx="10" fill="{t["soft"]}" stroke="{t["edge"]}"/>'
             f'<clipPath id="c"><rect x="1" y="38" width="{TW - 2}" height="{TH - 39}" rx="9"/></clipPath>'
             f'<circle cx="20" cy="21" r="5" fill="{colour}"/>'
             f'<text class="k" x="34" y="25">{escape(title)}</text>'
             f'<text class="q" x="{TW - 16}" y="25" text-anchor="end">{number} / 04</text>'
             f'<line x1="1" y1="38" x2="{TW - 1}" y2="38" stroke="{t["edge"]}"/>'
             f'<g clip-path="url(#c)">{body}</g>')
    return svg(TW, TH, label, base + style, frame)


# ---------------------------------------------------------------- hero

def hero(t):
    W, H = 840, 200
    c = t["cv"]
    line1 = "I teach cameras to notice things."
    line2 = "Lately, also agents and robots."
    style = (
        f".h{{font:700 46px {SANS};fill:{t['fg']}}}"
        f".s{{font:400 17px {SANS};fill:{t['muted']}}}"
        f".m{{font:400 16px {MONO};fill:{t['fg']}}}"
        f".tag{{font:600 12px {MONO};fill:#fff}}"
        f".q{{font:400 11px {MONO};fill:{t['muted']}}}"
        ".box{transform-box:fill-box;transform-origin:center;animation:lock 9s cubic-bezier(.2,.8,.2,1) infinite}"
        "@keyframes lock{0%{transform:scale(1.5);opacity:0}9%{transform:scale(1);opacity:1}"
        "92%{transform:scale(1);opacity:1}100%{transform:scale(1.04);opacity:0}}"
        ".lab{animation:lab 9s linear infinite}"
        "@keyframes lab{0%,9%{opacity:0}12%,92%{opacity:1}100%{opacity:0}}"
        ".scan{animation:scan 9s linear infinite}"
        "@keyframes scan{0%{transform:translateY(0);opacity:0}3%{opacity:.7}40%{transform:translateY(190px);opacity:0}100%{opacity:0}}"
        ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    )
    bx, by, bw, bh, L = 26, 46, 330, 70, 16
    corners = (f"M{bx},{by + L}V{by}H{bx + L} M{bx + bw - L},{by}H{bx + bw}V{by + L} "
               f"M{bx + bw},{by + bh - L}V{by + bh}H{bx + bw - L} M{bx + L},{by + bh}H{bx}V{by + bh - L}")
    tw1, tw2, tx = 308, 298, 462
    body = [
        f'<rect class="scan" x="0" y="4" width="{W}" height="1.5" fill="{c}"/>',
        f'<text class="h" x="40" y="98" textLength="302" lengthAdjust="spacingAndGlyphs">Hi, I\'m Jems.</text>',
        f'<g class="box"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{c}" fill-opacity=".06"/>'
        f'<path d="{corners}" fill="none" stroke="{c}" stroke-width="2.5"/></g>',
        f'<g class="lab"><rect x="{bx}" y="{by - 24}" width="176" height="20" rx="3" fill="{c}"/>'
        f'<text class="tag" x="{bx + 8}" y="{by - 10}">person: jems  0.99</text></g>',
        f'<text class="s" x="40" y="150">Chawin Sriviset · AI Engineer · Thailand</text>',
        f'<text class="q" x="{tx}" y="62">$ whoami</text>',
        # two typed lines, one after the other
        f'<clipPath id="a"><rect x="{tx}" y="74" height="24" width="0">'
        f'<animate attributeName="width" values="0;{tw1 + 2};{tw1 + 2}" keyTimes="0;.22;1" begin=".8s" dur="9s" repeatCount="indefinite"/></rect></clipPath>',
        f'<clipPath id="b"><rect x="{tx}" y="100" height="24" width="0">'
        f'<animate attributeName="width" values="0;0;{tw2 + 2};{tw2 + 2}" keyTimes="0;.24;.42;1" begin=".8s" dur="9s" repeatCount="indefinite"/></rect></clipPath>',
        f'<text class="m" x="{tx}" y="92" textLength="{tw1}" lengthAdjust="spacingAndGlyphs" clip-path="url(#a)">{line1}</text>',
        f'<text class="m" x="{tx}" y="118" textLength="{tw2}" lengthAdjust="spacingAndGlyphs" clip-path="url(#b)">{line2}</text>',
        f'<rect class="cur" x="{tx}" y="78" width="8" height="18" fill="{t["fg"]}">'
        f'<animate attributeName="x" values="{tx};{tx + tw1 + 4};{tx};{tx + tw2 + 4};{tx + tw2 + 4}" keyTimes="0;.22;.24;.42;1" calcMode="linear" begin=".8s" dur="9s" repeatCount="indefinite"/>'
        f'<animate attributeName="y" values="78;78;104;104" keyTimes="0;.23;.24;1" calcMode="discrete" begin=".8s" dur="9s" repeatCount="indefinite"/></rect>',
        f'<text class="q" x="{tx}" y="150">computer vision · evaluation · agents · simulation</text>',
    ]
    return svg(W, H, "Hi, I'm Jems. Chawin Sriviset, AI Engineer in Thailand. "
               "I teach cameras to notice things. Lately, also agents and robots.", style, "\n".join(body))


# ---------------------------------------------------------------- vision

def vision(t):
    c = t["cv"]
    style = (f".id{{font:600 9px {MONO};fill:{c}}}"
             ".sw{animation:sw 6s linear infinite}@keyframes sw{from{transform:translateX(-20px)}to{transform:translateX(430px)}}")
    tracks = [
        ("03", "0.97", "30,110;150,92;290,118;390,96;290,118;150,92;30,110", "13s"),
        ("07", "0.94", "380,170;250,186;120,164;40,190;120,164;250,186;380,170", "16s"),
        ("12", "0.91", "200,70;240,130;180,190;240,130;200,70", "11s"),
    ]
    body = [f'<g stroke="{t["edge"]}" stroke-width="1">'
            + "".join(f'<line x1="0" y1="{y}" x2="{TW}" y2="{y}"/>' for y in range(68, TH, 30))
            + "".join(f'<line x1="{x}" y1="38" x2="{x}" y2="{TH}"/>' for x in range(30, TW, 30)) + "</g>",
            f'<rect class="sw" x="0" y="38" width="2" height="{TH}" fill="{c}" opacity=".35"/>']
    for tid, conf, vals, dur in tracks:
        pts = vals.split(";")
        path = "M" + " L".join(p.replace(",", " ") for p in pts)
        body.append(f'<path d="{path}" fill="none" stroke="{c}" stroke-opacity=".25" stroke-dasharray="2 4"/>')
        body.append(
            f'<g><animateTransform attributeName="transform" type="translate" values="{vals.replace(",", " ")}" '
            f'dur="{dur}" repeatCount="indefinite"/>'
            f'<circle cx="0" cy="-15" r="5" fill="{t["muted"]}"/><rect x="-6" y="-8" width="12" height="22" rx="4" fill="{t["muted"]}"/>'
            f'<rect x="-15" y="-27" width="30" height="46" fill="{c}" fill-opacity=".08" stroke="{c}" stroke-width="1.5"/>'
            f'<text class="id" x="-15" y="-32">id {tid} · {conf}</text></g>')
    body.append(f'<text class="q" x="16" y="{TH - 12}">detect → track → count</text>')
    return tile(t, c, "01", "computer vision", "Computer vision: three objects being detected and tracked.",
                style, "".join(body))


# ---------------------------------------------------------------- evaluation

def evaluation(t):
    c = t["ev"]
    style = (".cv{stroke-dasharray:1;animation:draw 8s ease-in-out infinite}"
             ".cv2{animation-delay:.6s}"
             "@keyframes draw{0%{stroke-dashoffset:1}45%,90%{stroke-dashoffset:0}100%{stroke-dashoffset:1}}"
             ".ok{animation:ok 8s linear infinite}@keyframes ok{0%,50%{opacity:0}56%,90%{opacity:1}100%{opacity:0}}")
    x0, y0, x1, y1 = 46, 198, 388, 62
    grid = "".join(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{t["edge"]}" stroke-dasharray="2 4"/>'
                   for y in (96, 130, 164))
    body = [
        grid,
        f'<path d="M{x0} {y1}V{y0}H{x1}" fill="none" stroke="{t["muted"]}"/>',
        f'<text class="q" x="{x0}" y="54">precision</text>',
        f'<text class="q" x="{x1}" y="{y0 + 16}" text-anchor="end">recall</text>',
        f'<path class="cv cv2" pathLength="1" d="M{x0} 84 C150 86 250 100 310 138 S372 180 {x1} {y0}" '
        f'fill="none" stroke="{t["muted"]}" stroke-width="2"/>',
        f'<path class="cv" pathLength="1" d="M{x0} 70 C180 70 300 78 340 112 S380 160 {x1} {y0}" '
        f'fill="none" stroke="{c}" stroke-width="2.5"/>',
        f'<g class="ok"><circle cx="328" cy="103" r="5" fill="{c}"/>'
        f'<rect x="170" y="112" width="118" height="20" rx="3" fill="{c}"/>'
        f'<text x="178" y="126" style="font:600 11px {MONO};fill:#fff">clean test set ✓</text></g>',
        f'<text class="q" x="58" y="186">no leaks · hand-checked · reproducible</text>',
    ]
    return tile(t, c, "02", "data & evaluation",
                "Data and evaluation: two precision/recall curves drawn on a clean test set.", style, "".join(body))


# ---------------------------------------------------------------- agent

def agent(t):
    c = t["ag"]
    lines = [
        ("u", "> what did the team ship this week?"),
        ("p", "  plan    search → read → summarise"),
        ("p", "  tool    search_chat(\"shipped\")      ✓"),
        ("p", "  tool    read_thread(3)             ✓"),
        ("p", "  check   sources match, no guesses  ✓"),
        ("a", "< 3 releases, 1 blocker. Details sent."),
    ]
    style = [f".u{{font:400 12px {MONO};fill:{t['fg']}}}.p{{font:400 12px {MONO};fill:{t['muted']}}}"
             f".a{{font:600 12px {MONO};fill:{c}}}"]
    body = []
    for i, (cls, text) in enumerate(lines):
        a = 4 + i * 11
        style.append(f".l{i}{{animation:l{i} 10s linear infinite}}"
                     f"@keyframes l{i}{{0%,{a}%{{opacity:0}}{a + 2}%,93%{{opacity:1}}100%{{opacity:0}}}}")
        body.append(f'<text class="{cls} l{i}" x="18" y="{70 + i * 25}" xml:space="preserve">{escape(text, quote=False)}</text>')
    y = 70 + len(lines) * 25
    style.append(".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}")
    body.append(f'<rect class="cur" x="18" y="{y - 12}" width="7" height="14" fill="{c}"/>')
    return tile(t, c, "03", "llm & agents", "LLM agents: an agent plans, calls tools, checks its sources and answers.",
                "".join(style), "".join(body))


# ---------------------------------------------------------------- simulation

def simulation(t):
    c = t["sim"]
    s, ox, oy = 13.5, 192, 84
    cos30, sin30 = math.cos(math.radians(30)), 0.5

    def iso(x, y, z=0):
        return ox + (x - y) * cos30 * s, oy + (x + y) * sin30 * s - z * s

    def p(x, y, z=0):
        a, b = iso(x, y, z)
        return f"{a:.1f} {b:.1f}"

    style = (".w{stroke-dasharray:1;animation:build 12s ease-in-out infinite}"
             "@keyframes build{0%{stroke-dashoffset:1}30%,92%{stroke-dashoffset:0}100%{stroke-dashoffset:1}}"
             ".ring{transform-box:fill-box;transform-origin:center;animation:ring 1.6s ease-out infinite}"
             "@keyframes ring{from{transform:scale(.4);opacity:.9}to{transform:scale(1.8);opacity:0}}")
    NX, NY = 12, 9
    body = ['<g stroke="%s" stroke-width="1">' % t["edge"]]
    for i in range(NX + 1):
        body.append(f'<path d="M{p(i, 0)}L{p(i, NY)}"/>')
    for j in range(NY + 1):
        body.append(f'<path d="M{p(0, j)}L{p(NX, j)}"/>')
    body.append("</g>")
    # three tunnels along y, 3 wide, with a 1.5-wide aisle between them
    k = 0
    for x0 in (0.5, 4.5, 8.5):
        w, h = 3, 2.4
        for y in (0.5, 2.5, 4.5, 6.5, 8.5):
            delay = k * 0.12
            k += 1
            ax, ay = iso(x0, y)
            mx, my = iso(x0 + w / 2, y, h * 1.9)
            bx, by = iso(x0 + w, y)
            body.append(f'<path class="w" style="animation-delay:{delay:.2f}s" pathLength="1" '
                        f'd="M{ax:.1f} {ay:.1f}Q{mx:.1f} {my:.1f} {bx:.1f} {by:.1f}" fill="none" stroke="{c}" stroke-width="1.5"/>')
        for dx, z in ((0, 0), (w / 2, h * 0.95), (w, 0)):
            body.append(f'<path class="w" style="animation-delay:{k * 0.12:.2f}s" pathLength="1" '
                        f'd="M{p(x0 + dx, 0.5, z)}L{p(x0 + dx, 8.5, z)}" fill="none" stroke="{c}" stroke-opacity=".55"/>')
    # robot drives the aisle between the first two tunnels, then the next one
    route = f"M{p(4, 9)}L{p(4, 0)}L{p(8, 0)}L{p(8, 9)}L{p(4, 9)}"
    body.append(f'<path d="{route}" fill="none" stroke="{t["fg"]}" stroke-opacity=".35" stroke-dasharray="3 4"/>')
    body.append(f'<g><animateMotion dur="14s" repeatCount="indefinite" path="{route}"/>'
                f'<circle class="ring" r="9" fill="none" stroke="{t["fg"]}" stroke-width="1.5"/>'
                f'<circle r="4.5" fill="{t["fg"]}"/></g>')
    body.append(f'<text class="q" x="16" y="58">digital twin → synthetic data → navigation</text>')
    return tile(t, c, "04", "robotics & simulation",
                "Robotics and simulation: a wireframe greenhouse with a robot driving the aisles.", style, "".join(body))


# ---------------------------------------------------------------- merge

def merge(t):
    """Two weight grids slide together and become one: 0.5*A + 0.5*B."""
    import random
    W, H = 840, 190
    ca, cb = t["cv"], t["ag"]
    rng = random.Random(3)
    cols, rows, cell, gap = 7, 4, 18, 4
    gw = cols * (cell + gap) - gap
    wa = [[rng.uniform(.15, 1) for _ in range(cols)] for _ in range(rows)]
    wb = [[rng.uniform(.15, 1) for _ in range(cols)] for _ in range(rows)]
    mid, top, shift = (W - gw) / 2, 62, 230

    def grid(x, layers):
        out = []
        for r in range(rows):
            for c in range(cols):
                for colour, w in layers:
                    out.append(f'<rect x="{x + c * (cell + gap):.0f}" y="{top + r * (cell + gap)}" width="{cell}" '
                               f'height="{cell}" rx="3" fill="{colour}" fill-opacity="{w[r][c]:.2f}"/>')
        return "".join(out)

    style = (
        f".k{{font:600 12px {MONO};fill:{t['fg']};letter-spacing:.04em}}"
        f".q{{font:400 11px {MONO};fill:{t['muted']}}}"
        f".f{{font:600 14px {MONO};fill:{t['fg']}}}"
        ".a{animation:a 10s ease-in-out infinite}.b{animation:b 10s ease-in-out infinite}"
        f"@keyframes a{{0%,12%{{transform:translateX(-{shift}px);opacity:1}}42%{{transform:translateX(0);opacity:1}}"
        f"50%,92%{{transform:translateX(0);opacity:0}}100%{{transform:translateX(-{shift}px);opacity:0}}}}"
        f"@keyframes b{{0%,12%{{transform:translateX({shift}px);opacity:1}}42%{{transform:translateX(0);opacity:1}}"
        f"50%,92%{{transform:translateX(0);opacity:0}}100%{{transform:translateX({shift}px);opacity:0}}}}"
        ".m{transform-box:fill-box;transform-origin:center;animation:m 10s ease-out infinite}"
        "@keyframes m{0%,42%{opacity:0;transform:scale(.9)}50%{opacity:1;transform:scale(1.06)}"
        "56%,92%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(1)}}"
        ".plus{animation:plus 10s linear infinite}@keyframes plus{0%,10%{opacity:1}30%,100%{opacity:0}}"
        ".res{animation:res 10s linear infinite}@keyframes res{0%,50%{opacity:0}56%,92%{opacity:1}100%{opacity:0}}"
    )
    cx = W / 2
    body = [
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{t["soft"]}" stroke="{t["edge"]}"/>',
        f'<circle cx="20" cy="21" r="5" fill="{ca}"/><circle cx="29" cy="21" r="5" fill="{cb}" fill-opacity=".85"/>',
        f'<text class="k" x="44" y="25">model merging</text>',
        f'<text class="q" x="{W - 16}" y="25" text-anchor="end">lately</text>',
        f'<line x1="1" y1="38" x2="{W - 1}" y2="38" stroke="{t["edge"]}"/>',
        f'<g class="a">{grid(mid, [(ca, wa)])}<text class="q" x="{cx}" y="{top + 106}" text-anchor="middle">fine-tune A</text></g>',
        f'<g class="b">{grid(mid, [(cb, wb)])}<text class="q" x="{cx}" y="{top + 106}" text-anchor="middle">fine-tune B</text></g>',
        f'<text class="f plus" x="{cx}" y="{top + 48}" text-anchor="middle">+</text>',
        f'<g class="m">{grid(mid, [(t["ev"], [[(x + y) / 2 for x, y in zip(ra, rb)] for ra, rb in zip(wa, wb)])])}</g>',
        f'<text class="f res" x="{cx}" y="{top + 108}" text-anchor="middle">merged = 0.5·A + 0.5·B</text>',
        f'<text class="q res" x="{cx + gw / 2 + 28}" y="{top + 38}">no new data</text>',
        f'<text class="q res" x="{cx + gw / 2 + 28}" y="{top + 56}">no extra training</text>',
        f'<text class="q res" x="{cx - gw / 2 - 28}" y="{top + 38}" text-anchor="end">same architecture</text>',
        f'<text class="q res" x="{cx - gw / 2 - 28}" y="{top + 56}" text-anchor="end">same starting point</text>',
    ]
    return svg(W, H, "Model merging: the weights of two fine-tuned models slide together and are averaged into one.",
               style, "\n".join(body))


BUILDERS = dict(hero=hero, vision=vision, eval=evaluation, agent=agent, sim=simulation, merge=merge)

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for name, fn in BUILDERS.items():
        for theme, t in THEMES.items():
            (out / f"{name}-{theme}.svg").write_text(fn(t), encoding="utf-8")
    print("wrote", len(BUILDERS) * 2, "files to", out)
