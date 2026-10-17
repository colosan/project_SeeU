"""Window / taskbar icon: SeeU's head from her own map sprite (PixelLab character, docs/ASSETS.md), on the panel
colour with the teal accent rim, scaled x4 nearest so it stays pixel art. Writes assets/ui/icon.png (256x256)."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets/characters/seeu/rotations/south.png"
OUT = ROOT / "assets/ui/icon.png"
CROP = (32, 10, 96, 74)          # head, hat ears and the top of the twin tails (128px sprite)
BG, RIM = (16, 17, 19, 255), (58, 163, 168, 255)    # plastic 0 / glow 2 (UiStyle.BG / ACCENT)


def main():
    head = Image.open(SRC).convert("RGBA").crop(CROP)
    tile = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((0, 0, 63, 63), radius=8, fill=BG, outline=RIM, width=2)
    # keep the sprite inside the rim: clip it to the rounded square's inside
    mask = Image.new("L", (64, 64), 0)
    ImageDraw.Draw(mask).rounded_rectangle((2, 2, 61, 61), radius=6, fill=255)
    clipped = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    clipped.paste(head, (0, 0), Image.composite(head.split()[3], Image.new("L", (64, 64), 0), mask))
    tile.alpha_composite(clipped)
    tile.resize((256, 256), Image.NEAREST).save(OUT)
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
