from copy import deepcopy

from improve_yourself.validation import validate_analysis_payload


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
