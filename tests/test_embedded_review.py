import json
from pathlib import Path

import pytest

from improve_yourself.embedded_review import EmbeddedReviewSession


class Opener:
    def __init__(self) -> None:
        self.calls = []

    def open_scene(self, scene_id: str, tick: int) -> dict[str, object]:
        self.calls.append((scene_id, tick))
        return {"status": "sent", "scene_id": scene_id, "tick": tick}


def flow(path: Path, *, tick_rate=64.0) -> Path:
    payload = {
        "schema": "iy.analysis_flow/v1",
        "source": {"sha256": "a" * 64, "map_id": "de_ancient", "tick_rate": tick_rate},
        "roster": [{"player_id": "p1", "display_name": "Player One"}],
        "profile": {"profile_id": "review_v1", "purpose": "review"},
        "scenes": [
            {"scene_id": "r1-t128-0", "round_number": 1, "start_tick": 100, "end_tick": 200,
             "anchor_types": ["kill", "headshot"], "rule_ids": ["objective_kill"],
             "player_ids": ["p1"], "marker_ticks": [128], "review": {"tick": 128}},
            {"scene_id": "r2-t3840-1", "round_number": 2, "start_tick": 3800, "end_tick": 3900,
             "anchor_types": ["entry"], "rule_ids": ["objective_entry"],
             "player_ids": ["p1"], "marker_ticks": [3840], "review": {"tick": 3840}},
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_embedded_review_exposes_canonical_scene_context_and_timecode(tmp_path: Path) -> None:
    session = EmbeddedReviewSession(flow(tmp_path / "flow.json"), tmp_path / "state.json", "a" * 64, Opener())
    assert [scene.scene_id for scene in session.scenes] == ["r1-t128-0", "r2-t3840-1"]
    assert session.scenes[0].timecode == "00:02.000"
    assert session.scenes[0].player_names == ("Player One",)
    assert session.scenes[0].anchor_types == ("kill", "headshot")


def test_embedded_review_persists_status_and_note_source_bound(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    session = EmbeddedReviewSession(flow(tmp_path / "flow.json"), state, "a" * 64, Opener())
    session.save_review("r1-t128-0", "reviewed", "checked in CS2")
    reloaded = EmbeddedReviewSession(tmp_path / "flow.json", state, "a" * 64, Opener())
    assert reloaded.review("r1-t128-0") == {
        "scene_id": "r1-t128-0", "state": "reviewed", "note": "checked in CS2"
    }
    with pytest.raises(ValueError, match="at most"):
        session.save_review("r1-t128-0", "reviewed", "x" * 2001)


def test_embedded_review_uses_existing_scene_tick_opener_only(tmp_path: Path) -> None:
    opener = Opener()
    session = EmbeddedReviewSession(flow(tmp_path / "flow.json"), tmp_path / "state.json", "a" * 64, opener)
    assert session.open_in_cs2("r2-t3840-1") == {"status": "sent", "scene_id": "r2-t3840-1", "tick": 3840}
    assert opener.calls == [("r2-t3840-1", 3840)]
    with pytest.raises(ValueError, match="unknown"):
        session.open_in_cs2("invented")


def test_embedded_review_does_not_invent_time_without_tick_rate(tmp_path: Path) -> None:
    session = EmbeddedReviewSession(
        flow(tmp_path / "flow.json", tick_rate=None), tmp_path / "state.json", "a" * 64, Opener()
    )
    assert session.scenes[0].timecode == "Zeit nicht belegt"
