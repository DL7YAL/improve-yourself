"""Explicit, local-only Steam account candidate discovery.

This module intentionally reads only ``<user-selected-steam-root>/config/loginusers.vdf``.
It never locates Steam on its own, contacts Steam, or reads credentials, sessions,
inventories, friends, chats, purchases, registry values, or CS2 data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


LOCAL_STEAM_ACCOUNT_SOURCE = "LOCAL_STEAM_ACCOUNT_DISCOVERY"
_ACCOUNT_BLOCK = re.compile(
    r'^\s*"(?P<steam_id64>7656119\d{10})"\s*\{(?P<body>.*?)^\s*\}',
    re.MULTILINE | re.DOTALL,
)
_PERSONA_NAME = re.compile(r'^\s*"PersonaName"\s*"(?P<value>[^"]*)"', re.MULTILINE)


@dataclass(frozen=True)
class LocalSteamAccountCandidate:
    """A minimally disclosed local candidate, not proof of ownership or login."""

    steam_id64: str
    local_label: str | None
    source: str = LOCAL_STEAM_ACCOUNT_SOURCE


def parse_loginusers_vdf(text: str) -> tuple[LocalSteamAccountCandidate, ...]:
    """Parse only account IDs and optional local persona labels from VDF text."""
    if not isinstance(text, str):
        raise ValueError("loginusers.vdf content must be text")
    candidates: list[LocalSteamAccountCandidate] = []
    seen: set[str] = set()
    for match in _ACCOUNT_BLOCK.finditer(text):
        steam_id64 = match.group("steam_id64")
        if steam_id64 in seen:
            raise ValueError("loginusers.vdf contains a duplicate Steam account ID")
        seen.add(steam_id64)
        persona = _PERSONA_NAME.search(match.group("body"))
        label = persona.group("value").strip() if persona is not None else None
        candidates.append(LocalSteamAccountCandidate(steam_id64=steam_id64, local_label=label or None))
    return tuple(candidates)


def discover_local_steam_accounts(steam_root: Path) -> tuple[LocalSteamAccountCandidate, ...]:
    """Read the one disclosed Steam account-list file under an explicit root."""
    if not isinstance(steam_root, Path):
        raise ValueError("steam_root must be an explicit pathlib.Path")
    login_users = steam_root.resolve() / "config" / "loginusers.vdf"
    if not login_users.is_file():
        return ()
    return parse_loginusers_vdf(login_users.read_text(encoding="utf-8", errors="replace"))
