from __future__ import annotations

from typing import Any

from .model import Multikill

DEFAULT_PROFILE = {
    "id": "iy.default_review",
    "version": "v1",
    "label": "Improve Default V1",
    "disclaimer": "Profilregeln markieren vorhandene Fakten zur menschlichen Prüfung und sind kein Cheat-Nachweis.",
    "criteria": [{
        "id": "round_multikill", "label": "Rundenweiter Multi-Kill",
        "threshold": {"field": "kill_count", "operator": ">=", "value": 3},
        "requires": ["kills", "rounds"], "status": "active",
    }],
    "planned_families": [
        {"id": "crosshair_information", "label": "Crosshair Placement / Informationskorrelation", "requires": ["positions", "view_angles", "visibility"], "status": "not_implemented"},
        {"id": "aim_input", "label": "Aim / Mouse / Input-Verhalten", "requires": ["input"], "status": "not_implemented"},
        {"id": "visibility_reaction", "label": "Sichtbarkeit / Reaktion", "requires": ["positions", "view_angles", "visibility", "ticks"], "status": "not_implemented"},
        {"id": "sound_information", "label": "Sound / Information", "requires": ["footsteps"], "status": "not_implemented"},
        {"id": "gameplay_context", "label": "Gameplay- / Ereigniskontext", "requires": ["kills", "rounds"], "status": "not_implemented"},
        {"id": "statistical_context", "label": "Statistische Kontextwerte", "requires": ["kills", "rounds"], "status": "not_implemented"},
    ],
}


def default_review_hints(markers: list[Multikill]) -> list[dict[str, Any]]:
    """Turn existing round-wide markers into transparent, non-verdict review hints."""
    criterion = DEFAULT_PROFILE["criteria"][0]
    return [{
        "id": f"round-multikill-r{marker.round_number}-{marker.player}-{marker.first_tick}",
        "category": "review_scene",
        "criterion_id": criterion["id"],
        "criterion_label": criterion["label"],
        "threshold": criterion["threshold"],
        "observed_facts": {
            "round_number": marker.round_number, "player": marker.player,
            "kill_count": marker.kill_count, "first_tick": marker.first_tick,
            "last_tick": marker.last_tick, "victims": marker.victims,
        },
        "message": f"{marker.player}: {marker.kill_count} Kills in Runde {marker.round_number}; im Spielkontext prüfen.",
        "verdict": "review_hint",
    } for marker in markers]


def profile_capabilities(available_channels: list[str], missing_channels: list[str]) -> list[dict[str, Any]]:
    """Describe, without guessing, which profile rules can run on this demo."""
    available = set(available_channels)
    missing = set(missing_channels)
    capabilities: list[dict[str, Any]] = []
    for item in [*DEFAULT_PROFILE["criteria"], *DEFAULT_PROFILE["planned_families"]]:
        required = list(item["requires"])
        unavailable = [channel for channel in required if channel not in available]
        if item["status"] != "active":
            status = "not_implemented"
            message = "Für V1 noch nicht fachlich implementiert; es wird keine Schwelle oder Bewertung vorgetäuscht."
        elif unavailable:
            status = "not_assessable"
            message = f"Nicht bewertbar: benötigte Datenquelle(n) fehlen ({', '.join(unavailable)})."
        else:
            status = "assessable"
            message = "Mit den vorhandenen Datenquellen bewertbar."
        capabilities.append({
            "id": item["id"], "label": item["label"], "requires": required,
            "status": status, "message": message,
            "missing_sources": [channel for channel in unavailable if channel in missing or channel not in available],
        })
    return capabilities
