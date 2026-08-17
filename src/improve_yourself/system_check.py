from __future__ import annotations

import argparse
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SYSTEM_CHECK_SCHEMA = "iy.system_check/v1"
OK = "OK"
REVIEW = "REVIEW"
ACTION_REQUIRED = "ACTION_REQUIRED"


def _presentation(check_id: str, status: str) -> dict[str, str]:
    if status == OK and check_id == "gpu":
        return {
            "status": "Hinweis", "priority": "informativ",
            "relevance": "Der installierte Treiber wurde erkannt; seine Aktualität wird nicht automatisch bewertet.",
            "action": "Nur bei konkreten Grafikproblemen den Herstellerstand manuell vergleichen. Keine automatische Änderung wurde vorgenommen.",
        }
    if status == REVIEW:
        action = {
            "secure_boot": "Bei Bedarf in Windows-Sicherheit oder UEFI manuell prüfen. Keine Änderung wurde vorgenommen.",
            "tpm": "Bei Bedarf in Windows-Sicherheit oder UEFI manuell prüfen. Keine Änderung wurde vorgenommen.",
        }.get(check_id, "Keine Aktion nötig, solange die Information nicht für eine Entscheidung benötigt wird.")
        return {
            "status": "Nicht prüfbar / unbekannt", "priority": "wichtig" if check_id in {"secure_boot", "tpm"} else "informativ",
            "relevance": "Die Information fehlt; daraus wird kein negativer Befund abgeleitet.", "action": action,
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


def _result(check_id: str, label: str, status: str, summary: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": check_id, "label": label, "status": status, "summary": summary, "evidence": evidence,
        "user_view": _presentation(check_id, status),
    }


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
        "gpu", "Grafik und Treiber", OK if gpu_complete else REVIEW,
        f"{len(gpus)} Grafikadapter mit Treiberstand erkannt." if gpu_complete else "Grafikadapter oder Treiberstand unvollständig.",
        {"adapters": [{"name": g.get("name"), "driver_version": g.get("driver_version")} for g in gpus]},
    ))

    displays = facts.get("displays") or []
    rates = [d.get("refresh_hz") for d in displays if isinstance(d.get("refresh_hz"), (int, float))]
    display_status = OK if rates and max(rates) >= 120 else (ACTION_REQUIRED if rates else REVIEW)
    display_summary = f"Maximal {max(rates):g} Hz erkannt." if rates else "Bildwiederholrate konnte nicht erkannt werden."
    if rates and max(rates) < 120:
        display_summary += " Für den CS2-Fokus sollte die aktive Anzeigeeinstellung geprüft werden."
    checks.append(_result("display", "Anzeige", display_status, display_summary, {"refresh_rates_hz": rates}))

    for check_id, label in (("secure_boot", "Secure Boot"), ("tpm", "TPM")):
        value = facts.get(check_id)
        status = OK if value is True else (ACTION_REQUIRED if value is False else REVIEW)
        summary = f"{label} ist aktiv." if value is True else (
            f"{label} ist nicht aktiv; manuell für Anti-Cheat-Bereitschaft prüfen." if value is False
            else f"{label}-Status konnte ohne weitergehende Berechtigung nicht sicher ermittelt werden."
        )
        checks.append(_result(check_id, label, status, summary, {"enabled": value}))

    counts = {status: sum(c["status"] == status for c in checks) for status in (OK, REVIEW, ACTION_REQUIRED)}
    user_checks = [check["user_view"] for check in checks]
    priority_order = {"kritisch": 0, "wichtig": 1, "optional": 2, "informativ": 3}
    next_steps = [
        {"label": check["label"], "priority": check["user_view"]["priority"], "action": check["user_view"]["action"]}
        for check in sorted(checks, key=lambda value: priority_order[value["user_view"]["priority"]])
        if check["user_view"]["status"] not in {"OK", "Nicht prüfbar / unbekannt"}
    ]
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
$gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object { @{name=$_.Name;driver_version=$_.DriverVersion} })
$displays = @(Get-CimInstance Win32_VideoController | ForEach-Object { @{refresh_hz=$_.CurrentRefreshRate} })
$secureBoot = $null; try { $secureBoot = [bool](Confirm-SecureBootUEFI) } catch {}
$tpm = $null; try {
  $t = Get-Tpm
  if ($null -ne $t -and $null -ne $t.TpmPresent -and $null -ne $t.TpmReady) {
    $tpm = [bool]($t.TpmPresent -and $t.TpmReady)
  }
} catch {}
@{
 windows=@{caption=$os.Caption;version=$os.Version;build=$os.BuildNumber}
 cpu=@{name=$cpu.Name;logical_processors=$computer.NumberOfLogicalProcessors}
 memory=@{total_gb=[math]::Round($computer.TotalPhysicalMemory/1GB,1)}
 motherboard=@{manufacturer=$board.Manufacturer;product=$board.Product;bios_version=$bios.SMBIOSBIOSVersion;bios_date=[string]$bios.ReleaseDate}
 gpus=$gpus;displays=$displays;secure_boot=$secureBoot;tpm=$tpm
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
    return json.loads(completed.stdout)


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
