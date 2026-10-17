"""Builds scenes/world/elevator_hall.tscn from a placement plan with a reason for every object,
then checks the plan: nothing blocks or draws over the walkway from the entrance to the elevator,
floor props stand on the floor, wall props hang inside a wall face, every light has a visible source.

  python tools/layout_elevator_hall.py

Room story (native px; environment drawn at 1/3 and shown at 3x). A tall map (320x480, the view is 320x360):
  * Out of the junkyard you come in at the bottom left and go right along a short passage, then the way
    turns north into a long corridor: straight ahead to the far end. This is where the junkyard ends and the
    building begins: still underground and grey, but swept. A little junk drifted in and was pushed to the walls.
  * The old freight elevator stands at the corridor's far (top) end. Its shaft frame runs off the top of
    the map: the way on is UP. Its caged bulb is the brightest light in the room, its call button pulses -
    the car is waiting.
  * The route is worn into the concrete (lighter, cleaner) and the flatbed cart's wheel tracks run from the
    entrance round the corner into the elevator. Two lamps on the passage wall lead you to the corner, then
    the elevator's bulb pulls you up the corridor.
  * The front (south) wall has depth (hall_front.png, drawn over everything): the junk swept against it is
    half hidden behind it, and so is SeeU when she walks close to it.

Lighting (scripts/world/pixel_lighting.gd, one PixelLight per visible source, LIGHTS below): two warm
wall lamps along the passage, then the elevator's caged bulb high in the shaft frame - the brightest
light, the goal - and the cyan pulse of the call button beside the gate.
"""
import ast
import math
import os

from PIL import Image

import interactions
import pixel_lights
import scene_parts


def _floor_consts(names):
    """Read room geometry from the floor generator without running it (same numbers the floor uses)."""
    src = open(os.path.join(os.path.dirname(__file__), "gen_elevator_hall_floor.py"), encoding="utf-8").read()
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in names:
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


_c = _floor_consts({"W", "H", "PATH", "HALF", "ENTRANCE", "PASSAGE_WALL", "ALCOVE_WALL", "CORRIDOR_X", "FLOOR_BOTTOM",
                    "RIGHT_WALL_X"})
W, H, PATH, HALF, ENTRANCE = _c["W"], _c["H"], _c["PATH"], _c["HALF"], _c["ENTRANCE"]
PASSAGE_WALL, ALCOVE_WALL, CORRIDOR_X, FLOOR_BOTTOM, RIGHT_WALL_X = (
    _c[k] for k in ("PASSAGE_WALL", "ALCOVE_WALL", "CORRIDOR_X", "FLOOR_BOTTOM", "RIGHT_WALL_X"))
FACES = (PASSAGE_WALL, ALCOVE_WALL)                     # back wall faces that wall-hung props can hang on

S = 3                                                   # environment scale
WALK_CLEAR = HALF + 6                                   # native half width that must stay free of colliders
SCENE = "scenes/world/elevator_hall.tscn"
BASEMENT = "res://scenes/world/basement_test.tscn"

# Wall colliders (native Rect2: x, y, w, h)
WALLS = [
    (0, 0, CORRIDOR_X, PASSAGE_WALL[3] + 1),                          # the solid block and the passage's back wall
    (CORRIDOR_X, 0, W - CORRIDOR_X, ALCOVE_WALL[3] + 1),              # the corridor's far wall (elevator)
    (0, 0, 14, ENTRANCE[1]),                                          # left wall above the entrance
    (0, ENTRANCE[3] + 1, 14, H - ENTRANCE[3] - 1),                    # left wall below the entrance
    (RIGHT_WALL_X, 0, W - RIGHT_WALL_X, H),                           # right wall
    (0, FLOOR_BOTTOM + 1, W, H - FLOOR_BOTTOM - 1),                   # front (south) wall
]

E, B = "elevator", "basement/code"
# (folder under assets/env, file, x, y, kind, reason, extra)
#   x, y = native base-line centre. kind: goal | floor (solid) | wall (hung on a wall face) | decal (flat on the floor)
PLAN = [
    # 1. the destination, at the far end of the long corridor
    (E, "a_elevator", 232, 93, "goal",
     "freight elevator centred at the far end of the long corridor: the corridor walls and the walkway frame it, "
     "its shaft frame runs off the top of the map (the way on is up). Its frames are the folding gate opening: "
     "they play only when she rides (Game._ride), not on a loop",
     {"solid_fraction": 0.06, "frames": 6, "fps": 12, "autoplay": False, "group": "elevator",
      "sound": "gate", "sound_on": [1, 3, 5], "overlay": "a_elevator_gate"}),
    (E, "a_call", 296, 65, "wall",
     "call box right of the gate at hand height (~1.1 m); the pulsing button says the car is waiting", {"frames": 6, "fps": 4}),
    (E, "stool", 296, 101, "floor",
     "the operator's stool under the call box, tucked against the right wall, clear of the gate", {}),
    # 2. lamps that lead from the doorway to the corner where the way turns north
    (E, "wall_lamp", 44, 294, "wall", "first lamp, right by the entrance: the first light you see coming out of the junkyard", {}),
    (E, "a_lamp", 140, 294, "wall",
     "second lamp at the corner where the way turns north, an old bulb that flickers",
     {"frames": 8, "fps": 8, "sound": "buzz", "sound_on": [7], "sound_db": -20, "flashes": True}),   # it buzzes as it catches again
    (E, "notice", 92, 302, "wall",
     "notice board between the lamps at eye level; one sheet shows the building floor by floor", {}),
    # 3. the leaking pipe
    (E, "drum", 119, 333, "floor", "drum set right under the leaking pipe joint (x 119) to catch the drips", {}),
    (E, "a_drip", 119, 317, "wall", "drop falling from the pipe joint into the drum", {"frames": 10, "fps": 10,
     "sound": "drip", "sound_on": [8], "sound_db": -15}),                # frame 8: the drop has landed in the drum
    (E, "f_drip_puddle", 134, 337, "decal", "water splashed out of the overfull drum", {}),
    # 4. junk that drifted in from the junkyard, pushed to the walls (sparse: this is the cleaner level)
    (B, "c_small3", 42, 334, "floor", "junk that spilled through the doorway, pushed against the wall beside the entrance", {}),
    (B, "c_small1", 92, 448, "floor",
     "junk swept against the front wall, half hidden behind it (the wall has depth)", {}),
    (B, "c_small2", 180, 444, "floor", "more swept junk along the front wall at the corner, half hidden behind it", {}),
    # 5. floor guide lights flush with the concrete on both sides of the walkway up the long corridor: they
    #    lead the eye to the elevator (rule 8 - light, not arrows). Still underground and neglected: one is
    #    dead, one flickers.
    *[(E, "a_guide" if (gx, gy) == (252, 230) else ("f_guide_off" if (gx, gy) == (214, 275) else "f_guide"), gx, gy,
       "decal", "guide light beside the walkway up the corridor" + (", dead" if (gx, gy) == (214, 275) else
                                                                     (", flickering" if (gx, gy) == (252, 230) else "")),
       {"id": f"guide_{gx}_{gy}", **({"frames": 8, "fps": 8, "flashes": True} if (gx, gy) == (252, 230) else {})})
      for gy in (140, 185, 230, 275, 320) for gx in (214, 252)],
    # 6. the cart that made the wheel tracks
    (E, "cart", 284, 240, "floor",
     "flatbed cart with a crate, parked against the corridor's right wall halfway up, out of the walkway", {}),
]

# What SeeU can examine or use here (draft lines - docs/WORLD_PROPS.md 9). Keyed by file name.
INTERACT = {
    "a_elevator": {"use": "elevator", "prompt": "타기"},
    "a_call": {"use": "elevator", "prompt": "호출"},
    "notice": {"examine": ["층별 안내도.", "위에서부터 PLATINUM, LIVE, FAN, COVER, DEMO.", "맨 아래 칸에는 아무것도 적혀 있지 않다."]},
    "drum": {"examine": ["새는 배관 아래 받쳐 둔 드럼통. 물이 넘치고 있다."]},
    "cart": {"examine": ["상자를 실은 손수레.", "바퀴 자국이 엘리베이터까지 이어진다."]},
    "stool": {"examine": ["호출 버튼 아래 놓인 낡은 의자.", "엘리베이터를 몰던 누군가가 앉던 자리 같다. 지금은 비어 있다."]},
}

ROOM_TONE = ("hum", "the mains hum of the hall's old fittings - power still runs here")   # quiet background loop (scripts/world/room_tone.gd)
AMBIENT = (0.41, 0.43, 0.52)                            # dim cool base, a step under the junkyard's (still underground):
                                                         # enough that the corridor's dark side and the cart still read
WARM, CYAN = (1.0, 0.84, 0.60), (0.40, 0.92, 0.95)
# Native px. Each light sits on the centre of its source prop's glowing pixels (the .emit.png mask);
# wall-hung sources get their floor point 2 px in front of the wall base (tools/pixel_lights.py).
LIGHTS = [
    # Wall lamps light only the half-space in front of the wall they hang on (a wide spot aimed out and down):
    # as point lights, the screen-space shadows let them leak round the block's corner onto the corridor floor.
    # front=6: the lamps' floor point sits a step out from the wall, so the junk along the wall right under them
    # throws its shadow down toward us and short, not sideways along the wall base
    dict(name="EntryLamp", type="spot", src="wall_lamp", color=WARM, energy=2.7, radius=124, dir=(0, 1, -0.25),
         angle=190, halo=0.55, halo_r=5, front=6,
         why="first wall lamp right inside the doorway: a warm pool to walk into out of the junkyard"),
    dict(name="FlickerLamp", type="spot", src="a_lamp", color=WARM, energy=2.7, radius=124, dir=(0, 1, -0.25),
         angle=190, halo=0.55, halo_r=5, flicker=[1, 1, 1, 1, 0.45, 1, 0, 1], front=6,
         why="lamp at the corner where the way turns north, an old bulb: the light flickers in step with its frames"),
    dict(name="ElevatorBulb", type="point", src="a_elevator", color=(1.0, 0.88, 0.68), energy=2.6, radius=170,
         halo=0.6, halo_r=8, shadows=False,
         why="caged bulb high in the shaft frame: the brightest light in the hall, it pours down over the gate - the goal. "
             "No shadows: it hangs in front of the frame, and the screen-space shadow of the frame on the wall right "
             "behind it came out as horizontal stripes on both sides of the elevator"),
    # the guide lights: small warm pools on the floor, one after another up the corridor (the dead one has none)
    *[dict(name=f"Guide_{gx}_{gy}", type="point", src=f"guide_{gx}_{gy}", color=(1.0, 0.72, 0.38), energy=1.3,
           radius=30, halo=0.25, halo_r=3, shadows=False,
           **({"flicker": [1, 1, 0.5, 1, 1, 0, 1, 0.5]} if (gx, gy) == (252, 230) else {}),
           why="guide light set in the floor beside the walkway: a warm pool, the next step towards the elevator")
      for gy in (140, 185, 230, 275, 320) for gx in (214, 252) if (gx, gy) != (214, 275)],
    dict(name="CallGlow", type="point", src="a_call", color=CYAN, energy=1.4, radius=30, halo=0.45, halo_r=4,
         flicker=[1, 1, 0.75, 0.5, 0.25, 0.5], why="the call button pulses cyan: the car is waiting"),
]

SPAWNS = [  # name, x, y (native), facing, reason
    ("FromBasement", 37, 396, "east", "just inside the entrance, on the walkway, facing along the passage"),
    ("FromElevator", 232, 106, "south", "one step out of the gate, facing down the corridor: where a ride from "
     "another floor lets her out (Game._ride walks her here from inside the car)"),
]
EXITS = [  # name, rect (native x, y, w, h), target scene, target spawn
    ("ToBasement", (0, ENTRANCE[1], 14, ENTRANCE[3] - ENTRANCE[1] + 1), BASEMENT, "FromElevator"),
]
PLAYER_FEET = (6, 4.7)                                   # half width, height of the player's feet box (native)


def is_floor(x, y):
    if 14 <= x < RIGHT_WALL_X and PASSAGE_WALL[3] < y <= FLOOR_BOTTOM:
        return True
    if CORRIDOR_X <= x < RIGHT_WALL_X and ALCOVE_WALL[3] < y <= FLOOR_BOTTOM:
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
    for wx0, wy0, wx1, wy1 in FACES:
        if wx0 <= left and left + w - 1 <= wx1 and wy0 <= y - h and y - 1 <= wy1:
            return wy1 + 1
    return y


def light_props():
    """PLAN entries usable as light sources, keyed by their "id" extra or else their file name; native px."""
    props = {}
    for i, (folder, name, x, y, kind, why, extra) in enumerate(PLAN):
        w, h = sprite_size(folder, name, extra)
        left = round(x - w / 2)
        props[extra.get("id", name)] = dict(png=f"assets/env/{folder}/{name}.png", frames=extra.get("frames", 1), fps=extra.get("fps", 8),
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
                       for wx0, wy0, wx1, wy1 in FACES):
                problems.append(f"{name}: not inside a wall face")
        if kind in ("floor", "goal") and not name.startswith("c_"):   # only swept junk (c_*) may tuck behind a wall
            im = Image.open(f"assets/env/{folder}/{name}.png").split()[3]
            cut = [left + c for c in range(w) if any(im.getpixel((c, r)) > 128 for r in range(h))
                   and not is_floor(left + c, y - 1) and not is_floor(left + c, y - 3)]
            if cut:
                problems.append(f"{name}: art x {min(cut)}..{max(cut)} stands off the floor (cut by a wall)")
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
         '[ext_resource type="Texture2D" path="res://assets/env/elevator/hall_front.png" id="front"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_prop.gd" id="prop_s"]',
         '[ext_resource type="Script" path="res://scripts/world/exit_zone.gd" id="exit_s"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_lighting.gd" id="lighting_s"]',
         '[ext_resource type="Script" path="res://scripts/world/pixel_light.gd" id="light_s"]',
         scene_parts.ROOM_TONE_EXT,
         '[ext_resource type="PackedScene" path="res://scenes/characters/player.tscn" id="player"]',
         interactions.EXT]
    files += [(f, e["overlay"]) for f, _n, *_r, e in PLAN if "overlay" in e]
    L += [f'[ext_resource type="Texture2D" path="res://assets/env/{f}/{n}.png" id="{n}"]' for f, n in files]
    L += ["", '[node name="ElevatorHall" type="Node2D"]', "y_sort_enabled = true", "",
          "; 2.5D pixel lighting for this map (height buffer + light pass + composite)",
          '[node name="Lighting" type="Node" parent="."]', 'script = ExtResource("lighting_s")',
          f"ambient = Color({AMBIENT[0]}, {AMBIENT[1]}, {AMBIENT[2]}, 1)", "",
          *scene_parts.room_tone_lines(ROOM_TONE)]
    walls = ", ".join(f"Rect2({x}, {y}, {w}, {h})" for x, y, w, h in WALLS)
    L += ['[node name="Room" type="Sprite2D" parent="."]', "z_index = -10", 'texture = ExtResource("floor")',
          'script = ExtResource("room_s")', 'front = ExtResource("front")', f"walls = Array[Rect2]([{walls}])", ""]
    for i, (folder, name, x, y, kind, why, extra) in enumerate(PLAN):
        L += scene_parts.prop_lines(f"{name}_{i}", screen_pos(folder, name, x, y, extra), why, name, extra,
                                    solid=kind not in ("wall", "decal"),
                                    height_offset=wall_base(folder, name, x, y, extra) - y if kind == "wall" else None)
        if name in INTERACT:                                 # examinable / usable: an Interactable under the prop
            w, h = sprite_size(folder, name, extra)
            gap = (wall_base(folder, name, x, y, extra) - y) * S if kind == "wall" else 0
            L += interactions.scene_lines(f"{name}_{i}", INTERACT[name], w * S, h * S, gap)
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
