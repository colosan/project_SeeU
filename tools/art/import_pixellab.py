"""Import PixelLab map objects: keep the SHAPE, replace colour/noise/outline with our rules.

  python tools/art/import_pixellab.py            # import every entry in SOURCES that is missing
  python tools/art/import_pixellab.py --force org_arm.png

Steps: download (cached by id) -> harmonize every pixel onto our material ramps
(hue family + nearest luminance) -> remove stray pixels -> sel-out outline once.
Never deletes; overwrites only names listed after --force.
"""
import colorsys
import os
import sys
import urllib.request

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pix import RAMPS, Pix  # noqa: E402

OUT = "assets/env/basement/organic"
CACHE = "build/pixellab_cache"
SOURCES = {  # out name: (PixelLab map-object id, hint for neutral greys)
    "org_android_lying.png": ("e4317f37-d022-4751-b71d-036a84357960", "shell"),
    "org_android_sit.png": ("5a3c7f4b-7c57-442c-9690-67fdfba72a6f", "shell"),
    "org_arm.png": ("c6b111a2-0a1c-4c1c-93ed-cd784846078b", "shell"),
    "org_legs.png": ("b4d0d864-5044-487c-9076-a0174296d8ba", "shell"),
    "org_cables.png": ("bd0a4172-42d6-4353-8d0a-e8c064a8ea8c", "rubber"),
    "org_head.png": ("69afa5f4-d3ba-44e9-a85e-77d4cf7b593d", "shell"),
}


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def family(rgb, grey):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    hd = h * 360
    if s < 0.2:
        if grey == "shell" and v < 0.3:
            return "plastic"                 # dark joints on light shells stay dark plastic
        return grey
    if 170 <= hd < 200:
        return "glow"
    if 20 <= hd < 70:
        return "warn"
    if hd < 20 or hd >= 330:
        return "redp"
    if 200 <= hd < 260:
        return "rubber" if v < 0.45 else "tarp"
    return "steel"


def harmonize(im, grey):
    w, h = im.size
    p = Pix(w, h)
    for y in range(h):
        for x in range(w):
            r, g, b, a = im.getpixel((x, y))
            if a < 128:
                continue
            fam = family((r, g, b), grey)
            ramp = RAMPS[fam]
            # step 0 is reserved for the outline, so interior pixels use steps 1..n
            step = min(range(1, len(ramp)), key=lambda k: abs(lum(ramp[k]) - lum((r, g, b))))
            p.px[y][x] = (fam, step)
    return p


def clean(p):
    """Flatten lone pixels inside a material to the majority of their neighbours; drop floating specks."""
    out = [row[:] for row in p.px]
    for y in range(1, p.h - 1):
        for x in range(1, p.w - 1):
            c = p.px[y][x]
            if c is None:
                continue
            nb = [p.px[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            same_mat = [n for n in nb if n is not None and n[0] == c[0]]
            if len(same_mat) == 4 and all(n[1] != c[1] for n in same_mat):
                steps = [n[1] for n in same_mat]
                out[y][x] = (c[0], max(set(steps), key=steps.count))
            if all(n is None for n in nb):
                out[y][x] = None
    p.px = out
    return p


def fetch(oid):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, oid + ".png")
    if not os.path.exists(path):
        urllib.request.urlretrieve(f"https://api.pixellab.ai/mcp/map-objects/{oid}/download", path)
    return Image.open(path).convert("RGBA")


def main(argv):
    force = set(argv[argv.index("--force") + 1:]) if "--force" in argv else set()
    os.makedirs(OUT, exist_ok=True)
    for name, (oid, grey) in SOURCES.items():
        dst = os.path.join(OUT, name)
        if os.path.exists(dst) and name not in force:
            print("kept", dst)
            continue
        im = fetch(oid)
        im = im.crop(im.getbbox())
        p = clean(harmonize(im, grey))
        p.outline()
        p.bbox_crop().image().save(dst)
        print("wrote", dst, "from", oid)


if __name__ == "__main__":
    main(sys.argv[1:])
