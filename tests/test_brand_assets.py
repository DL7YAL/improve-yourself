import hashlib
from pathlib import Path

from PIL import Image


ASSETS = Path(__file__).parents[1] / "src" / "improve_yourself" / "assets"


def test_canonical_variant_three_source_is_preserved_exactly() -> None:
    source = ASSETS / "improve-yourself-logo-v3-full.png"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == (
        "3b33d2af88e97092506a1005012ba315e0484800585ef215b379f3f28390a25b"
    )
    with Image.open(source) as image:
        assert image.size == (490, 770)


def test_windows_icon_exports_are_real_supported_image_assets() -> None:
    with Image.open(ASSETS / "improve-yourself-icon-v3.png") as image:
        assert image.size == (512, 512)
        assert image.mode == "RGBA"
    with Image.open(ASSETS / "improve-yourself-icon-v3.ico") as image:
        assert image.format == "ICO"
        assert (256, 256) in image.info["sizes"]
