from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .analyzer_core import AnalysisRequestV1, AnalyzerCore, CoreParseResult
from .domain import round_multikills
from .importer import materialize_demo
from .model import AnalysisResult


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze(
    source: Path,
    output_directory: Path,
    max_bytes: int = 2_000_000_000,
    *,
    source_sha256: str | None = None,
    parsed_demo: Any | None = None,
    core_result: CoreParseResult | None = None,
) -> Path:
    """Write the existing iy.analysis/v1 artifact from a canonical source."""
    source = source.resolve()
    checksum = source_sha256 or _sha256(source)
    if core_result is not None:
        header, kills, channels, quality = core_result.analysis_input
    elif parsed_demo is None:
        with materialize_demo(source, max_bytes=max_bytes) as demo_path:
            prepared = AnalyzerCore().prepare(
                AnalysisRequestV1.create(source), parser_path=demo_path, source_sha256=checksum, source_name=source.name
            )
            header, kills, channels, quality = prepared.analysis_input
    else:
        # Compatibility for the former private call path.  New product code
        # passes ``core_result`` so the Core remains the Awpy boundary.
        raise ValueError("parsed_demo is internal; pass a CoreParseResult")
    tickrate_value = header.get("tick_rate", header.get("tickrate"))
    result = AnalysisResult(
        source_name=source.name,
        source_sha256=checksum,
        map_name=str(header.get("map_name", "")),
        tickrate=float(tickrate_value) if tickrate_value is not None else None,
        kills=kills,
        multikills=round_multikills(kills),
        data_quality=quality,
        available_channels=sorted(channels),
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / f"{checksum[:12]}.analysis.json"
    destination.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return destination
