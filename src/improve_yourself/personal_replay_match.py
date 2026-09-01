"""Exact, read-only personal player matching for canonical Replay V2 manifests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .user_profile import UserProfile


@dataclass(frozen=True)
class PersonalReplayMatch:
    state: str
    steam_id64: str | None
    player_ids: tuple[str, ...]


def match_active_profile_to_replay(profile: UserProfile, replay_manifest: dict[str, Any]) -> PersonalReplayMatch:
    """Match solely by exact ``steam:<SteamID64>`` player identity; never by name."""
    steam_id64 = profile.active_steam_id64
    if steam_id64 is None:
        return PersonalReplayMatch("NO_ACTIVE_ACCOUNT", None, ())
    expected_player_id = f"steam:{steam_id64}"
    players = replay_manifest.get("players") if isinstance(replay_manifest, dict) else None
    if not isinstance(players, list):
        return PersonalReplayMatch("REPLAY_IDENTITY_UNAVAILABLE", steam_id64, ())
    matches = tuple(
        item["player_id"] for item in players
        if isinstance(item, dict) and item.get("player_id") == expected_player_id
    )
    return PersonalReplayMatch("MATCHED" if matches else "NO_EXACT_MATCH", steam_id64, matches)
