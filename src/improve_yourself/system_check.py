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


def _result(check_id: str, label: str, status: str, summary: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"id": check_id, "label": label, "status": status, "summary": summary, "evidence": evidence}


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
    return {
        "schema": SYSTEM_CHECK_SCHEMA,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "platform": "windows",
        "policy": {"read_only": True, "changes_applied": False, "elevation_requested": False},
        "summary": counts,
        "checks": checks,
    }


_POWERSHELL = r'''
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$board = Get-CimInstance Win32_BaseBoard | Select-Object -First 1
$bios = Get-CimInstance Win32_BIOS | Select-Object -First 1
$computer = Get-CimInstance Win32_ComputerSystem
$gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object { @{name=$_.Name;vendor=$_.AdapterCompatibility;driver_version=$_.DriverVersion} })
$displays = @(Get-CimInstance Win32_VideoController | ForEach-Object { @{refresh_hz=$_.CurrentRefreshRate;width=$_.CurrentHorizontalResolution;height=$_.CurrentVerticalResolution} })
$network = @(Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.PhysicalAdapter -eq $true } | ForEach-Object {
  $ip = $null; try { $ip = Get-NetIPInterface -InterfaceIndex $_.InterfaceIndex -AddressFamily IPv4 -ErrorAction Stop | Select-Object -First 1 } catch {}
  $rss = $null; try { $rss = Get-NetAdapterRss -Name $_.Name -ErrorAction Stop } catch {}
  @{
    name=$_.Name;manufacturer=$_.Manufacturer;driver_version=$_.DriverVersion;interface_index=$_.InterfaceIndex;
    link_speed_mbps=$(if ($_.Speed) {[math]::Round($_.Speed/1MB,0)} else {$null});mac_address=$_.MACAddress;
    mtu=$(if ($ip) {$ip.NlMtu} else {$null});connection_state=$(if ($ip) {[string]$ip.ConnectionState} else {$null});
    rss=$(if ($rss) {[bool]$rss.Enabled} else {$null});eee='NOT_RELIABLY_DETECTABLE';interrupt_moderation='NOT_RELIABLY_DETECTABLE';offloads='NOT_RELIABLY_DETECTABLE';power_management='NOT_RELIABLY_DETECTABLE';duplex_link_mode='NOT_RELIABLY_DETECTABLE'
  }
})
$secureBoot = $null; try { $secureBoot = [bool](Confirm-SecureBootUEFI) } catch {}
$tpm = $null; try {
  $t = Get-Tpm
  if ($null -ne $t -and $null -ne $t.TpmPresent -and $null -ne $t.TpmReady) {
    $tpm = [bool]($t.TpmPresent -and $t.TpmReady)
  }
} catch {}
@{
 windows=@{caption=$os.Caption;version=$os.Version;build=$os.BuildNumber}
 cpu=@{name=$cpu.Name;manufacturer=$cpu.Manufacturer;architecture=$cpu.Architecture;family=$cpu.Family;logical_processors=$computer.NumberOfLogicalProcessors}
 memory=@{total_gb=[math]::Round($computer.TotalPhysicalMemory/1GB,1);speed_mt_s=$null}
 motherboard=@{manufacturer=$board.Manufacturer;product=$board.Product;version=$board.Version;bios_version=$bios.SMBIOSBIOSVersion;bios_date=[string]$bios.ReleaseDate}
 bios=@{version=$bios.SMBIOSBIOSVersion;date=[string]$bios.ReleaseDate;manufacturer=$bios.Manufacturer}
 gpus=$gpus;displays=$displays;network_adapters=$network;secure_boot=$secureBoot;tpm=$tpm
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
