from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .awpy_adapter import AwpyAdapter
from .criteria import DEFAULT_PROFILE, default_review_hints
from .domain import round_multikills
from .importer import materialize_demo
from .model import AnalysisResult


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_analysis_user_view(kills: list, multikills: list, quality: object) -> dict:
    quality_status = getattr(quality, "status", "not_assessable")
    missing = list(getattr(quality, "missing_channels", []))
    if quality_status == "ok":
        assessment = {
            "status": "OK", "priority": "informativ",
            "message": "Die verfügbaren Ereignisdaten reichen für diese erste Einordnung aus.",
            "action": "Szenen im Tactical Replay mit eigenem Spielkontext prüfen.",
        }
    elif quality_status == "limited":
        assessment = {
            "status": "Hinweis", "priority": "wichtig",
            "message": "Ein Teil der Ereignisdaten fehlt; einzelne Fragen bleiben offen.",
            "action": "Szenen prüfen, aber fehlende Quellen nicht hineininterpretieren.",
        }
    else:
        assessment = {
            "status": "Nicht prüfbar / unbekannt", "priority": "wichtig",
            "message": "Zentrale Daten fehlen; eine belastbare Szenenbewertung ist eingeschränkt.",
            "action": "Eine andere Demo oder vollständiger verfügbare Daten verwenden. Keine Aussage erzwingen.",
        }
    limitations = [
        "Schritt-Ereignisse fehlen; soundbezogene Hinweise sind nicht bewertbar." if channel == "footsteps"
        else f"Der Datenkanal „{channel}“ fehlt und wird nicht bewertet."
        for channel in missing
    ]
    return {
        "facts": [
            f"{len(kills)} Kills wurden aus der Demo gelesen.",
            f"{len(multikills)} Multi-Kill-Szenen wurden als Review-Einstieg gefunden.",
        ],
        "indicators": [
            "Szenen sind Prüfhinweise und kein Cheat-Nachweis.",
        ],
        "limitations": limitations or ["Keine relevante Datenlücke gemeldet."],
        "assessment": assessment,
    }


def analyze(source: Path, output_directory: Path, max_bytes: int = 2_000_000_000) -> Path:
    source = source.resolve()
    checksum = _sha256(source)
    with materialize_demo(source, max_bytes=max_bytes) as demo_path:
        header, kills, channels, quality = AwpyAdapter().parse(str(demo_path))
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
    payload = result.to_dict()
    payload["review_profile"] = DEFAULT_PROFILE
    payload["review_hints"] = default_review_hints(result.multikills)
    payload["user_view"] = build_analysis_user_view(kills, result.multikills, quality)
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / f"{checksum[:12]}.analysis.json"
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination
