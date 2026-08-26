from __future__ import annotations

from datetime import UTC, datetime

import pytest

from improve_yourself.network_quality import ProbeResult, collect_network_quality
from improve_yourself.network_target_pack import TargetStatus, select_target, selection_view_model, v1_target_pack


def test_v1_pack_is_versioned_transparent_and_contains_only_reviewed_local_target() -> None:
    pack = v1_target_pack()
    assert pack["schema"] == "iy.network_target_pack/v1"
    assert pack["pack_version"] == "1.0.0"
    assert len(pack["targets"]) == 1
    target = pack["targets"][0]
    assert target["target_id"] == "local-gateway-template"
    assert target["target_class"] == "LOCAL_GATEWAY"
    assert target["host"] is None
    assert target["status"] == TargetStatus.ACTIVE
    assert target["valid_from"] and target["privacy_notice"] and target["expected_disclosure"]


def test_selection_requires_known_active_valid_target_explicit_host_and_consent() -> None:
    pack = v1_target_pack()
    with pytest.raises(ValueError, match="unknown"):
        select_target(pack, "missing", resolved_host="192.168.1.1", user_confirmed=True)
    with pytest.raises(ValueError, match="resolved_host"):
        select_target(pack, "local-gateway-template", resolved_host=None, user_confirmed=True)
    with pytest.raises(PermissionError):
        select_target(pack, "local-gateway-template", resolved_host="192.168.1.1", user_confirmed=False)
    target = select_target(pack, "local-gateway-template", resolved_host="192.168.1.1", user_confirmed=True)
    assert target.target_pack_version == "1.0.0"


def test_disabled_deprecated_and_expired_targets_cannot_be_selected() -> None:
    pack = v1_target_pack()
    pack["targets"][0]["status"] = TargetStatus.DEPRECATED
    with pytest.raises(ValueError, match="not active"):
        select_target(pack, "local-gateway-template", resolved_host="192.168.1.1", user_confirmed=True)
    pack = v1_target_pack()
    pack["targets"][0]["valid_until"] = "2026-01-01"
    with pytest.raises(ValueError, match="validity"):
        select_target(pack, "local-gateway-template", resolved_host="192.168.1.1", user_confirmed=True, now=datetime(2026, 8, 22, tzinfo=UTC))


def test_collector_records_pack_version_for_historical_interpretation_without_contact() -> None:
    target = select_target(v1_target_pack(), "local-gateway-template", resolved_host="192.168.1.1", user_confirmed=True)
    measurement = collect_network_quality(target, sample_count=1, interval_ms=0, measurement_session_id="historical", probe=lambda *_args: ProbeResult(1, None, "timeout"))
    assert measurement["target_pack_version"] == "1.0.0"
    assert measurement["target"]["target_id"] == "local-gateway-template"
    assert measurement["summary"]["packet_loss_percent"] is None


def test_selection_view_has_required_consent_details_without_starting_measurement() -> None:
    view = selection_view_model(v1_target_pack(), "local-gateway-template")
    assert view["requires_user_confirmation"] is True
    assert view["measurement_starts_automatically"] is False
    assert view["purpose"] and view["privacy_notice"]
