import hashlib
import json
import re
from pathlib import Path


CONTROLLER = Path("assets/maps/improve_yourself_benchmark/scripts/benchmark_controller.js")


def source() -> str:
    return CONTROLLER.read_text(encoding="utf-8")


def test_source_manifest_hashes_every_versioned_addon_file() -> None:
    root = Path("assets/maps/improve_yourself_benchmark")
    manifest = json.loads((root / "source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "iy.cs2-addon-sources/v1"
    for item in manifest["files"]:
        digest = hashlib.sha256((root / item["path"]).read_bytes()).hexdigest().upper()
        assert digest == item["sha256"]


def test_transition_sequence_and_occlusions_are_locked() -> None:
    text = source()
    assert 'from: "nuke_outside", to: "ancient_b", occlusion: "smoke"' in text
    assert 'from: "ancient_b", to: "inferno_apps_a", occlusion: "flash"' in text
    assert 'landmark: "red_room"' in text
    assert 'grenade(CSGrenadeType.FLASHBANG, [0, 2950, 140])' in text
    assert 'fadeout 0.15 1.4 255 255 255 255' in text
    assert 'fadein 0.35 255 255 255 255' in text
    assert 'grenade(CSGrenadeType.SMOKE, [0, 2950, 140])' not in text
    assert 'grenade(CSGrenadeType.SMOKE, [0, 3500, 160])' not in text
    assert 'fadeout 0.25 3.3 160 0 0 96' in text


def test_hidden_swap_markers_follow_enter_and_precede_exit() -> None:
    text = source()
    for index in (0, 1):
        enter = text.index(f'transitionMarker({index}, "ENTER")')
        swap = text.index(f'transitionMarker({index}, "SWAP")')
        exit_ = text.index(f'transitionMarker({index}, "EXIT")')
        assert enter < swap < exit_


def test_hidden_swap_endpoint_height_and_yaw_are_matched() -> None:
    text = source()
    assert '{ t: 22, p: [470, 980, 125], q: [900, 1120, 70] }' in text
    assert '{ t: 22, p: [0, 1550, 160], q: [430, 1690, 72] }' in text
    assert '{ t: 22.35, p: [0, 1580, 165], q: [0, 2000, 72] }' in text
    assert '{ t: 43, p: [0, 2950, 140], q: [0, 3070, 90] }' in text
    assert '{ t: 43, p: [0, 3500, 160], q: [0, 3900, 72] }' in text
    assert '{ t: 43.35, p: [0, 3520, 165], q: [0, 3900, 90] }' in text
    assert re.search(r'\{ t: 44\.5, p: \[0, 3650, 170\], q: \[0, 4020, 100\] \}', text)
