from improve_yourself.system_check import ACTION_REQUIRED, OK, REVIEW, collect_official_gpu_driver_catalog, evaluate_system_facts


def test_evaluates_complete_read_only_baseline() -> None:
    payload = evaluate_system_facts({
        "windows": {"caption": "Windows 11", "version": "10.0", "build": "26200"},
        "cpu": {"name": "CPU", "logical_processors": 16},
        "memory": {"total_gb": 32.0},
        "motherboard": {"manufacturer": "Vendor", "product": "Board", "bios_version": "F1"},
        "gpus": [{"name": "GPU", "driver_version": "1.2.3"}],
        "amd_software": {"installed": True, "version": "26.7.1"},
        "amd_chipset": {"name": "AMD Chipset Software", "version": "8.07.16.1035"},
        "amd_adrenalin": {"installed": True, "version": "26.7.1"},
        "gpu_driver_catalog": {"version": "26.7.1", "source": "https://example.test/amd", "checked_at_utc": "2026-08-17T00:00:00+00:00"},
        "displays": [{"refresh_hz": 240}], "secure_boot": True, "secure_boot_source": "registry",
        "tpm": True, "tpm_version": "2.0", "tpm_source": "tpmtool",
    })
    assert payload["schema"] == "iy.system_check/v1"
    assert payload["policy"] == {"read_only": True, "changes_applied": False, "elevation_requested": False}
    assert payload["summary"] == {OK: 9, REVIEW: 2, ACTION_REQUIRED: 0}
    by_id = {item["id"]: item for item in payload["checks"]}
    assert by_id["gpu"]["user_view"]["status"] == "OK"
    assert by_id["gpu_driver"]["user_view"]["status"] == "OK"
    assert by_id["gpu_driver"]["evidence"]["official_version"] == "26.7.1"
    assert by_id["chipset_driver"]["user_view"]["status"] == "Nicht prüfbar / unbekannt"
    assert by_id["amd_adrenalin"]["evidence"]["read_api"] == "not_available"
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


def test_driver_update_and_missing_official_comparison_are_honest() -> None:
    update = evaluate_system_facts({
        "gpus": [{"name": "AMD Radeon RX 7900 XTX", "driver_version": "32.0"}],
        "amd_software": {"installed": True, "version": "26.6.1"},
        "gpu_driver_catalog": {"version": "26.7.1", "source": "https://example.test/amd", "checked_at_utc": "2026-08-17T00:00:00+00:00"},
    })
    unknown = evaluate_system_facts({"gpus": [{"name": "AMD Radeon RX 7900 XTX", "driver_version": "32.0"}], "amd_software": {"installed": True, "version": "26.6.1"}})
    by_id = {item["id"]: item for item in update["checks"]}
    unknown_by_id = {item["id"]: item for item in unknown["checks"]}
    assert by_id["gpu_driver"]["status"] == ACTION_REQUIRED
    assert by_id["gpu_driver"]["user_view"]["status"] == "Verbesserung empfohlen"
    assert unknown_by_id["gpu_driver"]["status"] == REVIEW
    assert unknown_by_id["gpu_driver"]["user_view"]["status"] == "Nicht prüfbar / unbekannt"


def test_official_amd_catalog_is_limited_to_mapped_adapter_and_safe_on_unavailable_source(monkeypatch) -> None:
    assert "reason" in collect_official_gpu_driver_catalog([{ "name": "Unmapped GPU" }])
    monkeypatch.setattr("improve_yourself.system_check.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")))
    result = collect_official_gpu_driver_catalog([{ "name": "AMD Radeon RX 7900 XTX" }])
    assert result["source"].startswith("https://www.amd.com/")
    assert "reason" in result
