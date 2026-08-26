from __future__ import annotations

from copy import deepcopy

import pytest

from improve_yourself.analyzer_shell import optimizer_product_view
from improve_yourself.optimizer_evidence import synthetic_system_matrix
from improve_yourself.rule_pack import RulePackValidationError, fixture_rule_pack_document, import_rule_pack, validate_rule_pack


def test_fixture_pack_imports_fail_closed_and_runs_synthetic_regression() -> None:
    document = fixture_rule_pack_document()
    report = validate_rule_pack(document)
    assert report["valid"] is True
    assert report["synthetic_regression"]["system_count"] == 150
    assert report["synthetic_regression"]["real_validation_result_created"] is False
    assert report["synthetic_regression"]["confidence_changed"] is False


@pytest.mark.parametrize("mutation", ["duplicate", "domain", "evidence", "conditions", "explanation"])
def test_invalid_rule_pack_is_not_imported(mutation: str) -> None:
    document = deepcopy(fixture_rule_pack_document())
    rule = document["rules"][0]
    if mutation == "duplicate":
        document["rules"].append(deepcopy(rule))
    elif mutation == "domain":
        rule["domain"] = "UNKNOWN_DOMAIN"
    elif mutation == "evidence":
        rule["evidence"] = []
    elif mutation == "conditions":
        condition = rule["compatibility"]["required"][0]
        rule["compatibility"]["excluded"] = [condition]
    else:
        rule["explanation"] = ""
    with pytest.raises(RulePackValidationError):
        import_rule_pack(document)


def test_imported_rule_pack_uses_existing_ui_without_rule_specific_code() -> None:
    rules = import_rule_pack(fixture_rule_pack_document())
    view = optimizer_product_view(synthetic_system_matrix()["systems"][36], internal_test=True, rules=rules)
    assert set(view["domains"]) == {"SYSTEM_OPTIMIZER", "GRAPHICS_OPTIMIZER", "NETWORK_OPTIMIZER", "BIOS_OPTIMIZER"}
    assert all(model["apply_available"] is False for model in view["models"])
    assert all(str(model["improve_recommendation"]).startswith("FIXTURE_ONLY") for model in view["models"])
