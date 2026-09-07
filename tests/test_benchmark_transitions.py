import hashlib
import json
import re
from pathlib import Path


CONTROLLER = Path("assets/maps/improve_yourself_benchmark/scripts/benchmark_controller.js")
PROVENANCE = Path("assets/maps/improve_yourself_benchmark/NUKE_OUTSIDE_ASSET_PROVENANCE.json")
TRANSITION_PROVENANCE = Path("assets/maps/improve_yourself_benchmark/TRANSITION_WORLDS_ASSET_PROVENANCE.json")
MAP = Path("assets/maps/improve_yourself_benchmark/maps/improve_yourself_benchmark.vmap")
SCENE_REFERENCE_PREFIXES = (
    b"materials/de_nuke/",
    b"materials/de_ancient/",
    b"materials/de_inferno/",
    b"models/props/de_nuke/",
    b"models/props/de_ancient/",
    b"models/props/de_inferno/",
)


def source() -> str:
    return CONTROLLER.read_text(encoding="utf-8")


def test_source_manifest_hashes_every_versioned_addon_file() -> None:
    root = Path("assets/maps/improve_yourself_benchmark")
    manifest = json.loads((root / "source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "iy.cs2-addon-sources/v1"
    for item in manifest["files"]:
        digest = hashlib.sha256((root / item["path"]).read_bytes()).hexdigest().upper()
        assert digest == item["sha256"]


def test_nuke_outside_runtime_references_are_fail_closed() -> None:
    record = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    assert record["schema"] == "iy.cs2-workshop-asset-provenance/v1"
    assert record["scene"] == "nuke_outside"
    assert record["verification"] == {
        "method": "Installed CS2 pak01_dir.vpk directory-index lookup only",
        "runtime_reference_only": True,
        "vpk_payload_extracted": False,
        "repository_asset_copy_created": False,
    }
    assert len(record["assets"]) == 11
    paths = set()
    for asset in record["assets"]:
        assert asset["rights_class"] == "VALVE_RUNTIME_REFERENCE"
        assert asset["distribution"] == "CS2_WORKSHOP_RUNTIME"
        assert asset["runtime_reference_only"] is True
        assert asset["asset_path"].endswith((".vmdl", ".vmat"))
        assert not asset["asset_path"].endswith("_c")
        paths.add(asset["asset_path"])
    assert len(paths) == len(record["assets"])


def test_transition_world_runtime_references_are_fail_closed() -> None:
    record = json.loads(TRANSITION_PROVENANCE.read_text(encoding="utf-8"))
    assert record["schema"] == "iy.cs2-workshop-asset-provenance/v1"
    assert record["scenes"] == ["benchmark_intro", "ancient_b", "inferno_apps_a"]
    assert record["verification"] == {
        "method": "Installed CS2 pak01_dir.vpk directory-index lookup only",
        "runtime_reference_only": True,
        "vpk_payload_extracted": False,
        "repository_asset_copy_created": False,
    }
    assert len(record["assets"]) == 22
    paths = set()
    for asset in record["assets"]:
        assert asset["scene"] in record["scenes"]
        assert asset["rights_class"] == "VALVE_RUNTIME_REFERENCE"
        assert asset["distribution"] == "CS2_WORKSHOP_RUNTIME"
        assert asset["runtime_reference_only"] is True
        assert asset["asset_path"].endswith((".vmdl", ".vmat"))
        assert not asset["asset_path"].endswith("_c")
        paths.add(asset["asset_path"])
    assert len(paths) == len(record["assets"])


def test_all_provenanced_runtime_references_exist_in_hammer_saved_map() -> None:
    map_bytes = MAP.read_bytes()
    records = (
        json.loads(PROVENANCE.read_text(encoding="utf-8")),
        json.loads(TRANSITION_PROVENANCE.read_text(encoding="utf-8")),
    )
    for record in records:
        for asset in record["assets"]:
            assert asset["asset_path"].encode("ascii") in map_bytes


def test_all_scene_runtime_references_are_provenanced() -> None:
    records = (
        json.loads(PROVENANCE.read_text(encoding="utf-8")),
        json.loads(TRANSITION_PROVENANCE.read_text(encoding="utf-8")),
    )
    provenanced = {
        asset["asset_path"].encode("ascii")
        for record in records
        for asset in record["assets"]
        if asset["asset_path"].encode("ascii").startswith(SCENE_REFERENCE_PREFIXES)
    }
    scene_references = {
        match
        for match in re.findall(
            rb"(?:materials|models)/[A-Za-z0-9_./-]+\.(?:vmat|vmdl)",
            MAP.read_bytes(),
        )
        if match.startswith(SCENE_REFERENCE_PREFIXES)
    }
    assert scene_references == provenanced


def test_transition_sequence_and_occlusions_are_locked() -> None:
    text = source()
    assert 'from: "nuke_outside", to: "ancient_b", occlusion: "smoke"' in text
    assert 'from: "ancient_b", to: "inferno_apps_a", occlusion: "flash"' in text
    assert 'landmark: "red_room"' in text
    assert 'grenade(CSGrenadeType.FLASHBANG, [0, 2950, 140])' in text
    assert 'fadeout 0.15 255 255 255' in text
    assert 'fadein 0.35 255 255 255' in text
    assert 'grenade(CSGrenadeType.SMOKE, [0, 2950, 140])' not in text
    assert 'grenade(CSGrenadeType.SMOKE, [0, 3500, 160])' not in text
    assert 'fadeout 0.25 160 0 0' in text


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
    assert re.search(r'\{ t: 44\.5, p: \[0, 3450, 600\], q: \[0, 4300, 0\] \}', text)
    assert '{ t: 48, p: [0, 3600, 560], q: [0, 4450, 20] }' in text
    assert '{ t: 53, p: [0, 3900, 520], q: [0, 4700, 60] }' in text


def test_transition_fades_use_cs2_time_and_rgb_syntax() -> None:
    text = CONTROLLER.read_text(encoding="utf-8")

    assert 'command("fadeout 0.15 255 255 255")' in text
    assert 'command("fadein 0.35 255 255 255")' in text
    assert 'command("fadeout 0.25 160 0 0")' in text
    assert 'command("fadein 0.1 160 0 0")' in text
    assert "255 255 255 255" not in text
    assert "160 0 0 96" not in text


def test_benchmark_suppresses_default_team_intro_delay() -> None:
    text = source()
    assert 'command("mp_team_intro_time 0")' in text
    assert 'command("mp_force_pick_time 0")' in text


def test_capture_windows_are_versioned_and_follow_scene_order() -> None:
    text = source()
    assert 'const VERSION = "iy-benchmark/v1.2-candidate.1"' in text
    markers = [
        'captureWindow("nuke_outside", "yard_landmarks", 9.0)',
        'captureWindow("ancient_b", "water_reflection", 27.0)',
        'captureWindow("ancient_b", "red_room", 38.0)',
        'captureWindow("inferno_apps_a", "stairs", 48.0)',
        'captureWindow("inferno_apps_a", "apps_details", 53.0)',
    ]
    positions = [text.index(marker) for marker in markers]
    assert positions == sorted(positions)
    assert "CAPTURE_WINDOW pass=${activePass} scene=${sceneId} landmark=${landmarkId}" in text
    assert "expected_t=${expectedTime}" in text


def test_runtime_completion_does_not_claim_verified_measurement() -> None:
    text = source()
    assert (
        "PASS_END type=measured runtime_status=complete measurement_status=unverified"
        in text
    )
    assert "MEASUREMENT_STATUS status=unverified" in text
    assert "client_commands_require_runtime_confirmation" in text
    assert 'runtimeStatus: "complete"' in text
    assert 'measurementStatus: "unverified"' in text
    assert 'PASS_END type=measured status=complete' not in text
