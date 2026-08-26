from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from improve_yourself.map_registry import MapRegistryV1, MapResourceStatus
from improve_yourself.module_integration import ModuleController, ModuleRegistry, ModuleStatus, TACTICAL_PROJECTION_V1
from improve_yourself.tactical_module import (
    TacticalContextV1,
    TacticalPositionSampleV1,
    map_transform_boundary,
    register_tactical_module,
)

ANCIENT_SOURCE_SHA256 = "c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f"


class TacticalProjectionProvider:
    def __init__(self, projection: dict | None) -> None:
        self.projection = projection

    def get_projection(self, contract: str) -> object | None:
        return deepcopy(self.projection) if contract == TACTICAL_PROJECTION_V1 and self.projection is not None else None


def resources() -> Path:
    return Path(__file__).parents[1] / "resources" / "maps"


def projection() -> dict:
    return {
        "schema": TACTICAL_PROJECTION_V1,
        "source": {"sha256": ANCIENT_SOURCE_SHA256, "map_id": "de_ancient"},
        "players": [{"player_id": "steam:76561198009555616", "display_name": "Ancient player"}],
        "rounds": [{"round_number": 1, "start_tick": 1, "end_tick": 3654}],
        "replay_reference": {"schema": "iy.replay/v2", "source_sha256": ANCIENT_SOURCE_SHA256, "reference": "replay"},
    }


def tactical_controller(*, enabled: bool = True, value: dict | None = None, missing: bool = False) -> ModuleController:
    registry = ModuleRegistry()
    register_tactical_module(registry, MapRegistryV1(resources()), enabled=enabled)
    return ModuleController(registry, TacticalProjectionProvider(None if missing else projection() if value is None else value))


def test_tactical_is_registered_and_ready_with_the_tactical_projection_only() -> None:
    result = tactical_controller().resolve("tactical")
    assert result.status is ModuleStatus.READY
    assert isinstance(result.context.projection, TacticalContextV1)
    assert result.context.projection.map_id == "de_ancient"
    assert result.context.projection.map_resource.status is MapResourceStatus.AVAILABLE


def test_tactical_disabled_and_missing_projection_are_not_loaded() -> None:
    assert tactical_controller(enabled=False).resolve("tactical").status is ModuleStatus.DISABLED
    assert tactical_controller(missing=True).resolve("tactical").status is ModuleStatus.UNAVAILABLE


def test_tactical_adapter_failure_is_isolated() -> None:
    broken = projection(); broken["schema"] = "wrong"
    assert tactical_controller(value=broken).resolve("tactical").status is ModuleStatus.ERROR
    assert tactical_controller().resolve("tactical").status is ModuleStatus.READY


def test_map_registry_loads_ancient_and_keeps_unknown_maps_unknown() -> None:
    registry = MapRegistryV1(resources())
    assert registry.get("de_ancient").status is MapResourceStatus.AVAILABLE
    assert registry.get("de_unknown").status is MapResourceStatus.UNKNOWN


def test_hash_bound_ancient_position_fixture_reaches_the_unverified_map_transform_boundary_without_mutating_context() -> None:
    result = tactical_controller().resolve("tactical")
    context = result.context.projection
    sample = TacticalPositionSampleV1(context.source["sha256"], "de_ancient", "steam:76561198009555616", 3654, (-1234.5, 567.25, 89.0))
    boundary = map_transform_boundary(context, sample)
    assert boundary.status == "UNAVAILABLE"
    assert boundary.world_position == (-1234.5, 567.25, 89.0)
    context.players[0]["display_name"] = "consumer mutation"
    assert tactical_controller().resolve("tactical").context.projection.players[0]["display_name"] == "Ancient player"


def test_tactical_strand_never_imports_awpy_or_parses() -> None:
    source_root = Path(__file__).parents[1] / "src" / "improve_yourself"
    for path in (source_root / "tactical_module.py", source_root / "map_registry.py"):
        source = path.read_text(encoding="utf-8").lower()
        assert "awpy" not in source
        assert "parse_demo" not in source
