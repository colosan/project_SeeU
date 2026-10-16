"""Pixel-art rotation for code-drawn parts (RotSprite style), so junk can tilt, lie and tumble
without turning into blurry or jaggy noise.

  from rot import rotate, quarter
  out, (ox, oy) = rotate(part, 23, pivot=(x, y))   # degrees, clockwise on screen; pivot = continuous point

Method (works on the (material, step) grid of a Pix, never on RGB, so every output pixel is still a
ramp colour and the per-material outline / emission rules keep working):
  1. pad the grid by one empty pixel and upscale it 8x with Scale2x (EPX) three times - Scale2x only
     ever copies neighbours, so diagonal edges get smoothed without inventing colours;
  2. for every output pixel, map its centre back through the inverse rotation (nearest neighbour)
     into the 8x grid;
  3. that sample is the output pixel (= sampling the rotated 8x image back down 8x).
Quarter turns (0/90/180/270) are done exactly instead (`quarter`).

Rules (docs/ART_PIPELINE.md "기울이기"): rotate parts in the picture plane only, around the corner they
rest on; never mirror (the baked upper-left light would flip); never rotate final images in Godot or
with a smooth filter. Boxy things lying on a side get their own "lying" drawing instead of a 90 deg turn
(a turned box would show its top face as a side face - not front-on 3/4).
"""
import math

from pix import Pix


def _pad(g, n=1):
    w = len(g[0]) + 2 * n
    out = [[None] * w for _ in range(n)]
    out += [[None] * n + list(row) + [None] * n for row in g]
    out += [[None] * w for _ in range(n)]
    return out


def scale2x(g):
    """EPX / Scale2x on a grid of hashable values (None = transparent). Edges count as transparent."""
    h, w = len(g), len(g[0])
    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        row = g[y]
        up = g[y - 1] if y > 0 else [None] * w
        dn = g[y + 1] if y < h - 1 else [None] * w
        o0, o1 = out[2 * y], out[2 * y + 1]
        for x in range(w):
            E = row[x]
            B, H = up[x], dn[x]
            D = row[x - 1] if x > 0 else None
            F = row[x + 1] if x < w - 1 else None
            if B != H and D != F:
                o0[2 * x] = D if D == B else E
                o0[2 * x + 1] = F if B == F else E
                o1[2 * x] = D if D == H else E
                o1[2 * x + 1] = F if H == F else E
            else:
                o0[2 * x] = o0[2 * x + 1] = o1[2 * x] = o1[2 * x + 1] = E
    return out


def _bbox(g):
    pts = [(x, y) for y, row in enumerate(g) for x, v in enumerate(row) if v is not None]
    if not pts:
        return None
    return (min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))


def rotate(p, deg, pivot):
    """Rotate Pix p by deg (clockwise on screen) around the continuous point pivot=(px, py) of p's frame.
    Returns (Pix, (ox, oy)): the rotated part and where its (0, 0) sits in p's frame (integers), so
    pasting it at (ox + dx, oy + dy) moves the pivot by exactly (dx, dy)."""
    a = deg % 360
    if a in (0, 90, 180, 270):
        return quarter(p, int(a), pivot)
    bb = _bbox(p.px)
    if bb is None:
        return Pix(1, 1), (0, 0)
    x0, y0, x1, y1 = bb
    g = [row[x0:x1 + 1] for row in p.px[y0:y1 + 1]]
    g = _pad(g)
    for _ in range(3):
        g = scale2x(g)
    S = 8
    gh, gw = len(g), len(g[0])
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    px, py = pivot
    # rotated corners of the content box -> output range (in p's frame)
    xs, ys = [], []
    for cx, cy in ((x0, y0), (x1 + 1, y0), (x0, y1 + 1), (x1 + 1, y1 + 1)):
        dx, dy = cx - px, cy - py
        xs.append(px + dx * c - dy * s)
        ys.append(py + dx * s + dy * c)
    ox, oy = math.floor(min(xs)) - 1, math.floor(min(ys)) - 1
    ow, oh = math.ceil(max(xs)) + 1 - ox, math.ceil(max(ys)) + 1 - oy
    out = Pix(ow, oh)
    for v in range(oh):
        for u in range(ow):
            X, Y = ox + u + 0.5 - px, oy + v + 0.5 - py
            sx = px + X * c + Y * s                       # inverse rotation
            sy = py - X * s + Y * c
            gx = math.floor((sx - x0 + 1) * S)            # +1: the pad
            gy = math.floor((sy - y0 + 1) * S)
            if 0 <= gx < gw and 0 <= gy < gh:
                val = g[gy][gx]
                if val is not None:
                    out.px[v][u] = val
    return out, (ox, oy)


def quarter(p, deg, pivot):
    """Exact rotation by 0/90/180/270 degrees (clockwise) around pivot; same return as rotate()."""
    bb = _bbox(p.px)
    if bb is None:
        return Pix(1, 1), (0, 0)
    x0, y0, x1, y1 = bb
    px, py = pivot
    pts = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = p.px[y][x]
            if v is None:
                continue
            dx, dy = x + 0.5 - px, y + 0.5 - py
            if deg == 0:
                nx, ny = dx, dy
            elif deg == 90:
                nx, ny = -dy, dx
            elif deg == 180:
                nx, ny = -dx, -dy
            else:
                nx, ny = dy, -dx
            pts.append((math.floor(px + nx), math.floor(py + ny), v))
    ox, oy = min(x for x, _, _ in pts), min(y for _, y, _ in pts)
    out = Pix(max(x for x, _, _ in pts) - ox + 1, max(y for _, y, _ in pts) - oy + 1)
    for x, y, v in pts:
        out.px[y - oy][x - ox] = v
    return out, (ox, oy)
