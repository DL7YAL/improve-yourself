from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .analysis_flow import AnalysisProfile

PROFILE_SCHEMA = "iy.analysis_profile/v1"
PURPOSES = ("review", "highlight", "coaching", "custom")
OBJECTIVE_RULES = (
    "objective_kill", "objective_multi_kill", "objective_headshot", "objective_wallbang",
    "objective_smoke_kill", "objective_blind_kill", "objective_entry",
)
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")


def built_in_profiles() -> tuple[AnalysisProfile, ...]:
    return (
        AnalysisProfile("review_v1", "review"),
        AnalysisProfile("highlight_v1", "highlight", enabled_rule_ids=(
            "objective_multi_kill", "objective_headshot", "objective_wallbang",
            "objective_smoke_kill", "objective_blind_kill",
        )),
        AnalysisProfile("coaching_v1", "coaching", enabled_rule_ids=("objective_entry", "objective_kill")),
        AnalysisProfile("custom_v1", "custom", enabled_rule_ids=OBJECTIVE_RULES),
    )


class LocalProfileStore:
    """User-controlled JSON profiles stored only in the disclosed local directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def list_profiles(self) -> tuple[AnalysisProfile, ...]:
        profiles = {profile.profile_id: profile for profile in built_in_profiles()}
        if self.root.is_dir():
            for path in sorted(self.root.glob("*.json")):
                profile = self._read(path)
                profiles[profile.profile_id] = profile
        return tuple(profiles.values())

    def save(self, profile: AnalysisProfile) -> Path:
        self._validate(profile)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{profile.profile_id}.json"
        payload = {"schema": PROFILE_SCHEMA, **asdict(profile)}
        temporary = path.with_suffix(".json.tmp")
        try:
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return path

    def _read(self, path: Path) -> AnalysisProfile:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema") != PROFILE_SCHEMA:
            raise ValueError(f"invalid local analysis profile: {path.name}")
        profile = AnalysisProfile(
            profile_id=payload.get("profile_id"), purpose=payload.get("purpose"),
            pre_ticks=payload.get("pre_ticks"), post_ticks=payload.get("post_ticks"),
            merge_gap_ticks=payload.get("merge_gap_ticks"),
            enabled_rule_ids=(tuple(payload["enabled_rule_ids"]) if payload.get("enabled_rule_ids") is not None else None),
        )
        self._validate(profile)
        return profile

    @staticmethod
    def _validate(profile: AnalysisProfile) -> None:
        if _SAFE_ID.fullmatch(profile.profile_id) is None:
            raise ValueError("profile_id must be a safe lowercase local identifier")
        if profile.purpose not in PURPOSES:
            raise ValueError("profile purpose must be review, highlight, coaching or custom")
        if any(not isinstance(value, int) or value < 0 for value in (profile.pre_ticks, profile.post_ticks, profile.merge_gap_ticks)):
            raise ValueError("profile tick windows must be non-negative integers")
        unknown = set(profile.enabled_rule_ids or ()) - set(OBJECTIVE_RULES)
        if unknown:
            raise ValueError(f"unknown objective rules: {sorted(unknown)}")
