"""Local user identity profile, deliberately separate from analysis profiles."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re

from .local_steam_accounts import LOCAL_STEAM_ACCOUNT_SOURCE, LocalSteamAccountCandidate


USER_PROFILE_SCHEMA = "iy.user_profile/v1"
_SAFE_PROFILE_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
_STEAM_ID64 = re.compile(r"7656119\d{10}")
_ACCOUNT_STATES = {
    "DETECTED_LOCAL",
    "USER_CONFIRMED_LOCAL",
    "ACTIVE_FOR_PERSONAL_MATCHING",
    "INACTIVE",
}


@dataclass(frozen=True)
class UserSteamAccount:
    steam_id64: str
    local_label: str | None
    state: str
    source: str = LOCAL_STEAM_ACCOUNT_SOURCE
    user_confirmed: bool = False


@dataclass(frozen=True)
class UserProfile:
    profile_id: str
    display_name: str | None
    steam_accounts: tuple[UserSteamAccount, ...]
    active_steam_id64: str | None
    created_at: str
    updated_at: str


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def profile_from_candidates(
    profile_id: str, candidates: tuple[LocalSteamAccountCandidate, ...], *, display_name: str | None = None
) -> UserProfile:
    """Create an unselected profile; the caller must explicitly confirm/select one account."""
    now = _timestamp()
    return UserProfile(
        profile_id=profile_id,
        display_name=display_name,
        steam_accounts=tuple(
            UserSteamAccount(candidate.steam_id64, candidate.local_label, "DETECTED_LOCAL") for candidate in candidates
        ),
        active_steam_id64=None,
        created_at=now,
        updated_at=now,
    )


def select_active_account(profile: UserProfile, steam_id64: str) -> UserProfile:
    """Record one user-confirmed local account as the sole personal-match identity."""
    if steam_id64 not in {account.steam_id64 for account in profile.steam_accounts}:
        raise ValueError("selected Steam account is not a detected local candidate")
    now = _timestamp()
    accounts = tuple(
        UserSteamAccount(
            account.steam_id64,
            account.local_label,
            "ACTIVE_FOR_PERSONAL_MATCHING" if account.steam_id64 == steam_id64 else "INACTIVE",
            account.source,
            True,
        )
        for account in profile.steam_accounts
    )
    return UserProfile(profile.profile_id, profile.display_name, accounts, steam_id64, profile.created_at, now)


class LocalUserProfileStore:
    """User-controlled JSON storage under one disclosed, caller-provided local root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def save(self, profile: UserProfile) -> Path:
        self._validate(profile)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{profile.profile_id}.json"
        temporary = path.with_suffix(".json.tmp")
        try:
            temporary.write_text(json.dumps({"schema": USER_PROFILE_SCHEMA, **asdict(profile)}, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return path

    def load(self, profile_id: str) -> UserProfile:
        if _SAFE_PROFILE_ID.fullmatch(profile_id) is None:
            raise ValueError("profile_id must be a safe lowercase local identifier")
        path = self.root / f"{profile_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        allowed = {"schema", "profile_id", "display_name", "steam_accounts", "active_steam_id64", "created_at", "updated_at"}
        if not isinstance(payload, dict) or payload.get("schema") != USER_PROFILE_SCHEMA or set(payload) != allowed:
            raise ValueError("invalid local user profile")
        raw_accounts = payload.get("steam_accounts")
        if not isinstance(raw_accounts, list) or any(not isinstance(account, dict) for account in raw_accounts):
            raise ValueError("invalid local user profile accounts")
        profile = UserProfile(
            profile_id=payload.get("profile_id"), display_name=payload.get("display_name"),
            steam_accounts=tuple(UserSteamAccount(**account) for account in raw_accounts),
            active_steam_id64=payload.get("active_steam_id64"), created_at=payload.get("created_at"), updated_at=payload.get("updated_at"),
        )
        self._validate(profile)
        return profile

    @staticmethod
    def _validate(profile: UserProfile) -> None:
        if not isinstance(profile.profile_id, str) or _SAFE_PROFILE_ID.fullmatch(profile.profile_id) is None:
            raise ValueError("profile_id must be a safe lowercase local identifier")
        if profile.display_name is not None and not isinstance(profile.display_name, str):
            raise ValueError("display_name must be text or null")
        ids: set[str] = set()
        for account in profile.steam_accounts:
            if _STEAM_ID64.fullmatch(account.steam_id64) is None:
                raise ValueError("Steam account ID must be a SteamID64")
            if account.steam_id64 in ids:
                raise ValueError("duplicate Steam account ID")
            ids.add(account.steam_id64)
            if account.state not in _ACCOUNT_STATES:
                raise ValueError("invalid local Steam account state")
            if account.source != LOCAL_STEAM_ACCOUNT_SOURCE:
                raise ValueError("unsupported local Steam account source")
        active = [account for account in profile.steam_accounts if account.state == "ACTIVE_FOR_PERSONAL_MATCHING"]
        if profile.active_steam_id64 is None:
            if active:
                raise ValueError("active account state requires active_steam_id64")
        elif profile.active_steam_id64 not in ids or len(active) != 1 or active[0].steam_id64 != profile.active_steam_id64:
            raise ValueError("exactly one matching active Steam account is required")
        elif active[0].user_confirmed is not True:
            raise ValueError("active Steam account must be user confirmed")
