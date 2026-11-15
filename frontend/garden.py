"""Builds the walkable garden roadmap (one self-contained HTML/SVG page) for the Streamlit iframe."""
import html
import math
import random

W, CX, AMP = 700, 350, 105
DY, GAP, TOP, BOTTOM = 128, 96, 180, 380


# ---------- plant library -------------------------------------------------------------------------------
def _lin(name, base, tip):
    return (f'<linearGradient id="g-{name}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{base}"/>'
            f'<stop offset="1" stop-color="{tip}"/></linearGradient>')


GRADS = "".join(_lin(*g) for g in [
    ("pink", "#E0708E", "#FCD6DF"), ("rose", "#A8264C", "#F08FA8"), ("white", "#EDE3A0", "#FFFFFF"),
    ("lav", "#6F4CA8", "#CDB4EA"), ("poppy", "#A81818", "#FF7A55"), ("peony", "#D4568A", "#FFD6E2"),
    ("butter", "#E3AE2E", "#FFF2A8"), ("fox", "#8C3F8C", "#F4BFE6"), ("leaf", "#4F7D3F", "#A9D08A"),
    ("wall", "#FBEFE6", "#EBD3C8"), ("roof", "#B97687", "#8E5568"), ("wood", "#A9794F", "#7F5A38")])
GRADS += ('<radialGradient id="g-tree" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#A5D180"/>'
          '<stop offset="1" stop-color="#4F7D3F"/></radialGradient>'
          '<radialGradient id="g-glow"><stop offset="0" stop-color="#FFF3B0" stop-opacity=".85"/>'
          '<stop offset="1" stop-color="#FFF3B0" stop-opacity="0"/></radialGradient>'
          '<radialGradient id="g-dark"><stop offset="0" stop-color="#5F8F4B" stop-opacity=".55"/>'
          '<stop offset="1" stop-color="#5F8F4B" stop-opacity="0"/></radialGradient>'
          '<radialGradient id="g-light"><stop offset="0" stop-color="#D5EBB0" stop-opacity=".7"/>'
          '<stop offset="1" stop-color="#D5EBB0" stop-opacity="0"/></radialGradient>'
          '<linearGradient id="g-mist" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#EEF4E6" stop-opacity="0"/>'
          '<stop offset="1" stop-color="#EEF4E6" stop-opacity=".66"/></linearGradient>'
          '<linearGradient id="g-ray" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF6C8" stop-opacity=".0"/>'
          '<stop offset=".5" stop-color="#FFF6C8" stop-opacity=".22"/><stop offset="1" stop-color="#FFF6C8" stop-opacity="0"/></linearGradient>'
          '<linearGradient id="g-edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3E6A33" stop-opacity=".4"/>'
          '<stop offset="1" stop-color="#3E6A33" stop-opacity="0"/></linearGradient>')


def _stem(h, col="#5F8F4B", w=2.6):
    return f'<path d="M0 0C-3 {-h * .35:.0f} 3 {-h * .7:.0f} 0 {-h}" stroke="{col}" stroke-width="{w}" fill="none" stroke-linecap="round"/>'


def _leaf(x, y, rot, s=1.0):
    return (f'<path d="M0 0C6-7 16-7 24 0C16 6 6 6 0 0Z" fill="url(#g-leaf)" '
            f'transform="translate({x} {y}) rotate({rot}) scale({s})"/>')


def _ring(n, cy, rx, ry, fill, a0=0):
    return "".join(f'<ellipse cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" transform="rotate({a0 + k * 360 / n:.1f})"/>'
                   for k in range(n))


def _daisy(g):
    head = _ring(14, -8, 2.4, 8.5, "url(#g-white)") + '<circle r="4.6" fill="#F0B63A"/><circle r="2" fill="#C98A1A"/>'
    return _stem(50) + _leaf(0, -10, -150) + _leaf(0, -18, -30, .9) + f'<g transform="translate(0 -52)">{head}</g>'


def _rose(g):
    f = f"url(#g-{g})"
    head = (f'<circle r="12.5" fill="{f}" stroke="#00000022" stroke-width=".6"/><circle r="9" fill="{f}" transform="rotate(180)"/>'
            '<path d="M-4-3C2-8 8-2 4 3C0 7-6 4-5-1C-4-5 1-4 1-1" stroke="#00000014" fill="none" stroke-width=".8"/><circle r="3.5" fill="#fff" opacity=".18"/>'
            '<ellipse cx="-4" cy="-6" rx="4" ry="2.4" fill="#fff" opacity=".3"/>')
    return _stem(54) + _leaf(0, -14, -160) + _leaf(0, -24, -20, .9) + f'<g transform="translate(0 -56)">{head}</g>'


def _tulip(g):
    f = f"url(#g-{g})"
    cup = (f'<path d="M-11-48C-13-66-4-74 0-62C4-74 13-66 11-48C7-39-7-39-11-48Z" fill="{f}"/>'
           '<path d="M0-62C-3-52-2-44 0-41C2-44 3-52 0-62Z" fill="#fff" opacity=".2"/>')
    return (_stem(46) + '<path d="M0 0C-14-10-16-30-8-44C-4-28-2-12 0 0Z" fill="url(#g-leaf)"/>'
            '<path d="M0 0C14-8 17-26 9-38C5-24 2-10 0 0Z" fill="url(#g-leaf)"/>' + cup)


def _peony(g):
    f = f"url(#g-{g})"
    head = (_ring(9, -10, 8.5, 11, f) + _ring(7, -6, 6, 8, f, 20) + _ring(5, -3, 4, 5.5, f, 10) + '<circle r="2.6" fill="#F6D26B"/>')
    return _stem(48) + _leaf(0, -12, -155) + _leaf(0, -22, -25, .9) + f'<g transform="translate(0 -50)">{head}</g>'


def _poppy(g):
    dots = "".join(f'<circle cx="{5 * math.cos(k):.1f}" cy="{5 * math.sin(k):.1f}" r=".9" fill="#2B2024"/>' for k in range(0, 7))
    head = _ring(5, -8, 9, 9.5, "url(#g-poppy)") + '<circle r="4" fill="#2B2024"/>' + dots
    return _stem(52, "#6F9A5A", 1.8) + _leaf(0, -8, -160, .8) + f'<g transform="translate(0 -54)">{head}</g>'


def _lavender(g):
    sp = "".join(f'<ellipse cx="-3" cy="{-24 - k * 4.4:.1f}" rx="3.2" ry="2" fill="url(#g-lav)" transform="rotate(-25 -3 {-24 - k * 4.4:.1f})"/>'
                 f'<ellipse cx="3" cy="{-24 - k * 4.4:.1f}" rx="3.2" ry="2" fill="url(#g-lav)" transform="rotate(25 3 {-24 - k * 4.4:.1f})"/>'
                 for k in range(9))
    return _stem(60, "#7C9A66", 2) + _leaf(0, -4, -165, .7) + _leaf(0, -8, -15, .7) + sp + '<ellipse cy="-64" rx="2.4" ry="3.4" fill="#8E6BC0"/>'


def _fox(g):
    bells = "".join(
        f'<path d="M0 0C-5 2-6 9-3 11H3C6 9 5 2 0 0Z" fill="url(#g-fox)" transform="translate({(1 if k % 2 else -1) * 5.5} {-28 - k * 6.8:.1f}) '
        f'scale({1 - k * .07:.2f}) rotate({(1 if k % 2 else -1) * -14})"/>' for k in range(8))
    return _stem(80, "#6F9A5A", 2.4) + _leaf(0, -6, -160, 1.1) + _leaf(0, -12, -20, 1.1) + bells + '<circle cy="-84" r="2.4" fill="#C77FC0"/>'


def _hydr(g):
    balls = "".join(
        f'<circle cx="{14 * math.sqrt(k / 22) * math.cos(k * 2.4):.1f}" cy="{-34 + 14 * math.sqrt(k / 22) * math.sin(k * 2.4):.1f}" r="4.4" '
        f'fill="url(#g-{"lav" if k % 3 else "pink"})"/>' for k in range(22))
    return _stem(30) + _leaf(0, -8, -170, 1.2) + _leaf(0, -12, -10, 1.2) + balls


SPECIES = {"daisy": _daisy, "rose": _rose, "tulip": _tulip, "peony": _peony, "poppy": _poppy,
           "lavender": _lavender, "fox": _fox, "hydr": _hydr}
COMBOS = [("daisy", "w"), ("rose", "rose"), ("rose", "pink"), ("tulip", "pink"), ("tulip", "butter"), ("tulip", "poppy"),
          ("peony", "peony"), ("poppy", "poppy"), ("lavender", "lav"), ("fox", "fox"), ("hydr", "lav")]
IDS = [f"p-{s}-{g}" for s, g in COMBOS]
SHADOW = '<ellipse cy="1" rx="12" ry="3.2" fill="#2E4A24" opacity=".2"/>'

DEFS = ("<defs>" + GRADS + "".join(f'<g id="p-{s}-{g}">{SHADOW}{SPECIES[s](g)}</g>' for s, g in COMBOS) + """
<g id="bud">""" + SHADOW + """<path d="M0 0C-3-16 3-26 0-38" stroke="#5F8F4B" stroke-width="3" fill="none"/>
<path d="M0-38C-9-44-7-58 0-62C7-58 9-44 0-38Z" fill="url(#g-pink)"/>""" + _leaf(0, -14, -160, .8) + _leaf(0, -20, -20, .7) + """</g>
<g id="sprout">""" + _stem(16, "#7FA070", 2.2) + _leaf(0, -14, -150, .45) + _leaf(0, -16, -30, .45) + """</g>
<g id="tuft"><path d="M-7 0Q-7-10-12-15M-3 0Q-3-13-5-19M0 0Q0-12 1-21M4 0Q4-12 8-17M8 0Q8-9 13-12" stroke="#6F9F55"
stroke-width="1.8" fill="none" stroke-linecap="round"/></g>
<g id="blades"><path d="M-6 0Q-5-10-9-16M0 0Q0-14 2-22M5 0Q6-10 11-14" stroke="#5E8F48" stroke-width="1.6" fill="none"
stroke-linecap="round"/><path d="M-2 0Q-2-8-4-12M3 0Q4-9 6-13" stroke="#8DBB6B" stroke-width="1.4" fill="none" stroke-linecap="round"/></g>
</defs>""")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Caveat:wght@600&family=Nunito:wght@400;600&display=swap');
html,body{margin:0;background:#EEF4E6}
.wrap{position:relative;width:100%;max-width:700px;margin:0 auto;container-type:inline-size;overflow:hidden;border-radius:22px}
svg{position:absolute;inset:0;width:100%;height:100%}
.lb{position:absolute;max-width:27%;transform:translateY(-60%);font:400 clamp(10px,2.1cqw,14px)/1.25 'Nunito',sans-serif;
 color:#5B4448;background:rgba(255,250,244,.94);border:1.5px solid #EBC8D0;border-radius:12px;padding:.35em .65em;box-shadow:0 2px 8px rgba(60,80,40,.18)}
.lb .n{font:600 1.25em 'Caveat',cursive;color:#B5657D;margin-right:.25em}
.lb.done{background:#FCE9ED;border-color:#E9A3B5}
.lb.sel{border:2px solid #D98BA0;box-shadow:0 4px 14px rgba(217,139,160,.5);font-weight:600}
.ch{position:absolute;left:10%;width:80%;transform:translateY(-50%);text-align:center;background:rgba(255,252,248,.95);
 border:2px solid #B7C99F;border-radius:16px;padding:.4em .6em;color:#5B4448;box-shadow:0 3px 10px rgba(60,80,40,.2)}
.ch.full{background:#FCE9ED;border-color:#E27D98}
.ch small{display:block;font:600 clamp(13px,3.2cqw,19px) 'Caveat',cursive;color:#B5657D}
.ch b{font:600 clamp(13px,2.9cqw,18px) 'Fraunces',serif}
.hello{position:absolute;left:0;right:0;text-align:center;font:600 clamp(16px,4cqw,26px) 'Caveat',cursive;color:#fff;
 text-shadow:0 1px 4px rgba(40,70,30,.7)}
.sway{transform-box:fill-box;transform-origin:50% 100%;animation:sway 4.5s ease-in-out infinite alternate}
.pop{transform-box:fill-box;transform-origin:50% 100%;animation:pop .9s cubic-bezier(.2,1.3,.4,1) both}
.bob{animation:bob 1.4s ease-in-out infinite alternate}.fly{animation:fly 3s ease-in-out infinite alternate}
.drift{animation:drift 11s linear infinite}.bee{animation:bee 5s ease-in-out infinite alternate}
.smoke{animation:rise 4s ease-out infinite}
@keyframes sway{from{transform:rotate(-2.5deg)}to{transform:rotate(2.5deg)}}
@keyframes pop{from{transform:scale(0)}to{transform:scale(1)}}
@keyframes bob{to{transform:translateY(-3px)}}@keyframes fly{to{transform:translate(8px,-10px)}}
@keyframes drift{from{transform:translate(0,0) rotate(0);opacity:0}15%{opacity:.9}to{transform:translate(70px,150px) rotate(220deg);opacity:0}}
@keyframes bee{25%{transform:translate(22px,-12px)}50%{transform:translate(-10px,-26px)}to{transform:translate(30px,6px)}}
@keyframes rise{from{opacity:.7;transform:translateY(0)}to{opacity:0;transform:translateY(-30px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


# ---------- geometry helpers ----------------------------------------------------------------------------
def _bez(p0, p1, t):
    (x0, y0), (x1, y1), ym, m = p0, p1, (p0[1] + p1[1]) / 2, 1 - t
    return (m ** 3 * x0 + 3 * m * m * t * x0 + 3 * m * t * t * x1 + t ** 3 * x1,
            m ** 3 * y0 + 3 * m * m * t * ym + 3 * m * t * t * ym + t ** 3 * y1)


def _path_x(y, pts):
    if y <= pts[0][1]:
        return pts[0][0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return x0 + (x1 - x0) * t * t * (3 - 2 * t)
    return pts[-1][0]


def _plant(x, y, ref, sc, rnd, grow=True):
    g = f'<g class="sway" style="animation-delay:{-rnd.random() * 4:.1f}s"><use xlink:href="#{ref}" transform="scale({sc:.2f})"/></g>'
    if grow:
        g = f'<g class="pop" style="animation-delay:{rnd.random() * 1.4:.2f}s">{g}</g>'
    return f'<g transform="translate({x:.0f} {y:.0f})">{g}</g>'


def _tree(x, y, r, bloom, rnd):
    out = [f'<ellipse cy="{r * .85:.0f}" rx="{r * 1.05:.0f}" ry="{r * .28:.0f}" fill="#2E4A24" opacity=".25"/>']
    for dx, dy, rr in [(-.45, -.2, .7), (.45, -.25, .75), (0, -.55, .8), (-.2, .1, .65), (.3, .05, .6)]:
        out.append(f'<circle cx="{dx * r:.0f}" cy="{dy * r:.0f}" r="{rr * r:.0f}" fill="url(#g-tree)"/>')
    if bloom:
        for _ in range(26):
            a, d = rnd.uniform(0, 6.28), r * rnd.uniform(.1, .95)
            out.append(f'<circle cx="{d * math.cos(a):.0f}" cy="{-.3 * r + d * .8 * math.sin(a):.0f}" r="{rnd.uniform(2.2, 4):.1f}" '
                       f'fill="{rnd.choice(["#FBD3DC", "#F4A6B8", "#FFFFFF", "#FBD3DC"])}"/>')
    return f'<g transform="translate({x:.0f} {y:.0f})">{"".join(out)}</g>'


# ---------- the scene -----------------------------------------------------------------------------------
def scene(data, cur):
    pts, topics, banners, y = [], [], [], TOP
    for si, s in enumerate(data["sections"]):
        y += GAP if si else 90
        banners.append((si, y))
        for t in s["topics"]:
            pts.append((CX + (AMP if len(pts) % 2 else -AMP), y))
            topics.append((si, t))
            y += DY
    n, H = len(pts), y - DY + BOTTOM
    done_ix = [i for i, (_, t) in enumerate(topics) if t["status"] == "done"]
    all_done = len(done_ix) == n
    frontier = pts[max(done_ix)][1] if done_ix else TOP
    cx, cy = pts[cur]
    rnd = random.Random(data["slug"])
    bg, ground, objs, top_layer, labels = [], [], [], [], []

    # lawn: tonal patches and grass blades
    bg.append(f'<rect width="{W}" height="{H}" fill="#A9CB8B"/><g>')
    for _ in range(int(H / 55)):
        px, py, pr = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(60, 150)
        bg.append(f'<ellipse cx="{px:.0f}" cy="{py:.0f}" rx="{pr:.0f}" ry="{pr * .55:.0f}" fill="url(#g-{"dark" if rnd.random() < .5 else "light"})"/>')
    bg.append("</g>")
    for _ in range(int(H / 6)):
        bg.append(f'<use xlink:href="#blades" transform="translate({rnd.uniform(0, W):.0f} {rnd.uniform(0, H):.0f}) scale({rnd.uniform(.7, 1.5):.2f})"/>')

    # trees along both edges (they blossom behind the frontier)
    ty = TOP + 20
    while ty < H - 200:
        for side in (0, 1):
            r = rnd.uniform(46, 70)
            tx = rnd.uniform(-10, 24) if side == 0 else rnd.uniform(W - 24, W + 10)
            objs.append((ty + r * .85, _tree(tx, ty + rnd.uniform(-30, 30), r, ty <= frontier, rnd)))
        ty += rnd.uniform(190, 250)

    # cobblestone path (pink-petalled where you've walked)
    route = [(CX, 125)] + pts + [(CX, H - 100)]
    for j in range(len(route) - 1):
        p0, p1 = route[j], route[j + 1]
        walked = j == 0 or topics[j - 1][1]["status"] == "done"
        d = f"M{p0[0]} {p0[1]} C{p0[0]} {(p0[1] + p1[1]) / 2} {p1[0]} {(p0[1] + p1[1]) / 2} {p1[0]} {p1[1]}"
        ground.append(f'<path d="{d}" fill="none" stroke="#5E8F48" stroke-opacity=".4" stroke-width="58" stroke-linecap="round"/>'
                      f'<path d="{d}" fill="none" stroke="{"#DDC6A6" if walked else "#CFC2AE"}" stroke-width="44" stroke-linecap="round"/>')
        k = max(4, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * 1.12 / 15))
        for i in range(k + 1):
            t = i / k
            x, yy = _bez(p0, p1, t)
            xa, ya = _bez(p0, p1, max(t - .02, 0))
            xb, yb = _bez(p0, p1, min(t + .02, 1))
            ang = math.atan2(yb - ya, xb - xa)
            for off in (-10, 10):
                sx = x - math.sin(ang) * off + rnd.uniform(-3, 3)
                sy = yy + math.cos(ang) * off + rnd.uniform(-3, 3)
                col = rnd.choice(["#EAD7BF", "#E0CBB2", "#F2E3D1"] if walked else ["#D2C7B5", "#C4B9A7", "#DCD2C2"])
                ground.append(f'<ellipse cx="{sx:.0f}" cy="{sy:.0f}" rx="{rnd.uniform(6, 8.5):.1f}" ry="{rnd.uniform(4.5, 6):.1f}" fill="{col}" '
                              f'stroke="#8A7560" stroke-opacity=".28" stroke-width=".7" transform="rotate({math.degrees(ang) + rnd.uniform(-25, 25):.0f} {sx:.0f} {sy:.0f})"/>')
            if walked and rnd.random() < .45:
                ground.append(f'<ellipse cx="{x + rnd.uniform(-16, 16):.0f}" cy="{yy + rnd.uniform(-6, 6):.0f}" rx="2.6" ry="1.4" fill="#F4A6B8" opacity=".85"/>')

    # plants: filler wildflowers, per-stop bouquets, chapter garlands, gate
    fy = TOP + 60
    while fy < H - 260:
        for _ in range(2):
            fx = rnd.uniform(26, W - 26)
            if abs(fx - _path_x(fy, pts)) < 54:
                continue
            if fy <= frontier:
                objs.append((fy, _plant(fx, fy, rnd.choice(IDS), rnd.uniform(.5, .85), rnd)))
            else:
                objs.append((fy, _plant(fx, fy, rnd.choice(["tuft", "sprout"]), rnd.uniform(.9, 1.2), rnd, False)))
        fy += 28

    for i, (si, t) in enumerate(topics):
        x, yy = pts[i]
        stt = t["status"]
        ground.append(f'<ellipse cx="{x}" cy="{yy}" rx="19" ry="10" fill="#EAD7BF" stroke="#8A7560" stroke-opacity=".35" stroke-width="1.2"/>')
        if i == cur:
            ground.append(f'<ellipse cx="{x}" cy="{yy}" rx="40" ry="22" fill="url(#g-glow)"/>'
                          f'<ellipse cx="{x}" cy="{yy}" rx="26" ry="14" fill="none" stroke="#D98BA0" stroke-width="2.5" stroke-dasharray="5 5"/>')
        mine = [IDS[(si * 2) % len(IDS)], IDS[(si * 2 + 1) % len(IDS)]]
        if stt == "done":
            for k in range(10):
                dx = rnd.choice([-1, 1]) * rnd.uniform(18, 52)
                ref = rnd.choice(mine) if rnd.random() < .55 else rnd.choice(IDS)
                objs.append((yy + rnd.uniform(-8, 16), _plant(x + dx, yy + rnd.uniform(-8, 16), ref, rnd.uniform(.75, 1.15), rnd)))
        elif stt == "in_progress":
            for dx, ref, sc in [(-30, "bud", 1), (28, "bud", .9), (-48, rnd.choice(IDS), .55), (46, "sprout", 1.2)]:
                objs.append((yy + 6, _plant(x + dx, yy + 6, ref, sc, rnd)))
        else:
            for dx in (-30, 30):
                objs.append((yy + 6, _plant(x + dx, yy + 6, "sprout", 1.1, rnd, False)))
        glyph = {"done": "🌸", "in_progress": "🌱"}.get(stt, "")
        side = f"left:{(x + 40) / W * 100:.2f}%" if x > CX else f"right:{(W - x + 40) / W * 100:.2f}%;text-align:right"
        cls = "lb" + (" done" if stt == "done" else "") + (" sel" if i == cur else "")
        labels.append(f'<div class="{cls}" style="top:{yy / H * 100:.2f}%;{side}"><span class="n">{i + 1}</span>'
                      f'{html.escape(t["title"])} {glyph}</div>')

    labels.append('<div class="hello" style="top:%.2f%%">begin your walk 🌿</div>' % (160 / H * 100))
    arch = f'<path d="M-72 62V0Q0-52 72 0V62" stroke="#6F9A5A" stroke-width="7" fill="none" stroke-linecap="round"/>'
    blooms = "".join(_plant(CX + gx, 70 + gy, IDS[(k * 3) % len(IDS)], .45, rnd) for k, (gx, gy) in enumerate(
        [(-70, 56), (-68, 18), (-40, -20), (0, -38), (40, -20), (68, 18), (70, 56)]))
    objs.append((70, f'<g transform="translate({CX} 70)">{arch}</g>' + blooms))

    for si, by in banners:
        s = data["sections"][si]
        got = sum(t["status"] == "done" for t in s["topics"])
        full = got == len(s["topics"])
        top = by - 95
        top_y = lambda u: top - 18 + 64 * u * (1 - u)
        vine = f'<path d="M70 {top - 18} Q350 {top + 14} 630 {top - 18}" stroke="#6F9A5A" stroke-width="4" fill="none"/>'
        objs.append((top, vine))
        for k in range(9):
            u = k / 8
            ref = rnd.choice([IDS[(si * 2) % len(IDS)], IDS[(si * 2 + 1) % len(IDS)], IDS[(si * 2 + 4) % len(IDS)]]) if full else "tuft"
            objs.append((top + 1, _plant(70 + 560 * u, top_y(u) + 8, ref, .42 if full else 1, rnd, full)))
        labels.append(f'<div class="ch{" full" if full else ""}" style="top:{top / H * 100:.2f}%"><small>Chapter {si + 1} · '
                      f'{got}/{len(s["topics"])} blooming</small><b>{html.escape(s["title"])}</b></div>')

    # the cottage and its picket fence
    glow = "#FFD98A" if all_done else "#CFC4B8"
    smoke = "".join(f'<circle class="smoke" cx="46" cy="-92" r="{5 + k * 2}" fill="#fff" style="animation-delay:{-k * 1.3}s"/>'
                    for k in range(3)) if all_done else ""
    pickets = "".join(f'<path d="M{x} 74V54L{x + 4} 48L{x + 8} 54V74Z" fill="#FFFDF8" stroke="#E0D5C4" stroke-width="1"/>'
                      for x in list(range(-150, -34, 13)) + list(range(36, 152, 13)))
    boxes = "".join(_plant(bx, 33, rnd.choice(IDS), .32, rnd, False) for bx in (-56, -46, -36, 36, 46, 56))
    objs.append((H - 100, f'<g transform="translate({CX} {H - 172})"><ellipse cy="76" rx="120" ry="14" fill="#2E4A24" opacity=".22"/>'
                 '<rect x="-72" y="-20" width="144" height="92" rx="5" fill="url(#g-wall)" stroke="#D9B9AE" stroke-width="2"/>'
                 '<path d="M-98-16L0-94L98-16Z" fill="url(#g-roof)"/><path d="M-70-22Q0-80 70-22M-52-34Q0-76 52-34" stroke="#00000022" fill="none"/>'
                 '<rect x="38" y="-86" width="16" height="38" fill="#9A6A58"/><rect x="35" y="-90" width="22" height="7" fill="#7F5444"/>'
                 '<path d="M-17 72V34Q0 12 17 34V72Z" fill="url(#g-wood)"/><circle cx="9" cy="54" r="2" fill="#E8C98E"/>'
                 f'<rect x="-62" y="2" width="30" height="28" rx="3" fill="{glow}" stroke="#7F5A38" stroke-width="3"/>'
                 f'<rect x="32" y="2" width="30" height="28" rx="3" fill="{glow}" stroke="#7F5A38" stroke-width="3"/>'
                 '<path d="M-47 2V30M-62 16H-32M47 2V30M32 16H62" stroke="#7F5A38" stroke-width="2"/>'
                 f'<rect x="-64" y="30" width="34" height="7" fill="url(#g-wood)"/><rect x="30" y="30" width="34" height="7" fill="url(#g-wood)"/>'
                 f'{boxes}{pickets}{smoke}</g>'))
    labels.append('<div class="hello" style="top:%.2f%%">%s</div>' % (
        (H - 52) / H * 100, "home at last — everything is in bloom 🌸" if all_done else "the cottage waits at the end"))

    # light, haze, life
    if done_ix:
        for k, rx in enumerate((120, 330, 520)):
            top_layer.append(f'<polygon points="{rx},{max(frontier - 700, 0)} {rx + 70},{max(frontier - 700, 0)} {rx - 120},{frontier + 40} {rx - 210},{frontier + 40}" '
                             'fill="url(#g-ray)" style="mix-blend-mode:screen"/>')
        for k in range(14):
            px, py = rnd.uniform(40, W - 40), rnd.uniform(max(frontier - 500, TOP), frontier + 30)
            top_layer.append(f'<g class="drift" style="animation-delay:{-rnd.uniform(0, 11):.1f}s"><ellipse cx="{px:.0f}" cy="{py:.0f}" rx="3" ry="1.8" fill="#F8C1CF"/></g>')
    top_layer.append(f'<rect width="70" height="{H}" fill="url(#g-edge)"/><rect x="{W}" width="70" height="{H}" fill="url(#g-edge)" transform="scale(-1 1) translate(-{2 * W} 0)"/>')
    if not all_done:
        my = max(frontier, cy)
        top_layer.append(f'<rect y="{my + 50}" width="{W}" height="160" fill="url(#g-mist)"/>'
                         f'<rect y="{my + 210}" width="{W}" height="{max(H - my - 210, 0)}" fill="#EEF4E6" opacity=".66"/>')
    wx, wy = cx + (40 if cx < CX else -40), cy + 10
    top_layer.append(
        f'<g class="bee" transform="translate({cx + 30} {cy - 70})"><ellipse rx="5" ry="3.4" fill="#F5C842"/><rect x="-1.5" y="-3.4" width="2" height="6.8" fill="#2B2024"/>'
        '<ellipse cx="-1" cy="-4" rx="4" ry="2" fill="#fff" opacity=".7"/></g>'
        f'<g transform="translate({wx} {wy})"><g class="bob"><ellipse cy="2" rx="12" ry="4" fill="#000" opacity=".15"/>'
        '<path d="M-9 0L-6-22H6L9 0Z" fill="#E9A3B5"/><circle cy="-30" r="7" fill="#F6D9C4"/>'
        '<ellipse cy="-34" rx="14" ry="4" fill="#E8C98E"/><path d="M-7-34Q0-46 7-34Z" fill="#E8C98E"/>'
        '<rect x="-7" y="-36" width="14" height="3" fill="#E27D98"/>'
        '<path d="M10-14h10l-2 9h-6z" fill="#C9A06A"/><path d="M11-14q4-8 8 0" stroke="#A9814F" fill="none"/></g></g>'
        f'<g transform="translate({wx + 24} {wy - 46})"><g class="fly"><path d="M0 0q-6-8-10-2q4 6 10 2q6-8 10-2q-4 6-10 2z" fill="#E9A3B5"/></g></g>')

    objs.sort(key=lambda o: o[0])
    body = "".join(bg) + "".join(ground) + "".join(o[1] for o in objs) + "".join(top_layer)
    return {"body": body, "labels": "".join(labels), "H": H, "cy": cy}


def build(data, cur):
    sc = scene(data, cur)
    H = sc["H"]
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="wrap" style="aspect-ratio:{W}/{H}"><svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" '
            f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">{DEFS}{sc["body"]}</svg>{sc["labels"]}'
            f'<div id="here" style="position:absolute;top:{sc["cy"] / H * 100:.2f}%"></div></div>'
            "<script>addEventListener('load',()=>{const e=document.getElementById('here');"
            "if(e)scrollTo(0,Math.max(0,e.offsetTop-innerHeight*.45))})</script></body></html>")
