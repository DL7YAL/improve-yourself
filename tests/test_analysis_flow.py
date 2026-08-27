import pytest

from improve_yourself.analysis_flow import AnalysisProfile, PlayerSelection, build_analysis_flow, render_analysis_review


def _fixture():
    manifest = {
        "source": {"sha256": "a" * 64, "map_id": "de_test", "tick_rate": 64, "parser": {"name": "awpy", "version": "2.0.2"}},
        "players": [
            {"player_id": "p1", "display_name": "Alpha", "steam_id": "1"},
            {"player_id": "p2", "display_name": "Bravo", "steam_id": "2"},
            {"player_id": "p3", "display_name": "Charlie", "steam_id": "3"},
        ],
    }
    frames = [
        {"tick": 100, "players": [{"player_id": "p1", "team": "CT"}, {"player_id": "p2", "team": "T"}], "events": [{"event_id": "k1", "type": "kill", "tick": 100, "player_ids": ["p1", "p2"], "details": {"headshot": True, "penetrated": 1}}]},
        {"tick": 180, "players": [{"player_id": "p1", "team": "CT"}, {"player_id": "p3", "team": "T"}], "events": [{"event_id": "k2", "type": "kill", "tick": 180, "player_ids": ["p1", "p3"], "details": {"thrusmoke": True}}]},
        {"tick": 900, "players": [], "events": [{"event_id": "k3", "type": "kill", "tick": 900, "player_ids": ["p3", "p1"], "details": {}}]},
    ]
    return manifest, [{"round_number": 1, "frames": frames}]


def test_objective_indicators_rules_and_overlapping_markers_merge_into_one_scene():
    flow = build_analysis_flow(*_fixture())
    types = {item["type"] for item in flow["indicators"]}
    assert {"kill", "headshot", "wallbang", "smoke_kill", "entry", "multi_kill"} <= types
    assert len(flow["scenes"]) == 2
    first = flow["scenes"][0]
    assert first["marker_ticks"] == [100, 180]
    assert {"kill", "headshot", "wallbang", "smoke_kill", "entry", "multi_kill"} <= set(first["anchor_types"])
    assert first["review"]["command"] == "demo_gototick 100"
    assert flow["rule_policy"]["weak_single_indicator_scenes"] is False


def test_player_selection_validates_and_filters_by_involvement():
    manifest, chunks = _fixture()
    selected = build_analysis_flow(manifest, chunks, selection=PlayerSelection("player_select", ("p2",)))
    assert len(selected["scenes"]) == 1
    deduplicated = build_analysis_flow(manifest, chunks, selection=PlayerSelection("player_select", ("p2", "p2")))
    assert deduplicated["selection"]["player_ids"] == ("p2",)
    with pytest.raises(ValueError, match="at least one"):
        build_analysis_flow(manifest, chunks, selection=PlayerSelection("player_select", ()))
    with pytest.raises(ValueError, match="unknown"):
        build_analysis_flow(manifest, chunks, selection=PlayerSelection("player_select", ("missing",)))


def test_profile_filters_named_rules_without_changing_indicators() -> None:
    manifest, chunks = _fixture()
    flow = build_analysis_flow(
        manifest, chunks,
        profile=AnalysisProfile("headshots", "custom", enabled_rule_ids=("objective_headshot",)),
    )
    assert len(flow["indicators"]) > len(flow["rule_matches"])
    assert {match["rule_id"] for match in flow["rule_matches"]} == {"objective_headshot"}
    assert flow["profile"]["purpose"] == "custom"
    none = build_analysis_flow(
        manifest, chunks,
        profile=AnalysisProfile("none", "custom", enabled_rule_ids=()),
    )
    assert none["indicators"]
    assert none["rule_matches"] == []
    assert none["scenes"] == []


def test_roster_preserves_names_lineups_and_review_controls(tmp_path):
    flow = build_analysis_flow(*_fixture())
    assert flow["roster"][0] == {"player_id": "p1", "display_name": "Alpha", "steam_id": "1", "teams": ["CT"], "initial_team": "CT"}
    review = render_analysis_review(flow, tmp_path / "review.html").read_text(encoding="utf-8")
    for token in ("Full Demo", "+ Add Player", "id=\"ctAll\"", "id=\"tAll\"", "Reset", "demo_gototick", "CS2 coordinator actions are unavailable"):
        assert token in review
    assert "/api/cs2/tick" not in review
    assert flow["rounds"] == [{"round_number": 1, "first_tick": 100, "last_tick": 900, "frame_count": 3}]
