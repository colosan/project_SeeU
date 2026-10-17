"""Pieces of .tscn text shared by the layout scripts (tools/layout_*.py), so every PLAN option means the same
in every map. See docs/ART_PIPELINE.md 6 for the PLAN options."""


def prop_lines(node, pos, why, tex_id, extra, solid=True, height_offset=None):
    """One environment prop (scripts/world/pixel_prop.gd) at screen position pos, with the PLAN extras applied."""
    groups = f' groups=["{extra["group"]}"]' if "group" in extra else ""
    L = [f"; {why}", f'[node name="{node}" type="StaticBody2D" parent="."{groups}]',
         f"position = Vector2({pos[0]:g}, {pos[1]:g})", 'script = ExtResource("prop_s")', f'texture = ExtResource("{tex_id}")']
    if not solid:
        L.append("solid = false")
    if height_offset is not None:                           # lighting: heights count from the wall's base
        L.append(f"height_offset = {height_offset}")
    if "solid_fraction" in extra:
        L.append(f"solid_fraction = {extra['solid_fraction']}")
    if "overlay" in extra:                                  # drawn over the art (the gate over the car)
        L.append(f'overlay = ExtResource("{extra["overlay"]}")')
    if "frames" in extra:
        L += [f"frames = {extra['frames']}", f"fps = {float(extra['fps'])}"]
        if extra.get("autoplay", True) is False:            # frames played on command only (pixel_prop.play_to)
            L.append("autoplay = false")
        if extra.get("flashes"):                            # held still under "reduce flicker" (pause menu)
            L.append("flashes = true")
    if "sound" in extra:                                    # room sound on animation frames (pixel_prop.gd)
        L += [f'sound = "{extra["sound"]}"',
              f"sound_frames = PackedInt32Array({', '.join(str(f) for f in extra['sound_on'])})"]
        if "sound_db" in extra:
            L.append(f"sound_db = {float(extra['sound_db'])}")
    L.append("")
    return L


ROOM_TONE_EXT = '[ext_resource type="Script" path="res://scripts/world/room_tone.gd" id="tone_s"]'


def room_tone_lines(tone):
    """The map's quiet background loop (scripts/world/room_tone.gd); tone = (name, reason)."""
    return [f"; {tone[1]}", '[node name="RoomTone" type="AudioStreamPlayer" parent="."]', 'script = ExtResource("tone_s")',
            f'tone = "{tone[0]}"', ""]
