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
    a ventilation fan turns in the exit corridor. Work lamps follow the walkway.
"""
import ast
import math
import os

from PIL import Image


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

C, O = "code", "organic"
# (folder, file, x, y, reason, extra)  - x, y = base line centre
PLAN = [
    # 1. the chute heap and what rolled off it
    (C, "c_main", 480, 350, "chute drop: biggest heap directly under the ceiling chute", {}),
    (O, "org_android_sit", 352, 400, "robot that slid down the heap, slumped at its foot", {}),
    (O, "org_head", 590, 398, "head rolled off the heap", {}),
    (O, "org_arm", 360, 486, "arm rolled off the heap, came to rest by the rug", {}),
    (O, "org_cables", 610, 368, "cables spilling from the heap", {}),
    # 2. sorted wall piles (pushed aside, sorted by kind)
    (C, "e_11", 322, 258, "back wall: overflow of the chute heap", {}),
    (C, "e_5", 708, 272, "back wall: overflow of the chute heap", {}),
    (C, "c_small2", 118, 336, "back-left: audio sorting corner", {}),
    (C, "t_amp_tower", 236, 396, "back-left: amps stacked by whoever sorted audio gear", {}),
    (C, "s_speaker", 172, 376, "back-left: speaker leaning on the audio corner", {}),
    (C, "e_0", 95, 300, "back-left corner fill", {}),
    (C, "e_1", 52, 438, "left wall: storage junk", {}),
    (C, "e_3", 70, 566, "left wall: storage junk", {}),
    (C, "e_7", 58, 692, "left wall: storage junk", {}),
    (C, "c_ridge", 250, 745, "pushed aside when the walkway was cleared (south side)", {}),
    (C, "t_crates", 470, 690, "crates shoved off the walkway", {}),
    (C, "c_small1", 790, 380, "back-right: server/tv sorting corner", {}),
    (C, "e_9", 902, 322, "back-right corner fill", {}),
    (C, "t_barrel_tv", 700, 420, "server corner: a TV left on a drum, still powered", {}),
    (C, "c_mid", 800, 752, "front-right: stage leftovers", {}),
    (C, "t_rack_monitor", 615, 708, "front: rack on a pallet waiting to be sorted", {}),
    (C, "e_8", 545, 750, "front wall: overflow", {}),
    (C, "e_10", 918, 735, "right wall below the exit", {}),
    (C, "s_mic", 548, 700, "mic stand dropped beside the walkway", {}),
    (O, "org_legs", 690, 690, "robot legs shoved off the walkway", {}),
    (O, "org_android_lying", 360, 560, "robot pushed off the walkway, lying on its back", {}),
    # 3. power and air (animated)
    (C, "a_rack", 652, 356, "server rack whose status lights still blink", {"frames": 6, "fps": 5}),
    (C, "a_spark", 612, 456, "severed power line from the racks, sparking at the walkway edge", {"frames": 8, "fps": 10}),
    (C, "a_tv", 268, 470, "TV on the same line, flickering", {"frames": 6, "fps": 6}),
    (C, "a_fan", 888, 625, "ventilation fan by the exit corridor", {"frames": 4, "fps": 12}),
    # 4. walkable floor details
    (C, "f_puddle1", 200, 520, "oil leaking from the storage junk by the left wall", {"solid": False}),
    (C, "f_plate1", 300, 520, "loose plate kicked off the walkway", {"solid": False}),
]
LIGHTS = [  # name, x, y, scale, color, energy, reason
    ("ChuteLight", 480, 420, 4.0, "0.88, 0.92, 1", 1.1, "light falling through the chute onto the rug"),
    ("RackGlow", 652, 318, 1.6, "0.4, 0.9, 0.95", 0.7, "server status lights"),
    ("TVGlow", 268, 440, 1.6, "0.4, 0.95, 0.95", 0.7, "flickering TV"),
    ("SparkLight", 612, 444, 1.2, "1, 0.9, 0.5", 0.6, "sparks"),
    ("WorkLamp1", 560, 530, 2.0, "1, 0.85, 0.6", 0.6, "work lamp along the walkway"),
    ("WorkLamp2", 700, 510, 2.0, "1, 0.85, 0.6", 0.6, "work lamp along the walkway"),
    ("WorkLamp3", 830, 460, 2.0, "1, 0.85, 0.6", 0.6, "work lamp along the walkway"),
    ("ExitLight", 905, 445, 2.4, "0.75, 0.8, 0.95", 0.75, "light from the exit corridor"),
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
         '[ext_resource type="Script" path="res://scripts/world/pixel_room.gd" id="room_s"]',
         '[ext_resource type="Texture2D" path="res://assets/env/basement/room_floor.png" id="floor"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_prop.gd" id="prop_s"]',
         '[ext_resource type="Script" path="res://scripts/world/exit_zone.gd" id="exit_s"]',
         '[ext_resource type="PackedScene" path="res://scenes/characters/player.tscn" id="player"]']
    L += [f'[ext_resource type="Texture2D" path="res://assets/env/basement/{f}/{n}.png" id="{n}"]' for f, n in files]
    L += ["", '[sub_resource type="Gradient" id="steps"]', "interpolation_mode = 1",
          "offsets = PackedFloat32Array(0, 0.3, 0.55, 0.78, 0.95)",
          "colors = PackedColorArray(1, 1, 1, 1, 0.82, 0.82, 0.82, 1, 0.62, 0.62, 0.62, 1, 0.38, 0.38, 0.38, 1, 0, 0, 0, 1)", "",
          '[sub_resource type="GradientTexture2D" id="lightTex"]', 'gradient = SubResource("steps")', "width = 128", "height = 128",
          "fill = 1", "fill_from = Vector2(0.5, 0.5)", "fill_to = Vector2(1, 0.5)", "",
          '[node name="BasementTest" type="Node2D"]', "y_sort_enabled = true", "",
          '[node name="Dark" type="CanvasModulate" parent="."]', "color = Color(0.36, 0.37, 0.44, 1)", "",
          '[node name="Room" type="Sprite2D" parent="."]', "z_index = -10", 'texture = ExtResource("floor")',
          'script = ExtResource("room_s")', ""]
    for i, (folder, name, x, y, why, extra) in enumerate(PLAN):
        L += [f"; {why}", f'[node name="{name}_{i}" type="StaticBody2D" parent="."]', f"position = Vector2({x}, {y})",
              'script = ExtResource("prop_s")', f'texture = ExtResource("{name}")']
        if not extra.get("solid", True):
            L.append("solid = false")
        if "frames" in extra:
            L += [f"frames = {extra['frames']}", f"fps = {float(extra['fps'])}"]
        L.append("")
    for n, x, y, s, c, e, why in LIGHTS:
        L += [f"; {why}", f'[node name="{n}" type="PointLight2D" parent="."]', f"position = Vector2({x}, {y})",
              f"color = Color({c}, 1)", f"energy = {e}", 'texture = SubResource("lightTex")', f"texture_scale = {s}", ""]
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
