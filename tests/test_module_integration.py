from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from improve_yourself.module_integration import (
    ANALYZER_PROJECTION_V1,
    MODULE_ADAPTER_CONTRACT_V1,
    AnalyzerDataHubProjectionProvider,
    ModuleContextV1,
    ModuleController,
    ModuleDefinitionV1,
    ModuleRegistry,
    ModuleStatus,
)


class ProjectionProviderStub:
    def __init__(self, projections: dict[str, object] | None = None) -> None:
        self.projections = projections or {}

    def get_projection(self, contract: str) -> object | None:
        value = self.projections.get(contract)
        return None if value is None else deepcopy(value)


class DummyAdapter:
    module_id = "dummy"
    required_contract = ANALYZER_PROJECTION_V1
    calls = 0

    def validate_dependencies(self, projection: object) -> None:
        assert isinstance(projection, dict)
        assert projection["contract"] == ANALYZER_PROJECTION_V1

    def prepare_input(self, projection: object) -> object:
        self.calls += 1
        return projection

    def create_module_context(self, prepared_input: object) -> ModuleContextV1:
        return ModuleContextV1(self.module_id, self.required_contract, prepared_input)


class BrokenAdapter(DummyAdapter):
    module_id = "broken"

    def prepare_input(self, projection: object) -> object:
        raise RuntimeError("intentional isolated failure")


def definition(module_id: str = "dummy", *, enabled: bool = True, contract: str = ANALYZER_PROJECTION_V1) -> ModuleDefinitionV1:
    return ModuleDefinitionV1(module_id, 1, MODULE_ADAPTER_CONTRACT_V1, contract, enabled=enabled, optional=True)


def test_registered_module_resolves_only_its_versioned_projection() -> None:
    payload = {"contract": ANALYZER_PROJECTION_V1, "nested": {"value": 1}}
    registry = ModuleRegistry(); adapter = DummyAdapter(); registry.register(definition(), lambda: adapter)
    result = ModuleController(registry, ProjectionProviderStub({ANALYZER_PROJECTION_V1: payload})).resolve("dummy")
    assert result.status is ModuleStatus.READY
    assert result.context is not None
    assert result.context.projection == payload
    assert adapter.calls == 1


def test_disabled_module_is_not_instantiated_or_prepared() -> None:
    registry = ModuleRegistry(); calls = 0
    def factory() -> DummyAdapter:
        nonlocal calls; calls += 1; return DummyAdapter()
    registry.register(definition(enabled=False), factory)
    result = ModuleController(registry, ProjectionProviderStub({ANALYZER_PROJECTION_V1: {}})).resolve("dummy")
    assert result.status is ModuleStatus.DISABLED
    assert calls == 0


def test_missing_projection_and_unknown_module_are_unavailable() -> None:
    registry = ModuleRegistry(); registry.register(definition(), DummyAdapter)
    controller = ModuleController(registry, ProjectionProviderStub())
    assert controller.resolve("dummy").status is ModuleStatus.UNAVAILABLE
    assert controller.resolve("unknown").status is ModuleStatus.UNAVAILABLE


def test_wrong_contract_is_rejected_at_registration() -> None:
    registry = ModuleRegistry()
    wrong = ModuleDefinitionV1("dummy", 1, "iy.module_adapter/v2", ANALYZER_PROJECTION_V1)
    try:
        registry.register(wrong, DummyAdapter)
    except ValueError as error:
        assert "adapter contract" in str(error)
    else:
        raise AssertionError("wrong contract must be rejected")


def test_optional_module_failure_is_isolated() -> None:
    registry = ModuleRegistry()
    registry.register(definition(), DummyAdapter)
    registry.register(definition("broken"), BrokenAdapter)
    controller = ModuleController(registry, ProjectionProviderStub({ANALYZER_PROJECTION_V1: {"contract": ANALYZER_PROJECTION_V1}}))
    assert controller.resolve("broken").status is ModuleStatus.ERROR
    assert controller.resolve("dummy").status is ModuleStatus.READY


def test_hub_and_each_module_context_are_mutation_isolated() -> None:
    original = {"contract": ANALYZER_PROJECTION_V1, "nested": {"value": 1}}
    registry = ModuleRegistry(); registry.register(definition(), DummyAdapter)
    controller = ModuleController(registry, ProjectionProviderStub({ANALYZER_PROJECTION_V1: original}))
    first = controller.resolve("dummy").context
    assert first is not None
    first.projection["nested"]["value"] = 99
    second = controller.resolve("dummy").context
    assert second is not None
    assert second.projection["nested"]["value"] == 1
    assert original["nested"]["value"] == 1


def test_existing_analyzer_data_hub_is_used_via_narrow_provider() -> None:
    class ExistingHubStub:
        def for_consumer(self, consumer: str) -> dict[str, str]:
            return {"schema": ANALYZER_PROJECTION_V1, "consumer": consumer}
    provider = AnalyzerDataHubProjectionProvider(ExistingHubStub())  # type: ignore[arg-type]
    assert provider.get_projection(ANALYZER_PROJECTION_V1) == {"schema": ANALYZER_PROJECTION_V1, "consumer": "analyzer"}
    assert provider.get_projection("iy.unknown_projection/v1") is None


def test_module_integration_and_adapters_do_not_import_awpy_or_trigger_parsing() -> None:
    source_root = Path(__file__).parents[1] / "src" / "improve_yourself"
    for path in (source_root / "module_integration.py",):
        assert "awpy" not in path.read_text(encoding="utf-8").lower()
