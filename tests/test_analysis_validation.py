from copy import deepcopy

from improve_yourself.validation import validate_analysis_payload
from improve_yourself.model import DataQuality, Kill, Multikill
from improve_yourself.service import build_analysis_user_view
from improve_yourself.criteria import DEFAULT_PROFILE, default_review_hints


def valid_payload() -> dict:
    kills = [
        {
            "round_number": 4,
            "tick": tick,
            "attacker": "Player",
            "victim": f"Victim-{tick}",
            "weapon": "ak47",
            "headshot": False,
        }
        for tick in (100, 2_000, 9_000)
    ]
    return {
        "schema": "iy.analysis/v1",
        "source_name": "fixture.dem.zst",
        "source_sha256": "a" * 64,
        "map_name": "de_nuke",
        "tickrate": 64.0,
        "kills": kills,
        "multikills": [
            {
                "round_number": 4,
                "player": "Player",
                "kill_count": 3,
                "first_tick": 100,
                "last_tick": 9_000,
                "victims": ["Victim-100", "Victim-2000", "Victim-9000"],
            }
        ],
        "data_quality": {
            "status": "limited",
            "missing_channels": ["footsteps"],
            "warnings": ["Footstep-Ereignisse fehlen; soundbezogene Marker sind deaktiviert."],
        },
        "available_channels": ["rounds", "kills", "shots"],
        "disclaimer": "Automatische Marker sind Prüfhinweise und kein Cheat-Nachweis.",
    }


def test_valid_round_wide_multikill_and_footstep_limitation() -> None:
    assert validate_analysis_payload(valid_payload()) == []


def test_rejects_overlapping_available_and_missing_channels() -> None:
    payload = valid_payload()
    payload["available_channels"].append("footsteps")
    assert "available and missing channels must not overlap" in validate_analysis_payload(payload)


def test_rejects_multikill_that_does_not_match_round_kills() -> None:
    payload = deepcopy(valid_payload())
    payload["multikills"][0]["kill_count"] = 4
    errors = validate_analysis_payload(payload)
    assert "multikills[0] does not match round-wide kill data" in errors


def test_invalid_marker_identity_is_reported_without_crashing() -> None:
    payload = deepcopy(valid_payload())
    payload["multikills"][0]["player"] = ["not", "a", "name"]
    errors = validate_analysis_payload(payload)
    assert "multikills[0].player must be a non-empty string" in errors


def test_user_summary_separates_facts_hints_and_missing_channels() -> None:
    kills = [Kill(1, tick, "Player", f"Victim-{tick}") for tick in (10, 20, 30)]
    markers = [Multikill(1, "Player", 3, 10, 30, ["Victim-10", "Victim-20", "Victim-30"])]
    view = build_analysis_user_view(kills, markers, DataQuality("limited", ["footsteps"], []))

    assert view["assessment"]["status"] == "Hinweis"
    assert any("3 Kills" in value for value in view["facts"])
    assert "kein Cheat-Nachweis" in view["indicators"][0]
    assert "Schritt-Ereignisse fehlen" in view["limitations"][0]


def test_default_profile_emits_transparent_multikill_review_hints() -> None:
    marker = Multikill(4, "Player", 3, 100, 9000, ["A", "B", "C"])
    hint = default_review_hints([marker])[0]

    assert DEFAULT_PROFILE["version"] == "v1"
    assert hint["criterion_id"] == "round_multikill"
    assert hint["threshold"]["value"] == 3
    assert hint["observed_facts"]["kill_count"] == 3
    assert hint["verdict"] == "review_hint"
