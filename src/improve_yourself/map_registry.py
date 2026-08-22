"""Static map-resource lookup; dynamic match data never belongs here."""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


MAP_RESOURCE_SCHEMA_V1 = "iy.map_resource/v1"


class MapResourceStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class MapResourceV1:
    map_id: str
    resource_root: Path
    transform: dict[str, Any]


@dataclass(frozen=True)
class MapResolutionV1:
    map_id: str
    status: MapResourceStatus
    resource: MapResourceV1 | None = None
    detail: str | None = None


class MapRegistryV1:
    """Loads declared static resource metadata; it does not inspect demos."""

    def __init__(self, resources_root: Path) -> None:
        self._resources_root = resources_root

    def get(self, map_id: str) -> MapResolutionV1:
        metadata_path = self._resources_root / map_id / "map.json"
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return MapResolutionV1(map_id, MapResourceStatus.UNKNOWN, detail="map resource is not registered")
        except json.JSONDecodeError as error:
            return MapResolutionV1(map_id, MapResourceStatus.UNKNOWN, detail=f"map metadata is invalid: {error}")
        if payload.get("schema") != MAP_RESOURCE_SCHEMA_V1 or payload.get("map_id") != map_id:
            return MapResolutionV1(map_id, MapResourceStatus.UNKNOWN, detail="map metadata contract differs")
        transform = payload.get("transform")
        if not isinstance(transform, dict):
            return MapResolutionV1(map_id, MapResourceStatus.UNKNOWN, detail="map transform metadata is missing")
        return MapResolutionV1(map_id, MapResourceStatus.AVAILABLE, MapResourceV1(map_id, metadata_path.parent, transform))
