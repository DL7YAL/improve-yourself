from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SystemKind(str, Enum):
    REAL = "REAL_HARDWARE"
    DUMMY = "DUMMY"


@dataclass(frozen=True)
class SystemEntry:
    system_id: int
    kind: SystemKind


def classify_system(system_id: int) -> SystemKind:
    if system_id < 1:
        raise ValueError("system_id must be >= 1")
    return SystemKind.REAL if system_id % 2 else SystemKind.DUMMY


def build_registry(start: int = 1, end: int = 120) -> list[SystemEntry]:
    if start < 1 or end < start:
        raise ValueError("invalid system id range")
    return [SystemEntry(i, classify_system(i)) for i in range(start, end + 1)]


def preflight_banner() -> str:
    return (
        "\n"
        "============================================================\n"
        "  SYSTEM REGISTRY PREFLIGHT\n"
        "  ODD ID  = REAL HARDWARE\n"
        "  EVEN ID = DUMMY / SYNTHETIC\n"
        "  DO NOT REASSIGN, GUESS OR MERGE CLASSIFICATIONS\n"
        "============================================================\n"
    )


def run_preflight(start: int = 1, end: int = 120) -> list[SystemEntry]:
    print(preflight_banner())
    registry = build_registry(start, end)
    real_count = sum(1 for item in registry if item.kind is SystemKind.REAL)
    dummy_count = len(registry) - real_count
    print(
        f"Validated IDs {start}-{end}: "
        f"{real_count} real / {dummy_count} dummy"
    )
    return registry


if __name__ == "__main__":
    run_preflight()
