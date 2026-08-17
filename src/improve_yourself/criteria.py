from __future__ import annotations

from typing import Any

from .model import Multikill

DEFAULT_PROFILE = {
    "id": "iy.default_review",
    "version": "v1",
    "label": "Improve Default Review V1",
    "disclaimer": "Profilregeln markieren vorhandene Fakten zur menschlichen Prüfung und sind kein Cheat-Nachweis.",
    "criteria": [{
        "id": "round_multikill", "label": "Rundenweiter Multi-Kill",
        "threshold": {"field": "kill_count", "operator": ">=", "value": 3},
        "requires": ["kills", "rounds"],
    }],
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
