"""Widens the tower in the upper half of the left panel's illustration (a PixelLab image) so it is as wide as
the lower half: PixelLab keeps drawing the upper floors narrower than asked (docs/ASSETS.md).

The facade is a piano roll - horizontal lanes of note bars - so repeating a column of it only lengthens the
lanes and reads as the same building, wider. Every row gets the same number of extra columns (N), so whatever
stands right of the tower (signs, the elevator lattice) moves right as one piece; where they go is chosen per
band of rows so round and framed things (the record windows, the concert screen, the VIP lettering) are never
cut. Then the picture is cropped back to 240 so the tower's edges and the lattice line up with the lower half.

  python tools/art/widen_stack_top.py <top.png> <out.png>
"""
import sys

from PIL import Image

N = 40                                       # columns added to every row
CROP_X = 27                                  # then cropped from the left (aligns the edges with the lower half)


def spread(x0, x1, n):
    """n insertion columns spread evenly over [x0, x1]."""
    return [round(x0 + (x1 - x0) * (i + 0.5) / n) for i in range(n)]


# row bands (native rows of the 240x540 top half) -> the columns repeated in them (len == N, repeats allowed)
BANDS = [
    (0, 106, spread(80, 160, N)),                                     # sky and the sloped crown
    (106, 130, [69] * 6 + [90] * 7 + [111] * 7 + [132] * 7 + [153] * 7 + [173] * 6),   # record band: only the gaps
                                                                      # between the discs (measured: dark in every row)
    (130, 332, spread(80, 160, N)),                                   # platinum facade
    (332, 356, spread(64, 100, 20) + spread(142, 172, 20)),           # VIP ring, around the lettering
    (356, 380, spread(66, 170, N)),                                   # gold floors above the screen
    (380, 468, spread(70, 100, 20) + spread(135, 165, 20)),           # the screen widens too, the note untouched
    (468, 540, spread(66, 170, N)),                                   # gold floors into the clouds
]


def widen(im):
    im = im.convert("RGB")
    w, h = im.size
    src = im.load()
    out = Image.new("RGB", (w + N, h))
    dst = out.load()
    for y0, y1, cols in BANDS:
        assert len(cols) == N, (y0, len(cols))
        extra = {}
        for c in cols:
            extra[c] = extra.get(c, 0) + 1
        for y in range(y0, min(y1, h)):
            xo = 0
            for x in range(w):
                for _ in range(1 + extra.get(x, 0)):
                    dst[xo, y] = src[x, y]
                    xo += 1
    out = out.crop((CROP_X, 0, CROP_X + w, h))
    # touch-up: PixelLab left the P of "VIP" open (it read VIF) - close its bowl with the letter's own colour
    px = out.load()
    for xy in ((117, 341), (117, 342)):
        px[xy] = px[113, 339]
    return out


if __name__ == "__main__":
    widen(Image.open(sys.argv[1])).save(sys.argv[2])
    print("saved", sys.argv[2])
