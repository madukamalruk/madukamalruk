"""
Builds the static artwork for the profile README:

  assets/madukz-space.svg   - animated electronics-lab hero scene
  assets/footer.svg         - PCB-trace footer

Everything is hand-placed on a 4px grid and animated with plain CSS / SMIL,
so it renders inside GitHub's <img> sandbox (no JS, no external fonts).

    python scripts/build_banner.py
"""
from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

# palette (matches madukamalruk.com.lk: obsidian, electric cyan, copper/gold) --
INK = "#06070A"
WALL = "#0A0D14"
WALL_2 = "#0D111A"
GRID = "#10151E"
LINE = "#1C2330"
CYAN = "#00E5FF"
CYAN_DIM = "#06363F"
AMBER = "#E0A84A"
AMBER_DIM = "#2E2310"
GOLD = "#C9A227"
COPPER = "#B87333"
RED = "#E5484D"
GREEN = "#3DD68C"
WOOD = "#10141B"      # bench front
WOOD_HI = "#1A2029"   # bench top / shelves
WOOD_LO = "#0B0E13"
STEEL = "#181E28"
STEEL_HI = "#2A3240"
TEXT_DIM = "#5A6E85"

def r(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'


# --------------------------------------------------------------------------
# 5x7 dot-matrix font for the LED sign
# --------------------------------------------------------------------------
GLYPHS = {
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    " ": ["00000"] * 7,
}


def led_sign(text: str, x0: int, y0: int, pitch: int = 8) -> str:
    """Dot-matrix LED sign: dim LEDs everywhere, lit LEDs shimmer column by column."""
    out = []
    col = 0
    for i, ch in enumerate(text):
        glyph = GLYPHS[ch]
        lit_cls = "ledc" if i < 6 else "leda"
        for gx in range(6):  # 5 cols + 1 spacer
            cx = x0 + col * pitch
            delay = -(col * 0.045)
            for gy in range(7):
                cy = y0 + gy * pitch
                on = gx < 5 and glyph[gy][gx] == "1"
                if on:
                    out.append(
                        f'<circle class="{lit_cls}" cx="{cx}" cy="{cy}" r="3.1" '
                        f'style="animation-delay:{delay:.2f}s"/>'
                    )
                else:
                    out.append(f'<circle cx="{cx}" cy="{cy}" r="2.4" fill="#11161F"/>')
            col += 1
    return "\n".join(out)


def sine_path(x0, y_mid, amp, period, length, phase=0.0, step=2):
    pts = []
    x = 0
    while x <= length:
        y = y_mid + amp * math.sin((x / period) * 2 * math.pi + phase)
        pts.append(f"{x0 + x:.1f},{y:.1f}")
        x += step
    return "M" + " L".join(pts)


def square_path(x0, y_hi, y_lo, half, length):
    d = [f"M{x0},{y_lo}"]
    x = x0
    hi = False
    while x < x0 + length:
        y = y_hi if hi else y_lo
        d.append(f"L{x},{y}")
        x += half
        d.append(f"L{x},{y}")
        hi = not hi
    return " ".join(d)


# --------------------------------------------------------------------------
# hero scene
# --------------------------------------------------------------------------
def hero() -> str:
    W, H = 1200, 500
    p: list[str] = []
    add = p.append

    # one shared rhythm: every loop is a multiple of 1.2 s, nothing strobes
    style = f"""
    <style>
      text {{ font-family: {MONO}; }}
      .ledc {{ fill:{CYAN}; filter:url(#glowC); animation: shimmer 4.8s ease-in-out infinite; }}
      .leda {{ fill:{AMBER}; filter:url(#glowA); animation: shimmer 4.8s ease-in-out infinite; }}
      @keyframes shimmer {{ 0%,100% {{opacity:.86}} 50% {{opacity:1}} }}
      .blink {{ animation: pulse 2.4s ease-in-out infinite; }}
      .blink-slow {{ animation: pulse 4.8s ease-in-out infinite; }}
      .blink-fast {{ animation: pulse 1.2s ease-in-out infinite; }}
      @keyframes pulse {{ 0%,100% {{opacity:1}} 50% {{opacity:.45}} }}
      .chase {{ opacity:.3; animation: chase 4.8s ease-in-out infinite; }}
      @keyframes chase {{ 0%,30% {{opacity:.9}} 45%,100% {{opacity:.3}} }}
      .twinkle {{ animation: twinkle 4.8s ease-in-out infinite; }}
      @keyframes twinkle {{ 0%,100% {{opacity:.3}} 50% {{opacity:.85}} }}
      .arc {{ opacity:0; animation: arc 4.8s ease-out infinite; }}
      @keyframes arc {{ 0% {{opacity:.4}} 4% {{opacity:0}} 100% {{opacity:0}} }}
      .scope {{ animation: scroll 2.4s linear infinite; }}
      .scope2 {{ animation: scroll2 4.8s linear infinite; }}
      @keyframes scroll {{ from {{transform:translateX(0)}} to {{transform:translateX(-40px)}} }}
      @keyframes scroll2 {{ from {{transform:translateX(0)}} to {{transform:translateX(-48px)}} }}
      .rd {{ opacity:0; animation: reading 14.4s steps(1) infinite; }}
      @keyframes reading {{ 0%,24.9% {{opacity:1}} 25%,100% {{opacity:0}} }}
      .pulse {{ stroke-dasharray: 10 150; animation: flow 4.8s linear infinite; }}
      .pulse.b {{ animation-delay: -1.6s; }}
      .pulse.c {{ animation-delay: -3.2s; }}
      @keyframes flow {{ from {{stroke-dashoffset:160}} to {{stroke-dashoffset:0}} }}
      .smoke {{ animation: smoke 4.8s ease-out infinite; }}
      @keyframes smoke {{ 0% {{transform:translate(0,0); opacity:0}} 15% {{opacity:.35}}
                          100% {{transform:translate(6px,-46px); opacity:0}} }}
      .cone {{ animation: lamp 9.6s ease-in-out infinite; }}
      @keyframes lamp {{ 0%,100% {{opacity:.1}} 50% {{opacity:.14}} }}
      .ticker {{ animation: ticker 48s linear infinite; }}
      @keyframes ticker {{ from {{transform:translateX(0)}} to {{transform:translateX(-1240px)}} }}
      .cursor {{ animation: pulse 2.4s steps(1) infinite; }}
    </style>"""

    defs = f"""
    <defs>
      <filter id="glowC" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="1.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <filter id="glowA" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="1.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.4"/></filter>
      <pattern id="bp" width="24" height="24" patternUnits="userSpaceOnUse">
        <path d="M24 0H0V24" fill="none" stroke="{GRID}" stroke-width="1"/>
      </pattern>
      <pattern id="bb" width="6" height="6" patternUnits="userSpaceOnUse">
        <rect x="2" y="2" width="2" height="2" fill="#a9a493"/>
      </pattern>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#04060B"/><stop offset="1" stop-color="#0E1828"/>
      </linearGradient>
      <linearGradient id="coneG" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{AMBER}" stop-opacity="1"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="screenG" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#08140F"/><stop offset="1" stop-color="#050C09"/>
      </linearGradient>
      <clipPath id="scopeClip"><rect x="44" y="286" width="118" height="72"/></clipPath>
      <clipPath id="tickerClip"><rect x="0" y="472" width="{W}" height="28"/></clipPath>
      <clipPath id="frame"><rect x="0" y="0" width="{W}" height="{H}" rx="14"/></clipPath>
    </defs>"""

    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d">')
    add('<title id="t">MADUKZ SPACE</title>')
    add('<desc id="d">Animated pixel-style electronics lab: LED sign, oscilloscope, multimeter, '
        'breadboard, PCB layout on a monitor, Tesla coil, robot arm, soldering station and a micromouse on the bench.</desc>')
    add(style)
    add(defs)
    add('<g clip-path="url(#frame)" shape-rendering="crispEdges">')

    # wall + blueprint grid -------------------------------------------------
    add(r(0, 0, W, H, WALL))
    add(r(0, 0, W, 440, "url(#bp)"))
    add(r(0, 0, W, 10, INK))
    # cable tray along the ceiling
    add(r(0, 10, W, 4, STEEL))
    for x in range(20, W, 120):
        add(r(x, 14, 4, 6, STEEL))

    # LED sign ----------------------------------------------------------------
    add('<g>')
    add(r(36, 28, 600, 92, INK, f'stroke="{LINE}" stroke-width="2" rx="6"'))
    for sx, sy in [(44, 36), (620, 36), (44, 104), (620, 104)]:
        add(f'<circle cx="{sx + 4}" cy="{sy + 4}" r="3" fill="{STEEL_HI}"/>')
    add(led_sign("MADUKZ SPACE", 54, 50))
    add("</g>")
    # sign power cable
    add(f'<path d="M636 74 C670 74 668 140 700 150" fill="none" stroke="#0E121A" stroke-width="4"/>')
    add(f'<text x="40" y="136" font-size="13" fill="{TEXT_DIM}" letter-spacing="2">'
        f'ELECTRICAL ENGINEERING · ROBOTICS · EMBEDDED SYSTEMS</text>')

    # window with night sky ----------------------------------------------------------
    add(r(904, 26, 264, 168, STEEL, 'rx="4"'))
    add(r(912, 34, 248, 152, "url(#sky)"))
    stars = [(930, 60), (962, 90), (1004, 52), (1040, 120), (1076, 70), (1118, 104), (1140, 50),
             (986, 140), (1092, 150), (950, 168), (1130, 162), (1060, 44)]
    for i, (sx, sy) in enumerate(stars):
        add(f'<rect class="twinkle" x="{sx}" y="{sy}" width="3" height="3" fill="#dbe8ff" '
            f'style="animation-delay:{-i * 0.37:.2f}s"/>')
    add('<circle cx="1112" cy="70" r="18" fill="#f1e6c6"/><circle cx="1104" cy="64" r="18" fill="#0b1934"/>')
    # far skyline
    for bx, bw, bh in [(912, 26, 26), (940, 18, 40), (960, 30, 22), (992, 22, 46), (1016, 34, 30),
                       (1052, 20, 52), (1074, 28, 24), (1104, 22, 38), (1128, 32, 28)]:
        add(r(bx, 186 - bh, bw, bh, "#080C14"))
        if bh > 30:
            add(f'<rect class="blink-slow" x="{bx + bw // 2 - 1}" y="{186 - bh - 3}" width="3" height="3" fill="{RED}"/>')
    add(r(1032, 34, 8, 152, STEEL))
    add(r(912, 106, 248, 6, STEEL))
    add(r(898, 190, 276, 8, STEEL_HI))

    # left shelf ------------------------------------------------------------------------
    add(r(28, 232, 306, 8, WOOD_HI))
    add(r(28, 240, 306, 4, WOOD_LO))
    for bx in (52, 300):
        add(r(bx, 244, 6, 14, STEEL))
        add(r(bx - 6, 244, 18, 4, STEEL))

    # Tesla coil on shelf
    add(r(44, 216, 48, 16, "#1b2338"))
    add(r(44, 216, 48, 3, STEEL_HI))
    add(f'<circle class="blink" cx="52" cy="226" r="2" fill="{GREEN}"/>')
    add(r(60, 166, 16, 50, "#b26b2c"))
    for yy in range(168, 214, 4):
        add(r(60, yy, 16, 1, "#7d4519"))
    add('<ellipse cx="68" cy="160" rx="22" ry="8" fill="#9aa6bd" stroke="#5c6880" stroke-width="2"/>')
    arcs = [
        "M88 158 L98 154 L94 150 L108 146 L104 142 L116 140",
        "M48 156 L40 152 L44 148 L32 146 L36 142 L26 140",
        "M86 164 L100 168 L98 176 L112 182",
        "M50 164 L38 170 L42 176 L30 184",
        "M90 162 L104 160 L102 166 L118 164",
    ]
    for i, d in enumerate(arcs):
        add(f'<path class="arc" d="{d}" fill="none" stroke="#9BE9FF" stroke-width="2" '
            f'filter="url(#glowC)" style="animation-delay:{-i * 0.38:.2f}s"/>')

    # capacitors
    for i, (cx, h, col) in enumerate([(116, 34, "#2b5fb8"), (138, 26, "#2b5fb8"), (156, 40, "#1f8a6a")]):
        add(r(cx, 232 - h, 16, h, col, 'rx="3"'))
        add(r(cx + 11, 232 - h + 2, 3, h - 4, "#cfd8e8", 'opacity=".55"'))
        add(r(cx + 2, 232 - h, 12, 3, "#9aa6bd"))
    # solder spool
    add('<circle cx="196" cy="216" r="16" fill="#3a3f4f"/><circle cx="196" cy="216" r="11" fill="#c0c6d4"/>'
        '<circle cx="196" cy="216" r="4" fill="#1b2338"/>')
    # ESP32 box
    add(r(220, 186, 84, 46, "#1c2b4a", f'stroke="{LINE}" stroke-width="2"'))
    add(r(228, 194, 30, 22, "#0e1628"))
    add(r(232, 198, 22, 14, "#20262f"))
    add(r(264, 198, 30, 4, CYAN, 'opacity=".7"'))
    add(r(264, 206, 20, 3, TEXT_DIM))
    add(r(306, 204, 22, 28, "#0d6c7a"))  # arduino leaning
    add(r(308, 206, 8, 6, "#d9dde6"))
    add(r(318, 216, 8, 8, "#111"))

    # clamp lamp under shelf + light cone
    add(r(300, 244, 4, 14, STEEL_HI))
    add('<path d="M296 258 L322 258 L330 274 L288 274 Z" fill="#2c3a5a"/>')
    add('<path class="cone" d="M290 274 L328 274 L430 380 L206 380 Z" fill="url(#coneG)"/>')

    # maze poster (animated flood-fill solve) -------------------------------------------
    px, py = 360, 154
    add(r(px - 6, py - 6, 132, 124, "#0b1a33", f'stroke="{LINE}" stroke-width="2"'))
    add(r(px + 54, py - 10, 12, 8, "#9aa6bd"))  # tape
    cell = 20
    walls = [  # (x1,y1,x2,y2) in cell units on a 6x5 board
        (0, 0, 6, 0), (0, 5, 6, 5), (0, 0, 0, 5), (6, 0, 6, 5),
        (1, 0, 1, 2), (2, 1, 2, 3), (1, 3, 3, 3), (3, 1, 5, 1), (4, 1, 4, 2),
        (5, 2, 5, 4), (3, 2, 3, 3), (2, 4, 5, 4), (1, 4, 1, 5),
    ]
    for x1, y1, x2, y2 in walls:
        add(f'<line x1="{px + x1 * cell}" y1="{py + y1 * cell}" x2="{px + x2 * cell}" y2="{py + y2 * cell}" '
            f'stroke="#cfe3ff" stroke-width="3" stroke-linecap="square"/>')
    add(r(px + 2 * cell + 4, py + 2 * cell + 4, 12, 12, AMBER_DIM))
    route = [(0.5, 4.5), (0.5, 0.5), (1.5, 0.5), (2.5, 0.5), (2.5, 1.5), (3.5, 1.5), (3.5, 2.5),
             (4.5, 2.5), (4.5, 3.5), (3.5, 3.5), (2.5, 3.5), (2.5, 2.5)]
    path = "M" + " L".join(f"{px + a * cell:.0f},{py + b * cell:.0f}" for a, b in route)
    add(f'<path d="{path}" fill="none" stroke="{CYAN}" stroke-width="2" stroke-dasharray="4 4" opacity=".35"/>')
    add(f'<g><rect x="-5" y="-5" width="10" height="10" fill="{CYAN}" filter="url(#glowC)"/>'
        f'<animateMotion path="{path}" dur="7s" repeatCount="indefinite" calcMode="linear"/></g>')

    # monitor: PCB layout --------------------------------------------------------------
    mx, my, mw, mh = 500, 150, 250, 172
    add(r(mx - 8, my - 8, mw + 16, mh + 16, "#111a2c", 'rx="8"'))
    add(r(mx - 8, my - 8, mw + 16, mh + 16, "none", f'rx="8" stroke="{CYAN}" stroke-opacity=".25" stroke-width="2"'))
    add(r(mx, my, mw, mh, "#06101e"))
    add(r(mx, my, mw, 14, "#1a2742"))
    for i, c in enumerate((RED, AMBER, GREEN)):
        add(f'<circle cx="{mx + 8 + i * 10}" cy="{my + 7}" r="3" fill="{c}"/>')
    add(r(mx + 44, my + 5, 84, 4, "#3a4a6e"))
    # board outline
    bx, by = mx + 16, my + 24
    add(r(bx, by, 170, 124, "#0b2a22", 'stroke="#C9A227" stroke-width="1.5"'))
    # copper traces (static)
    traces = [
        f"M{bx + 20} {by + 20} H{bx + 70} V{by + 50} H{bx + 120}",
        f"M{bx + 20} {by + 40} H{bx + 50} V{by + 90} H{bx + 140} V{by + 70}",
        f"M{bx + 150} {by + 20} V{by + 50} H{bx + 120}",
        f"M{bx + 30} {by + 104} H{bx + 100} V{by + 80}",
        f"M{bx + 140} {by + 104} H{bx + 156} V{by + 30}",
    ]
    for i, d in enumerate(traces):
        col = COPPER if i % 2 == 0 else "#2F6FB0"
        add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3"/>')
    for i, d in enumerate(traces):
        cls = ["", " b", " c", " b", ""][i]
        add(f'<path class="pulse{cls}" d="{d}" fill="none" stroke="#eaffff" stroke-width="3" '
            f'filter="url(#glowC)"/>')
    # MCU + pads
    add(r(bx + 64, by + 56, 40, 30, "#1a1a1a", 'stroke="#888" stroke-width="1"'))
    for k in range(5):
        add(r(bx + 66 + k * 8, by + 52, 4, 4, "#C9A227"))
        add(r(bx + 66 + k * 8, by + 86, 4, 4, "#C9A227"))
    for (vx, vy) in [(20, 20), (20, 40), (150, 20), (30, 104), (140, 104), (120, 50), (100, 80)]:
        add(f'<circle cx="{bx + vx}" cy="{by + vy}" r="3.5" fill="#C9A227"/>'
            f'<circle cx="{bx + vx}" cy="{by + vy}" r="1.4" fill="#06101e"/>')
    # side panel (layers)
    lx = mx + 196
    for i, (name, col) in enumerate([("F.Cu", COPPER), ("B.Cu", "#2F6FB0"), ("F.Silk", "#C9A227"),
                                     ("Edge", "#C9A227"), ("F.Mask", "#9a4fd6")]):
        add(r(lx, by + 4 + i * 16, 8, 8, col))
        add(r(lx + 12, by + 7 + i * 16, 24, 3, "#3a4a6e"))
    add(r(mx + 8, my + mh - 11, 70, 4, GREEN, 'opacity=".6"'))
    add(f'<rect class="cursor" x="{mx + 84}" y="{my + mh - 13}" width="5" height="9" fill="{GREEN}"/>')
    # stand
    add(r(606, 330, 38, 34, "#111a2c"))
    add(r(584, 364, 82, 8, "#18233a"))

    # schematic poster ---------------------------------------------------------------------
    sx, sy = 822, 208
    add(r(sx, sy, 144, 96, "#123a6b", 'stroke="#2e5c96" stroke-width="2"'))
    add(r(sx + 66, sy - 4, 12, 8, "#9aa6bd"))
    w = "#dfeaff"
    add(f'<path d="M{sx + 10} {sy + 50} H{sx + 22} l3 -6 l5 12 l5 -12 l5 12 l5 -12 l3 6 H{sx + 64}" '
        f'fill="none" stroke="{w}" stroke-width="1.6" shape-rendering="geometricPrecision"/>')
    add(f'<path d="M{sx + 64} {sy + 38} V{sy + 62} L{sx + 92} {sy + 50} Z" fill="none" stroke="{w}" stroke-width="1.6"/>')
    add(f'<path d="M{sx + 92} {sy + 50} H{sx + 132} M{sx + 112} {sy + 50} V{sy + 64} M{sx + 104} {sy + 64} H{sx + 120} '
        f'M{sx + 104} {sy + 68} H{sx + 120} M{sx + 112} {sy + 68} V{sy + 80} M{sx + 106} {sy + 80} H{sx + 118}" '
        f'fill="none" stroke="{w}" stroke-width="1.6"/>')

    # right shelf ---------------------------------------------------------------------------
    add(r(984, 252, 196, 8, WOOD_HI))
    add(r(984, 260, 196, 4, WOOD_LO))
    for bx2 in (1000, 1160):
        add(r(bx2, 264, 6, 12, STEEL))
    # trophy
    add('<path d="M1004 214 h28 v8 a14 14 0 0 1 -28 0 Z" fill="#f2c14e"/>')
    add(r(1014, 234, 8, 8, "#d9a43a"))
    add(r(1006, 242, 24, 10, "#4a3a20"))
    add('<rect class="twinkle" x="1010" y="216" width="3" height="3" fill="#fff"/>')
    # books
    for i, (lbl, col, h) in enumerate([("PID", "#2A3444", 44), ("DSP", "#22303F", 40), ("EMAG", COPPER, 46),
                                        ("C++", "#2E3A4C", 38), ("CTRL", "#1F2A38", 42)]):
        bx3 = 1044 + i * 16
        add(r(bx3, 252 - h, 14, h, col))
        add(r(bx3, 252 - h + 4, 14, 2, "#00000055"))
        add(r(bx3 + 3, 252 - 14, 8, 3, "#f3f3f3", 'opacity=".55"'))
    # desk ------------------------------------------------------------------------------------
    add(r(0, 380, W, 12, WOOD_HI))
    add(r(0, 380, W, 1, COPPER, 'opacity=".55"'))
    add(r(0, 392, W, 48, WOOD))
    add(r(0, 392, W, 3, WOOD_LO))
    for x in range(0, W, 150):
        add(r(x + 40, 404, 70, 1, LINE))
    add(r(0, 440, W, 32, INK))
    for x in range(0, W, 48):
        add(r(x, 440, 1, 32, WALL_2))

    # oscilloscope ---------------------------------------------------------------------------
    add(r(28, 272, 206, 108, "#1e2840", 'rx="4"'))
    add(r(28, 272, 206, 6, "#2b3858"))
    add(r(40, 282, 126, 80, "#000"))
    add(r(44, 286, 118, 72, "url(#screenG)"))
    for gx in range(44, 163, 20):
        add(f'<line x1="{gx}" y1="286" x2="{gx}" y2="358" stroke="#103a2e" stroke-width="1"/>')
    for gy in range(286, 359, 18):
        add(f'<line x1="44" y1="{gy}" x2="162" y2="{gy}" stroke="#103a2e" stroke-width="1"/>')
    add('<g clip-path="url(#scopeClip)" shape-rendering="geometricPrecision">')
    add(f'<path class="scope" d="{sine_path(44, 312, 14, 40, 200)}" fill="none" stroke="{GREEN}" stroke-width="2" filter="url(#glowC)"/>')
    add(f'<path class="scope2" d="{square_path(44, 334, 350, 24, 220)}" fill="none" stroke="{AMBER}" stroke-width="1.6" opacity=".9"/>')
    add("</g>")
    for i, (kx, ky) in enumerate([(184, 294), (212, 294), (184, 326), (212, 326)]):
        add(f'<circle cx="{kx}" cy="{ky}" r="9" fill="#0d1424" stroke="{STEEL_HI}" stroke-width="2"/>')
        add(r(kx - 1, ky - 8, 2, 6, "#cfd8e8"))
    add(f'<rect class="blink" x="176" y="350" width="8" height="5" fill="{GREEN}"/>')
    add(f'<rect class="blink-slow" x="190" y="350" width="8" height="5" fill="{AMBER}"/>')
    add(r(206, 348, 18, 10, "#0d1424"))
    for k in range(4):
        add(f'<circle cx="{54 + k * 30}" cy="372" r="4" fill="#0d1424" stroke="#4d5c80" stroke-width="2"/>')

    # multimeter ------------------------------------------------------------------------------
    add(r(246, 248, 100, 132, "#e0a30b", 'rx="10"'))  # holster
    add(r(254, 256, 84, 116, "#2a2f3a", 'rx="6"'))
    add(r(262, 264, 68, 32, "#a8b89a"))  # LCD
    add(r(262, 264, 68, 32, "none", 'stroke="#56604c" stroke-width="2"'))
    readings = [("12.04", "V DC"), ("3.301", "V DC"), ("0.472", "A"), ("4.70k", "Ω")]
    for i, (val, unit) in enumerate(readings):
        add(f'<g class="rd" style="animation-delay:{-12 + i * 3}s">'
            f'<text x="268" y="287" font-size="17" font-weight="700" fill="#1b2116">{val}</text></g>')
    # rotary dial
    add('<circle cx="296" cy="330" r="24" fill="#1a1e27" stroke="#4a5164" stroke-width="2"/>')
    for k, lbl in enumerate(["V", "V~", "A", "Ω"]):
        a = math.radians(-60 + k * 40)
        add(f'<circle cx="{296 + 30 * math.sin(a):.1f}" cy="{330 - 30 * math.cos(a):.1f}" r="2" fill="#e9edf5"/>')
    add(f'<g><rect x="293" y="310" width="6" height="22" fill="#e9edf5" rx="2"/>'
        f'<animateTransform attributeName="transform" type="rotate" values="-60 296 330;-60 296 330;-60 296 330;20 296 330;60 296 330" '
        f'keyTimes="0;0.25;0.5;0.75;1" calcMode="discrete" dur="12s" repeatCount="indefinite"/></g>')
    for k, col in enumerate(["#111", "#c22", "#c22"]):
        add(f'<circle cx="{272 + k * 24}" cy="362" r="5" fill="#0b0d12" stroke="{col}" stroke-width="2"/>')

    # probe leads to breadboard
    add('<path d="M272 362 C262 398 340 404 386 360" fill="none" stroke="#1c1c1c" stroke-width="3" shape-rendering="geometricPrecision"/>')
    add('<path d="M296 362 C300 404 420 410 452 352" fill="none" stroke="#d23030" stroke-width="3" shape-rendering="geometricPrecision"/>')
    add(r(382, 344, 6, 18, "#1c1c1c"))
    add(r(449, 336, 6, 18, "#d23030"))

    # breadboard --------------------------------------------------------------------------------
    add(r(366, 352, 150, 28, "#e6e1d2", 'rx="2"'))
    add(r(366, 352, 150, 28, "url(#bb)"))
    add(r(366, 364, 150, 3, "#cfc8b4"))
    for k, col in enumerate([RED, AMBER, GREEN, CYAN]):
        x = 400 + k * 14
        add(r(x, 344, 8, 8, col, f'class="chase" style="animation-delay:{k * 0.4:.1f}s"'))
        add(r(x + 1, 352, 2, 4, "#888"))
        add(r(x + 5, 352, 2, 4, "#888"))
    add(r(462, 356, 26, 10, "#1a1a1a"))  # 555 timer
    add(f'<path d="M396 360 C400 344 420 344 424 360" fill="none" stroke="#2b7de9" stroke-width="2" shape-rendering="geometricPrecision"/>')
    add(f'<path d="M440 372 C452 356 476 356 494 372" fill="none" stroke="#e9a12b" stroke-width="2" shape-rendering="geometricPrecision"/>')

    # keyboard ------------------------------------------------------------------------------------
    add(r(528, 368, 158, 12, "#141c2f", 'rx="2"'))
    k = 0
    for row in range(2):
        for col in range(14):
            kx = 532 + col * 11
            ky = 370 + row * 5
            add(r(kx, ky, 9, 3, CYAN, 'opacity=".35"'))
            k += 1

    # micromouse on the bench (centrepiece) -------------------------------------------------------
    add('<g shape-rendering="geometricPrecision">')
    add(f'<path d="M842 352 L900 340 L900 370 L842 362 Z" fill="{RED}" opacity=".06"/>')   # IR beam
    add('<ellipse cx="780" cy="381" rx="70" ry="3" fill="#000" opacity=".45"/>')         # contact shadow
    # rear motor + gearbox
    add(f'<rect x="748" y="356" width="64" height="10" rx="5" fill="{STEEL_HI}"/>')
    add('<rect x="752" y="358" width="56" height="2" fill="#3A4558"/>')
    # chassis PCB with gold edge plating
    add('<rect x="716" y="346" width="128" height="10" rx="2" fill="#0D2A20"/>')
    add(f'<rect x="716" y="346" width="128" height="1.5" fill="{GOLD}" opacity=".8"/>')
    for k in range(9):
        add(f'<rect x="{724 + k * 13}" y="352" width="5" height="2" fill="{GOLD}" opacity=".7"/>')
    # LiPo pack
    add('<rect x="724" y="333" width="34" height="13" rx="2" fill="#2C3442"/>')
    add('<rect x="726" y="335" width="30" height="3" fill="#3B4456"/>')
    add(f'<path d="M758 338 C764 338 764 344 770 344" stroke="{RED}" stroke-width="1.5" fill="none"/>')
    # MCU (QFP) + status LED
    add('<rect x="772" y="336" width="26" height="10" rx="1" fill="#0B0D11"/>')
    for k in range(6):
        add(f'<rect x="{774 + k * 4}" y="334" width="2" height="2" fill="{GOLD}"/>')
    add(f'<circle class="blink-slow" cx="804" cy="341" r="2.2" fill="{CYAN}" filter="url(#glowC)"/>')
    # IMU + driver
    add('<rect x="810" y="339" width="12" height="7" rx="1" fill="#14181F"/>')
    # front sensor mast with IR emitters
    add('<rect x="828" y="326" width="12" height="20" rx="2" fill="#14181F"/>')
    for k, yy in enumerate((330, 338)):
        add(f'<circle class="blink" cx="841" cy="{yy}" r="2" fill="{RED}" opacity=".85" '
            f'style="animation-delay:{-k * 1.2:.1f}s"/>')
    add('<rect x="830" y="329" width="4" height="4" fill="#2A3240"/><rect x="830" y="337" width="4" height="4" fill="#2A3240"/>')
    # wheels (slow spin)
    for cx in (744, 816):
        add(f'<circle cx="{cx}" cy="366" r="14" fill="#0B0D11"/>')
        add(f'<circle cx="{cx}" cy="366" r="10" fill="#1B212B"/>')
        add(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} 366" to="360 {cx} 366" dur="4.8s" repeatCount="indefinite"/>'
            + ''.join(f'<rect x="{cx - 1}" y="357" width="2" height="7" fill="#3A4558" transform="rotate({a} {cx} 366)"/>' for a in (0, 120, 240))
            + '</g>')
        add(f'<circle cx="{cx}" cy="366" r="3" fill="{GOLD}"/>')
    add('</g>')

    # bench power supply -------------------------------------------------------------------------------
    add(r(880, 318, 116, 62, "#cfd4de", 'rx="3"'))
    add(r(886, 324, 104, 30, "#0b0f16"))
    add(f'<text x="892" y="344" font-size="15" font-weight="700" fill="{RED}" filter="url(#glowA)">05.00</text>')
    add(f'<text x="944" y="344" font-size="15" font-weight="700" fill="{GREEN}" filter="url(#glowC)">0.25</text>')
    add(f'<circle class="blink-slow" cx="892" cy="366" r="3" fill="{GREEN}"/>')
    for k, col in enumerate(["#d23030", "#1c1c1c", "#1f8a3a"]):
        add(f'<circle cx="{938 + k * 18}" cy="366" r="6" fill="{col}" stroke="#666" stroke-width="1"/>')

    # robot arm -------------------------------------------------------------------------------------------
    add(r(1012, 364, 46, 16, "#2a3a5c", 'rx="3"'))
    add(r(1026, 352, 18, 14, "#3c4a6b"))
    add('<g shape-rendering="geometricPrecision">'
        '<animateTransform attributeName="transform" type="rotate" values="-18 1035 356;14 1035 356;-18 1035 356" dur="5s" repeatCount="indefinite"/>'
        f'<rect x="1030" y="304" width="10" height="54" fill="{AMBER}" rx="4"/>'
        '<circle cx="1035" cy="356" r="7" fill="#1b2338" stroke="#9aa6bd" stroke-width="2"/>'
        '<g>'
        '<animateTransform attributeName="transform" type="rotate" values="50 1035 308;95 1035 308;50 1035 308" dur="5s" repeatCount="indefinite"/>'
        f'<rect x="1031" y="268" width="8" height="42" fill="{AMBER}" rx="4"/>'
        '<circle cx="1035" cy="308" r="6" fill="#1b2338" stroke="#9aa6bd" stroke-width="2"/>'
        '<rect x="1027" y="262" width="16" height="6" fill="#9aa6bd"/>'
        '<rect x="1027" y="254" width="4" height="9" fill="#9aa6bd"><animate attributeName="x" values="1027;1031;1027" dur="5s" repeatCount="indefinite"/></rect>'
        '<rect x="1039" y="254" width="4" height="9" fill="#9aa6bd"><animate attributeName="x" values="1039;1035;1039" dur="5s" repeatCount="indefinite"/></rect>'
        '</g></g>')
    add(f'<circle class="blink" cx="1050" cy="372" r="2.5" fill="{GREEN}"/>')

    # soldering station -------------------------------------------------------------------------------------
    add(r(1084, 340, 92, 40, "#1d2436", 'rx="4"'))
    add(r(1092, 348, 44, 18, "#0b0f16"))
    add(f'<text x="1096" y="362" font-size="13" font-weight="700" fill="{AMBER}" filter="url(#glowA)">350°</text>')
    add(f'<circle class="blink" cx="1152" cy="356" r="4" fill="{RED}"/>')
    add('<circle cx="1164" cy="356" r="6" fill="#0b0f16" stroke="#4d5c80" stroke-width="2"/>')
    add('<path d="M1150 340 L1176 276" stroke="#3a3f4f" stroke-width="4" shape-rendering="geometricPrecision"/>')
    add('<path d="M1166 300 L1180 266" stroke="#1a1a1a" stroke-width="8" stroke-linecap="round" shape-rendering="geometricPrecision"/>')
    add('<path d="M1180 266 L1186 252" stroke="#c0c6d4" stroke-width="3" shape-rendering="geometricPrecision"/>')
    for i in range(4):
        add(f'<circle class="smoke" cx="1186" cy="250" r="3.5" fill="#cfd8e8" '
            f'style="animation-delay:{-i * 0.8:.2f}s" filter="url(#soft)"/>')

    # ticker -----------------------------------------------------------------------------------------------------
    add(r(0, 472, W, 28, "#03060d"))
    add(r(0, 472, W, 1, CYAN_DIM))
    msg = ("● ONLINE  ·  ELECTRICAL ENGINEERING @ UNIVERSITY OF MORATUWA  ·  "
           "NOW BUILDING: NEOMOUSE V2  ·  EMBEDDED C++ · PID · KiCad  ·  OPEN TO INTERNSHIPS  ·")
    add('<g clip-path="url(#tickerClip)"><g class="ticker">')
    for k in range(3):
        add(f'<text x="{20 + k * 1240}" y="491" font-size="12" fill="{CYAN}" textLength="1200" lengthAdjust="spacingAndGlyphs">{msg}</text>')
    add('</g></g>')

    add("</g>")  # frame clip
    add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="{LINE}" stroke-width="2"/>')
    add("</svg>")
    return "\n".join(p)


def footer() -> str:
    W, H = 1200, 120
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="End of datasheet">
  <style>
    text {{ font-family: {MONO}; }}
    .p {{ stroke-dasharray: 26 600; animation: f 3.2s linear infinite; }}
    .p2 {{ animation-delay: -1.6s; }}
    @keyframes f {{ from {{ stroke-dashoffset: 626 }} to {{ stroke-dashoffset: 0 }} }}
    .blink {{ animation: b 1.2s steps(1) infinite; }}
    @keyframes b {{ 50% {{ opacity: .15 }} }}
  </style>
  <defs><filter id="g"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
  <path d="M0 40 H360 L390 70 H560" fill="none" stroke="{COPPER}" stroke-width="3"/>
  <path d="M1200 40 H840 L810 70 H640" fill="none" stroke="#2F6FB0" stroke-width="3"/>
  <path class="p" d="M0 40 H360 L390 70 H560" fill="none" stroke="#eaffff" stroke-width="3" filter="url(#g)"/>
  <path class="p p2" d="M1200 40 H840 L810 70 H640" fill="none" stroke="#eaffff" stroke-width="3" filter="url(#g)"/>
  <rect x="560" y="50" width="80" height="40" rx="3" fill="#111" stroke="#555"/>
  {''.join(f'<rect x="{566 + i * 12}" y="44" width="6" height="6" fill="#C9A227"/><rect x="{566 + i * 12}" y="90" width="6" height="6" fill="#C9A227"/>' for i in range(6))}
  <text x="600" y="74" font-size="11" fill="#bbb" text-anchor="middle">MM-29</text>
  <circle cx="360" cy="40" r="5" fill="#C9A227"/><circle cx="840" cy="40" r="5" fill="#C9A227"/>
  <circle class="blink" cx="600" cy="62" r="2.5" fill="{GREEN}"/>
  <text x="600" y="114" font-size="12" fill="{TEXT_DIM}" text-anchor="middle" letter-spacing="3">MADUKZ SPACE · END OF DATASHEET · BUILT ON A BENCH IN SRI LANKA</text>
</svg>"""


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "madukz-space.svg").write_text(hero(), encoding="utf-8")
    (ASSETS / "footer.svg").write_text(footer(), encoding="utf-8")
    print("assets written to", ASSETS)


if __name__ == "__main__":
    main()
