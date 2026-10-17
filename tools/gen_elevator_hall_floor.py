"""Draws the elevator hall floor/walls at native 320x480 (shown at 3x in game) - a tall map: the view is
320x360, so the camera scrolls up the long corridor. Code-drawn with the pix.py material ramps: no AI generation.

  python tools/gen_elevator_hall_floor.py

Room (native px, front-on 3/4 view: floor from above, walls show only their top and their south face):
  * Entrance on the LEFT wall near the bottom. A short passage runs east along the bottom of the map;
    its back wall (the south face of the solid block in the upper left) carries the pipes and lamps.
  * At the passage's east end the way turns north into a long corridor: you go right, then straight ahead.
    At its far (top) end the corridor's back wall holds the freight elevator (a prop, tools/art/gen_elevator.py).
  * The walls are solid and have depth: the front (south) wall, the side walls and the solid block are drawn
    again on their own layer (hall_front.png) over everything, so whatever stands close behind the front wall
    - junk, SeeU - is partly hidden by it and nothing pokes through a wall.
  * The walkway is not painted: the concrete along the route is worn lighter and cleaner, dust sits along
    the wall feet and the edges of the route, and the hand truck's wheel tracks run into the elevator.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "art"))
from pix import KIND_CAP, KIND_FACE, KIND_FLOOR, Pix, save_height_map  # noqa: E402

W = 320
H = 480
ENTRANCE = (0, 368, 13, 423)              # opening in the left wall (x0, y0, x1, y1)
PASSAGE_WALL = (14, 264, 159, 327)        # south face of the solid block: back wall of the bottom passage
ALCOVE_WALL = (160, 24, 305, 87)          # back wall of the long corridor, where the elevator stands
CORRIDOR_X = 160                          # corridor floor x 160..305 (the block's east edge is its left side)
FLOOR_BOTTOM = 455                        # last floor row; the front wall stands south of it
FRONT_TOP = 432                           # first row of the front wall's top as seen (it hides rows 432..455)
RIGHT_WALL_X = 306                        # right wall band x 306..319
CALL_PANEL = (296, 50, 63)                # x centre, top, bottom of the call panel (prop) - conduit runs to it
# route from the entrance to the elevator gate (native px); the layout script reads this too
PATH = [(0, 396), (80, 396), (168, 393), (210, 381), (228, 357), (233, 320), (233, 220), (233, 130), (232, 94)]
HALF = 13

C = "concrete"
TOP, FACE_HI, FACE_LO, FLOOR, WALK = 0, 2, 1, 2, 4


def is_floor(x, y):
    if 14 <= x < RIGHT_WALL_X and PASSAGE_WALL[3] < y <= FLOOR_BOTTOM:
        return True                                                             # bottom passage
    if CORRIDOR_X <= x < RIGHT_WALL_X and ALCOVE_WALL[3] < y <= FLOOR_BOTTOM:
        return True                                                             # long corridor
    x0, y0, x1, y1 = ENTRANCE
    return x0 <= x <= x1 and y0 <= y <= y1


def foot_row(x):
    """First floor row in column x (right under the back wall face there)."""
    return ALCOVE_WALL[3] + 1 if x >= CORRIDOR_X else PASSAGE_WALL[3] + 1


def samples(pts, step=1.0):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / step))
        out += [(x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n) for t in range(n)]
    return out + [pts[-1]]


def draw():
    p = Pix(W, H)
    p.rect(0, 0, W - 1, H - 1, C, TOP)                                          # wall tops / the solid block

    # --- back wall faces: upper plaster, darker dado band, steel skirting, top edge catch-light
    for (x0, y0, x1, y1) in (PASSAGE_WALL, ALCOVE_WALL):
        p.rect(x0, y0, x1, y1, C, FACE_HI)
        p.rect(x0, y1 - 19, x1, y1, C, FACE_LO)                                 # dado band (lower ~0.9 m)
        p.hline(x0, x1, y1 - 20, C, 3)
        p.hline(x0, x1, y1 - 1, "steel", 1); p.hline(x0, x1, y1, "steel", 0)    # skirting
        p.hline(x0, x1, y0, C, 5)                                               # wall top edge
        for x in range(x0 + 23, x1, 24):                                        # panel joints
            p.vline(x, y0 + 1, y1 - 21, C, 1)
    # the passage wall's east end is a free corner of the solid block (the corridor runs past it): a catch-light down
    # its edge, so the face reads as the front of a thick block turning away, not a strip stuck on the floor
    p.vline(PASSAGE_WALL[2], PASSAGE_WALL[1] + 1, PASSAGE_WALL[3] - 2, C, 4)
    p.vline(PASSAGE_WALL[2] - 1, PASSAGE_WALL[1] + 1, PASSAGE_WALL[3] - 2, C, 2)

    # --- floor: big tidy panels (cleaner than the junkyard), grid from the corridor's far end
    for y in range(H):
        for x in range(W):
            if is_floor(x, y):
                p.put(x, y, C, FLOOR)
                if x >= 14 and ((x - CORRIDOR_X) % 32 == 31 or (y - ALCOVE_WALL[3] - 1) % 32 == 31):
                    p.put(x, y, C, 1)
    # dust gathers along the wall feet: a dark line, a little wider in the panel corners
    for x in range(14, RIGHT_WALL_X):
        foot = foot_row(x)
        p.put(x, foot, C, 1)
        if (x - CORRIDOR_X) % 32 in (0, 1, 30, 31):
            p.put(x, foot + 1, C, 1)
    for y in range(ALCOVE_WALL[3] + 1, PASSAGE_WALL[3] + 1):                    # along the block's east side
        p.put(CORRIDOR_X, y, C, 1)
    for y in range(ALCOVE_WALL[3] + 1, FLOOR_BOTTOM + 1):                       # along the right wall
        p.put(RIGHT_WALL_X - 1, y, C, 1)
    # placed details (no scattered noise): a settlement crack from the block's corner, and a floor drain
    # next to the leaking pipe's drum (see layout) where the spill runs off
    for x, y in ((160, 328), (161, 329), (161, 330), (162, 331), (163, 331), (164, 332), (164, 333), (165, 334),
                 (167, 334), (168, 335), (169, 336)):
        p.put(x, y, C, 1)
    p.rect(144, 333, 149, 336, "steel", 1); p.hline(144, 149, 333, "steel", 2)
    for gx in (145, 147, 149):
        p.vline(gx, 334, 336, "steel", 0)

    # --- the worn route: lighter, swept concrete with dust pushed to its edges
    pts = samples(PATH)

    def in_walk(x, y):
        return any(((x - px) / HALF) ** 2 + ((y - py) / (HALF * 0.75)) ** 2 <= 1 for px, py in pts[::2])

    mask = {(x, y) for x in range(0, RIGHT_WALL_X) for y in range(ALCOVE_WALL[3], FLOOR_BOTTOM)
            if is_floor(x, y) and in_walk(x, y)}
    for x, y in mask:
        p.put(x, y, C, WALK)
    for x, y in mask:                                                           # softer rim: one step between
        if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            p.put(x, y, C, 3)
    for x, y in mask:                                                           # dust swept to the route's edge: a thin dark rim
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ox, oy = x + dx, y + dy
            if (ox, oy) not in mask and is_floor(ox, oy) and oy > foot_row(ox):
                p.put(ox, oy, C, 1)
    # wheel tracks of the hand truck: from the entrance, round the corner, straight onto the elevator threshold
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
        for x in range(206 + inset, 259 - inset):
            if k < 8 or (x // 3) % 2:
                p.put(x, y, C, WALK if k < 7 else 3)

    # --- entrance: steel door jambs seen from above
    x0, y0, x1, y1 = ENTRANCE
    for yy in (y0 - 2, y0 - 1, y1 + 1, y1 + 2):
        p.hline(x0, x1, yy, "steel", 3 if yy in (y0 - 2, y1 + 1) else 1)

    # --- doorway sill across the entrance, flush with the wall's inner face (the wall tops themselves are
    #     unrendered void, so the sill is what makes the opening read as a door through a thick wall)
    p.vline(x1 + 1, y0, y1, "steel", 3)
    p.vline(x1, y0, y1, "steel", 1)

    # --- wall tops: inner edge catch-light (the front wall's is on its own layer, see draw_front)
    p.vline(13, PASSAGE_WALL[1], ENTRANCE[1] - 3, C, 3)
    p.vline(13, ENTRANCE[3] + 3, FLOOR_BOTTOM, C, 3)
    p.vline(CORRIDOR_X - 1, ALCOVE_WALL[1], PASSAGE_WALL[1] - 1, C, 3)          # the block's east edge
    p.vline(RIGHT_WALL_X, ALCOVE_WALL[1], FLOOR_BOTTOM, C, 3)

    # --- pipes along the passage wall: they come from the junkyard and turn up into the ceiling at the corner
    for py, mat in ((271, "steel"), (277, "steel")):
        ex = 145 + (py - 271)                                                   # upper pipe turns up first: no crossing
        p.rect(14, py, ex, py + 2, mat, 2)
        p.hline(14, ex, py, mat, 3); p.hline(14, ex, py + 2, mat, 1)
        p.rect(ex, PASSAGE_WALL[1], ex + 2, py + 2, mat, 2)
        p.vline(ex, PASSAGE_WALL[1], py + 2, mat, 3); p.vline(ex + 2, PASSAGE_WALL[1], py + 2, mat, 1)
        for bx in range(30, ex - 4, 32):                                        # brackets
            p.vline(bx, py - 1, py + 3, "steel", 0)
    p.rect(118, 269, 120, 275, "steel", 1); p.put(119, 268, "steel", 3)          # joint flange (drips: see layout)
    # conduit from the call panel up into the ceiling slab
    cx, ctop, _cbot = CALL_PANEL
    p.vline(cx, ALCOVE_WALL[1] + 1, ctop - 1, "rubber", 2); p.vline(cx + 1, ALCOVE_WALL[1] + 1, ctop - 1, "rubber", 1)
    for yy in range(ALCOVE_WALL[1] + 4, ctop - 1, 8):
        p.hline(cx - 1, cx + 2, yy, "steel", 1)
    return p


def in_front_layer(x, y):
    """Wall tops drawn over the room's contents: the front wall (rows FRONT_TOP..), the side walls and the
    solid block. The back walls' tops (above the faces) stay behind whatever stands at their feet."""
    if y >= FRONT_TOP:
        return True
    if x < 14:
        x0, y0, x1, y1 = ENTRANCE
        return y >= ALCOVE_WALL[1] and not (y0 <= y <= y1)                        # left wall, open at the entrance
    if x < CORRIDOR_X:
        return ALCOVE_WALL[1] <= y < PASSAGE_WALL[1]                             # the block (its south face is not a top)
    return x >= RIGHT_WALL_X and y >= ALCOVE_WALL[1]                             # right wall


def draw_front():
    """The walls' tops again, drawn over the room (pixel_room.gd `front`), with the same catch-light edges."""
    base = draw()
    p = Pix(W, H)
    for y in range(H):
        for x in range(W):
            if in_front_layer(x, y):
                p.px[y][x] = base.px[y][x]
    p.rect(14, FRONT_TOP, RIGHT_WALL_X - 1, H - 1, C, TOP)                       # the front wall's top over the floor
    p.hline(13, RIGHT_WALL_X, FRONT_TOP, C, 3)                                  # inner edge catch-light
    p.hline(13, RIGHT_WALL_X, FRONT_TOP + 1, C, 1)
    return p


WALL_H = PASSAGE_WALL[3] + 1 - PASSAGE_WALL[1]        # 64 px (~2.9 m): both back wall faces are this tall
FRONT_H = FLOOR_BOTTOM + 1 - FRONT_TOP                 # 24 px (~1.1 m): how much of what stands behind it hides


def height_cell(x, y):
    """Height/normal companion for the lighting pass: same geometry as draw()."""
    if is_floor(x, y):
        return 0, KIND_FLOOR
    for (x0, y0, x1, y1) in (PASSAGE_WALL, ALCOVE_WALL):
        if x0 <= x <= x1 and y0 <= y <= y1:
            return y1 + 1 - y, KIND_FACE                 # back wall face: height above its base (pipes, conduit included)
    return WALL_H, KIND_CAP                              # wall tops, the block, door jambs: never lit directly


def front_height_cell(x, y):
    if not in_front_layer(x, y):
        return None
    return (FRONT_H if y >= FRONT_TOP else WALL_H), KIND_CAP


if __name__ == "__main__":
    os.makedirs("assets/env/elevator", exist_ok=True)
    draw().image().save("assets/env/elevator/hall_floor.png")
    print("saved assets/env/elevator/hall_floor.png")
    save_height_map("assets/env/elevator/hall_floor.height.png", W, H, height_cell)
    print("saved assets/env/elevator/hall_floor.height.png")
    draw_front().image().save("assets/env/elevator/hall_front.png")
    print("saved assets/env/elevator/hall_front.png")
    save_height_map("assets/env/elevator/hall_front.height.png", W, H, front_height_cell)
    print("saved assets/env/elevator/hall_front.height.png")
