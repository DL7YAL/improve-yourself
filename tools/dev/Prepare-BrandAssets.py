from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from PIL import Image


CANONICAL_NAME = "Improve-Yourself-Logo-Variante-3-vollstaendig.png"
CANONICAL_SHA256 = "3b33d2af88e97092506a1005012ba315e0484800585ef215b379f3f28390a25b"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare faithful Variant-3 Windows brand exports.")
    parser.add_argument("source", type=Path, help=f"Canonical {CANONICAL_NAME}")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    if source.name != CANONICAL_NAME:
        raise ValueError(f"expected canonical filename {CANONICAL_NAME}")
    if sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical Variant-3 source hash differs; refusing to derive brand assets")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    canonical = output / "improve-yourself-logo-v3-full.png"
    shutil.copyfile(source, canonical)

    with Image.open(source) as image:
        image.load()
        if image.size != (490, 770):
            raise ValueError(f"unexpected canonical dimensions: {image.size}")
        # Exact crop of the approved ascending bars/final I; no redrawing or reinterpretation.
        mark = image.crop((40, 62, 450, 536)).convert("RGBA")
        canvas = Image.new("RGBA", (512, 512), (7, 17, 30, 255))
        mark.thumbnail((452, 452), Image.Resampling.LANCZOS)
        canvas.alpha_composite(mark, ((512 - mark.width) // 2, (512 - mark.height) // 2))
        canvas.save(output / "improve-yourself-icon-v3.png", optimize=True)
        canvas.save(
            output / "improve-yourself-icon-v3.ico",
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
