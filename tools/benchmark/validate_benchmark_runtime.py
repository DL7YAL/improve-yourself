"""Validate a complete iy-benchmark/v1.2-candidate.2 CS2 runtime log.

The validator is read-only and uses only the Python standard library. It is
intended to run on the Windows benchmark machine after a normal CS2 viewer
run. Quoted console echoes are ignored so each canonical ``[IYBENCH]`` event
is counted once.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


VERSION = "iy-benchmark/v1.2-candidate.2"
MEASUREMENT_STATUS = (
    "MEASUREMENT_STATUS status=unverified "
    "reason=client_commands_require_runtime_confirmation"
)


def pass_events(pass_name: str) -> list[str]:
    events = [
        f"PASS_START type={pass_name} version={VERSION}",
        f"SCENE_START scene=nuke_outside pass={pass_name}",
        f"CAPTURE_WINDOW pass={pass_name} scene=nuke_outside "
        "landmark=yard_landmarks expected_t=9",
        "TRANSITION_ENTER from=nuke_outside to=ancient_b occlusion=smoke",
    ]
    if pass_name == "measured":
        events.append("REPORT scene=nuke_outside")
    events.extend(
        [
            "TRANSITION_SWAP from=nuke_outside to=ancient_b occlusion=smoke",
            f"SCENE_START scene=ancient_b pass={pass_name}",
            "TRANSITION_EXIT from=nuke_outside to=ancient_b occlusion=smoke",
            f"CAPTURE_WINDOW pass={pass_name} scene=ancient_b "
            "landmark=water_reflection expected_t=27",
            f"CAPTURE_WINDOW pass={pass_name} scene=ancient_b "
            "landmark=red_room expected_t=38",
            "TRANSITION_APPROACH from=ancient_b to=inferno_apps_a "
            "occlusion=flash landmark=red_room",
            "TRANSITION_ENTER from=ancient_b to=inferno_apps_a "
            "occlusion=flash landmark=red_room",
        ]
    )
    if pass_name == "measured":
        events.append("REPORT scene=ancient_b")
    events.extend(
        [
            "TRANSITION_SWAP from=ancient_b to=inferno_apps_a "
            "occlusion=flash landmark=red_room",
            f"SCENE_START scene=inferno_apps_a pass={pass_name}",
            "TRANSITION_EXIT from=ancient_b to=inferno_apps_a "
            "occlusion=flash landmark=red_room",
            f"CAPTURE_WINDOW pass={pass_name} scene=inferno_apps_a "
            "landmark=stairs expected_t=48",
            f"CAPTURE_WINDOW pass={pass_name} scene=inferno_apps_a "
            "landmark=apps_details expected_t=53",
        ]
    )
    if pass_name == "measured":
        events.extend(
            [
                "REPORT scene=inferno_apps_a",
                "PASS_END type=measured runtime_status=complete "
                "measurement_status=unverified",
            ]
        )
    else:
        events.append("PASS_END type=warmup")
    return events


EXPECTED_EVENTS = [
    f"READY version={VERSION}",
    *pass_events("warmup"),
    MEASUREMENT_STATUS,
    *pass_events("measured"),
]

CONTRACT_PREFIXES = (
    "READY ",
    "PASS_START ",
    "PASS_END ",
    "SCENE_START ",
    "CAPTURE_WINDOW ",
    "TRANSITION_",
    "REPORT ",
    "MEASUREMENT_STATUS ",
    "ERROR ",
)

PLAIN_EVENT = re.compile(r"^\s*\[IYBENCH\]\s+(.*)$")
VCONSOLE_SCRIPT_EVENT = re.compile(
    r"^\s*\[\s*cs_script\s*\]\s*:\s*\[IYBENCH\]\s+(.*)$"
)


def canonical_events(text: str) -> list[str]:
    events = []
    for line in text.splitlines():
        match = PLAIN_EVENT.match(line) or VCONSOLE_SCRIPT_EVENT.match(line)
        if match:
            events.append(match.group(1))
    return events


def split_segments(events: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    for event in events:
        if event.startswith("READY "):
            segments.append([])
        if segments:
            segments[-1].append(event)
    return segments


@dataclass(frozen=True)
class Validation:
    status: str
    segment_index: int
    segment_count: int
    canonical_event_count: int
    errors: tuple[str, ...]

    def as_dict(self, sha256: str) -> dict[str, object]:
        return {
            "schema": "iy.cs2-benchmark-runtime-validation/v1",
            "benchmark_version": VERSION,
            "status": self.status,
            "selected_segment": self.segment_index,
            "segments_detected": self.segment_count,
            "canonical_event_count": self.canonical_event_count,
            "runtime_status": "complete" if self.status == "PASS" else "unverified",
            "measurement_status": "unverified",
            "input_sha256": sha256.upper(),
            "errors": list(self.errors),
        }


def validate_latest(text: str) -> Validation:
    events = canonical_events(text)
    segments = split_segments(events)
    if not segments:
        return Validation("BLOCKED", 0, 0, 0, ("no canonical READY segment found",))

    selected = segments[-1]
    observed = [event for event in selected if event.startswith(CONTRACT_PREFIXES)]
    errors: list[str] = []
    runtime_errors = [event for event in observed if event.startswith("ERROR ")]
    if runtime_errors:
        errors.extend(runtime_errors)

    if observed != EXPECTED_EVENTS:
        mismatch = next(
            (
                index
                for index, (actual, expected) in enumerate(zip(observed, EXPECTED_EVENTS))
                if actual != expected
            ),
            min(len(observed), len(EXPECTED_EVENTS)),
        )
        expected = EXPECTED_EVENTS[mismatch] if mismatch < len(EXPECTED_EVENTS) else "<end>"
        actual = observed[mismatch] if mismatch < len(observed) else "<missing>"
        errors.append(
            f"contract mismatch at event {mismatch + 1}: expected {expected!r}, got {actual!r}"
        )
        if len(observed) != len(EXPECTED_EVENTS):
            errors.append(
                f"contract event count: expected {len(EXPECTED_EVENTS)}, got {len(observed)}"
            )

    status = "PASS" if not errors else "PARTIAL"
    return Validation(status, len(segments), len(segments), len(selected), tuple(errors))


def read_input(path: str) -> bytes:
    if path == "-":
        return sys.stdin.buffer.read()
    return Path(path).read_bytes()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the latest canonical IYBENCH run in a CS2 console log."
    )
    parser.add_argument("log", help="Path to the CS2 log, or - for standard input")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    raw = read_input(args.log)
    digest = hashlib.sha256(raw).hexdigest()
    result = validate_latest(raw.decode("utf-8", errors="replace"))
    payload = result.as_dict(digest)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"STATUS={payload['status']}")
        print(f"benchmark_version={VERSION}")
        print(f"selected_segment={result.segment_index}/{result.segment_count}")
        print(f"canonical_events={result.canonical_event_count}")
        print(f"runtime_status={payload['runtime_status']}")
        print("measurement_status=unverified")
        print(f"input_sha256={payload['input_sha256']}")
        for error in result.errors:
            print(f"ERROR={error}")

    return 0 if result.status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
