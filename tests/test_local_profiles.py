import json

import pytest

from improve_yourself.analysis_flow import AnalysisProfile
from improve_yourself.local_profiles import LocalProfileStore, built_in_profiles


def test_builtin_profiles_cover_neutral_purposes() -> None:
    profiles = built_in_profiles()
    assert {profile.purpose for profile in profiles} == {"review", "highlight", "coaching", "custom"}
    assert next(profile for profile in profiles if profile.purpose == "review").enabled_rule_ids is None


def test_local_profile_roundtrip_is_json_only_in_disclosed_root(tmp_path) -> None:
    store = LocalProfileStore(tmp_path / "profiles")
    profile = AnalysisProfile("my_review", "custom", 64, 128, 32, ("objective_headshot",))
    path = store.save(profile)
    assert path.parent == (tmp_path / "profiles").resolve()
    assert json.loads(path.read_text(encoding="utf-8"))["schema"] == "iy.analysis_profile/v1"
    assert {item.profile_id for item in store.list_profiles()} >= {"my_review", "review_v1", "highlight_v1", "coaching_v1", "custom_v1"}


def test_local_profile_rejects_unsafe_id_and_unknown_rule(tmp_path) -> None:
    store = LocalProfileStore(tmp_path)
    with pytest.raises(ValueError, match="safe lowercase"):
        store.save(AnalysisProfile("../escape", "custom"))
    with pytest.raises(ValueError, match="unknown objective rules"):
        store.save(AnalysisProfile("bad_rule", "custom", enabled_rule_ids=("free_suspicion",)))
