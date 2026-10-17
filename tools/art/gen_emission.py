"""Emission masks for the pixel-lighting system: <name>.emit.png next to every environment PNG.

  python tools/art/gen_emission.py            # (re)write masks whose content changed
  python tools/art/gen_emission.py --check    # report only, write nothing

A mask is a greyscale PNG the same size as its source (animated strips stay strips, frame for
frame): 0 = lit by the room like everything else, 255 = self-luminous (the lighting pass shows
the pixel's true art colour at full brightness). Values in between are dimmer emitters.

Pixels are found by EXACT match against the material ramps in pix.py - the art only uses ramp
colours, so (material, step) is recoverable per pixel. Rules:
  * generic: glow steps >= 2 (screens, LEDs, the call button, robot eyes) and every spark step.
  * per file (FILES): lit bulbs (shell/warn on the bulb only), red rack LEDs, and files where
    nothing glows even though they use glow colours (a printed notice is not a screen).
  * calm glow (STORY_EMITTERS): in a folder listed there ONLY the listed files may glow - the story's
    light sources (docs/ART_PIPELINE.md 8). Everything else in that folder is dark even if its art still
    has glow colours; adding a file to the list (with its reason) is how a new light source is allowed.
Source art is never touched; masks are derived files and are rewritten when they change.
Files without a single emissive pixel get no mask (the lighting treats a missing mask as "nothing glows");
if such a file still has an old mask, the mask is overwritten with an all-dark one (we never delete files).
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pix import RAMPS  # noqa: E402

ROOT = "assets/env"
SUFFIXES = (".emit.png", ".height.png")         # derived companions, never inputs

GENERIC = {
    ("glow", 2): 0.6, ("glow", 3): 0.85, ("glow", 4): 1.0,
    ("spark", 0): 0.6, ("spark", 1): 0.8, ("spark", 2): 1.0, ("spark", 3): 1.0, ("spark", 4): 1.0,
}
BULB = {("shell", 4): 1.0, ("warn", 4): 1.0}

# path relative to ROOT: {"add": extra rules, "region": (x0, y0, x1, y1) the extra rules are limited to
#                         (per frame for strips), "generic": False to switch the generic rules off}
FILES = {
    # caged work bulb hanging in the shaft frame (gen_elevator.elevator: ellipse at 35.5, 8.5 inside x 32..39, y 5..12);
    # the floor dial is also shell 4 but it is a painted dial, not a lamp
    "elevator/elevator.png": {"add": BULB, "region": (32, 5, 39, 12)},
    "elevator/a_elevator.png": {"add": BULB, "region": (32, 5, 39, 12)},      # same bulb in every gate frame
    "elevator/wall_lamp.png": {"add": BULB},                                 # only the bulb uses shell
    "elevator/a_lamp.png": {"add": {**BULB, ("shell", 2): 0.45}},           # LAMP_DIM frame glows weakly, LAMP_OFF is plastic
    "elevator/notice.png": {"generic": False},                              # the glow line is printed on paper
    "elevator/f_guide.png": {"add": {("warn", 4): 1.0, ("warn", 3): 0.75}},  # floor guide light: the amber lens
    "elevator/a_guide.png": {"add": {("warn", 4): 1.0, ("warn", 3): 0.75, ("warn", 2): 0.4, ("warn", 1): 0.25}},
    "basement/code/a_rack.png": {"add": {("redp", 4): 1.0}},                # red status LEDs when on (glow ones are generic)
    "basement/code/s_worklamp.png": {"add": BULB},                          # caged work bulb on its stand
    "basement/digital/dg_s_worklamp.png": {"add": BULB},                    # same lamp in the virtual-world set
    "basement/digital/dg_a_rack.png": {"add": {("redp", 4): 1.0}},          # legacy server: red LEDs when on
}

# Calm-glow rule: folder -> {file: why it may glow}. Only story sources glow; dumped junk is dead.
STORY_EMITTERS = {
    "basement/digital": {
        "dg_s_worklamp.png": "the GC crew's caged work bulbs light the walkway (LIGHTS WorkLampA/B)",
        "dg_a_spark.png": "the severed line sparking at the walkway edge",
        "dg_a_tv.png": "the one TV still fed by that line, flickering an error",
        "dg_t_barrel_tv.png": "the display left on the bit bucket, still powered",
        "dg_a_rack.png": "a legacy server whose few status LEDs still blink (dim)",
        "dg_a_meme_fine.png": "the little burning room: only the flame tips (spark ramp) glow",
        "dg_a_gcbot.png": "the garbage collector's sensor eye breathing like a sleep light: asleep, not dead",
    },
}


def colour_table():
    table = {}
    for mat, ramp in RAMPS.items():
        for step, rgb in enumerate(ramp):
            if rgb in table:
                print(f"warning: {rgb} is both {table[rgb]} and {(mat, step)}; using the first")
                continue
            table[rgb] = (mat, step)
    return table


def allowed(rel):
    """False when rel is in a calm-glow folder but not on its story list."""
    folder, name = os.path.dirname(rel), os.path.basename(rel)
    return folder not in STORY_EMITTERS or name in STORY_EMITTERS[folder]


def mask_for(rel, im, table):
    rule = FILES.get(rel, {})
    if not allowed(rel):
        return Image.new("L", im.size, 0), 0
    generic = GENERIC if rule.get("generic", True) else {}
    extra = rule.get("add", {})
    region = rule.get("region")
    out = Image.new("L", im.size, 0)
    px = im.load()
    opx = out.load()
    hits = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            ms = table.get((r, g, b))
            if ms is None:
                continue
            v = generic.get(ms, 0.0)
            if ms in extra and (region is None or (region[0] <= x <= region[2] and region[1] <= y <= region[3])):
                v = max(v, extra[ms])
            if v > 0:
                opx[x, y] = round(v * 255)
                hits += 1
    return out, hits


def sources():
    for d, _dirs, files in os.walk(ROOT):
        for f in sorted(files):
            if f.endswith(".png") and not f.endswith(SUFFIXES):
                yield os.path.join(d, f)


def main(argv):
    check = "--check" in argv
    table = colour_table()
    for rel in FILES:
        if not os.path.exists(os.path.join(ROOT, rel)):
            print(f"warning: FILES rule for missing {rel}")
    for folder, names in STORY_EMITTERS.items():
        for n in names:
            if not os.path.exists(os.path.join(ROOT, folder, n)):
                print(f"warning: STORY_EMITTERS lists missing {folder}/{n}")
    written = same = 0
    for path in sources():
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        im = Image.open(path).convert("RGBA")
        mask, hits = mask_for(rel, im, table)
        dst = path[:-4] + ".emit.png"
        if hits == 0:                                  # nothing glows: no mask (the lighting treats a missing mask as dark)
            if os.path.exists(dst):                    # ...but an old mask would still light it: make it all dark
                old = Image.open(dst).convert("L")
                if old.size == mask.size and not old.getbbox():
                    same += 1
                    continue
                print(f"{'would darken' if check else 'darkened'} {dst} (nothing glows here any more)")
                if not check:
                    mask.save(dst)
                written += 1
            continue
        if os.path.exists(dst):
            old = Image.open(dst).convert("L")
            if old.size == mask.size and old.tobytes() == mask.tobytes():
                same += 1
                continue
        print(f"{'would write' if check else 'wrote'} {dst} ({hits} emissive px)")
        if not check:
            mask.save(dst)
        written += 1
    print(f"{written} masks {'to update' if check else 'written'}, {same} unchanged")
    return written


if __name__ == "__main__":
    main(sys.argv[1:])
