"""Draws the basement test room floor/walls at native 320x240 (shown at 3x in game).
Hand-made flat art: no AI generation. Run: python tools/gen_basement_floor.py

The side walls and the front (south) wall are real, solid walls with depth: their tops are drawn again on
their own layer (room_front.png) over everything in the room, so junk pushed against them is partly hidden
behind them instead of poking through. The front wall hides the bottom FRONT_H rows of the floor."""
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "art"))
from pix import KIND_CAP, KIND_FACE, KIND_FLOOR, save_height_map  # noqa: E402

random.seed(3)
W, H = 320, 240
FLOOR_BOTTOM = 227                # last floor row; the front wall stands south of it
FRONT_TOP = 204                   # first row of the front wall's top as seen (it hides floor rows 204..227)
EXIT_Y = (120, 175)               # opening in the right wall
VOID, WALL_TOP, WALL, EDGE = (14, 14, 14), (24, 24, 25), (34, 34, 35), (88, 86, 82)
FLOOR, SEAM, SPECK = (46, 46, 46), (41, 41, 41), (56, 56, 55)

im = Image.new('RGBA', (W, H), VOID + (255,))
d = ImageDraw.Draw(im)
d.rectangle((14, 64, W - 15, FLOOR_BOTTOM), fill=FLOOR)
for x in range(14 + 32, W - 15, 32):          # large floor panels: 32 native px = 96 screen px
    d.line((x, 64, x, FLOOR_BOTTOM), fill=SEAM)
for y in range(64 + 32, FLOOR_BOTTOM, 32):
    d.line((14, y, W - 15, y), fill=SEAM)
for _ in range(60):
    d.point((random.randint(16, W - 18), random.randint(66, FLOOR_BOTTOM - 1)), fill=SPECK)
d.rectangle((0, 0, W - 1, 39), fill=WALL_TOP)             # back wall top
d.rectangle((14, 40, W - 15, 63), fill=WALL)              # back wall face
d.line((14, 40, W - 15, 40), fill=EDGE)
d.rectangle((0, 0, 13, H - 1), fill=WALL_TOP); d.line((13, 40, 13, H - 1), fill=EDGE)
d.rectangle((W - 14, 0, W - 1, H - 1), fill=WALL_TOP); d.line((W - 15, 40, W - 15, H - 1), fill=EDGE)
d.rectangle((0, FLOOR_BOTTOM + 1, W - 1, H - 1), fill=WALL_TOP)   # front wall (its top is also on the front layer)
d.rectangle((W - 15, EXIT_Y[0], W - 1, EXIT_Y[1]), fill=FLOOR)   # exit on the right
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


mask = {(x, y) for x in range(14, W - 1) for y in range(64, FLOOR_BOTTOM + 1) if in_walk(x, y)}
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

# --- doorway sill across the exit, flush with the wall's inner face: the wall tops are unrendered (void dots),
#     so without it the opening reads as a missing tile instead of a door through a thick wall
d = ImageDraw.Draw(im)
d.line((W - 15, EXIT_Y[0], W - 15, EXIT_Y[1]), fill=EDGE)
d.line((W - 14, EXIT_Y[0], W - 14, EXIT_Y[1]), fill=BERM_D)
im.save('assets/env/basement/room_floor.png')
print('saved assets/env/basement/room_floor.png')

# --- height/normal companion for the lighting pass: same numbers as the drawing above
WALL_BASE, WALL_TOP_Y = 64, 40                      # back wall face rows 40..63 stand on the floor at y 64
WALL_H = WALL_BASE - WALL_TOP_Y                     # 24 px (~1.1 m) visible face; the band above is the wall's top


def cell(x, y):
    if 14 <= x <= W - 15 and WALL_BASE <= y <= FLOOR_BOTTOM:
        return 0, KIND_FLOOR                            # floor (rug, walkway and seams are all flat)
    if x >= W - 15 and EXIT_Y[0] <= y <= EXIT_Y[1]:
        return 0, KIND_FLOOR                            # exit opening in the right wall
    if 14 <= x <= W - 15 and WALL_TOP_Y <= y < WALL_BASE:
        return WALL_BASE - y, KIND_FACE                 # back wall face: height above its base
    return WALL_H, KIND_CAP                             # wall tops, side walls, the ceiling chute: never lit directly


save_height_map('assets/env/basement/room_floor.height.png', W, H, cell)
print('saved assets/env/basement/room_floor.height.png')


# --- the walls' tops again, on their own layer drawn over the room's contents (pixel_room.gd `front`):
#     left wall, right wall (open at the exit) and the front wall, which also hides FRONT_H floor rows
FRONT_H = FLOOR_BOTTOM + 1 - FRONT_TOP              # 24 px (~1.1 m), as tall as the back wall's face


def in_front_layer(x, y):
    if y >= FRONT_TOP:
        return True                                     # front wall
    if y < WALL_TOP_Y:
        return False                                    # the back wall's top stays behind things standing at it
    if x <= 13:
        return True                                     # left wall
    return x >= W - 14 and not (EXIT_Y[0] <= y <= EXIT_Y[1])   # right wall, open at the exit


front = Image.new('RGBA', (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(front)
for y in range(H):
    for x in range(W):
        if in_front_layer(x, y):
            front.putpixel((x, y), WALL_TOP + (255,))
fd.line((13, FRONT_TOP, W - 14, FRONT_TOP), fill=EDGE)                  # inner edges catch the light
fd.line((13, WALL_TOP_Y, 13, FRONT_TOP), fill=EDGE)
fd.line((W - 14, WALL_TOP_Y, W - 14, EXIT_Y[0] - 1), fill=EDGE)
fd.line((W - 14, EXIT_Y[1] + 1, W - 14, FRONT_TOP), fill=EDGE)
front.save('assets/env/basement/room_front.png')
print('saved assets/env/basement/room_front.png')
save_height_map('assets/env/basement/room_front.height.png', W, H,
                lambda x, y: (FRONT_H if y >= FRONT_TOP else WALL_H, KIND_CAP) if in_front_layer(x, y) else None)
print('saved assets/env/basement/room_front.height.png')
