"""The left panel's illustration: the Stack seen from outside (docs/WORLD.md) - a golden glass tower shaped like
Seoul's 63 Building, cyberpunk inside and around it, the tallest tower in the world. The picture is tall (480x2160); the panel shows a 1080-high
window of it and rises as SeeU climbs. The tower is enormous next to the game's rooms: neighbouring rooms are a
few pixels apart on it (PLACES).

Two steps - the final picture is PixelLab Pro art; this script draws its composition guide and assembles it:

  python tools/art/gen_stack_map.py --guide
      -> build/stack_guide.png (480x2160) and build/stack_guide_{top,bottom}.png (the two 480x1080 halves)
      PixelLab create_image_pro, one call per half at GEN_SIZE, the half as the labelled composition reference
      (and the finished top half as the style reference for the bottom). Prompts and job ids: docs/ASSETS.md.
  python tools/art/widen_stack_top.py tools/art/source/stack_top_raw.png tools/art/source/stack_top.png
      (PixelLab draws the upper floors narrower than asked; this widens them to match the lower half)
  python tools/art/gen_stack_map.py --finish tools/art/source/stack_top.png tools/art/source/stack_bottom.png          tools/art/source/stack_seam.png          (the PixelLab outputs, kept in tools/art/source/)
      -> assets/ui/stack_map.png: the halves stacked, the inpainted 240x240 seam patch (a cloud bank over the
         seam) at SEAM_PATCH_Y, then x2

The guide, bottom to top (the way the game climbs):
  L0  the recycle bin: a landfill of discontinued voicebanks around the tower's foot. A chute from the tower's underside
      lights the hollow where SeeU wakes; right beside it the elevator's foot (the freight elevator hall).
  The tower of the VOCALOIDs - every singer lives in it, but no person is drawn (no silhouettes) and signs use
  numbers and English, not Korean: its facade is a giant piano roll (the keyboard up the left edge, lit windows
  are note bars). The floors are classes of fame,
  split by total views (the Snowpiercer idea, docs/WORLD.md):
  L1  views in the hundreds: dark practice rooms; shacks, pipes and cables cling to the base.
  L2  10K views: cover songs, a play counter that barely moves.
  L3  1M views: fan art, music-note bubbles.
  --  a mechanical floor (louvres) inside the cloud sea - where the two generated halves meet.
  L4  100M views: the live stage - a screen with a giant note over a waveform, glow sticks, spotlights.
  --  the firewall: a red laser ring, the VIP gate between the classes.
  L5  1B views: platinum glass up to the sloped crown, a hall-of-fame band of platinum records under it.
  Each class has its own facade material, like medal grades: rusted iron, bronze, silver, gold, platinum.
  The world's tallest tower: the middle floors are wedged in a sea of clouds (the internet's "cloud"), the top
  stands in the near-black, starry stratosphere, other towers are tiny and hazy far below.
Rendering law: the higher, the more lit and the cleaner; the base is dark, cluttered and partly unrendered.
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 480, 2160
HALF = H // 2                                  # the seam between the two generated halves
GEN_SIZE = (240, 540)                          # PixelLab canvas per half; shown at 2x
SS = 3
GUIDE = "build/stack_guide.png"
OUT = "assets/ui/stack_map.png"
GROUND = 1860                                  # where the tower's foot meets the landfill
# the tower's front face (63 Building: a gentle taper, the crown sloping up to the right)
TOWER = {"lb": (30, GROUND), "lt": (44, 150), "rb": (392, GROUND), "rt": (378, 112)}   # the world's tallest: it fills the view,
# almost the same width all the way up (a very gentle taper)
DEPTH = 30                                     # the side face receding to the right
KEYS_W = 10                                    # the piano keyboard up the facade's left edge
OB = (0.62, -0.34)
ZONES = [  # name, top y, bottom y (on the facade), lit share, glow colours
    ("L5", 112, 680, 0.85, ["gold", "white"]),
    ("FW", 680, 720, 0.0, []),
    ("L4", 720, 1060, 0.6, ["pink", "violet", "cyan"]),
    ("MECH", 1060, 1100, 0.0, []),
    ("L3", 1100, 1360, 0.45, ["warm", "amber"]),
    ("L2", 1360, 1610, 0.16, ["yellow", "blue"]),
    ("L1", 1610, GROUND, 0.07, ["green"]),
]
LIFT = (438, 450)
CX_GATE = 211                                  # where the firewall's VIP mark sits
PLACES = {"BasementTest": (367, 2102), "ElevatorHall": (407, 2102)}   # on the finished art (px); the game reads Game.PLACES

BG = (11, 12, 14)
INK = (206, 212, 222)
INK2 = (128, 136, 148)
INK3 = (58, 63, 72)
FRONT = (21, 23, 27)
SIDE = (14, 15, 18)
TOP = (30, 33, 38)
ACC = {
    "teal": (64, 206, 210), "magenta": (214, 80, 190), "green": (88, 224, 128), "amber": (240, 188, 92),
    "yellow": (226, 210, 120), "blue": (130, 160, 230), "warm": (255, 176, 104), "red": (255, 84, 70),
    "pink": (255, 110, 220), "violet": (150, 130, 255), "cyan": (90, 236, 255), "orange": (255, 130, 40),
    "gold": (246, 210, 120), "white": (246, 248, 252),
}
GLASS_HI = (196, 156, 76)
# each class has its own facade, like medal grades: rusted iron, bronze, silver, gold, platinum at the top
TIER_GLASS = {"L1": (58, 46, 40), "L2": (104, 66, 36), "L3": (118, 126, 140), "MECH": (40, 40, 46),
              "L4": (150, 116, 44), "FW": (60, 20, 18), "L5": (206, 212, 226)}


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Ink:
    """Ink and neon on two layers: `base` (lines, fills) and `glow` (blurred and added at the end)."""

    def __init__(self):
        self.base = Image.new("RGB", (W * SS, H * SS), BG)
        self.glow = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
        self.d = ImageDraw.Draw(self.base)
        self.g = ImageDraw.Draw(self.glow)
        self.fonts = {}

    @staticmethod
    def s(pts):
        return [(x * SS, y * SS) for x, y in pts]

    def line(self, pts, col, w=1.0, glow=None, gw=3.0):
        self.d.line(self.s(pts), fill=col, width=max(1, round(w * SS)), joint="curve")
        if glow:
            self.g.line(self.s(pts), fill=glow, width=max(1, round(gw * SS)), joint="curve")

    def poly(self, pts, fill=None, outline=None, w=1.0, glow=None):
        if fill:
            self.d.polygon(self.s(pts), fill=fill)
        if glow:
            self.g.polygon(self.s(pts), fill=glow)
        if outline:
            self.line(list(pts) + [pts[0]], outline, w)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, w=1.0, glow=None):
        if fill:
            self.d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill)
        if outline:
            self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], outline, w)
        if glow:
            self.g.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=glow)

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, w=1.0, glow=None, gw=3.0):
        box = [(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS]
        if fill:
            self.d.ellipse(box, fill=fill)
        if outline:
            self.d.ellipse(box, outline=outline, width=max(1, round(w * SS)))
        if glow:
            self.g.ellipse(box, outline=glow, width=max(1, round(gw * SS)))

    def text(self, x, y, s, size, col, glow=None, anchor="la"):
        f = self.font(size)
        if f is None:
            return
        self.d.text((x * SS, y * SS), s, fill=col, font=f, anchor=anchor)
        if glow:
            self.g.text((x * SS, y * SS), s, fill=glow, font=f, anchor=anchor, stroke_width=SS, stroke_fill=glow)

    def font(self, size):
        if size not in self.fonts:
            path = "C:/Windows/Fonts/malgunbd.ttf"
            self.fonts[size] = ImageFont.truetype(path, round(size * SS)) if os.path.exists(path) else None
        return self.fonts[size]

    def finish(self):
        blur = self.glow.filter(ImageFilter.GaussianBlur(4 * SS))
        wide = self.glow.filter(ImageFilter.GaussianBlur(14 * SS))
        out = ImageChops.add(self.base, ImageChops.multiply(blur, Image.new("RGB", blur.size, (190, 190, 190))))
        out = ImageChops.add(out, ImageChops.multiply(wide, Image.new("RGB", wide.size, (110, 110, 110))))
        return out.resize((W, H), Image.LANCZOS)


def ob(depth):
    return OB[0] * depth, OB[1] * depth


def edge_x(y, side):
    """x of the tower's left or right front edge at row y."""
    (bx, by), (tx, ty) = (TOWER["lb"], TOWER["lt"]) if side == "l" else (TOWER["rb"], TOWER["rt"])
    return bx + (tx - bx) * (by - y) / (by - ty)


def box3d(k, x0, y0, x1, y1, depth, front=FRONT, edge=INK2, w=0.7):
    dx, dy = ob(depth)
    k.poly([(x1, y0), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1)], fill=SIDE)
    k.poly([(x0, y0), (x0 + dx, y0 + dy), (x1 + dx, y0 + dy), (x1, y0)], fill=TOP)
    k.rect(x0, y0, x1, y1, fill=front)
    k.line([(x1, y0), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1)], edge, w)
    k.line([(x0, y0), (x0 + dx, y0 + dy), (x1 + dx, y0 + dy)], edge, w)
    k.rect(x0, y0, x1, y1, outline=edge, w=w)


def cable(k, a, b, sag, col=INK3, w=0.6):
    pts = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t))
           for t in (i / 24 for i in range(25))]
    k.line(pts, col, w)


def sign(k, x, y, txt, col, size=10, pad=3):
    """Vertical neon sign."""
    hgt = len(txt) * size * 1.05 + pad * 2
    k.rect(x - size / 2 - pad, y, x + size / 2 + pad, y + hgt, fill=(8, 9, 11), outline=col, w=0.8)
    k.g.rectangle([(x - size / 2 - pad) * SS, y * SS, (x + size / 2 + pad) * SS, (y + hgt) * SS],
                  outline=mix(col, (0, 0, 0), 0.4), width=2 * SS)
    for i, ch in enumerate(txt):
        k.text(x, y + pad + i * size * 1.05, ch, size, mix(col, (255, 255, 255), 0.35),
               glow=mix(col, (0, 0, 0), 0.2), anchor="ma")


def antenna(k, x, y, hgt, blink=None):
    k.line([(x, y), (x, y - hgt)], INK2, 0.6)
    for i in range(1, 4):
        yy = y - hgt * i / 4
        k.line([(x - 4 + i, yy), (x + 4 - i, yy)], INK3, 0.6)
    if blink:
        k.ellipse(x, y - hgt, 0.9, 0.9, fill=blink, glow=blink, gw=2)


# ------------------------------------------------------------------------------------------------ the scene

CLOUDS = (980, 1250)                            # the cloud sea the middle floors are wedged in (covers the seam)


def sky_color(y):
    """Stratosphere at the top (near black, deep navy), dusk violet at the clouds, smog brown below them."""
    stops = [(0, (4, 6, 18)), (420, (10, 18, 48)), (900, (40, 46, 96)), (1100, (92, 84, 130)),
             (1300, (52, 44, 62)), (1700, (28, 24, 30)), (H, (16, 15, 18))]
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        if y <= y1:
            return mix(c0, c1, (y - y0) / max(1, y1 - y0))
    return stops[-1][1]


def draw_background(k):
    for y in range(H):
        k.line([(0, y), (W, y)], sky_color(y), 1.0)
    rng = random.Random(7)
    for _ in range(260):                                                             # stars thin out toward the clouds
        x, y = rng.uniform(0, W), rng.uniform(0, 760) ** 1.0
        if rng.random() < 1 - y / 800:
            r = 0.6 if rng.random() < 0.85 else 1.1
            k.ellipse(x, y, r, r, fill=mix((230, 236, 255), sky_color(y), 0.2 + 0.6 * y / 800))
    k.line([(0, 560), (W, 548)], (44, 70, 140), 2.0, glow=(20, 40, 90), gw=10)       # the thin blue edge of the air
    # far below the clouds: other towers of the world, tiny and hazy next to this one
    for x, wdt, top in ((2, 10, 1480), (14, 7, 1600), (458, 14, 1420), (470, 8, 1560), (446, 6, 1660)):
        k.rect(x, top, x + wdt, H, fill=mix(sky_color(top), (0, 0, 0), 0.4))
        for y in range(top + 6, H, 9):
            if (x + y) % 3 == 0:
                k.rect(x + 2, y, x + 3, y + 1, fill=mix(ACC["amber"], sky_color(y), 0.5))
    draw_clouds(k, back=True)


def draw_clouds(k, back):
    """The cloud sea around the middle floors: a back layer behind the tower, puffs in front of it."""
    rng = random.Random(31 if back else 32)
    top, bot = CLOUDS
    for _ in range(70 if back else 46):
        y = rng.uniform(top, bot)
        x = rng.uniform(-30, W + 30)
        if not back and edge_x(y, "l") + 30 < x < edge_x(y, "r") - 30 and rng.random() < 0.5:
            continue                                                                  # leave windows to see the tower
        rx, ry = rng.uniform(30, 80), rng.uniform(10, 22)
        shade = (y - top) / (bot - top)
        body = mix((236, 230, 246), (150, 140, 176), shade)
        k.ellipse(x, y, rx, ry, fill=mix(body, (0, 0, 0), 0.15 if back else 0.0))
        k.ellipse(x - rx * 0.2, y - ry * 0.35, rx * 0.7, ry * 0.6, fill=mix(body, (255, 255, 255), 0.25))


def draw_beams(k):
    """Spotlights from the stage floors raking the dark."""
    layer = Image.new("RGB", k.base.size, (0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for ox, oy, ang, c in ((112, 730, -2.3, "violet"), (140, 722, -2.0, "pink"), (330, 715, -1.2, "cyan"),
                           (360, 722, -0.9, "violet")):
        ln, spread = 700, 0.05
        a = (ox + math.cos(ang - spread) * ln, oy + math.sin(ang - spread) * ln)
        b = (ox + math.cos(ang + spread) * ln, oy + math.sin(ang + spread) * ln)
        ld.polygon(Ink.s([(ox, oy), a, b]), fill=mix(ACC[c], (0, 0, 0), 0.8))
    k.base.paste(ImageChops.add(k.base, layer.filter(ImageFilter.GaussianBlur(3 * SS))))


def draw_tower(k):
    """The tower: front and side faces, each class in its own material, panes lit by what is inside."""
    lb, lt, rb, rt = TOWER["lb"], TOWER["lt"], TOWER["rb"], TOWER["rt"]
    dx, dy = ob(DEPTH)
    front = [lb, lt, rt, rb]
    for name, top, bot, _lit, _cols in ZONES:                                      # each class's own material
        glass = TIER_GLASS[name]
        yt = max(top, rt[1])
        k.poly([(edge_x(yt, "l"), yt), (edge_x(yt, "r"), yt), (edge_x(bot, "r"), bot), (edge_x(bot, "l"), bot)], fill=glass)
        k.poly([(edge_x(yt, "r"), yt), (edge_x(yt, "r") + dx, yt + dy), (edge_x(bot, "r") + dx, bot + dy),
                (edge_x(bot, "r"), bot)], fill=mix(glass, (0, 0, 0), 0.45))
        k.line([(edge_x(top, "l") - 3, top), (edge_x(top, "r") + 3, top)], mix(glass, (255, 255, 255), 0.4), 1.2)  # trim
    rng = random.Random(3)
    BLACK_KEYS = {1, 3, 6, 8, 10}                                                   # semitones of an octave
    for name, top, bot, lit, cols in ZONES:
        y = top
        while y < bot - 1:
            xl, xr = edge_x(y, "l") + 2, edge_x(y, "r") - 2
            if name in ("FW", "MECH"):
                break
            key = (-y // 6) % 12
            lane = mix(TIER_GLASS[name], (0, 0, 0), 0.15 + 0.25 * (y / H) + (0.12 if key in BLACK_KEYS else 0.0))
            k.rect(xl + KEYS_W, y, xr, y + 4, fill=lane)                              # the piano-roll lane
            # the keyboard up the left edge, like the singing-synth editor's
            k.rect(xl, y, xl + KEYS_W - 1, y + 5, fill=(32, 30, 36) if key in BLACK_KEYS else (226, 222, 210))
            x = xl + KEYS_W + 2
            while x < xr - 6:
                roof_y = lt[1] + (rt[1] - lt[1]) * (x - lt[0]) / (rt[0] - lt[0])   # the crown slopes
                if y > roof_y + 3 and rng.random() < lit * 0.45:
                    ln = rng.choice((4, 6, 9, 14, 20))                               # a note: its length is its duration
                    c = ACC[cols[rng.randrange(len(cols))]]
                    k.rect(x, y, min(x + ln, xr - 1), y + 3, fill=mix(c, TIER_GLASS[name], 0.2), glow=mix(c, (0, 0, 0), 0.55))
                    x += ln + rng.choice((2, 4, 8))
                else:
                    x += rng.choice((4, 6, 10))
            y += 6
        for yy in range(top, bot, 6):                                              # the side face's storeys
            k.line([(edge_x(yy, "r"), yy), (edge_x(yy, "r") + dx, yy + dy)], mix(TIER_GLASS[name], (0, 0, 0), 0.6), 0.6)
    # the mechanical floor: louvres across the facade
    for y in range(1062, 1098, 4):
        k.line([(edge_x(y, "l"), y), (edge_x(y, "r"), y)], INK3, 1.4)
    k.line([(edge_x(1060, "l"), 1060), (edge_x(1060, "r"), 1060)], GLASS_HI, 1.0)
    k.line([(edge_x(1100, "l"), 1100), (edge_x(1100, "r"), 1100)], GLASS_HI, 1.0)
    # reflections: diagonal streaks across the glass
    refl = Image.new("RGB", k.base.size, (0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for x0, wdt in ((40, 30), (120, 12), (190, 46)):
        rd.polygon(Ink.s([(x0, GROUND), (x0 + wdt, GROUND), (x0 + wdt + 300, 100), (x0 + 300, 100)]), fill=(40, 32, 14))
    mask = Image.new("L", k.base.size, 0)
    ImageDraw.Draw(mask).polygon(Ink.s(front), fill=255)
    k.base.paste(ImageChops.add(k.base, refl), mask=mask)
    k.line(front + [lb], GLASS_HI, 1.0)
    k.line([rt, (rt[0] + dx, rt[1] + dy), (rb[0] + dx, rb[1] + dy)], mix(GLASS_HI, BG, 0.4), 0.8)
    k.poly([lt, rt, (rt[0] + dx, rt[1] + dy), (lt[0] + dx * 0.4, lt[1] + dy * 0.4)], fill=(150, 118, 56))
    k.line([lt, rt], (255, 230, 160), 1.2, glow=(120, 96, 40), gw=4)



def draw_firewall(k):
    top, bot = 680, 720
    xl, xr = edge_x(bot, "l") - 24, edge_x(top, "r") + DEPTH * 0.62 + 18
    for i, y in enumerate(range(top + 4, bot - 2, 4)):
        k.line([(xl, y), (xr, y - 8)], mix(ACC["red"], BG, 0.15 + 0.1 * (i % 2)), 1.0, glow=mix(ACC["red"], (0, 0, 0), 0.25))
    for x in (xl - 5, xr):
        k.rect(x, top - 4, x + 6, bot + 2, fill=TOP, outline=INK, w=0.7)
        k.ellipse(x + 3, top + 4, 1.6, 1.6, fill=ACC["red"], glow=ACC["red"], gw=4)


def draw_story(k):
    """The class tower of VOCALOID fame (Snowpiercer: floors split by total views). Each tier says what it is:
    a view-count sign on the left edge, what goes on there on the right edge, and one thing on the glass."""
    # top: 1B views - a hall-of-fame band under the crown: one row of equal round windows set flush in a
    # dark band, each a platinum record (grooves, centre label) - part of the building, not stuck on it
    by = 250
    xl, xr = edge_x(by, "l"), edge_x(by, "r")
    k.rect(xl, by - 26, xr, by + 26, fill=(26, 28, 36), outline=(236, 240, 250), w=1.0)
    n = 5
    for i in range(n):
        x = xl + (xr - xl) * (i + 0.5) / n
        k.ellipse(x, by, 21, 21, fill=(18, 18, 22), outline=(236, 240, 250), w=1.6, glow=(90, 96, 120), gw=4)
        for r in (17, 13, 10):
            k.ellipse(x, by, r, r, outline=(70, 72, 84), w=0.5)
        k.ellipse(x, by, 6, 6, fill=(214, 176, 80))
        k.ellipse(x, by, 1.2, 1.2, fill=(18, 18, 22))
    # the stage tier (100M views): a concert screen showing a giant music note over a waveform (no people)
    x0, x1 = edge_x(900, "l") + 20, edge_x(900, "r") - 20
    k.rect(x0, 780, x1, 960, fill=(16, 10, 30), outline=INK2, w=1.0, glow=(30, 16, 60))
    mx, wy = (x0 + x1) / 2, 900
    pts = [(x, wy + math.sin((x - x0) / 7.0) * 24 * math.sin((x - x0) / (x1 - x0) * math.pi)) for x in range(int(x0) + 6, int(x1) - 6, 2)]
    k.line(pts, ACC["cyan"], 1.6, glow=mix(ACC["cyan"], (0, 0, 0), 0.4), gw=4)
    k.ellipse(mx - 10, 900, 16, 12, fill=ACC["pink"], glow=mix(ACC["pink"], (0, 0, 0), 0.3), gw=6)      # the note
    k.rect(mx + 3, 820, mx + 7, 900, fill=ACC["pink"])
    k.poly([(mx + 7, 820), (mx + 34, 836), (mx + 34, 850), (mx + 7, 836)], fill=ACC["pink"])
    for i in range(14):                                                               # a crowd of glow sticks
        x = x0 + 8 + i * 9
        c = ACC[("cyan", "pink", "yellow", "violet")[i % 4]]
        k.line([(x, 952), (x + 2, 942)], c, 1.4, glow=mix(c, (0, 0, 0), 0.4), gw=3)
    # the fan tier (1M views): fan-art board and music-note bubbles
    for bx, by, txt, c in ((edge_x(1180, "l") + 30, 1170, "♪♪", "cyan"), (edge_x(1250, "r") - 100, 1236, "♪", "pink"),
                           (edge_x(1300, "l") + 120, 1290, "♪", "yellow")):
        w = 14 + len(txt) * 10
        k.rect(bx, by, bx + w, by + 18, fill=mix(ACC[c], BG, 0.85), outline=mix(ACC[c], BG, 0.3), w=0.8,
               glow=mix(ACC[c], (0, 0, 0), 0.75))
        k.text(bx + w / 2, by + 2, txt, 11, mix(ACC[c], (255, 255, 255), 0.3), glow=mix(ACC[c], (0, 0, 0), 0.4), anchor="ma")
    # the cover tier (10K views): a play-count board that barely moves
    cx = (edge_x(1450, "l") + edge_x(1450, "r")) / 2 - 30
    k.rect(cx - 80, 1420, cx + 80, 1464, fill=(6, 6, 7), outline=INK2, w=0.8)
    k.text(cx, 1422, "▶ 12,034", 26, mix(ACC["orange"], BG, 0.1), glow=mix(ACC["orange"], (0, 0, 0), 0.3), anchor="ma")
    # the practice tier (views in the tens): dark rooms, an old keyboard in one lit window
    kx = edge_x(1720, "l") + 60
    k.rect(kx, 1700, kx + 40, 1712, fill=(20, 20, 24), outline=INK2, w=0.6)
    for i in range(9):
        k.line([(kx + 3 + i * 4, 1702), (kx + 3 + i * 4, 1710)], (200, 200, 205), 1.2)
    # view counts down the left edge, what each tier is down the right
    for y, count, what, c in ((300, "1B", "PLATINUM", "white"), (760, "100M", "LIVE", "pink"), (1140, "1M", "FAN", "warm"),
                              (1400, "10K", "COVER", "yellow"), (1640, "100", "DEMO", "green")):
        sign(k, edge_x(y + 20, "l") - 16, y, count, ACC[c], 11)
        sign(k, edge_x(y + 20, "r") + DEPTH * 0.62 + 14, y + 20, what, ACC[c], 10)
    # the gate between the classes
    k.text(CX_GATE, 682, "VIP", 14, (255, 220, 210), glow=mix(ACC["red"], (0, 0, 0), 0.2), anchor="ma")
    # the bottom: discontinued voicebanks
    sign(k, 40, 1880, "EOL", ACC["teal"], 10)


def draw_eq(k):
    """Equalizer bars glowing beside the stage floors."""
    for side, x0 in (("l", edge_x(940, "l") - 40), ("r", edge_x(940, "r") + DEPTH * 0.62 + 6)):  # EQ bars by the stage
        for i in range(6):
            h = (30, 52, 40, 64, 26, 46)[i]
            c = ACC[("pink", "cyan", "violet")[i % 3]]
            k.rect(x0 + i * 6, 960 - h, x0 + i * 6 + 3, 960, fill=mix(c, BG, 0.3), glow=mix(c, (0, 0, 0), 0.5))


def draw_base_slums(k):
    """Shacks, pipes and cables climbing the tower's foot: the dark, cluttered bottom."""
    rng = random.Random(21)
    for side in ("l", "r"):
        for _ in range(26):
            y0 = rng.randint(1480, GROUND - 16)
            w, h = rng.randint(6, 16), rng.randint(5, 12)                       # tiny next to the tower
            out = rng.randint(0, 14)
            if side == "l":
                x1 = edge_x(y0, "l") + rng.randint(4, 14) - out
                x0 = x1 - w
            else:
                x0 = edge_x(y0, "r") + DEPTH * 0.62 * rng.uniform(0.3, 1) - 6 + out
                x1 = x0 + w
                if x1 > LIFT[0] - 4:
                    continue
            box3d(k, x0, y0, x1, y0 + h, rng.randint(5, 12))
            for wy in range(int(y0) + 3, int(y0 + h) - 3, 5):
                for wx in range(int(x0) + 3, int(x1) - 3, 5):
                    if rng.random() < 0.12:
                        c = ACC[rng.choice(["green", "amber", "teal"])]
                        k.rect(wx, wy, wx + 2, wy + 2, fill=c, glow=mix(c, (0, 0, 0), 0.5))
            if rng.random() < 0.3:
                antenna(k, x0 + w / 2, y0, rng.randint(8, 18), ACC["red"] if rng.random() < 0.5 else None)
    for x in (edge_x(1700, "l") + 14, edge_x(1700, "l") + 20, edge_x(1700, "r") - 18):
        k.rect(x - 2, 1400, x + 2, GROUND, fill=TOP)
        k.line([(x - 2, 1400), (x - 2, GROUND)], INK2, 0.6)
    for a, b, s in (((30, 1500), (100, 1560), 30), ((330, 1540), (400, 1600), 26), ((40, 1700), (110, 1720), 20)):
        cable(k, a, b, s, INK3, 0.6)


def draw_landfill(k):
    """The landfill around the foot; the hollow where she wakes and, right beside it, the elevator's foot."""
    rng = random.Random(10)
    pts = [(0, GROUND - 30)]
    for x in range(0, W + 6, 6):
        peak = max(0, 50 - abs(x - 220) * 0.25) + max(0, 40 - abs(x - 40) * 0.5)
        pts.append((x, GROUND + 18 - peak + rng.uniform(-5, 5)))
    pts += [(W, H), (0, H)]
    k.poly(pts, fill=(16, 17, 20))
    k.line(pts[1:-2], INK2, 0.9)
    for _ in range(200):
        x, y = rng.uniform(4, W - 12), rng.uniform(GROUND + 12, H - 4)
        c = mix(INK3, INK2, rng.random() * 0.6)
        if rng.random() < 0.6:
            w, h, a = rng.uniform(4, 14), rng.uniform(2, 8), rng.uniform(-0.5, 0.5)
            corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
            k.poly([(x + cx * math.cos(a) - cy * math.sin(a), y + cx * math.sin(a) + cy * math.cos(a))
                    for cx, cy in corners], fill=(20, 22, 25), outline=c, w=0.5)
        else:
            r = rng.uniform(2, 5)
            k.ellipse(x, y, r, r * 0.8, fill=(18, 19, 22), outline=c, w=0.5)
    for x, y in ((120, 1980), (260, 2060), (60, 2100)):
        for i in range(4):
            for j in range(3):
                if (i + j) % 2 == 0:
                    k.rect(x + i * 3, y + j * 3, x + i * 3 + 2.6, y + j * 3 + 2.6,
                           fill=mix(ACC["magenta"], BG, 0.45), glow=mix(ACC["magenta"], (0, 0, 0), 0.75))
    hx, hy = PLACES["BasementTest"]
    k.rect(hx - 4, GROUND - 6, hx + 4, hy - 20, fill=TOP, outline=INK2, w=0.7)          # the chute
    k.ellipse(hx, hy - 4, 14, 10, fill=(6, 7, 8), outline=INK2, w=0.8)
    k.rect(hx - 14, hy - 4, hx + 14, hy + 5, fill=(6, 7, 8))
    k.poly([(hx - 3, hy - 18), (hx + 3, hy - 18), (hx + 6, hy + 2), (hx - 6, hy + 2)],
           fill=mix(ACC["teal"], BG, 0.75), glow=mix(ACC["teal"], (0, 0, 0), 0.5))
    k.rect(hx - 5, hy + 2, hx + 5, hy + 4, fill=(150, 70, 62))
    k.rect(hx + 14, hy - 2, LIFT[0], hy + 5, fill=(8, 9, 11), outline=INK3, w=0.5)     # a few steps to the lift
    k.ellipse(hx + 18, hy, 0.9, 0.9, fill=ACC["amber"], glow=mix(ACC["amber"], (0, 0, 0), 0.4), gw=4)


def draw_lift(k):
    a, b = LIFT
    top, bot = 140, PLACES["ElevatorHall"][1] + 8
    for x in (a, b):
        k.line([(x, top), (x, bot)], INK2, 0.8)
    for y in range(top, bot, 12):
        k.line([(a, y), (b, y + 12)], INK3, 0.5)
        k.line([(b, y), (a, y + 12)], INK3, 0.5)
    for y in (660, 1040, 1340, 1590, 1840):                                          # catwalks to the tower
        x0 = edge_x(y, "r") + DEPTH * 0.62 * 0.5
        k.rect(x0, y, a, y + 3, fill=TOP, outline=INK2, w=0.5)
    cy = PLACES["ElevatorHall"][1] - 12
    k.rect(a + 1, cy - 10, b - 1, cy + 12, fill=TOP, outline=INK, w=0.7)
    k.rect(a + 3, cy - 6, b - 3, cy - 1, fill=ACC["amber"], glow=mix(ACC["amber"], (0, 0, 0), 0.3))


def guide():
    k = Ink()
    draw_background(k)
    draw_beams(k)
    draw_tower(k)
    draw_firewall(k)
    draw_base_slums(k)
    draw_story(k)
    draw_eq(k)
    draw_landfill(k)
    draw_lift(k)
    draw_clouds(k, back=False)
    return k.finish()


SEAM_PATCH_Y = 420                              # where the inpainted seam patch (clouds over the seam) goes


# The lower half came back with a grey smog band under the clouds, so the background looked split in layers.
# Its sky is recoloured into one gradient continuing the violet above the clouds down to the dark at the
# landfill. Only the background strips beside the tower (outside the facade and the elevator lattice), only
# greyish pixels (neon signs keep their colour), and the original brightness is kept as detail.
SKY_COLS = [(0, 13), (206, 211), (233, 239)]                  # background columns of the lower half (native)
SKY_ROWS = (40, 430)                                          # rows graded; blends in/out over BLEND rows
SKY_FROM, SKY_TO = (44, 18, 84), (22, 9, 30)                  # violet under the clouds -> dark at the landfill
BLEND = 30


def grade_sky(bottom):
    px = bottom.load()
    y0, y1 = SKY_ROWS
    for y in range(y0, y1):
        t = (y - y0) / (y1 - y0)
        target = mix(SKY_FROM, SKY_TO, t)
        amount = min(1.0, (y - y0) / BLEND, (y1 - y) / BLEND)
        lum_ref = 62.0                                        # typical brightness of the grey smog
        for x0, x1 in SKY_COLS:
            for x in range(x0, x1 + 1):
                r, g, b = px[x, y]
                if max(r, g, b) - min(r, g, b) > 45:          # saturated: a neon sign, keep it
                    continue
                k = (0.3 * r + 0.59 * g + 0.11 * b) / lum_ref
                graded = tuple(min(255, round(c * k)) for c in target)
                px[x, y] = mix((r, g, b), graded, amount)
    return bottom


def finish(top_png, bottom_png, seam_png=None):
    """The PixelLab halves (GEN_SIZE each) stacked, the seam covered by the inpainted cloud patch, shown at 2x."""
    halves = []
    for p in (top_png, bottom_png):
        im = Image.open(p).convert("RGB")
        halves.append(im if im.size == GEN_SIZE else im.resize(GEN_SIZE, Image.NEAREST))
    grade_sky(halves[1])
    out = Image.new("RGB", (GEN_SIZE[0], GEN_SIZE[1] * 2))
    out.paste(halves[0], (0, 0))
    out.paste(halves[1], (0, GEN_SIZE[1]))
    if seam_png:
        out.paste(Image.open(seam_png).convert("RGB"), (0, SEAM_PATCH_Y))
    return out.resize((W, H), Image.NEAREST)


if __name__ == "__main__":
    if "--finish" in sys.argv:
        i = sys.argv.index("--finish")
        args = sys.argv[i + 1:i + 4]
        out = finish(*args)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        out.save(OUT)
        print(f"saved {OUT} {out.size}; places: {PLACES}")
    else:
        os.makedirs("build", exist_ok=True)
        im = guide()
        im.save(GUIDE)
        im.crop((0, 0, W, HALF)).save("build/stack_guide_top.png")
        im.crop((0, HALF, W, H)).save("build/stack_guide_bottom.png")
        print(f"saved {GUIDE} {im.size} + top/bottom halves")
