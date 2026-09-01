from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from improve_yourself.owned_tactical_representation import (
    OWNED_TACTICAL_REPRESENTATION_SCHEMA,
    OwnedTacticalRepresentationError,
    load_owned_tactical_representation,
    player_marker_instructions,
)
from improve_yourself.replay_contract import PlayerState, ReplayFrame, Vec3


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = ROOT / "resources" / "3d_pov" / "de_anubis" / "owned_tactical_representation.json"


def _document() -> dict:
    return json.loads(DESCRIPTOR.read_text(encoding="utf-8"))


def _write(tmp_path: Path, document: dict) -> Path:
    path = tmp_path / "representation.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _frame() -> ReplayFrame:
    return ReplayFrame(
        tick=6401,
        round_number=1,
        time_in_round_seconds=None,
        players=(
            PlayerState("ct", True, True, "CT", Vec3(10.0, 20.0, 30.0), 90.0, 2.0, None, 100, 0, None),
            PlayerState("t", True, True, "T", Vec3(-5.0, 6.0, 7.0), None, None, None, 100, 0, None),
            PlayerState("unknown", True, True, "spectator", Vec3(1.0, 2.0, 3.0), 180.0, 0.0, None, 100, 0, None),
            PlayerState("inactive", False, True, "CT", Vec3(4.0, 5.0, 6.0), 0.0, 0.0, None, 100, 0, None),
            PlayerState("unpositioned", True, True, "T", None, 0.0, 0.0, None, 100, 0, None),
        ),
        utilities=(),
        events=(),
    )


def test_owned_descriptor_is_strict_presentation_only_and_reserves_no_game_content() -> None:
    document = _document()
    assert document["schema"] == OWNED_TACTICAL_REPRESENTATION_SCHEMA
    assert set(document) == {
        "schema", "map_id", "purpose", "source_classification", "player_markers", "outbox", "discovery",
    }
    assert document["purpose"] == "presentation_only"
    assert document["source_classification"] == "OWNED_IMPROVE_PROCEDURAL"
    assert document["player_markers"]["mode"] == "procedural_marker"
    assert document["player_markers"]["badge_anchor"] == "not_available"
    assert document["outbox"] == {"state": "not_available"}
    assert document["discovery"] == {"state": "not_available", "slots": []}

    prohibited_tokens = {
        "tick", "yaw", "pitch", "position", "transform", "collision", "visibility", "route", "callout",
        "reward", "unlock", "score", "progress", "profile", "steam", "vpk", "valve", "path", "url",
    }
    serialized = json.dumps(document, sort_keys=True).lower()
    assert not any(f'"{token}"' in serialized for token in prohibited_tokens)


def test_descriptor_loads_only_for_its_exact_canonical_map() -> None:
    representation = load_owned_tactical_representation(DESCRIPTOR, "de_anubis")
    assert representation.map_id == "de_anubis"
    assert representation.badge_anchor_state == "not_available"
    assert representation.outbox_state == "not_available"
    assert representation.discovery_state == "not_available"
    with pytest.raises(OwnedTacticalRepresentationError, match="differs from replay map"):
        load_owned_tactical_representation(DESCRIPTOR, "de_mirage")


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d.update({"unknown": True}), "representation document"),
        (lambda d: d.update({"purpose": "map_geometry"}), "presentation_only"),
        (lambda d: d.update({"source_classification": "LOCAL_CS2_EXTRACTION"}), "not approved"),
        (lambda d: d["player_markers"].update({"mesh_path": "C:/Steam/player.obj"}), "player_markers"),
        (lambda d: d["player_markers"].update({"badge_anchor": "available"}), "badge_anchor"),
        (lambda d: d["outbox"].update({"state": "available"}), "outbox.state"),
        (lambda d: d["discovery"].update({"slots": [{"position": [1, 2, 3]}]}), "discovery slots"),
        (lambda d: d["player_markers"]["team_colors"].update({"CT": [2, 0, 0, 1]}), "within"),
    ],
)
def test_unsafe_or_future_gameplay_claims_fail_closed(tmp_path: Path, mutate, message: str) -> None:
    document = deepcopy(_document())
    mutate(document)
    with pytest.raises(OwnedTacticalRepresentationError, match=message):
        load_owned_tactical_representation(_write(tmp_path, document), "de_anubis")


def test_procedural_markers_preserve_canonical_positions_and_never_invent_direction() -> None:
    representation = load_owned_tactical_representation(DESCRIPTOR, "de_anubis")
    frame = _frame()
    instructions = player_marker_instructions(
        representation, frame, selected_player_id="ct", view_mode="third_person",
    )
    assert [item.player_id for item in instructions] == ["ct", "t", "unknown"]
    assert instructions[0].position == Vec3(10.0, 20.0, 30.0)
    assert instructions[0].forward_xy == pytest.approx((0.0, 1.0))
    assert instructions[1].position == Vec3(-5.0, 6.0, 7.0)
    assert instructions[1].forward_xy is None
    assert instructions[2].color == representation.team_styles["unknown"].color
    assert all(item.badge_anchor_state == "not_available" for item in instructions)


def test_selected_first_person_marker_is_hidden_without_altering_other_canonical_players() -> None:
    representation = load_owned_tactical_representation(DESCRIPTOR, "de_anubis")
    first_person = player_marker_instructions(
        representation, _frame(), selected_player_id="ct", view_mode="first_person",
    )
    assert [item.player_id for item in first_person] == ["t", "unknown"]
    assert first_person[0].position == Vec3(-5.0, 6.0, 7.0)


def test_presentation_module_and_runner_add_no_model_asset_loader_or_second_runtime_path() -> None:
    module_source = (ROOT / "src" / "improve_yourself" / "owned_tactical_representation.py").read_text(encoding="utf-8")
    renderer_source = (ROOT / "src" / "improve_yourself" / "panda_renderer.py").read_text(encoding="utf-8")
    runner_source = (ROOT / "tools" / "dev" / "Run-AnubisViewerDemo.py").read_text(encoding="utf-8")
    assert "loadModel" not in module_source
    assert "assess_map_asset" not in module_source
    assert "ReplayStore(" not in module_source and "ReplayController(" not in module_source
    assert "def load_owned_tactical_representation" in renderer_source
    assert "self._base.loader.loadModel" not in renderer_source.split("def load_owned_tactical_representation", 1)[1].split("def set_frame", 1)[0]
    assert "--owned-presentation" in runner_source
    assert "ReplayRendererSession(controller, renderer)" in runner_source
