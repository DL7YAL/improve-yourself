from improve_yourself.local_steam_accounts import LocalSteamAccountCandidate
from improve_yourself.personal_replay_match import match_active_profile_to_replay
from improve_yourself.user_profile import profile_from_candidates, select_active_account


def test_replay_personal_match_uses_exact_steam_player_id_not_name() -> None:
    profile = select_active_account(
        profile_from_candidates("my_profile", (LocalSteamAccountCandidate("76561198000000001", "Shared name"),)),
        "76561198000000001",
    )
    manifest = {"players": [
        {"player_id": "steam:76561198000000002", "display_name": "Shared name"},
        {"player_id": "steam:76561198000000001", "display_name": "Different name"},
    ]}
    result = match_active_profile_to_replay(profile, manifest)
    assert result.state == "MATCHED"
    assert result.player_ids == ("steam:76561198000000001",)


def test_no_active_account_or_missing_replay_identity_stays_explicit() -> None:
    profile = profile_from_candidates("my_profile", ())
    assert match_active_profile_to_replay(profile, {"players": []}).state == "NO_ACTIVE_ACCOUNT"
    active = select_active_account(
        profile_from_candidates("my_profile", (LocalSteamAccountCandidate("76561198000000001", None),)),
        "76561198000000001",
    )
    assert match_active_profile_to_replay(active, {}).state == "REPLAY_IDENTITY_UNAVAILABLE"
