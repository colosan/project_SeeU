"""Builds scenes/world/basement_test.tscn from a placement plan with a reason for every object,
then checks the plan: nothing solid on the rug or the cleared walkway, everything inside the room.

  python tools/layout_basement.py

Room story (screen px, environment drawn at 1/3 and shown at 3x):
  * Junk from the upper floors falls down the ceiling chute -> the biggest heap sits right under it.
  * Small things that rolled off the heap lie around its foot.
  * SeeU rolled down and woke up on the old rug in front of the heap (nothing on the rug).
  * Somebody bulldozed a walkway from the rug to the exit; pushed junk lines both sides of it.
  * Wall piles are sorted by kind (it is a scrapyard): storage left, audio back-left,
    servers back-right, stage leftovers and overflow along the front.
  * The exit on the right leads to the elevator hall (ExitZone -> elevator_hall.tscn).
  * A severed power line from the server racks sparks; the TVs it still feeds flicker;
    a ventilation fan turns in the exit corridor. Work lamps on tripods follow the walkway.

Lighting (scripts/world/pixel_lighting.gd, one PixelLight per visible source, LIGHTS below):
  the chute beam lands on the rug (start), warm work lamps light the walkway, the elevator hall's
  light spills in through the exit (the goal), cyan screens/LEDs and the sparks are small accents.
"""
import ast
import math
import os

from PIL import Image

import pixel_lights


def _floor_consts(names):
    """Read PATH / HALF / RUG from the floor generator without running it (same numbers the floor uses)."""
    src = open(os.path.join(os.path.dirname(__file__), "gen_basement_floor.py"), encoding="utf-8").read()
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in names:
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


_c = _floor_consts({"PATH", "HALF", "RUG"})
PATH, HALF, RUG = _c["PATH"], _c["HALF"], _c["RUG"]

S = 3                                                    # environment scale
CHUTE = (480, 330)
SPAWN = (480, 440)
WALK = [(x * S, y * S) for x, y in PATH]
WALK_CLEAR = HALF * S + 18                               # half width that must stay free of colliders
RUG_RECT = tuple(v * S for v in RUG)
ROOM = (42, 192, 918, 720)

C, O, D = "code", "organic", "digital"
# (folder, file, x, y, reason, extra)  - x, y = base line centre
PLAN = [
    # 0. the recycle bin itself: deleted data falls through the chute and piles up here (docs/WORLD.md)
    (D, "dg_c_main", 480, 350, "deletion chute drop: the biggest heap of deleted data right under the chute", {}),
    (D, "dg_s_recycle", 300, 332, "the recycle bin's own intake can, overflowing next to the heap", {}),
    (D, "dg_a_cursor", 556, 300, "a mouse cursor stuck on the heap's slope, still hovering over something nobody clicked",
     {"frames": 4, "fps": 4, "solid": False}),
    (O, "org_android_sit", 352, 400, "a deprecated avatar that slid down the heap, slumped at its foot", {}),
    (O, "org_head", 590, 398, "an avatar head rolled off the heap", {}),
    (O, "org_arm", 360, 486, "an avatar arm rolled off the heap, came to rest by the rug", {}),
    (O, "org_cables", 610, 368, "cables spilling from the heap", {}),
    (D, "dg_s_dialog_404", 430, 380, "a 404 dialog that came down the chute with her - her voice is the missing page", {}),
    (D, "dg_s_softbox", 628, 420, "her own discontinued software box (EOL), dumped beside the rug she wakes on", {}),
    (D, "dg_f_home", 500, 505, "127.0.0.1 doormat at the rug's edge: there's no place like home", {"solid": False}),
    # 1. sorted wall piles (the garbage collector pushed deleted data aside by type)
    (D, "dg_e_11", 322, 258, "back wall: overflow of the deletion heap", {}),
    (D, "dg_e_5", 708, 272, "back wall: overflow of the deletion heap", {}),
    (D, "dg_c_small2", 118, 336, "back-left: deprecated audio drivers sorting corner", {}),
    (D, "dg_t_amp_tower", 236, 396, "back-left: unsupported .wav drivers stacked by type", {}),
    (D, "dg_s_speaker", 172, 376, "back-left: speaker driver leaning on the audio corner", {}),
    (D, "dg_s_meme_doge", 214, 456, "a retired meme mascot sitting with the old audio gear - much deleted, very wow", {}),
    (D, "dg_e_0", 95, 300, "back-left corner fill", {}),
    (D, "dg_e_1", 52, 438, "left wall: compressed archives (.zip) of deleted storage", {}),
    (D, "dg_s_meme_troll", 128, 522, "a .bak of an old reaction face nobody uses any more", {}),
    (D, "dg_e_3", 70, 566, "left wall: compressed archives (.zip) of deleted storage", {}),
    (D, "dg_a_meme_fine", 158, 640, "a corner where a tiny burning room keeps saying everything is fine (an unhandled error)",
     {"frames": 4, "fps": 8}),
    (D, "dg_e_7", 58, 692, "left wall: storage junk", {}),
    (D, "dg_s_spam", 236, 610, "spam tins swept off the walkway with the rest of the junk mail", {}),
    (D, "dg_c_ridge", 250, 745, "pushed aside when the walkway was cleared (south side)", {}),
    (D, "dg_t_crates", 470, 690, "archives shoved off the walkway", {}),
    (D, "dg_c_small1", 790, 380, "back-right: legacy servers and dead displays", {}),
    (D, "dg_e_9", 902, 322, "back-right corner fill", {}),
    (D, "dg_t_barrel_tv", 700, 420, "a display left on a bit bucket, still powered", {}),
    (D, "dg_c_mid", 800, 752, "front-right: leftovers of a virtual stage", {}),
    (D, "dg_t_rack_monitor", 615, 708, "a legacy server on a pallet waiting for the next collection", {}),
    (D, "dg_e_8", 545, 750, "front wall: overflow", {}),
    (D, "dg_e_10", 918, 735, "right wall below the exit", {}),
    (D, "dg_s_mic", 548, 700, "mic stand dropped beside the walkway", {}),
    (O, "org_legs", 690, 690, "avatar legs shoved off the walkway", {}),
    (O, "org_android_lying", 360, 560, "a deprecated avatar pushed off the walkway, lying on its back", {}),
    (D, "dg_s_gcbot", 868, 392, "the garbage collector, parked by the exit between collection cycles - the room's threat", {}),
    # 2. power, data and air (animated)
    (D, "dg_a_rack", 652, 356, "a legacy server whose status lights still blink", {"frames": 6, "fps": 5}),
    (D, "dg_a_spark", 612, 456, "severed power line from the servers, sparking at the walkway edge", {"frames": 8, "fps": 10}),
    (D, "dg_a_tv", 268, 470, "a display on the same line, flickering an error", {"frames": 6, "fps": 6}),
    (D, "dg_a_fan", 888, 625, "cooling fan by the exit corridor", {"frames": 4, "fps": 12}),
    (D, "dg_a_bugs", 222, 548, "bugs crawling around the oil leak - every dump has them", {"frames": 12, "fps": 8, "solid": False}),
    # 3. work lamps: whoever cleared the walkway set up caged bulbs on tripods along its north edge
    (D, "dg_s_worklamp", 669, 459, "work lamp at the walkway's first stretch, next to the sparking line it was plugged into",
     {"id": "lamp_a"}),
    (D, "dg_s_worklamp", 792, 408, "work lamp on the last stretch before the exit, in front of the server corner", {"id": "lamp_b"}),
    # 4. walkable floor details
    (D, "dg_f_puddle1", 200, 520, "oil leaking from the archives by the left wall", {"solid": False}),
    (D, "dg_f_plate1", 300, 520, "a broken UI window pane kicked off the walkway", {"solid": False}),
    (D, "dg_f_hello", 300, 448, "a HELLO WORLD printout - the first thing every program says, dropped by the avatar", {"solid": False}),
]
AMBIENT = (0.35, 0.37, 0.46)                             # dim cool base light; the floor never goes black
WARM, CYAN = (1.0, 0.80, 0.52), (0.40, 0.92, 0.95)
# Native px. Prop sources without "at"/"height" sit on the centre of the prop's glowing pixels
# (tools/pixel_lights.py). Room sources are drawn in room_floor.png (ROOM_SOURCES).
ROOM_SOURCES = {
    "chute": (146, 26, 173, 36),                         # ceiling chute mouth (gen_basement_floor.py)
    "exit": (305, 120, 319, 175),                        # opening in the right wall
}
LIGHTS = [
    dict(name="ChuteBeam", type="beam", src="room:chute", at=(160, 144), height=110, color=(0.86, 0.92, 1.0),
         energy=1.5, pool=30, mouth=9, haze=0.14, halo=0.3, halo_r=7,
         why="cold light falling through the ceiling chute: a shaft of haze and dust that lands on the rug where "
             "she wakes up - the brightest, cleanest spot in the room"),
    dict(name="WorkLampA", type="point", src="lamp_a", color=WARM, energy=1.8, radius=88, halo=0.6, halo_r=6,
         why="caged work bulb at the walkway's first stretch: a warm pool leading away from the rug; it also rakes "
             "the junk behind it, so those piles throw shadows away from the path"),
    dict(name="WorkLampB", type="point", src="lamp_b", color=WARM, energy=1.8, radius=88, halo=0.6, halo_r=6,
         why="second work bulb on the last stretch: keeps the walkway the lit band all the way to the exit"),
    dict(name="ExitSpill", type="spot", src="room:exit", at=(313, 148), height=14, color=(1.0, 0.86, 0.66),
         energy=1.4, radius=70, dir=(-1, 0, -0.35), angle=160,
         why="the elevator hall's entry lamp spilling in through the exit opening: the way out glows warm"),
    dict(name="RackLEDs", type="point", src="dg_a_rack", at=(220, 120), height=16, color=CYAN, energy=0.9, radius=30, halo=0.2, halo_r=3,
         why="status LEDs of the server rack, still blinking"),
    dict(name="TVFlicker", type="spot", src="dg_a_tv", color=CYAN, energy=1.8, radius=46, dir=(0, 1, -0.25), angle=150,
         halo=0.3, halo_r=4, flicker=[0.35, 0.7, 0.35, 1.0, 0.35, 0.0],
         why="the flickering TV fed by the severed line: its screen throws cyan onto the floor in front of it"),
    dict(name="BarrelTV", type="spot", src="dg_t_barrel_tv", color=CYAN, energy=1.0, radius=34, dir=(0, 1, -0.3),
         angle=150, halo=0.2, halo_r=3, why="the TV left on a drum in the server corner, still powered"),
    dict(name="MemeFire", type="point", src="dg_a_meme_fine", color=(1.0, 0.62, 0.30), energy=1.4, radius=40,
         halo=0.35, halo_r=4, flicker=[1.0, 0.8, 1.0, 0.7],
         why="the little burning room in the corner: its flames light the junk around it (everything is fine)"),
    dict(name="Sparks", type="point", src="dg_a_spark", color=(1.0, 0.88, 0.45), energy=2.6, radius=48, halo=0.6,
         halo_r=5, flicker=[1.0, 0.55, 0.0, 0.0, 1.0, 0.0, 0.55, 0.0],
         why="sparks from the severed power line flash in step with the burst frames"),
]

HALL = "res://scenes/world/elevator_hall.tscn"
EXITS = [  # name, rect (screen x, y, w, h), target scene, target spawn, reason
    ("ToElevatorHall", (918, 360, 42, 168), HALL, "FromBasement", "the exit opening in the right wall (native x 306..319, y 120..175)"),
]
SPAWNS = [  # name, x, y, facing, reason
    ("FromElevator", 864, 444, "west", "just inside the exit, at the end of the walkway, facing back into the junkyard"),
]
PLAYER_FEET = (18, 14)                                   # half width, height of the player's feet box (screen px)


def walk_samples():
    out = []
    for (x0, y0), (x1, y1) in zip(WALK, WALK[1:]):
        n = max(1, int(math.dist((x0, y0), (x1, y1)) / 6))
        out += [(x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n) for t in range(n)]
    return out + [WALK[-1]]


def snapped(folder, name, x, y, extra):
    """Screen position snapped so the sprite's left edge and base line sit on the 3x pixel grid
    (the lighting buffers are native-res; art off the grid would shift against its own light)."""
    im = Image.open(f"assets/env/basement/{folder}/{name}.png")
    w = im.width // extra.get("frames", 1)
    left = round((x - w * S / 2) / S) * S
    return left + w * S / 2, round(y / S) * S


def light_props():
    """PLAN entries usable as light sources, keyed by their "id" extra or their (unique) file name; native px."""
    props, count = {}, {}
    for _f, name, *_r in PLAN:
        count[name] = count.get(name, 0) + 1
    for i, (folder, name, x, y, why, extra) in enumerate(PLAN):
        key = extra.get("id", name)
        if "id" not in extra and count[name] > 1:
            continue                                     # ambiguous: give it an "id" to use it as a source
        im = Image.open(f"assets/env/basement/{folder}/{name}.png")
        fr = extra.get("frames", 1)
        sx, sy = snapped(folder, name, x, y, extra)
        w = im.width // fr
        props[key] = dict(png=f"assets/env/basement/{folder}/{name}.png", frames=fr, fps=extra.get("fps", 8),
                          left=(sx - w * S / 2) / S, top=sy / S - im.height, base_y=sy / S, wall_base=None,
                          node=f"{name}_{i}")
    return props


def collider(folder, name, x, y, extra):
    im = Image.open(f"assets/env/basement/{folder}/{name}.png")
    w = im.width / extra.get("frames", 1) * S
    h = im.height * S
    cw, ch = w * 0.8, h * 0.35
    return (x - cw / 2, y - ch, x + cw / 2, y)


def check():
    problems = []
    pts = walk_samples()
    for folder, name, x, y, why, extra in PLAN:
        if not extra.get("solid", True):
            continue
        x0, y0, x1, y1 = collider(folder, name, x, y, extra)
        for px, py in pts:
            nx, ny = min(max(px, x0), x1), min(max(py, y0), y1)
            if math.dist((px, py), (nx, ny)) < WALK_CLEAR:
                problems.append(f"{name}: blocks the walkway near ({int(px)}, {int(py)})")
                break
        # visual: a prop standing IN FRONT of the walkway must not draw over it
        im = Image.open(f"assets/env/basement/{folder}/{name}.png")
        sw, sh = im.width / extra.get("frames", 1) * S, im.height * S
        vx0, vy0, vx1 = x - sw / 2, y - sh, x + sw / 2
        for px, py in pts:
            if vx0 - 6 <= px <= vx1 + 6 and vy0 <= py + HALF * S * 0.75 and py < y:
                problems.append(f"{name}: drawn over the walkway near ({int(px)}, {int(py)})")
                break
        rx0, ry0, rx1, ry1 = RUG_RECT
        if x0 < rx1 and x1 > rx0 and y0 < ry1 and y1 > ry0:
            problems.append(f"{name}: sits on the rug")
    problems += pixel_lights.check(LIGHTS, light_props(), ROOM_SOURCES)
    for name, sx, sy, _face, _why in SPAWNS:
        if not any(math.dist((sx, sy), q) <= HALF * S for q in pts):
            problems.append(f"spawn {name}: not on the walkway")
        for ename, (ex, ey, ew, eh), *_ in EXITS:
            if sx - PLAYER_FEET[0] < ex + ew and sx + PLAYER_FEET[0] > ex and sy - PLAYER_FEET[1] < ey + eh and sy > ey:
                problems.append(f"spawn {name}: inside exit {ename} (would bounce straight back)")
    return problems


def write_scene():
    files = list(dict.fromkeys((f, n) for f, n, *_ in PLAN))
    L = ["[gd_scene format=3]", "",
         '[ext_resource type="Script" path="res://scripts/world/pixel_lighting.gd" id="lighting_s"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_light.gd" id="light_s"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_room.gd" id="room_s"]',
         '[ext_resource type="Texture2D" path="res://assets/env/basement/room_floor.png" id="floor"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_prop.gd" id="prop_s"]',
         '[ext_resource type="Script" path="res://scripts/world/exit_zone.gd" id="exit_s"]',
         '[ext_resource type="PackedScene" path="res://scenes/characters/player.tscn" id="player"]']
    L += [f'[ext_resource type="Texture2D" path="res://assets/env/basement/{f}/{n}.png" id="{n}"]' for f, n in files]
    L += ["", '[node name="BasementTest" type="Node2D"]', "y_sort_enabled = true", "",
          "; 2.5D pixel lighting for this map (height buffer + light pass + composite)",
          '[node name="Lighting" type="Node" parent="."]', 'script = ExtResource("lighting_s")',
          f"ambient = Color({AMBIENT[0]}, {AMBIENT[1]}, {AMBIENT[2]}, 1)", "",
          '[node name="Room" type="Sprite2D" parent="."]', "z_index = -10", 'texture = ExtResource("floor")',
          'script = ExtResource("room_s")', ""]
    for i, (folder, name, x, y, why, extra) in enumerate(PLAN):
        sx, sy = snapped(folder, name, x, y, extra)
        L += [f"; {why}", f'[node name="{name}_{i}" type="StaticBody2D" parent="."]', f"position = Vector2({sx:g}, {sy:g})",
              'script = ExtResource("prop_s")', f'texture = ExtResource("{name}")']
        if not extra.get("solid", True):
            L.append("solid = false")
        if "frames" in extra:
            L += [f"frames = {extra['frames']}", f"fps = {float(extra['fps'])}"]
        L.append("")
    L += pixel_lights.scene_lines(LIGHTS, light_props(), ROOM_SOURCES)
    for name, (x, y, w, h), target, spawn, why in EXITS:
        L += [f"; {why}", f'[node name="{name}" type="Area2D" parent="."]',
              f"position = Vector2({x + w / 2:g}, {y + h / 2:g})", 'script = ExtResource("exit_s")',
              f'target_map = "{target}"', f'target_spawn = &"{spawn}"', f"size = Vector2({w}, {h})", ""]
    for name, x, y, face, why in SPAWNS:
        L += [f"; {why}", f'[node name="{name}" type="Marker2D" parent="."]', f"position = Vector2({x}, {y})",
              f'metadata/facing = "{face}"', ""]
    L += ["; SeeU wakes up on the rug", '[node name="Player" parent="." instance=ExtResource("player")]',
          f"position = Vector2({SPAWN[0]}, {SPAWN[1]})", ""]
    with open("scenes/world/basement_test.tscn", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    probs = check()
    for p in probs:
        print("PROBLEM:", p)
    write_scene()
    print(f"wrote scene with {len(PLAN)} objects, {len(LIGHTS)} lights, {len(probs)} problems")
