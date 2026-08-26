import gzip
import hashlib
import json

import pytest

from improve_yourself.replay_contract import REPLAY_V2_SCHEMA, ROUND_CHUNK_SCHEMA
from improve_yourself.replay_controller import PlaybackTimingUnavailable, ReplayController
from improve_yourself.replay_store import ReplayStore


def _store(tmp_path, tick_rate=10.0) -> ReplayStore:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    descriptors = []
    for round_number, ticks in ((1, (10, 12, 15)), (2, (30, 32))):
        frames = [
            {
                "tick": tick,
                "round_number": round_number,
                "players": [{"player_id": "steam:7"}],
                "utilities": [],
                "events": ([{"event_id": f"event-{tick}", "type": "kill", "tick": tick}] if tick in (12, 32) else []),
            }
            for tick in ticks
        ]
        chunk = {"schema": ROUND_CHUNK_SCHEMA, "round_number": round_number, "frames": frames}
        chunk_path = rounds_dir / f"round-{round_number:03d}.json.gz"
        with gzip.open(chunk_path, "wt", encoding="utf-8") as stream:
            json.dump(chunk, stream)
        descriptors.append({
            "round_number": round_number,
            "first_tick": ticks[0],
            "last_tick": ticks[-1],
            "frame_count": len(ticks),
            "chunk": f"rounds/{chunk_path.name}",
            "sha256": hashlib.sha256(chunk_path.read_bytes()).hexdigest(),
        })
    manifest = {
        "schema": REPLAY_V2_SCHEMA,
        "source": {"sha256": "a" * 64, "map_id": "de_anubis", "tick_rate": tick_rate},
        "coordinate_space": "cs2_world",
        "players": [{"player_id": "steam:7"}, {"player_id": "steam:8"}],
        "rounds": descriptors,
        "scenes": [{"scene_id": "scene-1", "round_number": 1, "tick": 14, "focus_player_id": "steam:8"}],
        "capabilities": {
            "positions": "full", "view_yaw": "full", "view_pitch": "full",
            "alive_state": "partial", "weapon_state": "full", "velocity": "full",
            "utility_lifetimes": "unavailable", "utility_trajectories": "unavailable",
            "flash_effect": "unavailable", "sound": "unavailable", "map_geometry": "unavailable",
        },
    }
    path = tmp_path / "replay-v2.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return ReplayStore(path)


def test_seek_reports_requested_and_resolved_tick(tmp_path) -> None:
    controller = ReplayController(_store(tmp_path))
    context = controller.seek(1, 14)
    assert context.requested_tick == 14
    assert context.resolved_tick == 12
    assert context.frame["tick"] == 12


def test_view_switch_preserves_all_other_context(tmp_path) -> None:
    controller = ReplayController(_store(tmp_path))
    controller.seek_scene("scene-1")
    controller.set_speed(0.5)
    before = controller.snapshot()
    after = controller.set_view_mode("first_person")
    assert after.view_mode == "first_person"
    assert after.current_round == before.current_round
    assert after.resolved_tick == before.resolved_tick
    assert after.selected_player_id == "steam:8"
    assert after.selected_scene_id == "scene-1"
    assert after.playback_speed == 0.5


def test_playback_uses_tick_rate_speed_and_stops_at_match_end(tmp_path) -> None:
    controller = ReplayController(_store(tmp_path))
    controller.set_speed(0.5)
    controller.play()
    context = controller.advance(0.4)
    assert (context.requested_tick, context.resolved_tick) == (12, 12)
    context = controller.advance(1.0)
    assert (context.current_round, context.requested_tick, context.resolved_tick) == (1, 17, 15)
    assert context.play_state == "playing"
    context = controller.advance(3.0)
    assert (context.current_round, context.resolved_tick) == (2, 32)
    assert context.play_state == "paused"


def test_unknown_tick_rate_blocks_wall_clock_play_but_allows_navigation(tmp_path) -> None:
    controller = ReplayController(_store(tmp_path, tick_rate=None))
    with pytest.raises(PlaybackTimingUnavailable):
        controller.play()
    context = controller.seek(1, 15)
    assert context.resolved_tick == 15
    assert context.timing_available is False
    assert context.play_state == "paused"


def test_relevant_step_uses_exact_event_or_scene_tick(tmp_path) -> None:
    controller = ReplayController(_store(tmp_path))
    assert controller.step_relevant(1).resolved_tick == 12
    scene = controller.step_relevant(1)
    assert scene.requested_tick == 14
    assert scene.resolved_tick == 12
    assert controller.step_relevant(1).resolved_tick == 32
    assert controller.step_relevant(-1).requested_tick == 14


def test_subscribers_observe_committed_context_and_can_unsubscribe(tmp_path) -> None:
    controller = ReplayController(_store(tmp_path))
    observed = []
    unsubscribe = controller.subscribe(observed.append)
    controller.select_player("steam:7")
    unsubscribe()
    controller.select_player(None)
    assert len(observed) == 1
    assert observed[0].selected_player_id == "steam:7"


def test_invalid_mutations_are_atomic(tmp_path) -> None:
    controller = ReplayController(_store(tmp_path))
    before = controller.snapshot()
    with pytest.raises(KeyError):
        controller.seek_scene("missing")
    with pytest.raises(KeyError):
        controller.select_player("missing")
    with pytest.raises(ValueError):
        controller.set_speed(3.0)
    assert controller.snapshot() == before
