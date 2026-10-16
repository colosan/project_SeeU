"""Code-drawn junk parts and piles for the basement (native res, shown at 3x).

  python tools/art/gen_junk.py                 # write any missing files
  python tools/art/gen_junk.py --out=build/art_preview
  python tools/art/gen_junk.py --force pile_a.png

Never overwrites unless the file name is listed after --force. Never deletes.
Size reference: SeeU is ~37 native px tall (1.65 m) -> 1 px ~ 4.5 cm.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pix import Pix, box  # noqa: E402

OUT_DEFAULT = "assets/env/basement/code"


# ---------- parts: each draws at base-left (x, y) on canvas p and returns its top-face rect ----------

def crate(p, x, y, r):
    w, d, h = r.choice([(14, 5, 11), (12, 4, 9), (16, 5, 10)])
    bx = box(p, x, y, w, d, h, "card", front=2, top=3)
    p.vline(x + w // 2, y - h + 2, y, "card", 1)                         # seam
    p.hline(x + 1, x + w - 2, y - h // 2, "card", 1)                     # strap
    if r.random() < 0.5:
        p.rect(x + 2, y - h + 3, x + 4, y - h + 4, "warn", 3)            # label
    return bx, w


def amp(p, x, y, r):
    w, d, h = 14, 5, 18
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    cx, cy = x + w // 2 - 1, y - 6
    p.ellipse(cx, cy, 4.5, 4.5, "steel", 1)
    p.ellipse(cx, cy, 3.2, 3.2, "rubber", 2)
    p.ellipse(cx, cy, 1, 1, "rubber", 0)
    p.put(cx - 2, cy - 2, "steel", 3)                                    # glint
    p.hline(x + 2, x + w - 3, y - h + 3, "steel", 3)                     # control strip
    p.put(x + w - 4, y - h + 3, "glow", 3)                               # one LED
    return bx, w


def rack(p, x, y, r):
    w, d, h = 12, 4, r.choice([24, 27])
    bx = box(p, x, y, w, d, h, "steel", front=1, top=3)
    for yy in range(y - h + 3, y - 1, 3):
        p.hline(x + 2, x + w - 3, yy, "plastic", 1)
        if r.random() < 0.35:
            p.put(x + w - 4, yy, "glow", 3)
    return bx, w


def tv(p, x, y, r):
    w, d, h = 13, 6, 11
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    p.rect(x + 2, y - h + 3, x + w - 4, y - 2, "glow", 1)               # dead screen
    p.hline(x + 3, x + w - 5, y - h + 4, "glow", 2)
    p.put(x + 4, y - 4, "glow", 3); p.put(x + 5, y - 5, "glow", 3)      # crack glint
    return bx, w


def bag(p, x, y, r):
    w = r.choice([11, 12, 13])
    cx = x + w // 2
    p.ellipse(cx, y - 5, w / 2, 5.5, "rubber", 2)
    p.ellipse(cx - 2, y - 7, 2.5, 2, "rubber", 3)                        # highlight upper-left
    p.rect(cx - 1, y - 12, cx, y - 10, "rubber", 2)                     # knot
    return (x, y - 11, x + w - 1, y), w


def cable(p, x, y, r):
    for i in range(14):
        xx = x + i
        yy = y - (1 if (i // 3) % 2 else 0)
        p.put(xx, yy, "rubber", 1)
    p.put(x + 14, y, "steel", 3)
    return (x, y - 1, x + 14, y), 15


def speaker(p, x, y, r):
    w, d, h = 10, 4, 22
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    for cy, rr in ((y - 15, 3.2), (y - 6, 3.8)):
        p.ellipse(x + 4, cy, rr, rr, "steel", 1)
        p.ellipse(x + 4, cy, rr - 1.2, rr - 1.2, "rubber", 2)
    return bx, w


def mic_stand(p, x, y, r):
    h = r.choice([20, 23])
    p.vline(x + 3, y - h, y - 1, "steel", 3)
    p.hline(x, x + 6, y, "steel", 2)
    p.put(x, y, "steel", 1); p.put(x + 6, y, "steel", 1)
    p.ellipse(x + 3, y - h - 1, 1.5, 2, "rubber", 2)
    p.put(x + 2, y - h - 2, "rubber", 4)
    return (x, y - h - 3, x + 6, y), 7


def synth(p, x, y, r):
    w, d, h = 22, 6, 4
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=2)
    top = y - h + 1
    for kx in range(x + 2, x + w - 2):
        p.vline(kx, top - d + 2, top - 2, "shell", 4 if (kx - x) % 3 else 1)    # keys on the top face
    p.put(x + w - 3, y - 2, "glow", 3)
    return bx, w


def monitor(p, x, y, r):
    w, d, h = 14, 3, 10
    bx = box(p, x, y - 3, w, d, h, "plastic", front=1, top=3)
    p.rect(x + 1, y - h - 1, x + w - 3, y - 5, "glow", r.choice([1, 2]))
    p.rect(x + 5, y - 2, x + 8, y, "plastic", 2)                                # stand
    return (x, bx[1], x + w - 1, y), w


def spotlight(p, x, y, r):
    w, d, h = 9, 5, 8
    bx = box(p, x, y, w, d, h, "steel", front=2, top=3)
    p.ellipse(x + 4, y - 4, 3, 3, "warn", 3)
    p.ellipse(x + 4, y - 4, 1.5, 1.5, "warn", 4)
    return bx, w


def truss(p, x, y, r):
    w, h = 30, 6
    p.hline(x, x + w, y - h, "steel", 3); p.hline(x, x + w, y, "steel", 2)
    for i in range(0, w, 6):
        for k in range(h):
            p.put(x + i + k, y - k, "steel", 2)
    return (x, y - h, x + w, y), w + 1


def robot_head(p, x, y, r):
    p.ellipse(x + 5, y - 5, 5.5, 5, "shell", 3)
    p.ellipse(x + 4, y - 7, 2.5, 1.5, "shell", 4)                               # highlight
    p.rect(x + 1, y - 5, x + 9, y - 3, "plastic", 1)                            # visor
    if r.random() < 0.5:
        p.put(x + 3, y - 4, "glow", 4)
    return (x, y - 10, x + 11, y), 11


def robot_torso(p, x, y, r):
    w, d, h = 14, 4, 12
    bx = box(p, x, y, w, d, h, "shell", front=2, top=3)
    p.rect(x + 3, y - 8, x + 10, y - 4, "shell", 1)                             # chest panel
    p.rect(x - 3, y - 9, x - 1, y - 3, "shell", 2); p.rect(x + w, y - 9, x + w + 2, y - 3, "shell", 1)
    return bx, w + 3


def pallet(p, x, y, r):
    w, d, h = 20, 7, 3
    bx = box(p, x, y, w, d, h, "card", front=1, top=3)
    for sx in range(x + 1, x + w, 4):
        p.vline(sx, y - h - d + 2, y - h, "card", 1)
    return bx, w


def barrel(p, x, y, r):
    w, h = 11, 14
    p.rect(x, y - h + 3, x + w - 1, y, "steel", 2)
    p.vline(x + w - 1, y - h + 3, y, "steel", 1); p.vline(x + 1, y - h + 4, y - 1, "steel", 3)
    p.hline(x, x + w - 1, y - 4, "steel", 1); p.hline(x, x + w - 1, y - h + 7, "steel", 1)
    p.ellipse(x + w / 2 - 0.5, y - h + 2, w / 2, 2.2, "steel", 3)
    if r.random() < 0.4:
        p.rect(x + 3, y - 9, x + 6, y - 8, "warn", 3)
    return (x, y - h, x + w - 1, y), w


def tire(p, x, y, r):
    w = 14
    p.ellipse(x + 7, y - 4, 7, 4, "rubber", 2)                                  # tire lying flat: top ring
    p.rect(x, y - 4, x + w - 1, y, "rubber", 1)                                 # tread (front)
    p.ellipse(x + 7, y - 4, 3.5, 2, "rubber", 0)                                # hole
    p.hline(x + 1, x + w - 2, y - 2, "rubber", 2)
    if r.random() < 0.5:                                                        # stacked second tire
        p.ellipse(x + 7, y - 8, 7, 4, "rubber", 3); p.rect(x, y - 8, x + w - 1, y - 5, "rubber", 1)
        p.ellipse(x + 7, y - 8, 3.5, 2, "rubber", 0)
    return (x, y - 12, x + w - 1, y), w


def pipes(p, x, y, r):
    n, w = r.choice([2, 3]), r.choice([28, 34])
    for i in range(n):
        yy = y - i * 5
        p.rect(x + i * 2, yy - 4, x + w - 1 - i, yy, "steel", 2)
        p.hline(x + i * 2, x + w - 1 - i, yy - 3, "steel", 3)
        p.ellipse(x + i * 2, yy - 2, 2, 2.5, "steel", 1)                         # open end
        p.put(x + i * 2, yy - 2, "rubber", 0)
    return (x, y - n * 5, x + w, y), w


def fan(p, x, y, r):
    w, d, h = 14, 4, 14
    bx = box(p, x, y, w, d, h, "steel", front=2, top=3)
    p.ellipse(x + 6, y - 6, 5, 5, "plastic", 1)
    for k in (-3, 0, 3):
        p.hline(x + 3, x + 9, y - 6 + k, "steel", 3)
    return bx, w


def chair(p, x, y, r):
    mat = r.choice(["redp", "steel", "tarp"])
    p.rect(x + 1, y - 14, x + 9, y - 8, mat, 2); p.hline(x + 1, x + 9, y - 14, mat, 3)   # back rest
    p.rect(x, y - 8, x + 10, y - 6, mat, 3)                                               # seat
    for lx in (x + 1, x + 9):
        p.vline(lx, y - 5, y, "steel", 2)
    return (x, y - 15, x + 10, y), 11


def ladder(p, x, y, r):
    h = r.choice([26, 30])
    for lx in (x, x + 7):
        p.vline(lx, y - h, y, "warn", 2); p.vline(lx + 1, y - h, y, "warn", 3)
    for yy in range(y - h + 3, y - 1, 5):
        p.hline(x + 1, x + 7, yy, "warn", 1)
    return (x, y - h, x + 8, y), 9


def plate(p, x, y, r):
    w, h = r.choice([(22, 6), (26, 5)])
    mat = r.choice(["steel", "tarp", "steel"])
    p.rect(x, y - h, x + w - 1, y, mat, 3); p.hline(x, x + w - 1, y, mat, 1)
    p.hline(x, x + w - 1, y - h, mat, 4)
    for bx in (x + 2, x + w - 3):
        p.put(bx, y - h + 1, mat, 1)
    return (x, y - h, x + w - 1, y), w


def tank(p, x, y, r):
    w, h = 16, 20
    mat = r.choice(["steel", "redp"])
    p.rect(x, y - h + 4, x + w - 1, y, mat, 2)
    p.vline(x + 2, y - h + 5, y - 1, mat, 3); p.vline(x + w - 1, y - h + 4, y, mat, 1)
    p.ellipse(x + w / 2 - 0.5, y - h + 3, w / 2, 3, mat, 3)
    p.rect(x + 6, y - h - 1, x + 9, y - h + 1, "steel", 2)                       # valve
    p.rect(x + 3, y - 10, x + 12, y - 7, "warn", 3)                             # hazard band
    return (x, y - h - 1, x + w - 1, y), w


PARTS = {"tire": tire, "pipes": pipes, "fan": fan, "chair": chair, "ladder": ladder, "plate": plate, "tank": tank,
         "crate": crate, "amp": amp, "rack": rack, "tv": tv, "bag": bag, "speaker": speaker,
         "mic": mic_stand, "synth": synth, "monitor": monitor, "spot": spotlight, "truss": truss,
         "rhead": robot_head, "rtorso": robot_torso, "pallet": pallet, "barrel": barrel}

THEMES = {
    "audio":   ["amp", "speaker", "synth", "mic", "chair", "tire", "plate"],
    "server":  ["rack", "rack", "monitor", "fan", "pipes", "plate"],
    "storage": ["crate", "pallet", "barrel", "tire", "tank", "plate", "bag"],
    "robot":   ["rhead", "rtorso", "rtorso", "plate", "pipes", "bag"],
    "stage":   ["truss", "spot", "speaker", "ladder", "chair", "mic"],
    "tvs":     ["tv", "monitor", "monitor", "fan", "tire", "chair"],
}


# ---------- piles: parts stacked back row -> things on top -> front row, outline once ----------

def pile(seed, kinds, w=118, h=74):
    r = random.Random(seed)
    p = Pix(w, h)
    ground = h - 4

    def row(y, n, kinds, x0, gap):
        tops, x = [], x0
        for _ in range(n):
            k = r.choice(kinds)
            bx, pw = PARTS[k](p, x, y, r)
            tops.append((k, bx))
            x += pw + gap
        return tops

    back = row(ground - 6, 4, kinds, 8, -1)                                # back row sits deeper
    for k, (x0, top_y, x1, _y1) in back:                                   # stack on the back row
        if r.random() < 0.6:
            kind = r.choice([c for c in kinds if c != "rack"] or kinds)
            PARTS[kind](p, x0 + r.randint(-2, 2), top_y + 3, r)
    row(ground, 3, [k for k in kinds if k != "rack"] or kinds, 2, 3)       # front row, lower things
    for _ in range(2):
        bag(p, r.randint(0, w - 14), ground + 1, r)
    cable(p, r.randint(10, w - 30), ground + 2, r)
    p.outline()
    return p.bbox_crop()


def mound(seed, kinds, n=16, w=120, h=84, peak=30):
    """Heap: every part gets a spot inside a mound silhouette. Parts near the middle
    sit higher (resting on the heap), parts at the rim sit on the floor. Drawn from
    the highest/farthest spot to the lowest/nearest so nearer junk overlaps."""
    r = random.Random(seed)
    h += 10                                                                  # room for an uneven, spilling foot
    p = Pix(w, h)
    ground = h - 12
    cx = w / 2 + r.uniform(-w * 0.12, w * 0.12)                              # off-centre peak: asymmetric heap
    phase, phase2 = r.uniform(0, 6.3), r.uniform(0, 6.3)

    def foot(x):  # wavy, irregular bottom edge instead of a ruler-straight line
        return int(ground + 3 * math.sin(x * 0.09 + phase) + 2 * math.sin(x * 0.23 + phase2))

    spots = []
    for _ in range(n):
        x = r.gauss(cx, w * 0.2)
        x = max(6, min(w - 20, x))
        lift = peak * max(0.0, 1 - abs(x - cx) / (w * 0.45)) ** 1.3       # mound height at x
        base = foot(int(x)) - lift * r.uniform(0.55, 1.0)
        spots.append((base, x, r.choice(kinds)))
    for _ in range(max(2, n // 6)):                                         # a few things slid out in front
        x = r.uniform(4, w - 24)
        spots.append((foot(int(x)) + r.randint(2, 6), x, r.choice(kinds)))
    # heap body: a dark mass of chunky scrap filling the mound, so lifted parts rest on something
    for x in range(2, w - 2):
        lift = peak * max(0.0, 1 - abs(x - cx) / (w * 0.47)) ** 1.3
        top = int(foot(x) - lift)
        for y in range(top, foot(x) + 1):
            p.put(x, y, "plastic", 1)
    for _ in range(int(w * peak / 9)):                                       # 2-4 px scrap chunks inside the body
        x = r.randint(4, w - 6)
        lift = peak * max(0.0, 1 - abs(x - cx) / (w * 0.47)) ** 1.3
        if lift < 3:
            continue
        y = r.randint(int(ground - lift) + 1, ground - 1)
        mat = r.choice(["steel", "rubber", "plastic", "card"])
        cw, ch = r.randint(2, 4), r.randint(1, 2)
        p.rect(x, y, x + cw, y + ch, mat, r.choice([1, 2, 2, 3]))
    for base, x, k in sorted(spots):                                        # far/high first
        PARTS[k](p, int(x) - 6, int(base), r)
    for _ in range(2):                                                      # things spilled at the foot
        bx = r.randint(0, w - 14)
        bag(p, bx, foot(bx) + r.randint(1, 5), r)
    p.outline()
    return p.bbox_crop()


ROOM_PILES = {  # name: (theme, seed, n, width, peak) - every pile in the room is unique
    "z_audio_1.png": ("audio", 101, 16, 120, 30), "z_audio_2.png": ("audio", 102, 12, 96, 24),
    "z_server_1.png": ("server", 201, 18, 130, 36), "z_server_2.png": ("server", 202, 12, 100, 28),
    "z_storage_1.png": ("storage", 301, 16, 120, 26), "z_storage_2.png": ("storage", 302, 12, 96, 22),
    "z_robot_1.png": ("robot", 401, 18, 120, 28), "z_robot_2.png": ("robot", 402, 12, 96, 22),
    "z_stage_1.png": ("stage", 501, 14, 120, 26), "z_tvs_1.png": ("tvs", 601, 18, 110, 34),
}

MIX = {  # composition pieces: very different sizes so the room has one hero mass, ridges, and small clutter
    "c_main.png":   (THEMES["robot"] + THEMES["audio"] + THEMES["tvs"], 701, 46, 210, 64),
    "c_ridge.png":  (THEMES["storage"] + THEMES["server"], 702, 30, 170, 34),
    "c_mid.png":    (THEMES["stage"] + THEMES["audio"], 703, 18, 110, 30),
    "c_small1.png": (THEMES["tvs"], 704, 6, 52, 12),
    "c_small2.png": (THEMES["robot"], 705, 5, 46, 10),
    "c_small3.png": (THEMES["storage"], 706, 6, 56, 12),
}
def stack(seed, parts, w=44, h=70):
    """Things literally stacked: each part rests on the top face of the one below."""
    r = random.Random(seed)
    p = Pix(w, h)
    base, x = h - 3, 6
    for k in parts:
        x0, top_y, x1, _ = PARTS[k](p, x + r.randint(-2, 2), base, r)[0]
        base = top_y + 3                                                     # sit inside the top face
    p.outline()
    return p.bbox_crop()


STACKS = {"t_barrel_tv.png": (21, ["barrel", "tv"]), "t_crates.png": (22, ["crate", "crate", "speaker"]),
          "t_rack_monitor.png": (23, ["pallet", "rack"]), "t_amp_tower.png": (24, ["amp", "amp", "monitor"])}

def scatter(seed, w=64, h=26, n=34):
    """Flat floor litter (walkable decal): chunky bits, bolts, a cable or two. No outline ring."""
    r = random.Random(seed)
    p = Pix(w, h)
    for _ in range(n):
        x, y = r.randint(1, w - 5), r.randint(1, h - 3)
        mat = r.choice(["steel", "rubber", "plastic", "card", "shell"])
        p.rect(x, y, x + r.randint(1, 3), y + r.randint(0, 1), mat, r.choice([1, 2, 3]))
    for _ in range(r.randint(1, 2)):
        x0, y0 = r.randint(0, w - 20), r.randint(2, h - 3)
        for i in range(r.randint(10, 18)):
            p.put(x0 + i, y0 + (1 if (i // 3) % 2 else 0), "rubber", 1)
    if r.random() < 0.5:
        p.put(r.randint(3, w - 3), r.randint(2, h - 2), "glow", 3)
    return p.bbox_crop()


def puddle(seed):
    r = random.Random(seed)
    p = Pix(40, 14)
    p.ellipse(20, 7, 18, 5.5, "oil", 1)
    p.ellipse(14 + r.randint(-2, 2), 6, 8, 3, "oil", 2)
    p.hline(10, 16, 5, "oil", 4); p.put(24, 8, "glow", 1)                     # sheen + reflected screen glow
    return p.bbox_crop()


def floor_plate(seed):
    p = Pix(30, 10)
    plate(p, 1, 8, random.Random(seed))
    return p.bbox_crop()


def coil(seed):
    p = Pix(24, 12)
    p.ellipse(11, 6, 10, 4.5, "rubber", 1)
    p.ellipse(11, 6, 6, 2.5, "rubber", 0)
    p.ellipse(11, 6, 4, 1.5, "oil", 2)
    p.put(21, 6, "steel", 3)
    return p.bbox_crop()


# ---------- animated props: frames side by side in one strip (Godot plays them) ----------

def anim_strip(frames):
    w, h = max(f.w for f in frames), max(f.h for f in frames)
    strip = Pix(w * len(frames), h)
    for i, f in enumerate(frames):
        strip.paste(f, i * w + (w - f.w) // 2, h - f.h)
    return strip


def spark_cable(seed):
    """Severed cable on the floor spitting sparks (8 frames)."""
    frames = []
    for i in range(8):
        r = random.Random(seed * 100 + i)
        p = Pix(30, 22)
        for k in range(20):
            p.put(2 + k, 19 + (1 if (k // 4) % 2 else 0), "rubber", 2)
        p.rect(21, 18, 23, 20, "steel", 3)                                       # torn end
        if i in (0, 1, 4, 6):                                                    # bursts on some frames only
            n = 6 if i in (0, 4) else 3
            for _ in range(n):
                dx, dy = r.randint(-5, 6), r.randint(-9, 1)
                p.put(23 + dx, 18 + dy, "spark", r.choice([2, 3, 4]))
            p.put(24, 17, "spark", 4)
        p.outline()
        frames.append(p)
    return anim_strip(frames)


def flicker_tv(seed):
    """CRT on the floor whose dead screen flickers (6 frames)."""
    levels = [1, 2, 1, 3, 1, 0]
    frames = []
    for lv in levels:
        p = Pix(20, 20)
        box(p, 2, 18, 15, 6, 11, "plastic", front=2, top=3)
        p.rect(4, 10, 13, 16, "glow", lv)
        if lv >= 2:
            p.hline(5, 12, 12, "glow", min(4, lv + 1))
        p.outline()
        frames.append(p)
    return anim_strip(frames)


def blink_rack(seed):
    """Server rack with blinking status lights (6 frames)."""
    r0 = random.Random(seed)
    leds = [(r0.randint(0, 6), r0.random() < 0.3) for _ in range(9)]
    frames = []
    for i in range(6):
        p = Pix(18, 36)
        box(p, 2, 34, 12, 4, 27, "steel", front=1, top=3)
        for k, (ph, red) in enumerate(leds):
            yy = 11 + k * 3
            p.hline(4, 11, yy, "plastic", 1)
            on = (i + ph) % 3 != 0
            p.put(11, yy, "redp" if red else "glow", 4 if on else 1)
        p.outline()
        frames.append(p)
    return anim_strip(frames)


def spin_fan(seed):
    """Wall fan unit whose blades turn (4 frames)."""
    frames = []
    for i in range(4):
        p = Pix(18, 20)
        box(p, 2, 18, 14, 4, 14, "steel", front=2, top=3)
        p.ellipse(8, 12, 5, 5, "plastic", 1)
        blades = [((-4, 0), (4, 0)), ((-3, -3), (3, 3)), ((0, -4), (0, 4)), ((3, -3), (-3, 3))][i]
        (ax, ay), (bx, by) = blades
        for t in range(9):
            f = t / 8
            p.put(round(8 + ax + (bx - ax) * f), round(12 + ay + (by - ay) * f), "steel", 3)
        p.put(8, 12, "steel", 4)
        p.outline()
        frames.append(p)
    return anim_strip(frames)


ANIMS = {"a_spark.png": (spark_cable, 1), "a_tv.png": (flicker_tv, 2), "a_rack.png": (blink_rack, 3),
         "a_fan.png": (spin_fan, 4)}

ALL_KINDS = sorted(set(sum(THEMES.values(), [])))
EDGES = {f"e_{i}.png": (900 + i, r_w, r_pk, r_n) for i, (r_w, r_pk, r_n) in enumerate(
    [(96, 26, 16), (84, 22, 13), (110, 30, 18), (76, 20, 12), (100, 24, 15), (90, 28, 15), (120, 32, 20), (70, 18, 11),
     (104, 26, 16), (88, 22, 14), (96, 30, 16), (80, 20, 12)])}
DECALS = {f"d_{i}.png": 950 + i for i in range(6)}

SINGLES = {"s_mic.png": (mic_stand, 1), "s_rhead.png": (robot_head, 2), "s_barrel.png": (barrel, 3),
           "s_tv.png": (tv, 4), "s_spot.png": (spotlight, 5), "s_speaker.png": (speaker, 6)}

TARGETS = {
    **{n: (lambda t=t, s=s, k=k, w=w, pk=pk: mound(s, THEMES[t], n=k, w=w, peak=pk))
       for n, (t, s, k, w, pk) in ROOM_PILES.items()},
    **{n: (lambda kinds=kinds, s=s, k=k, w=w, pk=pk: mound(s, kinds, n=k, w=w, h=pk + 44, peak=pk))
       for n, (kinds, s, k, w, pk) in MIX.items()},
    **{n: (lambda fn=fn, s=s: _single(fn, s)) for n, (fn, s) in SINGLES.items()},
    **{n: (lambda s=s, ps=ps: stack(s, ps)) for n, (s, ps) in STACKS.items()},
    **{n: (lambda s=s, w=w, pk=pk, k=k: mound(s, ALL_KINDS, n=k, w=w, h=pk + 44, peak=pk))
       for n, (s, w, pk, k) in EDGES.items()},
    **{n: (lambda s=s: scatter(s)) for n, s in DECALS.items()},
    "f_puddle1.png": lambda: puddle(1), "f_puddle2.png": lambda: puddle(2),
    "f_plate1.png": lambda: floor_plate(3), "f_coil1.png": lambda: coil(4),
    **{n: (lambda fn=fn, s=s: fn(s)) for n, (fn, s) in ANIMS.items()},
    "pile_a.png": lambda: mound(11, ["crate", "crate", "tv", "amp", "bag"]),
    "pile_b.png": lambda: mound(23, ["amp", "rack", "amp", "crate", "bag"]),
    "pile_c.png": lambda: mound(37, ["rack", "tv", "crate", "crate", "bag"], n=20, w=140, peak=38),
    "crate.png": lambda: _single(crate, 3),
    "amp.png": lambda: _single(amp, 3),
    "rack.png": lambda: _single(rack, 3),
    "tv.png": lambda: _single(tv, 3),
}


def _single(fn, seed):
    p = Pix(40, 40)
    fn(p, 4, 36, random.Random(seed))
    p.outline()
    return p.bbox_crop()


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
