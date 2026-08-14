from __future__ import annotations

import bz2
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import zstandard

SUPPORTED_SUFFIXES = (".dem", ".dem.zst", ".dem.bz2")


def validate_source(path: Path, max_bytes: int) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if not any(path.name.lower().endswith(suffix) for suffix in SUPPORTED_SUFFIXES):
        raise ValueError(f"Nicht unterstützter Dateityp: {path.name}")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"Demo ist größer als das Limit von {max_bytes} Bytes")


@contextmanager
def materialize_demo(path: Path, max_bytes: int = 2_000_000_000) -> Iterator[Path]:
    """Yield a parser-ready .dem and delete temporary data afterwards."""
    validate_source(path, max_bytes)
    if path.name.lower().endswith(".dem"):
        yield path
        return

    with tempfile.TemporaryDirectory(prefix="iy-demo-") as temp_dir:
        target = Path(temp_dir) / path.name.rsplit(".", 1)[0]
        if path.name.lower().endswith(".zst"):
            with path.open("rb") as source, target.open("wb") as output:
                zstandard.ZstdDecompressor().copy_stream(source, output)
        else:
            with bz2.open(path, "rb") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
        if target.stat().st_size > max_bytes:
            raise ValueError("Entpackte Demo überschreitet das Größenlimit")
        yield target
