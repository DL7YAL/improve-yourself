from pathlib import Path

import pytest
import zstandard

from improve_yourself.importer import materialize_demo, validate_source


def test_zst_is_materialized_and_removed(tmp_path: Path) -> None:
    source = tmp_path / "match.dem.zst"
    source.write_bytes(zstandard.ZstdCompressor().compress(b"demo-data"))
    with materialize_demo(source) as demo:
        temporary = demo
        assert demo.read_bytes() == b"demo-data"
    assert not temporary.exists()


def test_unknown_extension_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "match.zip"
    source.write_bytes(b"data")
    with pytest.raises(ValueError):
        validate_source(source, 1_000)
