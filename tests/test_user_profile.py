from pathlib import Path
import json

import pytest

from improve_yourself.local_steam_accounts import LocalSteamAccountCandidate
from improve_yourself.user_profile import LocalUserProfileStore, profile_from_candidates, select_active_account


def test_user_profile_is_separate_from_analysis_profiles_and_requires_selection(tmp_path: Path) -> None:
    profile = profile_from_candidates("my_profile", (
        LocalSteamAccountCandidate("76561198000000001", "First"),
        LocalSteamAccountCandidate("76561198000000002", "Second"),
    ), display_name="Local player")
    assert profile.active_steam_id64 is None
    assert {account.state for account in profile.steam_accounts} == {"DETECTED_LOCAL"}
    active = select_active_account(profile, "76561198000000002")
    store = LocalUserProfileStore(tmp_path / "user-profile")
    path = store.save(active)
    loaded = store.load("my_profile")
    assert path.parent == (tmp_path / "user-profile").resolve()
    assert loaded.active_steam_id64 == "76561198000000002"
    assert [account.state for account in loaded.steam_accounts] == ["INACTIVE", "ACTIVE_FOR_PERSONAL_MATCHING"]


def test_user_profile_rejects_unconfirmed_or_unknown_active_selection(tmp_path: Path) -> None:
    profile = profile_from_candidates("my_profile", (LocalSteamAccountCandidate("76561198000000001", None),))
    with pytest.raises(ValueError, match="not a detected"):
        select_active_account(profile, "76561198000000002")
    store = LocalUserProfileStore(tmp_path)
    with pytest.raises(ValueError, match="safe lowercase"):
        store.load("../escape")


def test_user_profile_storage_rejects_extra_fields_and_unconfirmed_active_account(tmp_path: Path) -> None:
    profile = select_active_account(
        profile_from_candidates("my_profile", (LocalSteamAccountCandidate("76561198000000001", None),)),
        "76561198000000001",
    )
    store = LocalUserProfileStore(tmp_path)
    path = store.save(profile)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["unexpected"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid local user profile"):
        store.load("my_profile")
    payload.pop("unexpected")
    payload["steam_accounts"][0]["user_confirmed"] = False
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="user confirmed"):
        store.load("my_profile")
