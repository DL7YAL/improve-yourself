from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "iy.analysis/v1"


@dataclass(frozen=True)
class Kill:
    round_number: int
    tick: int
    attacker: str
    victim: str
    weapon: str = ""
    headshot: bool = False


@dataclass(frozen=True)
class Multikill:
    round_number: int
    player: str
    kill_count: int
    first_tick: int
    last_tick: int
    victims: list[str]


@dataclass
class DataQuality:
    status: str = "ok"
    missing_channels: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    source_name: str
    source_sha256: str
    map_name: str
    tickrate: float | None
    kills: list[Kill]
    multikills: list[Multikill]
    data_quality: DataQuality
    available_channels: list[str]
    schema: str = SCHEMA_VERSION
    disclaimer: str = (
        "Automatische Marker sind Prüfhinweise und kein Cheat-Nachweis."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
