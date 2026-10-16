"""Builds scenes/world/elevator_hall.tscn from a placement plan with a reason for every object,
then checks the plan: nothing blocks or draws over the walkway from the entrance to the elevator,
floor props stand on the floor, wall props hang inside a wall face, every light has a visible source.

  python tools/layout_elevator_hall.py

Room story (native px; environment drawn at 1/3 and shown at 3x):
  * The corridor is where the junkyard ends and the building begins: still underground and grey,
    but swept. A little junk has drifted in from the junkyard and was pushed against the walls.
  * The old freight elevator stands in the alcove at the end of the corridor. Its shaft frame runs
    off the top of the map: the way on is UP. Its caged bulb is the brightest light in the room,
    its call button pulses - the car is waiting.
  * The route is worn into the concrete (lighter, cleaner) and the flatbed cart's wheel tracks run
    from the entrance into the elevator. Lamps on the corridor wall lead the eye from the doorway
    to the elevator, each one a step closer.

Lighting (scripts/world/pixel_lighting.gd, one PixelLight per visible source, LIGHTS below): two warm
wall lamps along the corridor, then the elevator's caged bulb high in the shaft frame - the brightest
light, the goal - and the cyan pulse of the call button beside the gate.
"""
import ast
import math
import os

from PIL import Image

import pixel_lights


def _floor_consts(names):
    """Read room geometry from the floor generator without running it (same numbers the floor uses)."""
    src = open(os.path.join(os.path.dirname(__file__), "gen_elevator_hall_floor.py"), encoding="utf-8").read()
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in names:
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


_c = _floor_consts({"PATH", "HALF", "ENTRANCE", "CORRIDOR_WALL", "ALCOVE_WALL", "FLOOR_BOTTOM", "RIGHT_WALL_X"})
PATH, HALF, ENTRANCE = _c["PATH"], _c["HALF"], _c["ENTRANCE"]
CORRIDOR_WALL, ALCOVE_WALL, FLOOR_BOTTOM, RIGHT_WALL_X = (_c[k] for k in ("CORRIDOR_WALL", "ALCOVE_WALL", "FLOOR_BOTTOM", "RIGHT_WALL_X"))

S = 3                                                   # environment scale
WALK_CLEAR = HALF + 6                                   # native half width that must stay free of colliders
SCENE = "scenes/world/elevator_hall.tscn"
BASEMENT = "res://scenes/world/basement_test.tscn"

# Wall colliders (native Rect2: x, y, w, h)
WALLS = [
    (0, 0, CORRIDOR_WALL[2] + 1, CORRIDOR_WALL[3] + 1),              # corridor back wall
    (ALCOVE_WALL[0], 0, 320 - ALCOVE_WALL[0], ALCOVE_WALL[3] + 1),     # alcove back wall
    (0, 0, 14, ENTRANCE[1]),                                          # left wall above the entrance
    (0, ENTRANCE[3] + 1, 14, 240 - ENTRANCE[3] - 1),                  # left wall below the entrance
    (RIGHT_WALL_X, 0, 320 - RIGHT_WALL_X, 240),                       # right wall
    (0, FLOOR_BOTTOM + 1, 320, 240 - FLOOR_BOTTOM - 1),               # front (south) wall
]

E, B = "elevator", "basement/code"
# (folder under assets/env, file, x, y, kind, reason, extra)
#   x, y = native base-line centre. kind: goal | floor (solid) | wall (hung on a wall face) | decal (flat on the floor)
PLAN = [
    # 1. the destination
    (E, "elevator", 252, 93, "goal",
     "freight elevator centred in the alcove at the corridor's end: the alcove walls and the walkway frame it, "
     "its shaft frame runs off the top of the map (the way on is up)", {"solid_fraction": 0.06}),
    (E, "a_call", 296, 65, "wall",
     "call box right of the gate at hand height (~1.1 m); the pulsing button says the car is waiting", {"frames": 6, "fps": 4}),
    (E, "stool", 296, 101, "floor",
     "the operator's stool under the call box, tucked against the right wall, clear of the gate", {}),
    # 2. lamps that lead from the doorway to the elevator
    (E, "wall_lamp", 44, 78, "wall", "first lamp, right by the entrance: the first light you see coming out of the junkyard", {}),
    (E, "a_lamp", 150, 78, "wall", "second lamp halfway down the corridor, an old bulb that flickers", {"frames": 8, "fps": 8}),
    (E, "notice", 92, 86, "wall",
     "notice board between the lamps at eye level, where people wait; one sheet shows the building floor by floor", {}),
    # 3. the leaking pipe
    (E, "drum", 119, 117, "floor", "drum set right under the leaking pipe joint (x 119) to catch the drips", {}),
    (E, "a_drip", 119, 101, "wall", "drop falling from the pipe joint into the drum", {"frames": 10, "fps": 10}),
    (E, "f_drip_puddle", 134, 121, "decal", "water splashed out of the overfull drum", {}),
    # 4. junk that drifted in from the junkyard, pushed to the walls (sparse: this is the cleaner level)
    (B, "c_small3", 42, 118, "floor", "junk that spilled through the doorway, pushed against the wall beside the entrance", {}),
    (B, "c_small1", 92, 212, "floor", "junk drifted in from the junkyard, swept against the south wall", {}),
    (B, "c_small2", 182, 212, "floor", "more swept junk along the south wall, further down the corridor", {}),
    # 5. the cart that made the wheel tracks
    (E, "cart", 262, 206, "floor",
     "flatbed cart with a crate, parked on the open floor south of the elevator, out of the walkway", {}),
]

AMBIENT = (0.35, 0.37, 0.46)                            # same dim cool base as the junkyard (still underground)
WARM, CYAN = (1.0, 0.84, 0.60), (0.40, 0.92, 0.95)
# Native px. Each light sits on the centre of its source prop's glowing pixels (the .emit.png mask);
# wall-hung sources get their floor point 2 px in front of the wall base (tools/pixel_lights.py).
LIGHTS = [
    dict(name="EntryLamp", type="point", src="wall_lamp", color=WARM, energy=2.7, radius=124, halo=0.55, halo_r=5,
         why="first wall lamp right inside the doorway: a warm pool to walk into out of the junkyard"),
    dict(name="FlickerLamp", type="point", src="a_lamp", color=WARM, energy=2.7, radius=124, halo=0.55, halo_r=5,
         flicker=[1, 1, 1, 1, 0.45, 1, 0, 1],
         why="halfway lamp with an old bulb: the light flickers in step with the bulb's frames"),
    dict(name="ElevatorBulb", type="point", src="elevator", color=(1.0, 0.88, 0.68), energy=2.6, radius=170,
         halo=0.6, halo_r=8,
         why="caged bulb high in the shaft frame: the brightest light in the hall, it pours down over the gate - the goal"),
    dict(name="CallGlow", type="point", src="a_call", color=CYAN, energy=1.4, radius=30, halo=0.45, halo_r=4,
         flicker=[1, 1, 0.75, 0.5, 0.25, 0.5], why="the call button pulses cyan: the car is waiting"),
]

SPAWNS = [  # name, x, y (native), facing, reason
    ("FromBasement", 37, 148, "east", "just inside the entrance, on the walkway, facing down the corridor"),
]
EXITS = [  # name, rect (native x, y, w, h), target scene, target spawn
    ("ToBasement", (0, ENTRANCE[1], 14, ENTRANCE[3] - ENTRANCE[1] + 1), BASEMENT, "FromElevator"),
]
PLAYER_FEET = (6, 4.7)                                   # half width, height of the player's feet box (native)


def is_floor(x, y):
    if 14 <= x < RIGHT_WALL_X and CORRIDOR_WALL[3] < y <= FLOOR_BOTTOM:
        return True
    if ALCOVE_WALL[0] <= x < RIGHT_WALL_X and ALCOVE_WALL[3] < y <= FLOOR_BOTTOM:
        return True
    return ENTRANCE[0] <= x <= ENTRANCE[2] and ENTRANCE[1] <= y <= ENTRANCE[3]


def walk_samples():
    out = []
    for (x0, y0), (x1, y1) in zip(PATH, PATH[1:]):
        n = max(1, int(math.dist((x0, y0), (x1, y1)) / 2))
        out += [(x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n) for t in range(n)]
    return out + [PATH[-1]]


def sprite_size(folder, name, extra):
    im = Image.open(f"assets/env/{folder}/{name}.png")
    return im.width // extra.get("frames", 1), im.height


def screen_pos(folder, name, x, y, extra):
    """Base-centre position in screen px, snapped so the sprite's left edge sits on the 3x pixel grid."""
    w, _ = sprite_size(folder, name, extra)
    left = round(x - w / 2)
    return left * S + w * S / 2, y * S


def collider(folder, name, x, y, extra):
    """Native-px collider box, same maths as pixel_prop.gd."""
    w, h = sprite_size(folder, name, extra)
    cw, ch = w * 0.8, h * extra.get("solid_fraction", 0.35)
    return (x - cw / 2, y - ch, x + cw / 2, y)


def wall_base(folder, name, x, y, extra):
    """Floor row under the wall face a wall-hung prop is on (its lighting heights count from there)."""
    w, h = sprite_size(folder, name, extra)
    left = round(x - w / 2)
    for wx0, wy0, wx1, wy1 in (CORRIDOR_WALL, ALCOVE_WALL):
        if wx0 <= left and left + w - 1 <= wx1 and wy0 <= y - h and y - 1 <= wy1:
            return wy1 + 1
    return y


def light_props():
    """PLAN entries usable as light sources, keyed by their (unique) file name; native px."""
    props = {}
    for i, (folder, name, x, y, kind, why, extra) in enumerate(PLAN):
        w, h = sprite_size(folder, name, extra)
        left = round(x - w / 2)
        props[name] = dict(png=f"assets/env/{folder}/{name}.png", frames=extra.get("frames", 1), fps=extra.get("fps", 8),
                           left=left, top=y - h, base_y=y, node=f"{name}_{i}",
                           wall_base=wall_base(folder, name, x, y, extra) if kind == "wall" else None)
    return props


def check():
    problems = []
    pts = walk_samples()
    for px, py in pts:                                       # the route itself is open floor
        if not is_floor(round(px), round(py)):
            problems.append(f"walkway leaves the floor at ({px:.0f}, {py:.0f})")
            break
    for folder, name, x, y, kind, why, extra in PLAN:
        w, h = sprite_size(folder, name, extra)
        left, top = round(x - w / 2), y - h
        if kind in ("floor", "goal", "decal"):               # stands on the floor, not on a wall or in the void
            for fx in (left + 2, round(x), left + w - 3):
                if not is_floor(fx, y - 1):
                    problems.append(f"{name}: base at ({fx}, {y - 1}) is not on the floor (floating)")
                    break
        if kind == "wall":                                    # hangs fully inside one wall face
            if not any(wx0 <= left and left + w - 1 <= wx1 and wy0 <= top and y - 1 <= wy1
                       for wx0, wy0, wx1, wy1 in (CORRIDOR_WALL, ALCOVE_WALL)):
                problems.append(f"{name}: not inside a wall face")
        if kind in ("floor",):
            x0, y0, x1, y1 = collider(folder, name, x, y, extra)
            for px, py in pts:
                nx, ny = min(max(px, x0), x1), min(max(py, y0), y1)
                if math.dist((px, py), (nx, ny)) < WALK_CLEAR:
                    problems.append(f"{name}: blocks the walkway near ({px:.0f}, {py:.0f})")
                    break
            # visual: a prop standing IN FRONT of (south of) the walkway must not draw over it
            for px, py in pts:
                if left - 2 <= px <= left + w + 2 and top <= py + HALF * 0.75 and py < y:
                    problems.append(f"{name}: drawn over the walkway near ({px:.0f}, {py:.0f})")
                    break
        if kind == "goal":                                    # the walkway must end at the goal
            x0, y0, x1, y1 = collider(folder, name, x, y, extra)
            ex, ey = PATH[-1]
            if not (x0 <= ex <= x1 and ey - y1 <= 6):
                problems.append(f"{name}: the walkway does not end at it")
    problems += pixel_lights.check(LIGHTS, light_props(), {})
    for name, sx, sy, _face, _why in SPAWNS:
        if not any(math.dist((sx, sy), q) <= HALF for q in pts):
            problems.append(f"spawn {name}: not on the walkway")
        for ename, (ex, ey, ew, eh), *_ in EXITS:
            if sx - PLAYER_FEET[0] < ex + ew and sx + PLAYER_FEET[0] > ex and sy - PLAYER_FEET[1] < ey + eh and sy > ey:
                problems.append(f"spawn {name}: inside exit {ename} (would bounce straight back)")
    return problems


def write_scene():
    files = list(dict.fromkeys((f, n) for f, n, *_ in PLAN))
    L = ["[gd_scene format=3]", "",
         '[ext_resource type="Script" path="res://scripts/world/pixel_room.gd" id="room_s"]',
         '[ext_resource type="Texture2D" path="res://assets/env/elevator/hall_floor.png" id="floor"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_prop.gd" id="prop_s"]',
         '[ext_resource type="Script" path="res://scripts/world/exit_zone.gd" id="exit_s"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_lighting.gd" id="lighting_s"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_light.gd" id="light_s"]',
         '[ext_resource type="PackedScene" path="res://scenes/characters/player.tscn" id="player"]']
    L += [f'[ext_resource type="Texture2D" path="res://assets/env/{f}/{n}.png" id="{n}"]' for f, n in files]
    L += ["", '[node name="ElevatorHall" type="Node2D"]', "y_sort_enabled = true", "",
          "; 2.5D pixel lighting for this map (height buffer + light pass + composite)",
          '[node name="Lighting" type="Node" parent="."]', 'script = ExtResource("lighting_s")',
          f"ambient = Color({AMBIENT[0]}, {AMBIENT[1]}, {AMBIENT[2]}, 1)", ""]
    walls = ", ".join(f"Rect2({x}, {y}, {w}, {h})" for x, y, w, h in WALLS)
    L += ['[node name="Room" type="Sprite2D" parent="."]', "z_index = -10", 'texture = ExtResource("floor")',
          'script = ExtResource("room_s")', f"walls = Array[Rect2]([{walls}])", ""]
    for i, (folder, name, x, y, kind, why, extra) in enumerate(PLAN):
        sx, sy = screen_pos(folder, name, x, y, extra)
        L += [f"; {why}", f'[node name="{name}_{i}" type="StaticBody2D" parent="."]', f"position = Vector2({sx:g}, {sy:g})",
              'script = ExtResource("prop_s")', f'texture = ExtResource("{name}")']
        if kind in ("wall", "decal"):
            L.append("solid = false")
        if kind == "wall":                                    # lighting: heights count from the wall's base
            L.append(f"height_offset = {wall_base(folder, name, x, y, extra) - y}")
        if "solid_fraction" in extra:
            L.append(f"solid_fraction = {extra['solid_fraction']}")
        if "frames" in extra:
            L += [f"frames = {extra['frames']}", f"fps = {float(extra['fps'])}"]
        L.append("")
    L += pixel_lights.scene_lines(LIGHTS, light_props(), {})
    for name, (x, y, w, h), target, spawn in EXITS:
        L += [f"; back to {target.rsplit('/', 1)[-1]}", f'[node name="{name}" type="Area2D" parent="."]',
              f"position = Vector2({(x + w / 2) * S:g}, {(y + h / 2) * S:g})", 'script = ExtResource("exit_s")',
              f'target_map = "{target}"', f'target_spawn = &"{spawn}"', f"size = Vector2({w * S}, {h * S})", ""]
    for name, x, y, face, why in SPAWNS:
        L += [f"; {why}", f'[node name="{name}" type="Marker2D" parent="."]', f"position = Vector2({x * S}, {y * S})",
              f'metadata/facing = "{face}"', ""]
    sx, sy = SPAWNS[0][1], SPAWNS[0][2]
    L += ["; placed on the entrance spawn when the scene is run on its own; Game moves her on arrival",
          '[node name="Player" parent="." instance=ExtResource("player")]', f"position = Vector2({sx * S}, {sy * S})", ""]
    with open(SCENE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    probs = check()
    for p in probs:
        print("PROBLEM:", p)
    write_scene()
    print(f"wrote {SCENE} with {len(PLAN)} objects, {len(LIGHTS)} lights, {len(probs)} problems")
