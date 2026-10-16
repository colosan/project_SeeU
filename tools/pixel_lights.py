"""Shared by tools/layout_*.py: places PixelLight nodes (scripts/world/pixel_light.gd) on their visible
sources and checks them.

A light record (dict) in a layout's LIGHTS table:
  name, type ("point" | "spot" | "beam"), color (r, g, b), energy, radius (native px), why (reason)
  src     - the visible source: a PLAN entry (its "id" extra, or its file name if unique), or
            "room:<key>" for something drawn in the room background (rect given in ROOM_SOURCES)
  at      - floor point (native x, y) under the source; optional for prop sources: then the light sits on
            the centre of the prop's emissive pixels (its .emit.png mask, all frames), its floor point
            `front` px in front of the prop's base line (or of the wall base for wall-hung props)
  height  - native px of the source above its floor point (derived like `at` when omitted)
  optional: dir (x, y, z: x east, y south, z up), angle (deg), pool, mouth, haze, halo, halo_r,
            shadows (bool), flicker [multipliers per frame] (synced to the source prop's frames), front
Coordinates are native px (1/3 of screen px).
"""
from PIL import Image

S = 3
TYPES = {"point": 0, "spot": 1, "beam": 2}


def emissive_pixels(png_path, frames=1):
    """Local (x, y) of every emissive pixel, all frames folded onto one frame."""
    import os
    mask = png_path[:-4] + ".emit.png"
    if not os.path.exists(mask):
        return []
    im = Image.open(mask).convert("L")
    fw = im.width // frames
    px = im.load()
    out = set()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] > 0:
                out.add((x % fw, y))
    return sorted(out)


def resolve(light, props, room_sources):
    """props: {key: dict(png, frames, fps, left, top, base_y, wall_base or None, node)} in native px.
    Returns (floor_x, floor_y, height, source_node_or_None) in native px."""
    src = light["src"]
    if src.startswith("room:"):
        fx, fy = light["at"]
        return fx, fy, light["height"], None
    p = props[src]
    if "at" in light and "height" in light:
        fx, fy = light["at"]
        return fx, fy, light["height"], p["node"]
    pts = emissive_pixels(p["png"], p["frames"])
    if not pts:
        raise SystemExit(f"light {light['name']}: source {src} has no emissive pixels (run tools/art/gen_emission.py)")
    cx = p["left"] + sum(x for x, _ in pts) / len(pts) + 0.5
    cy = p["top"] + sum(y for _, y in pts) / len(pts) + 0.5
    base = p["wall_base"] if p.get("wall_base") is not None else p["base_y"]
    fy = base + light.get("front", 1 if p.get("wall_base") is None else 2)
    return cx, fy, round(fy - cy, 1), p["node"]


def check(lights, props, room_sources):
    """Every light must sit on its visible source and stay within the budget the shader allows."""
    problems = []
    if len(lights) > 16:
        problems.append(f"{len(lights)} lights: the lighting pass takes at most 16 per map")
    for l in lights:
        src = l["src"]
        if src.startswith("room:"):
            if src[5:] not in room_sources:
                problems.append(f"light {l['name']}: unknown room source {src}")
                continue
            x0, y0, x1, y1 = room_sources[src[5:]]
            fx, fy = l["at"]
            sx, sy = fx, fy - l["height"]
            if not (x0 <= sx <= x1 and y0 <= sy <= y1):
                problems.append(f"light {l['name']}: source point ({sx:.0f}, {sy:.0f}) is not on {src}")
            continue
        if src not in props:
            problems.append(f"light {l['name']}: no visible source ({src})")
            continue
        fx, fy, h, _node = resolve(l, props, room_sources)
        p = props[src]
        sx, sy = fx - p["left"], fy - h - p["top"]
        pts = emissive_pixels(p["png"], p["frames"])
        if not any(abs(x + 0.5 - sx) <= 2.5 and abs(y + 0.5 - sy) <= 2.5 for x, y in pts):
            problems.append(f"light {l['name']}: source point is not on a glowing pixel of {src}")
        if l.get("flicker") and p["frames"] < 2:
            problems.append(f"light {l['name']}: flicker needs an animated source")
        if l.get("flicker") and len(l["flicker"]) != p["frames"]:
            problems.append(f"light {l['name']}: flicker has {len(l['flicker'])} steps, {src} has {p['frames']} frames")
    return problems


def _vec(v):
    return ", ".join(f"{float(c):g}" for c in v)


def scene_lines(lights, props, room_sources):
    """[node] blocks for the .tscn (needs ext_resource id "light_s" = pixel_light.gd)."""
    L = []
    for l in lights:
        fx, fy, h, node = resolve(l, props, room_sources)
        L += [f"; {l['why']}", f'[node name="{l["name"]}" type="Node2D" parent="."]',
              f"position = Vector2({fx * S:g}, {fy * S:g})", 'script = ExtResource("light_s")',
              f"type = {TYPES[l['type']]}", f"color = Color({_vec(l['color'])}, 1)", f"energy = {l['energy']}",
              f"height = {float(h):g}", f"radius = {float(l.get('radius', 80)):g}"]
        if not l.get("shadows", True):
            L.append("casts_shadows = false")
        if "dir" in l:
            L.append(f"direction = Vector3({_vec(l['dir'])})")
        if "angle" in l:
            L.append(f"angle = {float(l['angle']):g}")
        for key, prop in (("pool", "pool_radius"), ("mouth", "mouth_radius"), ("haze", "haze"),
                          ("halo", "halo"), ("halo_r", "halo_radius")):
            if key in l:
                L.append(f"{prop} = {float(l[key]):g}")
        if l.get("flicker"):
            L.append(f"flicker = PackedFloat32Array({_vec(l['flicker'])})")
            L.append(f"flicker_fps = {float(props[l['src']]['fps']):g}")
            L.append(f'sync_prop = NodePath("../{node}")')
        L.append("")
    return L
