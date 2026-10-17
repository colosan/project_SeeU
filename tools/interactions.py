"""Shared by tools/layout_*.py: turns a PLAN entry's interaction extras into an Interactable child node
(scripts/world/interactable.gd) under the prop.

PLAN extras:
  "examine": ["page", "page", ...]   - examined: these pages are shown in the dialogue box (draft lines: docs/WORLD_PROPS.md 9)
  "use": "elevator"                  - used: opens the elevator's floor panel
  "prompt": "조사"                    - the hint word (default: 조사 for examine, 타기 for the elevator)

The trigger box covers the prop's lower part; for a prop hung on a wall it reaches down to the floor at the
wall's foot (`floor_gap` screen px below the prop's base), so standing in front of the wall is enough.
"""
import json

EXT = '[ext_resource type="Script" path="res://scripts/world/interactable.gd" id="interact_s"]'


def has_interaction(extra):
    return "examine" in extra or "use" in extra


def scene_lines(parent, extra, w, h, floor_gap=0.0):
    """Lines of the Interactable node under `parent`; w, h = the prop sprite's size and floor_gap in screen px."""
    if not has_interaction(extra):
        return []
    box_h = h * 0.5 + floor_gap + 30
    cy = -h * 0.5 + (h * 0.5 + floor_gap + 30) / 2 - 15
    L = [f'[node name="Interact" type="Area2D" parent="{parent}"]', f"position = Vector2(0, {cy:g})",
         'script = ExtResource("interact_s")', f"size = Vector2({w + 24:g}, {box_h:g})"]
    if "examine" in extra:
        L.append("lines = PackedStringArray(" + ", ".join(json.dumps(p, ensure_ascii=False) for p in extra["examine"]) + ")")
    if "use" in extra:
        L.append(f'action = &"{extra["use"]}"')
    prompt = extra.get("prompt", "타기" if extra.get("use") == "elevator" else "조사")
    L.append("prompt = " + json.dumps(prompt, ensure_ascii=False))
    L.append("")
    return L
