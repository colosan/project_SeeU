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
im.save('assets/env/basement/room_floor.png')
print('saved assets/env/basement/room_floor.png')
