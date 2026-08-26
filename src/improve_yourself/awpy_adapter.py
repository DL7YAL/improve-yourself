from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from awpy import Demo

from .model import DataQuality, Kill

OPTIONAL_CHANNELS = ("damages", "shots", "bomb", "smokes", "infernos", "grenades", "footsteps")
REPLAY_PLAYER_PROPS = (
    "health",
    "armor_value",
    "pitch",
    "yaw",
    "active_weapon_name",
    "velocity_X",
    "velocity_Y",
    "velocity_Z",
)


def _records(frame: Any) -> list[dict[str, Any]]:
    if frame is None:
        return []
    if isinstance(frame, list):
        return frame
    converter = getattr(frame, "to_dicts", None)
    return converter() if converter else []


def _value(row: dict[str, Any], names: Iterable[str], default: Any = None) -> Any:
    lowered = {str(key).lower(): value for key, value in row.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return default


def _round_for_tick(tick: int, rounds: list[dict[str, Any]]) -> int:
    for index, round_row in enumerate(rounds, start=1):
        start = int(_value(round_row, ("start", "start_tick"), -1))
        # The parser's regular end can precede official late-round events.
        # Prefer the explicit official boundary when it is available.
        end = int(_value(round_row, ("official_end", "end", "end_tick"), 2**63 - 1))
        if start <= tick <= end:
            number = _value(round_row, ("round_num", "round_number"), index)
            try:
                return int(number) if int(number) >= 1 else index
            except (TypeError, ValueError):
                return index
    return 0


def _round_for_kill(row: dict[str, Any], tick: int, rounds: list[dict[str, Any]]) -> int:
    """Prefer AWPy's explicit kill-round evidence over a boundary fallback."""
    number = _value(row, ("round_num", "round_number"))
    try:
        if number is not None and int(number) >= 1:
            return int(number)
    except (TypeError, ValueError):
        pass
    return _round_for_tick(tick, rounds)


def _regular_round_numbers(rounds: list[dict[str, Any]]) -> set[int]:
    """Return only completed rounds backed by usable AWPy round evidence."""
    numbers: set[int] = set()
    for round_row in rounds:
        number = _value(round_row, ("round_num", "round_number"))
        start = _value(round_row, ("start", "start_tick"))
        end = _value(round_row, ("official_end", "end", "end_tick"))
        winner = _value(round_row, ("winner",))
        reason = _value(round_row, ("reason",))
        try:
            if int(number) >= 1 and int(start) <= int(end) and isinstance(winner, str) and winner and isinstance(reason, str) and reason:
                numbers.add(int(number))
        except (TypeError, ValueError):
            continue
    return numbers


def _regular_kills(kill_rows: list[dict[str, Any]], rounds: list[dict[str, Any]]) -> tuple[list[Kill], int]:
    """Exclude warmup and unproven-round events from regular match metrics."""
    regular_rounds = _regular_round_numbers(rounds)
    kills: list[Kill] = []
    excluded = 0
    for row in kill_rows:
        tick = int(_value(row, ("tick",), 0) or 0)
        round_number = _round_for_kill(row, tick, rounds)
        if round_number not in regular_rounds:
            excluded += 1
            continue
        kills.append(
            Kill(
                round_number=round_number,
                tick=tick,
                attacker=str(_value(row, ("attacker_name", "attacker"), "") or "").strip(),
                victim=str(_value(row, ("victim_name", "victim", "user_name"), "") or "").strip(),
                weapon=str(_value(row, ("weapon",), "") or "").strip(),
                headshot=bool(_value(row, ("headshot",), False)),
            )
        )
    return kills, excluded


def _read_optional_channel(demo: Any, channel: str) -> tuple[Any, str | None]:
    """Awpy computes some channels lazily and may raise when their event is absent."""
    try:
        return getattr(demo, channel, None), None
    except (KeyError, AttributeError, TypeError, ValueError) as error:
        return None, f"{channel}: {type(error).__name__}: {error}"


class AwpyAdapter:
    """Adapt one parsed Awpy demo without giving consumers a second parser truth."""

    def parse_demo(self, path: str) -> Any:
        demo = Demo(path, verbose=False)
        # The replay builder needs these fields. Parsing them here lets the
        # workflow derive the compact analysis and replay-v2 from one Awpy run.
        demo.parse(player_props=list(REPLAY_PLAYER_PROPS))
        return demo

    def adapt(self, demo: Any) -> tuple[dict[str, Any], list[Kill], list[str], DataQuality]:
        header = getattr(demo, "header", {}) or {}
        rounds = _records(getattr(demo, "rounds", None))
        kill_rows = _records(getattr(demo, "kills", None))
        kills, excluded_non_match = _regular_kills(kill_rows, rounds)

        available = ["rounds", "kills"]
        missing: list[str] = []
        channel_errors: list[str] = []
        for channel in OPTIONAL_CHANNELS:
            value, channel_error = _read_optional_channel(demo, channel)
            if value is None:
                missing.append(channel)
                if channel_error:
                    channel_errors.append(channel_error)
            else:
                available.append(channel)

        warnings: list[str] = channel_errors
        status = "ok"
        if "footsteps" in missing:
            status = "limited"
            warnings.append("Footstep-Ereignisse fehlen; soundbezogene Marker sind deaktiviert.")
        if excluded_non_match:
            warnings.append(f"{excluded_non_match} Ereignis(se) außerhalb regulärer Matchrunden wurden ausgeschlossen.")
        if not rounds or not kill_rows:
            status = "not_assessable"
            warnings.append("Zentrale Runden- oder Killdaten fehlen.")
        return header, kills, available, DataQuality(status, missing, warnings)

    def parse(self, path: str) -> tuple[dict[str, Any], list[Kill], list[str], DataQuality]:
        """Compatibility entry point for independent analysis callers."""
        return self.adapt(self.parse_demo(path))
