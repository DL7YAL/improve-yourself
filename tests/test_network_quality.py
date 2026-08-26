from __future__ import annotations

from improve_yourself.network_quality import (
    MeasurementStatus,
    NetworkTarget,
    ProbeResult,
    TargetClass,
    collect_network_quality,
    network_quality_evidence,
    summarize_probes,
)


def test_rtt_jitter_and_partial_loss_are_methodically_reported() -> None:
    summary = summarize_probes([ProbeResult(1, 10, "success"), ProbeResult(2, None, "timeout"), ProbeResult(3, 16, "success"), ProbeResult(4, 13, "success")], requested=4)
    assert summary["status"] == MeasurementStatus.VALID
    assert summary["packet_loss_percent"] == 25
    assert summary["rtt_ms"]["mean"] == 13
    assert summary["jitter_ms"] == 4.5


def test_unreachable_target_is_not_presented_as_connection_packet_loss() -> None:
    summary = summarize_probes([ProbeResult(1, None, "timeout"), ProbeResult(2, None, "timeout")], requested=2)
    assert summary["status"] == MeasurementStatus.TIMEOUT
    assert summary["packet_loss_percent"] is None
    assert "not interpreted" in summary["note"]


def test_collector_is_deterministic_with_recorded_probes_and_sanitizes_adapter() -> None:
    recorded = iter([ProbeResult(1, 8, "success"), ProbeResult(2, 9, "success"), ProbeResult(3, 8, "success")])
    measurement = collect_network_quality(NetworkTarget("fixture-gateway", TargetClass.LOCAL_GATEWAY, "gateway.example", "fixture"), sample_count=3, interval_ms=0, measurement_session_id="session-1", adapter_context={"name": "NIC", "mtu": 1500, "mac_address": "must-not-persist"}, probe=lambda _host, _timeout, _sequence: next(recorded))
    assert measurement["schema"] == "iy.network_quality_measurement/v1"
    assert measurement["summary"]["status"] == MeasurementStatus.VALID
    assert measurement["adapter_context"] == {"name": "NIC", "mtu": 1500}
    assert measurement["policy"] == {"read_only": True, "external_transfer": False, "public_ip_persisted": False}
    assert measurement["target"]["target_class"] == TargetClass.LOCAL_GATEWAY


def test_quality_observation_integrates_as_evidence_not_a_recommendation() -> None:
    measurement = collect_network_quality(NetworkTarget("fixture", TargetClass.CONTROLLED_PUBLIC_TARGET, "declared.example", "fixture"), sample_count=1, interval_ms=0, measurement_session_id="session-2", probe=lambda *_args: ProbeResult(1, 10, "success"))
    evidence = network_quality_evidence(measurement)
    assert evidence.source_type == "OBSERVED_NETWORK_QUALITY"
    assert evidence.result == MeasurementStatus.TOO_FEW_SAMPLES
    assert "causation" in evidence.provenance
