"""Audit CS2 VConsole evidence beyond the IYBENCH event contract.

The runtime validator proves event order. This companion audit keeps engine
diagnostics and the bot population separate so a contract PASS cannot be
mistaken for world acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from validate_benchmark_runtime import validate_latest


EXPECTED_BOTS = 10
BOT_CREATE = re.compile(r"ClientPutInServer create new player controller \[([^]]+)\]")
BOT_IDENTITY = re.compile(r'"([^<]+)<[^>]*><BOT><')
BOT_KICK = re.compile(r"]:\s+(.+?) kicked by Console \(")
FIRST_WARMUP = re.compile(
    r"^\s*\[\s*cs_script\s*\]\s*:\s*\[IYBENCH\]\s+PASS_START type=warmup\b"
)
DENIED_COMMAND = re.compile(
    r"Cannot (?:execute concommand|set convar) '([^']+)'[^\n]*missing required FCVAR flag"
)

CLIENT_ONLY_COMMANDS = frozenset(
    {
        "con_enable",
        "con_logfile",
        "fps_max",
        "cl_drawhud",
        "r_drawviewmodel",
        "cl_showfps",
        "cl_frametime_summary_report_detailed",
        "+attack",
        "-attack",
        "vprof_off",
        "vprof_reset",
        "vprof_on",
        "vprof_generate_report",
    }
)


@dataclass(frozen=True)
class Pattern:
    identifier: str
    severity: str
    needle: str


PATTERNS = (
    Pattern(
        "cubemap_resource_missing",
        "BLOCKER",
        'Failed loading resource "maps/improve_yourself_benchmark/cubemaps/'
        'env_cubemap_array.vtex_c"',
    ),
    Pattern(
        "cubemap_fog_unresolved",
        "BLOCKER",
        "Unable to determine cubemap texture for env_cubemap_fog",
    ),
    Pattern(
        "nav_generation_mismatch",
        "BLOCKER",
        "used during construction differ from defaults. Please re-export the map.",
    ),
    Pattern(
        "vertical_velocity_failure",
        "BLOCKER",
        "Got a velocity too low (<-3500.00) on Z",
    ),
    Pattern("vscript_exception", "BLOCKER", "VScript exception"),
    Pattern(
        "pipeline_cache_write_failed",
        "WARNING",
        "Unable to write to pipeline cache file",
    ),
    Pattern(
        "camera_nodes_missing",
        "WARNING",
        "improve_yourself_benchmark_camera_nodes.kv3",
    ),
    Pattern(
        "overview_missing",
        "WARNING",
        "CMapOverview::SetMap: couldn't load file",
    ),
)


def bots_at_first_warmup(text: str) -> tuple[str, ...] | None:
    created: set[str] = set()
    bots: set[str] = set()
    for line in text.splitlines():
        if FIRST_WARMUP.match(line):
            return tuple(sorted(bots))
        if match := BOT_CREATE.search(line):
            created.add(match.group(1))
        if match := BOT_IDENTITY.search(line):
            name = match.group(1)
            if name in created:
                bots.add(name)
        if match := BOT_KICK.search(line):
            name = match.group(1)
            created.discard(name)
            bots.discard(name)
    return None


def audit_text(text: str, sha256: str) -> dict[str, object]:
    runtime = validate_latest(text)
    bot_names = bots_at_first_warmup(text)
    lines = text.splitlines()
    diagnostics = [
        {
            "id": pattern.identifier,
            "severity": pattern.severity,
            "count": sum(pattern.needle in line for line in lines),
        }
        for pattern in PATTERNS
        if pattern.needle in text
    ]

    denied = [
        match.group(1)
        for match in DENIED_COMMAND.finditer(text)
        if match.group(1) in CLIENT_ONLY_COMMANDS
    ]
    if denied:
        diagnostics.append(
            {
                "id": "required_client_command_denied",
                "severity": "BLOCKER",
                "count": len(denied),
                "commands": sorted(set(denied)),
            }
        )

    if bot_names is None:
        diagnostics.append(
            {"id": "bot_population_unverified", "severity": "BLOCKER", "count": 1}
        )
    elif len(bot_names) != EXPECTED_BOTS:
        diagnostics.append(
            {
                "id": "bot_population_mismatch",
                "severity": "BLOCKER",
                "count": 1,
                "expected": EXPECTED_BOTS,
                "observed": len(bot_names),
            }
        )

    if runtime.status != "PASS":
        status = "BLOCKED"
    elif any(item["severity"] == "BLOCKER" for item in diagnostics):
        status = "NEEDS_WORK"
    else:
        status = "CLEAR"

    return {
        "schema": "iy.cs2-benchmark-vconsole-audit/v1",
        "status": status,
        "runtime_contract_status": runtime.status,
        "runtime_contract_errors": list(runtime.errors),
        "input_sha256": sha256.upper(),
        "expected_bots_at_first_warmup": EXPECTED_BOTS,
        "observed_bots_at_first_warmup": None if bot_names is None else len(bot_names),
        "observed_bot_names": [] if bot_names is None else list(bot_names),
        "diagnostics": diagnostics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit a full benchmark VConsole capture for world/runtime blockers."
    )
    parser.add_argument("log", help="Path to the VConsole capture, or - for stdin")
    args = parser.parse_args(argv)

    raw = sys.stdin.buffer.read() if args.log == "-" else Path(args.log).read_bytes()
    payload = audit_text(
        raw.decode("utf-8", errors="replace"), hashlib.sha256(raw).hexdigest()
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "CLEAR" else 2


if __name__ == "__main__":
    raise SystemExit(main())
