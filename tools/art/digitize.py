"""Digital tells for code-drawn props: this world is INSIDE THE INTERNET, so even ordinary junk
shows it is made of data (docs/DESIGN.md "세계 컨셉: 인터넷 속 가상 세계").

All helpers work on Pix canvases ((material, step) per pixel, tools/art/pix.py) at native res.

  * DPix            Pix that remembers which part drew each pixel (p.tag) and keeps a list of
                    post-outline effects (p.post), so a far part's wireframe or dissolve only
                    touches the pixels of that part that are still visible.
  * derez()         de-rez / dissolve: a corner of the silhouette breaks into 2x2 / 1x1 blocks,
                    a few drift just above it (deleted data decaying). 1-2 spots per object.
  * checker()       missing-texture patch: corrupt-magenta / darkest-steel checker on a face.
  * wireframe()     part of an object drawn as dim mesh edges only (unrendered mesh).
  * contour_spots() picks purposeful de-rez spots on a pile's top contour.

Extra material ramps are registered into pix.RAMPS at import (runtime only - pix.py is not
edited). They should move into pix.py once the art is accepted:
  corrupt  muted magenta, the ONLY second accent: glitches / missing textures, used sparingly
  paper    warm off-white: documents, labels, file icons, cursors
  icon     muted manila: folder icons
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pix import Pix, RAMPS, _ramp  # noqa: E402

EXTRA_RAMPS = {
    "corrupt": _ramp("1e1320 381c35 54284c 723866 8e5080"),
    "paper":   _ramp("27241f 45413a 6a6559 928c7c b9b29f"),
    "icon":    _ramp("2a2416 4b4128 6f6040 94824f b5a265"),
}
for _k, _v in EXTRA_RAMPS.items():
    RAMPS.setdefault(_k, _v)

# Every random choice that gen_junk does NOT make (which tell, which screen, substitutions) comes
# from this detail rng, so the shared rng sequence - and with it every pile's composition - stays
# exactly gen_junk's. Generators reseed it per image.
DETAIL = random.Random(0)


def Q():
    return DETAIL


def reseed(seed):
    DETAIL.seed(f"detail-{seed}")


# How much corrupt magenta a single generated image may use (number of checker patches /
# corrupt tells). Piles reset it; parts consume it. Keeps the second accent rare.
BUDGET = {"corrupt": 1}


def spend(kind="corrupt"):
    if BUDGET.get(kind, 0) > 0:
        BUDGET[kind] -= 1
        return True
    return False


class DPix(Pix):
    """Pix with per-pixel owner tags and post-outline effects."""

    def __init__(self, w, h):
        super().__init__(w, h)
        self.own = [[None] * w for _ in range(h)]
        self.tag = None
        self.post = []          # callables fn(p) run after the outline, in order
        self._n = 0

    def new_tag(self, name="part"):
        self._n += 1
        self.tag = f"{name}#{self._n}"
        return self.tag

    def put(self, x, y, mat, step):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = (mat, max(0, min(step, len(RAMPS[mat]) - 1)))
            self.own[y][x] = self.tag

    def clear(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = None
            self.own[y][x] = None

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def finish(self, crop=True, outline=True):
        """Outline once, then run the post effects (dissolves, wireframes, floating bits).
        Drifting bits never leave the bounding box the object had before the effects, and the
        crop is that box - so a digital version has exactly its gen_junk twin's size and base line.
        outline=False for walkable floor decals (they get no sel-out ring, like gen_junk's)."""
        self.tag = "outline"
        if outline:
            self.outline()
        self.box0 = self._bbox()
        for fn in self.post:
            self.tag = "post"
            fn(self)
        self.post = []
        if not crop:
            return self
        x0, y0, x1, y1 = self.box0
        out = Pix(x1 - x0 + 1, y1 - y0 + 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                out.px[y - y0][x - x0] = self.px[y][x]
        return out

    def _bbox(self):
        ys = [y for y in range(self.h) if any(self.px[y])]
        xs = [x for x in range(self.w) if any(self.px[y][x] for y in range(self.h))]
        return (min(xs), min(ys), max(xs), max(ys))


def float_put(p, x, y, mat, step):
    """Put a pixel only where nothing is drawn (things drifting in the air are hidden behind solids)
    and only inside the object's pre-effect bounding box (p.box0) when there is one."""
    b = getattr(p, "box0", None)
    if b and not (b[0] <= x <= b[2] and b[1] <= y <= b[3]):
        return
    if 0 <= x < p.w and 0 <= y < p.h and p.px[y][x] is None:
        p.put(x, y, mat, step)


def float_block(p, x, y, size, mat, step):
    """A 2x2 (or 1x1) floating data block: lit top-left, one darker pixel bottom-right."""
    for dy in range(size):
        for dx in range(size):
            s = step - 1 if (size == 2 and dx == 1 and dy == 1) else step
            float_put(p, x + dx, y + dy, mat, s)


# ---------------------------------------------------------------- de-rez / dissolve

def derez(p, ax, ay, r, size=6, drift=(1, -1), n_bits=4, data=True):
    """Dissolve the silhouette around edge pixel (ax, ay): 2x2 cells are knocked out (most near
    the edge, fewer deeper in), the exposed rim gets the material's darkest step (inner sel-out),
    and a short trail of blocks drifts away in `drift` direction, shrinking 2x2 -> 1x1 and turning
    into dim data (glow) as it goes. Run AFTER the outline (it is a post effect)."""
    half = size // 2
    x0 = ax - half
    x0 -= x0 % 2
    carved, mats = [], {}
    cols = size // 2
    for cy in range(size // 2):
        for cx in range(cols):
            dist = cy + abs(cx - (cols - 1) / 2) * 0.8
            chance = 1.0 if dist < 1 else 0.6 if dist < 2 else 0.25 if dist < 2.8 else 0.0
            if r.random() >= chance:
                continue
            for dy in range(2):
                for dx in range(2):
                    x, y = x0 + cx * 2 + dx, ay + cy * 2 + dy
                    v = p.get(x, y)
                    if v is not None:
                        mats[v[0]] = mats.get(v[0], 0) + 1
                        carved.append((x, y))
    if not carved:
        return
    for x, y in carved:
        p.clear(x, y)
    holes = set(carved)
    rim = set()
    for x, y in holes:
        for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
            if p.get(x + dx, y + dy) is not None:
                rim.add((x + dx, y + dy))
    for x, y in rim:
        m, s = p.px[y][x]
        p.put(x, y, m, 0 if s > 1 else s)
    mat = max(mats, key=mats.get)
    if mat in ("glow", "spark", "corrupt"):
        mat = "steel"
    top_y = min(y for _x, y in carved)
    cx = sum(x for x, _y in carved) / len(carved)
    # trail: big blocks close to the hole, small dim data bits farther away
    x, y = cx + drift[0] * 1, top_y - 3
    steps = [(2, mat, 3), (2, mat, 2), (1, "glow", 2), (1, "glow", 1), (1, mat, 2)][:n_bits]
    if not data:
        steps = [(2, mat, 3), (2, mat, 2), (1, mat, 3), (1, mat, 2)][:n_bits]
    for i, (sz, m, s) in enumerate(steps):
        jitter = (1 if i % 2 else -1) * r.choice([0, 1])
        float_block(p, int(round(x)) + jitter, int(round(y)), sz, m, s)
        x += drift[0] * (2 + i)
        y += drift[1] * (2 + i * 0.7)


def contour_spots(p, n, r, min_lift=6, headroom=7):
    """n de-rez spots on the top contour of a pile: in each of n slices take the highest column
    that still has `headroom` px of air below the pile's overall top (so the drifting trail is
    visible inside the sprite), never on low flat rims. Returns [(x, y_top)]."""
    tops = []
    for x in range(p.w):
        ys = [y for y in range(p.h) if p.px[y][x] is not None]
        tops.append(min(ys) if ys else None)
    valid = [t for t in tops if t is not None]
    if not valid:
        return []
    floor = max(valid)
    spots = []
    lo = next(i for i, t in enumerate(tops) if t is not None)
    hi = len(tops) - 1 - next(i for i, t in enumerate(reversed(tops)) if t is not None)
    span = (hi - lo) / n
    for k in range(n):
        a, b = int(lo + span * k + span * 0.15), int(lo + span * (k + 1) - span * 0.15)
        cand = [(tops[x], x) for x in range(a, b + 1) if tops[x] is not None and floor - tops[x] >= min_lift
                and tops[x] - min(valid) >= headroom]
        if not cand:
            continue
        cand.sort()
        y, x = cand[min(len(cand) - 1, r.randint(0, 2))]
        spots.append((x, y))
    return spots


# ---------------------------------------------------------------- missing texture

def checker(p, x0, y0, x1, y1, cell=2, a=("corrupt", 3), b=("steel", 0), only_drawn=True):
    """Missing-texture checker over a rect (only over pixels already drawn when only_drawn)."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if only_drawn and p.get(x, y) is None:
                continue
            c = a if ((x - x0) // cell + (y - y0) // cell) % 2 == 0 else b
            p.put(x, y, *c)


# ---------------------------------------------------------------- wireframe

def wireframe(p, rect, tag=None, grid=5, line=("glow", 1), vertex=("glow", 2), diag=True):
    """Turn the pixels inside rect (optionally only those drawn by part `tag`, plus the outline
    pixels around them) into a see-through triangulated mesh: region border + grid lines (+ one
    diagonal per quad) stay as dim edges, everything else is cleared. Run AFTER the outline."""
    x0, y0, x1, y1 = rect

    def mine(x, y):
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return False
        if p.get(x, y) is None:
            return False
        if tag is None:
            return True
        o = p.own[y][x]
        if o == tag:
            return True
        if o == "outline":
            return any(0 <= x + dx < p.w and 0 <= y + dy < p.h and p.own[y + dy][x + dx] == tag
                       for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)))
        return False

    region = {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if mine(x, y)}
    keep, drop = [], []
    for x, y in region:
        border = any((x + dx, y + dy) not in region for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)))
        gx, gy = (x - x0) % grid == 0, (y - y0) % grid == 0
        dg = diag and ((x - x0) - (y - y0)) % grid == 0
        if border or gx or gy or dg:
            keep.append((x, y, gx and gy))
        else:
            drop.append((x, y))
    for x, y in drop:
        p.clear(x, y)
    for x, y, vtx in keep:
        p.put(x, y, *(vertex if vtx else line))


# ---------------------------------------------------------------- small drawing helpers

def line(p, x0, y0, x1, y1, mat, step):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for t in range(n + 1):
        p.put(round(x0 + (x1 - x0) * t / n), round(y0 + (y1 - y0) * t / n), mat, step)
