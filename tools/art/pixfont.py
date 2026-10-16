"""Tiny 3x5 pixel font for labels drawn into a Pix (native res, legible at 3x).

  from pixfont import text, text_width, label
  text(p, x, y, ".ZIP", "paper", 1)            # top-left of the first glyph at (x, y)
  label(p, x, y, "404")                        # paper plate with 1 px padding + dark ink

Upper case only (lower case is mapped to upper case). Most glyphs are 3 wide, a few
punctuation marks are narrower; glyphs are separated by 1 px. Height is always 5.
`scale=2` draws each font pixel as a 2x2 block (big signs), still on the native grid.
"""

_G = {
    "A": ".#. #.# ### #.# #.#", "B": "##. #.# ##. #.# ##.", "C": ".## #.. #.. #.. .##",
    "D": "##. #.# #.# #.# ##.", "E": "### #.. ##. #.. ###", "F": "### #.. ##. #.. #..",
    "G": ".## #.. #.# #.# .##", "H": "#.# #.# ### #.# #.#", "I": "### .#. .#. .#. ###",
    "J": "..# ..# ..# #.# .#.", "K": "#.# #.# ##. #.# #.#", "L": "#.. #.. #.. #.. ###",
    "M": "#.# ### ### #.# #.#", "N": "##. #.# #.# #.# #.#", "O": ".#. #.# #.# #.# .#.",
    "P": "##. #.# ##. #.. #..", "Q": ".#. #.# #.# ##. .##", "R": "##. #.# ##. #.# #.#",
    "S": ".## #.. .#. ..# ##.", "T": "### .#. .#. .#. .#.", "U": "#.# #.# #.# #.# ###",
    "V": "#.# #.# #.# #.# .#.", "W": "#.# #.# ### ### #.#", "X": "#.# #.# .#. #.# #.#",
    "Y": "#.# #.# .#. .#. .#.", "Z": "### ..# .#. #.. ###",
    "0": "### #.# #.# #.# ###", "1": ".#. ##. .#. .#. ###", "2": "##. ..# .#. #.. ###",
    "3": "##. ..# .#. ..# ##.", "4": "#.# #.# ### ..# ..#", "5": "### #.. ##. ..# ##.",
    "6": ".## #.. ### #.# ###", "7": "### ..# .#. .#. .#.", "8": "### #.# ### #.# ###",
    "9": "### #.# ### ..# ##.",
    ".": ". . . . #", ":": ". # . # .", "!": "# # # . #", "'": "# # . . .",
    "?": "##. ..# .#. ... .#.", "-": "... ... ### ... ...", "+": "... .#. ### .#. ...",
    "%": "#.# ..# .#. #.. #.#", "/": "..# ..# .#. #.. #..", "_": "... ... ... ... ###",
    "^": ".#. #.# ... ... ...", "<": "..# .#. #.. .#. ..#", ">": "#.. .#. ..# .#. #..",
    "(": ".# #. #. #. .#", ")": "#. .# .# .# #.", "=": "... ### ... ### ...",
    "#": "#.# ### #.# ### #.#", "$": ".## ##. .#. .## ##.", "*": "... #.# .#. #.# ...",
    " ": ".. .. .. .. ..",
}
GLYPHS = {ch: [row for row in rows.split()] for ch, rows in _G.items()}
HEIGHT = 5


def text_width(s, scale=1):
    s = s.upper()
    if not s:
        return 0
    return (sum(len(GLYPHS.get(c, GLYPHS["?"])[0]) for c in s) + len(s) - 1) * scale


def text(p, x, y, s, mat, step, scale=1):
    """Draws s with its top-left at (x, y). Returns the width drawn."""
    cx = x
    for c in s.upper():
        g = GLYPHS.get(c, GLYPHS["?"])
        for gy, row in enumerate(g):
            for gx, ch in enumerate(row):
                if ch == "#":
                    for sy in range(scale):
                        for sx in range(scale):
                            p.put(cx + gx * scale + sx, y + gy * scale + sy, mat, step)
        cx += (len(g[0]) + 1) * scale
    return cx - x - scale


def label(p, x, y, s, plate=("paper", 4), ink=("paper", 1), pad=1, edge=None):
    """A plate (sticker / stencil board) with text on it; top-left at (x, y).
    edge: optional (mat, step) for a 1 px darker bottom/right lip so the plate reads as a separate sheet.
    Returns the plate rect (x0, y0, x1, y1)."""
    w = text_width(s) + 2 * pad
    h = HEIGHT + 2 * pad
    p.rect(x, y, x + w - 1, y + h - 1, *plate)
    if edge:
        p.hline(x, x + w - 1, y + h - 1, *edge)
        p.vline(x + w - 1, y, y + h - 1, *edge)
    text(p, x + pad, y + pad, s, *ink)
    return (x, y, x + w - 1, y + h - 1)
