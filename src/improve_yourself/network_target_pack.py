"""Versioned, privacy-reviewed target catalog for the existing network collector."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Iterable

from .network_quality import NetworkTarget, TargetClass


TARGET_PACK_SCHEMA = "iy.network_target_pack/v1"


class TargetStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    TEMPORARILY_DISABLED = "TEMPORARILY_DISABLED"


@dataclass(frozen=True)
class ControlledTarget:
    target_id: str
    display_name: str
    target_class: TargetClass
    host: str | None
    protocol: str
    purpose: str
    owner: str | None
    privacy_notice: str
    expected_disclosure: str
    interpretation_scope: str
    version: str
    valid_from: str
    valid_until: str | None
    status: TargetStatus
    technical_prerequisites: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["target_class"] = self.target_class.value
        data["status"] = self.status.value
        return data


def v1_target_pack() -> dict[str, object]:
    """Small V1 pack: no uncontrolled external or game endpoint is asserted."""
    target = ControlledTarget(
        "local-gateway-template", "Lokales Standard-Gateway", TargetClass.LOCAL_GATEWAY, None,
        "ICMP_ECHO", "Misst die lokale Verbindung bis zum vom Nutzer bestätigten Standard-Gateway.",
        "Lokales Netzwerk des Nutzers", "Die Messung kontaktiert ausschließlich die vom Nutzer bestätigte lokale Gateway-Adresse.",
        "Die Zieladresse erhält ICMP-Anfragen; Ergebnisse bleiben ausschließlich lokal.",
        "LOCAL_CONNECTION_ONLY; keine Aussage zu Internet-, CS2- oder FACEIT-Latenz.",
        "1.0.0", "2025-01-01", None, TargetStatus.ACTIVE,
        ("Der Nutzer muss die lokale Gateway-Adresse vor Start bestätigen.", "Kein Host wird automatisch entdeckt oder kontaktiert."),
    )
    return {"schema": TARGET_PACK_SCHEMA, "pack_id": "improve-controlled-network-targets", "pack_version": "1.0.0", "reviewed_at_utc": "2026-08-22T00:00:00+00:00", "targets": [target.as_dict()]}


def _today(value: datetime | None = None) -> date:
    return (value or datetime.now(UTC)).date()


def select_target(pack: dict[str, object], target_id: str, *, resolved_host: str | None, user_confirmed: bool, now: datetime | None = None) -> NetworkTarget:
    """Authorize an explicitly selected target; never contact a host by itself."""
    if pack.get("schema") != TARGET_PACK_SCHEMA or not isinstance(pack.get("targets"), list):
        raise ValueError("invalid target-pack schema")
    selected = next((item for item in pack["targets"] if isinstance(item, dict) and item.get("target_id") == target_id), None)
    if selected is None:
        raise ValueError("unknown target_id")
    if selected.get("status") != TargetStatus.ACTIVE.value:
        raise ValueError("target is not active")
    today = _today(now)
    if date.fromisoformat(str(selected["valid_from"])) > today or (selected.get("valid_until") and date.fromisoformat(str(selected["valid_until"])) < today):
        raise ValueError("target is outside its validity window")
    host = selected.get("host") or resolved_host
    if not isinstance(host, str) or not host.strip():
        raise ValueError("selected target requires an explicit resolved_host")
    if not user_confirmed:
        raise PermissionError("explicit user confirmation is required before measurement")
    return NetworkTarget(str(selected["target_id"]), TargetClass(str(selected["target_class"])), host, str(selected["purpose"]), str(selected["version"]), str(pack["pack_version"]))


def selection_view_model(pack: dict[str, object], target_id: str) -> dict[str, object]:
    selected = next((item for item in pack.get("targets", []) if isinstance(item, dict) and item.get("target_id") == target_id), None)
    if selected is None:
        raise ValueError("unknown target_id")
    return {"target_id": selected["target_id"], "display_name": selected["display_name"], "purpose": selected["purpose"], "target_class": selected["target_class"], "privacy_notice": selected["privacy_notice"], "expected_disclosure": selected["expected_disclosure"], "protocol": selected["protocol"], "requires_user_confirmation": True, "measurement_starts_automatically": False}
