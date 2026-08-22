"""Small, local-only module integration contracts for Improve Yourself V1."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol


MODULE_ADAPTER_CONTRACT_V1 = "iy.module_adapter/v1"
ANALYZER_PROJECTION_V1 = "iy.analyzer_projection/v1"
TACTICAL_PROJECTION_V1 = "iy.tactical_projection/v1"
REVIEW_PROJECTION_V1 = "iy.review_projection/v1"
REPORT_PROJECTION_V1 = "iy.report_projection/v1"


class ModuleStatus(StrEnum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ModuleDefinitionV1:
    module_id: str
    module_version: int
    adapter_contract: str
    required_projection: str
    enabled: bool = True
    optional: bool = True


@dataclass(frozen=True)
class ModuleContextV1:
    """Private copy of the single projection a module is allowed to consume."""

    module_id: str
    projection_contract: str
    projection: Any


@dataclass(frozen=True)
class ModuleResolutionV1:
    module_id: str
    status: ModuleStatus
    context: ModuleContextV1 | None = None
    detail: str | None = None


class ModuleAdapterV1(Protocol):
    module_id: str
    required_contract: str

    def validate_dependencies(self, projection: Any) -> None: ...

    def prepare_input(self, projection: Any) -> Any: ...

    def create_module_context(self, prepared_input: Any) -> ModuleContextV1: ...


class AnalyzerDataHubV1:
    """Versioned projections only; it never parses demos or exposes raw parser data."""

    def __init__(self, projections: Mapping[str, Any] | None = None) -> None:
        self._projections = deepcopy(dict(projections or {}))

    def get_projection(self, contract: str) -> Any | None:
        value = self._projections.get(contract)
        return None if value is None else deepcopy(value)


class ModuleRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, tuple[ModuleDefinitionV1, ModuleAdapterV1]] = {}

    def register(self, definition: ModuleDefinitionV1, adapter: ModuleAdapterV1) -> None:
        if definition.module_id != adapter.module_id:
            raise ValueError("module definition and adapter ids differ")
        if definition.adapter_contract != MODULE_ADAPTER_CONTRACT_V1:
            raise ValueError("unsupported adapter contract")
        if adapter.required_contract != definition.required_projection:
            raise ValueError("adapter and required projection differ")
        if definition.module_id in self._entries:
            raise ValueError(f"module already registered: {definition.module_id}")
        self._entries[definition.module_id] = (definition, adapter)

    def get(self, module_id: str) -> tuple[ModuleDefinitionV1, ModuleAdapterV1] | None:
        return self._entries.get(module_id)

    def known_modules(self) -> tuple[ModuleDefinitionV1, ...]:
        return tuple(definition for definition, _ in self._entries.values())


class ModuleController:
    def __init__(self, registry: ModuleRegistry, data_hub: AnalyzerDataHubV1) -> None:
        self._registry = registry
        self._data_hub = data_hub

    def resolve(self, module_id: str) -> ModuleResolutionV1:
        entry = self._registry.get(module_id)
        if entry is None:
            return ModuleResolutionV1(module_id, ModuleStatus.UNAVAILABLE, detail="module is not registered")
        definition, adapter = entry
        if not definition.enabled:
            return ModuleResolutionV1(module_id, ModuleStatus.DISABLED, detail="module is disabled")
        projection = self._data_hub.get_projection(definition.required_projection)
        if projection is None:
            return ModuleResolutionV1(module_id, ModuleStatus.UNAVAILABLE, detail="required projection is unavailable")
        try:
            adapter.validate_dependencies(projection)
            prepared = adapter.prepare_input(projection)
            context = adapter.create_module_context(deepcopy(prepared))
            if context.module_id != module_id or context.projection_contract != definition.required_projection:
                raise ValueError("adapter returned an incompatible module context")
            return ModuleResolutionV1(module_id, ModuleStatus.READY, context=deepcopy(context))
        except Exception as error:
            return ModuleResolutionV1(module_id, ModuleStatus.ERROR, detail=str(error))
