"""V2 review presentation from canonical projections, without a second data source."""

from __future__ import annotations

from typing import Any

from .analyzer_data_hub import REVIEW_PROJECTION_V1_SCHEMA


REVIEW_PRESENTATION_V1_SCHEMA = "iy.review_presentation/v1"


def _system_check_view(payload: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(payload, dict) or payload.get("schema") != "iy.system_check/v1":
        return {"availability": "UNKNOWN / NOT AVAILABLE", "source": None, "results": (), "limits": ("Kein bestätigter read-only System Check geladen.",)}
    policy = payload.get("policy")
    checks = payload.get("checks")
    if not isinstance(policy, dict) or policy.get("read_only") is not True or policy.get("changes_applied") is not False or not isinstance(checks, list):
        return {"availability": "UNKNOWN / NOT AVAILABLE", "source": None, "results": (), "limits": ("System-Check-Evidenz ist nicht als read-only bestätigt.",)}
    results = tuple(
        {
            "label": item.get("label", "Unbenannte Prüfung"),
            "status": item.get("status", "REVIEW"),
            "summary": item.get("summary", "Nicht belegt."),
            "next_step": (item.get("user_view") or {}).get("action", "Keine automatische Änderung wurde vorgenommen.") if isinstance(item.get("user_view"), dict) else "Keine automatische Änderung wurde vorgenommen.",
        }
        for item in checks if isinstance(item, dict)
    )
    return {"availability": "AVAILABLE / READ-ONLY", "source": "iy.system_check/v1", "results": results, "limits": ()}


def build_review_presentation(review_projection: dict[str, object], system_check: dict[str, object] | None = None) -> dict[str, object]:
    """Separate proven review facts from hints, limits, next steps and System Check.

    Only ``iy.review_projection/v1`` is accepted for analysis/replay context.
    System Check remains a sibling read-only source; optimizer, demo and replay
    payloads are neither accepted nor emitted.
    """
    if review_projection.get("schema") != REVIEW_PROJECTION_V1_SCHEMA:
        raise ValueError(f"expected {REVIEW_PROJECTION_V1_SCHEMA}")
    match = review_projection.get("match") if isinstance(review_projection.get("match"), dict) else {}
    rounds = review_projection.get("rounds") if isinstance(review_projection.get("rounds"), list) else []
    events = review_projection.get("events") if isinstance(review_projection.get("events"), dict) else {}
    kills = events.get("kills") if isinstance(events.get("kills"), list) else []
    unavailable = events.get("unavailable_channels") if isinstance(events.get("unavailable_channels"), list) else []
    limits = tuple(f"{channel}: UNKNOWN / NOT AVAILABLE" for channel in unavailable if isinstance(channel, str))
    return {
        "schema": REVIEW_PRESENTATION_V1_SCHEMA,
        "analysis": {
            "source": REVIEW_PROJECTION_V1_SCHEMA,
            "facts": (
                f"Map: {match.get('map_id', 'UNKNOWN / NOT AVAILABLE')}",
                f"Runden: {len(rounds)}",
                f"Belegte Kill-Ereignisse: {len(kills)}",
            ),
            "hints": ("Szenen sind Prüfhinweise und kein Cheat-Nachweis.",),
            "limits": limits or ("Keine zusätzlich gemeldete Datenlücke.",),
            "next_steps": ("Eine Szene auswählen und den belegten Tick im lokalen Review prüfen.",),
        },
        "system_check": _system_check_view(system_check),
    }
