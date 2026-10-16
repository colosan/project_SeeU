"""Digital (internet-world) versions of the basement junk + new digital-native props.

The basement is the RECYCLE BIN / garbage-collection zone of a world inside the internet
(docs/DESIGN.md, docs/WORLD_PROPS.md). The parts reuse tools/art/gen_junk.py's shapes, but tell
they are data: archives instead of crates, bit buckets instead of drums, error screens, deprecated
avatars, de-rezzing corners, a missing texture.

Calm rules (docs/ART_PIPELINE.md 9-10, CLAUDE.md rule 6) for everything placed in the room:
  * glow only where the story needs it: heaps, stacks and dumped singles are drawn with
    `calm(lit=False, labels=False)` - dead dark screens, LEDs off, no stencils; tools/art/gen_emission.py
    lets only STORY_EMITTERS glow;
  * fewer, bigger things: calm heaps (dheap) have about a quarter of gen_junk's parts plus dim
    silhouettes of swallowed junk; labels / checker / de-rez are a small room-wide budget;
  * nothing stands tidy: parts tilt, lie (LIE drawings), fall or flip (rot.py RotSprite rotation around
    the corner they rest on) and sink into the heap (bury); stacks lean (dstack_lean).

  python tools/art/gen_digital.py                      # write any missing files
  python tools/art/gen_digital.py --out=build/art_preview/digital
  python tools/art/gen_digital.py --force dg_c_main.png dg_a_tv.png
  python tools/art/gen_digital.py --preview=DIR        # only write preview sheets (3x) to DIR

Never overwrites unless the file name is listed after --force. Never deletes.
Output names mirror gen_junk with a `dg_` prefix (dg_c_main.png <-> c_main.png; same seeds and
footprint, so the room layout can swap them); new props are dg_s_* (single), dg_f_* (walkable floor decal),
dg_a_* (animated strip, frames side by side - see ANIM_INFO for frames/fps), memes contain `meme`.
Size reference: SeeU is ~37 native px tall (1.65 m) -> 1 px ~ 4.5 cm.
"""
import math
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import digitize as D  # noqa: E402  (registers the corrupt / paper / icon ramps)
import gen_junk as J  # noqa: E402
import pixfont as F  # noqa: E402
from digitize import DPix, Q, checker, derez, float_put, line, spend, wireframe  # noqa: E402
import rot  # noqa: E402
from pix import Pix, box  # noqa: E402

OUT_DEFAULT = "assets/env/basement/digital"


def _rr(r):
    """Child rng for post effects (keeps the main sequence deterministic)."""
    return random.Random(r.random())


# =============================================================== screens (monochrome CRT, glow ramp)

SPIN = [(-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1)]


def screen(p, x0, y0, x1, y1, kind, k=0):
    """Screen content inside the rect: err (dialog with title bar, '!' and OK), spin (loading
    ring, phase k), sad (crashed face), bar (progress stuck at 99%), 404 / ERR (text), cursor,
    dead (no signal), glitch (one corrupt tear line)."""
    w, h = x1 - x0 + 1, y1 - y0 + 1
    cx, cy = x0 + (w - 1) // 2, y0 + (h - 1) // 2
    p.rect(x0, y0, x1, y1, "glow", 1)
    if kind == "dead":
        p.hline(x0 + 1, x1 - 1, y0 + 1, "glow", 2)
        p.put(x0 + 2, y1 - 2, "glow", 3); p.put(x0 + 3, y1 - 3, "glow", 3)
    elif kind == "err":
        p.hline(x0, x1, y0, "glow", 3)                                   # title bar
        p.put(x1 - 1, y0, "glow", 1)                                     # close box
        p.vline(x0 + 1, y0 + 2, y1 - 2, "glow", 4); p.put(x0 + 1, y1, "glow", 4)   # "!"
        p.hline(x0 + 3, x1 - 1, y0 + 2, "glow", 2)
        if h >= 7:
            p.hline(x0 + 3, x1 - 2, y0 + 4, "glow", 2)
        p.hline(x1 - 3, x1 - 1, y1, "glow", 3)                           # OK button
    elif kind == "spin":
        for i, (dx, dy) in enumerate(SPIN):
            age = (k - i) % 8
            p.put(cx + dx, cy + dy, "glow", 4 if age == 0 else 3 if age == 1 else 2)
    elif kind == "sad":
        p.put(cx - 2, cy - 1, "glow", 4); p.put(cx + 2, cy - 1, "glow", 4)
        for dx, dy in ((-2, 2), (-1, 1), (0, 1), (1, 1), (2, 2)):
            p.put(cx + dx, cy + dy, "glow", 3)
    elif kind == "bar":
        p.hline(x0 + 1, x1 - 1, cy - 1, "glow", 2); p.hline(x0 + 1, x1 - 1, cy + 1, "glow", 2)
        p.put(x0 + 1, cy, "glow", 2); p.put(x1 - 1, cy, "glow", 2)
        p.hline(x0 + 2, x1 - 3, cy, "glow", 4)                          # never reaches the end
    elif kind in ("404", "ERR"):
        tw = F.text_width(kind)
        F.text(p, x0 + (w - tw) // 2, y0 + (h - 5) // 2, kind, "glow", 4)
    elif kind == "cursor":
        for i, n in enumerate((1, 2, 3, 4, 2, 1)):
            p.hline(cx - 1, cx - 2 + n, cy - 3 + i, "glow", 4)
    elif kind == "glitch":
        p.hline(x0 + 1, x1 - 1, y0 + 1, "glow", 2)
        p.hline(x0, x1, cy, "corrupt", 3); p.hline(x0 + 2, x1, cy + 1, "glow", 3)


# Calm-glow switches (docs/ART_PIPELINE.md "조용한 빛"). The glow ramp means "this is ON", so only story
# sources may use it. Heaps, stacks and dumped singles turn both off: their screens are dead dark glass,
# their LEDs are off, and they carry no stencils/labels (a few story labels are placed on purpose).
CALM = {"lit": True, "labels": True}


class calm:
    """with calm(lit=False, labels=False): ... - parts drawn inside are dead and unlabelled."""

    def __init__(self, lit=False, labels=False):
        self.new = {"lit": lit, "labels": labels}

    def __enter__(self):
        self.old = dict(CALM)
        CALM.update(self.new)

    def __exit__(self, *a):
        CALM.update(self.old)


def dead_glass(p, x0, y0, x1, y1):
    """A switched-off screen: dark glass with one soft diagonal reflection (upper-left light). No glow."""
    p.rect(x0, y0, x1, y1, "plastic", 0)
    p.hline(x0, x1, y0, "plastic", 1)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    for k in range(min(w, h) // 2):
        p.put(x0 + 1 + k, y1 - 1 - k - (h // 3), "plastic", 2)
    p.put(x0 + 1, y0 + 1, "steel", 2)


def dim_screen(p, x0, y0, x1, y1, cap):
    """Caps every glow step inside the rect (screen brightness for flicker frames)."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = p.get(x, y)
            if v and v[0] == "glow":
                p.put(x, y, "glow", min(v[1], cap) if cap > 0 else 0)


# =============================================================== reinterpreted gen_junk parts
# Same signatures and silhouettes as gen_junk: fn(p, x, y, r) -> (top-face bbox, width).

def archive(p, x, y, r, size=None):
    """crate -> compressed archive: zipper over the lid and down the front, compression straps.
    rng: same calls as gen_junk.crate (size, label roll)."""
    w, d, h = r.choice([(14, 5, 11), (12, 4, 9), (16, 5, 10)])
    if size:
        w, d, h = size
    tagged = r.random() < 0.5
    bx = box(p, x, y, w, d, h, "card", front=2, top=3)
    ft = y - h + 1
    zx = x + w // 2 - 1
    hi, lo = (3, 1) if CALM["labels"] else (2, 1)                        # calm: a quieter zipper
    for yy in range(ft - d + 1, y):
        a = yy % 2 == 0
        p.put(zx, yy, "steel", hi if a else lo)
        p.put(zx + 1, yy, "steel", lo if a else hi)
    p.rect(zx, ft, zx + 1, ft + 1, "steel", 4 if CALM["labels"] else 3)  # slider
    p.put(zx, ft + 2, "steel", 2); p.put(zx, ft + 3, "steel", 3)        # pull tab
    sy = y - h // 2 + 1
    p.hline(x + 1, zx - 1, sy, "card", 1); p.hline(zx + 2, x + w - 2, sy, "card", 1)
    if tagged and Q().random() < 0.7 and CALM["labels"]:
        p.rect(x + 2, ft + 2, x + 4, ft + 3, "paper", 4)                 # file tag
    return bx, w


def driver_amp(p, x, y, r, size=None):
    """amp -> deprecated audio driver: a WAV sticker or a flat-lined waveform display."""
    w, d, h = size or (14, 5, 18)
    q = Q()
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    if not CALM["lit"] and not CALM["labels"]:                           # dumped: plain grille, knobs, no light
        p.hline(x + 2, x + w - 3, y - h + 3, "steel", 2)
        p.put(x + 3, y - h + 3, "steel", 3); p.put(x + 6, y - h + 3, "steel", 3)
        cx, cy, rr = x + w // 2 - 1, y - h // 3, (w - 5) / 2
    elif q.random() < 0.5:
        F.label(p, x, y - h + 2, "WAV", plate=("paper", 3), ink=("paper", 1))
        cx, cy, rr = x + w // 2 - 1, y - 5, 3.6
    else:
        p.rect(x + 2, y - h + 3, x + w - 3, y - h + 5, "glow", 1)        # scope strip
        p.hline(x + 2, x + w - 3, y - h + 4, "glow", 2)                  # flat line
        bx_ = x + 4 + q.randint(0, 4)
        p.put(bx_, y - h + 3, "glow", 3); p.put(bx_ + 1, y - h + 5, "glow", 3)   # one last blip
        cx, cy, rr = x + w // 2 - 1, y - 6, 4.5
    p.ellipse(cx, cy, rr, rr, "steel", 1)
    p.ellipse(cx, cy, rr - 1.3, rr - 1.3, "rubber", 2)
    p.ellipse(cx, cy, 1, 1, "rubber", 0)
    p.put(cx - 2, cy - 2, "steel", 3)
    return bx, w


def driver_speaker(p, x, y, r):
    """speaker -> deprecated audio driver: a printed sound-wave decal, the top corner dissolving."""
    w, d, h = 10, 4, 22
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    for cy, rr in ((y - 15, 3.2), (y - 6, 3.8)):
        p.ellipse(x + 4, cy, rr, rr, "steel", 1)
        p.ellipse(x + 4, cy, rr - 1.2, rr - 1.2, "rubber", 2)
    for i, dy in enumerate((0, -1, -1, 0, 1, 1, 0)):                    # printed sine decal
        p.put(x + 1 + i, y - 11 + dy, "shell", 4 if CALM["labels"] else 1)
    if spend("derez"):
        rr_ = _rr(Q())
        p.post.append(lambda q: derez(q, x + 7, y - h - d, rr_, size=4, drift=(1, -1), n_bits=3))
    return bx, w


def legacy_rack(p, x, y, r, size=None):
    """rack -> legacy server: a half-pulled drive caddy, a dangling network cable, red fault LED.
    rng: same calls as gen_junk.rack (height, one LED roll per slot)."""
    w, d, h = 12, 4, r.choice([24, 27])
    if size:
        w, d, h = size
    q = Q()
    bx = box(p, x, y, w, d, h, "steel", front=1, top=3)
    slots = list(range(y - h + 3, y - 1, 3))
    pulled = q.choice(slots[1:-1]) if q.random() < 0.5 else None
    for yy in slots:
        led = r.random() < 0.35
        if yy == pulled:
            p.hline(x + 1, x + w - 2, yy - 1, "steel", 4)
            p.hline(x + 1, x + w - 2, yy, "plastic", 2)
            continue
        p.hline(x + 2, x + w - 3, yy, "plastic", 1)
        if led:
            red, bright = q.random() < 0.25, q.random() < 0.5
            if CALM["lit"]:
                p.put(x + w - 4, yy, "redp" if red else "glow", 4 if bright else 3)
            else:
                p.put(x + w - 4, yy, "plastic", 2)                       # dead LED
    if q.random() < 0.6:                                                  # network cable hanging out of a port
        py = q.choice(slots[:-2])
        p.put(x + 3, py, "shell", 3)
        for k, yy in enumerate(range(py + 1, y)):
            p.put(x + 3 - (1 if (k // 3) % 2 else 0), yy, "rubber", 1)
    return bx, w


def err_tv(p, x, y, r, kind=None, size=None):
    """tv -> error screen (dialog, loading ring, crash face, stuck bar or no signal)."""
    w, d, h = size or (13, 6, 11)
    q = Q()
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    kind = kind or q.choice(["err", "err", "spin", "sad", "bar", "dead"])
    k = q.randint(0, 7)
    if CALM["lit"]:
        screen(p, x + 2, y - h + 3, x + w - 4, y - 2, kind, k)
    else:
        dead_glass(p, x + 2, y - h + 3, x + w - 4, y - 2)
    return bx, w


def err_monitor(p, x, y, r, kind=None):
    """monitor -> 404 / ERR / loading / crash screen. rng: same call as gen_junk.monitor."""
    w, d, h = 14, 3, 10
    q = Q()
    r.choice([1, 2])
    bx = box(p, x, y - 3, w, d, h, "plastic", front=1, top=3)
    kind = kind or q.choice(["404", "err", "spin", "sad", "bar", "ERR", "cursor", "dead"])
    k = q.randint(0, 7)
    if CALM["lit"]:
        screen(p, x + 1, y - h - 1, x + w - 3, y - 5, kind, k)
    else:
        dead_glass(p, x + 1, y - h - 1, x + w - 3, y - 5)
    p.rect(x + 5, y - 2, x + 8, y, "plastic", 2)
    return (x, bx[1], x + w - 1, y), w


def avatar_head(p, x, y, r):
    """robot head -> deprecated avatar head; half of it is unrendered wireframe."""
    p.ellipse(x + 5, y - 5, 5.5, 5, "shell", 3)
    p.ellipse(x + 4, y - 7, 2.5, 1.5, "shell", 4)
    p.rect(x + 1, y - 5, x + 9, y - 3, "plastic", 1)
    if r.random() < 0.5 and CALM["lit"]:
        p.put(x + 3, y - 4, "glow", 4)
    if spend("wire"):
        tag = p.tag
        p.post.append(lambda q, tag=tag: wireframe(q, (x + 6, y - 11, x + 12, y + 1), tag=tag))
    return (x, y - 10, x + 11, y), 11


def avatar_torso(p, x, y, r):
    """robot torso -> body of a discontinued voice model: sound-wave chest emblem; wireframe arm,
    missing-texture chest or a dissolving shoulder."""
    w, d, h = 14, 4, 12
    bx = box(p, x, y, w, d, h, "shell", front=2, top=3)
    p.rect(x + 3, y - 8, x + 10, y - 4, "shell", 1)
    for i, dy in enumerate((0, -1, -1, 0, 1, 1, 0, -1)):
        p.put(x + 3 + i, y - 6 + dy, "shell", 4 if CALM["labels"] else 3)
    p.rect(x - 3, y - 9, x - 1, y - 3, "shell", 2); p.rect(x + w, y - 9, x + w + 2, y - 3, "shell", 1)
    t = Q().random()
    tag = p.tag
    if t < 0.45 and spend("wire"):
        p.post.append(lambda q, tag=tag: wireframe(q, (x + 9, y - h - d, x + w + 3, y + 1), tag=tag))
    elif t < 0.7 and spend("corrupt"):
        checker(p, x + 3, y - 8, x + 10, y - 4)
    elif spend("derez"):
        rr = _rr(Q())
        p.post.append(lambda q: derez(q, x + 2, y - h - d, rr, size=4, drift=(-1, -1), n_bits=3))
    return bx, w + 3


def disc_stack(p, x, y, r):
    """tire -> spindle of scratched optical discs (old install media). Same round footprint.
    rng: same call as gen_junk.tire (stacked roll)."""
    w = 14
    hgt = 8 if r.random() < 0.5 else 4
    top = y - hgt
    for yy in range(top, y + 1):                                          # disc edges
        p.hline(x, x + w - 1, yy, "steel", 3 if (y - yy) % 2 == 0 else 1)
        p.put(x + w - 1, yy, "steel", 1)
    p.ellipse(x + 7, top, 7, 4, "steel", 3)
    p.ellipse(x + 7, top - 0.3, 5.2, 2.6, "steel", 4)
    p.ellipse(x + 7, top, 4.2, 2.0, "steel", 3)
    p.ellipse(x + 7, top, 2.2, 1.2, "steel", 2)                          # hub
    p.put(x + 3, top - 2, "tarp", 4); p.put(x + 4, top - 2, "glow" if CALM["lit"] else "tarp", 1)   # muted sheen
    line(p, x + 9, top + 2, x + 11, top + 1, "steel", 2)                 # scratch
    p.vline(x + 7, top - 3, top, "steel", 3)                              # spindle
    p.put(x + 7, top - 4, "steel", 4)
    return (x, top - 4, x + w - 1, y), w


def pipeline(p, x, y, r):
    """pipes -> data pipeline: a sight glass with a packet of light, glowing open end.
    rng: same calls as gen_junk.pipes (count, length)."""
    n, w = r.choice([2, 3]), r.choice([28, 34])
    q = Q()
    lit = q.randint(0, n - 1)
    for i in range(n):
        yy = y - i * 5
        x0, x1 = x + i * 2, x + w - 1 - i
        p.rect(x0, yy - 4, x1, yy, "steel", 2)
        p.hline(x0, x1, yy - 3, "steel", 3)
        for fx in range(x0 + 8, x1 - 3, 11):                              # flanges
            p.vline(fx, yy - 4, yy, "steel", 3); p.vline(fx + 1, yy - 4, yy, "steel", 1)
        gx = x0 + 3 + q.randint(0, 3)
        k = q.randint(0, 3)
        if i == lit and CALM["lit"]:
            p.rect(gx, yy - 2, gx + 4, yy - 1, "glow", 1)                 # sight glass
            p.put(gx + k, yy - 2, "glow", 4); p.put(gx + k + 1, yy - 2, "glow", 3)   # a packet passing
        p.ellipse(x0, yy - 2, 2, 2.5, "steel", 1)
        if CALM["lit"]:
            p.put(x0, yy - 2, "glow", 2 if i == 0 else 1)                 # light inside the open end
        else:
            p.put(x0, yy - 2, "plastic", 0)                               # dark open end
    return (x, y - n * 5, x + w, y), w


def bit_bucket(p, x, y, r):
    """barrel -> the bit bucket: open drum where deleted bits go, "01" stencil, bits falling in.
    rng: same call as gen_junk.barrel (label roll)."""
    w, h = 11, 14
    r.random()
    p.rect(x, y - h + 3, x + w - 1, y, "steel", 2)
    p.vline(x + w - 1, y - h + 3, y, "steel", 1); p.vline(x + 1, y - h + 4, y - 1, "steel", 3)
    p.hline(x, x + w - 1, y - 1, "steel", 1); p.hline(x, x + w - 1, y - h + 5, "steel", 1)
    cx = x + w / 2 - 0.5
    p.ellipse(cx, y - h + 2, w / 2, 2.2, "steel", 3)
    p.ellipse(cx, y - h + 2, w / 2 - 1.6, 1.1, "plastic", 0)
    if CALM["lit"]:
        for k, s_ in enumerate((1, 2, 1, 1, 3, 1, 2)):                    # a pool of bits
            p.put(x + 2 + k, y - h + 2 + (k % 2), "glow", s_)
    else:
        p.hline(x + 3, x + 6, y - h + 2, "plastic", 1)                    # dead bits: a dark heap inside
    if CALM["labels"]:
        F.text(p, x + 2, y - h + 7, "01", "paper", 3)
    if CALM["lit"] and spend("bits"):
        bx0 = int(cx)

        def bits(q):
            float_put(q, bx0, y - h - 3, "glow", 3); float_put(q, bx0, y - h - 2, "glow", 3)   # a "1"
            float_put(q, bx0 - 2, y - h - 6, "glow", 2)
            float_put(q, bx0 + 1, y - h - 8, "glow", 1); float_put(q, bx0 + 1, y - h - 9, "glow", 1)
        p.post.append(bits)
    return (x, y - h, x + w - 1, y), w


def leak_tank(p, x, y, r):
    """tank -> memory-leak tank: MEM stencil (or plain hazard band), a crack, glowing data dripping
    into a puddle at its foot. rng: same call as gen_junk.tank (material)."""
    w, h = 16, 20
    mat = r.choice(["steel", "redp"])
    if not CALM["lit"] and Q().random() < 0.7:                           # calm heaps: mostly plain steel
        mat = "steel"
    p.rect(x, y - h + 4, x + w - 1, y, mat, 2)
    p.vline(x + 2, y - h + 5, y - 1, mat, 3); p.vline(x + w - 1, y - h + 4, y, mat, 1)
    p.ellipse(x + w / 2 - 0.5, y - h + 3, w / 2, 3, mat, 3)
    p.rect(x + 6, y - h - 1, x + 9, y - h + 1, "steel", 2)
    stencil = Q().random() < 0.5
    if stencil and CALM["labels"]:
        p.hline(x + 1, x + w - 2, y - 13, "warn", 3)
        F.text(p, x + 3, y - 11, "MEM", "warn", 3)
    else:
        p.rect(x + 3, y - 10, x + 12, y - 7, "warn", 3 if CALM["labels"] else 1)
    cx = x + 11
    for dx, dy in ((0, -5), (1, -4), (0, -3)):
        p.put(cx + dx, y + dy, mat, 0)
    if CALM["lit"]:
        p.put(cx, y - 2, "glow", 2); p.put(cx, y - 1, "glow", 3)
        p.hline(cx - 3, cx + 3, y, "glow", 1); p.hline(cx - 1, cx + 1, y, "glow", 2)
    else:
        p.put(cx, y - 2, "oil", 2); p.put(cx, y - 1, "oil", 2)           # a dried, dark leak stain
    return (x, y - h - 1, x + w - 1, y), w


def stage_chair(p, x, y, r):
    """chair -> abandoned virtual-stage chair: missing-texture seat or a dissolving back rest."""
    bx, w = J.chair(p, x, y, r)
    if not CALM["lit"]:                                                  # dumped: no red accent (a fallen red
        for yy in range(bx[1], bx[3] + 1):                               # chair reads as a glyph in the light)
            for xx in range(bx[0], bx[2] + 1):
                v = p.get(xx, yy)
                if v and v[0] == "redp":
                    p.put(xx, yy, "steel", v[1])
    t = Q().random()
    if t < 0.3 and spend("corrupt"):
        checker(p, x, y - 8, x + 10, y - 6)
    elif spend("derez"):
        rr = _rr(Q())
        p.post.append(lambda q: derez(q, x + 8, y - 15, rr, size=4))
    return bx, w


def stage_ladder(p, x, y, r):
    """ladder -> stage ladder whose top is dissolving and a rung never loaded.
    rng: same call as gen_junk.ladder (height)."""
    h = r.choice([26, 30])
    for lx in (x, x + 7):
        p.vline(lx, y - h, y, "warn", 2); p.vline(lx + 1, y - h, y, "warn", 3)
    rungs = list(range(y - h + 3, y - 1, 5))
    gone = Q().choice(rungs[1:])
    for yy in rungs:
        if yy != gone:
            p.hline(x + 1, x + 7, yy, "warn", 1)
    if spend("derez"):
        rr = _rr(Q())
        p.post.append(lambda q: derez(q, x + 4, y - h - 1, rr, size=6, drift=(1, -1)))
    return (x, y - h, x + 8, y), 9


def stage_truss(p, x, y, r):
    """truss -> virtual-stage truss; its far end dissolves into blocks."""
    bx, w = J.truss(p, x, y, r)
    if spend("derez"):
        rr = _rr(Q())
        p.post.append(lambda q: derez(q, x + 27, y - 7, rr, size=6, drift=(-1, -1)))
    return bx, w


def projector(p, x, y, r):
    """spotlight -> hologram stage projector, lens dead except a pilot glint."""
    w, d, h = 9, 5, 8
    bx = box(p, x, y, w, d, h, "steel", front=2, top=3)
    p.ellipse(x + 4, y - 4, 3, 3, "plastic", 1)
    if CALM["lit"]:
        p.ellipse(x + 4, y - 4, 2, 2, "glow", 1)
        p.put(x + 3, y - 5, "glow", 3)
    else:
        p.ellipse(x + 4, y - 4, 2, 2, "plastic", 0)
        p.put(x + 3, y - 5, "steel", 3)                                    # dead lens, one glint
    return bx, w


def ui_pane(p, x, y, r):
    """plate -> broken pane of a UI window: title bar strip, close box, snapped end."""
    w, h = r.choice([(22, 6), (26, 5)])
    mat = r.choice(["steel", "tarp", "steel"])
    p.rect(x, y - h, x + w - 1, y, mat, 3); p.hline(x, x + w - 1, y, mat, 1)
    p.hline(x, x + w - 1, y - h, mat, 4)
    bar = "tarp" if mat == "steel" else "steel"
    p.hline(x + 1, x + w - 3, y - h + 1, bar, 2)
    p.put(x + w - 5, y - h + 1, "paper", 4)
    for k, cut in enumerate((2, 0, 1, 3, 1, 0, 2)):                      # snapped right end
        yy = y - h + k
        if yy <= y:
            for c in range(cut):
                p.clear(x + w - 1 - c, yy)
    return (x, y - h, x + w - 1, y), w


def synth_dg(p, x, y, r):
    """synth -> keyboard of a sound module: tiny LCD with one waveform pixel lit."""
    bx, w = J.synth(p, x, y, r)
    if CALM["lit"]:
        p.rect(x + w - 7, y - 2, x + w - 3, y - 1, "glow", 1)
        p.put(x + w - 5, y - 2, "glow", 3)
    else:
        p.rect(x + w - 7, y - 2, x + w - 3, y - 1, "plastic", 0)          # LCD off
        p.put(x + w - 3, y - 2, "plastic", 0)                              # (and the gen_junk LED)
    return bx, w


# =============================================================== new digital-native parts (fit in piles)

EXTS = ["TMP", "BAK", "EXE", "WAV", "ZIP", "DLL", "LOG", "OLD"]


def file_doc(p, x, y, r, ext=None, w=13, h=16, dot=False):
    """A file icon the size of a board: dog-eared sheet, text lines, extension at the bottom."""
    top = y - h + 1
    p.rect(x, top, x + w - 1, y, "paper", 3)
    p.hline(x, x + w - 1, top, "paper", 4)
    p.vline(x + w - 1, top, y, "paper", 2)
    p.hline(x, x + w - 1, y, "paper", 2)
    e = 4
    for i in range(e):
        for j in range(e):
            X, Y = x + w - e + i, top + j
            if i > j:
                p.clear(X, Y)
            elif i == j:
                p.put(X, Y, "paper", 1)
            else:
                p.put(X, Y, "paper", 2)
    if ext is None and r.random() < 0.55:
        ext = r.choice(EXTS)
    rows = [top + 2, top + 4, top + 6] if ext else [top + 2, top + 4, top + 6, top + 8, top + 10]
    for k, yy in enumerate(rows):
        x1 = x + w - 3 - (e if k == 0 else 0) - r.randint(0, 3)
        p.hline(x + 2, x1, yy, "paper", 2)
    if ext:
        s = ("." + ext) if dot else ext
        tw = F.text_width(s)
        F.text(p, x + (w - tw) // 2, y - 6, s, "paper", 1)
    return (x, top, x + w - 1, y), w


def folder_icon(p, x, y, r, w=14, h=11, torn=False):
    """A folder icon: back panel with a tab, papers sticking out, lower front flap."""
    top = y - h + 1
    tab = w // 3 + 1
    p.rect(x, top + 2, x + w - 1, y, "icon", 2)
    p.rect(x, top, x + tab - 1, top + 1, "icon", 2); p.put(x + tab, top + 1, "icon", 2)
    p.hline(x, x + tab - 1, top, "icon", 3); p.hline(x + tab, x + w - 1, top + 2, "icon", 3)
    p.rect(x + 2, top + 3, x + w - 4, top + 5, "paper", 4)
    p.rect(x + 4, top + 2, x + w - 2, top + 4, "paper", 3)
    p.hline(x + 5, x + w - 4, top + 3, "paper", 2)
    ft = top + 4 + (h // 6)
    p.rect(x, ft, x + w - 1, y, "icon", 3)
    p.hline(x, x + w - 1, ft, "icon", 4)
    p.vline(x + w - 1, ft, y, "icon", 2)
    p.hline(x, x + w - 1, y, "icon", 2)
    return (x, top, x + w - 1, y), w


def tin(p, x, y, label_mat="tarp"):
    """One spam tin: rounded tin with a lid key, label band with an envelope (mail spam)."""
    w, d, h = 8, 2, 5
    box(p, x, y, w, d, h, "steel", front=2, top=3)
    p.put(x + 1, y - h - 1, "steel", 4); p.put(x + 2, y - h - 1, "steel", 4)    # key on the lid
    p.rect(x, y - 3, x + w - 1, y - 1, label_mat, 2)
    p.vline(x + w - 1, y - 3, y - 1, label_mat, 1)
    p.rect(x + 2, y - 3, x + 5, y - 1, "paper", 4)
    p.put(x + 2, y - 3, "paper", 2); p.put(x + 5, y - 3, "paper", 2)
    p.put(x + 3, y - 2, "paper", 2); p.put(x + 4, y - 2, "paper", 2)
    return (x, y - h - d + 1, x + w - 1, y)


def spam_part(p, x, y, r):
    mat = r.choice(["tarp", "redp"])
    tin(p, x, y, mat)
    tin(p, x + 8, y, mat)
    if r.random() < 0.6:
        tin(p, x + 4, y - 5, "redp" if mat == "tarp" else "tarp")
    return (x, y - 12, x + 15, y), 16


def parcel(p, x, y, r, size=None, lab=None):
    """A network packet as a parcel: taped lid, routing label with an address line."""
    w, d, h = size or r.choice([(8, 3, 5), (10, 4, 6), (7, 3, 4)])
    bx = box(p, x, y, w, d, h, "card", front=2, top=3)
    p.vline(x + w // 2, y - h - d + 2, y - h, "card", 4)                  # tape on the lid
    if lab:
        F.label(p, x + (w - F.text_width(lab) - 2) // 2, y - h + 2, lab, plate=("paper", 4), ink=("paper", 1))
    else:
        lx, ly = x + 1, y - h + 2
        p.rect(lx, ly, lx + 3, ly + 1, "paper", 4)
        p.hline(lx, lx + 2, ly + 1, "paper", 1)
    return bx, w


def floppy(p, x, y, r):
    """Floppy disk standing on edge (the 'save' icon, long deprecated)."""
    mat = r.choice(["plastic", "plastic", "tarp", "redp"])
    w, h = 10, 10
    top = y - h + 1
    p.rect(x, top, x + w - 1, y, mat, 2)
    p.hline(x, x + w - 2, top, mat, 3)
    p.vline(x + w - 1, top, y, mat, 1)
    p.clear(x + w - 1, top)
    p.rect(x + 2, top, x + 6, top + 3, "steel", 3)
    p.vline(x + 5, top + 1, top + 2, "steel", 1)
    p.rect(x + 1, top + 5, x + w - 2, y - 1, "paper", 4)
    p.hline(x + 2, x + w - 3, top + 6, "paper", 2)
    return (x, top, x + w - 1, y), w


def keycap(p, x, y, r, legend=None):
    """A giant keyboard key (legend on its top face)."""
    legend = legend or r.choice(["Z", "F5", "ESC", "DEL", "^C"])
    tw = F.text_width(legend)
    w = max(9, tw + 4)
    d, h = 7, 3
    bx = box(p, x, y, w, d, h, "shell", front=2, top=3)
    F.text(p, x + (w - tw) // 2, y - h - d + 2, legend, "plastic", 1)
    return bx, w


def missing_cube(p, x, y, r, s=10):
    """A block whose texture failed to load: the magenta/black checker; one corner de-rezzing."""
    d = max(3, s // 3)
    box(p, x, y, s, d, s, "steel", front=1, top=2)
    checker(p, x, y - s + 1, x + s - 1, y, a=("corrupt", 3), b=("steel", 0))
    checker(p, x, y - s - d + 1, x + s - 1, y - s, a=("corrupt", 4), b=("steel", 1))
    p.hline(x, x + s - 1, y - s + 1, "corrupt", 4)
    p.vline(x + s - 1, y - s - d + 1, y, "corrupt", 2)
    if hasattr(p, "post") and spend("derez"):
        rr = _rr(r)
        p.post.append(lambda q: derez(q, x + s - 2, y - s - d, rr, size=4, drift=(1, -1), n_bits=3))
    return (x, y - s - d + 1, x + s - 1, y), s


def cube_part(p, x, y, r):
    if spend("corrupt"):
        return missing_cube(p, x, y, r, s=8)
    return archive(p, x, y, r)


def modem(p, x, y, r, frame=0):
    """Dial-up modem with an old beige phone handset in its acoustic coupler, '56K' silkscreen,
    status LEDs (frame = handshake step)."""
    w, d, h = 22, 6, 7
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    tt = y - h - d + 1                                                    # top face first row
    for cx in (x + 5, x + 16):
        p.ellipse(cx, tt + 3, 3, 1.6, "rubber", 1)                        # coupler cups
    for cx in (x + 5, x + 16):
        p.ellipse(cx, tt + 1, 2.8, 1.8, "paper", 3)                       # handset ends
        p.put(cx - 1, tt, "paper", 4)
    p.rect(x + 5, tt - 2, x + 16, tt - 1, "paper", 3)                     # handset grip
    p.hline(x + 5, x + 16, tt - 2, "paper", 4)
    p.hline(x + 7, x + 14, tt - 1, "paper", 2)
    F.text(p, x + 2, y - 5, "56K", "shell", 3)
    pat = [(1, 0, 1, 0), (1, 1, 0, 1), (1, 0, 0, 1), (1, 1, 1, 0), (1, 0, 1, 1), (1, 1, 0, 0), (1, 0, 1, 0), (1, 1, 1, 1)]
    leds = pat[frame % len(pat)]
    for i, on in enumerate(leds):
        p.put(x + 14 + i * 2, y - 3, "redp" if i == 3 else "glow", 4 if on else 1)
    return (x, tt - 2, x + w - 1, y), w


def paper_wad(p, x, y, r):
    """A crumpled deleted document, the size of a trash bag: angular facets lit from the upper
    left, dark creases between them, a few printed lines. rng: same call as gen_junk.bag."""
    w = r.choice([11, 12, 13])
    cx, cy = x + w / 2 - 0.5, y - 4.5
    q = Q()
    rot = q.uniform(-0.4, 0.4)
    for yy in range(y - 9, y + 1):
        for xx in range(x, x + w):
            dx, dy = (xx - cx) / (w / 2), (yy - cy) / 4.6
            if abs(dx) + abs(dy) * 0.9 > 1.25 or dx * dx + dy * dy > 1.0:
                continue
            a = math.atan2(dy, dx) + rot
            sector = int(((a + math.pi) / (2 * math.pi)) * 5) % 5
            tone = (4, 3, 2, 2, 3)[sector]
            edge = abs(((a + math.pi) / (2 * math.pi)) * 5 % 1 - 0.5) > 0.42 and dx * dx + dy * dy > 0.12
            p.put(xx, yy, "paper", 1 if edge else tone)
    for k in range(2):
        p.hline(int(cx) - 3 + k, int(cx) - 1 + k, int(cy) - 2 + k * 2, "paper", 2)   # printed lines
    return (x, y - 9, x + w - 1, y), w


def crate_slot(p, x, y, r):
    """What lands where gen_junk put a crate: mostly archives, sometimes another digital thing of
    the same footprint (parcel, spam tins, folder icon, file icon, missing-texture block)."""
    if not D.BUDGET.get("subst", 1):
        return {"crate_slot": archive, "tire_slot": disc_stack, "bag_slot": J.bag}["crate_slot"](p, x, y, r)
    t = Q().random()
    if t < 0.62:
        return archive(p, x, y, r)
    r.choice([(14, 5, 11), (12, 4, 9), (16, 5, 10)]); r.random()           # keep gen_junk's sequence
    q = Q()
    if t < 0.70:
        return parcel(p, x, y, q, size=q.choice([(12, 4, 8), (14, 4, 9)]))
    if t < 0.78:
        return spam_part(p, x, y, q)
    if t < 0.86:
        return folder_icon(p, x, y, q)
    if t < 0.95 or not spend("corrupt"):
        return file_doc(p, x, y, q, w=13, h=15)
    return missing_cube(p, x, y, q, s=10)


def tire_slot(p, x, y, r):
    """Where gen_junk put a tire: mostly disc spindles, sometimes a giant key or floppies."""
    if not D.BUDGET.get("subst", 1):
        return {"crate_slot": archive, "tire_slot": disc_stack, "bag_slot": J.bag}["tire_slot"](p, x, y, r)
    t = Q().random()
    if t < 0.7:
        return disc_stack(p, x, y, r)
    r.random()
    q = Q()
    if t < 0.85:
        return keycap(p, x, y, q)
    return floppy(p, x, y, q)


def bag_slot(p, x, y, r):
    """Where gen_junk put a trash bag: mostly bags (it is the recycle bin), some crumpled files."""
    if not D.BUDGET.get("subst", 1):
        return {"crate_slot": archive, "tire_slot": disc_stack, "bag_slot": J.bag}["bag_slot"](p, x, y, r)
    if Q().random() < 0.14:
        return paper_wad(p, x, y, r)
    return J.bag(p, x, y, r)


# =============================================================== part tables

DPARTS = {
    "tire": tire_slot, "pipes": pipeline, "fan": J.fan, "chair": stage_chair, "ladder": stage_ladder,
    "plate": ui_pane, "tank": leak_tank, "crate": crate_slot, "amp": driver_amp, "rack": legacy_rack,
    "tv": err_tv, "bag": bag_slot, "speaker": driver_speaker, "mic": J.mic_stand, "synth": synth_dg,
    "monitor": err_monitor, "spot": projector, "truss": stage_truss, "rhead": avatar_head,
    "rtorso": avatar_torso, "pallet": J.pallet, "barrel": bit_bucket,
}
NEW_PARTS = {  # digital-native parts; they enter the piles by substitution (crate_slot / tire_slot / bag_slot)
    "doc": file_doc, "folder": folder_icon, "spam": spam_part, "parcel": parcel, "floppy": floppy,
    "keycap": keycap, "cube": cube_part, "modem": modem, "wad": paper_wad,
}

REINTERPRETED = {  # gen_junk kind -> (digital meaning) for the before/after sheet and the catalog
    "crate": "compressed archive (.zip)", "barrel": "bit bucket", "tank": "memory-leak tank",
    "pipes": "data pipeline", "tv": "error screen", "monitor": "404 / loading monitor",
    "amp": "deprecated audio driver", "speaker": "deprecated audio driver", "rack": "legacy server",
    "rhead": "deprecated avatar head", "rtorso": "discontinued voice-model body", "tire": "optical disc spindle",
    "chair": "virtual-stage chair", "ladder": "virtual-stage ladder", "truss": "virtual-stage truss",
    "spot": "hologram projector", "plate": "broken UI window pane", "synth": "sound module keyboard",
}

DTHEMES = J.THEMES          # same kind lists as gen_junk (calm heaps drop HEAP_SKIP kinds)
ALL_KINDS = J.ALL_KINDS


def pile_derez(p, r, n):
    """n quiet de-rez spots on a pile's top contour (no glowing data bits: a rare accent, not a light)."""
    for x, y in D.contour_spots(p, n, r):
        derez(p, x, y, r, size=4, drift=(r.choice([-1, 1]), -1), n_bits=2, data=False)


# =============================================================== lying drawings
# Boxy things that fell over get their own drawing in the front-on 3/4 view (top face + front face),
# instead of a 90 deg turn that would show the old top face as an isometric side face. Same signature
# as the parts: fn(p, x, y, r) -> (bbox, width), (x, y) = front-bottom-left. Always dead (no glow).

def lie_archive(p, x, y, r, size=None):
    """Archive knocked onto its side: wide and low, the zipper now runs along the front, the
    compression strap stands up."""
    w, d, h = size or r.choice([(16, 5, 9), (14, 4, 8), (18, 5, 10)])
    bx = box(p, x, y, w, d, h, "card", front=2, top=3)
    zy = y - h // 2
    for xx in range(x + 1, x + w - 1):
        p.put(xx, zy, "steel", 2 if xx % 2 == 0 else 1)
    p.rect(x + 3, zy - 1, x + 4, zy, "steel", 3)                          # slider
    sx = x + w // 2 + 2
    p.vline(sx, y - h + 2, y - 1, "card", 1)                              # strap, vertical now
    p.vline(sx, y - h - d + 2, y - h, "card", 2)
    return bx, w


def lie_amp(p, x, y, r, size=None):
    """Audio driver on its back: the speaker faces the ceiling (a foreshortened cone on the top face)."""
    w, d, h = size or (14, 10, 6)
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    tt = y - h + 1 - d
    cx, cy = x + w // 2 - 1, tt + d // 2 + 1
    p.ellipse(cx, cy, (w - 5) / 2, d * 0.26, "steel", 1)
    p.ellipse(cx, cy, (w - 8) / 2, d * 0.16, "rubber", 2)
    p.put(cx, cy, "rubber", 0); p.put(cx - 2, cy - 1, "steel", 3)
    p.hline(x + 2, x + w - 3, tt + 1, "steel", 2)                         # control strip, far edge now
    p.put(x + 1, y - 1, "rubber", 0); p.put(x + w - 3, y - 1, "rubber", 0)   # feet on the panel facing us
    return bx, w


def lie_speaker(p, x, y, r):
    """Speaker fallen on its side: the cones now sit side by side."""
    w, d, h = 22, 4, 10
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    for cx, rr in ((x + 6, 3.8), (x + 15, 3.2)):
        p.ellipse(cx, y - 5, rr, rr, "steel", 1)
        p.ellipse(cx, y - 5, rr - 1.2, rr - 1.2, "rubber", 2)
    return bx, w


def lie_rack(p, x, y, r, size=None):
    """Legacy server fallen on its side: long and low, drive slots standing upright, all lights out."""
    w, d, h = size or (r.choice([24, 27]), 4, 12)
    bx = box(p, x, y, w, d, h, "steel", front=1, top=3)
    slots = list(range(x + 3, x + w - 2, 3))
    pulled = Q().choice(slots[1:-1])
    for xx in slots:
        if xx == pulled:                                                  # one caddy half out
            p.vline(xx - 1, y - h + 2, y - 1, "steel", 3); p.vline(xx, y - h + 2, y - 1, "plastic", 2)
            continue
        p.vline(xx, y - h + 3, y - 2, "plastic", 1)
    return bx, w


def lie_tv(p, x, y, r, size=None):
    """CRT on its back: the dead screen faces up (dark glass on the top face), vents toward us."""
    w, d, h = size or (13, 8, 6)
    bx = box(p, x, y, w, d, h, "plastic", front=2, top=3)
    tt = y - h + 1 - d
    p.rect(x + 2, tt + 1, x + w - 4, tt + d - 2, "plastic", 0)
    p.hline(x + 2, x + w - 4, tt + 1, "plastic", 1)
    p.put(x + 3, tt + d - 3, "plastic", 2); p.put(x + 4, tt + d - 4, "plastic", 2)
    for xx in range(x + 2, x + w - 3, 2):
        p.put(xx, y - 2, "plastic", 1)
    return bx, w


def lie_monitor(p, x, y, r):
    """Flat monitor fallen on its face: a slab with the stand sticking up from its back."""
    w, d, h = 14, 7, 3
    bx = box(p, x, y, w, d, h, "plastic", front=1, top=3)
    tt = y - h + 1 - d
    p.rect(x + 6, tt - 3, x + 7, tt + 3, "plastic", 2)                    # neck
    box(p, x + 3, tt - 3, 8, 2, 1, "plastic", front=2, top=3)            # foot plate
    return (x, tt - 6, x + w - 1, y), w


def _cylinder_side(p, x, y, w, h, mat, bands=(), dark=1):
    """A drum / tank lying with its axis left-right: lit from above, rounded ends, raised bands."""
    for yy in range(y - h + 1, y + 1):
        t = (yy - (y - h + 1)) / max(1, h - 1)
        s = 4 if t < 0.12 else 3 if t < 0.42 else 2 if t < 0.78 else dark
        p.hline(x, x + w - 1, yy, mat, s)
    for bxx in bands:
        p.vline(x + bxx, y - h + 2, y - 1, mat, 3); p.vline(x + bxx + 1, y - h + 2, y - 1, mat, 1)
    p.vline(x, y - h + 2, y - 1, mat, 3)
    p.vline(x + w - 1, y - h + 2, y - 1, mat, 1)
    for cx_ in (x, x + w - 1):                                             # rounded ends
        p.clear(cx_, y - h + 1)
        p.clear(cx_, y)


def lie_barrel(p, x, y, r):
    """Bit bucket rolled onto its side."""
    w, h = 15, 11
    _cylinder_side(p, x, y, w, h, "steel", bands=(4, w - 6))
    return (x, y - h + 1, x + w - 1, y), w


def lie_tank(p, x, y, r):
    """Memory-leak tank lying on its side, valve stub at the end, hazard band dulled."""
    w, h = 20, 13
    mat = "redp" if r.random() < 0.25 else "steel"                       # a rare faded-red one
    _cylinder_side(p, x, y, w, h, mat, bands=(5, 13))
    p.rect(x + w, y - 8, x + w + 1, y - 5, "steel", 2)
    return (x, y - h + 1, x + w + 1, y), w + 2


def lie_torso(p, x, y, r):
    """Voice-model body on its back: chest panel and sound-wave emblem face up, arms at its sides."""
    w, d, h = 14, 8, 5
    bx = box(p, x, y, w, d, h, "shell", front=2, top=3)
    tt = y - h + 1 - d
    p.rect(x + 3, tt + 2, x + 10, tt + 5, "shell", 1)
    for i, dy in enumerate((0, -1, 0, 1, 0, -1, 0, 1)):
        p.put(x + 3 + i, tt + 4 + dy, "shell", 3)
    p.rect(x - 3, tt + 2, x - 1, tt + 6, "shell", 2); p.rect(x + w, tt + 2, x + w + 2, tt + 6, "shell", 1)
    return bx, w + 3


def lie_softbox(p, x, y, r):
    """Her discontinued software box lying on its back: the cover faces up (title, waveform, the EOL
    sticker), the box's spine toward us."""
    w, d, h = 16, 12, 4
    bx = box(p, x, y, w, d, h, "tarp", front=1, top=3)
    tt = y - h + 1 - d
    p.hline(x + 2, x + 8, tt + 1, "paper", 4); p.hline(x + 2, x + 6, tt + 2, "paper", 3)   # title
    for i, hb in enumerate((1, 2, 3, 2, 3, 1, 2, 1)):                     # waveform (foreshortened)
        p.vline(x + 9 + (i % 6), tt + 3 - hb // 2, tt + 3, "shell", 4 if i % 2 == 0 else 3)
    for k in range(4):                                                    # discontinued ribbon on the corner
        p.put(x + w - 5 + k, tt + k, "redp", 3); p.put(x + w - 4 + k, tt + k, "redp", 4)
    F.label(p, x + 2, tt + 4, "EOL", plate=("paper", 4), ink=("redp", 2))
    p.hline(x + 1, x + w - 3, y - 2, "tarp", 2)                           # spine stripe
    return bx, w


LIE = {"crate": lie_archive, "amp": lie_amp, "speaker": lie_speaker, "rack": lie_rack, "tv": lie_tv,
       "monitor": lie_monitor, "barrel": lie_barrel, "tank": lie_tank, "rtorso": lie_torso}

# How each kind comes to rest in a heap: tilt (8..40 deg on its contact corner), lie (lying drawing,
# 0..12 deg), fall (on its side, 65..95 deg), flip (upside down, 180 +- 20 deg), slump (long thin
# things lying along the heap, 3..14 deg - steep sticks crossing everywhere read as noise).
POSES = {
    "crate": (("tilt", 5), ("lie", 4)), "amp": (("tilt", 4), ("lie", 5)), "speaker": (("tilt", 4), ("lie", 5)),
    "rack": (("tilt", 4), ("lie", 5)), "tv": (("tilt", 5), ("lie", 4)), "monitor": (("tilt", 4), ("lie", 5)),
    "barrel": (("tilt", 4), ("lie", 5)), "tank": (("tilt", 3), ("lie", 6)), "rtorso": (("tilt", 4), ("lie", 5)),
    "rhead": (("tilt", 5), ("flip", 4)), "chair": (("tilt", 3), ("fall", 4), ("flip", 4)),
    "ladder": (("fall", 6),), "truss": (("slump", 6),), "mic": (("fall", 1),),
    "plate": (("slump", 6),), "pipes": (("slump", 6),), "spot": (("tilt", 4), ("flip", 4)),
    "fan": (("tilt", 5), ("flip", 2)), "pallet": (("tilt", 6),), "synth": (("tilt", 6),), "tire": (("tilt", 6),),
    "bag": (("tilt", 1),),
}
HEAP_SKIP = {"mic", "tire", "bag", "synth"}   # thin / tiny / soft / comb-patterned kinds only add noise to a calm heap
CALM_PARTS = {"crate": archive}          # no substitutions in calm heaps: archives stay archives


def _pix_bbox(p):
    pts = [(x, y) for y in range(p.h) for x in range(p.w) if p.px[y][x] is not None]
    if not pts:
        return None
    return (min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))


def _wchoice(r, opts):
    t = r.uniform(0, sum(w for _o, w in opts))
    for o, w in opts:
        t -= w
        if t <= 0:
            return o
    return opts[-1][0]


BIG = {  # (kind, lying): size of the big variant - a few big shapes give each heap its size hierarchy
    ("crate", False): (22, 6, 14), ("crate", True): (24, 6, 11), ("tv", False): (18, 7, 14), ("tv", True): (18, 10, 8),
    ("amp", False): (18, 6, 22), ("amp", True): (18, 12, 7), ("rack", False): (15, 5, 34), ("rack", True): (34, 5, 14),
}


def posed(kind, r, side=1, pose=None, angle=None, lit=False, fn=None, checker_patch=False, big=False, shade=0):
    """Draw one part alone and bring it to rest: returns (Pix, contact) where contact is the continuous
    point (in the Pix frame) that touches the ground/heap - the pivot corner for tilts and falls, the
    bottom centre for flips. side = which way is downhill (-1 left, +1 right); 70% lean that way.
    big: draw the big variant (BIG) when the kind has one; shade: darken every step by this much (junk
    deep inside a heap reads as dim silhouettes, not as more detail)."""
    pose = pose or _wchoice(r, POSES.get(kind, (("tilt", 1),)))
    c = DPix(110, 110)
    c.new_tag(kind)
    kw = {"size": BIG[(kind, pose == "lie")]} if big and (kind, pose == "lie") in BIG and fn is None else {}
    with calm(lit=lit, labels=False):
        if fn is None:
            fn = LIE[kind] if pose == "lie" and kind in LIE else (CALM_PARTS.get(kind) or DPARTS.get(kind) or NEW_PARTS[kind])
        fn(c, 42, 80, r, **kw)
    c.tag, c.post = None, []
    if shade:
        for row in c.px:
            for i, v in enumerate(row):
                if v is not None:
                    row[i] = (v[0], max(1, v[1] - shade))
    x0, y0, x1, y1 = _pix_bbox(c)
    if checker_patch:                                                       # the room's one missing texture
        my = (y0 + y1) // 2
        checker(c, x0 + 2, my - 2, min(x1 - 2, x0 + 7), my + 1)
    if angle is None:
        sgn = side if r.random() < 0.7 else -side
        angle = {"tilt": lambda: sgn * r.uniform(8, 40), "lie": lambda: sgn * r.uniform(0, 12),
                 "fall": lambda: sgn * r.uniform(80, 95), "flip": lambda: 180 + r.uniform(-20, 20),
                 "slump": lambda: side * r.uniform(3, 14)}[pose]()
    if pose == "flip" or abs(angle) > 120:
        pivot = ((x0 + x1 + 1) // 2, (y0 + y1 + 1) // 2)
    else:
        pivot = (x1 + 1, y1 + 1) if angle > 0 else (x0, y1 + 1)
    q, (ox, oy) = rot.rotate(c, angle, pivot) if abs(angle) >= 1 else (c, (0, 0))
    if pose == "flip" or abs(angle) > 120:
        bx0, _by0, bx1, by1 = _pix_bbox(q)
        return q, ((bx0 + bx1 + 1) // 2, by1 + 1)
    return q, (pivot[0] - ox, pivot[1] - oy)


def paste_at(p, q, contact, X, Y):
    """Paste q so its contact point lands on (X, Y) of p; returns the set of p pixels it wrote."""
    dx, dy = int(round(X - contact[0])), int(round(Y - contact[1]))
    wrote = []
    for v in range(q.h):
        for u in range(q.w):
            val = q.px[v][u]
            if val is not None and 0 <= u + dx < p.w and 0 <= v + dy < p.h:
                p.put(u + dx, v + dy, *val)
                wrote.append((u + dx, v + dy))
    return wrote


def bury(p, pts, line, r, rim=True):
    """Sink a part into the heap: every pixel of the part below the debris line line(x) becomes heap
    body (dark scrap), with a lit crest on the debris edge, so the part reads as half swallowed."""
    cols = {}
    for x, y in pts:
        if y > line(x):
            cols.setdefault(x, []).append(y)
    for x, ys in cols.items():
        top = min(ys)
        for y in ys:
            p.put(x, y, "plastic", 1)
        if rim:
            p.put(x, top, "plastic", 2)


def debris_skirt(p, x0, x1, y, hgt, r, mats=(("plastic", 1), ("rubber", 1))):
    """A low lumpy bank of dark scrap on the floor from x0 to x1 (base row y, up to hgt high) - what a
    dumped single sinks into or rests on. Lit crest, no speckle."""
    ph = r.uniform(0, 6.3)
    mid = (x0 + x1) / 2
    half = max(1, (x1 - x0) / 2)
    for x in range(x0, x1 + 1):
        k = max(0.0, 1 - abs(x - mid) / half) ** 0.6
        top = int(round(y - hgt * k - 0.8 * math.sin(x * 0.7 + ph)))
        if top > y:
            continue
        for yy in range(top, y + 1):
            p.put(x, yy, *mats[0])
        p.put(x, top, mats[0][0], mats[0][1] + 1)


# =============================================================== calm heaps (fewer, bigger, tumbled)

def dheap(seed, kinds, n=6, w=120, peak=30, derez=0, checker_at=None, spills=None):
    """A heap of deleted data: one big quiet dark mass with a few large things tumbled into it.
    Every part lies, tilts, falls or is upside down (never upright); most are half buried in the heap;
    a couple slid out at the foot. Screens are dead, LEDs off, no labels (calm-glow rule).
    derez = quiet de-rez spots on the top (room budget: a few in total); checker_at = index of the part
    that gets the room's one missing-texture patch."""
    r = random.Random(seed)
    D.reseed(seed)
    D.BUDGET.update(subst=0, corrupt=0, wire=0, derez=0, bits=0)
    kinds = [k for k in kinds if k not in HEAP_SKIP] or ["crate"]
    head = 34                                                               # room for things sticking up
    H = peak + head + 16
    p = DPix(w, H)
    ground = H - 8
    cx = w / 2 + r.uniform(-w * 0.12, w * 0.12)
    ph1, ph2, ph3 = r.uniform(0, 6.3), r.uniform(0, 6.3), r.uniform(0, 6.3)

    def foot(x):
        return int(ground + 2 * math.sin(x * 0.09 + ph1) + 1.5 * math.sin(x * 0.23 + ph2))

    def lift(x, spread=0.47):
        base = peak * max(0.0, 1 - abs(x - cx) / (w * spread)) ** 1.3
        return base * (1 + 0.10 * math.sin(x * 0.21 + ph3))                 # a lumpy, not ruler-smooth, crest

    def top(x):
        return foot(x) - lift(x)

    # the body: one dark mass, a lit crest along its top, a handful of broad lumps (no speckle)
    for x in range(2, w - 2):
        t = int(top(x))
        for y in range(t, foot(x) + 1):
            p.put(x, y, "plastic", 1)
        if foot(x) - t >= 2:
            p.put(x, t, "plastic", 2)
    for _ in range(max(1, w // 40)):
        lx = r.uniform(w * 0.15, w * 0.85)
        if lift(lx) < 6:
            continue
        ly = r.uniform(top(lx) + 3, foot(int(lx)) - 2)
        rx, ry = r.uniform(4, 7), r.uniform(2, 3)
        mat = r.choice(["rubber", "plastic"])
        for yy in range(int(ly - ry), int(ly + ry) + 1):
            for xx in range(int(lx - rx), int(lx + rx) + 1):
                if ((xx - lx) / rx) ** 2 + ((yy - ly) / ry) ** 2 <= 1 and p.get(xx, yy) == ("plastic", 1):
                    lit_px = (xx - lx) / rx + (yy - ly) / ry < -0.9
                    p.put(xx, yy, mat, 3 if lit_px else 2)

    def sink(pts, X, Y, frac):
        ys = [y for _x, y in pts]
        depth = max(2, int((max(ys) - min(ys) + 1) * frac))
        t0, ph = top(X), r.uniform(0, 6.3)
        bury(p, pts, lambda xx: Y - depth + 0.7 * (top(xx) - t0) + 1.2 * math.sin(xx * 0.6 + ph), r)

    # deep layer: dim silhouettes of junk the heap already swallowed, so the mass reads as junk (calmly)
    deep = []
    for _ in range(max(2, n // 2 + 1)):
        x = max(8, min(w - 8, r.gauss(cx, w * 0.24)))
        deep.append((foot(int(x)) - lift(x) * r.uniform(0.3, 0.85), x, r.choice(kinds)))
    for base, x, kind in sorted(deep):
        q, contact = posed(kind, r, side=-1 if x < cx else 1, big=r.random() < 0.6, shade=2)
        X, Y = int(x), int(base) + 1
        sink(paste_at(p, q, contact, X, Y), X, Y, r.uniform(0.45, 0.8))

    # parts: spots inside the mound, drawn far/high first so nearer junk overlaps
    spots = []
    nbig = max(1, n // 3)
    for i in range(n):
        x = max(8, min(w - 8, r.gauss(cx, w * 0.21)))
        k = r.uniform(0.5, 1.0)
        spots.append((foot(int(x)) - lift(x) * k, x, r.choice(kinds), k, i))
    nspill = spills if spills is not None else 1 if n < 5 else 2
    for i in range(nspill):                                                 # slid out in front of the heap
        x = r.uniform(10, w - 10)
        spots.append((foot(int(x)) + r.randint(2, 5), x, r.choice(kinds), -1, n + i))
    for base, x, kind, k, i in sorted(spots):
        side = -1 if x < cx else 1
        q, contact = posed(kind, r, side=side, checker_patch=(i == checker_at), big=0 <= i < nbig, shade=1)
        X, Y = int(x), int(base) + 1
        pts = paste_at(p, q, contact, X, Y)
        if k < 0:                                                           # spill: barely sunk into floor junk
            if r.random() < 0.5:
                bury(p, pts, lambda xx: Y - 3, r, rim=False)
            continue
        if r.random() < 0.8:
            sink(pts, X, Y, r.uniform(0.25, 0.55))
    p.outline()
    if derez:
        D.BUDGET["derez"] = derez
        pile_derez(p, _rr(Q()), derez)
    return p.bbox_crop()


def drop(p, q, x, ground, sink=2):
    """Lower q (left edge at x) onto what is already drawn in p - or the ground row - until it touches;
    then let it settle `sink` px into the top face it lands on. sink="ground": stand on the floor in front
    of what is there (leaning against it). Returns the pixels written."""
    bb = _pix_bbox(q)
    best, on_ground = None, True
    if sink == "ground":
        best, sink = ground - bb[3], 0
    for u in range(bb[0], bb[2] + 1) if best is None else ():
        col = [v for v in range(q.h) if q.px[v][u] is not None]
        if not col:
            continue
        b = max(col)
        X = x + u - bb[0]
        s = ground + 1
        if 0 <= X < p.w:
            for yy in range(p.h):
                if p.px[yy][X] is not None:
                    s = min(s, yy)
                    break
        cand = s - 1 - b
        if best is None or cand < best:
            best, on_ground = cand, s == ground + 1
    dy = best + (0 if on_ground else sink)
    wrote = []
    for v in range(q.h):
        for u in range(q.w):
            val = q.px[v][u]
            if val is not None and 0 <= x + u - bb[0] < p.w and 0 <= v + dy < p.h:
                p.put(x + u - bb[0], v + dy, *val)
                wrote.append((x + u - bb[0], v + dy))
    return wrote


def dstack_lean(seed, spec, w=64, h=84, lit_top=False):
    """Things stacked by somebody once and now leaning: each part (kind, pose, angle, dx, sink) is
    dropped onto what is below it, so the tower leans and looks like it could topple."""
    r = random.Random(seed)
    D.reseed(seed)
    D.BUDGET.update(subst=0, corrupt=0, wire=0, derez=0, bits=0)
    p = DPix(w, h)
    ground = h - 3
    for i, (kind, pose, angle, dx, sink, *fn) in enumerate(spec):
        lit = lit_top and i == len(spec) - 1
        q, _contact = posed(kind, r, pose=pose, angle=angle, lit=lit, fn=fn[0] if fn else None)
        drop(p, q, 14 + dx, ground, sink)
    p.outline()
    return p.bbox_crop()


def dsingle(fn, seed, w=56, h=64, budget=True, **kw):
    r = random.Random(seed)
    D.reseed(seed)
    D.BUDGET.update(corrupt=1 if budget else 0, wire=1 if budget else 0, derez=1 if budget else 0, bits=1)
    p = DPix(w + 12, h + 8)
    p.new_tag("single")
    fn(p, 12, h + 4, r, **kw)
    p.tag = None
    return p.finish()


# =============================================================== new standalone props

def dialog(p, x, y, r, msg="ERR", shards=True, title=True):
    """Broken error dialog standing on the floor: bevelled grey window, title bar with close box,
    error icon, message, OK button. The lower-right corner shattered off."""
    w, h, d = 36, 26, 2
    top = y - h + 1
    p.rect(x, top - d, x + w - 1, top - 1, "steel", 4)                    # thin top edge
    p.rect(x, top, x + w - 1, y, "steel", 3)                              # window body
    p.hline(x, x + w - 1, top, "steel", 4); p.vline(x, top, y, "steel", 4)
    p.hline(x, x + w - 1, y, "steel", 1); p.vline(x + w - 1, top - d, y, "steel", 1)
    p.rect(x + 2, top + 2, x + w - 3, top + 8, "tarp", 2)                 # title bar
    p.hline(x + 2, x + w - 3, top + 2, "tarp", 3)
    if title:
        F.text(p, x + 4, top + 3, "ERROR", "paper", 4)
    else:                                                                  # tilted: tiny text would turn to noise
        p.hline(x + 4, x + 16, top + 5, "tarp", 3)
    bxx = x + w - 10
    p.rect(bxx, top + 3, bxx + 6, top + 7, "steel", 3)                    # close box
    p.hline(bxx, bxx + 6, top + 3, "steel", 4); p.vline(bxx + 6, top + 3, top + 7, "steel", 1)
    F.text(p, bxx + 2, top + 3, "X", "plastic", 1)
    iy = top + 11
    if msg == "404":
        F.text(p, x + 7, iy - 1, msg, "plastic", 1, scale=2)
    else:
        p.ellipse(x + 7, iy + 3, 3.6, 3.6, "redp", 3)                      # error icon
        p.ellipse(x + 6, iy + 2, 1.4, 1.4, "redp", 4)
        for k in (-1, 0, 1):
            p.put(x + 7 + k, iy + 3 + k, "paper", 4); p.put(x + 7 + k, iy + 3 - k, "paper", 4)
        F.text(p, x + 14, iy + 1, msg, "plastic", 1)
        p.hline(x + 14, x + 30, iy + 7, "steel", 1)
    by = y - 5
    if msg == "404":
        by += 1
    p.rect(x + 13, by, x + 23, by + 3, "steel", 3)                        # OK button
    p.hline(x + 13, x + 23, by, "steel", 4); p.hline(x + 13, x + 23, by + 3, "steel", 1)
    p.vline(x + 23, by, by + 3, "steel", 1)
    p.hline(x + 16, x + 20, by + 1, "plastic", 2)
    for yy in range(y - 9, y + 1):                                        # shattered corner
        cut = (yy - (y - 9)) + 1
        for c in range(min(cut, 11)):
            p.clear(x + w - 1 - c, yy)
    line(p, x + w - 12, y, x + w - 15, y - 4, "steel", 1)                 # crack running up
    if msg != "404":
        line(p, x + w - 15, y - 4, x + w - 18, y - 8, "steel", 1)
        line(p, x + w - 18, y - 8, x + w - 16, y - 13, "steel", 1)
    for sx, sy, s in ((x + w - 4, y, 2), (x + w - 8, y, 1), (x + w + 1, y - 1, 1)) if shards else ():   # shards
        p.rect(sx, sy - s + 1, sx + s - 1, sy, "steel", 3)
    return (x, top - d, x + w + 1, y), w + 2


def big_folder(p, x, y, r):
    """Torn folder icon, big, propped up by a scrap rod; a rip in the front flap shows the files
    inside, one sheet already slid out."""
    w, h = 32, 25
    top = y - h + 1
    folder_icon(p, x, y, r, w=w, h=h)
    ft = top + 4 + h // 6
    rip = [(16, 27), (17, 26), (17, 26), (18, 25), (19, 25), (19, 24), (20, 23), (21, 22)]
    for i, (a, b) in enumerate(rip):                                       # V-shaped rip
        yy = ft + i
        for xx in range(x + a, x + b + 1):
            p.put(xx, yy, "paper", 2 if i % 2 else 3)                      # the files inside
        p.put(x + a, yy, "icon", 4)                                        # torn fibres (lit edge)
        p.put(x + b, yy, "icon", 1)
    for i in range(4):                                                     # peeled-back flap corner
        for k in range(4 - i):
            p.put(x + 28 + k, ft + 1 + i, "icon", 1 if k == 3 - i else 2)
    d1, d2 = (x + w + 7, y), (x + w - 2, y - 16)                           # scrap rod propping it up
    line(p, d1[0], d1[1], d2[0], d2[1], "steel", 3)
    line(p, d1[0] + 1, d1[1], d2[0] + 1, d2[1], "steel", 1)
    p.rect(d1[0] - 1, y - 1, d1[0] + 2, y, "rubber", 1)
    file_doc(p, x - 7, y, r, ext="TMP", w=13, h=14)                       # a sheet slid out
    p.hline(x + 12, x + 13, y + 1, "paper", 3)                             # scraps of the rip
    return (x - 7, top, x + w + 9, y + 1), w + 16


def recycle_bin(p, x, y, r):
    """The recycle bin itself: a mesh wastebasket, wider at the top, full of crumpled files,
    one deleted sheet sticking out; a dim recycling triangle on its plate."""
    wt, wb, h = 30, 24, 30
    cx = x + wt / 2 - 0.5
    top = y - h + 1
    for yy in range(top + 2, y + 1):                                      # mesh body
        t = (yy - top) / h
        half = (wt / 2) * (1 - t) + (wb / 2) * t
        x0, x1 = int(round(cx - half + 0.5)), int(round(cx + half - 0.5))
        for xx in range(x0, x1 + 1):
            u = (xx - x0) / max(1, x1 - x0)
            side = 4 if u < 0.25 else 3 if u < 0.6 else 2 if u < 0.85 else 1
            wire_v = round((xx - cx) / half * 6) != round((xx - 1 - cx) / half * 6)
            if (yy - top) % 3 == 0 or wire_v or xx in (x0, x1):
                p.put(xx, yy, "steel", side)
            else:
                p.put(xx, yy, "plastic", 1 if u < 0.7 else 0)            # dark inside through the mesh
    for xx in range(int(cx - 9), int(cx + 9)):                            # contents seen through the mesh
        for yy in range(top + 5, top + 12):
            if p.get(xx, yy) == ("plastic", 1) and ((xx * 7 + yy * 3) % 11) < 6:
                p.put(xx, yy, "paper", 2)
    p.rect(int(cx) - 12, y - 2, int(cx) + 12, y, "steel", 2)              # base band
    p.hline(int(cx) - 12, int(cx) + 12, y - 2, "steel", 3)
    p.ellipse(cx, top + 2, wt / 2, 3.2, "steel", 4)                       # rolled rim
    p.ellipse(cx, top + 2, wt / 2 - 1.6, 2.0, "plastic", 0)               # opening
    sx = int(cx) - 2                                                      # a deleted sheet sticking out
    p.rect(sx, top - 8, sx + 6, top + 2, "paper", 3)
    p.hline(sx, sx + 6, top - 8, "paper", 4); p.vline(sx + 6, top - 8, top + 2, "paper", 2)
    p.clear(sx + 6, top - 8); p.put(sx + 5, top - 7, "paper", 2)
    for k, yy in enumerate((top - 6, top - 4, top - 2)):
        p.hline(sx + 1, sx + 4 - (k % 2), yy, "paper", 2)
    for bx_, by_, rw, rh, m in ((cx - 8, top + 1, 3.5, 2.5, "paper"), (cx + 5, top + 1, 3.2, 2.2, "paper"),
                                (cx + 9, top + 2, 2.5, 1.5, "card"), (cx - 3, top + 2, 2.6, 1.4, "paper")):
        p.ellipse(bx_, by_, rw, rh, m, 3)
        p.ellipse(bx_ - 1, by_ - 1, rw * 0.5, rh * 0.5, m, 4)
    pc = (int(cx), top + 15)                                              # recycling triangle plate
    p.rect(pc[0] - 5, pc[1] - 4, pc[0] + 5, pc[1] + 4, "steel", 3)
    p.hline(pc[0] - 5, pc[0] + 5, pc[1] - 4, "steel", 4); p.vline(pc[0] + 5, pc[1] - 4, pc[1] + 4, "steel", 2)
    tri = [(0, -3), (-1, -2), (1, -2), (-2, -1), (2, -1), (-3, 1), (3, 1), (-3, 2), (-2, 2), (2, 2), (3, 2), (0, 2)]
    tm, ts = ("glow", 1) if CALM["lit"] else ("steel", 1)                  # calm: an embossed, unlit symbol
    for dx, dy in tri:
        p.put(pc[0] + dx, pc[1] + dy, tm, ts)
    p.put(pc[0] + 1, pc[1] - 3, tm, ts); p.put(pc[0] - 4, pc[1] + 1, tm, ts); p.put(pc[0] + 1, pc[1] + 3, tm, ts)
    return (x, top - 8, x + wt - 1, y), wt


def spam_pyramid(p, x, y, r):
    """Tins of spam stacked 3-2-1, one rolled off."""
    for i in range(3):
        tin(p, x + i * 8, y, "redp" if i != 1 else "tarp")
    for i in range(2):
        tin(p, x + 4 + i * 8, y - 5, "tarp" if i else "redp")
    tin(p, x + 8, y - 10, "redp")
    tin(p, x + 25, y + 3, "tarp")
    return (x, y - 17, x + 32, y + 3), 33


def cookie(p, cx, cy, bite=False):
    p.ellipse(cx, cy, 3.2, 1.8, "card", 3)
    p.put(cx - 1, cy - 1, "card", 4)
    p.put(cx - 1, cy, "plastic", 1); p.put(cx + 1, cy - 1, "plastic", 1); p.put(cx + 1, cy + 1, "plastic", 1)
    if bite:
        for dx, dy in ((3, -1), (3, 0), (2, -1)):
            p.clear(int(cx) + dx, int(cy) + dy)


def cookie_jar(p, x, y, r):
    """Cookie jar (browser cookies): glass jar of cookies, lid with knob, one bitten cookie outside."""
    w = 14
    p.rect(x, y - 12, x + w - 1, y, "steel", 1)                            # glass seen against the dark
    for yy, xs in ((y - 12, (x, x + w - 1)), (y, (x, x + w - 1))):
        p.clear(xs[0], yy); p.clear(xs[1], yy)
    for k, cy in enumerate((y - 2, y - 4, y - 6, y - 8)):                  # cookies stacked inside
        cookie(p, x + 6 + (1 if k % 2 else -1) * (k // 2), cy)
    p.vline(x + 1, y - 11, y - 2, "shell", 4); p.put(x + 2, y - 10, "shell", 4)   # glass glints
    p.vline(x + w - 2, y - 10, y - 2, "shell", 2)
    p.vline(x + w - 1, y - 11, y - 1, "steel", 2)
    p.hline(x + 1, x + w - 2, y, "steel", 2)
    p.rect(x + 2, y - 14, x + w - 3, y - 13, "shell", 3)                   # neck
    p.rect(x + 1, y - 17, x + w - 2, y - 15, "redp", 3)                    # lid
    p.hline(x + 1, x + w - 2, y - 17, "redp", 4); p.vline(x + w - 2, y - 17, y - 15, "redp", 2)
    p.rect(x + 5, y - 19, x + 8, y - 18, "redp", 3); p.hline(x + 5, x + 8, y - 19, "redp", 4)
    cookie(p, x + w + 4, y - 1, bite=True)
    return (x, y - 19, x + w + 7, y), w + 8


def software_box(p, x, y, r):
    """Discontinued software box: retail box with a sound-wave cover and a discontinued ribbon."""
    w, d, h = 15, 4, 20
    bx = box(p, x, y, w, d, h, "tarp", front=1, top=3)
    ft = y - h + 1
    p.rect(x + 1, ft + 2, x + w - 3, ft + 3, "tarp", 3)                    # title block
    p.hline(x + 2, x + 8, ft + 2, "paper", 4); p.hline(x + 2, x + 6, ft + 3, "paper", 3)
    cy = ft + 9
    for i, hb in enumerate((1, 2, 4, 3, 5, 2, 4, 3, 1, 2, 1)):            # waveform bars
        p.vline(x + 2 + i, cy - hb // 2 - (hb % 2 == 0) * 0, cy + hb // 2, "shell", 4 if i % 2 == 0 else 3)
    p.ellipse(x + 7, y - 4, 4, 2, "tarp", 2)                               # disc art (half circle)
    p.hline(x + 1, x + w - 2, y - 5, "tarp", 3)
    for k in range(5):                                                     # corner ribbon
        p.put(x + w - 6 + k, ft + k - 1, "redp", 3)
        p.put(x + w - 5 + k, ft + k - 1, "redp", 4)
    F.label(p, x + 1, y - 7, "EOL", plate=("paper", 4), ink=("redp", 2))
    return bx, w


def captcha_panel(p, x, y, r):
    """CAPTCHA board in a robot scrapyard: 3x3 picture tiles, the 'not a robot' box crossed out."""
    w, h, d = 23, 31, 2
    top = y - h + 1
    legs = (x + 4, x + w - 5)
    for lx in legs:
        p.vline(lx, y - 3, y, "steel", 2)
    p.rect(x, top - d, x + w - 1, top - 1, "paper", 4)
    p.rect(x, top, x + w - 1, y - 4, "paper", 3)
    p.vline(x + w - 1, top - d, y - 4, "paper", 2); p.hline(x, x + w - 1, y - 4, "paper", 2)
    p.rect(x + 1, top + 1, x + w - 2, top + 4, "tarp", 3)                 # instruction bar
    p.hline(x + 2, x + 13, top + 2, "paper", 4); p.hline(x + 2, x + 9, top + 3, "paper", 3)
    sel = {(0, 1), (1, 2), (2, 0)}
    for gy in range(3):
        for gx in range(3):
            tx, ty = x + 2 + gx * 7, top + 6 + gy * 6
            p.rect(tx, ty, tx + 5, ty + 4, "steel", 2)
            pic = (gx * 2 + gy) % 3
            if pic == 0:                                                   # traffic light
                p.rect(tx + 2, ty + 1, tx + 3, ty + 4, "plastic", 1)
                p.put(tx + 2, ty + 1, "redp", 4); p.put(tx + 3, ty + 3, "warn", 3)
            elif pic == 1:                                                 # crosswalk
                for k in range(0, 6, 2):
                    p.vline(tx + k, ty + 3, ty + 4, "paper", 4)
            else:                                                          # bus / car
                p.rect(tx + 1, ty + 1, tx + 4, ty + 3, "warn", 2); p.hline(tx + 1, tx + 4, ty + 1, "warn", 3)
                p.put(tx + 1, ty + 4, "plastic", 0); p.put(tx + 4, ty + 4, "plastic", 0)
            if (gx, gy) in sel:
                p.put(tx, ty, "tarp", 4); p.put(tx + 1, ty, "tarp", 4); p.put(tx, ty + 1, "tarp", 4)
    cyy = y - 9
    p.rect(x + 2, cyy - 1, x + 6, cyy + 3, "paper", 4)                     # the checkbox
    p.rect(x + 3, cyy, x + 5, cyy + 2, "paper", 4)
    p.hline(x + 2, x + 6, cyy - 1, "paper", 1); p.hline(x + 2, x + 6, cyy + 3, "paper", 1)
    p.vline(x + 2, cyy - 1, cyy + 3, "paper", 1); p.vline(x + 6, cyy - 1, cyy + 3, "paper", 1)
    for k in range(3):
        p.put(x + 3 + k, cyy + k, "redp", 3); p.put(x + 5 - k, cyy + k, "redp", 3)
    p.hline(x + 8, x + 19, cyy, "paper", 1); p.hline(x + 8, x + 15, cyy + 2, "paper", 2)
    return (x, top - d, x + w - 1, y), w


def gc_robot(p, x, y, r):
    """Garbage-collector robot, deactivated: tracked base, hopper full of deleted files, 'GC'
    stencil, sweeper arm slumped to the floor, eye dark."""
    bx_ = x + 6
    p.rect(bx_, y - 3, bx_ + 19, y, "rubber", 1)                           # tracks
    p.hline(bx_, bx_ + 19, y - 3, "rubber", 2)
    for wx in (bx_ + 3, bx_ + 10, bx_ + 16):
        p.ellipse(wx, y - 1.5, 1.6, 1.6, "rubber", 0); p.put(wx, y - 2, "steel", 3)
    box(p, bx_ + 1, y - 4, 18, 4, 11, "steel", front=2, top=3)            # body
    for k in range(18):                                                    # hazard bumper
        p.put(bx_ + 1 + k, y - 5, "warn", 3 if (k // 2) % 2 == 0 else 1)
        p.put(bx_ + 1 + k, y - 6, "warn", 3 if ((k + 1) // 2) % 2 == 0 else 1)
    F.text(p, bx_ + 3, y - 12, "GC", "warn", 3)
    for gy in (y - 12, y - 10, y - 8):
        p.hline(bx_ + 11, bx_ + 16, gy, "plastic", 1)                      # intake grille
    box(p, bx_ + 2, y - 16, 10, 3, 4, "steel", front=1, top=2)             # hopper
    for hx, m, s in ((bx_ + 3, "paper", 4), (bx_ + 5, "paper", 3), (bx_ + 7, "icon", 3), (bx_ + 9, "paper", 4)):
        p.rect(hx, y - 21, hx + 1, y - 20, m, s)
    p.put(bx_ + 6, y - 22, "paper", 4)
    p.ellipse(bx_ + 15, y - 18, 3.2, 2.8, "shell", 3)                       # sensor dome
    p.ellipse(bx_ + 14, y - 19, 1.2, 1, "shell", 4)
    p.hline(bx_ + 13, bx_ + 17, y - 17, "plastic", 1)
    p.put(bx_ + 14, y - 17, "glow", 1)                                     # eye: off
    p.vline(bx_ + 17, y - 23, y - 21, "steel", 2); p.put(bx_ + 17, y - 24, "redp", 2)   # antenna, LED off
    line(p, bx_, y - 11, bx_ - 3, y - 4, "steel", 2)                        # slumped sweeper arm
    line(p, bx_ + 1, y - 11, bx_ - 2, y - 4, "steel", 3)
    p.rect(x, y - 3, x + 6, y, "rubber", 2)                                  # brush head on the floor
    for k in range(0, 7, 2):
        p.vline(x + k, y - 1, y, "rubber", 3)
    p.hline(x, x + 6, y - 3, "steel", 2)
    return (x, y - 24, bx_ + 19, y), 26


def parcels(p, x, y, r):
    """Packet loss: scattered parcels with routing labels, one burst open with bits leaking out."""
    parcel(p, x + 2, y - 6, r, size=(9, 3, 5))
    parcel(p, x + 14, y - 3, r, size=(15, 4, 9), lab="UDP")
    parcel(p, x + 33, y - 7, r, size=(7, 3, 4))
    parcel(p, x + 30, y, r, size=(8, 3, 5))
    ox, oy = x + 3, y                                                      # the burst one, lid flaps open
    box(p, ox, oy, 9, 3, 4, "card", front=2, top=3)
    p.rect(ox + 1, oy - 6, ox + 7, oy - 4, "plastic", 0)
    p.hline(ox - 1, ox + 2, oy - 7, "card", 4); p.hline(ox + 6, ox + 9, oy - 7, "card", 4)
    p.put(ox + 4, oy - 5, "glow", 3)

    def leak(q):
        for bx, by, s in ((ox + 4, oy - 9, 3), (ox + 6, oy - 11, 2), (ox + 3, oy - 13, 1)):
            float_put(q, bx, by, "glow", s)
    p.post.append(leak)
    return (x, y - 17, x + 41, y), 42


def cache_box(p, x, y, r):
    """Cache = cash: a steel cash box, lid open, coins inside and a few spilled."""
    w, d, h = 14, 5, 7
    p.rect(x + 1, y - h - d - 7, x + w - 2, y - h - d, "steel", 1)          # open lid (inside face)
    p.hline(x + 1, x + w - 2, y - h - d - 7, "steel", 3)
    p.vline(x + 1, y - h - d - 7, y - h - d, "steel", 2)
    bx = box(p, x, y, w, d, h, "steel", front=2, top=3)
    p.rect(x + 1, y - h - d + 2, x + w - 2, y - h, "plastic", 1)            # tray
    for k, (cx, cy) in enumerate(((x + 3, y - h - 2), (x + 6, y - h - 1), (x + 9, y - h - 2), (x + 11, y - h - 1),
                                   (x + 5, y - h - 3), (x + 8, y - h - 3))):
        p.hline(cx, cx + 1, cy, "warn", 3 if k % 2 else 4)
    p.rect(x + 5, y - 4, x + 8, y - 3, "steel", 1); p.put(x + 6, y - 4, "steel", 4)   # lock
    for cx, cy in ((x + w + 2, y), (x + w + 5, y - 1)):
        p.hline(cx, cx + 1, cy, "warn", 3)
    return (x, y - h - d - 7, x + w + 6, y), w + 7


def keys_undo(p, x, y, r):
    keycap(p, x, y - 3, r, "CTRL")
    keycap(p, x + 17, y, r, "Z")
    return (x, y - 12, x + 26, y), 27


def teapot(p, x, y, r):
    """HTTP 418 I'm a teapot: a big teapot with its status code painted on."""
    cx = x + 11
    p.ellipse(cx + 8.5, y - 6, 3, 3.6, "shell", 2)                         # handle ring
    for yy in range(y - 8, y - 3):
        for xx in range(cx + 8, cx + 10):
            if ((xx - cx - 8.5) / 1.4) ** 2 + ((yy - y + 6) / 2.0) ** 2 <= 1:
                p.clear(xx, yy)
    line(p, cx - 6, y - 4, cx - 11, y - 10, "shell", 3)                    # spout
    line(p, cx - 6, y - 3, cx - 10, y - 9, "shell", 2)
    line(p, cx - 7, y - 3, cx - 10, y - 8, "shell", 2)
    p.put(cx - 11, y - 11, "shell", 4); p.put(cx - 12, y - 11, "shell", 3)
    p.ellipse(cx, y - 5, 7.5, 5.5, "shell", 3)                             # body
    p.ellipse(cx - 3, y - 8, 3, 1.6, "shell", 4)
    p.hline(cx - 5, cx + 5, y, "shell", 2)
    p.vline(cx + 7, y - 7, y - 3, "shell", 2)
    p.ellipse(cx, y - 11, 3.5, 1.4, "shell", 4); p.rect(cx - 1, y - 14, cx, y - 13, "shell", 3)
    F.text(p, cx - 5, y - 7, "418", "plastic", 1)
    return (x, y - 14, x + 22, y), 23


def duck(p, x, y, r):
    """Rubber debugging duck."""
    p.ellipse(x + 5, y - 3, 5, 3, "warn", 3)
    p.ellipse(x + 3, y - 4, 2, 1, "warn", 4)
    p.ellipse(x + 7, y - 7, 2.6, 2.6, "warn", 3)
    p.put(x + 6, y - 8, "warn", 4)
    p.put(x + 8, y - 8, "plastic", 0)
    p.rect(x + 10, y - 7, x + 11, y - 6, "redp", 4)
    p.hline(x + 1, x + 8, y, "warn", 2)
    return (x, y - 10, x + 11, y), 12


def trojan(p, x, y, r):
    """Trojan horse dumped in the recycle bin: wooden horse on a wheeled board, belly hatch ajar."""
    p.rect(x, y - 4, x + 23, y - 3, "card", 2); p.hline(x, x + 23, y - 4, "card", 3)    # board
    for wx in (x + 3, x + 20):
        p.ellipse(wx, y - 1.5, 2, 2, "card", 1); p.put(wx, y - 2, "card", 4)
    for lx, s in ((x + 7, 1), (x + 17, 1), (x + 5, 2), (x + 15, 2)):         # far legs darker, near lighter
        p.rect(lx, y - 10, lx + 1, y - 5, "card", s + 1)
    p.rect(x + 4, y - 16, x + 19, y - 10, "card", 3)                       # body
    p.hline(x + 4, x + 19, y - 16, "card", 4)
    for py in (y - 14, y - 12):
        p.hline(x + 5, x + 18, py, "card", 2)                              # planks
    p.rect(x + 9, y - 11, x + 13, y - 10, "plastic", 0)                     # hatch ajar
    p.put(x + 10, y - 11, "corrupt", 3); p.put(x + 12, y - 10, "corrupt", 2)   # malware inside
    p.rect(x + 3, y - 22, x + 7, y - 15, "card", 3)                         # neck
    p.rect(x, y - 25, x + 6, y - 21, "card", 3); p.hline(x, x + 6, y - 25, "card", 4)   # head
    p.rect(x, y - 22, x + 1, y - 21, "card", 2)                             # muzzle
    p.put(x + 3, y - 24, "plastic", 0)
    p.put(x + 5, y - 27, "card", 3); p.put(x + 5, y - 26, "card", 3)       # ear
    for k in range(6):
        p.put(x + 7 + (k % 2), y - 24 + k, "card", 1)                       # mane
    line(p, x + 20, y - 15, x + 23, y - 9, "card", 1)                       # tail
    return (x, y - 27, x + 23, y), 24


def floppies(p, x, y, r):
    floppy(p, x, y - 2, r)
    floppy(p, x + 7, y, random.Random(5))
    return (x, y - 11, x + 16, y), 17


# --- memes (homages redrawn in our palette; listed in docs/WORLD_PROPS.md for review) ---

def meme_doge(p, x, y, r):
    """Homage: the side-eyeing shiba meme, as an abandoned plush sitting in the junk:
    big front-facing head, cream mask and eyebrow dots, eyes glancing to the side."""
    hx, hy = x + 1, y - 19                                                   # head box top-left (11 x 9)
    for ex in (1, 8):                                                        # ears
        p.rect(hx + ex, hy, hx + ex + 1, hy + 2, "warn", 2)
        p.put(hx + ex + (1 if ex == 1 else 0), hy + 2, "paper", 3)
    p.ellipse(x + 8, y - 6, 4.8, 4.6, "warn", 2)                             # body
    p.ellipse(x + 6, y - 6, 2.2, 3.4, "paper", 4)                            # cream chest
    for lx in (x + 3, x + 8):                                                # paws
        p.rect(lx, y - 1, lx + 1, y, "paper", 4)
    p.ellipse(x + 13, y - 7, 1.8, 1.8, "warn", 3); p.put(x + 13, y - 7, "warn", 1)   # curled tail
    p.ellipse(hx + 5, hy + 6, 5.6, 4.0, "warn", 2)                           # head
    p.ellipse(hx + 4, hy + 4, 2.4, 1.2, "warn", 3)                           # lit forehead
    p.ellipse(hx + 5, hy + 7.6, 3.6, 2.2, "paper", 4)                        # cream muzzle / cheeks
    p.put(hx + 3, hy + 3, "paper", 4); p.put(hx + 7, hy + 3, "paper", 4)     # eyebrow dots
    for ex in (hx + 2, hx + 6):                                              # side-eye: white, pupil to the right
        p.put(ex, hy + 5, "paper", 4); p.put(ex + 1, hy + 5, "plastic", 0)
    p.put(hx + 5, hy + 7, "plastic", 0)                                      # nose
    p.put(hx + 4, hy + 8, "paper", 2); p.put(hx + 6, hy + 8, "paper", 2)     # mouth corners
    return (x, hy, x + 15, y), 16


def meme_poptart(p, x, y, r):
    """Homage: the rainbow pop-tart cat, as a broken toy with a faded rainbow."""
    stripes = [("redp", 4), ("warn", 2), ("warn", 4), ("tarp", 3), ("corrupt", 3)]
    for k in range(10):
        dy = 0 if (k // 3) % 2 == 0 else 1
        for i, (m, s) in enumerate(stripes):
            p.put(x + k, y - 9 + i + dy, m, s)
    bx = x + 9
    p.rect(bx, y - 10, bx + 9, y - 3, "card", 3)                             # pastry
    p.rect(bx + 1, y - 9, bx + 8, y - 4, "corrupt", 4)                       # frosting
    for sx, sy in ((bx + 2, y - 8), (bx + 5, y - 7), (bx + 3, y - 5), (bx + 7, y - 6), (bx + 6, y - 9)):
        p.put(sx, sy, "redp", 4)
    hx = bx + 8
    p.rect(hx, y - 8, hx + 5, y - 4, "steel", 3)                              # cat head
    p.put(hx, y - 9, "steel", 3); p.put(hx + 5, y - 9, "steel", 3)           # ears
    p.put(hx + 2, y - 7, "plastic", 0); p.put(hx + 4, y - 7, "plastic", 0)
    p.put(hx + 1, y - 5, "corrupt", 3); p.put(hx + 5, y - 5, "corrupt", 3)
    p.hline(hx + 2, hx + 4, y - 5, "steel", 1)
    for lx in (bx + 1, bx + 3, bx + 6, bx + 8):                              # stubby legs
        p.vline(lx, y - 2, y - 1, "steel", 3)
    p.rect(bx - 1, y - 6, bx, y - 5, "steel", 3)                             # tail
    return (x, y - 10, hx + 5, y), hx + 6 - x


def meme_troll(p, x, y, r):
    """Homage: the troll-face doodle, scribbled on a deleted file (trollface.bak)."""
    w, h = 17, 21
    file_doc(p, x, y, random.Random(1), ext="BAK", w=w, h=h, dot=True)
    top = y - h + 1
    p.rect(x + 2, top + 2, x + w - 3, top + 12, "paper", 3)                  # blank over the lines
    for dx, dy in ((3, 4), (4, 3), (5, 3), (9, 3), (10, 3), (11, 4)):        # brows
        p.put(x + dx, top + dy, "paper", 1)
    p.put(x + 5, top + 5, "paper", 1); p.put(x + 10, top + 5, "paper", 1)   # squint eyes
    for k in range(11):                                                      # huge grin
        dy = 0 if 2 <= k <= 8 else -1 if k in (1, 9) else -2
        p.put(x + 3 + k, top + 9 + dy, "paper", 1)
        if 2 <= k <= 8:
            p.put(x + 3 + k, top + 11, "paper", 1)
    for k in range(2, 9, 2):
        p.put(x + 3 + k, top + 10, "paper", 1)                               # teeth
    p.put(x + 2, top + 6, "paper", 2); p.put(x + w - 4, top + 6, "paper", 2)
    return (x, top, x + w - 1, y), w


# =============================================================== floor decals (walkable, no outline ring)

def doc_sheets(seed):
    """Deleted documents lying flat on the floor (seen from above, foreshortened). Decal: no ring."""
    r = random.Random(seed)
    p = DPix(48, 18)
    for sx, sy, w, h in ((3, 3, 12, 8), (14, 7, 12, 8), (30, 4, 11, 7)):
        p.rect(sx, sy, sx + w - 1, sy + h - 1, "paper", 3)
        p.hline(sx, sx + w - 1, sy, "paper", 4)
        p.hline(sx, sx + w - 1, sy + h - 1, "paper", 1); p.vline(sx + w - 1, sy, sy + h - 1, "paper", 2)
        p.clear(sx + w - 1, sy); p.put(sx + w - 2, sy + 1, "paper", 2)
        for k in range(1, h - 2, 2):
            p.hline(sx + 2, sx + w - 3 - r.randint(0, 3), sy + 1 + k, "paper", 2)
    return p.finish(outline=False)


def hello_printout(seed):
    """Continuous-form printout of the first program everyone writes. Decal: no ring."""
    p = DPix(56, 16)
    x0, y0, w, h = 2, 2, 50, 11
    p.rect(x0, y0, x0 + w - 1, y0 + h - 1, "paper", 3)
    p.hline(x0, x0 + w - 1, y0, "paper", 4); p.hline(x0, x0 + w - 1, y0 + h - 1, "paper", 1)
    for xx in (x0 + 1, x0 + w - 2):
        for yy in range(y0 + 1, y0 + h - 1, 2):
            p.put(xx, yy, "paper", 1)                                         # tractor-feed holes
    for yy in range(y0, y0 + h):
        if yy % 2 == 0:
            p.put(x0 + w - 6, yy, "paper", 2)                                 # perforation
    F.text(p, x0 + 4, y0 + 3, "HELLO WORLD", "paper", 1)
    p.rect(x0 + w, y0 + 2, x0 + w + 2, y0 + h - 2, "paper", 2)              # next fold curling up
    p.vline(x0 + w + 2, y0 + 2, y0 + h - 2, "paper", 1)
    return p.finish(outline=False)


def home_mat(seed):
    """Doormat: there's no place like 127.0.0.1. Decal: no ring."""
    p = DPix(40, 16)
    x0, y0, w, h = 2, 2, 35, 11
    p.rect(x0, y0, x0 + w - 1, y0 + h - 1, "card", 2)
    p.rect(x0 + 1, y0 + 1, x0 + w - 2, y0 + h - 2, "card", 3)
    p.hline(x0, x0 + w - 1, y0 + h - 1, "card", 1)
    for xx in range(x0 + 1, x0 + w - 1, 3):
        p.put(xx, y0 + 1, "card", 4)
    F.text(p, x0 + 3, y0 + 3, "127.0.0.1", "card", 1)
    return p.finish(outline=False)


def data_puddle(seed):
    """Leaked memory pooling on the floor: oily, with a faint data sheen. Decal: no ring."""
    r = random.Random(seed)
    p = DPix(40, 14)
    p.ellipse(20, 7, 18, 5.5, "oil", 1)
    p.ellipse(14 + r.randint(-2, 2), 6, 8, 3, "oil", 2)
    p.hline(10, 16, 5, "oil", 4)
    p.hline(22, 27, 8, "glow", 1); p.put(24, 8, "glow", 2)
    p.put(29 + r.randint(0, 3), 6, "glow", 1)
    return p.finish(outline=False)


def floor_pane(seed):
    """A broken UI window pane lying on the floor. Decal: no ring."""
    p = DPix(30, 10)
    p.new_tag("pane")
    ui_pane(p, 1, 8, random.Random(seed))
    return p.finish(outline=False)


def lan_coil_frame(k=None, n=12):
    """Coiled network cable on the floor (decal: no ring, like gen_junk's coil, same 21 x 9 size);
    with k a packet of light runs once round the outer loop per n frames."""
    p = DPix(24, 12)
    cx, cy = 11, 6
    p.ellipse(cx, cy, 10, 4.5, "rubber", 1)
    for yy in range(p.h):                                                    # floor shows through the middle
        for xx in range(p.w):
            if ((xx - cx) / 5.6) ** 2 + ((yy - cy) / 1.9) ** 2 <= 1:
                p.clear(xx, yy)
    for a in range(120):                                                     # groove between the loops
        t = a / 120 * 2 * math.pi
        p.put(round(cx + 8.2 * math.cos(t)), round(cy + 3.3 * math.sin(t)), "rubber", 0)
    for rx, ry in ((9.3, 3.9), (7.0, 2.6)):                                  # lit upper-left arcs
        for a in range(40):
            t = math.pi + a / 40 * (math.pi * 0.7)
            p.put(round(cx + rx * math.cos(t)), round(cy + ry * math.sin(t)), "rubber", 3)
    p.put(21, 6, "shell", 3)                                                 # plug, where gen_junk's coil ends
    if k is not None:
        ring = []
        for a in range(200):
            t = a / 200 * 2 * math.pi
            pt = (round(cx + 9.1 * math.cos(t)), round(cy + 3.8 * math.sin(t)))
            if pt not in ring:
                ring.append(pt)
        m = len(ring)
        head = int(k * m / n) % m
        for j, s_ in ((0, 4), (1, 3), (2, 2), (3, 1)):
            p.put(*ring[(head - j) % m], "glow", s_)
    return p.finish(crop=k is None, outline=False)

def scatter_dg(seed, w=64, h=26, n=34):
    """gen_junk.scatter with digital bits: paper scraps, a key, a network cable."""
    r = random.Random(seed)
    D.reseed(seed)
    q = Q()
    p = DPix(w, h)
    for _ in range(n):
        x, y = r.randint(1, w - 5), r.randint(1, h - 3)
        mat = r.choice(["steel", "rubber", "plastic", "card", "shell"])
        if mat == "shell" and q.random() < 0.6:
            mat = "paper"                                                     # scraps of deleted files
        p.rect(x, y, x + r.randint(1, 3), y + r.randint(0, 1), mat, r.choice([1, 2, 3]))
    for _ in range(r.randint(1, 2)):
        x0, y0 = r.randint(0, w - 20), r.randint(2, h - 3)
        n_ = r.randint(10, 18)
        for i in range(n_):
            p.put(x0 + i, y0 + (1 if (i // 3) % 2 else 0), "rubber", 1)
        p.put(x0 + n_ - 1, y0 + (1 if ((n_ - 1) // 3) % 2 else 0), "shell", 3)   # network plug at the end
    if r.random() < 0.5:
        p.put(r.randint(3, w - 3), r.randint(2, h - 2), "glow", 3)
    return p.bbox_crop()


# =============================================================== animated strips

def tight(frames):
    """Crop every frame to the union bounding box of all frames (same size, art keeps its place),
    so the strip's bottom row is the prop's base line."""
    pts = [(x, y) for f in frames for y in range(f.h) for x in range(f.w) if f.px[y][x] is not None]
    x0, y0 = min(x for x, _ in pts), min(y for _, y in pts)
    x1, y1 = max(x for x, _ in pts), max(y for _, y in pts)
    out = []
    for f in frames:
        c = Pix(x1 - x0 + 1, y1 - y0 + 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                c.px[y - y0][x - x0] = f.px[y][x]
        out.append(c)
    return out


def anim_strip(frames, crop=False):
    """Frames side by side. crop=True for new props (tight to the art); the dg_a_* mirrors keep
    gen_junk's frame canvases so they swap 1:1."""
    if crop:
        frames = tight(frames)
    w, h = max(f.w for f in frames), max(f.h for f in frames)
    strip = Pix(w * len(frames), h)
    for i, f in enumerate(frames):
        strip.paste(f, i * w + (w - f.w) // 2, h - f.h)
    return strip


def dg_spark(seed):
    """Severed network trunk spitting sparks and loose bits (8 frames, bursts on 0,1,4,6 like a_spark)."""
    frames = []
    for i in range(8):
        r = random.Random(seed * 100 + i)
        p = DPix(30, 22)
        for k in range(20):
            p.put(2 + k, 19 + (1 if (k // 4) % 2 else 0), "rubber", 2)
        p.rect(21, 18, 23, 20, "shell", 3)                                   # torn plug end
        p.put(23, 19, "warn", 3)
        bits = []
        if i in (0, 1, 4, 6):
            nn = 6 if i in (0, 4) else 3
            for _ in range(nn):
                dx, dy = r.randint(-5, 6), r.randint(-9, 1)
                bits.append((23 + dx, 18 + dy, "spark", r.choice([2, 3, 4])))
            bits.append((24, 17, "spark", 4))
        p.finish(crop=False)
        for x, y, m, s in bits:
            p.put(x, y, m, s)
        frames.append(p)
    return anim_strip(frames)


def dg_fan(seed):
    """Cooling fan of the GC zone (4 frames, like a_fan); its housing corner is de-rezzing."""
    frames = []
    for i in range(4):
        p = DPix(18, 20)
        box(p, 2, 18, 14, 4, 14, "steel", front=2, top=3)
        p.ellipse(8, 12, 5, 5, "plastic", 1)
        (ax, ay), (bx, by) = [((-4, 0), (4, 0)), ((-3, -3), (3, 3)), ((0, -4), (0, 4)), ((3, -3), (-3, 3))][i]
        for t in range(9):
            f = t / 8
            p.put(round(8 + ax + (bx - ax) * f), round(12 + ay + (by - ay) * f), "steel", 3)
        p.put(8, 12, "steel", 4)
        rr = random.Random(seed)
        p.post.append(lambda q, rr=rr: derez(q, 14, 0, rr, size=4, drift=(1, -1), n_bits=2))
        frames.append(p.finish(crop=False))
    return anim_strip(frames)


def dg_bugs(seed, n=12):
    """Bugs (beetles) crawling out of a crack in the data and into another one (12 frames).
    Walkable decal: no ring; the beetles are dark so they read on the grey floor."""
    frames = []
    for i in range(n):
        p = DPix(36, 10)
        for xx in range(1, 35):                                              # the crack they use
            if xx < 5 or xx > 30 or xx % 9 in (0, 1):
                p.put(xx, 6 + (1 if xx % 7 < 3 else 0), "oil", 0)
        p.rect(2, 5, 5, 7, "oil", 0); p.put(3, 6, "glow", 1)
        p.rect(30, 5, 33, 7, "oil", 0); p.put(31, 6, "glow", 1)
        for b in range(2):
            pos = 4 + ((i * 2 + b * 12) % 24) + 1
            leg = (i + b) % 2
            by = 4 + (1 if (pos // 6) % 2 else 0)
            pix = []
            for dx in range(4):                                              # shell, split down the middle
                for dy in range(2):
                    s = 4 if (dx, dy) == (1, 0) else 2 if dy == 0 else 1
                    pix.append((pos + dx, by + dy, "plastic", s))
            pix.append((pos + 4, by, "plastic", 0)); pix.append((pos + 4, by + 1, "plastic", 0))   # head
            pix.append((pos + 5, by, "glow", 2))                             # eye
            for lx in (pos, pos + 2):
                pix.append((lx + leg, by - 1, "rubber", 0)); pix.append((lx + 1 - leg, by + 2, "rubber", 0))
            for x, y, m, s in pix:
                if 5 <= x <= 30:
                    p.put(x, y, m, s)
        frames.append(p.finish(crop=False, outline=False))
    return anim_strip(frames, crop=True)


def dg_modem(seed, n=8):
    frames = []
    for i in range(n):
        p = DPix(28, 24)
        p.new_tag("modem")
        modem(p, 3, 21, random.Random(seed), frame=i)
        frames.append(p.finish(crop=False))
    return anim_strip(frames, crop=True)


def dg_lan(seed, n=12):
    return anim_strip([lan_coil_frame(k, n) for k in range(n)], crop=True)


CURSOR = ["#........", "##.......", "###......", "####.....", "#####....", "######...", "#######..",
          "########.", "#####....", "##.##....", "#..##....", "....##...", "....##...", ".....#..."]


def dg_cursor(seed):
    """A mouse cursor stuck in mid-air, bobbing 1 px (4 frames)."""
    frames = []
    for off in (0, 0, 1, 1):
        p = DPix(14, 24)
        for yy, row in enumerate(CURSOR):
            for xx, c in enumerate(row):
                if c == "#":
                    edge = xx == 0 or row[xx - 1] != "#"
                    p.put(3 + xx, 2 + off + yy, "paper", 4 if edge or xx < 3 else 3)
        p.finish(crop=False)
        p.hline(3, 7, 22, "oil", 1); p.hline(4, 6, 23, "oil", 1)              # its shadow on the floor
        frames.append(p)
    return anim_strip(frames, crop=True)


def ring_pixels(cx, cy, rad):
    pts = []
    for a in range(96):
        t = a / 96 * 2 * math.pi - math.pi / 2
        pt = (round(cx + rad * math.cos(t)), round(cy + rad * math.sin(t)))
        if pt not in pts:
            pts.append(pt)
    return pts


def puck(p, cx, y, rw=5):
    """Small projector puck on the floor (the visible source of a hologram)."""
    p.rect(cx - rw, y - 1, cx + rw, y, "steel", 2)
    p.ellipse(cx, y - 2, rw, 1.6, "steel", 3)
    p.hline(cx - rw + 1, cx + rw - 1, y - 3, "steel", 4)
    p.put(cx, y - 2, "glow", 3)


def dg_loading(seed, n=8):
    """Loading ring hovering over a projector puck (8 frames)."""
    frames = []
    for i in range(n):
        p = DPix(16, 24)
        puck(p, 7, 22, 4)
        p.finish(crop=False)
        pts = ring_pixels(7, 8, 4.4)
        m = len(pts)
        head = int(i * m / n)
        for j, pt in enumerate(pts):
            age = (head - j) % m
            s = 4 if age < 2 else 3 if age < 5 else 2 if age < 8 else 1
            p.put(*pt, "glow", s)
        for yy in (15, 17, 19):
            p.put(7, yy, "glow", 1)                                           # thin beam
        frames.append(p)
    return anim_strip(frames, crop=True)


HOLO = [  # generic avatar silhouette (bob haircut, A-line dress), 13 x 27, '#' = body
    "....#####....", "...#######...", "..#########..", "..#########..", "..##.###.##..", "..#########..",
    "..##.....##..", "...#######...", ".....###.....", "...#######...", "..#########..", ".##.#####.##.",
    ".##.#####.##.", ".#..#####..#.", "....#####....", "...#######...", "...#######...", "..#########..",
    "..#########..", ".###########.", ".###########.", "....##.##....", "....##.##....", "....##.##....",
    "....##.##....", "....##.##....", "...###.###...",
]


def dg_holo(seed, n=8):
    """Flickering hologram of a deleted avatar above a projector puck (8 frames):
    steady scanlines, a dim dropout, a horizontal tear, a half dropout."""
    frames = []
    mode = ["ok", "ok", "dim", "ok", "tear", "ok", "half", "ok"]
    for i in range(n):
        p = DPix(24, 36)
        puck(p, 11, 34, 6)
        p.finish(crop=False)
        md = mode[i % len(mode)]
        oy = 3
        for yy, row in enumerate(HOLO):
            if md == "half" and yy < 11 and yy % 2 == 0:
                continue
            shift = 2 if (md == "tear" and 9 <= yy <= 12) else 0
            for xx, c in enumerate(row):
                if c != "#":
                    continue
                edge = xx == 0 or row[xx - 1] != "#"
                s = 3 if edge else (2 if (yy + i) % 2 == 0 else 1)
                if md == "dim":
                    s = 2 if edge else 1
                p.put(5 + xx + shift, oy + yy, "glow", s)
        if md == "tear":
            p.hline(6, 17, oy + 13, "corrupt", 3)
        for k in range(3):
            p.put(10 + k, 31, "glow", 1)
        frames.append(p)
    return anim_strip(frames, crop=True)


def dg_leak(seed, n=8):
    """Memory-leak tank dripping glowing data into a slowly growing-and-resetting puddle (8 frames)."""
    frames = []
    for i in range(n):
        p = DPix(24, 30)
        p.new_tag("tank")
        r = random.Random(seed)
        w, h, x, y = 16, 20, 3, 26
        mat = "steel"
        p.rect(x, y - h + 4, x + w - 1, y, mat, 2)
        p.vline(x + 2, y - h + 5, y - 1, mat, 3); p.vline(x + w - 1, y - h + 4, y, mat, 1)
        p.ellipse(x + w / 2 - 0.5, y - h + 3, w / 2, 3, mat, 3)
        p.rect(x + 6, y - h - 1, x + 9, y - h + 1, "steel", 2)
        p.hline(x + 1, x + w - 2, y - 13, "warn", 3)
        F.text(p, x + 3, y - 11, "MEM", "warn", 3)
        cx = x + 11
        for dx, dy in ((0, -5), (1, -4), (0, -3)):
            p.put(cx + dx, y + dy, mat, 0)
        p.put(cx, y - 2, "glow", 2)
        pw = 2 + i // 3
        p.hline(cx - pw, cx + pw, y + 1, "glow", 1); p.hline(cx - 1, cx + 1, y + 1, "glow", 2)
        del r
        p.finish(crop=False)
        drop_y = [y - 1, y, None, None, y - 1, y, None, None][i]
        if drop_y is not None:
            p.put(cx, drop_y, "glow", 3)
        frames.append(p)
    return anim_strip(frames, crop=True)


def dg_pipe(seed, n=8):
    """Data pipeline (two pipes) with packets of light sliding through long sight glasses (8 frames)."""
    frames = []
    for i in range(n):
        p = DPix(40, 16)
        for k in range(2):
            yy = 13 - k * 5
            x0, x1 = 2 + k * 2, 37 - k
            p.rect(x0, yy - 4, x1, yy, "steel", 2); p.hline(x0, x1, yy - 3, "steel", 3)
            for fx in (x0 + 7, x0 + 22):
                p.vline(fx, yy - 4, yy, "steel", 3); p.vline(fx + 1, yy - 4, yy, "steel", 1)
            gx0, gx1 = x0 + 10, x0 + 20
            p.rect(gx0, yy - 2, gx1, yy - 1, "glow", 1)
            span = gx1 - gx0 + 1
            pos = gx0 + (i * 2 + k * 5) % (span + 2) - 1
            for j, s in ((0, 4), (-1, 3), (-2, 2)):
                if gx0 <= pos + j <= gx1:
                    p.put(pos + j, yy - 2, "glow", s)
            p.ellipse(x0, yy - 2, 2, 2.5, "steel", 1)
            p.put(x0, yy - 2, "glow", 2 if (i + k) % 4 else 3)
        frames.append(p.finish(crop=False))
    return anim_strip(frames, crop=True)


def dg_meme_fine(seed, n=4):
    """Homage: the 'this is fine' dog in a bowler hat, sitting at a table with a mug while the
    junk around it burns (4 frames: flames lick, the dog stays calm)."""
    frames = []
    flames = [(3, 9), (7, 6), (32, 10), (36, 7)]                          # (x, base height): the room around him burns
    for i in range(n):
        r = random.Random(seed * 10 + i)
        p = DPix(40, 32)
        y = 30
        p.hline(5, 16, y - 10, "card", 4); p.hline(5, 16, y - 9, "card", 2)    # table
        p.vline(6, y - 8, y, "card", 2); p.vline(15, y - 8, y, "card", 1)
        p.rect(13, y - 14, 15, y - 11, "paper", 4); p.put(16, y - 13, "paper", 3); p.put(16, y - 12, "paper", 3)   # mug
        p.vline(29, y - 16, y, "card", 2); p.vline(30, y - 16, y, "card", 1)  # chair back
        p.rect(21, y - 8, 29, y - 7, "card", 3); p.vline(22, y - 6, y, "card", 2)   # seat + front leg
        p.rect(22, y - 16, 28, y - 8, "warn", 3)                               # dog body
        p.vline(22, y - 16, y - 8, "warn", 4)
        p.rect(18, y - 8, 23, y - 7, "warn", 3); p.rect(18, y - 6, 19, y - 1, "warn", 3)   # thigh + shin
        p.hline(17, 19, y, "warn", 2)                                          # foot
        p.rect(17, y - 13, 22, y - 12, "warn", 3)                              # arm to the mug
        p.ellipse(24, y - 20, 4.0, 3.6, "warn", 3); p.put(23, y - 22, "warn", 4)   # round head
        p.rect(20, y - 20, 21, y - 18, "warn", 3); p.put(20, y - 20, "plastic", 0)   # short snout + nose
        p.put(23, y - 21, "plastic", 0)                                        # calm eye
        p.hline(21, 23, y - 18, "warn", 1)                                     # small smile
        p.rect(26, y - 21, 27, y - 17, "card", 1)                              # floppy ear
        p.hline(20, 28, y - 24, "card", 1); p.rect(22, y - 27, 27, y - 25, "card", 1)   # bowler hat
        p.hline(22, 26, y - 27, "card", 2)
        p.finish(crop=False)
        p.box0 = None                                                          # flames may leave the furniture's box
        for fx, base in flames:                                                # flames behind everything
            hgt = base + r.randint(-1, 2)
            sway = r.choice([-1, 0, 1])
            for k in range(hgt):
                t = k / max(1, hgt - 1)
                half = 2 if t < 0.35 else 1 if t < 0.75 else 0
                xx = fx + (sway if t > 0.5 else 0)
                m, s = ("redp", 3) if t < 0.2 else ("warn", 3) if t < 0.5 else ("spark", 2) if t < 0.85 else ("spark", 3)
                for dx in range(-half, half + 1):
                    float_put(p, xx + dx, y - k, m, s)
            if r.random() < 0.6:
                float_put(p, fx + r.randint(-1, 1), y - hgt - 2, "spark", 2)   # ember
        for sx, sy in ((4, 6), (8, 4), (33, 7), (13, 3)):                      # smoke under the ceiling
            for dx in range(3):
                float_put(p, sx + dx + (i % 2), sy, "rubber", 2)
        frames.append(p)
    return anim_strip(frames, crop=True)


RICK = [  # tiny dancing man in a coat, 2 poses (hair, face, coat, legs)
    ["..###..", ".#####.", "..#.#..", "..###..", ".#####.", "#.###.#", "..###..", "..#.#..", ".#...#."],
    ["..###..", ".#####.", "..#.#..", "..###..", "#.###..", ".#####.", "..###.#", "..#.#..", "..#..#."],
]


def dg_meme_rick(seed, n=4):
    """Homage: the rickroll - a CRT showing a little man dancing in a trench coat (4 frames)."""
    frames = []
    for i in range(n):
        p = DPix(22, 22)
        box(p, 2, 20, 18, 6, 15, "plastic", front=2, top=3)
        p.rect(4, 8, 15, 18, "glow", 1)
        fig = RICK[(i // 1) % 2]
        ox = 6 + (1 if i in (1, 2) else 0)
        for yy, row in enumerate(fig):
            for xx, c in enumerate(row):
                if c == "#":
                    p.put(ox + xx, 9 + yy, "glow", 4 if yy < 2 else 3)
        p.put(17, 10, "glow", 3); p.put(17, 12, "glow", 2)                   # knobs
        frames.append(p.finish(crop=False))
    return anim_strip(frames, crop=True)


# =============================================================== dumped story singles and calm animations
# Nothing in the recycle bin stands tidy: every single is turned onto the corner it rests on (rot.py),
# propped on or sunk into a low bank of scrap. Story labels (404, EOL, GC) stay readable: small angles.

def _settle(fn, seed, angle, lit=False, labels=True, canvas=160, **kw):
    """Draw a single alone (calm switches applied) and turn it onto its contact corner.
    Returns (Pix, contact point, rng)."""
    r = random.Random(seed)
    D.reseed(seed)
    D.BUDGET.update(subst=0, corrupt=0, wire=0, derez=0, bits=0)
    c = DPix(canvas, canvas)
    c.new_tag("single")
    with calm(lit=lit, labels=labels):
        fn(c, canvas // 3, canvas * 2 // 3, r, **kw)
    c.tag, c.post = None, []
    x0, _y0, x1, y1 = _pix_bbox(c)
    pivot = (x1 + 1, y1 + 1) if angle > 0 else (x0, y1 + 1)
    if not angle:
        return c, pivot, r
    q, (ox, oy) = rot.rotate(c, angle, pivot)
    return q, (pivot[0] - ox, pivot[1] - oy), r


def _span(q, ct, X):
    x0, _y0, x1, _y1 = _pix_bbox(q)
    return X - ct[0] + x0, X - ct[0] + x1


def dumped_dialog(seed=2, angle=-9):
    """The 404 dialog that came down the chute with her: tipped back onto a bank of scrap, its shattered
    corner sunk in it. Scale-2 glyphs, so the 404 survives the small turn."""
    q, ct, r = _settle(lambda p, x, y, r: dialog(p, x, y, r, msg="404", shards=False, title=False), seed, angle)
    p = DPix(110, 80)
    X, Y = 24, 72
    L, R = _span(q, ct, X)
    mid = L + (R - L) * 0.45
    debris_skirt(p, int(mid), R + 7, Y, 8, r)                         # what it fell onto
    pts = paste_at(p, q, ct, X, Y)
    t = math.tan(math.radians(-angle))
    bury(p, pts, lambda x: Y - (x - L) * t - 3 if x > mid + 3 else Y + 1, r)
    p.outline()
    return p.bbox_crop()


def dumped_softbox(seed=9, angle=-5):
    """Her discontinued software box, dropped on its back beside the rug, a little askew."""
    q, ct, r = _settle(lie_softbox, seed, angle)
    p = DPix(60, 50)
    X, Y = 10, 44
    L, R = _span(q, ct, X)
    debris_skirt(p, R - 7, R + 2, Y, 2, r)                            # a scrap under the lifted end
    paste_at(p, q, ct, X, Y)
    p.outline()
    return p.bbox_crop()


def dumped_recycle(seed=5, angle=21):
    """The recycle bin's intake can, shoved over by the heap: leaning hard on its bottom corner, propped
    on scrap, crumpled files spilled out in front of it."""
    q, ct, r = _settle(recycle_bin, seed, angle, labels=False)
    p = DPix(100, 80)
    X, Y = 66, 70
    L, R = _span(q, ct, X)
    debris_skirt(p, L - 2, L + 12, Y, 9, r)                           # scrap under the lifted side
    paste_at(p, q, ct, X, Y)
    for dx, dy in ((-11, 2), (-3, 3)):                                # spilled crumpled files
        paper_wad(p, L + dx, Y + dy, r)
    p.outline()
    return p.bbox_crop()


def dumped_gcbot(seed=11, angle=5):
    """The garbage collector parked between cycles, one track up on a scrap bank (so it sits tilted)."""
    q, ct, r = _settle(gc_robot, seed, angle, labels=True)
    p = DPix(80, 60)
    X, Y = 64, 54
    L, _R = _span(q, ct, X)
    debris_skirt(p, L - 4, L + 11, Y, 4, r)
    paste_at(p, q, ct, X, Y)
    p.outline()
    return p.bbox_crop()


def dg_tv(seed, angle=13):
    """Error-dialog CRT knocked onto a lump of scrap, its screen still flickering (6 frames, same
    brightness pattern as a_tv). The only screen in the room besides the one on the bit bucket."""
    levels = [1, 2, 1, 3, 1, 0]
    r = random.Random(seed)
    frames = []
    for lv in levels:
        c = DPix(30, 30)
        box(c, 4, 26, 15, 6, 11, "plastic", front=2, top=3)
        screen(c, 6, 18, 15, 24, "err")
        dim_screen(c, 6, 18, 15, 24, {0: 0, 1: 2, 2: 3, 3: 4}[lv])
        q, (ox, oy) = rot.rotate(c, angle, (19, 27))
        p = DPix(40, 34)
        rr = random.Random(seed)
        debris_skirt(p, 3, 14, 31, 4, rr)
        paste_at(p, q, (19 - ox, 27 - oy), 30, 32)
        frames.append(p.finish(crop=False))
    del r
    return anim_strip(frames, crop=True)


def dg_rack(seed, angle=-9):
    """Legacy server leaning back against the heap (on its bottom-left corner, the other propped on
    scrap); a few status lights still blink - dim, the only LEDs left on in the room (6 frames)."""
    r0 = random.Random(seed)
    leds = {1: (0, False), 3: (2, False), 6: (1, True), 8: (4, False)}   # slot: (phase, red)
    frames = []
    for i in range(6):
        c = DPix(24, 40)
        box(c, 4, 36, 12, 4, 27, "steel", front=1, top=3)
        for k in range(9):
            yy = 13 + k * 3
            if k == 4:                                                       # half-pulled drive caddy
                c.hline(5, 14, yy - 1, "steel", 4); c.hline(5, 14, yy, "plastic", 2)
                continue
            c.hline(6, 13, yy, "plastic", 1)
            if k in leds:
                ph, red = leds[k]
                on = (i + ph) % 3 != 0
                c.put(13, yy, "redp" if red else "glow", (4 if red else 3) if on else 1)
        c.put(7, 19, "shell", 3)
        for kk, yy in enumerate(range(20, 36)):
            c.put(7 - (1 if (kk // 3) % 2 else 0), yy, "rubber", 1)
        q, (ox, oy) = rot.rotate(c, angle, (4, 37))
        p = DPix(36, 44)
        debris_skirt(p, 14, 24, 40, 3, random.Random(seed))
        paste_at(p, q, (4 - ox, 37 - oy), 8, 41)
        frames.append(p.finish(crop=False))
    del r0
    return anim_strip(frames, crop=True)


# =============================================================== targets

ANIM_INFO = {  # name: (frames, fps, meaning) - used by the integration step and the catalog
    "dg_a_spark.png": (8, 10, "severed network trunk sparking"), "dg_a_tv.png": (6, 6, "flickering error-dialog CRT"),
    "dg_a_rack.png": (6, 5, "legacy server blinking"), "dg_a_fan.png": (4, 12, "cooling fan"),
    "dg_a_bugs.png": (12, 8, "bugs crawling between cracks"), "dg_a_modem.png": (8, 8, "dial-up modem handshake LEDs"),
    "dg_a_lan.png": (12, 12, "packet running along a coiled LAN cable"), "dg_a_cursor.png": (4, 4, "stuck cursor bobbing"),
    "dg_a_loading.png": (8, 12, "loading ring"), "dg_a_holo.png": (8, 8, "flickering avatar hologram"),
    "dg_a_leak.png": (8, 8, "memory-leak tank dripping"), "dg_a_pipe.png": (8, 10, "data pipeline packets"),
    "dg_a_meme_fine.png": (4, 8, "'this is fine' homage"), "dg_a_meme_rick.png": (4, 6, "rickroll homage"),
}

# Calm heaps (dheap): the gen_junk names and seeds, about a third of the parts (bigger, fewer, all
# tumbled and half buried). Room-wide accent budget: 3 quiet de-rez spots and 1 missing-texture patch.
HEAP_ACCENTS = {"dg_c_main.png": dict(derez=1, checker_at=12), "dg_c_ridge.png": dict(derez=1),
                "dg_e_5.png": dict(derez=1)}


def _calm_n(n):
    return max(2, round(n / 4))


MIRROR = {}  # dg_<gen_junk name>: builder (same file names, so the room layout swaps them 1:1)
MIRROR.update({f"dg_{n}": (lambda t=t, s=s, k=k, w=w, pk=pk, a=HEAP_ACCENTS.get(f"dg_{n}", {}):
                           dheap(s, DTHEMES[t], n=_calm_n(k), w=w, peak=pk, **a))
               for n, (t, s, k, w, pk) in J.ROOM_PILES.items()})
MIRROR.update({f"dg_{n}": (lambda kinds=kinds, s=s, k=k, w=w, pk=pk, a=HEAP_ACCENTS.get(f"dg_{n}", {}):
                           dheap(s, kinds, n=_calm_n(k), w=w, peak=pk, **a))
               for n, (kinds, s, k, w, pk) in J.MIX.items()})
MIRROR.update({f"dg_{n}": (lambda s=s, w=w, pk=pk, k=k, a=HEAP_ACCENTS.get(f"dg_{n}", {}):
                           dheap(s, ALL_KINDS, n=_calm_n(k), w=w, peak=pk, **a))
               for n, (s, w, pk, k) in J.EDGES.items()})
LEAN_STACKS = {  # name: (seed, [(kind, pose, angle, dx, sink)], lit top) - towers that lean and could topple
    "dg_t_amp_tower.png": (24, [("amp", "tilt", 6, 0, 0), ("amp", "tilt", 15, 3, 2), ("monitor", "tilt", 30, 9, 2)], False),
    "dg_t_crates.png": (22, [("crate", "lie", -3, 0, 0), ("crate", "tilt", -17, -1, 2), ("speaker", "tilt", -24, 13, "ground")], False),
    "dg_t_rack_monitor.png": (23, [("pallet", "tilt", 3, 0, 0), ("rack", "lie", -8, 1, 2)], False),
    "dg_t_barrel_tv.png": (21, [("barrel", "tilt", -5, 0, 0),
                                ("tv", "tilt", 12, 1, 2, lambda p, x, y, r: err_tv(p, x, y, r, kind="err"))], True),
}
MIRROR.update({n: (lambda s=s, sp=sp, lt=lt: dstack_lean(s, sp, lit_top=lt)) for n, (s, sp, lt) in LEAN_STACKS.items()})
_SINGLE_FN = {"s_worklamp.png": None, "s_mic.png": "mic", "s_rhead.png": "rhead", "s_barrel.png": "barrel",
              "s_tv.png": "tv", "s_spot.png": "spot", "s_speaker.png": "speaker"}


def _worklamp(p, x, y, r):
    """Work lamp of the GC crew. Kept identical to gen_junk's: it is a light source whose bulb
    position the lighting is tuned to, and it is the crew's tool, not deleted data."""
    return J.work_lamp(p, x, y, r)


for _n, _k in _SINGLE_FN.items():
    _fn = _worklamp if _k is None else DPARTS[_k]
    MIRROR[f"dg_{_n}"] = (lambda fn=_fn, s=J.SINGLES[_n][1], wl=_k is None: dsingle(fn, s, budget=not wl))
MIRROR.update({f"dg_{n}": (lambda s=s: scatter_dg(s)) for n, s in J.DECALS.items()})
MIRROR.update({
    "dg_f_puddle1.png": lambda: data_puddle(1), "dg_f_puddle2.png": lambda: data_puddle(2),
    "dg_f_plate1.png": lambda: floor_pane(3), "dg_f_coil1.png": lambda: lan_coil_frame(None),
    "dg_a_spark.png": lambda: dg_spark(1), "dg_a_tv.png": lambda: dg_tv(2), "dg_a_rack.png": lambda: dg_rack(3),
    "dg_a_fan.png": lambda: dg_fan(4),
    "dg_pile_a.png": lambda: dheap(11, ["crate", "crate", "tv", "amp"], n=5),
    "dg_pile_b.png": lambda: dheap(23, ["amp", "rack", "amp", "crate"], n=5),
    "dg_pile_c.png": lambda: dheap(37, ["rack", "tv", "crate", "crate"], n=7, w=140, peak=38),
    "dg_crate.png": lambda: dsingle(archive, 3), "dg_amp.png": lambda: dsingle(driver_amp, 3),
    "dg_rack.png": lambda: dsingle(legacy_rack, 3), "dg_tv.png": lambda: dsingle(err_tv, 3),
})

NEW = {  # new digital-native props
    "dg_s_dialog_err.png": lambda: dsingle(dialog, 1, w=60, h=40),
    "dg_s_dialog_404.png": lambda: dumped_dialog(2),
    "dg_s_folder.png": lambda: dsingle(big_folder, 3, w=64, h=40),
    "dg_s_files.png": lambda: dsingle(_files, 4, w=64, h=30),
    "dg_s_recycle.png": lambda: dumped_recycle(5),
    "dg_s_spam.png": lambda: dsingle(spam_pyramid, 6, w=50, h=34),
    "dg_s_cookiejar.png": lambda: dsingle(cookie_jar, 7, w=40, h=32),
    "dg_s_missing.png": lambda: dsingle(lambda p, x, y, r: missing_cube(p, x, y, r, s=13), 8, w=30, h=30),
    "dg_s_softbox.png": lambda: dumped_softbox(9),
    "dg_s_captcha.png": lambda: dsingle(captcha_panel, 10, w=36, h=44),
    "dg_s_gcbot.png": lambda: dumped_gcbot(11),
    "dg_s_parcels.png": lambda: dsingle(parcels, 12, w=60, h=34),
    "dg_s_cache.png": lambda: dsingle(cache_box, 13, w=32, h=30),
    "dg_s_keys_undo.png": lambda: dsingle(keys_undo, 14, w=40, h=24),
    "dg_s_key_any.png": lambda: dsingle(lambda p, x, y, r: keycap(p, x, y, r, "ANY"), 15, w=30, h=20),
    "dg_s_teapot.png": lambda: dsingle(teapot, 16, w=34, h=24),
    "dg_s_duck.png": lambda: dsingle(duck, 17, w=24, h=18),
    "dg_s_trojan.png": lambda: dsingle(trojan, 18, w=36, h=36),
    "dg_s_floppies.png": lambda: dsingle(floppies, 19, w=30, h=20),
    "dg_s_modem.png": lambda: dsingle(modem, 20, w=34, h=24),
    "dg_s_meme_doge.png": lambda: dsingle(meme_doge, 21, w=28, h=28),
    "dg_s_meme_poptart.png": lambda: dsingle(meme_poptart, 22, w=36, h=20),
    "dg_s_meme_troll.png": lambda: dsingle(meme_troll, 23, w=30, h=30),
    "dg_f_docs.png": lambda: doc_sheets(1),
    "dg_f_hello.png": lambda: hello_printout(2),
    "dg_f_home.png": lambda: home_mat(3),
    "dg_a_bugs.png": lambda: dg_bugs(1), "dg_a_modem.png": lambda: dg_modem(2), "dg_a_lan.png": lambda: dg_lan(3),
    "dg_a_cursor.png": lambda: dg_cursor(4), "dg_a_loading.png": lambda: dg_loading(5),
    "dg_a_holo.png": lambda: dg_holo(6), "dg_a_leak.png": lambda: dg_leak(7), "dg_a_pipe.png": lambda: dg_pipe(8),
    "dg_a_meme_fine.png": lambda: dg_meme_fine(9), "dg_a_meme_rick.png": lambda: dg_meme_rick(10),
}


def _files(p, x, y, r):
    """Three deleted files leaning together: .TMP, .BAK, .EXE."""
    file_doc(p, x, y - 2, r, ext="TMP", w=15, h=19, dot=True)
    file_doc(p, x + 16, y, r, ext="BAK", w=15, h=17, dot=True)
    file_doc(p, x + 32, y - 1, r, ext="EXE", w=15, h=20, dot=True)
    return (x, y - 21, x + 46, y), 47


TARGETS = {**MIRROR, **NEW}


# =============================================================== preview sheets

def _label_img(text, color=(200, 200, 205, 255)):
    p = Pix(F.text_width(text) + 2, 7)
    F.text(p, 1, 1, text, "shell", 4)
    im = p.image()
    return im


def sheet(items, path, bg=(46, 46, 52, 255), scale=3, max_w=640, gap=8, title=None):
    """items: [(caption, PIL image)] laid out in rows (bottom-aligned), captions under each, then x scale."""
    rows, row, rw = [], [], 0
    for cap, im in items:
        cw = max(im.width, F.text_width(cap.replace("_", "-")) + 2)
        if row and rw + cw + gap > max_w:
            rows.append(row); row, rw = [], 0
        row.append((cap, im, cw)); rw += cw + gap
    if row:
        rows.append(row)
    heights = [max(im.height for _c, im, _w in r) + 10 for r in rows]
    W = max(sum(cw + gap for _c, _i, cw in r) for r in rows) + gap
    H = sum(heights) + gap * (len(rows) + 1) + (10 if title else 0)
    out = Image.new("RGBA", (W, H), bg)
    y = gap + (10 if title else 0)
    if title:
        out.alpha_composite(_label_img(title), (gap, 2))
    for r, hh in zip(rows, heights):
        x = gap
        for cap, im, cw in r:
            out.alpha_composite(im, (x, y + hh - 10 - im.height))
            out.alpha_composite(_label_img(cap.replace("_", "-")), (x, y + hh - 8))
            x += cw + gap
        y += hh + gap
    out = out.resize((W * scale, H * scale), Image.NEAREST)
    out.save(path)
    print("preview", path, out.size)


def before_after(seed=7):
    items = []
    for k in REINTERPRETED:
        for s in (seed, seed + 1):
            a = Pix(60, 60)
            J.PARTS[k](a, 8, 50, random.Random(s))
            a.outline()
            items.append((f"{k}", a.bbox_crop().image()))
            D.BUDGET.update(corrupt=1, wire=1, derez=1, bits=1)
            D.reseed(s * 31 + len(k))
            b = DPix(60, 64)
            b.new_tag(k)
            {"crate": archive, "tire": disc_stack}.get(k, DPARTS[k])(b, 8, 54, random.Random(s))
            b.tag = None
            items.append(("-> dg", b.finish().image()))
    return items


def scale_sheet(imgs, path):
    """SeeU at 1x vs props at 3x on a crop of the real basement floor, bases on one line."""
    floor = Image.open("assets/env/basement/room_floor.png").convert("RGBA")
    seeu = Image.open("assets/characters/seeu/rotations/south.png").convert("RGBA")
    sb = seeu.getbbox()
    gap = 6
    total = sum(im.width for _n, im in imgs) + gap * (len(imgs) + 1) + 40
    rows, row, rw = [], [], 0
    for n, im in imgs:
        if row and rw + im.width + gap > 300:
            rows.append(row); row, rw = [], 0
        row.append((n, im)); rw += im.width + gap
    rows.append(row)
    rowh = [max(46, max(im.height for _n, im in r) + 6) for r in rows]
    W, H = 340, sum(rowh) + 8
    del total
    bg = Image.new("RGBA", (W, H))
    fx, fy, tw, th = 16, 66, 96, 48                                       # plain tiled floor left of the rug
    for yy in range(0, H, th):
        for xx in range(0, W, tw):
            bg.alpha_composite(floor.crop((fx, fy, fx + tw, fy + th)), (xx, yy))
    y = 4
    base_lines = []
    for r, hh in zip(rows, rowh):
        x = 36
        base = y + hh - 3
        base_lines.append(base)
        for _n, im in r:
            bg.alpha_composite(im, (x, base - im.height))
            x += im.width + gap
        y += hh
    big = bg.resize((W * 3, H * 3), Image.NEAREST)
    for base in base_lines:
        big.alpha_composite(seeu, (8, base * 3 - sb[3]))
    big.save(path)
    print("preview", path, big.size)


def calm_items():
    """Lying drawings, posed (tilted / lying / fallen / flipped) parts, a buried heap, leaning stacks and
    the dumped story singles - the calm-room vocabulary at a glance."""
    items = []
    for k, fn in LIE.items():
        c = DPix(70, 60)
        D.reseed(1)
        fn(c, 10, 50, random.Random(3))
        c.outline()
        items.append((f"lie {k}", c.bbox_crop().image()))
    for kind, pose, ang in (("crate", "tilt", 18), ("crate", "tilt", -34), ("amp", "lie", 9), ("rack", "tilt", -24),
                            ("tv", "lie", -7), ("chair", "flip", 190), ("ladder", "fall", 88), ("rtorso", "lie", 6),
                            ("pipes", "slump", 9), ("monitor", "tilt", 30), ("barrel", "lie", -5), ("spot", "flip", 172)):
        D.reseed(2)
        q, _ct = posed(kind, random.Random(5), pose=pose, angle=ang)
        q.outline()
        items.append((f"{kind} {pose} {ang}", q.bbox_crop().image()))
    for n in ("dg_e_5.png", "dg_c_small1.png", "dg_c_small2.png"):
        items.append((n[3:-4] + " heap", MIRROR[n]().image()))
    for n in LEAN_STACKS:
        items.append((n[3:-4], MIRROR[n]().image()))
    for n in ("dg_s_dialog_404.png", "dg_s_softbox.png", "dg_s_recycle.png", "dg_s_gcbot.png"):
        items.append((n[3:-4], NEW[n]().image()))
    for n, mk in (("dg_a_tv.png", MIRROR["dg_a_tv.png"]), ("dg_a_rack.png", MIRROR["dg_a_rack.png"]),
                  ("dg_a_meme_fine.png", NEW["dg_a_meme_fine.png"])):
        im = mk().image()
        fr = ANIM_INFO[n][0]
        items.append((n[3:-4] + " f0", im.crop((0, 0, im.width // fr, im.height))))
    return items


def previews(d):
    os.makedirs(d, exist_ok=True)
    sheet(calm_items(), os.path.join(d, "e_calm_parts.png"), max_w=600, title="CALM: LYING / TILTED / BURIED / LEANING")
    sheet(before_after(), os.path.join(d, "a_before_after.png"), max_w=560, title="GEN-JUNK PART -> DIGITAL")
    new_items = []
    for n, mk in NEW.items():
        new_items.append((n[3:-4], mk().image()))
    sheet(new_items, os.path.join(d, "b_new_props.png"), max_w=600, title="NEW DIGITAL PROPS")
    piles = []
    for n in list(J.ROOM_PILES) + list(J.MIX) + list(J.STACKS) + list(J.EDGES):
        piles.append((n[:-4], MIRROR[f"dg_{n}"]().image()))
    sheet(piles, os.path.join(d, "c_piles.png"), max_w=640, title="DIGITAL ROOM PILES")
    singles = [(n[3:-4], MIRROR[n]().image()) for n in MIRROR if n.startswith(("dg_s_", "dg_a_", "dg_f_", "dg_d_"))]
    sheet(singles, os.path.join(d, "c2_singles_anims.png"), max_w=600, title="DIGITAL SINGLES / ANIMS / DECALS")
    orig = []
    for n in ("c_main.png", "c_ridge.png", "z_robot_1.png", "z_tvs_1.png"):
        orig.append((n[:-4], Image.open(f"assets/env/basement/code/{n}").convert("RGBA")))
        orig.append(("dg-" + n[:-4], MIRROR[f"dg_{n}"]().image()))
    sheet(orig, os.path.join(d, "c3_pile_before_after.png"), max_w=440, title="PILE BEFORE / AFTER")
    sc = []
    for n in ("dg_s_recycle.png", "dg_s_folder.png", "dg_s_dialog_err.png", "dg_s_gcbot.png", "dg_s_captcha.png",
              "dg_s_spam.png", "dg_s_cookiejar.png", "dg_s_softbox.png", "dg_s_missing.png", "dg_s_trojan.png",
              "dg_s_files.png", "dg_s_parcels.png", "dg_s_meme_doge.png", "dg_s_teapot.png"):
        sc.append((n, NEW[n]().image()))
    for n in ("dg_a_holo.png", "dg_a_cursor.png", "dg_a_loading.png", "dg_a_modem.png"):
        im = NEW[n]().image()
        fr = ANIM_INFO[n][0]
        sc.append((n, im.crop((0, 0, im.width // fr, im.height))))
    for n in ("dg_c_small1.png", "dg_t_barrel_tv.png", "dg_e_7.png"):
        sc.append((n, MIRROR[n]().image()))
    for n in ("dg_a_meme_fine.png", "dg_s_meme_poptart.png", "dg_s_keys_undo.png", "dg_s_duck.png"):
        im = NEW[n]().image()
        fr = ANIM_INFO.get(n, (1,))[0]
        sc.append((n, im.crop((0, 0, im.width // fr, im.height))))
    scale_sheet(sc, os.path.join(d, "d_scale_vs_seeu.png"))


def main(argv):
    out = OUT_DEFAULT
    force = set()
    preview = None
    it = iter(argv)
    for a in it:
        if a.startswith("--out="):
            out = a.split("=", 1)[1]
        elif a.startswith("--preview="):
            preview = a.split("=", 1)[1]
        elif a == "--force":
            force.update(it)
    if preview:
        previews(preview)
        return
    os.makedirs(out, exist_ok=True)
    for name, make in TARGETS.items():
        path = os.path.join(out, name)
        if os.path.exists(path) and name not in force:
            print("kept", path)
            continue
        make().image().save(path)
        print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1:])
