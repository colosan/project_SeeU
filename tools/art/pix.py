"""Tiny pixel-art drawing kit for SeeU environment art.

Everything is drawn at ENV native resolution (shown at 3x in game) in a
front-on 3/4 view: flat floor, standing things show a TOP face and the FRONT
face below it. Every pixel comes from a material ramp (dark -> light) and a
per-pixel material map is kept so the outline can use each material's darkest
step (sel-out) instead of pure black. Outline is applied ONCE on the final
silhouette, never per part.
"""
from PIL import Image


def _ramp(s):
    return [tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in s.split()]


# Basement world ramps (dull, grey). Index 0 = darkest = that material's outline.
RAMPS = {
    "steel":   _ramp("17181b 2a2c31 3f434a 5a6068 7c838b"),
    "plastic": _ramp("101113 1b1c1f 28292d 383a3f 4b4e54"),
    "card":    _ramp("221b16 3a2e25 54443a 6e5b4b 8a7562"),
    "shell":   _ramp("2a2c30 4c4f55 72767c 9a9ea3 c3c6c9"),
    "rubber":  _ramp("0f1011 1a1b1d 26282b 35383c 474b50"),
    "glow":    _ramp("12393d 1f6a70 3aa3a8 7fdad8 c4f4f0"),   # the single accent colour
    "warn":    _ramp("3a2a14 6a4a1c 9a6c26 c49434 e0b858"),   # hazard paint, used sparingly
    # muted colour accents for variety (faded, desaturated so the room stays grey overall)
    "redp":    _ramp("2a1414 4a2222 6a3232 8a4a46 a8665e"),   # faded red plastic
    "tarp":    _ramp("161e2a 223044 32465e 4a6078 6a7e94"),   # dull blue tarp
    "oil":     _ramp("0c0c0e 141518 1c1e22 262a30 323844"),   # oily puddle
    "spark":   _ramp("6a5a20 c8a838 f0d860 fff4b0 ffffff"),   # spark / hot light (animation only)
}
ACCENT = "glow"


class Pix:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[None] * w for _ in range(h)]          # (material, step) or None

    def put(self, x, y, mat, step):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = (mat, max(0, min(step, len(RAMPS[mat]) - 1)))

    def rect(self, x0, y0, x1, y1, mat, step):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, mat, step)

    def hline(self, x0, x1, y, mat, step):
        self.rect(x0, y, x1, y, mat, step)

    def vline(self, x, y0, y1, mat, step):
        self.rect(x, y0, x, y1, mat, step)

    def ellipse(self, cx, cy, rx, ry, mat, step):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                    self.put(x, y, mat, step)

    def paste(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                if other.px[y][x] is not None:
                    m, s = other.px[y][x]
                    self.put(ox + x, oy + y, m, s)

    def outline(self):
        """One-pixel sel-out ring around the whole silhouette: each new pixel takes the
        darkest step of the material it borders."""
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is not None:
                    continue
                for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h and self.px[ny][nx] is not None:
                        add.append((x, y, self.px[ny][nx][0]))
                        break
        for x, y, m in add:
            self.put(x, y, m, 0)

    def bbox_crop(self, pad=0):
        ys = [y for y in range(self.h) if any(self.px[y])]
        xs = [x for x in range(self.w) if any(self.px[y][x] for y in range(self.h))]
        out = Pix(max(xs) - min(xs) + 1 + 2 * pad, max(ys) - min(ys) + 1 + 2 * pad)
        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                if self.px[y][x] is not None:
                    out.px[y - min(ys) + pad][x - min(xs) + pad] = self.px[y][x]
        return out

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is not None:
                    m, s = self.px[y][x]
                    im.putpixel((x, y), RAMPS[m][s] + (255,))
        return im


def box(p, x, y, w, d, h, mat="steel", front=2, top=3):
    """Axis-aligned box whose FRONT-BOTTOM-LEFT corner is (x, y).
    Top face depth d (rows above the front face), front face height h.
    Light comes from the upper left: top face is light, a bright rim on the
    top/front edge, the right column one step darker. No per-part outline."""
    y_front_top = y - h + 1
    p.rect(x, y_front_top - d, x + w - 1, y_front_top - 1, mat, top)          # top face
    p.rect(x, y_front_top, x + w - 1, y, mat, front)                           # front face
    p.hline(x, x + w - 1, y_front_top, mat, front + 1)                         # lit rim
    p.vline(x + w - 1, y_front_top - d, y, mat, front - 1)                     # shade side
    p.hline(x, x + w - 1, y_front_top - d, mat, top + 1)                       # back edge catch-light
    return (x, y_front_top - d, x + w - 1, y)                                  # bbox
