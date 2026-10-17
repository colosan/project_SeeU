"""Cuts SeeU's front view out of the official 15th-anniversary design sheet for the right panel's standing
illustration (scripts/ui/info_panel.gd). Input and output both live in /reference/, which is gitignored:
official art never goes into the repository (CLAUDE.md, Git).

  python tools/art/cut_standing.py [reference/seeu_15th_design_sheet.webp]
  -> reference/seeu_standing.png

Steps: crop the front figure, flood-fill the white paper from the crop's border to transparent, keep only the
largest connected shape (drops the notes, swatches and badges drawn around her), soften the edge so no white
fringe shows on the dark panel, trim to the figure.
"""
import sys
from collections import deque

import numpy as np
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "reference/seeu_15th_design_sheet.webp"
OUT = "reference/seeu_standing.png"
CROP = (95, 0, 515, 915)          # front view on the 1000x1000 sheet (x0, y0, x1, y1)
PAPER = 232                       # min(R, G, B) above this counts as paper (if it touches the paper)
EDGE = 200                        # light pixels next to the paper get partial alpha down to this

im = Image.open(SRC).convert("RGB").crop(CROP)
a = np.asarray(im).astype(np.int16)
h, w, _ = a.shape
light = a.min(axis=2)

# 1. paper = light pixels connected to the crop border
paper = np.zeros((h, w), bool)
q = deque([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
          + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
while q:
    x, y = q.popleft()
    if paper[y, x] or light[y, x] <= PAPER:
        continue
    paper[y, x] = True
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < w and 0 <= ny < h and not paper[ny, nx]:
            q.append((nx, ny))

# 2. keep the largest shape that is not paper (the figure)
label = np.zeros((h, w), np.int32)
sizes = [0]
for sy in range(h):
    for sx in range(w):
        if paper[sy, sx] or label[sy, sx]:
            continue
        n = len(sizes)
        sizes.append(0)
        q = deque([(sx, sy)])
        label[sy, sx] = n
        while q:
            x, y = q.popleft()
            sizes[n] += 1
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and not paper[ny, nx] and not label[ny, nx]:
                    label[ny, nx] = n
                    q.append((nx, ny))
keep = label == int(np.argmax(sizes))

# 3. alpha: solid inside; light pixels on the rim fade out so the paper's white does not halo
alpha = np.where(keep, 255, 0).astype(np.float32)
rim = keep & (np.roll(~keep, 1, 0) | np.roll(~keep, -1, 0) | np.roll(~keep, 1, 1) | np.roll(~keep, -1, 1))
fade = np.clip((PAPER + 8 - light) / float(PAPER + 8 - EDGE), 0.0, 1.0)
alpha[rim] *= fade[rim]

rgba = np.dstack([a.astype(np.uint8), alpha.astype(np.uint8)])
out = Image.fromarray(rgba, "RGBA")
out = out.crop(out.getbbox())
out.save(OUT)
print(f"saved {OUT} {out.size}, {len(sizes) - 1} shapes found, kept {max(sizes)} px")
