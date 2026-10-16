"""Draws the basement test room floor/walls at native 320x240 (shown at 3x in game).
Hand-made flat art: no AI generation. Run: python tools/gen_basement_floor.py"""
import random
from PIL import Image, ImageDraw

random.seed(3)
W, H = 320, 240
VOID, WALL_TOP, WALL, EDGE = (14, 14, 14), (24, 24, 25), (34, 34, 35), (88, 86, 82)
FLOOR, SEAM, SPECK = (46, 46, 46), (41, 41, 41), (56, 56, 55)

im = Image.new('RGBA', (W, H), VOID + (255,))
d = ImageDraw.Draw(im)
d.rectangle((14, 64, W - 15, H - 1), fill=FLOOR)
for x in range(14 + 32, W - 15, 32):          # large floor panels: 32 native px = 96 screen px
    d.line((x, 64, x, H - 1), fill=SEAM)
for y in range(64 + 32, H, 32):
    d.line((14, y, W - 15, y), fill=SEAM)
for _ in range(60):
    d.point((random.randint(16, W - 18), random.randint(66, H - 2)), fill=SPECK)
d.rectangle((0, 0, W - 1, 39), fill=WALL_TOP)             # back wall top
d.rectangle((14, 40, W - 15, 63), fill=WALL)              # back wall face
d.line((14, 40, W - 15, 40), fill=EDGE)
d.rectangle((0, 0, 13, H - 1), fill=WALL_TOP); d.line((13, 40, 13, H - 1), fill=EDGE)
d.rectangle((W - 14, 0, W - 1, H - 1), fill=WALL_TOP); d.line((W - 15, 40, W - 15, H - 1), fill=EDGE)
d.rectangle((W - 15, 120, W - 1, 175), fill=FLOOR)        # exit on the right
d.rectangle((150, 0, 169, 30), fill=WALL); d.rectangle((146, 30, 173, 35), fill=EDGE)  # ceiling chute

# --- cleared walkway from the rug to the exit (native px), with faded hazard dashes on both sides
PATH = [(160, 146), (166, 166), (192, 178), (236, 172), (276, 154), (319, 148)]
WALK, DASH, DASH_DARK = (54, 54, 53), (110, 92, 52), (70, 60, 40)
HALF = 13


def samples(pts, step=1.0):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / step))
        out += [(x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n) for t in range(n)]
    return out + [pts[-1]]


pts = samples(PATH)
WALK_FLOOR, TAPE_Y, TAPE_K, ARROW = (66, 66, 63), (176, 146, 70), (30, 28, 26), (120, 112, 92)


def in_walk(x, y):
    return any(((x - px) / HALF) ** 2 + ((y - py) / (HALF * 0.75)) ** 2 <= 1 for px, py in pts[::2])


mask = {(x, y) for x in range(14, W - 1) for y in range(64, H) if in_walk(x, y)}
TRACK, BERM_D, BERM_L = (52, 52, 50), (36, 36, 36), (74, 72, 68)
for x, y in mask:                                          # swept floor: cleaner and a bit lighter than the rest
    d.point((x, y), fill=WALK_FLOOR)
edge = [(x, y) for x, y in mask if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
rb = random.Random(7)
for x, y in edge:                                          # berm: grit pushed to the sides when the lane was cleared
    if rb.random() < 0.55:
        w, h = rb.randint(1, 3), rb.randint(1, 2)
        ox, oy = x + rb.randint(-1, 1), y + rb.randint(-1, 1)
        d.rectangle((ox, oy, ox + w - 1, oy + h - 1), fill=BERM_D if rb.random() < 0.7 else BERM_L)
for i in range(3, len(pts) - 3):                           # two worn wheel tracks running toward the exit
    (x0, y0), (x1, y1) = pts[i - 3], pts[i + 3]
    ux, uy = x1 - x0, y1 - y0
    n = (ux * ux + uy * uy) ** 0.5 or 1
    nx, ny = -uy / n, ux / n
    cx, cy = pts[i]
    for off in (-4.5, 4.5):
        if (i // 9) % 5 == 4:                              # tracks fade in and out
            continue
        d.point((round(cx + nx * off), round(cy + ny * off)), fill=TRACK)

# --- the old rug SeeU wakes up on (under the chute), frayed and worn
RUG = (136, 128, 184, 160)
RUG_BASE, RUG_DARK, RUG_LIGHT, RUG_BORDER = (86, 52, 48), (62, 38, 36), (112, 74, 62), (120, 100, 70)
x0, y0, x1, y1 = RUG
d.rectangle(RUG, fill=RUG_BASE)
d.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), outline=RUG_BORDER)
d.rectangle((x0 + 5, y0 + 5, x1 - 5, y1 - 5), outline=RUG_DARK)
for k in range(0, (x1 - x0) // 2 - 8, 6):                  # simple diamond motif down the middle
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    d.polygon([(cx - k - 3, cy), (cx - k, cy - 3), (cx - k + 3, cy), (cx - k, cy + 3)], outline=RUG_LIGHT)
    d.polygon([(cx + k - 3, cy), (cx + k, cy - 3), (cx + k + 3, cy), (cx + k, cy + 3)], outline=RUG_LIGHT)
for x in range(x0, x1 + 1, 2):                            # frayed tassels on the short edges
    d.point((x, y0 - 1), fill=RUG_BORDER); d.point((x + 1, y1 + 1), fill=RUG_BORDER)
for hx, hy, hw in ((x0 + 8, y1 - 6, 3), (x1 - 12, y0 + 7, 2)):   # worn holes showing the floor
    d.rectangle((hx, hy, hx + hw, hy + 1), fill=FLOOR)
d.rectangle((x1 - 6, y1 - 4, x1, y1), fill=WALK)           # one corner folded/missing

im.save('assets/env/basement/room_floor.png')
print('saved assets/env/basement/room_floor.png')
