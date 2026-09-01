from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from improve_yourself.owned_scene_presentation import (
    OWNED_SCENE_PRESENTATION_SCHEMA,
    OwnedScenePresentationError,
    load_owned_scene_presentation,
)


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = ROOT / "resources" / "3d_pov" / "de_anubis" / "owned_scene_presentation.json"


def _document() -> dict:
    return json.loads(DESCRIPTOR.read_text(encoding="utf-8"))


def _write(tmp_path: Path, document: dict) -> Path:
    path = tmp_path / "scene.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_scene_descriptor_is_strict_owned_presentation_and_honestly_technical_only() -> None:
    document = _document()
    assert document["schema"] == OWNED_SCENE_PRESENTATION_SCHEMA
    assert document["purpose"] == "presentation_only"
    assert document["source_classification"] == "OWNED_IMPROVE_PROCEDURAL"
    assert document["output_state"] == "technical_only"
    assert document["visual_layers"] == {
        "player_markers": "canonical_replay",
        "view_directions": "canonical_replay",
        "neutral_spatial_reference": "technical_only",
    }
    assert document["future_reservations"] == {
        "badge": "not_available", "outbox": "not_available", "discovery": "not_available",
    }
    states = {
        document["output_state"],
        document["visual_layers"]["neutral_spatial_reference"],
        *document["future_reservations"].values(),
    }
    assert "available" not in states


def test_scene_descriptor_loads_only_for_exact_canonical_map() -> None:
    scene = load_owned_scene_presentation(DESCRIPTOR, "de_anubis")
    assert scene.output_state == "technical_only"
    assert scene.neutral_spatial_reference_state == "technical_only"
    with pytest.raises(OwnedScenePresentationError, match="differs from replay map"):
        load_owned_scene_presentation(DESCRIPTOR, "de_mirage")


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d.update({"unknown": True}), "scene document"),
        (lambda d: d.update({"purpose": "map_geometry"}), "presentation_only"),
        (lambda d: d.update({"source_classification": "LOCAL_CS2_EXTRACTION"}), "not approved"),
        (lambda d: d.update({"output_state": "available"}), "output_state"),
        (lambda d: d["visual_layers"].update({"map_mesh_path": "C:/Steam/world.glb"}), "visual_layers"),
        (lambda d: d["visual_layers"].update({"player_markers": "manual_coordinates"}), "player_markers"),
        (lambda d: d["future_reservations"].update({"badge": "available"}), "future_reservations.badge"),
        (lambda d: d.update({"non_authority": []}), "non_authority"),
    ],
)
def test_scene_contract_fails_closed_on_assets_map_truth_or_future_promotion(tmp_path: Path, mutate, message: str) -> None:
    document = deepcopy(_document())
    mutate(document)
    with pytest.raises(OwnedScenePresentationError, match=message):
        load_owned_scene_presentation(_write(tmp_path, document), "de_anubis")


def test_scene_module_has_no_map_asset_replay_or_renderer_implementation() -> None:
    source = (ROOT / "src" / "improve_yourself" / "owned_scene_presentation.py").read_text(encoding="utf-8")
    assert "assess_map_asset" not in source
    assert "ReplayStore" not in source and "ReplayController" not in source
    assert "PandaReplayRenderer" not in source
    assert "loadModel" not in source and "loadSfx" not in source
