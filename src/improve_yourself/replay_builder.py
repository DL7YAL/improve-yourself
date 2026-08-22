from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .analyzer_core import AnalysisRequestV1, AnalyzerCore
from .importer import materialize_demo
from .replay_contract import (
    REPLAY_V2_SCHEMA,
    ROUND_CHUNK_SCHEMA,
    PlayerIdentity,
    PlayerState,
    ReplayCapabilities,
    ReplayEvent,
    ReplayFrame,
    UtilityState,
    Vec3,
    to_dict,
)
from .replay_validation import validate_replay_manifest, validate_round_chunk
from .validation import validate_analysis_payload


def _records(frame: Any) -> list[dict[str, Any]]:
    if frame is None:
        return []
    converter = getattr(frame, "to_dicts", None)
    return converter() if converter else list(frame)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _vec3(row: dict[str, Any], prefix: str = "") -> Vec3 | None:
    values = tuple(_float(row.get(f"{prefix}{axis}")) for axis in ("X", "Y", "Z"))
    if any(value is None for value in values):
        return None
    return Vec3(*values)  # type: ignore[arg-type]


def _team(value: Any) -> str:
    normalized = str(value or "").upper()
    return normalized if normalized in {"T", "CT"} else "unknown"


class IdentityRegistry:
    def __init__(self, source_hash: str) -> None:
        self.source_hash = source_hash
        self.identities: dict[str, PlayerIdentity] = {}
        self.omitted_unresolved_snapshots = 0

    def resolve(self, steam_id: Any, display_name: Any, *, count_omission: bool = False) -> str | None:
        numeric = _int(steam_id)
        if numeric is None or numeric <= 0:
            if count_omission:
                self.omitted_unresolved_snapshots += 1
            return None
        steam = str(numeric)
        player_id = f"steam:{steam}"
        name = str(display_name or "")
        existing = self.identities.get(player_id)
        if existing is None or (not existing.display_name and name):
            self.identities[player_id] = PlayerIdentity(
                player_id=player_id,
                steam_id=steam,
                entity_id=None,
                display_name=name,
                identity_quality="steam",
            )
        return player_id


class CapabilityAccumulator:
    PLAYER_FIELDS = {
        "positions": ("X", "Y", "Z"),
        "view_yaw": ("yaw",),
        "view_pitch": ("pitch",),
        "weapon_state": ("active_weapon_name",),
        "velocity": ("velocity_X", "velocity_Y", "velocity_Z"),
    }

    def __init__(self) -> None:
        self.total = 0
        self.complete = {name: 0 for name in self.PLAYER_FIELDS}
        self.health_present = 0

    def observe(self, row: dict[str, Any]) -> None:
        self.total += 1
        for name, fields in self.PLAYER_FIELDS.items():
            if all(row.get(field) is not None for field in fields):
                self.complete[name] += 1
        if row.get("health") is not None:
            self.health_present += 1

    def level(self, name: str) -> str:
        count = self.complete[name]
        if not self.total or not count:
            return "unavailable"
        return "full" if count == self.total else "partial"


def _player_state(row: dict[str, Any], registry: IdentityRegistry) -> PlayerState | None:
    player_id = registry.resolve(row.get("steamid"), row.get("name"), count_omission=True)
    if player_id is None:
        return None
    position = _vec3(row)
    velocity = _vec3(row, "velocity_")
    health = _int(row.get("health"))
    armor = _int(row.get("armor"))
    yaw = _float(row.get("yaw"))
    pitch = _float(row.get("pitch"))
    availability = []
    if position is not None:
        availability.append("position")
    if yaw is not None:
        availability.append("view_yaw")
    if pitch is not None:
        availability.append("view_pitch")
    if velocity is not None:
        availability.append("velocity")
    if health is not None:
        availability.extend(("health", "alive"))
    if armor is not None:
        availability.append("armor")
    weapon = str(row.get("active_weapon_name") or "") or None
    if weapon is not None:
        availability.append("weapon")
    return PlayerState(
        player_id=player_id,
        active=True,
        alive=(health > 0) if health is not None else None,
        team=_team(row.get("side")),  # type: ignore[arg-type]
        position=position,
        view_yaw_deg=yaw,
        view_pitch_deg=pitch,
        velocity=velocity,
        health=health,
        armor=armor,
        weapon=weapon,
        availability=tuple(sorted(availability)),
    )


def _event_player_ids(row: dict[str, Any], channel: str, registry: IdentityRegistry) -> tuple[str, ...]:
    candidates: list[tuple[Any, Any]] = []
    if channel == "kills":
        candidates = [(row.get("attacker_steamid"), row.get("attacker_name")), (row.get("victim_steamid"), row.get("victim_name"))]
    elif channel == "damages":
        candidates = [(row.get("attacker_steamid"), row.get("attacker_name")), (row.get("victim_steamid"), row.get("victim_name"))]
    elif channel == "shots":
        candidates = [(row.get("player_steamid"), row.get("player_name"))]
    elif channel == "bomb":
        candidates = [(row.get("steamid"), row.get("name"))]
    result = []
    for steam_id, name in candidates:
        player_id = registry.resolve(steam_id, name)
        if player_id is not None and player_id not in result:
            result.append(player_id)
    return tuple(result)


def normalize_events(
    channel: str, rows: list[dict[str, Any]], registry: IdentityRegistry
) -> dict[int, list[ReplayEvent]]:
    by_tick: dict[int, list[ReplayEvent]] = defaultdict(list)
    type_map = {"kills": "kill", "damages": "damage", "shots": "weapon_fire"}
    for index, row in enumerate(rows):
        tick = _int(row.get("tick"))
        if tick is None or tick < 0:
            continue
        event_type = type_map.get(channel)
        if channel == "bomb":
            raw = str(row.get("event") or "").lower()
            event_type = {"plant": "bomb_plant", "planted": "bomb_plant", "defuse": "bomb_defuse", "defused": "bomb_defuse"}.get(raw)
        if event_type is None:
            continue
        position_prefix = "attacker_" if channel in {"kills", "damages"} else "player_" if channel == "shots" else ""
        position = _vec3(row, position_prefix)
        details = {}
        for key in ("weapon", "headshot", "penetrated", "thrusmoke", "attacker_blind", "dmg_health", "dmg_armor", "bombsite"):
            if row.get(key) is not None:
                details[key] = row[key]
        if "thrusmoke" not in details and row.get("through_smoke") is not None:
            details["thrusmoke"] = row["through_smoke"]
        by_tick[tick].append(
            ReplayEvent(
                event_id=f"{channel}:{tick}:{index}",
                type=event_type,
                tick=tick,
                player_ids=_event_player_ids(row, channel, registry),
                position=position,
                details=details,
            )
        )
    return by_tick


def normalize_utilities(
    channel: str, rows: list[dict[str, Any]], registry: IdentityRegistry
) -> list[UtilityState]:
    result = []
    utility_type = "smoke" if channel == "smokes" else "molotov"
    for index, row in enumerate(rows):
        start = _int(row.get("start_tick"))
        if start is None:
            continue
        entity = _int(row.get("entity_id"))
        owner = registry.resolve(row.get("thrower_steamid"), row.get("thrower_name"))
        result.append(
            UtilityState(
                utility_id=f"{channel}:{entity if entity is not None else index}:{start}",
                utility_type=utility_type,
                owner_player_id=owner,
                start_tick=start,
                end_tick=_int(row.get("end_tick")),
                position=_vec3(row),
                trajectory=None,
                active=False,
                evidence="lifetime",
            )
        )
    return result


def build_round_chunk(
    round_number: int,
    tick_rows: list[dict[str, Any]],
    *,
    round_start_tick: int | None,
    tick_rate: float | None,
    events_by_tick: dict[int, list[ReplayEvent]],
    utilities: list[UtilityState],
    registry: IdentityRegistry,
    capabilities: CapabilityAccumulator,
) -> dict[str, Any]:
    player_rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in tick_rows:
        capabilities.observe(row)
        tick = _int(row.get("tick"))
        if tick is not None:
            player_rows[tick].append(row)
    all_ticks = sorted(set(player_rows) | set(events_by_tick))
    frames = []
    for tick in all_ticks:
        players = [state for row in player_rows.get(tick, []) if (state := _player_state(row, registry)) is not None]
        active_utilities = [
            UtilityState(**{**utility.__dict__, "active": True})
            for utility in utilities
            if utility.start_tick <= tick and (utility.end_tick is None or tick <= utility.end_tick)
        ]
        display_seconds = None
        if tick_rate and round_start_tick is not None:
            display_seconds = (tick - round_start_tick) / tick_rate
        frame = ReplayFrame(
            tick=tick,
            round_number=round_number,
            time_in_round_seconds=display_seconds,
            players=tuple(sorted(players, key=lambda item: item.player_id)),
            utilities=tuple(sorted(active_utilities, key=lambda item: item.utility_id)),
            events=tuple(events_by_tick.get(tick, [])),
        )
        frames.append(to_dict(frame))
    return {"schema": ROUND_CHUNK_SCHEMA, "round_number": round_number, "frames": frames}


def _write_gzip_json(path: Path, payload: dict[str, Any]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as stream:
        json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"))


def export_replay_v2(
    source: Path,
    analysis_path: Path,
    output: Path,
    *,
    source_sha256: str | None = None,
    parsed_demo: Any | None = None,
) -> Path:
    """Build the canonical replay artifact.

    The optional canonical values are used by ``preflight_demo_workflow`` so a
    new import does not hash or parse the same source again. Standalone callers
    retain the self-contained source validation and parse path.
    """
    source = source.resolve()
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    analysis_errors = validate_analysis_payload(analysis)
    if analysis_errors:
        raise ValueError("invalid analysis payload: " + "; ".join(analysis_errors))
    digest = source_sha256 or _sha256(source)
    if digest != analysis.get("source_sha256"):
        raise ValueError("demo and analysis source hashes differ")

    if parsed_demo is None:
        with materialize_demo(source, max_bytes=2_000_000_000) as demo_path:
            prepared = AnalyzerCore().prepare(
                AnalysisRequestV1.create(source), parser_path=demo_path, source_sha256=digest, source_name=source.name
            )
            return _export_replay_v2_from_parsed(source, analysis, output, digest, prepared.parsed_demo)
    return _export_replay_v2_from_parsed(source, analysis, output, digest, parsed_demo)


def _export_replay_v2_from_parsed(
    source: Path, analysis: dict[str, Any], output: Path, digest: str, demo: Any
) -> Path:

    output = output.resolve() / digest[:12]
    chunks_directory = output / "rounds"
    chunks_directory.mkdir(parents=True, exist_ok=True)
    registry = IdentityRegistry(digest)
    accumulator = CapabilityAccumulator()

    header = getattr(demo, "header", {}) or {}
    if str(header.get("map_name", "")) != analysis.get("map_name"):
        raise ValueError("demo header map differs from analysis")
    round_rows = _records(getattr(demo, "rounds", None))
    round_metadata = {int(row["round_num"]): row for row in round_rows}

    event_channels = {name: _records(getattr(demo, name, None)) for name in ("kills", "damages", "shots", "bomb")}
    utility_channels = {name: _records(getattr(demo, name, None)) for name in ("smokes", "infernos")}
    events_by_round: dict[int, dict[int, list[ReplayEvent]]] = defaultdict(lambda: defaultdict(list))
    for channel, rows in event_channels.items():
        per_tick = normalize_events(channel, rows, registry)
        rows_by_tick = {int(row["tick"]): int(row.get("round_num", 0) or 0) for row in rows if row.get("tick") is not None}
        for tick, events in per_tick.items():
            events_by_round[rows_by_tick.get(tick, 0)][tick].extend(events)
    utilities_by_round: dict[int, list[UtilityState]] = defaultdict(list)
    for channel, rows in utility_channels.items():
        normalized = normalize_utilities(channel, rows, registry)
        round_by_start = {int(row["start_tick"]): int(row.get("round_num", 0) or 0) for row in rows if row.get("start_tick") is not None}
        for utility in normalized:
            utilities_by_round[round_by_start.get(utility.start_tick, 0)].append(utility)

    round_descriptors = []
    current_round: int | None = None
    current_rows: list[dict[str, Any]] = []

    def flush_round(number: int, rows: list[dict[str, Any]]) -> None:
        metadata = round_metadata.get(number, {})
        chunk = build_round_chunk(
            number,
            rows,
            round_start_tick=_int(metadata.get("start")),
            tick_rate=analysis.get("tickrate"),
            events_by_tick=events_by_round.get(number, {}),
            utilities=utilities_by_round.get(number, []),
            registry=registry,
            capabilities=accumulator,
        )
        chunk_errors = validate_round_chunk(chunk)
        if chunk_errors:
            raise ValueError(f"round {number} is invalid: " + "; ".join(chunk_errors))
        chunk_name = f"round-{number:03d}.json.gz"
        chunk_path = chunks_directory / chunk_name
        _write_gzip_json(chunk_path, chunk)
        frames = chunk["frames"]
        round_descriptors.append({
            "round_number": number,
            "first_tick": frames[0]["tick"],
            "last_tick": frames[-1]["tick"],
            "frame_count": len(frames),
            "chunk": f"rounds/{chunk_name}",
            "sha256": _sha256(chunk_path),
        })

    for row in demo.ticks.iter_rows(named=True):
        number = int(row.get("round_num", 0) or 0)
        if number <= 0:
            continue
        if current_round is None:
            current_round = number
        if number != current_round:
            flush_round(current_round, current_rows)
            current_round, current_rows = number, []
        current_rows.append(row)
    if current_round is not None and current_rows:
        flush_round(current_round, current_rows)

    grenade_frame = getattr(demo, "grenades", None)
    has_trajectories = grenade_frame is not None and getattr(grenade_frame, "height", 0) > 0
    try:
        footsteps = getattr(demo, "footsteps", None)
    except (KeyError, AttributeError, TypeError, ValueError):
        footsteps = None

    def level(name: str) -> str:
        return accumulator.level(name)

    utility_rows = utility_channels["smokes"] + utility_channels["infernos"]
    capabilities = ReplayCapabilities(
        positions=level("positions"),  # type: ignore[arg-type]
        view_yaw=level("view_yaw"),  # type: ignore[arg-type]
        view_pitch=level("view_pitch"),  # type: ignore[arg-type]
        alive_state="partial" if accumulator.health_present else "unavailable",
        weapon_state=level("weapon_state"),  # type: ignore[arg-type]
        velocity=level("velocity"),  # type: ignore[arg-type]
        utility_lifetimes="full" if utility_rows and all(all(row.get(key) is not None for key in ("start_tick", "end_tick", "X", "Y", "Z")) for row in utility_rows) else "partial" if utility_rows else "unavailable",
        utility_trajectories="partial" if has_trajectories else "unavailable",
        flash_effect="unavailable",
        sound="full" if footsteps is not None else "unavailable",
    )
    names_to_ids: dict[str, list[str]] = defaultdict(list)
    for identity in registry.identities.values():
        names_to_ids[identity.display_name].append(identity.player_id)
    scenes = []
    for marker in analysis.get("multikills", []):
        matches = names_to_ids.get(marker["player"], [])
        scenes.append({
            "scene_id": f"r{marker['round_number']}-t{marker['first_tick']}-{marker['last_tick']}-{len(scenes)}",
            "round_number": marker["round_number"],
            "tick": marker["first_tick"],
            "end_tick": marker["last_tick"],
            "focus_player_id": matches[0] if len(matches) == 1 else None,
            "criterion_id": "round_multikill",
            "event_ids": [],
        })
    manifest = {
        "schema": REPLAY_V2_SCHEMA,
        "source": {
            "sha256": digest,
            "map_id": analysis["map_name"],
            "tick_rate": analysis.get("tickrate"),
            "parser": {"name": "awpy", "version": "2.0.2"},
        },
        "coordinate_space": "cs2_world",
        "capabilities": to_dict(capabilities),
        "players": [to_dict(registry.identities[key]) for key in sorted(registry.identities)],
        "rounds": round_descriptors,
        "scenes": scenes,
        "data_quality": {
            "omitted_unresolved_player_snapshots": registry.omitted_unresolved_snapshots,
            "alive_state_note": "Health-derived state is available only for observed active rows; absent/dead rows are not reconstructed.",
            "trajectory_note": "Grenade trajectory source exists but is not materialized in Slice A; capability is partial.",
            "warnings": list(analysis.get("data_quality", {}).get("warnings", [])),
        },
    }
    errors = validate_replay_manifest(manifest)
    if errors:
        raise ValueError("invalid replay manifest: " + "; ".join(errors))
    destination = output / "replay-v2.json"
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an iy.replay/v2 full-match store")
    parser.add_argument("demo", type=Path)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/replay-v2"))
    args = parser.parse_args()
    try:
        print(export_replay_v2(args.demo, args.analysis, args.output))
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
