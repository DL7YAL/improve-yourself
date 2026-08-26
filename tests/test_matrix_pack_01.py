from __future__ import annotations

from pathlib import Path

from improve_yourself.analyzer_shell import matrix_pack_01_rules, optimizer_product_view
from improve_yourself.optimizer_evidence import synthetic_system_matrix
from improve_yourself.rule_pack import import_rule_pack, load_rule_pack_document, validate_rule_pack


PACK_PATH = Path("config/rule-packs/improve-matrix-pack-01.json")
CHECK_IDS = (
    "windows", "cpu", "memory", "motherboard", "gpu", "gpu_driver",
    "chipset_driver", "graphics_settings_profile", "display", "monitor",
    "secure_boot", "tpm",
)
SETTING_IDS = (
    "latency", "upscaling", "frame_pacing", "sync", "sharpening",
    "quality_overrides", "game_tuning",
)


def test_matrix_pack_01_is_versioned_json_with_only_existing_system_check_contract() -> None:
    document = load_rule_pack_document(PACK_PATH)
    assert document["schema"] == "iy.improve_rule_pack/v1"
    assert document["pack_id"] == "improve-matrix-pack-01"
    assert document["pack_version"] == "1.0.0"
    assert document["pack_kind"] == "READ_ONLY_SYSTEM_CHECK_BASIS"
    contract = document["source_contract"]
    assert isinstance(contract, dict)
    assert tuple(contract["check_ids"]) == CHECK_IDS
    assert tuple(contract["setting_ids"]) == SETTING_IDS
    sources = contract["manufacturer_sources"]
    assert isinstance(sources, list) and len(sources) == 3
    assert all(item["release_fixed"] is False for item in sources)
    assert {rule["rule_id"] for rule in document["rules"]} == {f"system-check-{item.replace('_', '-')}" for item in CHECK_IDS}
    assert all(rule["apply_capable"] is False and rule["restore_capable"] is False for rule in document["rules"])


def test_matrix_pack_01_fail_closed_import_and_150_system_regression_are_deterministic() -> None:
    first = validate_rule_pack(load_rule_pack_document(PACK_PATH))
    second = validate_rule_pack(load_rule_pack_document(PACK_PATH))
    assert first == second
    regression = first["synthetic_regression"]
    assert regression["system_count"] == 150
    assert regression["real_validation_result_created"] is False
    assert regression["confidence_changed"] is False
    assert regression["state_counts"]["RECOMMENDED"] == 0
    assert regression["state_counts"]["ALREADY_RECOMMENDED"] == 0
    assert regression["state_counts"]["NO_CHANGE"] > 0
    assert regression["state_counts"]["CONDITIONAL"] > 0
    assert regression["state_counts"]["INSUFFICIENT_EVIDENCE"] > 0


def test_matrix_pack_01_is_the_normal_shell_import_source() -> None:
    assert tuple(rule.rule_id for rule in matrix_pack_01_rules()) == tuple(
        rule.rule_id for rule in import_rule_pack(load_rule_pack_document(PACK_PATH))
    )


def test_matrix_pack_01_preserves_unknown_conditional_exclusion_and_no_apply_ui_states() -> None:
    rules = import_rule_pack(load_rule_pack_document(PACK_PATH))
    profiles = synthetic_system_matrix()["systems"]
    known_view = optimizer_product_view(profiles[1], internal_test=True, rules=rules)
    unknown_view = optimizer_product_view(profiles[0], internal_test=True, rules=rules)
    assert known_view["read_only"] is True
    assert known_view["fixture_only"] is False
    assert len(known_view["models"]) == 12
    assert all(model["apply_available"] is False for model in known_view["models"])
    assert all(str(model["improve_recommendation"]).startswith("NO AUTOMATIC IMPROVE RECOMMENDATION") for model in known_view["models"])
    by_title = {model["title"]: model for model in known_view["models"]}
    assert by_title["Chipsatztreiber"]["current_state"] == "CONDITIONAL / NOT CONFIRMED"
    unknown = {model["title"]: model for model in unknown_view["models"]}
    assert unknown["Grafiktreiber-Aktualität"]["current_state"] == "UNKNOWN / NOT AVAILABLE"
    assert unknown["Grafiktreiber-Aktualität"]["explainability"]["missing_evidence"] == ["gpu.driver_version"]
    assert unknown["Secure Boot"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert unknown["TPM 2.0"]["current_state"] == "UNKNOWN / NOT AVAILABLE"
