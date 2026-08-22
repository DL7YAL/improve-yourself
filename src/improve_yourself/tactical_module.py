"""Tactical V1 module skeleton over the versioned Tactical projection only."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .map_registry import MapRegistryV1, MapResolutionV1, MapResourceStatus
from .module_integration import (
    MODULE_ADAPTER_CONTRACT_V1,
    TACTICAL_PROJECTION_V1,
    ModuleContextV1,
    ModuleDefinitionV1,
    ModuleRegistry,
)


TACTICAL_MODULE_ID = "tactical"


@dataclass(frozen=True)
class TacticalContextV1:
    """Narrow dynamic match input; large position state stays in replay-v2."""

    source: dict[str, Any]
    map_id: str
    players: tuple[dict[str, Any], ...]
    rounds: tuple[dict[str, Any], ...]
    replay_reference: dict[str, Any]
    map_resource: MapResolutionV1


@dataclass(frozen=True)
class TacticalPositionSampleV1:
    """An explicit canonical replay sample, never obtained by parsing here."""

    source_sha256: str
    map_id: str
    player_id: str
    tick: int
    world_position: tuple[float, float, float]


@dataclass(frozen=True)
class MapTransformBoundaryV1:
    status: str
    world_position: tuple[float, float, float]
    detail: str


def map_transform_boundary(context: TacticalContextV1, sample: TacticalPositionSampleV1) -> MapTransformBoundaryV1:
    """Preserve a canonical world position until static transform evidence exists."""
    if sample.map_id != context.map_id or sample.source_sha256 != context.source.get("sha256"):
        raise ValueError("position sample is not bound to this tactical context")
    if context.map_resource.status is not MapResourceStatus.AVAILABLE:
        return MapTransformBoundaryV1("UNAVAILABLE", sample.world_position, "map resource is unknown")
    transform_status = context.map_resource.resource.transform.get("status") if context.map_resource.resource else None
    if transform_status != "VERIFIED":
        return MapTransformBoundaryV1("UNAVAILABLE", sample.world_position, "map transform is not verified")
    raise ValueError("verified map transforms are not implemented in the V1 skeleton")


class TacticalModuleAdapterV1:
    module_id = TACTICAL_MODULE_ID
    required_contract = TACTICAL_PROJECTION_V1

    def __init__(self, map_registry: MapRegistryV1) -> None:
        self._map_registry = map_registry

    def validate_dependencies(self, projection: Any) -> None:
        if not isinstance(projection, dict) or projection.get("schema") != TACTICAL_PROJECTION_V1:
            raise ValueError(f"expected {TACTICAL_PROJECTION_V1}")
        source = projection.get("source")
        if not isinstance(source, dict) or not isinstance(source.get("sha256"), str):
            raise ValueError("tactical projection source is missing")
        map_id = source.get("map_id")
        if not isinstance(map_id, str) or not map_id:
            raise ValueError("tactical projection map_id is missing")
        if not isinstance(projection.get("players"), list) or not isinstance(projection.get("rounds"), list):
            raise ValueError("tactical projection identity context is missing")
        reference = projection.get("replay_reference")
        if not isinstance(reference, dict) or reference.get("schema") != "iy.replay/v2":
            raise ValueError("canonical replay reference is missing")

    def prepare_input(self, projection: Any) -> TacticalContextV1:
        source = deepcopy(projection["source"])
        return TacticalContextV1(
            source=source,
            map_id=source["map_id"],
            players=tuple(deepcopy(projection["players"])),
            rounds=tuple(deepcopy(projection["rounds"])),
            replay_reference=deepcopy(projection["replay_reference"]),
            map_resource=self._map_registry.get(source["map_id"]),
        )

    def create_module_context(self, prepared_input: TacticalContextV1) -> ModuleContextV1:
        return ModuleContextV1(self.module_id, self.required_contract, prepared_input)


def register_tactical_module(registry: ModuleRegistry, map_registry: MapRegistryV1, *, enabled: bool = True) -> None:
    """Explicit registration only; no discovery or plugin loading."""
    registry.register(
        ModuleDefinitionV1(TACTICAL_MODULE_ID, 1, MODULE_ADAPTER_CONTRACT_V1, TACTICAL_PROJECTION_V1, enabled=enabled, optional=True),
        lambda: TacticalModuleAdapterV1(map_registry),
    )
