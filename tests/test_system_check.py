from improve_yourself.system_check import ACTION_REQUIRED, OK, REVIEW, evaluate_system_facts


def test_evaluates_complete_read_only_baseline() -> None:
    payload = evaluate_system_facts({
        "windows": {"caption": "Windows 11", "version": "10.0", "build": "26200"},
        "cpu": {"name": "CPU", "logical_processors": 16},
        "memory": {"total_gb": 32.0},
        "motherboard": {"manufacturer": "Vendor", "product": "Board", "bios_version": "F1"},
        "gpus": [{"name": "GPU", "driver_version": "1.2.3"}],
        "displays": [{"refresh_hz": 240}], "secure_boot": True, "secure_boot_source": "registry",
        "tpm": True, "tpm_version": "2.0", "tpm_source": "tpmtool",
    })
    assert payload["schema"] == "iy.system_check/v1"
    assert payload["policy"] == {"read_only": True, "changes_applied": False, "elevation_requested": False}
    assert payload["summary"] == {OK: 8, REVIEW: 0, ACTION_REQUIRED: 0}
    by_id = {item["id"]: item for item in payload["checks"]}
    assert by_id["gpu"]["user_view"]["status"] == "Hinweis"
    assert by_id["gpu"]["user_view"]["priority"] == "informativ"
    assert by_id["motherboard"]["user_view"]["priority"] == "optional"
    assert by_id["secure_boot"]["user_view"]["area"] == "Anti-Cheat-Readiness"
    assert payload["user_summary"]["anti_cheat_readiness"]["status"] == "bestätigt"


def test_discloses_missing_and_actionable_facts() -> None:
    payload = evaluate_system_facts({"memory": {"total_gb": 8}, "displays": [{"refresh_hz": 60}], "secure_boot": False})
    by_id = {item["id"]: item for item in payload["checks"]}
    assert by_id["memory"]["status"] == ACTION_REQUIRED
    assert by_id["display"]["status"] == ACTION_REQUIRED
    assert by_id["secure_boot"]["status"] == ACTION_REQUIRED
    assert by_id["tpm"]["status"] == REVIEW
    assert payload["summary"][REVIEW] > 0
    assert by_id["memory"]["user_view"]["status"] == "Verbesserung empfohlen"
    assert by_id["display"]["user_view"]["priority"] == "wichtig"
    assert by_id["secure_boot"]["user_view"]["status"] == "Problem"
    assert "Keine Änderung wurde vorgenommen." in by_id["secure_boot"]["user_view"]["action"]
    assert payload["user_summary"]["next_steps"][0]["priority"] == "kritisch"


def test_unknown_security_values_never_become_false() -> None:
    payload = evaluate_system_facts({"secure_boot": None, "tpm": None})
    by_id = {item["id"]: item for item in payload["checks"]}
    assert by_id["secure_boot"]["status"] == REVIEW
    assert by_id["tpm"]["status"] == REVIEW
    assert by_id["secure_boot"]["evidence"]["enabled"] is None
    assert by_id["tpm"]["evidence"]["enabled"] is None
    assert by_id["secure_boot"]["user_view"]["status"] == "Nicht prüfbar / unbekannt"
    assert "kein negativer Befund" in by_id["secure_boot"]["user_view"]["relevance"]
    readiness = payload["user_summary"]["anti_cheat_readiness"]
    assert readiness["status"] == "Nicht vollständig bestätigbar"
    assert "bedeutet nicht" in readiness["message"]


def test_unmet_anti_cheat_requirement_needs_attention() -> None:
    payload = evaluate_system_facts({"secure_boot": True, "tpm": False})
    by_id = {item["id"]: item for item in payload["checks"]}

    assert by_id["tpm"]["status"] == ACTION_REQUIRED
    assert by_id["tpm"]["user_view"]["status"] == "Problem"
    assert payload["user_summary"]["anti_cheat_readiness"]["status"] == "Aufmerksamkeit erforderlich"
