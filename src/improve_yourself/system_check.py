from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

SYSTEM_CHECK_SCHEMA = "iy.system_check/v1"
OK = "OK"
REVIEW = "REVIEW"
ACTION_REQUIRED = "ACTION_REQUIRED"

RELIABLY_CHECKED = "reliably_automatically_checked"
RELIABLY_EVALUATED = "reliably_evaluated"
RECOGNIZED_ONLY = "recognized_only"
INVESTIGATED_UNKNOWN = "technically_investigated_not_reliably_readable"
NOT_IMPLEMENTED = "not_implemented"

_AMD_RX_7900_XTX_URL = "https://www.amd.com/en/support/downloads/drivers.html/graphics/radeon-rx/radeon-rx-7000-series/amd-radeon-rx-7900-xtx.html"
_GIGABYTE_X870_GAMING_X_WIFI7_URL = "https://www.gigabyte.com/us/Motherboard/X870-GAMING-X-WIFI7-rev-1x/sp"
_AMD_X870_CHIPSET_URL = "https://www.amd.com/en/support/downloads/drivers.html/chipsets/am5/x870.html"


def detect_chipset(board: dict[str, Any]) -> dict[str, str]:
    """Return only an exact board-to-chipset mapping backed by the board vendor."""
    if (board.get("manufacturer"), board.get("product")) == ("Gigabyte Technology Co., Ltd.", "X870 GAMING X WIFI7"):
        return {"name": "AMD X870", "source": _GIGABYTE_X870_GAMING_X_WIFI7_URL}
    return {}


def collect_official_gpu_driver_catalog(gpus: list[dict[str, Any]], timeout_seconds: int = 5) -> dict[str, Any]:
    """Read the official AMD product page for a known adapter; never download or install."""
    names = " ".join(str(gpu.get("name", "")) for gpu in gpus).lower()
    if "amd radeon rx 7900 xtx" not in names:
        return {"reason": "No supported official product-page mapping for the detected adapter."}
    checked_at = datetime.now(UTC).isoformat()
    try:
        request = Request(_AMD_RX_7900_XTX_URL, headers={"User-Agent": "Improve-Yourself-System-Check/1.0"})
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed official HTTPS source
            document = response.read().decode("utf-8", errors="replace")
        match = re.search(r"Adrenalin\s+([0-9]+(?:\.[0-9]+)+)\s*\((?:WHQL Recommended|Optional)\)", document, re.I)
        if not match:
            return {"source": _AMD_RX_7900_XTX_URL, "checked_at_utc": checked_at, "reason": "Official page format did not expose a comparable version."}
        return {"version": match.group(1), "source": _AMD_RX_7900_XTX_URL, "checked_at_utc": checked_at}
    except (OSError, URLError, TimeoutError) as error:
        return {"source": _AMD_RX_7900_XTX_URL, "checked_at_utc": checked_at, "reason": f"Official comparison source unavailable: {type(error).__name__}"}


def collect_official_chipset_catalog(chipset: dict[str, Any], timeout_seconds: int = 5) -> dict[str, Any]:
    """Read the fixed official AMD page only for an exactly identified chipset."""
    if chipset.get("name") != "AMD X870":
        return {"reason": "No supported official product-page mapping for the identified chipset."}
    checked_at = datetime.now(UTC).isoformat()
    try:
        request = Request(_AMD_X870_CHIPSET_URL, headers={"User-Agent": "Improve-Yourself-System-Check/1.0"})
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed official HTTPS source
            document = response.read().decode("utf-8", errors="replace")
        match = re.search(r"AMD\s+Chipset\s+(?:Drivers|Software).*?(?:Revision Number\s*)?([0-9]+(?:\.[0-9]+){2,})", document, re.I | re.S)
        if not match:
            return {"source": _AMD_X870_CHIPSET_URL, "checked_at_utc": checked_at, "reason": "Official page format did not expose a comparable chipset version."}
        return {"version": match.group(1), "source": _AMD_X870_CHIPSET_URL, "checked_at_utc": checked_at}
    except (OSError, URLError, TimeoutError) as error:
        return {"source": _AMD_X870_CHIPSET_URL, "checked_at_utc": checked_at, "reason": f"Official comparison source unavailable: {type(error).__name__}"}


def _presentation(check_id: str, status: str, *, detail: str | None = None) -> dict[str, str]:
    if check_id == "gpu_driver" and status == OK:
        return {
            "status": "OK", "priority": "informativ",
            "relevance": "Der installierte Treiber wurde gegen den offiziellen Herstellerstand geprüft.",
            "action": "Keine Aktion erforderlich.",
        }
    if check_id == "gpu_driver" and status == ACTION_REQUIRED:
        return {
            "status": "Verbesserung empfohlen", "priority": "wichtig",
            "relevance": "Ein neuerer offizieller Grafiktreiber steht für den erkannten Adapter bereit.",
            "action": "Den offiziellen Hersteller-Download prüfen und die Aktualisierung nur bewusst manuell durchführen. Keine Änderung wurde vorgenommen.",
        }
    if check_id == "chipset_driver" and status == OK:
        return {
            "status": "OK", "priority": "informativ",
            "relevance": "Der installierte Chipsatztreiber wurde gegen den offiziellen Stand des eindeutig erkannten Chipsatzes geprüft.",
            "action": "Keine Aktion erforderlich.",
        }
    if check_id == "chipset_driver" and status == ACTION_REQUIRED:
        return {
            "status": "Verbesserung empfohlen", "priority": "wichtig",
            "relevance": "Für den eindeutig erkannten Chipsatz steht ein neueres offizielles Paket bereit.",
            "action": "Das offizielle AMD-Chipsatzpaket manuell prüfen und eine Aktualisierung nur bewusst durchführen. Keine Änderung wurde vorgenommen.",
        }
    if status == REVIEW:
        security_actions = {
            "secure_boot": "In Windows-Sicherheit > Gerätesicherheit oder in Systeminformationen den sicheren Startzustand prüfen. Unbekannt bedeutet nicht deaktiviert; keine Änderung wurde vorgenommen.",
            "tpm": "In Windows-Sicherheit > Gerätesicherheit > Sicherheitsprozessor-Details den TPM-Status prüfen. Unbekannt bedeutet nicht deaktiviert; keine Änderung wurde vorgenommen.",
        }
        return {
            "status": "Nicht prüfbar / unbekannt", "priority": "wichtig" if check_id in {"secure_boot", "tpm"} else "informativ",
            "relevance": "Für die Anti-Cheat-Readiness relevant; Improve konnte diesen Pflichtpunkt nicht bestätigen. Daraus wird kein negativer Befund abgeleitet." if check_id in security_actions else "Die Information fehlt; daraus wird kein negativer Befund abgeleitet.",
            "action": security_actions.get(check_id, detail or "Keine Aktion nötig, solange die Information nicht für eine Entscheidung benötigt wird."),
        }
    if status == ACTION_REQUIRED:
        if check_id in {"secure_boot", "tpm"}:
            return {
                "status": "Problem", "priority": "kritisch",
                "relevance": "Kann die Anti-Cheat-Bereitschaft beeinflussen.",
                "action": "Vor dem Spielen manuell prüfen und bei Bedarf nach Hersteller-/Windows-Anleitung aktivieren. Keine Änderung wurde vorgenommen.",
            }
        actions = {
            "memory": "Für CS2 mehr Arbeitsspeicher einplanen oder andere speicherintensive Programme schließen. Keine Änderung wurde vorgenommen.",
            "display": "In Windows und im Monitor-Menü prüfen, ob die höchste unterstützte Bildwiederholrate aktiv ist. Keine Änderung wurde vorgenommen.",
        }
        return {
            "status": "Verbesserung empfohlen", "priority": "wichtig",
            "relevance": "Kann die praktische Nutzung oder Spielbereitschaft beeinträchtigen.",
            "action": actions.get(check_id, "Manuell prüfen; keine automatische Änderung wurde vorgenommen."),
        }
    return {
        "status": "OK", "priority": "optional" if check_id == "motherboard" else "informativ",
        "relevance": "Kein Handlungsbedarf aus dieser Prüfung.",
        "action": "Keine Aktion erforderlich.",
    }


def _result(
    check_id: str, label: str, status: str, summary: str, evidence: dict[str, Any], *,
    detail: str | None = None, classification: str = RELIABLY_CHECKED,
) -> dict[str, Any]:
    return {
        "id": check_id, "label": label, "status": status, "summary": summary, "evidence": evidence,
        "classification": classification, "user_view": _presentation(check_id, status, detail=detail),
    }


def _graphics_profile_matrix(provider: str | None, *, cs2_observed: bool) -> list[dict[str, Any]]:
    """Return a vendor-neutral matrix without guessing undocumented settings."""
    settings = (
        ("latency", "Latenzfunktion (z. B. Anti-Lag)"),
        ("upscaling", "Treiber-Upscaling (z. B. RSR)"),
        ("frame_pacing", "FPS-Limit / Frame-Pacing (z. B. Chill)"),
        ("sync", "Synchronisation (z. B. Enhanced Sync / VSync)"),
        ("sharpening", "Bildschärfung"),
        ("quality_overrides", "Erweiterte Qualitäts-Overrides"),
        ("game_tuning", "Spielbezogenes GPU-Tuning"),
    )
    return [{
        "id": setting_id,
        "label": label,
        "provider": provider,
        "global_value": "unknown",
        "cs2_override": "unknown",
        "effective_value": "unknown",
        "reliably_readable": False,
        "classification": INVESTIGATED_UNKNOWN,
        "source": "No documented, locally available read-only value source in this V1 build.",
        "cs2_application_observed": cs2_observed,
    } for setting_id, label in settings]


def evaluate_system_facts(facts: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    windows = facts.get("windows") or {}
    build = windows.get("build")
    checks.append(_result(
        "windows", "Windows", OK if build else REVIEW,
        f"Windows build {build} erkannt." if build else "Windows-Version konnte nicht vollständig erkannt werden.",
        {"caption": windows.get("caption"), "version": windows.get("version"), "build": build},
    ))

    cpu = facts.get("cpu") or {}
    checks.append(_result(
        "cpu", "CPU", OK if cpu.get("name") else REVIEW,
        cpu.get("name") or "CPU konnte nicht erkannt werden.",
        {"name": cpu.get("name"), "logical_processors": cpu.get("logical_processors")},
    ))

    memory = facts.get("memory") or {}
    ram_gb = memory.get("total_gb")
    ram_status = OK if isinstance(ram_gb, (int, float)) and ram_gb >= 16 else (ACTION_REQUIRED if ram_gb else REVIEW)
    ram_summary = f"{ram_gb:.1f} GB RAM erkannt." if ram_gb else "Arbeitsspeicher konnte nicht erkannt werden."
    if ram_gb and ram_gb < 16:
        ram_summary += " Weniger als die V1-CS2-Basis von 16 GB."
    checks.append(_result("memory", "Arbeitsspeicher", ram_status, ram_summary, {"total_gb": ram_gb}))

    board = facts.get("motherboard") or {}
    checks.append(_result(
        "motherboard", "Mainboard und BIOS", OK if board.get("product") else REVIEW,
        "Mainboard und BIOS erkannt." if board.get("product") else "Mainboard konnte nicht vollständig erkannt werden.",
        {key: board.get(key) for key in ("manufacturer", "product", "bios_version", "bios_date")},
    ))

    gpus = facts.get("gpus") or []
    gpu_complete = bool(gpus) and all(g.get("name") and g.get("driver_version") for g in gpus)
    checks.append(_result(
        "gpu", "Grafikadapter", OK if gpu_complete else REVIEW,
        f"{len(gpus)} Grafikadapter erkannt." if gpu_complete else "Grafikadapter oder Treiberstand unvollständig.",
        {"adapters": [{key: g.get(key) for key in ("name", "driver_version", "driver_date")} for g in gpus]},
    ))

    gpu_catalog = facts.get("gpu_driver_catalog") or {}
    installed_package = facts.get("amd_software") or {}
    current_version = gpu_catalog.get("version")
    installed_version = installed_package.get("version")
    if installed_version and current_version:
        driver_status = OK if installed_version == current_version else ACTION_REQUIRED
        driver_summary = (
            f"AMD Software Adrenalin {installed_version} entspricht dem offiziellen Stand {current_version}."
            if driver_status == OK else
            f"AMD Software Adrenalin {installed_version} erkannt; offizieller Stand ist {current_version}."
        )
    else:
        driver_status = REVIEW
        driver_summary = "Installierter oder offizieller Grafiktreiberstand konnte nicht zuverlässig verglichen werden."
    checks.append(_result(
        "gpu_driver", "Grafiktreiber-Aktualität", driver_status, driver_summary,
        {"installed_package_version": installed_version, "installed_driver_versions": [g.get("driver_version") for g in gpus],
         "official_version": current_version, "official_source": gpu_catalog.get("source"),
         "checked_at_utc": gpu_catalog.get("checked_at_utc")},
        detail="Der aktuelle Herstellerstand war bei dieser Prüfung nicht zuverlässig verfügbar. Den Stand auf der offiziellen Hersteller-Supportseite manuell vergleichen; keine Änderung wurde vorgenommen.",
        classification=RELIABLY_EVALUATED if installed_version and current_version else INVESTIGATED_UNKNOWN,
    ))

    chipset = facts.get("amd_chipset") or {}
    chipset_identity = facts.get("chipset") or {}
    chipset_catalog = facts.get("chipset_driver_catalog") or {}
    chipset_version = chipset.get("version")
    official_chipset_version = chipset_catalog.get("version")
    if chipset_identity.get("name") and chipset_version and official_chipset_version:
        chipset_status = OK if chipset_version == official_chipset_version else ACTION_REQUIRED
        chipset_summary = (
            f"{chipset_identity['name']}: installierte AMD-Chipsatzsoftware {chipset_version} entspricht dem offiziellen Stand {official_chipset_version}."
            if chipset_status == OK else
            f"{chipset_identity['name']}: AMD-Chipsatzsoftware {chipset_version} erkannt; offizieller Stand ist {official_chipset_version}."
        )
    else:
        chipset_status = REVIEW
        chipset_summary = "Chipsatz oder offizieller Chipsatztreiberstand konnte nicht zuverlässig verglichen werden."
    checks.append(_result(
        "chipset_driver", "Chipsatztreiber", chipset_status, chipset_summary,
        {"chipset": chipset_identity.get("name"), "chipset_source": chipset_identity.get("source"), "package": chipset.get("name"),
         "installed_version": chipset_version, "official_version": official_chipset_version,
         "official_source": chipset_catalog.get("source"), "checked_at_utc": chipset_catalog.get("checked_at_utc")},
        detail="Der Chipsatz oder sein offizieller Herstellerstand war bei dieser Prüfung nicht zuverlässig bestimmbar. Ohne eindeutige Zuordnung wird keine Aktualität geraten; keine Änderung wurde vorgenommen.",
        classification=RELIABLY_EVALUATED if chipset_identity.get("name") and chipset_version and official_chipset_version else INVESTIGATED_UNKNOWN,
    ))

    adrenalin = facts.get("amd_adrenalin") or {}
    graphics_profiles = facts.get("graphics_profiles") or {}
    provider = graphics_profiles.get("provider") or ("AMD" if adrenalin.get("installed") else None)
    cs2_observed = graphics_profiles.get("cs2_application_observed") is True
    source_classes = graphics_profiles.get("sources_examined") or [
        "active AMD display-driver UMD configuration", "AMD CN GameReport/cs2.exe",
        "AMD CN steamdata/730", "AMD ADLX runtime availability",
    ]
    checks.append(_result(
        "graphics_settings_profile", "Grafikeinstellungen und Spielprofil", REVIEW,
        "AMD Software ist erkannt; CS2 wurde von AMD lokal beobachtet. Die tatsächlich wirksamen globalen und CS2-Profilschalter sind ohne dokumentierten read-only Wertpfad nicht belastbar auslesbar." if adrenalin.get("installed") and cs2_observed else
        ("AMD Software ist erkannt; ein CS2-spezifischer Profilwert konnte nicht belastbar festgestellt werden." if adrenalin.get("installed") else "Kein unterstützter Hersteller-Profilerfassungsweg wurde erkannt."),
        {"provider": provider, "software_detected": bool(adrenalin.get("installed")), "software_version": adrenalin.get("version"),
         "cs2_application_observed": cs2_observed, "cs2_profile_status": "not_reliably_determinable",
         "global_settings_status": INVESTIGATED_UNKNOWN, "effective_settings_status": INVESTIGATED_UNKNOWN,
         "sources_examined": source_classes,
         "manual_snapshot": {"available": provider == "AMD", "requires_user_export": provider == "AMD", "documented_format": "AMD Software Snap Settings ZIP", "automatically_readable_in_v1": False},
         "setting_matrix": _graphics_profile_matrix(provider, cs2_observed=cs2_observed)},
        detail="AMD Software > Gaming > das CS2-Spielprofil manuell prüfen. Für eine spätere, ausdrücklich bereitgestellte AMD-Snap-Settings-Datei ist ein dokumentierter Importleser separat zu spezifizieren; Improve importiert sie nicht in AMD Software und interpretiert keine undokumentierten Registry-/Binärwerte.",
        classification=INVESTIGATED_UNKNOWN,
    ))

    displays = facts.get("displays") or []
    rates = [d.get("refresh_hz") for d in displays if isinstance(d.get("refresh_hz"), (int, float))]
    display_status = OK if rates and max(rates) >= 120 else (ACTION_REQUIRED if rates else REVIEW)
    display_summary = f"Maximal {max(rates):g} Hz erkannt." if rates else "Bildwiederholrate konnte nicht erkannt werden."
    if rates and max(rates) < 120:
        display_summary += " Für den CS2-Fokus sollte die aktive Anzeigeeinstellung geprüft werden."
    checks.append(_result("display", "Anzeige", display_status, display_summary, {"active_displays": [{key: d.get(key) for key in ("name", "width", "height", "refresh_hz")} for d in displays]}))

    monitors = facts.get("monitors") or []
    checks.append(_result(
        "monitor", "Monitorerkennung", OK if monitors else REVIEW,
        f"{len(monitors)} Monitor(e) erkannt." if monitors else "Monitorbezeichnung konnte nicht zuverlässig automatisch erkannt werden.",
        {"monitors": [{"name": monitor.get("name")} for monitor in monitors]},
        detail="In Windows Einstellungen > System > Anzeige den verwendeten Monitor prüfen. Ein unbekannter Name bedeutet nicht, dass kein Monitor verbunden ist.",
        classification=RELIABLY_CHECKED if monitors else INVESTIGATED_UNKNOWN,
    ))

    for check_id, label in (("secure_boot", "Secure Boot"), ("tpm", "TPM 2.0")):
        value = facts.get(check_id)
        status = OK if value is True else (ACTION_REQUIRED if value is False else REVIEW)
        if value is True:
            summary = "Secure Boot ist aktiviert." if check_id == "secure_boot" else "TPM 2.0 ist vorhanden und bereit."
        elif value is False:
            summary = f"{label} ist nicht erfüllt; manuell für die Anti-Cheat-Readiness prüfen."
        else:
            summary = f"{label} konnte nicht automatisch bestätigt werden. Das bedeutet nicht, dass es deaktiviert ist."
        evidence = {"enabled": value, "source": facts.get(f"{check_id}_source")}
        if check_id == "tpm":
            evidence["version"] = facts.get("tpm_version")
        check = _result(check_id, label, status, summary, evidence)
        check["user_view"]["area"] = "Anti-Cheat-Readiness"
        checks.append(check)

    counts = {status: sum(c["status"] == status for c in checks) for status in (OK, REVIEW, ACTION_REQUIRED)}
    user_checks = [check["user_view"] for check in checks]
    priority_order = {"kritisch": 0, "wichtig": 1, "optional": 2, "informativ": 3}
    next_steps = [
        {"label": check["label"], "priority": check["user_view"]["priority"], "action": check["user_view"]["action"]}
        for check in sorted(checks, key=lambda value: priority_order[value["user_view"]["priority"]])
        if check["user_view"]["status"] not in {"OK", "Nicht prüfbar / unbekannt"}
    ]
    anti_cheat = {check["id"]: check for check in checks if check["id"] in {"secure_boot", "tpm"}}
    security_values = [anti_cheat[key]["evidence"]["enabled"] for key in ("secure_boot", "tpm")]
    criteria = [{"label": anti_cheat[key]["label"], "status": anti_cheat[key]["user_view"]["status"]} for key in ("secure_boot", "tpm")]
    if all(value is True for value in security_values):
        readiness = {"status": "bestätigt", "message": "Secure Boot und TPM 2.0 wurden für die Anti-Cheat-Readiness bestätigt.", "criteria": criteria}
    elif any(value is False for value in security_values):
        readiness = {"status": "Aufmerksamkeit erforderlich", "message": "Mindestens eine Anti-Cheat-Pflichtprüfung ist nicht erfüllt. Keine automatische Änderung wurde vorgenommen.", "criteria": criteria}
    else:
        readiness = {"status": "Nicht vollständig bestätigbar", "message": "Mindestens eine Anti-Cheat-Pflichtprüfung konnte nicht automatisch bestätigt werden. Das bedeutet nicht, dass sie deaktiviert ist.", "criteria": criteria}
    return {
        "schema": SYSTEM_CHECK_SCHEMA,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "platform": "windows",
        "policy": {"read_only": True, "changes_applied": False, "elevation_requested": False},
        "summary": counts,
        "user_summary": {
            "counts": {status: sum(item["status"] == status for item in user_checks) for status in (
                "OK", "Hinweis", "Verbesserung empfohlen", "Problem", "Nicht prüfbar / unbekannt"
            )},
            "next_steps": next_steps,
            "anti_cheat_readiness": readiness,
        },
        "checks": checks,
    }


_POWERSHELL = r'''
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$board = Get-CimInstance Win32_BaseBoard | Select-Object -First 1
$bios = Get-CimInstance Win32_BIOS | Select-Object -First 1
$computer = Get-CimInstance Win32_ComputerSystem
$gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object { @{name=$_.Name;driver_version=$_.DriverVersion;driver_date=[string]$_.DriverDate} })
$displays = @(Get-CimInstance Win32_VideoController | Where-Object { $_.CurrentHorizontalResolution -and $_.CurrentVerticalResolution -and $_.CurrentRefreshRate } | ForEach-Object { @{name=$_.Name;width=$_.CurrentHorizontalResolution;height=$_.CurrentVerticalResolution;refresh_hz=$_.CurrentRefreshRate} })
$monitors = @(); try { $monitors = @(Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorID -ErrorAction Stop | ForEach-Object { $name = -join ($_.UserFriendlyName | Where-Object { $_ -ne 0 } | ForEach-Object { [char]$_ }); if ($name) { @{name=$name} } }) } catch {}
$installed = @(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue)
$amdSoftware = $installed | Where-Object { $_.DisplayName -eq 'AMD Software' } | Select-Object -First 1
$amdChipset = $installed | Where-Object { $_.DisplayName -eq 'AMD Chipset Software' } | Select-Object -First 1
$secureBoot = $null;$secureBootSource = $null; try { $secureBoot = [bool](Confirm-SecureBootUEFI);$secureBootSource='Confirm-SecureBootUEFI' } catch {}
if ($null -eq $secureBoot) { try { $state=(Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State' -Name UEFISecureBootEnabled -ErrorAction Stop).UEFISecureBootEnabled;if ($state -in 0,1) { $secureBoot=[bool]$state;$secureBootSource='SecureBootStateRegistry' } } catch {} }
$tpm = $null;$tpmVersion=$null;$tpmSource=$null; try {
  $t = Get-Tpm
  if ($null -ne $t -and $null -ne $t.TpmPresent -and $null -ne $t.TpmReady) {
    $tpm = [bool]($t.TpmPresent -and $t.TpmReady);$tpmVersion=$t.SpecVersion;$tpmSource='Get-Tpm'
  }
} catch {}
if ($null -eq $tpm) { try { $tpmTool=& "$env:SystemRoot\System32\tpmtool.exe" getdeviceinformation 2>&1;$text=($tpmTool | Out-String);$present=$text -match '(?im)^\s*-\s*(?:TPM present|TPM vorhanden)\s*:\s*(?:True|Wahr)\s*$';$ready=$text -match '(?im)^\s*-\s*(?:Is ready for storage|Zum Speichern bereit)\s*:\s*(?:True|Wahr)\s*$';$version=[regex]::Match($text,'(?im)^\s*-\s*(?:TPM version|TPM-Version)\s*:\s*([0-9]+(?:\.[0-9]+)?)').Groups[1].Value;if ($present -and $ready -and $version -like '2.*') { $tpm=$true;$tpmVersion=$version;$tpmSource='tpmtool getdeviceinformation' } elseif ($text -match '(?im)^\s*-\s*(?:TPM present|TPM vorhanden)\s*:\s*(?:False|Falsch)\s*$') { $tpm=$false;$tpmSource='tpmtool getdeviceinformation' } } catch {} }
@{
 windows=@{caption=$os.Caption;version=$os.Version;build=$os.BuildNumber}
 cpu=@{name=$cpu.Name;logical_processors=$computer.NumberOfLogicalProcessors}
 memory=@{total_gb=[math]::Round($computer.TotalPhysicalMemory/1GB,1)}
 motherboard=@{manufacturer=$board.Manufacturer;product=$board.Product;bios_version=$bios.SMBIOSBIOSVersion;bios_date=[string]$bios.ReleaseDate}
 gpus=$gpus;displays=$displays;monitors=$monitors;amd_software=@{installed=($null -ne $amdSoftware);name=$amdSoftware.DisplayName;version=$amdSoftware.DisplayVersion};amd_chipset=@{name=$amdChipset.DisplayName;version=$amdChipset.DisplayVersion};amd_adrenalin=@{installed=($null -ne $amdSoftware);version=$amdSoftware.DisplayVersion};secure_boot=$secureBoot;secure_boot_source=$secureBootSource;tpm=$tpm;tpm_version=$tpmVersion;tpm_source=$tpmSource
} | ConvertTo-Json -Depth 6 -Compress
'''


def collect_windows_facts(timeout_seconds: int = 20) -> dict[str, Any]:
    if platform.system() != "Windows":
        raise RuntimeError("System Check V1 currently supports Windows only")
    completed = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", _POWERSHELL],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_seconds, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or "Windows inventory failed"
        raise RuntimeError(message)
    facts = json.loads(completed.stdout)
    amd_cn = Path.home() / "AppData" / "Local" / "AMD" / "CN"
    game_report = amd_cn / "GameReport" / "cs2.exe" / "gpa.bin"
    steam_metadata = amd_cn / "steamdata" / "730.json"
    adlx_runtime = any((Path.home() / "AppData" / "Local" / "AMD").glob("**/ADLX*.dll"))
    facts["graphics_profiles"] = {
        "provider": "AMD" if (facts.get("amd_adrenalin") or {}).get("installed") else None,
        "cs2_application_observed": game_report.is_file() or steam_metadata.is_file(),
        "sources_examined": [
            "AMD display-driver UMD configuration (undocumented values not decoded)",
            "AMD CN GameReport/cs2.exe (application observation only)",
            "AMD CN steamdata/730 (store metadata only)",
            "AMD ADLX runtime availability" if adlx_runtime else "AMD ADLX runtime not locally exposed to this build",
            "AMD Software Snap Settings (manual export; no supplied snapshot parser contract)",
        ],
    }
    facts["chipset"] = detect_chipset(facts.get("motherboard") or {})
    facts["gpu_driver_catalog"] = collect_official_gpu_driver_catalog(facts.get("gpus") or [])
    facts["chipset_driver_catalog"] = collect_official_chipset_catalog(facts["chipset"])
    return facts


def run_system_check(output: Path) -> Path:
    payload = evaluate_system_facts(collect_windows_facts())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Improve Yourself Windows system check")
    parser.add_argument("--output", type=Path, default=Path("results/system-check.json"))
    args = parser.parse_args()
    try:
        result = run_system_check(args.output)
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
