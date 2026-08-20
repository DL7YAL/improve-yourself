from __future__ import annotations

import gzip
import hashlib
import json
import argparse
from bisect import bisect_right
from pathlib import Path
from typing import Any

from .replay_validation import validate_replay_manifest, validate_round_chunk


class ReplayStore:
    """Read-only indexed access to a chunked iy.replay/v2 artifact."""

    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = manifest_path.resolve()
        self.root = self.manifest_path.parent
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        errors = validate_replay_manifest(self.manifest)
        if errors:
            raise ValueError("invalid replay manifest: " + "; ".join(errors))
        self._rounds = {item["round_number"]: item for item in self.manifest["rounds"]}
        self._cache: dict[int, dict[str, Any]] = {}

    @property
    def round_numbers(self) -> tuple[int, ...]:
        return tuple(sorted(self._rounds))

    def round_descriptor(self, round_number: int) -> dict[str, Any]:
        try:
            return dict(self._rounds[round_number])
        except KeyError as error:
            raise KeyError(f"round {round_number} is not available") from error

    def load_round(self, round_number: int) -> dict[str, Any]:
        if round_number in self._cache:
            return self._cache[round_number]
        descriptor = self._rounds.get(round_number)
        if descriptor is None:
            raise KeyError(f"round {round_number} is not available")
        path = (self.root / descriptor["chunk"]).resolve()
        if self.root not in path.parents:
            raise ValueError("round chunk escapes replay root")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != descriptor.get("sha256"):
            raise ValueError(f"round {round_number} chunk hash differs")
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            chunk = json.load(stream)
        known_ids = {player["player_id"] for player in self.manifest["players"]}
        errors = validate_round_chunk(chunk, known_ids)
        if errors:
            raise ValueError(f"invalid round {round_number}: " + "; ".join(errors))
        self._cache = {round_number: chunk}
        return chunk

    def frame_at_or_before(self, round_number: int, tick: int) -> dict[str, Any]:
        frames = self.load_round(round_number)["frames"]
        ticks = [frame["tick"] for frame in frames]
        index = bisect_right(ticks, tick) - 1
        if index < 0:
            raise KeyError(f"no frame at or before tick {tick} in round {round_number}")
        return frames[index]

    def exact_frame(self, round_number: int, tick: int) -> dict[str, Any]:
        frame = self.frame_at_or_before(round_number, tick)
        if frame["tick"] != tick:
            raise KeyError(f"tick {tick} is not present in round {round_number}")
        return frame


def validate_store(manifest_path: Path) -> dict[str, Any]:
    store = ReplayStore(manifest_path)
    totals = {"rounds": 0, "frames": 0, "player_states": 0, "events": 0, "active_utility_states": 0}
    for round_number in store.round_numbers:
        chunk = store.load_round(round_number)
        totals["rounds"] += 1
        totals["frames"] += len(chunk["frames"])
        totals["player_states"] += sum(len(frame.get("players", [])) for frame in chunk["frames"])
        totals["events"] += sum(len(frame.get("events", [])) for frame in chunk["frames"])
        totals["active_utility_states"] += sum(len(frame.get("utilities", [])) for frame in chunk["frames"])
    return {
        "schema": "iy.replay_regression/v1",
        "status": "PASS",
        "source_sha256": store.manifest["source"]["sha256"],
        "map_id": store.manifest["source"]["map_id"],
        "tick_rate": store.manifest["source"]["tick_rate"],
        "players": len(store.manifest["players"]),
        "scenes": len(store.manifest.get("scenes", [])),
        "capabilities": store.manifest["capabilities"],
        "data_quality": store.manifest["data_quality"],
        **totals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an iy.replay/v2 store")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    try:
        summary = validate_store(args.manifest)
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
