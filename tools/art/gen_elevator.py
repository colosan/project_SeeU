"""Code-drawn freight elevator and elevator-hall props (native res, shown at 3x).

  python tools/art/gen_elevator.py                  # write any missing files
  python tools/art/gen_elevator.py --out=build/art_preview
  python tools/art/gen_elevator.py --force elevator.png

Never overwrites unless the file name is listed after --force. Never deletes.
Front-on 3/4 view, material ramps only (pix.py), outline once per silhouette.
Size reference: SeeU ~37 px tall (1.65 m) -> 1 px ~ 4.5 cm. Gate opening 48 px (~2.15 m).
All canvases have even widths so a centred prop lands on the 3x pixel grid.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pix import Pix, box  # noqa: E402
import gen_junk  # noqa: E402

OUT_DEFAULT = "assets/env/elevator"


def line(p, x0, y0, x1, y1, mat, step):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for t in range(n + 1):
        p.put(round(x0 + (x1 - x0) * t / n), round(y0 + (y1 - y0) * t / n), mat, step)


# ---------- the freight elevator (canvas = room x 216..287, y 0..92; base line = room y 93) ----------

def elevator():
    p = Pix(72, 93)
    # open shaft above the car: it keeps going up through the whole building
    p.rect(7, 0, 64, 29, "plastic", 0)
    for cx in (30, 41):                                                       # hoist cables
        p.vline(cx, 0, 29, "steel", 2); p.vline(cx + 1, 0, 29, "steel", 1)
    for x0, x1 in ((7, 35), (36, 64)):                                        # X bracing between the posts
        line(p, x0, 4, x1, 15, "steel", 1); line(p, x1, 4, x0, 15, "steel", 1)
    p.rect(2, 0, 69, 2, "steel", 2); p.hline(2, 69, 0, "steel", 3); p.hline(2, 69, 2, "steel", 1)
    p.rect(2, 15, 69, 16, "steel", 2); p.hline(2, 69, 15, "steel", 3)        # lower tie beam

    # caged work bulb hanging from the top beam: the hall's main light source
    p.vline(35, 3, 4, "rubber", 1); p.vline(36, 3, 4, "rubber", 1)
    p.ellipse(35.5, 8.5, 2.6, 3.2, "shell", 4)
    p.put(35, 8, "warn", 4); p.put(36, 9, "warn", 4)                          # filament
    for cx in (32, 39):
        p.vline(cx, 5, 12, "steel", 2)
    p.hline(32, 39, 5, "steel", 2); p.hline(32, 39, 12, "steel", 2); p.hline(33, 38, 9, "steel", 1)

    # steel I-beam posts of the shaft frame, floor to top of the map
    for px in (2, 65):
        for dx, st in enumerate((1, 3, 2, 2, 1)):
            p.vline(px + dx, 0, 87, "steel", st)
        for ry in range(5, 86, 7):
            p.put(px + 1, ry, "steel", 4)
        p.rect(px - 1, 85, px + 5, 87, "steel", 2); p.hline(px - 1, px + 5, 85, "steel", 3)

    # half-dial floor indicator on top of the header; the needle rests at the lowest mark (basement)
    p.rect(24, 17, 47, 29, "steel", 2); p.hline(24, 47, 17, "steel", 3); p.vline(47, 17, 29, "steel", 1)
    cx, cy, rad = 35.5, 28.5, 10.0
    for y in range(17, 29):
        for x in range(24, 48):
            d = math.hypot(x - cx, y - cy)
            if d <= rad - 1.2:
                p.put(x, y, "shell", 4)
            elif d <= rad:
                p.put(x, y, "steel", 1)
    for k, ang in enumerate((168, 132, 96, 60, 24)):                          # floor marks
        a = math.radians(ang)
        tx, ty = round(cx + math.cos(a) * 7.2), round(cy - math.sin(a) * 7.2)
        p.put(tx, ty, "warn", 2) if k == 0 else p.put(tx, ty, "shell", 1)
    a = math.radians(160)
    line(p, 35, 28, round(cx + math.cos(a) * 6.5), round(cy - math.sin(a) * 6.5), "rubber", 0)   # needle
    p.put(35, 28, "steel", 1); p.put(36, 28, "steel", 1)

    # riveted header
    p.rect(4, 30, 67, 39, "steel", 2)
    p.hline(4, 67, 30, "steel", 4); p.hline(4, 67, 31, "steel", 3); p.hline(4, 67, 39, "steel", 1)
    for rx in range(8, 64, 6):
        p.put(rx, 35, "steel", 4); p.put(rx, 36, "steel", 1)

    # door guide channels
    for jx in (7, 63):
        p.vline(jx, 40, 87, "steel", 1); p.vline(jx + 1, 40, 87, "steel", 0 if jx == 63 else 2)

    # the car waiting behind the gate: dark cabin, handrail, checker-plate floor
    p.rect(9, 40, 62, 81, "plastic", 1)
    for vx in range(18, 62, 9):
        p.vline(vx, 42, 81, "plastic", 2)
    p.hline(20, 51, 41, "plastic", 3)                                         # unlit cabin light strip
    p.hline(9, 62, 63, "steel", 2); p.hline(9, 62, 64, "steel", 1)
    p.rect(9, 82, 62, 87, "steel", 1)
    for y in range(82, 88):
        for x in range(9, 63):
            if (x + 2 * y) % 4 == 0:
                p.put(x, y, "steel", 2)

    # folding scissor gate in front of the car
    p.rect(9, 40, 62, 41, "steel", 3); p.hline(9, 62, 41, "steel", 1)        # top track
    bars = list(range(10, 59, 6))
    for a in bars[:-1]:
        for y0 in range(44, 75, 10):                                          # tall scissor diamonds
            line(p, a, y0, a + 6, y0 + 10, "steel", 2); line(p, a + 6, y0, a, y0 + 10, "steel", 2)
    for bx in bars:
        p.vline(bx, 42, 85, "steel", 3)
    p.rect(60, 42, 61, 85, "steel", 3); p.vline(61, 42, 85, "steel", 2)      # leading stile
    p.rect(58, 59, 59, 64, "rubber", 2); p.put(58, 59, "rubber", 4)           # gate handle
    p.rect(9, 85, 62, 86, "steel", 2); p.hline(9, 62, 85, "steel", 3)        # bottom track

    # threshold plate on the floor with a worn hazard lip
    p.rect(3, 88, 68, 89, "steel", 3); p.hline(3, 68, 88, "steel", 4)
    for y in (90, 91):
        for x in range(3, 69):
            p.put(x, y, "warn", 2) if ((x + y) // 3) % 2 else p.put(x, y, "rubber", 1)
    p.outline()
    return p


# ---------- small hall props ----------

def call_panel_frames():
    """Call box beside the gate; its button pulses (the car is waiting)."""
    frames = []
    for lv in (4, 4, 3, 2, 1, 2):
        p = Pix(12, 16)
        box(p, 2, 14, 8, 1, 13, "steel", front=2, top=3)
        p.ellipse(5.5, 6, 2.2, 2.2, "steel", 1)
        p.rect(5, 5, 6, 7, "glow", lv); p.put(5, 5, "glow", min(4, lv + 1))
        p.hline(4, 7, 10, "shell", 3)                                         # faded label plate
        p.put(5, 12, "rubber", 0); p.put(6, 12, "steel", 4)                   # key switch
        p.outline()
        frames.append(p)
    return gen_junk.anim_strip(frames)


LAMP_ON, LAMP_DIM, LAMP_OFF = ("shell", 4), ("shell", 2), ("plastic", 2)
FLICKER = [LAMP_ON, LAMP_ON, LAMP_ON, LAMP_ON, LAMP_DIM, LAMP_ON, LAMP_OFF, LAMP_ON]   # 8 fps, see layout


def wall_lamp(state=LAMP_ON):
    """Caged bulb on a wall bracket."""
    p = Pix(10, 12)
    p.rect(3, 0, 6, 1, "steel", 2); p.hline(3, 6, 0, "steel", 3)             # wall plate
    p.vline(4, 2, 3, "steel", 1); p.vline(5, 2, 3, "steel", 1)
    m, s = state
    p.ellipse(4.5, 7, 2.2, 2.6, m, s)
    if state == LAMP_ON:
        p.put(4, 7, "warn", 4)
    for cx in (2, 7):
        p.vline(cx, 4, 10, "steel", 2)
    p.hline(2, 7, 4, "steel", 2); p.hline(3, 6, 10, "steel", 2); p.hline(2, 7, 7, "steel", 1)
    p.outline()
    return p


def flicker_lamp():
    return gen_junk.anim_strip([wall_lamp(s) for s in FLICKER])


def notice_board():
    """Cork board with yellowed notices; one sheet is a cross-section of the building's floors."""
    p = Pix(28, 20)
    p.rect(1, 1, 26, 18, "card", 1)
    p.rect(2, 2, 25, 17, "card", 3)
    for y in range(3, 17):                                                    # even cork grain
        for x in range(3, 25):
            if (x * 3 + y * 5) % 13 == 0:
                p.put(x, y, "card", 2)
    sheets = [(3, 3, 9, 11), (11, 4, 17, 10), (19, 3, 24, 9), (12, 11, 19, 16)]
    for i, (x0, y0, x1, y1) in enumerate(sheets):
        p.rect(x0, y0, x1, y1, "shell", 3 if i % 2 else 4)
        for yy in range(y0 + 2, y1, 2):
            p.hline(x0 + 1, x1 - 1 - (yy % 3), yy, "shell", 2)
        p.put((x0 + x1) // 2, y0, "redp", 3)                                  # pin
    for k, yy in enumerate(range(4, 12, 2)):                                  # the building, floor by floor
        p.hline(20 + (1 if k == 0 else 0), 23 - (1 if k == 0 else 0), yy, "steel", 2)
    p.hline(20, 23, 11, "glow", 2)
    p.outline()
    return p


def cart():
    """Flatbed cart with a crate still on it, parked out of the way; its wheels left the tracks on the floor."""
    r = random.Random(6)
    p = Pix(34, 30)
    for wx in (6, 26):                                                        # castors under the deck
        p.rect(wx, 25, wx + 2, 27, "rubber", 2); p.put(wx, 25, "rubber", 3)
    box(p, 2, 24, 29, 6, 3, "steel", front=2, top=3)                          # deck
    p.vline(3, 6, 21, "steel", 3); p.vline(4, 6, 21, "steel", 2)              # push handle at the left end
    p.rect(2, 4, 5, 6, "rubber", 2); p.hline(2, 5, 4, "rubber", 3)            # grip
    gen_junk.crate(p, 9, 20, r)                                               # the load, sitting on the deck
    p.outline()
    return p


def stool():
    """The elevator operator's stool, left by the call box."""
    p = Pix(12, 18)
    p.ellipse(5.5, 4, 4.5, 2, "card", 3); p.hline(3, 6, 3, "card", 4)
    p.rect(1, 5, 10, 6, "card", 2); p.hline(1, 10, 6, "card", 1)
    p.vline(5, 7, 14, "steel", 3); p.vline(6, 7, 14, "steel", 2)
    p.hline(2, 9, 15, "steel", 2); p.put(2, 16, "steel", 1); p.put(9, 16, "steel", 1)
    p.outline()
    return p


def drum():
    """Drum catching drips from the leaking pipe joint."""
    p = Pix(14, 19)
    gen_junk.barrel(p, 1, 17, random.Random(2))
    p.outline()
    return p


def drip():
    """Water drop falling from the pipe joint into the drum (10 frames, last two: drop forming)."""
    frames = []
    for i in range(10):
        p = Pix(4, 42)
        if i < 8:
            y = 1 + i * 5
            p.put(1, y, "tarp", 4); p.put(1, y + 1, "tarp", 3)
        else:
            p.put(1, 0, "tarp", 3 if i == 8 else 4)
        frames.append(p)
    return gen_junk.anim_strip(frames)


def drip_puddle():
    p = Pix(24, 8)
    p.ellipse(11.5, 3.5, 10.5, 3, "oil", 2)
    p.ellipse(9, 3, 5, 1.5, "tarp", 1)
    p.hline(6, 10, 2, "tarp", 3)
    return p


TARGETS = {
    "elevator.png": elevator,
    "a_call.png": call_panel_frames,
    "a_lamp.png": flicker_lamp,
    "wall_lamp.png": wall_lamp,
    "notice.png": notice_board,
    "cart.png": cart,
    "stool.png": stool,
    "drum.png": drum,
    "a_drip.png": drip,
    "f_drip_puddle.png": drip_puddle,
}


def main(argv):
    out = OUT_DEFAULT
    force = set()
    it = iter(argv)
    for a in it:
        if a.startswith("--out="):
            out = a.split("=", 1)[1]
        elif a == "--force":
            force.update(it)
    os.makedirs(out, exist_ok=True)
    for name, make in TARGETS.items():
        path = os.path.join(out, name)
        if os.path.exists(path) and name not in force:
            print("kept", path)
            continue
        make().image().save(path)
        print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1:])
