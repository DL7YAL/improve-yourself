from pathlib import Path

import pytest

from improve_yourself.local_steam_accounts import discover_local_steam_accounts, parse_loginusers_vdf


VDF = '''"users"
{
  "76561198000000001"
  {
    "PersonaName" "First local account"
    "RememberPassword" "1"
  }
  "76561198000000002"
  {
    "PersonaName" "Second local account"
  }
}
'''


def test_parses_only_minimal_local_account_candidates() -> None:
    candidates = parse_loginusers_vdf(VDF)
    assert [(item.steam_id64, item.local_label, item.source) for item in candidates] == [
        ("76561198000000001", "First local account", "LOCAL_STEAM_ACCOUNT_DISCOVERY"),
        ("76561198000000002", "Second local account", "LOCAL_STEAM_ACCOUNT_DISCOVERY"),
    ]


def test_discovery_requires_explicit_root_and_only_loginusers_file(tmp_path: Path) -> None:
    assert discover_local_steam_accounts(tmp_path) == ()
    path = tmp_path / "config" / "loginusers.vdf"
    path.parent.mkdir()
    path.write_text(VDF, encoding="utf-8")
    assert [item.steam_id64 for item in discover_local_steam_accounts(tmp_path)] == [
        "76561198000000001", "76561198000000002"
    ]
    with pytest.raises(ValueError, match="pathlib.Path"):
        discover_local_steam_accounts(str(tmp_path))  # type: ignore[arg-type]


def test_duplicate_candidate_ids_fail_closed() -> None:
    duplicate = VDF.replace('"76561198000000002"', '"76561198000000001"')
    with pytest.raises(ValueError, match="duplicate"):
        parse_loginusers_vdf(duplicate)
