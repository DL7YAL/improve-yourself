import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from improve_yourself.cs2_review_coordinator import Cs2ReviewCoordinator, DemoReadiness, ReviewCoordinatorServer


class FakeNetcon:
    def __init__(self, readiness: DemoReadiness) -> None:
        self.result = readiness
        self.sent: list[int] = []

    def readiness(self) -> DemoReadiness:
        return self.result

    def goto_tick(self, tick: int) -> None:
        self.sent.append(tick)


def _flow(path: Path) -> Path:
    path.write_text(
        json.dumps({"scenes": [{"scene_id": "r1-t3654-0", "review": {"tick": 3654}}]}),
        encoding="utf-8",
    )
    return path


def test_coordinator_sends_only_generated_pair_for_expected_demo(tmp_path: Path) -> None:
    netcon = FakeNetcon(DemoReadiness(True, "match.dem", "Client: Connected [DEMO]"))
    coordinator = Cs2ReviewCoordinator(_flow(tmp_path / "flow.json"), "match.dem", netcon=netcon)
    result = coordinator.open_scene("r1-t3654-0", 3654)
    assert result == {"status": "sent", "scene_id": "r1-t3654-0", "tick": 3654, "demo_name": "match.dem"}
    assert netcon.sent == [3654]


def test_coordinator_fails_closed_for_wrong_scene_or_demo(tmp_path: Path) -> None:
    netcon = FakeNetcon(DemoReadiness(True, "other.dem", "Client: Connected [DEMO]"))
    coordinator = Cs2ReviewCoordinator(_flow(tmp_path / "flow.json"), "match.dem", netcon=netcon)
    with pytest.raises(ValueError, match="scene/tick pair"):
        coordinator.open_scene("r1-t3654-0", 999)
    with pytest.raises(RuntimeError, match="Falsche Demo"):
        coordinator.open_scene("r1-t3654-0", 3654)
    assert netcon.sent == []


def test_preflight_reports_each_readiness_boundary(tmp_path: Path) -> None:
    class MissingNetcon:
        def readiness(self) -> DemoReadiness:
            raise ConnectionRefusedError("offline")

    missing = Cs2ReviewCoordinator(_flow(tmp_path / "missing.json"), "match.dem", netcon=MissingNetcon())
    assert missing.preflight().netcon_reachable is False

    inactive = Cs2ReviewCoordinator(
        _flow(tmp_path / "inactive.json"),
        "match.dem",
        netcon=FakeNetcon(DemoReadiness(False, None, "Server: Inactive")),
    ).preflight()
    assert inactive.netcon_reachable is True
    assert inactive.demo_active is False
    assert inactive.ready is False

    ready = Cs2ReviewCoordinator(
        _flow(tmp_path / "ready.json"),
        "MATCH.DEM",
        netcon=FakeNetcon(DemoReadiness(True, "match.dem", "Client: Connected [DEMO]")),
    ).preflight()
    assert ready.netcon_reachable is True
    assert ready.demo_active is True
    assert ready.filename_matches is True
    assert ready.ready is True


def test_loopback_server_enforces_origin_and_returns_status(tmp_path: Path) -> None:
    review = tmp_path / "review.html"
    review.write_text("<h1>review</h1>", encoding="utf-8")
    netcon = FakeNetcon(DemoReadiness(True, "match.dem", "Client: Connected [DEMO]"))
    coordinator = Cs2ReviewCoordinator(_flow(tmp_path / "flow.json"), "match.dem", netcon=netcon)
    server = ReviewCoordinatorServer(review, coordinator)
    server.start()
    try:
        assert urllib.request.urlopen(server.url, timeout=2).read() == b"<h1>review</h1>"
        payload = json.dumps({"scene_id": "r1-t3654-0", "tick": 3654}).encode()
        request = urllib.request.Request(
            server.url + "api/cs2/tick",
            data=payload,
            headers={"Content-Type": "application/json", "Origin": server.url.rstrip("/")},
        )
        response = json.loads(urllib.request.urlopen(request, timeout=2).read())
        assert response["status"] == "sent"

        rejected = urllib.request.Request(
            server.url + "api/cs2/tick",
            data=payload,
            headers={"Content-Type": "application/json", "Origin": "http://example.invalid"},
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(rejected, timeout=2)
        assert error.value.code == 403

        oversized = urllib.request.Request(
            server.url + "api/cs2/tick",
            data=b"x" * 1025,
            headers={"Content-Type": "application/json", "Origin": server.url.rstrip("/")},
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(oversized, timeout=2)
        assert error.value.code == 413
    finally:
        server.close()
