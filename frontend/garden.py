"""Builds the walkable garden roadmap as one self-contained HTML/SVG page (shown in a Streamlit iframe)."""
import html
import random

W, CX, AMP = 700, 350, 105
DY, GAP, TOP, BOTTOM = 120, 90, 170, 340
PETALS = {"pink": "#F4A6B8", "rose": "#E27D98", "lav": "#CDB4EA", "butter": "#F8DC82", "white": "#FFF3EE"}
KINDS = list(PETALS)


def _flower(name, colour):
    petals = "".join(f'<ellipse cy="-10" rx="6" ry="10" fill="{colour}" transform="rotate({a})"/>'
                     for a in range(0, 360, 60))
    centre = "#E27D98" if name == "butter" else "#F2B84B"
    return (f'<g id="fl-{name}"><path d="M0 0 C-3 -18 3 -30 0 -44" stroke="#7FA070" stroke-width="3" fill="none"/>'
            '<ellipse cx="-9" cy="-20" rx="9" ry="4" fill="#9CBB86" transform="rotate(-35 -9 -20)"/>'
            '<ellipse cx="9" cy="-28" rx="9" ry="4" fill="#9CBB86" transform="rotate(30 9 -28)"/>'
            f'<g transform="translate(0 -48)">{petals}<circle r="5" fill="{centre}"/></g></g>')


DEFS = "<defs>" + "".join(_flower(k, v) for k, v in PETALS.items()) + """
<g id="bud"><path d="M0 0 C-3 -16 3 -26 0 -38" stroke="#7FA070" stroke-width="3" fill="none"/>
<ellipse cx="-8" cy="-16" rx="8" ry="3.5" fill="#9CBB86" transform="rotate(-30 -8 -16)"/>
<path d="M0 -38 C-9 -44 -7 -58 0 -62 C7 -58 9 -44 0 -38Z" fill="#F4A6B8"/></g>
<g id="sprout"><path d="M0 0 V-16" stroke="#7FA070" stroke-width="2.5" fill="none"/>
<ellipse cx="-6" cy="-16" rx="6" ry="3" fill="#A8C694" transform="rotate(-30 -6 -16)"/>
<ellipse cx="6" cy="-18" rx="6" ry="3" fill="#A8C694" transform="rotate(30 6 -18)"/></g>
<g id="tuft"><path d="M-6 0 Q-6 -10 -10 -14 M0 0 Q0 -12 0 -18 M6 0 Q6 -10 10 -14" stroke="#A8C694"
stroke-width="2" fill="none" stroke-linecap="round"/></g>
<g id="stone"><ellipse rx="17" ry="9" fill="#EADCCB" stroke="#D5C2AB" stroke-width="2"/></g>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FDEFF1"/>
<stop offset=".5" stop-color="#F3F1E2"/><stop offset="1" stop-color="#E4EED9"/></linearGradient>
<linearGradient id="mist" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF8F0" stop-opacity="0"/>
<stop offset="1" stop-color="#FFF8F0" stop-opacity=".62"/></linearGradient></defs>"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Caveat:wght@600&family=Nunito:wght@400;600&display=swap');
html,body{margin:0;background:#FFF8F0}
.wrap{position:relative;width:100%;max-width:700px;margin:0 auto;container-type:inline-size;overflow:hidden;border-radius:22px}
svg{position:absolute;inset:0;width:100%;height:100%}
.lb{position:absolute;max-width:27%;transform:translateY(-60%);font:400 clamp(10px,2.1cqw,14px)/1.25 'Nunito',sans-serif;
 color:#5B4448;background:rgba(255,250,244,.93);border:1.5px solid #EBC8D0;border-radius:12px;padding:.35em .65em}
.lb .n{font:600 1.25em 'Caveat',cursive;color:#B5657D;margin-right:.25em}
.lb.done{background:#FCE9ED;border-color:#E9A3B5}
.lb.sel{border:2px solid #D98BA0;box-shadow:0 4px 14px rgba(217,139,160,.35);font-weight:600}
.ch{position:absolute;left:10%;width:80%;transform:translateY(-50%);text-align:center;background:#FFFCF8;
 border:2px dashed #9CAF88;border-radius:16px;padding:.4em .6em;color:#5B4448}
.ch.full{background:#FCE9ED;border-color:#E27D98}
.ch small{display:block;font:600 clamp(13px,3.2cqw,19px) 'Caveat',cursive;color:#B5657D}
.ch b{font:600 clamp(13px,2.9cqw,18px) 'Fraunces',serif}
.hello{position:absolute;left:0;right:0;text-align:center;font:600 clamp(16px,4cqw,26px) 'Caveat',cursive;color:#B5657D}
.sway{transform-box:fill-box;transform-origin:50% 100%;animation:sway 4s ease-in-out infinite alternate}
.bob{animation:bob 1.4s ease-in-out infinite alternate}.fly{animation:fly 3s ease-in-out infinite alternate}
.smoke{animation:rise 4s ease-out infinite}
@keyframes sway{from{transform:rotate(-3deg)}to{transform:rotate(3deg)}}
@keyframes bob{to{transform:translateY(-3px)}}@keyframes fly{to{transform:translate(8px,-10px)}}
@keyframes rise{from{opacity:.7;transform:translateY(0)}to{opacity:0;transform:translateY(-30px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def _path_x(y, pts):
    if y <= pts[0][1]:
        return pts[0][0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return x0 + (x1 - x0) * t * t * (3 - 2 * t)
    return pts[-1][0]


def build(data, cur):
    pts, topics, banners, y = [], [], [], TOP
    for si, s in enumerate(data["sections"]):
        y += GAP if si else 90
        banners.append((si, y))
        for t in s["topics"]:
            pts.append((CX + (AMP if len(pts) % 2 else -AMP), y))
            topics.append((si, t))
            y += DY
    n, H = len(pts), y - DY + BOTTOM
    all_done = all(t["status"] == "done" for _, t in topics)
    done_ix = [i for i, (_, t) in enumerate(topics) if t["status"] == "done"]
    frontier = pts[max(done_ix)][1] if done_ix else TOP

    rnd = random.Random(data["slug"])
    svg = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    fy = TOP + 60
    while fy < H - 260:  # filler plants: bloom behind the frontier, bare sprouts ahead
        for _ in range(2):
            fx = rnd.uniform(26, W - 26)
            if abs(fx - _path_x(fy, pts)) < 52:
                continue
            if fy <= frontier:
                ref, sc = f"fl-{rnd.choice(KINDS)}", rnd.uniform(.45, .85)
            else:
                ref, sc = rnd.choice(["tuft", "sprout"]), rnd.uniform(.9, 1.2)
            svg.append(f'<g transform="translate({fx:.0f} {fy:.0f})"><g class="sway" style="animation-delay:'
                       f'{-rnd.random() * 4:.1f}s"><use href="#{ref}" transform="scale({sc:.2f})"/></g></g>')
        fy += 30

    route = [(CX, 125)] + pts + [(CX, H - 100)]  # gate -> stops -> cottage door
    for j in range(len(route) - 1):
        (x0, y0), (x1, y1) = route[j], route[j + 1]
        walked = j == 0 or topics[j - 1][1]["status"] == "done"
        d = f"M{x0} {y0} C{x0} {(y0 + y1) / 2} {x1} {(y0 + y1) / 2} {x1} {y1}"
        svg.append(f'<path d="{d}" fill="none" stroke="{"#F3C9D3" if walked else "#E6DACA"}" stroke-width="30" stroke-linecap="round"/>'
                   f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="3" stroke-dasharray="1 13" stroke-linecap="round"/>')
    svg.append(f'<rect y="{frontier + 20}" width="{W}" height="150" fill="url(#mist)"/>'
               f'<rect y="{frontier + 170}" width="{W}" height="{max(H - frontier - 170, 0)}" fill="#FFF8F0" opacity=".62"/>')

    svg.append(f'<g transform="translate({CX} 70)"><path d="M-70 60V0Q0-50 70 0V60" stroke="#9CAF88" stroke-width="7" '
               'fill="none" stroke-linecap="round"/>' + "".join(
                   f'<use href="#fl-{KINDS[k % 5]}" transform="translate({x} {yy}) scale(.35)"/>'
                   for k, (x, yy) in enumerate([(-66, 40), (-62, 6), (-36, -22), (0, -34), (36, -22), (62, 6), (66, 40)])) + "</g>")

    labels = ['<div class="hello" style="top:%.2f%%">begin your walk 🌿</div>' % (150 / H * 100)]
    for si, by in banners:  # chapter signs; the vine on top blooms when the chapter is complete
        s = data["sections"][si]
        got = sum(t["status"] == "done" for t in s["topics"])
        full = got == len(s["topics"])
        top = by - 95
        for x in range(110, 600, 80):
            ref = f"fl-{KINDS[si % 5]}" if full else "tuft"
            svg.append(f'<use href="#{ref}" transform="translate({x} {top - 16}) scale(.4)"/>')
        labels.append(f'<div class="ch{" full" if full else ""}" style="top:{top / H * 100:.2f}%"><small>Chapter {si + 1} · '
                      f'{got}/{len(s["topics"])} blooming</small><b>{html.escape(s["title"])}</b></div>')

    for i, (si, t) in enumerate(topics):
        x, y = pts[i]
        stt = t["status"]
        ref, sc = ({"done": (f"fl-{KINDS[si % 5]}", 1.1), "in_progress": ("bud", 1.0)}).get(stt, ("sprout", .8))
        op = "" if stt != "not_started" else ' opacity=".55"'
        svg.append(f'<g transform="translate({x} {y})"><use href="#stone"/><g transform="translate(0 2)"{op}>'
                   f'<g class="sway"><use href="#{ref}" transform="scale({sc})"/></g></g>'
                   + ('<ellipse rx="26" ry="14" fill="none" stroke="#D98BA0" stroke-width="2.5" stroke-dasharray="5 5"/>'
                      if i == cur else "") + "</g>")
        glyph = {"done": "🌸", "in_progress": "🌱"}.get(stt, "")
        side = f"left:{(x + 40) / W * 100:.2f}%" if x > CX else f"right:{(W - x + 40) / W * 100:.2f}%;text-align:right"
        cls = "lb" + (" done" if stt == "done" else "") + (" sel" if i == cur else "")
        labels.append(f'<div class="{cls}" style="top:{y / H * 100:.2f}%;{side}"><span class="n">{i + 1}</span>'
                      f'{html.escape(t["title"])} {glyph}</div>')

    cx, cy = pts[cur]  # the walker stands on the inner side of the current stop
    wx, wy = cx + (40 if cx < CX else -40), cy + 10
    svg.append(f'<g transform="translate({wx} {wy})"><g class="bob"><ellipse cy="2" rx="12" ry="4" fill="#000" opacity=".1"/>'
               '<path d="M-9 0L-6-22H6L9 0Z" fill="#E9A3B5"/><circle cy="-30" r="7" fill="#F6D9C4"/>'
               '<ellipse cy="-34" rx="14" ry="4" fill="#E8C98E"/><path d="M-7-34Q0-46 7-34Z" fill="#E8C98E"/>'
               '<rect x="-7" y="-36" width="14" height="3" fill="#E27D98"/>'
               '<path d="M10-14h10l-2 9h-6z" fill="#C9A06A"/><path d="M11-14q4-8 8 0" stroke="#A9814F" fill="none"/></g></g>'
               f'<g transform="translate({wx + 24} {wy - 46})"><g class="fly"><path d="M0 0q-6-8-10-2q4 6 10 2q6-8 10-2q-4 6-10 2z" fill="#E9A3B5"/></g></g>')

    glow = "#FFD98A" if all_done else "#DCD0C4"  # the cottage lights up when the roadmap is complete
    smoke = "".join(f'<circle class="smoke" cx="43" cy="-90" r="{5 + k * 2}" fill="#fff" style="animation-delay:{-k * 1.3}s"/>'
                    for k in range(3)) if all_done else ""
    svg.append(f'<g transform="translate({CX} {H - 170})"><rect x="-70" y="-20" width="140" height="90" rx="6" fill="#F7E1E4" '
               'stroke="#E2BCC6" stroke-width="3"/><path d="M-90-18L0-88L90-18Z" fill="#C98A9B"/><rect x="35" y="-82" width="16" height="36" fill="#B8788A"/>'
               f'<path d="M-16 70V36Q0 14 16 36V70Z" fill="#9CAF88"/><rect x="-58" y="0" width="28" height="26" rx="4" fill="{glow}"/>'
               f'<rect x="30" y="0" width="28" height="26" rx="4" fill="{glow}"/>{smoke}</g>')
    labels.append('<div class="hello" style="top:%.2f%%">%s</div>' % (
        (H - 60) / H * 100, "home at last — everything is in bloom 🌸" if all_done else "the cottage waits at the end"))

    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="wrap" style="aspect-ratio:{W}/{H}"><svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" '
            f'xmlns="http://www.w3.org/2000/svg">{DEFS}{"".join(svg)}</svg>{"".join(labels)}'
            f'<div id="here" style="position:absolute;top:{cy / H * 100:.2f}%"></div></div>'
            "<script>addEventListener('load',()=>{const e=document.getElementById('here');"
            "if(e)scrollTo(0,Math.max(0,e.offsetTop-innerHeight*.45))})</script></body></html>")
