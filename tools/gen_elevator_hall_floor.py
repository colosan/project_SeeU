"""Draws the elevator hall floor/walls at native 320x240 (shown at 3x in game).
Code-drawn with the pix.py material ramps: no AI generation.

  python tools/gen_elevator_hall_floor.py

Room (native px, front-on 3/4 view: floor from above, walls show only their front face):
  * Entrance on the LEFT wall at y 120..175 - the same height as the basement's right-hand
    exit, so walking out of the junkyard continues straight into this corridor.
  * A corridor runs east. Its back wall carries the pipes and lamps.
  * At the east end the back wall steps back into an alcove: the freight elevator stands in it
    (the elevator itself is a prop, tools/art/gen_elevator.py). The alcove frames it.
  * The walkway is not painted: the concrete along the route is worn lighter and cleaner, dust
    sits along the wall feet and the edges of the route, and the wheel tracks of the hand truck
    run from the entrance straight into the elevator.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "art"))
from pix import Pix  # noqa: E402

W, H = 320, 240
ENTRANCE = (0, 120, 13, 175)              # opening in the left wall (x0, y0, x1, y1)
CORRIDOR_WALL = (14, 48, 199, 111)        # back wall face of the corridor
ALCOVE_WALL = (200, 24, 305, 87)          # back wall face of the elevator alcove (24 px deeper)
FLOOR_BOTTOM = 213                        # last floor row; the south wall's top band is below
RIGHT_WALL_X = 306                        # right wall band x 306..319
CALL_PANEL = (296, 50, 63)                # x centre, top, bottom of the call panel (prop) - conduit runs to it
# route from the entrance to the elevator gate (native px); the layout script reads this too
PATH = [(0, 148), (60, 148), (140, 147), (192, 141), (228, 125), (248, 106), (252, 94)]
HALF = 13

C = "concrete"
TOP, FACE_HI, FACE_LO, FLOOR, WALK = 0, 2, 1, 2, 4


def is_floor(x, y):
    if 14 <= x < RIGHT_WALL_X and 112 <= y <= FLOOR_BOTTOM:
        return True
    if ALCOVE_WALL[0] <= x < RIGHT_WALL_X and ALCOVE_WALL[3] < y <= FLOOR_BOTTOM:
        return True
    x0, y0, x1, y1 = ENTRANCE
    return x0 <= x <= x1 and y0 <= y <= y1


def samples(pts, step=1.0):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / step))
        out += [(x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n) for t in range(n)]
    return out + [pts[-1]]


def draw():
    p = Pix(W, H)
    p.rect(0, 0, W - 1, H - 1, C, TOP)                                          # wall tops / void

    # --- back wall faces: upper plaster, darker dado band, steel skirting, top edge catch-light
    for (x0, y0, x1, y1) in (CORRIDOR_WALL, ALCOVE_WALL):
        p.rect(x0, y0, x1, y1, C, FACE_HI)
        p.rect(x0, y1 - 19, x1, y1, C, FACE_LO)                                 # dado band (lower ~0.9 m)
        p.hline(x0, x1, y1 - 20, C, 3)
        p.hline(x0, x1, y1 - 1, "steel", 1); p.hline(x0, x1, y1, "steel", 0)    # skirting
        p.hline(x0, x1, y0, C, 5)                                               # wall top edge
        for x in range(x0 + 23, x1, 24):                                        # panel joints
            p.vline(x, y0 + 1, y1 - 21, C, 1)
    p.vline(CORRIDOR_WALL[2], ALCOVE_WALL[1], CORRIDOR_WALL[3], C, 4)           # corner where the wall steps back

    # --- floor: big tidy panels (cleaner than the junkyard)
    for y in range(H):
        for x in range(W):
            if is_floor(x, y):
                p.put(x, y, C, FLOOR)
    for y in range(112, FLOOR_BOTTOM + 1):
        for x in range(0, RIGHT_WALL_X):
            if is_floor(x, y) and ((x - 14) % 32 == 31 or (y - 112) % 32 == 31):
                p.put(x, y, C, 1)
    # dust gathers along the wall feet: a dark line, a little wider in the panel corners
    for x in range(14, RIGHT_WALL_X):
        foot = 112 if x < ALCOVE_WALL[0] else ALCOVE_WALL[3] + 1
        p.put(x, foot, C, 1)
        if (x - 14) % 32 in (0, 1, 30, 31):
            p.put(x, foot + 1, C, 1)
        p.put(x, FLOOR_BOTTOM, C, 1)
    # placed details (no scattered noise): a settlement crack from the corner where the wall steps
    # back, and a floor drain next to the leaking pipe's drum (see layout) where the spill runs off
    for x, y in ((200, 112), (201, 113), (201, 114), (202, 115), (203, 115), (204, 116), (204, 117), (205, 118),
                 (207, 118), (208, 119), (209, 120)):
        p.put(x, y, C, 1)
    p.rect(144, 117, 149, 120, "steel", 1); p.hline(144, 149, 117, "steel", 2)
    for gx in (145, 147, 149):
        p.vline(gx, 118, 120, "steel", 0)

    # --- the worn route: lighter, swept concrete with dust pushed to its edges
    pts = samples(PATH)

    def in_walk(x, y):
        return any(((x - px) / HALF) ** 2 + ((y - py) / (HALF * 0.75)) ** 2 <= 1 for px, py in pts[::2])

    mask = {(x, y) for x in range(0, RIGHT_WALL_X) for y in range(88, FLOOR_BOTTOM) if is_floor(x, y) and in_walk(x, y)}
    for x, y in mask:
        p.put(x, y, C, WALK)
    for x, y in mask:                                                           # softer rim: one step between
        if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            p.put(x, y, C, 3)
    for x, y in mask:                                                           # dust swept to the route's edge: a thin dark rim
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ox, oy = x + dx, y + dy
            if (ox, oy) not in mask and is_floor(ox, oy) and oy > 112 - (24 if ox >= ALCOVE_WALL[0] else 0):
                p.put(ox, oy, C, 1)
    # wheel tracks of the hand truck: from the entrance straight onto the elevator threshold
    for i in range(3, len(pts) - 3):
        (x0, y0), (x1, y1) = pts[i - 3], pts[i + 3]
        ux, uy = x1 - x0, y1 - y0
        n = (ux * ux + uy * uy) ** 0.5 or 1
        nx, ny = -uy / n, ux / n
        cx, cy = pts[i]
        if (i // 11) % 6 == 5:                                                  # tracks fade in and out
            continue
        for off in (-4, 4):
            tx, ty = round(cx + nx * off), round(cy + ny * off)
            if (tx, ty) in mask:
                p.put(tx, ty, C, 3)
    # where people wait for the car: a worn landing in front of the gate
    for k, y in enumerate(range(ALCOVE_WALL[3] + 1, ALCOVE_WALL[3] + 10)):
        inset = max(0, k - 5) * 4                                               # narrows into the route
        for x in range(226 + inset, 279 - inset):
            if k < 8 or (x // 3) % 2:
                p.put(x, y, C, WALK if k < 7 else 3)

    # --- entrance: steel door jambs seen from above
    x0, y0, x1, y1 = ENTRANCE
    for yy in (y0 - 2, y0 - 1, y1 + 1, y1 + 2):
        p.hline(x0, x1, yy, "steel", 3 if yy in (y0 - 2, y1 + 1) else 1)

    # --- side and front wall bands: inner edge catch-light
    p.vline(13, CORRIDOR_WALL[1], ENTRANCE[1] - 3, C, 3)
    p.vline(13, ENTRANCE[3] + 3, FLOOR_BOTTOM, C, 3)
    p.vline(RIGHT_WALL_X, ALCOVE_WALL[1], FLOOR_BOTTOM, C, 3)
    p.hline(14, RIGHT_WALL_X - 1, FLOOR_BOTTOM + 1, C, 3)

    # --- pipes along the corridor wall: they come from the junkyard and turn up into the ceiling
    for py, mat in ((55, "steel"), (61, "steel")):
        ex = 185 + (py - 55)                                                    # upper pipe turns up first: no crossing
        p.rect(14, py, ex, py + 2, mat, 2)
        p.hline(14, ex, py, mat, 3); p.hline(14, ex, py + 2, mat, 1)
        p.rect(ex, CORRIDOR_WALL[1], ex + 2, py + 2, mat, 2)
        p.vline(ex, CORRIDOR_WALL[1], py + 2, mat, 3); p.vline(ex + 2, CORRIDOR_WALL[1], py + 2, mat, 1)
        for bx in range(30, ex - 4, 32):                                        # brackets
            p.vline(bx, py - 1, py + 3, "steel", 0)
    p.rect(118, 53, 120, 59, "steel", 1); p.put(119, 52, "steel", 3)             # joint flange (drips: see layout)
    # conduit from the call panel up into the ceiling slab
    cx, ctop, _cbot = CALL_PANEL
    p.vline(cx, ALCOVE_WALL[1] + 1, ctop - 1, "rubber", 2); p.vline(cx + 1, ALCOVE_WALL[1] + 1, ctop - 1, "rubber", 1)
    for yy in range(ALCOVE_WALL[1] + 4, ctop - 1, 8):
        p.hline(cx - 1, cx + 2, yy, "steel", 1)
    return p


if __name__ == "__main__":
    os.makedirs("assets/env/elevator", exist_ok=True)
    draw().image().save("assets/env/elevator/hall_floor.png")
    print("saved assets/env/elevator/hall_floor.png")
