from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .replay_contract import ReplayCapabilities


def _coverage(rows: list[dict[str, Any]], fields: Iterable[str]) -> str:
    fields = tuple(fields)
    if not rows or not fields:
        return "unavailable"
    complete = sum(all(row.get(field) is not None for field in fields) for row in rows)
    if complete == len(rows):
        return "full"
    if complete:
        return "partial"
    return "unavailable"


def assess_capabilities(
    tick_rows: list[dict[str, Any]],
    channels: dict[str, list[dict[str, Any]]],
    *,
    trajectories_materialized: bool = False,
) -> ReplayCapabilities:
    utility_rows = channels.get("smokes", []) + channels.get("infernos", [])
    has_grenade_points = bool(channels.get("grenades"))
    return ReplayCapabilities(
        positions=_coverage(tick_rows, ("X", "Y", "Z")),
        view_yaw=_coverage(tick_rows, ("yaw",)),
        view_pitch=_coverage(tick_rows, ("pitch",)),
        alive_state="partial" if tick_rows and any(row.get("health") is not None for row in tick_rows) else "unavailable",
        weapon_state=_coverage(tick_rows, ("active_weapon_name",)),
        velocity=_coverage(tick_rows, ("velocity_X", "velocity_Y", "velocity_Z")),
        utility_lifetimes=_coverage(utility_rows, ("start_tick", "end_tick", "X", "Y", "Z")),
        utility_trajectories=("full" if has_grenade_points and trajectories_materialized else "partial" if has_grenade_points else "unavailable"),
        flash_effect="unavailable",
        sound="full" if channels.get("footsteps") else "unavailable",
    )
