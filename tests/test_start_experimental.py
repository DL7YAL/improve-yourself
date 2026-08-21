from __future__ import annotations

import platform
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(platform.system() != "Windows", reason="Windows PowerShell launcher")


def _launcher() -> Path:
    return Path(__file__).parents[1] / "tools" / "dev" / "Start-Experimental.ps1"


def test_experimental_launcher_rejects_missing_workflow(tmp_path: Path) -> None:
    missing = tmp_path / "demo-workflow.json"
    completed = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_launcher()),
         "-SkipSetup", "-Workflow", str(missing)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode != 0
    assert "Workflow does not exist" in completed.stderr


def test_experimental_launcher_rejects_non_manifest_file() -> None:
    completed = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_launcher()),
         "-SkipSetup", "-Workflow", str(Path(__file__).parents[1] / "README.md")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert completed.returncode != 0
    assert "must be an explicitly selected demo-workflow.json" in completed.stderr
