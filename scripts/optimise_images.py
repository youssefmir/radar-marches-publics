"""Réduit le poids des captures PNG (palette adaptative 256 couleurs) pour garder le dépôt léger.

Usage : python scripts/optimise_images.py docs/img
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def optimise(path: Path) -> tuple[int, int]:
    before = path.stat().st_size
    img = Image.open(path).convert("RGB")
    img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, optimize=True)
    return before, path.stat().st_size


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/img")
    for p in sorted(folder.glob("*.png")):
        b, a = optimise(p)
        print(f"{p.name}: {b / 1e3:.0f} Ko -> {a / 1e3:.0f} Ko")
