from pathlib import Path
from types import SimpleNamespace
import subprocess

import pytest
from PIL import Image

from improve_yourself.local_minimap import (
    LocalMinimap, load_local_minimap, overview_transform, project_point, viewport,
)

DESCRIPTOR = '''"de_anubis" { "material" "overviews/de_anubis"
"pos_x" "-2796" "pos_y" "3328" "scale" "5.22" }'''


@pytest.mark.parametrize("text", [
    DESCRIPTOR.replace('5.22', 'nan'),
    DESCRIPTOR.replace('5.22', '0'),
    DESCRIPTOR.replace('5.22', '6'),
    DESCRIPTOR.replace('de_anubis', 'de_mirage'),
    DESCRIPTOR.replace('}', '"pos_x" "1" }'),
    DESCRIPTOR.replace('}', '"verticalsections" {} }'),
])
def test_reject_incompatible_or_ambiguous_descriptor(text):
    with pytest.raises(ValueError):
        overview_transform(text, "de_anubis")


def test_projection_keeps_map_and_markers_together():
    minimap = LocalMinimap("de_anubis", None, overview_transform(DESCRIPTOR, "de_anubis"), "a", "b", "c")
    view = viewport(1600, 900, 2, (30, -20))
    assert project_point(minimap, -123.36, 655.36, view) == pytest.approx((830, 430))
    assert project_point(minimap, -2796, 3328, view) == pytest.approx(view[:2])
    assert minimap.compatibility == "unknown"


def setup_source(tmp_path):
    installation = tmp_path / "CS2 with spaces"
    folder = installation / "game/csgo"
    folder.mkdir(parents=True)
    archive = folder / "pak01_dir.vpk"
    archive.write_bytes(b"synthetic index")
    converter = tmp_path / "converter"
    converter.touch()
    return installation, archive, converter


def test_local_load_selects_only_two_resources_and_leaves_source_unchanged(tmp_path, monkeypatch):
    installation, archive, converter = setup_source(tmp_path)
    outputs = []
    members = []

    def run(args, **kwargs):
        output = Path(args[args.index("-o") + 1])
        outputs.append(output)
        members.append(args[args.index("--vpk_filepath") + 1])
        assert kwargs["timeout"] == 90
        if output.suffix == ".txt":
            output.write_text(DESCRIPTOR)
        else:
            Image.new("RGBA", (1024, 1024)).save(output)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", run)
    result = load_local_minimap(installation, converter, "de_anubis")
    assert result.image.size == (1024, 1024)
    assert result.transform == (-2796, 3328, 5.22)
    assert result.compatibility == "unknown"
    assert members == ["resource/overviews/de_anubis.txt", "panorama/images/overheadmaps/de_anubis_radar_psd.vtex_c"]
    assert archive.read_bytes() == b"synthetic index"
    assert all(not path.exists() for path in outputs)


@pytest.mark.parametrize("mode", ["missing", "failure", "timeout", "size", "changed"])
def test_conversion_failure_never_returns_a_map(tmp_path, monkeypatch, mode):
    installation, archive, converter = setup_source(tmp_path)

    def run(args, **kwargs):
        output = Path(args[args.index("-o") + 1])
        if mode == "timeout":
            raise subprocess.TimeoutExpired(args, 90)
        if mode == "missing":
            return SimpleNamespace(returncode=0)
        if output.suffix == ".txt":
            output.write_text(DESCRIPTOR)
        else:
            Image.new("RGB", (128, 128) if mode == "size" else (1024, 1024)).save(output)
        if mode == "changed":
            archive.write_bytes(b"updated index")
        return SimpleNamespace(returncode=1 if mode == "failure" else 0)

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(ValueError):
        load_local_minimap(installation, converter, "de_anubis")


def test_unknown_map_does_not_invoke_converter(tmp_path, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("must not invoke converter")
    monkeypatch.setattr(subprocess, "run", unexpected)
    with pytest.raises(ValueError):
        load_local_minimap(tmp_path, tmp_path / "tool", "../de_anubis")
