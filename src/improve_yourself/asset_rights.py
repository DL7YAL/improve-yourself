"""Fail-closed distribution gate for optional visual assets."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


ASSET_RIGHTS_SCHEMA = "iy.asset_rights/v1"
RightsStatus = Literal[
    "OWNED",
    "LICENSED_FOR_DISTRIBUTION",
    "LICENSED_INTERNAL_ONLY",
    "THIRD_PARTY_REFERENCE_ONLY",
    "PUBLICATION_BLOCKED",
    "UNKNOWN",
]
_KNOWN_STATUSES = {
    "OWNED",
    "LICENSED_FOR_DISTRIBUTION",
    "LICENSED_INTERNAL_ONLY",
    "THIRD_PARTY_REFERENCE_ONLY",
    "PUBLICATION_BLOCKED",
    "UNKNOWN",
}
_PUBLIC_ALLOWED = {"OWNED", "LICENSED_FOR_DISTRIBUTION"}
_INTERNAL_ALLOWED = _PUBLIC_ALLOWED | {"LICENSED_INTERNAL_ONLY", "THIRD_PARTY_REFERENCE_ONLY"}


@dataclass(frozen=True)
class RightsDecision:
    allowed: bool
    channel: str
    blocked_asset_ids: tuple[str, ...]
    detail: str


class AssetRightsError(ValueError):
    """The rights manifest is malformed and cannot authorize distribution."""


def _validate_document(document: object) -> dict:
    if not isinstance(document, dict) or document.get("schema") != ASSET_RIGHTS_SCHEMA:
        raise AssetRightsError("asset rights schema is invalid")
    assets = document.get("assets")
    if not isinstance(assets, list) or not assets:
        raise AssetRightsError("asset rights manifest must contain assets")
    seen: set[str] = set()
    for item in assets:
        if not isinstance(item, dict):
            raise AssetRightsError("asset rights entry must be an object")
        asset_id = item.get("asset_id")
        status = item.get("status")
        evidence = item.get("evidence")
        if not isinstance(asset_id, str) or not asset_id or asset_id in seen:
            raise AssetRightsError("asset IDs must be non-empty and unique")
        if status not in _KNOWN_STATUSES:
            raise AssetRightsError(f"asset rights status is invalid for {asset_id}")
        if not isinstance(evidence, str) or not evidence:
            raise AssetRightsError(f"rights evidence is missing for {asset_id}")
        seen.add(asset_id)
    return document


def load_asset_rights(path: Path) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssetRightsError("asset rights manifest is not readable") from error
    return _validate_document(document)


def assess_asset_rights(document: dict, channel: Literal["internal", "public"]) -> RightsDecision:
    document = _validate_document(document)
    allowed_statuses = _PUBLIC_ALLOWED if channel == "public" else _INTERNAL_ALLOWED
    blocked = tuple(
        str(item.get("asset_id", "UNKNOWN"))
        for item in document["assets"]
        if not isinstance(item, dict) or item.get("status") not in allowed_statuses
    )
    if blocked:
        return RightsDecision(False, channel, blocked, f"{channel} distribution blocked by rights evidence")
    return RightsDecision(True, channel, (), f"{channel} distribution rights gate passed")
