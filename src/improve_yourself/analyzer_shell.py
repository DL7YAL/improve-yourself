from __future__ import annotations

import argparse
from collections import Counter
import ctypes
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable

from .analysis_flow import AnalysisProfile
from .analysis_library import LocalAnalysisLibrary
from .cs2_review_coordinator import Cs2ReviewCoordinator, ReviewCoordinatorServer, ReviewPreflight
from .demo_workflow import ensure_tactical_replay_export, preflight_demo_workflow, rerender_demo_workflow
from .analyzer_data_hub import AnalyzerDataHub
from .embedded_review import EmbeddedReviewSession
from .embedded_tactical import EmbeddedTacticalSession
from .local_profiles import OBJECTIVE_RULES, LocalProfileStore
from .optimizer_evidence import evaluate_profile, profile_from_system_check
from .optimizer_foundation import OptimizationRule, integration_proof
from .replay_store import ReplayStore
from .review_presentation import build_review_presentation
from .rule_pack import RulePackValidationError, import_rule_pack, load_rule_pack_document
from .system_check import run_system_check


_SOURCE_HASH = re.compile(r"[0-9a-f]{64}")
_BASE_ARTIFACTS = ("analysis", "replay_v2", "improve_match_data", "validation_report")
_REVIEW_ARTIFACTS = (
    "analysis_flow", "timeline", "review", "cs2_review_commands"
)

UI_REFERENCE_STATUS = {
    "Dashboard": "IMPLEMENTED",
    "My Improvement": "IMPLEMENTED",
    "Analyzer": "IMPLEMENTED",
    "Reports": "IMPLEMENTED",
    "System Check / Optimizer": "IMPLEMENTED",
    "Settings": "IMPLEMENTED",
    "Tactical Replay": "IMPLEMENTED",
    "Benchmark": "IMPLEMENTED",
}

# The unified Analyzer is the only top-level analysis product area.  Demo
# selection, rules and review are internal tabs so they share one local replay
# truth instead of presenting separate product modules.
SIDEBAR_NAVIGATION = (
    "Dashboard",
    "Analyzer",
    "Tactical Replay",
    "My Improvement",
    "System Check / Optimizer",
    "Benchmark",
    "Reports",
    "Settings",
)

# The visible wording is intentionally product-facing while the existing
# internal page key remains stable.  This prevents a navigation-only release
# task from changing the established read-only System Check/Optimizer route.
_SIDEBAR_PRIMARY = SIDEBAR_NAVIGATION[:6]
_SIDEBAR_SECONDARY = SIDEBAR_NAVIGATION[6:]

_THEME = {
    # Final Home master calibration: near-black Navy surfaces lead. Blue is
    # reserved for wayfinding and intentional state, never the card ground.
    "night": "#020A12", "deep": "#0A1C2D", "panel": "#071725",
    "panel_high": "#0A1C2D", "panel_hover": "#0D2236", "card": "#0A1C2D", "sidebar": "#03101C",
    "border": "#0A2132", "border_soft": "#071A27", "border_active": "#1174AD",
    "metal": "#0B79C9", "cyan": "#13A7E8", "line": "#13A7E8", "line_soft": "#071A27",
    "accent": "#0B79C9", "accent_bright": "#13A7E8", "accent_strong": "#0B79C9",
    "ice": "#E4E8ED", "ink": "#E4E8ED", "secondary": "#A0ABB8",
    "muted": "#687789", "success": "#58d69a",
}

# Optimizer visual-fidelity tokens.  These are deliberately independent from
# the shared Home surface scale: this approved pilot needs the deeper metallic
# blue hierarchy, compact cyan edge-light and cooler text of the Optimizer
# reference without rolling a new, unreviewed treatment across other routes.
_OPTIMIZER_THEME = {
    "page": "#020A12",
    "surface": "#071827",
    "surface_raised": "#0A1D2E",
    "surface_hero": "#081B2B",
    "surface_detail": "#061521",
    "surface_input": "#04111C",
    "surface_hover": "#0B2639",
    "border": "#0A2538",
    "border_soft": "#061722",
    "border_bright": "#127EC0",
    "accent": "#159BE1",
    "accent_soft": "#0B4D73",
    "text": "#E8F0F5",
    "secondary": "#AAB9C5",
    "muted": "#728696",
    "success": "#6DBE6A",
    "warning": "#E5B854",
    "unknown": "#9AAAB6",
}

# The two approved Optimizer MASTER exports distinguish the four fixed product
# areas with these compact icon/status accents. They are presentation-only;
# recommendation state remains sourced from the existing evidence model.
_OPTIMIZER_DOMAIN_ACCENTS = {
    "SYSTEM_OPTIMIZER": "#159BE1",
    "GRAPHICS_OPTIMIZER": "#22C55E",
    "NETWORK_OPTIMIZER": "#B36CFF",
    "BIOS_OPTIMIZER": "#F59E0B",
}

_UI_FONT = "Inter"
_DISPLAY_FONT = "Orbitron"
_PRIVATE_FONT_FLAG = 0x10
_SYSTEM_SCAN_HOME_FIELDS = ("cpu", "gpu", "memory", "windows", "drivers", "display")
_MATRIX_PACK_01_RELATIVE_PATH = Path("config") / "rule-packs" / "improve-matrix-pack-01.json"

_STATUS_PRESENTATION = {
    "OK": ("READY / OK", "ready"),
    "NO_CHANGE": ("EVIDENCE / NO CHANGE", "evidence"),
    "ALREADY_RECOMMENDED": ("READY / ALREADY MATCHED", "ready"),
    "RECOMMENDED": ("READY / REVIEW", "ready"),
    "REVIEW": ("CONDITIONAL / CHECK", "conditional"),
    "CONDITIONAL": ("CONDITIONAL", "conditional"),
    "ACTION_REQUIRED": ("WARNING / ACTION REQUIRED", "warning"),
    "INSUFFICIENT_EVIDENCE": ("UNKNOWN / NOT AVAILABLE", "unknown"),
    "UNKNOWN": ("UNKNOWN / NOT AVAILABLE", "unknown"),
    "EXCLUSION": ("UNSUPPORTED / EXCLUDED", "unknown"),
}


def matrix_pack_01_rules() -> tuple[OptimizationRule, ...]:
    """Load the bundled, fail-closed Pack 01 without adding a second rule path."""
    resource_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return import_rule_pack(load_rule_pack_document(resource_root / _MATRIX_PACK_01_RELATIVE_PATH))


def status_presentation(status: object) -> tuple[str, str]:
    """Return one stable label and semantic class for an existing status.

    Presentation never changes a finding. In particular, an absent or unknown
    state stays unknown instead of being styled like a ready result.
    """
    return _STATUS_PRESENTATION.get(str(status), _STATUS_PRESENTATION["UNKNOWN"])


def analysis_profile_criteria_view(profile: AnalysisProfile) -> dict[str, object]:
    """Expose the selected profile's real criterion count through one semantic hook."""
    enabled = tuple(profile.enabled_rule_ids or OBJECTIVE_RULES)
    return {
        "profile_id": profile.profile_id,
        "active": len(enabled),
        "available": len(OBJECTIVE_RULES),
        "text": f"Aktive Kriterien: {len(enabled)} / {len(OBJECTIVE_RULES)}",
    }


def optimizer_domain_overview(view: dict[str, object] | None = None) -> tuple[dict[str, str], ...]:
    """Return the four fixed Optimizer areas without manufacturing capabilities."""
    definitions = (
        ("SYSTEM_OPTIMIZER", "System Optimizer", "System Check und read-only Bewertung"),
        ("GRAPHICS_OPTIMIZER", "Graphics Optimizer", "Darstellungs- und Treiberfakten einordnen"),
        ("NETWORK_OPTIMIZER", "Network Optimizer", "Beobachtete Qualität von Konfiguration trennen"),
        ("BIOS_OPTIMIZER", "BIOS Optimizer", "Nur manuelle Guidance; kein Apply"),
    )
    domains = view.get("domains", {}) if isinstance(view, dict) else {}
    result = []
    for domain, title, description in definitions:
        models = domains.get(domain, []) if isinstance(domains, dict) else []
        if not isinstance(models, list) or not models:
            state = "PREVIEW · noch keine bestätigte lokale Bewertung"
        else:
            statuses = [str(model.get("status")) for model in models if isinstance(model, dict)]
            conditional = sum(status in {"CONDITIONAL", "INSUFFICIENT_EVIDENCE", "UNKNOWN"} for status in statuses)
            state = f"{len(statuses)} Prüfpunkte · {conditional} bedingt oder unbekannt"
        result.append({"domain": domain, "title": title, "description": description, "state": state})
    return tuple(result)


def optimizer_visible_models(
    view: dict[str, object] | None,
    domain: str,
    *,
    query: str = "",
    status_filter: str = "Alle Status",
) -> tuple[dict[str, object], ...]:
    """Return display rows for one Optimizer area without changing a result.

    The function is deliberately a presentation-only filter.  It keeps the
    existing recommendation objects intact, never fills missing information,
    and gives the native reference-locked table one deterministic source.
    """
    domains = view.get("domains") if isinstance(view, dict) else None
    candidates = domains.get(domain, []) if isinstance(domains, dict) else []
    if not isinstance(candidates, list):
        return ()
    normalized_query = query.strip().casefold()
    normalized_status = status_filter.strip().upper()
    visible: list[dict[str, object]] = []
    for model in candidates:
        if not isinstance(model, dict):
            continue
        status = str(model.get("status") or "UNKNOWN")
        if normalized_status not in {"", "ALLE STATUS"} and status != normalized_status:
            continue
        haystack = " ".join(
            str(model.get(field) or "")
            for field in ("title", "current_state", "improve_recommendation", "why_for_this_system")
        ).casefold()
        if normalized_query and normalized_query not in haystack:
            continue
        visible.append(model)
    return tuple(visible)


def optimizer_table_cell(value: object, *, maximum: int = 27) -> str:
    """Condense a real value for a narrow table cell without changing truth.

    Full values remain in the right detail panel.  The table uses this only to
    preserve scanability at the approved two-column/detail-panel proportions.
    """
    raw = str(value or "Nicht verfügbar")
    semantic_shortcuts = {
        "READ_ONLY_FACTS_AVAILABLE": "Fakten verfügbar",
        "NO_AUTOMATIC_IMPROVE_RECOMMENDATION": "Keine Empfehlung",
        "EVIDENCE / NO CHANGE": "Keine Änderung",
        "UNKNOWN / NOT AVAILABLE": "Unbekannt",
        "READY / ALREADY MATCHED": "Bereits passend",
        "READY / REVIEW": "Prüfen",
    }
    if raw in semantic_shortcuts:
        return semantic_shortcuts[raw]
    if raw.startswith("READ-ONLY FACTS AVAILABLE"):
        return "Fakten verfügbar"
    if raw.startswith("NO AUTOMATIC IMPROVE RECOMMENDATION"):
        return "Keine Empfehlung"
    text = raw.replace("_", " ").replace("FIXTURE ONLY", "Fixture")
    text = " ".join(text.split())
    return text if len(text) <= maximum else text[: maximum - 1].rstrip() + "…"


def optimizer_user_detail_sections(model: dict[str, object] | None) -> dict[str, str]:
    """Translate an existing result into the reference detail-panel language.

    This is intentionally a presentation adapter: it never derives a setting,
    fills a gap, or changes a recommendation.  Raw provenance remains behind
    the existing technical-details control.
    """
    if model is None:
        return {
            "state": "Keine Einstellung ausgewählt",
            "what": "Wähle eine Zeile, um vorhandene lokale Fakten, die Bewertung und ihre Grenzen zu sehen.",
            "why": "Für den gewählten Filter liegt keine bestätigte Einstellung vor.",
            "effect": "Keine Wirkung wird behauptet.",
            "evidence": "Nicht verfügbar.",
            "change": "Read-only · es wird keine Änderung ausgeführt.",
        }
    status = str(model.get("status") or "UNKNOWN")
    state = optimizer_table_cell(model.get("current_state"), maximum=56)
    if status == "INSUFFICIENT_EVIDENCE":
        why = "Die vorhandene Evidenz reicht für eine sichere Improve-Empfehlung nicht aus. Fehlende Werte bleiben unbekannt."
    elif status in {"CONDITIONAL", "UNKNOWN", "EXCLUSION"}:
        why = "Die vorhandenen Fakten erlauben nur eine bedingte oder ausgeschlossene Einordnung; daraus entsteht keine positive Empfehlung."
    elif status == "ALREADY_RECOMMENDED":
        why = "Der bestätigte aktuelle Zustand entspricht der vorhandenen Improve-Empfehlung."
    elif status == "RECOMMENDED":
        why = "Die vorhandenen lokalen Fakten erfüllen die Datenbedingungen dieser read-only Bewertung."
    else:
        why = "Für diese Einstellung liegt keine automatische Improve-Empfehlung vor."
    validity = model.get("evidence_validity")
    evidence = (
        "Vorhandene Evidenzdaten · technische Details verfügbar."
        if isinstance(validity, (dict, list, tuple))
        else optimizer_table_cell(validity, maximum=76)
    )
    return {
        "state": state,
        "what": "Diese Ansicht ordnet die vorhandene lokale System-Check-Evidenz ein. Sie ändert keine Einstellungen.",
        "why": why,
        "effect": str(model.get("what_can_change") or "Keine Wirkung wird behauptet."),
        "evidence": evidence,
        "change": "Read-only · keine Änderung angewendet; Wiederherstellung ist nicht erforderlich.",
    }


def system_scan_home_view(payload: dict[str, object]) -> dict[str, object] | None:
    """Project an existing read-only system scan into six honest Home cells.

    The function deliberately consumes the existing `iy.system_check/v1`
    payload.  It neither probes the machine nor infers missing facts.
    """
    if payload.get("schema") != "iy.system_check/v1":
        return None
    raw_checks = payload.get("checks")
    if not isinstance(raw_checks, list):
        return None
    checks = {item.get("id"): item for item in raw_checks if isinstance(item, dict) and isinstance(item.get("id"), str)}

    def check_value(check_id: str, fallback: str = "Nicht verfügbar") -> tuple[dict[str, object], str, str]:
        check = checks.get(check_id)
        if not isinstance(check, dict):
            return {}, fallback, "REVIEW"
        evidence = check.get("evidence")
        return evidence if isinstance(evidence, dict) else {}, str(check.get("summary") or fallback), str(check.get("status") or "REVIEW")

    cpu_evidence, cpu_fallback, cpu_status = check_value("cpu")
    gpu_evidence, gpu_fallback, gpu_status = check_value("gpu")
    memory_evidence, memory_fallback, memory_status = check_value("memory")
    windows_evidence, windows_fallback, windows_status = check_value("windows")
    display_evidence, display_fallback, display_status = check_value("display")
    adapters = gpu_evidence.get("adapters")
    first_adapter = adapters[0] if isinstance(adapters, list) and adapters and isinstance(adapters[0], dict) else {}
    ram_gb = memory_evidence.get("total_gb")
    active_displays = display_evidence.get("active_displays")
    refresh_rates = [
        display.get("refresh_hz")
        for display in active_displays
        if isinstance(display, dict) and isinstance(display.get("refresh_hz"), (int, float))
    ] if isinstance(active_displays, list) else []
    if not refresh_rates:
        legacy_refresh = display_evidence.get("refresh_rates_hz")
        refresh_rates = [rate for rate in legacy_refresh if isinstance(rate, (int, float))] if isinstance(legacy_refresh, list) else []
    entries = {
        "cpu": ("CPU", str(cpu_evidence.get("name") or cpu_fallback), cpu_status),
        "gpu": ("GPU", str(first_adapter.get("name") or gpu_fallback), gpu_status),
        "memory": ("RAM", f"{ram_gb:g} GB" if isinstance(ram_gb, (int, float)) else memory_fallback, memory_status),
        "windows": ("Windows", str(windows_evidence.get("caption") or windows_evidence.get("build") or windows_fallback), windows_status),
        "drivers": ("Treiber", str(first_adapter.get("driver_version") or gpu_fallback), gpu_status),
        "display": ("Monitor", f"{max(refresh_rates):g} Hz" if refresh_rates else display_fallback, display_status),
    }
    summary = payload.get("summary")
    counts = summary if isinstance(summary, dict) else {}
    attention = [label for label, _value, status in entries.values() if status != "OK"]
    return {
        "generated_at_utc": str(payload.get("generated_at_utc") or "Zeitpunkt nicht verfügbar"),
        "overall": f"{counts.get('OK', 0)} OK · {counts.get('REVIEW', 0)} zu prüfen · {counts.get('ACTION_REQUIRED', 0)} Handlungsbedarf",
        "attention": "Hinweise: " + ", ".join(attention) if attention else "Keine offenen Hinweise aus dem letzten Scan.",
        "entries": entries,
    }


def _system_evidence_text(value: object) -> str:
    """Format persisted read-only evidence without inferring missing facts."""
    if value is None:
        return "nicht sicher ermittelt"
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, (str, int, float)):
        return str(value).strip() or "nicht verfügbar"
    if isinstance(value, list):
        rendered = [_system_evidence_text(item) for item in value]
        return " · ".join(item for item in rendered if item) or "nicht verfügbar"
    if isinstance(value, dict):
        rendered = [
            f"{key}: {_system_evidence_text(item)}"
            for key, item in value.items()
            if _system_evidence_text(item) != "nicht verfügbar"
        ]
        return " · ".join(rendered) or "nicht verfügbar"
    return "nicht verfügbar"


def system_check_result_view(payload: dict[str, object]) -> dict[str, object] | None:
    """Turn an existing `iy.system_check/v1` document into display-only rows.

    It intentionally presents the persisted summary, status and evidence as
    separate fields. The view neither reevaluates the device nor turns an
    unknown check into an actionable recommendation.
    """
    if payload.get("schema") != "iy.system_check/v1":
        return None
    summary = payload.get("summary")
    checks = payload.get("checks")
    policy = payload.get("policy")
    if not isinstance(summary, dict) or not isinstance(checks, list) or not isinstance(policy, dict):
        return None
    rows: list[dict[str, str]] = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        label = check.get("label")
        status = check.get("status")
        description = check.get("summary")
        evidence = check.get("evidence")
        if not all(isinstance(value, str) and value for value in (label, status, description)):
            continue
        rows.append({
            "label": label,
            "status": status if status in {"OK", "REVIEW", "ACTION_REQUIRED"} else "UNKNOWN",
            "summary": description,
            "evidence": _system_evidence_text(evidence if isinstance(evidence, dict) else None),
        })
    if not rows:
        return None
    return {
        "generated_at_utc": str(payload.get("generated_at_utc") or "Zeitpunkt nicht verfügbar"),
        "summary": {
            "OK": str(summary.get("OK", 0)),
            "REVIEW": str(summary.get("REVIEW", 0)),
            "ACTION_REQUIRED": str(summary.get("ACTION_REQUIRED", 0)),
        },
        "policy": (
            "Read-only · keine Änderungen angewendet"
            if policy.get("read_only") is True and policy.get("changes_applied") is False
            else "Ausführungsrichtlinie konnte nicht vollständig bestätigt werden"
        ),
        "rows": rows,
    }


def optimizer_evidence_view(payload: dict[str, object]) -> dict[str, object] | None:
    """Present read-only selection evidence; it deliberately exposes no apply action."""
    profile = profile_from_system_check(payload)
    if profile is None:
        return None
    report = evaluate_profile(profile)
    groups = (
        ("VERIFIED / STABLE", report["stable_recommendations"]),
        ("CONDITIONAL", report["conditional_recommendations"]),
        ("EXPERIMENTAL", report["experimental_candidates"]),
    )
    rows: list[dict[str, str]] = []
    for evidence_class, rules in groups:
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            rows.append({
                "evidence_class": evidence_class,
                "name": str(rule.get("name") or "Unbenannter Kandidat"),
                "effect": str(rule.get("expected_effect") or "Keine Wirkung behauptet."),
                "risk": _system_evidence_text(rule.get("possible_side_effects")),
                "restore": str(rule.get("backup_restore_requirement") or "Snapshot und Restore erforderlich."),
            })
    return {
        "profile_source": str(report["profile_source"]),
        "performance_evidence": str(report["performance_evidence"]),
        "rows": rows,
        "missing_input_data": [str(item) for item in report["missing_input_data"]],
        "excluded_rules": [item for item in report["excluded_rules"] if isinstance(item, dict)],
    }


def optimizer_product_view(profile: dict[str, object], *, internal_test: bool = False, rules: tuple[OptimizationRule, ...] | None = None) -> dict[str, object]:
    """Common read-only Optimizer product/UI contract for real or synthetic profiles."""
    proof = integration_proof(profile, (), rules=rules)
    models = proof["view_models"]
    domains: dict[str, list[dict[str, object]]] = {}
    counts = {"checked": len(models), "recommended": 0, "already": 0, "conditional": 0, "manual_bios": 0, "insufficient": 0, "tradeoffs": 0}
    for model in models:
        domain = str(model["domain"])
        domains.setdefault(domain, []).append(model)
        status = str(model["status"])
        counts["recommended"] += status == "RECOMMENDED"
        counts["already"] += status == "ALREADY_RECOMMENDED"
        counts["conditional"] += status == "CONDITIONAL"
        counts["insufficient"] += status == "INSUFFICIENT_EVIDENCE"
        counts["manual_bios"] += bool(model["guidance"]["manual_action_required"])
        counts["tradeoffs"] += model["risk_notes"] == "HIGH" and "Trade-off" in str(model["title"])
    return {"read_only": True, "internal_test": internal_test, "fixture_only": bool(models) and all(bool(model["improve_recommendation"].startswith("FIXTURE_ONLY")) for model in models), "counts": counts, "domains": domains, "models": models}


def _register_private_fonts(root, assets: Path) -> tuple[str, str]:
    """Register the packaged V1 font files for this process only.

    The portable build must not depend on a machine-wide font installation.
    Windows keeps FR_PRIVATE registrations local to the running application;
    other platforms retain their safe system sans fallback.
    """
    if os.name != "nt" or not hasattr(ctypes, "windll"):
        return "Segoe UI", "Segoe UI"
    add_font = ctypes.windll.gdi32.AddFontResourceExW
    for filename in ("Inter-Variable.ttf", "Orbitron-Variable.ttf"):
        font_path = assets / "fonts" / filename
        if font_path.is_file():
            add_font(str(font_path), _PRIVATE_FONT_FLAG, None)
    families = set(root.tk.call("font", "families"))
    return (
        _UI_FONT if _UI_FONT in families else "Segoe UI",
        _DISPLAY_FONT if _DISPLAY_FONT in families else "Segoe UI",
    )


class SidebarNavItem:
    """One reusable, rounded navigation surface for the Midnight shell.

    ttk's native button element remains visibly rectangular even with the
    custom theme.  A small canvas component gives the sidebar a single,
    controlled active/hover treatment without changing any page routing.
    """

    def __init__(self, tk, parent, *, text: str, ui_font: str, command: Callable[[], None]) -> None:
        self.tk = tk
        self.text = text
        self.ui_font = ui_font
        self.command = command
        self.active = False
        self.hovered = False
        self.canvas = tk.Canvas(
            parent, height=54, background=_THEME["sidebar"], highlightthickness=0,
            borderwidth=0, bd=0, takefocus=True,
        )
        self.canvas.bind("<Configure>", self._draw)
        for target in (self.canvas,):
            target.bind("<Enter>", self._enter)
            target.bind("<Leave>", self._leave)
            target.bind("<Button-1>", self._activate)
            target.bind("<Return>", self._activate)
            target.bind("<space>", self._activate)

    def pack(self, **kwargs) -> None:
        self.canvas.pack(**kwargs)

    def set_active(self, active: bool) -> None:
        self.active = active
        self._draw()

    def _enter(self, _event=None) -> None:
        self.hovered = True
        self._draw()

    def _leave(self, _event=None) -> None:
        self.hovered = False
        self._draw()

    def _activate(self, _event=None) -> None:
        self.command()

    def _rounded_rect(self, x1: int, y1: int, x2: int, y2: int, radius: int, *, fill: str, outline: str = "") -> None:
        canvas = self.canvas
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline="")
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline="")
        for start in (90, 180, 270, 0):
            if start == 90:
                box = (x1, y1, x1 + 2 * radius, y1 + 2 * radius)
            elif start == 180:
                box = (x1, y2 - 2 * radius, x1 + 2 * radius, y2)
            elif start == 270:
                box = (x2 - 2 * radius, y2 - 2 * radius, x2, y2)
            else:
                box = (x2 - 2 * radius, y1, x2, y1 + 2 * radius)
            canvas.create_arc(*box, start=start, extent=90, fill=fill, outline=outline or fill)
        if outline:
            canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline)
            canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=outline)
            canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=outline)
            canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=outline)

    def _draw(self, _event=None) -> None:
        canvas = self.canvas
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        canvas.delete("all")
        if self.active:
            # A filled navigation surface plus a short leading accent is the
            # approved active state.  It deliberately replaces the earlier
            # technical cyan outline: the page stays recognisable at a glance
            # without looking like a focused developer control.
            self._rounded_rect(7, 6, width - 7, height - 6, 9, fill="#0A2638")
            self._rounded_rect(8, 14, 12, height - 14, 2, fill=_THEME["cyan"])
            icon_color, label_color = "#c4ecff", _THEME["ice"]
        elif self.hovered:
            self._rounded_rect(7, 6, width - 7, height - 6, 9, fill="#081E2D")
            icon_color, label_color = "#79c9ed", "#d7e1ea"
        else:
            icon_color, label_color = "#5f8eaa", _THEME["muted"]
        icon, label = self.text[:1], self.text[1:].strip()
        canvas.create_text(30, height // 2, text=icon, fill=icon_color, anchor="center", font=(self.ui_font, 13, "bold"))
        canvas.create_text(54, height // 2, text=label, fill=label_color, anchor="w", font=(self.ui_font, 10, "bold" if self.active else "normal"))


class SidebarStatusPanel:
    """Quiet, rounded local-status surface that matches the navigation."""

    def __init__(self, tk, parent, *, ui_font: str) -> None:
        self.tk = tk
        self.ui_font = ui_font
        self.canvas = tk.Canvas(parent, height=63, background=_THEME["sidebar"], highlightthickness=0, borderwidth=0, bd=0)
        self.canvas.bind("<Configure>", self._draw)

    def pack(self, **kwargs) -> None:
        self.canvas.pack(**kwargs)

    def _draw(self, _event=None) -> None:
        canvas = self.canvas
        width, height = max(canvas.winfo_width(), 1), max(canvas.winfo_height(), 1)
        canvas.delete("all")
        radius = 9
        canvas.create_rectangle(8 + radius, 4, width - 8 - radius, height - 4, fill="#04131F", outline="")
        canvas.create_rectangle(8, 4 + radius, width - 8, height - 4 - radius, fill="#04131F", outline="")
        for box, start in (((8, 4, 8 + 2 * radius, 4 + 2 * radius), 90), ((8, height - 4 - 2 * radius, 8 + 2 * radius, height - 4), 180), ((width - 8 - 2 * radius, height - 4 - 2 * radius, width - 8, height - 4), 270), ((width - 8 - 2 * radius, 4, width - 8, 4 + 2 * radius), 0)):
            canvas.create_arc(*box, start=start, extent=90, fill="#04131F", outline=_THEME["border_soft"])
        canvas.create_line(8 + radius, 4, width - 8 - radius, 4, fill=_THEME["border_soft"])
        canvas.create_text(19, 20, text="●", fill="#2bdcbb", anchor="center", font=(self.ui_font, 9, "bold"))
        canvas.create_text(31, 18, text="LOCAL / PRIVATE", fill=_THEME["secondary"], anchor="w", font=(self.ui_font, 8, "bold"))
        canvas.create_text(19, 39, text="READ-ONLY WHERE MARKED", fill=_THEME["muted"], anchor="w", font=(self.ui_font, 7))


class RoundedHomeSurface:
    """Reusable rounded Home card chrome with an unchanged ttk content grid.

    The canvas owns only the visual perimeter; all existing labels, buttons
    and responsive grid rules live in ``body``.  This keeps Home's approved
    layout and action alignment intact while giving surfaces real rounded
    corners instead of relying on a rectangular ttk border.
    """

    def __init__(self, tk, ttk, parent, *, style: str, fill: str, outline: str, padding, min_height: int, min_width: int = 1, radius: int = 9) -> None:
        self.tk = tk
        self.radius = radius
        self.fill = fill
        self.outline = outline
        self.canvas = tk.Canvas(parent, width=min_width, height=min_height, background=_THEME["night"], highlightthickness=0, borderwidth=0, bd=0)
        self.body = ttk.Frame(self.canvas, style=style, padding=padding)
        self.window = self.canvas.create_window((radius, 0), window=self.body, anchor="nw")
        self.canvas.bind("<Configure>", self._sync)

    def pack(self, **kwargs) -> None:
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.canvas.grid(**kwargs)

    def grid_configure(self, **kwargs) -> None:
        self.canvas.grid_configure(**kwargs)

    def columnconfigure(self, index: int, **kwargs) -> None:
        self.body.columnconfigure(index, **kwargs)

    def rowconfigure(self, index: int, **kwargs) -> None:
        self.body.rowconfigure(index, **kwargs)

    def _sync(self, _event=None) -> None:
        width, height = max(self.canvas.winfo_width(), 1), max(self.canvas.winfo_height(), 1)
        self.canvas.itemconfigure(self.window, width=max(1, width - 2 * self.radius), height=height)
        self.canvas.delete("surface")
        x1, y1, x2, y2, radius = 0, 0, width - 1, height - 1, self.radius
        # Fill the center and sides first, then four arcs.  The canvas itself
        # stays on the midnight page color, so the uncovered corners are real.
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=self.fill, outline="", tags="surface")
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=self.fill, outline="", tags="surface")
        for box, start in (((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 90), ((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 180), ((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 270), ((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 0)):
            self.canvas.create_arc(*box, start=start, extent=90, fill=self.fill, outline=self.outline, tags="surface")
        self.canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=self.outline, tags="surface")
        self.canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=self.outline, tags="surface")
        self.canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=self.outline, tags="surface")
        self.canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=self.outline, tags="surface")
        self.canvas.tag_lower("surface")


class RoundedHomeAction:
    """A shared, restrained module action for the six approved Home cards.

    Native ttk buttons cannot render the rounded, low-fill Master treatment
    consistently on Windows.  This component changes only the Home action
    chrome; it forwards the existing command and keeps normal keyboard
    activation and disabled-state behaviour intact.
    """

    def __init__(self, tk, parent, *, text: str, accent: str, command: Callable[[], None], enabled: bool, font) -> None:
        self.tk = tk
        self.text = text
        self.accent = accent
        self.command = command
        self.enabled = enabled
        self.font = font
        self.hovered = False
        self.radius = 7
        self.canvas = tk.Canvas(
            parent, height=37, background=_THEME["panel"], highlightthickness=0,
            borderwidth=0, bd=0, takefocus=1 if enabled else 0,
        )
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Enter>", self._enter)
        self.canvas.bind("<Leave>", self._leave)
        self.canvas.bind("<ButtonRelease-1>", self._activate)
        self.canvas.bind("<Return>", self._activate)
        self.canvas.bind("<space>", self._activate)

    def grid(self, **kwargs) -> None:
        self.canvas.grid(**kwargs)

    def pack(self, **kwargs) -> None:
        self.canvas.pack(**kwargs)

    def _enter(self, _event=None) -> None:
        if self.enabled:
            self.hovered = True
            self._draw()

    def _leave(self, _event=None) -> None:
        self.hovered = False
        self._draw()

    def _activate(self, _event=None) -> str | None:
        if not self.enabled:
            return "break"
        self.command()
        return "break"

    def _draw(self, _event=None) -> None:
        width, height = max(self.canvas.winfo_width(), 1), max(self.canvas.winfo_height(), 1)
        radius = min(self.radius, max(1, height // 2 - 1), max(1, width // 2 - 1))
        fill = _THEME["panel_hover"] if self.hovered and self.enabled else _THEME["panel_high"]
        outline = self.accent if self.enabled else _THEME["border_soft"]
        foreground = _THEME["ice"] if self.enabled else _THEME["muted"]
        self.canvas.delete("action")
        self.canvas.create_rectangle(radius, 1, width - radius - 1, height - 2, fill=fill, outline="", tags="action")
        self.canvas.create_rectangle(1, radius, width - 2, height - radius - 1, fill=fill, outline="", tags="action")
        for box, start in (
            ((1, 1, 1 + 2 * radius, 1 + 2 * radius), 90),
            ((1, height - 2 - 2 * radius, 1 + 2 * radius, height - 2), 180),
            ((width - 2 - 2 * radius, height - 2 - 2 * radius, width - 2, height - 2), 270),
            ((width - 2 - 2 * radius, 1, width - 2, 1 + 2 * radius), 0),
        ):
            self.canvas.create_arc(*box, start=start, extent=90, fill=fill, outline=outline, tags="action")
        self.canvas.create_line(1 + radius, 1, width - 2 - radius, 1, fill=outline, tags="action")
        self.canvas.create_line(1 + radius, height - 2, width - 2 - radius, height - 2, fill=outline, tags="action")
        self.canvas.create_line(1, 1 + radius, 1, height - 2 - radius, fill=outline, tags="action")
        self.canvas.create_line(width - 2, 1 + radius, width - 2, height - 2 - radius, fill=outline, tags="action")
        self.canvas.create_text(width // 2, height // 2, text=self.text, fill=foreground, font=self.font, tags="action")


class RoundedOptimizerSurface(RoundedHomeSurface):
    """Optimizer-only metallic card perimeter over the existing Tk content.

    The body continues to host the existing labels, result adapters and table.
    This class owns only the rounded dark surface and restrained blue contour,
    so visual fidelity does not change application behaviour or data flow.
    """

    def __init__(self, tk, ttk, parent, *, style: str, fill: str, padding, min_height: int, min_width: int = 1, radius: int = 12) -> None:
        super().__init__(
            tk, ttk, parent, style=style, fill=fill,
            outline=_OPTIMIZER_THEME["border"], padding=padding,
            min_height=min_height, min_width=min_width, radius=radius,
        )


class RoundedOptimizerAction:
    """Low-fill outlined action used only by the reference-locked Optimizer.

    Tk buttons otherwise retain a platform rectangle even under the dark theme.
    The canvas forwards the same callback and keyboard activation while keeping
    the reference's dark interior, cyan contour and compact rounded form.
    """

    def __init__(self, tk, parent, *, text: str, command: Callable[[], None], primary: bool = False, enabled: bool = True, font=None) -> None:
        self.tk = tk
        self.text = text
        self.command = command
        self.primary = primary
        self.enabled = enabled
        self.font = font
        self.hovered = False
        self.canvas = tk.Canvas(
            parent, height=38, background=_OPTIMIZER_THEME["surface"],
            highlightthickness=0, borderwidth=0, bd=0, takefocus=1 if enabled else 0,
        )
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Enter>", self._enter)
        self.canvas.bind("<Leave>", self._leave)
        self.canvas.bind("<ButtonRelease-1>", self._activate)
        self.canvas.bind("<Return>", self._activate)
        self.canvas.bind("<space>", self._activate)

    def pack(self, **kwargs) -> None:
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.canvas.grid(**kwargs)

    def _enter(self, _event=None) -> None:
        if self.enabled:
            self.hovered = True
            self._draw()

    def _leave(self, _event=None) -> None:
        self.hovered = False
        self._draw()

    def _activate(self, _event=None) -> str | None:
        if not self.enabled:
            return "break"
        self.command()
        return "break"

    def _rounded_rect(self, width: int, height: int, *, fill: str, outline: str) -> None:
        radius = min(8, max(1, height // 2 - 1), max(1, width // 2 - 1))
        canvas = self.canvas
        canvas.create_rectangle(radius, 1, width - radius - 1, height - 2, fill=fill, outline="", tags="action")
        canvas.create_rectangle(1, radius, width - 2, height - radius - 1, fill=fill, outline="", tags="action")
        for box, start in (
            ((1, 1, 1 + 2 * radius, 1 + 2 * radius), 90),
            ((1, height - 2 - 2 * radius, 1 + 2 * radius, height - 2), 180),
            ((width - 2 - 2 * radius, height - 2 - 2 * radius, width - 2, height - 2), 270),
            ((width - 2 - 2 * radius, 1, width - 2, 1 + 2 * radius), 0),
        ):
            canvas.create_arc(*box, start=start, extent=90, fill=fill, outline=outline, tags="action")
        canvas.create_line(1 + radius, 1, width - 2 - radius, 1, fill=outline, tags="action")
        canvas.create_line(1 + radius, height - 2, width - 2 - radius, height - 2, fill=outline, tags="action")
        canvas.create_line(1, 1 + radius, 1, height - 2 - radius, fill=outline, tags="action")
        canvas.create_line(width - 2, 1 + radius, width - 2, height - 2 - radius, fill=outline, tags="action")

    def _draw(self, _event=None) -> None:
        width, height = max(self.canvas.winfo_width(), 1), max(self.canvas.winfo_height(), 1)
        if not self.enabled:
            fill, outline, foreground = _OPTIMIZER_THEME["surface_input"], _OPTIMIZER_THEME["border_soft"], _OPTIMIZER_THEME["muted"]
        elif self.primary:
            fill = "#0A3150" if self.hovered else "#082B46"
            outline, foreground = _OPTIMIZER_THEME["accent"], _OPTIMIZER_THEME["text"]
        else:
            fill = _OPTIMIZER_THEME["surface_hover"] if self.hovered else _OPTIMIZER_THEME["surface_raised"]
            outline = _OPTIMIZER_THEME["border_bright"] if self.hovered else _OPTIMIZER_THEME["border"]
            foreground = _OPTIMIZER_THEME["text"]
        self.canvas.delete("action")
        self._rounded_rect(width, height, fill=fill, outline=outline)
        self.canvas.create_text(width // 2, height // 2, text=self.text, fill=foreground, font=self.font, tags="action")


class OptimizerHardwareChip:
    """A compact two-line hardware chip with a reference-style blue contour."""

    def __init__(self, tk, parent, *, label: str, value: str, ui_font: str) -> None:
        self.tk = tk
        self.label = label
        self.value = value
        self.ui_font = ui_font
        self.canvas = tk.Canvas(parent, width=112, height=48, background=_THEME["night"], highlightthickness=0, borderwidth=0, bd=0)
        self.canvas.bind("<Configure>", self._draw)

    def pack(self, **kwargs) -> None:
        self.canvas.pack(**kwargs)

    def _draw(self, _event=None) -> None:
        canvas = self.canvas
        width, height = max(canvas.winfo_width(), 1), max(canvas.winfo_height(), 1)
        canvas.delete("all")
        radius = 8
        fill, outline = _OPTIMIZER_THEME["surface_raised"], _OPTIMIZER_THEME["border_soft"]
        canvas.create_rectangle(radius, 1, width - radius - 1, height - 2, fill=fill, outline="")
        canvas.create_rectangle(1, radius, width - 2, height - radius - 1, fill=fill, outline="")
        for box, start in (((1, 1, 1 + 2 * radius, 1 + 2 * radius), 90), ((1, height - 2 - 2 * radius, 1 + 2 * radius, height - 2), 180), ((width - 2 - 2 * radius, height - 2 - 2 * radius, width - 2, height - 2), 270), ((width - 2 - 2 * radius, 1, width - 2, 1 + 2 * radius), 0)):
            canvas.create_arc(*box, start=start, extent=90, fill=fill, outline=outline)
        canvas.create_line(radius, 1, width - radius - 1, 1, fill=outline)
        canvas.create_line(radius, height - 2, width - radius - 1, height - 2, fill=outline)
        canvas.create_text(10, 13, text=self.label, fill=_OPTIMIZER_THEME["muted"], anchor="w", font=(self.ui_font, 6, "bold"))
        canvas.create_text(10, 30, text=self.value, fill=_OPTIMIZER_THEME["text"], anchor="w", width=max(1, width - 20), font=(self.ui_font, 7, "bold"))


def dashboard_layout_metrics(content_width: int, viewport_height: int) -> tuple[bool, int, int, int, int]:
    """Return responsive Home metrics without scaling the whole interface."""
    compact = content_width < 1000
    extra_height = max(0, min(300, viewport_height - 650))
    return (
        compact,
        196 + extra_height // 12,
        214 + extra_height // 3,
        86 + extra_height // 4,
        12 + extra_height // 20,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def default_output_root() -> Path:
    """Use a stable user-writable root in packaged Windows builds."""
    if getattr(sys, "frozen", False) and os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Improve Yourself" / "Experimental" / "results"
    return Path("results/analyzer-shell")


def _enable_dark_titlebar(root) -> None:
    if not hasattr(ctypes, "windll"):
        return
    root.update_idletasks()
    enabled = ctypes.c_int(1)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        ctypes.windll.user32.GetParent(root.winfo_id()), 20, ctypes.byref(enabled), ctypes.sizeof(enabled)
    )


def validate_existing_workflow(manifest_path: Path) -> Path:
    """Fail-closed validation for an explicitly selected local workflow."""
    manifest_path = manifest_path.resolve()
    if manifest_path.name != "demo-workflow.json" or not manifest_path.is_file():
        raise ValueError("select an existing demo-workflow.json file")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != "iy.demo_workflow/v1":
        raise ValueError("expected iy.demo_workflow/v1 manifest")
    status = manifest.get("status")
    if status not in {"READY_FOR_SELECTION", "READY_FOR_REVIEW"}:
        raise ValueError("workflow is not READY_FOR_SELECTION or READY_FOR_REVIEW")
    source_hash = manifest.get("source_sha256")
    if not isinstance(source_hash, str) or _SOURCE_HASH.fullmatch(source_hash) is None:
        raise ValueError("source_sha256 must be 64 lowercase hexadecimal characters")
    policy = manifest.get("policy")
    if not isinstance(policy, dict) or policy.get("real_demo_required") is not True or policy.get("fake_results") is not False or policy.get("local_only") is not True:
        raise ValueError("workflow policy does not prove a local real-demo result")

    root = manifest_path.parent
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("workflow artifacts must be an object")
    resolved: dict[str, Path] = {}
    required = _BASE_ARTIFACTS + (_REVIEW_ARTIFACTS if status == "READY_FOR_REVIEW" else ())
    optional = tuple(name for name in ("tactical_replay", "report") if name in artifacts)
    for name in required + optional:
        relative = artifacts.get(name)
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"required artifact is missing: {name}")
        candidate = Path(relative)
        if candidate.is_absolute():
            raise ValueError(f"artifact must use a relative local path: {name}")
        path = (root / candidate).resolve()
        if root != path and root not in path.parents:
            raise ValueError(f"artifact escapes workflow root: {name}")
        if not path.is_file():
            raise ValueError(f"required artifact file is missing: {name}")
        resolved[name] = path

    analysis = json.loads(resolved["analysis"].read_text(encoding="utf-8"))
    if analysis.get("schema") != "iy.analysis/v1" or analysis.get("source_sha256") != source_hash:
        raise ValueError("analysis source metadata differs from workflow")
    store = ReplayStore(resolved["replay_v2"])
    if store.manifest["source"]["sha256"] != source_hash:
        raise ValueError("replay source metadata differs from workflow")
    loaded_chunks = [store.load_round(round_number) for round_number in store.round_numbers]
    match_data = json.loads(resolved["improve_match_data"].read_text(encoding="utf-8"))
    hub = AnalyzerDataHub(match_data)
    if hub.overview()["source"].get("sha256") != source_hash:
        raise ValueError("Improve Match Data source metadata differs from workflow")
    if hub.replay_projection().get("source", {}).get("sha256") != source_hash:
        raise ValueError("Improve Match Data replay differs from workflow")
    validation = json.loads(resolved["validation_report"].read_text(encoding="utf-8"))
    if validation.get("schema") != "iy.validation_report/v1" or validation.get("status") != "PASS":
        raise ValueError("Improve Match Data validation report is not PASS")

    if status == "READY_FOR_SELECTION":
        preflight = manifest.get("preflight")
        if not isinstance(preflight, dict) or preflight.get("parser_status") != "PASS":
            raise ValueError("workflow demo preflight is not valid")
        if preflight.get("map_id") != store.manifest["source"]["map_id"] or preflight.get("rounds") != len(store.round_numbers):
            raise ValueError("workflow demo preflight differs from replay")
        roster = preflight.get("roster")
        if not isinstance(roster, list) or {item.get("player_id") for item in roster if isinstance(item, dict)} != {item["player_id"] for item in store.manifest["players"]}:
            raise ValueError("workflow demo preflight roster differs from replay")
        event_count = sum(len(frame.get("events", [])) for chunk in loaded_chunks for frame in chunk["frames"])
        if preflight.get("basic_event_count") != event_count:
            raise ValueError("workflow demo preflight event count differs from replay")
        return manifest_path

    flow = json.loads(resolved["analysis_flow"].read_text(encoding="utf-8"))
    if flow.get("schema") != "iy.analysis_flow/v1" or flow.get("source", {}).get("sha256") != source_hash:
        raise ValueError("analysis flow source metadata differs from workflow")
    timeline = json.loads(resolved["timeline"].read_text(encoding="utf-8"))
    if timeline.get("source", {}).get("sha256") != source_hash or not isinstance(timeline.get("timeline"), list):
        raise ValueError("timeline source metadata differs from workflow")
    if manifest.get("selection") != flow.get("selection"):
        raise ValueError("workflow selection differs from analysis flow")
    counts = manifest.get("counts", {})
    if counts.get("players") != len(flow.get("roster", [])) or counts.get("scenes") != len(flow.get("scenes", [])):
        raise ValueError("workflow counts differ from analysis flow")
    if not resolved["review"].read_text(encoding="utf-8").strip():
        raise ValueError("review artifact is empty")
    if "report" in resolved:
        report = json.loads(resolved["report"].read_text(encoding="utf-8"))
        if report.get("schema") != "iy.analysis_report/v1" or report.get("source", {}).get("sha256") != source_hash:
            raise ValueError("report source metadata differs from workflow")
    if "tactical_replay" in resolved and not resolved["tactical_replay"].read_text(encoding="utf-8").strip():
        raise ValueError("tactical replay artifact is empty")
    return manifest_path


def _load_analyzer_data_hub(manifest_path: Path) -> AnalyzerDataHub:
    """Load the validated, local Match Data gate for the Analyzer controller."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not isinstance(artifacts.get("improve_match_data"), str):
        raise ValueError("workflow lacks Improve Match Data")
    root = manifest_path.parent.resolve()
    path = (root / artifacts["improve_match_data"]).resolve()
    if root not in path.parents:
        raise ValueError("Improve Match Data artifact escapes workflow root")
    return AnalyzerDataHub(json.loads(path.read_text(encoding="utf-8")))


@dataclass(frozen=True)
class ShellPlayer:
    player_id: str
    display_name: str
    initial_team: str


@dataclass(frozen=True)
class ShellResult:
    manifest_path: Path
    review_path: Path
    players: tuple[ShellPlayer, ...]
    selected_ids: tuple[str, ...]
    selection_mode: str
    scene_count: int
    map_id: str
    source_demo_name: str
    source_sha256: str
    status: str
    round_count: int
    basic_event_count: int
    parser_status: str
    profile_id: str


def analyzer_result_projection(result: ShellResult, flow: dict[str, object]) -> dict[str, object]:
    """Project the canonical analysis flow into factual Analyzer UI content.

    This is intentionally a presentation adapter, not an additional analyzer:
    it only repeats verified workflow facts and objective scene anchors.  In
    particular it does not turn marker frequency into a skill score, strength,
    weakness, or coaching conclusion.
    """
    source = flow.get("source") if isinstance(flow.get("source"), dict) else {}
    if str(source.get("sha256") or "") != result.source_sha256:
        raise ValueError("analyzer result source differs from workflow")
    raw_scenes = flow.get("scenes")
    if not isinstance(raw_scenes, list):
        raise ValueError("analysis flow scenes must be a list")
    anchors: Counter[str] = Counter()
    situations: list[dict[str, str]] = []
    for item in raw_scenes:
        if not isinstance(item, dict):
            continue
        anchor_types = tuple(str(value) for value in item.get("anchor_types", ()) if str(value))
        anchors.update(anchor_types)
        round_number = item.get("round_number")
        review = item.get("review") if isinstance(item.get("review"), dict) else {}
        tick = review.get("tick")
        situations.append({
            "title": f"Runde {round_number if isinstance(round_number, int) else '—'} · Tick {tick if isinstance(tick, int) else '—'}",
            "detail": ", ".join(anchor_types) if anchor_types else "Objektive Szene ohne benannten Ankertyp",
        })
    anchor_summary = tuple(
        {"anchor": anchor, "count": count}
        for anchor, count in sorted(anchors.items(), key=lambda item: (-item[1], item[0]))
    )
    return {
        "map_id": result.map_id,
        "round_count": result.round_count,
        "player_count": len(result.players),
        "event_count": result.basic_event_count,
        "scene_count": len(raw_scenes),
        "profile_id": result.profile_id or "nicht belegt",
        "situations": tuple(situations[:4]),
        "anchor_summary": anchor_summary[:4],
    }


class AnalyzerShellController:
    def __init__(
        self,
        output_root: Path,
        *,
        runner: Callable[..., Path] = preflight_demo_workflow,
        rerenderer: Callable[..., Path] = rerender_demo_workflow,
        profile_store: LocalProfileStore | None = None,
    ) -> None:
        self.output_root = output_root
        self._runner = runner
        self._rerenderer = rerenderer
        self.profile_store = profile_store or LocalProfileStore(output_root / "profiles")
        self.profiles = {profile.profile_id: profile for profile in self.profile_store.list_profiles()}
        self.profile_id = "review_v1"
        self.library = LocalAnalysisLibrary(output_root / "analysis-library.json", validate_existing_workflow)
        self.result: ShellResult | None = None
        self.data_hub: AnalyzerDataHub | None = None
        self.selected_ids: list[str] = []
        self.selection_mode = "full_demo"

    def begin_import(self) -> None:
        """Clear the prior workflow before an explicitly chosen new demo parses.

        The UI must never leave an old workflow actionable while a different
        demo is being imported.  This changes no parser or analysis semantics:
        it only makes the selected-demo boundary explicit and fail-closed.
        """
        self.result = None
        self.data_hub = None
        self.selected_ids.clear()
        self.selection_mode = "full_demo"

    def import_demo(self, demo: Path, *, max_bytes: int = 2_000_000_000) -> ShellResult:
        demo = demo.resolve()
        if demo.suffix.lower() != ".dem" and not demo.name.lower().endswith(".dem.zst"):
            raise ValueError("select a .dem or .dem.zst file")
        manifest = self._runner(demo, self.output_root, max_bytes=max_bytes)
        self.selected_ids.clear()
        self.selection_mode = "full_demo"
        self.result = self._load(manifest)
        self.data_hub = _load_analyzer_data_hub(manifest)
        if self.result.status == "READY_FOR_REVIEW":
            self.library.register(manifest)
        return self.result

    def open_existing_workflow(self, manifest_path: Path) -> ShellResult:
        manifest = validate_existing_workflow(manifest_path)
        self.result = self._load(manifest)
        self.data_hub = _load_analyzer_data_hub(manifest)
        self.selected_ids = list(self.result.selected_ids)
        self.selection_mode = self.result.selection_mode
        if self.result.status == "READY_FOR_REVIEW":
            self.library.register(manifest)
        return self.result

    def link_source_demo(self, demo: Path) -> ShellResult:
        result = self._require_result()
        manifest_path = validate_existing_workflow(result.manifest_path)
        demo = demo.resolve()
        if not demo.is_file() or (demo.suffix.lower() != ".dem" and not demo.name.lower().endswith(".dem.zst")):
            raise ValueError("select an existing .dem or .dem.zst file")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if _sha256_file(demo) != manifest["source_sha256"]:
            raise ValueError("selected demo SHA-256 differs from workflow source")
        manifest["source_demo_name"] = demo.name
        temporary = manifest_path.with_name("demo-workflow.json.tmp")
        try:
            temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(manifest_path)
        finally:
            if temporary.exists():
                temporary.unlink()
        self.result = self._load(manifest_path)
        self.data_hub = _load_analyzer_data_hub(manifest_path)
        if self.result.status == "READY_FOR_REVIEW":
            self.library.register(manifest_path)
        return self.result

    def set_full_demo(self) -> None:
        self._require_result()
        self.selected_ids.clear()
        self.selection_mode = "full_demo"

    def reset_players(self) -> None:
        self._require_result()
        self.selected_ids.clear()
        self.selection_mode = "player_select"

    def add_player(self, player_id: str) -> None:
        result = self._require_result()
        known = {player.player_id for player in result.players}
        if player_id not in known:
            raise ValueError(f"unknown player: {player_id}")
        if player_id not in self.selected_ids:
            self.selected_ids.append(player_id)
        self.selection_mode = "player_select"

    def add_team(self, team: str) -> None:
        result = self._require_result()
        if team not in {"CT", "T"}:
            raise ValueError("team must be CT or T")
        for player in result.players:
            if player.initial_team == team and player.player_id not in self.selected_ids:
                self.selected_ids.append(player.player_id)
        self.selection_mode = "player_select"

    def available_players(self) -> tuple[ShellPlayer, ...]:
        result = self._require_result()
        selected = set(self.selected_ids)
        return tuple(player for player in result.players if player.player_id not in selected)

    def analyze_selection(self) -> ShellResult:
        result = self._require_result()
        if self.selection_mode == "player_select" and not self.selected_ids:
            raise ValueError("Player Select requires at least one player")
        manifest_path = self.validate_current_workflow()
        manifest = self._rerenderer(
            manifest_path, player_ids=tuple(self.selected_ids), profile=self.profiles[self.profile_id]
        )
        self.result = self._load(manifest)
        self.data_hub = _load_analyzer_data_hub(manifest)
        if self.result.status == "READY_FOR_REVIEW":
            self.library.register(manifest)
        return self.result

    def library_entries(self) -> tuple[dict[str, object], ...]:
        return self.library.entries()

    def remove_from_library(self, manifest_path: Path) -> None:
        """Remove only the navigation reference; workflow files remain untouched."""
        self.library.remove(manifest_path)

    def select_profile(self, profile_id: str) -> None:
        if profile_id not in self.profiles:
            raise ValueError(f"unknown local analysis profile: {profile_id}")
        self.profile_id = profile_id

    def update_custom_rules(self, enabled_rule_ids: tuple[str, ...]) -> Path:
        profile = self.profiles.get(self.profile_id)
        if profile is None or profile.purpose != "custom":
            raise ValueError("rule toggles are editable only for a Custom profile")
        updated = replace(profile, enabled_rule_ids=tuple(rule for rule in OBJECTIVE_RULES if rule in enabled_rule_ids))
        path = self.profile_store.save(updated)
        self.profiles[updated.profile_id] = updated
        return path

    def validate_current_workflow(self) -> Path:
        return validate_existing_workflow(self._require_result().manifest_path)

    def review_presentation(self, system_check: dict[str, object] | None = None) -> dict[str, object]:
        if self.data_hub is None:
            raise RuntimeError("import a demo first")
        return build_review_presentation(self.data_hub.for_consumer("review"), system_check)

    def _require_result(self) -> ShellResult:
        if self.result is None:
            raise RuntimeError("import a demo first")
        return self.result

    @staticmethod
    def _load(manifest_path: Path) -> ShellResult:
        manifest_path = manifest_path.resolve()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != "iy.demo_workflow/v1":
            raise ValueError("expected iy.demo_workflow/v1 manifest")
        root = manifest_path.parent
        if manifest["status"] == "READY_FOR_REVIEW":
            flow = json.loads((root / manifest["artifacts"]["analysis_flow"]).read_text(encoding="utf-8"))
            roster, scenes, selection = flow["roster"], flow["scenes"], flow["selection"]
            map_id = flow["source"].get("map_id")
            round_count = len(flow.get("rounds", ())) or int(manifest.get("counts", {}).get("rounds", 0))
        else:
            preflight = manifest["preflight"]
            roster, scenes, selection = preflight["roster"], [], manifest["selection"]
            map_id, round_count = preflight["map_id"], int(preflight["rounds"])
        players = tuple(
            ShellPlayer(item["player_id"], item["display_name"], item["initial_team"])
            for item in roster
        )
        return ShellResult(
            manifest_path=manifest_path,
            review_path=root / manifest["artifacts"].get("review", "review.html"),
            players=players,
            selected_ids=tuple(selection["player_ids"]), selection_mode=selection["mode"],
            scene_count=len(scenes), map_id=str(map_id or "unknown"),
            source_demo_name=str(manifest.get("source_demo_name") or ""),
            source_sha256=str(manifest["source_sha256"]), status=str(manifest["status"]),
            round_count=round_count,
            basic_event_count=int(manifest.get("preflight", {}).get("basic_event_count", 0)),
            parser_status=str(manifest.get("preflight", {}).get("parser_status", "PASS")),
            profile_id=str((manifest.get("profile") or {}).get("profile_id") or ""),
        )


class AnalyzerShellApp:
    def __init__(self, controller: AnalyzerShellController) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("Improve Yourself – Experimental")
        # The approved Optimizer MASTER exports use a 1536×1024 viewport.
        # Start at that comparable desktop geometry; the existing minimum-size
        # contract remains responsible for compact windows.
        self.root.geometry("1536x1024")
        self.root.minsize(1080, 720)
        self.root.configure(background=_THEME["night"])
        _enable_dark_titlebar(self.root)
        assets_path = Path(__file__).with_name("assets")
        self.ui_font, self.display_font = _register_private_fonts(self.root, assets_path)
        self.root.option_add("*Font", f"{self.ui_font} 10")
        icon_path = assets_path / "improve-yourself-icon-v3.png"
        try:
            self.app_icon = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self.app_icon)
        except tk.TclError:
            self.app_icon = None
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            ".", background=_THEME["panel"], foreground=_THEME["ink"],
            fieldbackground=_THEME["deep"], font=(self.ui_font, 10),
            bordercolor=_THEME["line_soft"], lightcolor=_THEME["panel_high"],
            darkcolor=_THEME["deep"], focuscolor=_THEME["accent"],
        )
        style.configure("TFrame", background=_THEME["night"])
        style.configure("Content.TFrame", background=_THEME["night"])
        # Dark V1 is shared by Home and every existing product route.  The
        # card family intentionally stays close to the app background; a
        # border is a depth cue, not a permanently lit frame.
        style.configure("Card.TFrame", background=_THEME["card"], relief="flat", borderwidth=1, bordercolor=_THEME["border_soft"])
        style.configure("CardInner.TFrame", background=_THEME["card"], relief="flat", borderwidth=0)
        # Reference-locked Optimizer token family.  It intentionally derives
        # its values from the approved metallic master rather than inheriting
        # the older generic shell widgets.
        style.configure("OptimizerArea.TFrame", background=_OPTIMIZER_THEME["surface"], relief="flat", borderwidth=0)
        style.configure("OptimizerAreaActive.TFrame", background=_OPTIMIZER_THEME["surface_raised"], relief="flat", borderwidth=0)
        style.configure("OptimizerArea.TLabel", background=_OPTIMIZER_THEME["surface"], foreground=_OPTIMIZER_THEME["text"])
        style.configure("OptimizerAreaMuted.TLabel", background=_OPTIMIZER_THEME["surface"], foreground=_OPTIMIZER_THEME["muted"])
        style.configure("OptimizerAreaActive.TLabel", background=_OPTIMIZER_THEME["surface_raised"], foreground=_OPTIMIZER_THEME["text"])
        style.configure("OptimizerAreaActiveMuted.TLabel", background=_OPTIMIZER_THEME["surface_raised"], foreground=_OPTIMIZER_THEME["secondary"])
        style.configure("OptimizerHero.TFrame", background=_OPTIMIZER_THEME["surface_hero"], relief="flat", borderwidth=0)
        style.configure("OptimizerHero.TLabel", background=_OPTIMIZER_THEME["surface_hero"], foreground=_OPTIMIZER_THEME["text"])
        style.configure("OptimizerHeroMuted.TLabel", background=_OPTIMIZER_THEME["surface_hero"], foreground=_OPTIMIZER_THEME["secondary"])
        style.configure("OptimizerDetail.TFrame", background=_OPTIMIZER_THEME["surface_detail"], relief="flat", borderwidth=0)
        style.configure("OptimizerDetail.TLabel", background=_OPTIMIZER_THEME["surface_detail"], foreground=_OPTIMIZER_THEME["text"])
        style.configure("OptimizerDetailMuted.TLabel", background=_OPTIMIZER_THEME["surface_detail"], foreground=_OPTIMIZER_THEME["secondary"])
        style.configure("OptimizerMetric.TFrame", background=_OPTIMIZER_THEME["surface_raised"], relief="flat", borderwidth=0)
        style.configure("OptimizerMetric.TLabel", background=_OPTIMIZER_THEME["surface_raised"], foreground=_OPTIMIZER_THEME["text"])
        style.configure("OptimizerMetricMuted.TLabel", background=_OPTIMIZER_THEME["surface_raised"], foreground=_OPTIMIZER_THEME["muted"])
        style.configure("Optimizer.Treeview", background=_OPTIMIZER_THEME["surface_input"], fieldbackground=_OPTIMIZER_THEME["surface_input"], foreground=_OPTIMIZER_THEME["text"], rowheight=42, borderwidth=0, relief="flat")
        style.map("Optimizer.Treeview", background=[("selected", "#0B3857")], foreground=[("selected", "#F4FBFF")])
        style.configure("Optimizer.Treeview.Heading", background=_OPTIMIZER_THEME["surface_raised"], foreground=_OPTIMIZER_THEME["secondary"], relief="flat", borderwidth=0, font=(self.ui_font, 8, "bold"))
        style.configure("Optimizer.TEntry", background=_OPTIMIZER_THEME["surface_input"], fieldbackground=_OPTIMIZER_THEME["surface_input"], foreground=_OPTIMIZER_THEME["text"], bordercolor=_OPTIMIZER_THEME["border"], insertcolor=_OPTIMIZER_THEME["accent"], padding=(10, 8))
        style.map("Optimizer.TEntry", bordercolor=[("focus", _OPTIMIZER_THEME["border_bright"])])
        style.configure("Optimizer.TCombobox", background=_OPTIMIZER_THEME["surface_input"], fieldbackground=_OPTIMIZER_THEME["surface_input"], foreground=_OPTIMIZER_THEME["text"], arrowcolor=_OPTIMIZER_THEME["secondary"], bordercolor=_OPTIMIZER_THEME["border"], padding=(10, 8))
        style.map("Optimizer.TCombobox", fieldbackground=[("readonly", _OPTIMIZER_THEME["surface_input"])], foreground=[("readonly", _OPTIMIZER_THEME["text"])], bordercolor=[("focus", _OPTIMIZER_THEME["border_bright"])])
        style.configure("PageTitle.TLabel", background=_THEME["night"], foreground=_THEME["ink"], font=(self.display_font, 22, "bold"))
        style.configure("PageKicker.TLabel", background=_THEME["night"], foreground=_THEME["cyan"], font=(self.display_font, 8))
        style.configure("StatusBadge.TLabel", background=_THEME["panel_high"], foreground=_THEME["secondary"], padding=(9, 5), font=(self.ui_font, 8, "bold"))
        # Home deliberately has its own component family.  The command-centre
        # layout is shared with the rest of the shell, while these styles keep
        # its cards from falling back to the generic/native looking controls.
        # Home uses the darkest approved panel level.  Raised blue remains a
        # small interaction state, never the ground of a large card.
        style.configure("HomeStat.TFrame", background=_THEME["panel"], relief="flat", borderwidth=1, bordercolor=_THEME["border"])
        style.configure("HomeModule.TFrame", background=_THEME["panel"], relief="flat", borderwidth=1, bordercolor=_THEME["border"])
        style.configure("HomePanel.TFrame", background=_THEME["panel"], relief="flat", borderwidth=1, bordercolor=_THEME["border"])
        style.configure("HomeInner.TFrame", background=_THEME["panel"], relief="flat", borderwidth=0)
        style.configure("HomeMetric.TFrame", background=_THEME["panel_high"], relief="flat", borderwidth=1, bordercolor=_THEME["border_soft"])
        style.configure("HomeStat.TLabel", background=_THEME["panel"], foreground=_THEME["ice"])
        style.configure("HomeModule.TLabel", background=_THEME["panel"], foreground=_THEME["ink"])
        style.configure("HomePanel.TLabel", background=_THEME["panel"], foreground=_THEME["ink"])
        style.configure("HomeMetricLabel.TLabel", background=_THEME["panel_high"], foreground=_THEME["secondary"])
        style.configure("HomeMetricValue.TLabel", background=_THEME["panel_high"], foreground=_THEME["ink"])
        style.configure("HomeMuted.TLabel", background=_THEME["panel"], foreground=_THEME["secondary"])
        style.configure("HomePanelMuted.TLabel", background=_THEME["panel"], foreground=_THEME["secondary"])
        style.configure("HomeKicker.TLabel", background=_THEME["night"], foreground=_THEME["cyan"], font=(self.display_font, 9))
        style.configure("HomePrimary.TButton", background=_THEME["accent"], foreground="#f7fbff", padding=(13, 8), borderwidth=1, bordercolor=_THEME["accent_bright"], relief="flat", font=(self.ui_font, 9, "bold"))
        style.map("HomePrimary.TButton", background=[("active", _THEME["accent_bright"]), ("pressed", "#05456f"), ("disabled", "#0b2232")], bordercolor=[("active", "#8fd9ff"), ("disabled", "#1a3a50")])
        style.configure("HomeTeal.TButton", background="#07574f", foreground="#ecfffb", padding=(13, 8), borderwidth=1, bordercolor="#20d0b0", relief="flat", font=(self.ui_font, 9, "bold"))
        style.map("HomeTeal.TButton", background=[("active", "#087b70"), ("pressed", "#06463f"), ("disabled", "#0b2232")], bordercolor=[("active", "#9fffe9"), ("disabled", "#1a3a50")])
        style.configure("HomeViolet.TButton", background="#38285e", foreground="#f6f0ff", padding=(13, 8), borderwidth=1, bordercolor="#a684ff", relief="flat", font=(self.ui_font, 9, "bold"))
        style.map("HomeViolet.TButton", background=[("active", "#564090"), ("pressed", "#2c2049"), ("disabled", "#171d2b")], bordercolor=[("active", "#dfd1ff"), ("disabled", "#30384b")])
        style.configure("HomeGold.TButton", background="#6b5014", foreground="#fff8e5", padding=(13, 8), borderwidth=1, bordercolor="#e3b940", relief="flat", font=(self.ui_font, 9, "bold"))
        style.map("HomeGold.TButton", background=[("active", "#927123"), ("pressed", "#513d10"), ("disabled", "#272417")], bordercolor=[("active", "#ffdc77"), ("disabled", "#3b3520")])
        style.configure("Sidebar.TFrame", background=_THEME["sidebar"], borderwidth=0)
        style.configure("TLabel", background=_THEME["night"], foreground=_THEME["ink"])
        style.configure("Card.TLabel", background=_THEME["card"], foreground=_THEME["ink"])
        style.configure("Muted.TLabel", background=_THEME["card"], foreground=_THEME["muted"])
        style.configure("TLabelframe", background=_THEME["card"], foreground=_THEME["ink"], relief="flat", borderwidth=1, bordercolor=_THEME["border_soft"])
        style.configure("TLabelframe.Label", background=_THEME["card"], foreground=_THEME["ice"], font=(self.ui_font, 9, "bold"))
        style.configure(
            "TButton", background=_THEME["panel_hover"], foreground=_THEME["ice"], padding=(14, 9),
            borderwidth=1, bordercolor=_THEME["border"], relief="flat", font=(self.ui_font, 9, "bold"),
            focusthickness=0,
        )
        style.map(
            "TButton",
            background=[("active", "#122D43"), ("pressed", "#085A95"), ("disabled", _THEME["panel"])],
            bordercolor=[("active", _THEME["border_active"]), ("pressed", _THEME["accent"]), ("disabled", _THEME["border_soft"])],
            foreground=[("disabled", _THEME["muted"])],
        )
        style.configure(
            "Primary.TButton", background=_THEME["accent"], foreground="#ffffff",
            bordercolor=_THEME["cyan"], font=(self.ui_font, 9, "bold"), padding=(16, 9),
        )
        style.map("Primary.TButton", background=[("active", _THEME["cyan"]), ("pressed", "#085A95"), ("disabled", _THEME["panel"])])
        # The native Windows scrollbar trough was the final bright foreign
        # surface in the Optimizer canvas.  Keep its platform behaviour, but
        # render it as a quiet part of the Midnight shell.
        style.configure(
            "Vertical.TScrollbar", background=_THEME["panel_high"], troughcolor=_THEME["night"],
            bordercolor=_THEME["border_soft"], arrowcolor=_THEME["secondary"],
            lightcolor=_THEME["panel_high"], darkcolor=_THEME["panel_high"],
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", _THEME["panel_hover"]), ("pressed", _THEME["accent"])],
        )
        style.configure(
            "TCombobox", background=_THEME["deep"], fieldbackground=_THEME["deep"],
            foreground=_THEME["ink"], arrowcolor=_THEME["ice"], bordercolor=_THEME["border"],
            lightcolor=_THEME["deep"], darkcolor=_THEME["deep"], padding=(8, 6),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", _THEME["deep"]), ("disabled", _THEME["deep"])],
            foreground=[("readonly", _THEME["ink"]), ("disabled", _THEME["muted"])],
            selectbackground=[("readonly", _THEME["deep"])],
            selectforeground=[("readonly", _THEME["ink"])],
        )
        style.configure(
            "TCheckbutton", background=_THEME["panel"], foreground=_THEME["ink"],
            indicatorcolor=_THEME["deep"], indicatormargin=6, padding=(4, 4),
        )
        style.map(
            "TCheckbutton",
            background=[("active", _THEME["panel"]), ("disabled", _THEME["panel"])],
            foreground=[("disabled", _THEME["muted"])],
            indicatorcolor=[("selected", _THEME["ice"]), ("disabled", _THEME["metal"])],
        )
        style.configure(
            "Rule.TCheckbutton", indicatoron=False, anchor="w", background=_THEME["panel"],
            foreground=_THEME["muted"], padding=(12, 10), borderwidth=1,
            bordercolor=_THEME["line_soft"], font=(self.ui_font, 9, "bold"),
        )
        style.map(
            "Rule.TCheckbutton",
            background=[("selected", _THEME["panel_hover"]), ("active", "#122D43"), ("disabled", _THEME["panel"])],
            foreground=[("selected", "#ffffff"), ("active", "#ffffff"), ("disabled", "#587184")],
            bordercolor=[("selected", _THEME["accent"]), ("active", _THEME["line"]), ("disabled", _THEME["line_soft"])],
        )
        style.configure(
            "Horizontal.TScale", background=_THEME["panel"], troughcolor="#04131F",
            bordercolor=_THEME["border_soft"], lightcolor=_THEME["cyan"], darkcolor=_THEME["accent"],
            slidercolor=_THEME["cyan"], gripcount=0, borderwidth=0,
        )
        self.status = tk.StringVar(value="Echte CS2-Demo auswählen")
        self.identity = tk.StringVar(value="Keine lokale Analyse geladen")
        self.demo_preflight = tk.StringVar(value="Demo-Preflight ausstehend")
        self.player_by_label: dict[str, str] = {}
        self.review_server: ReviewCoordinatorServer | None = None
        self.netcon_status = tk.StringVar(value="○ Lokale CS2-Verbindung: noch nicht geprüft")
        self.demo_status = tk.StringVar(value="○ Demo-Modus: noch nicht geprüft")
        self.filename_status = tk.StringVar(value="○ Dateiname: noch nicht geprüft")
        self.preflight_message = tk.StringVar(value="Vor dem Review CS2 prüfen.")
        self.overview_status = tk.StringVar(value="Noch keine Demo geladen")
        self.dashboard_rounds = tk.StringVar(value="—\nRunden")
        self.dashboard_players = tk.StringVar(value="—\nSpieler")
        self.dashboard_scenes = tk.StringVar(value="—\nSzenen")
        self.dashboard_readiness = tk.StringVar(value="BEREIT\nLokaler Modus")
        self.dashboard_pipeline = tk.StringVar(value="Demo nicht geladen\nParser —  ·  Auswahl —  ·  Szenen —  ·  Review —")
        self.dashboard_recent = tk.StringVar(value="Noch keine lokale Analyse geöffnet.")
        self.dashboard_progress_summary = tk.StringVar(value="Gesamtfortschritt: noch keine Datenbasis")
        self.dashboard_progress_dimensions = {
            name: tk.StringVar(value="Nicht verfügbar")
            for name in ("AIM", "DUELS", "UTILITY", "GAME SENSE / POSITIONING", "PERFORMANCE")
        }
        self.dashboard_system_scan_time = tk.StringVar(value="Noch kein Systemscan")
        self.dashboard_system_scan_overall = tk.StringVar(value="Noch keine lokalen Systemdaten vorhanden.")
        self.dashboard_system_scan_attention = tk.StringVar(value="")
        self.dashboard_system_scan_cells = {
            name: tk.StringVar(value="—") for name in _SYSTEM_SCAN_HOME_FIELDS
        }
        self.report_status = tk.StringVar(value="Nach einer Analyse stehen Report und Timeline lokal bereit.")
        self.system_status = tk.StringVar(value="System Check wurde noch nicht ausgeführt.")
        self.embedded_review: EmbeddedReviewSession | None = None
        self.embedded_scene_id: str | None = None
        self.embedded_cs2_status = tk.StringVar(value="CS2-Bereitschaft noch nicht geprüft.")
        self.embedded_scene_title = tk.StringVar(value="Keine Szene ausgewählt")
        self.embedded_scene_context = tk.StringVar(value="")
        self.embedded_scene_players = tk.StringVar(value="")
        self.embedded_scene_rules = tk.StringVar(value="")
        self.embedded_tactical: EmbeddedTacticalSession | None = None
        self.tactical_scene_title = tk.StringVar(value="Keine Szene ausgewählt")
        self.tactical_scene_context = tk.StringVar(value="")
        self.tactical_scene_note = tk.StringVar(value="Keine Review-Notiz")
        self.tactical_frame_status = tk.StringVar(value="")
        self.tactical_action_status = tk.StringVar(value="Tactical Replay wird aus einer Review-Szene geöffnet.")
        self.tactical_frame_index = 0
        self.tactical_zoom = 1.0
        self.tactical_pan = [0.0, 0.0]
        self.tactical_drag_origin: tuple[int, int] | None = None
        self.tactical_syncing_selection = False
        self.tactical_ignore_selection_event = False
        self.analyzer_setup_expanded = False
        self.current_page: str | None = None
        self.page_history: list[str] = []
        self._import_started_at: float | None = None
        self._import_status_after: str | None = None

        shell = ttk.Frame(self.root, style="Content.TFrame")
        shell.pack(fill="both", expand=True)
        self.shell = shell
        # Variant 3 uses a compact fixed shell: content begins close to the
        # 243 px MASTER boundary while navigation remains comfortably readable.
        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", width=243)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Frame(sidebar, width=1, background=_THEME["line_soft"]).pack(side="right", fill="y")
        brand_path = Path(__file__).with_name("assets") / "improve-yourself-wordmark-v3.png"
        try:
            self.brand_image = tk.PhotoImage(file=str(brand_path)).subsample(3, 3)
            tk.Label(sidebar, image=self.brand_image, background=_THEME["sidebar"]).pack(anchor="w", padx=20, pady=(24, 7))
        except tk.TclError:
            ttk.Label(sidebar, text="IMPROVE\nYOURSELF", style="Card.TLabel", font=("Segoe UI", 17, "bold"), justify="left").pack(anchor="w", padx=20, pady=(26, 7))
        tk.Label(sidebar, text="EXPERIMENTAL BUILD", background=_THEME["sidebar"], foreground="#73bddf", font=(self.ui_font, 8, "bold")).pack(anchor="w", padx=21, pady=(0, 22))
        content = ttk.Frame(shell, style="Content.TFrame", padding=(24, 18, 24, 24))
        content.pack(side="left", fill="both", expand=True)
        self.pages: dict[str, ttk.Frame] = {}
        self.page_hosts: dict[str, ttk.Frame] = {}
        self.nav_buttons: dict[str, SidebarNavItem] = {}
        nav_labels = {
            "Dashboard": "⌂   Dashboard",
            "My Improvement": "↗   My Improvement",
            "Analyzer": "◎   Analyzer",
            "Reports": "▤   Reports",
            "System Check / Optimizer": "◈   Optimizer",
            "Settings": "⚙   Settings",
            "Tactical Replay": "⌖   Tactical Replay",
            "Benchmark": "▱   Improve Benchmark",
        }
        for name in UI_REFERENCE_STATUS:
            host = ttk.Frame(content, style="Content.TFrame")
            host.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.page_hosts[name] = host
            if name in {"Analyzer", "Dashboard", "My Improvement", "Benchmark"}:
                canvas = tk.Canvas(
                    host, background=_THEME["night"], borderwidth=0, highlightthickness=0,
                )
                scrollbar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=scrollbar.set)
                canvas.pack(side="left", fill="both", expand=True)
                page = ttk.Frame(canvas, style="Content.TFrame")
                page_window = canvas.create_window((0, 0), window=page, anchor="nw")
                page.bind("<Configure>", lambda _event, target=canvas, body=page, bar=scrollbar: self._sync_scrollable_page(target, body, bar))
                canvas.bind(
                    "<Configure>",
                    lambda event, target=canvas, item=page_window, body=page, bar=scrollbar: self._resize_scrollable_page(target, item, body, bar, event.width),
                )
                canvas.bind(
                    "<MouseWheel>",
                    lambda event, target=canvas: target.yview_scroll(int(-event.delta / 120), "units"),
                )
                page.bind(
                    "<MouseWheel>",
                    lambda event, target=canvas: target.yview_scroll(int(-event.delta / 120), "units"),
                )
                if name == "Analyzer":
                    self.analyzer_canvas = canvas
                elif name == "Dashboard":
                    self.dashboard_canvas = canvas
                    self.dashboard_scrollbar = scrollbar
            elif name == "System Check / Optimizer":
                # The Optimizer must not inherit a page-wide scrollbar. Its
                # overview is compact and its only potentially long content,
                # "Details & Erklärung", owns a local scroll surface.
                page = ttk.Frame(host, style="Content.TFrame")
                page.pack(fill="both", expand=True)
                self.system_canvas = None
            else:
                page = ttk.Frame(host, style="Content.TFrame")
                page.pack(fill="both", expand=True)
            self.pages[name] = page
        # Hosts follow the canonical product-section map above.  Navigation,
        # however, must follow the explicit workflow order rather than the
        # implementation order of that map.
        primary_navigation = ttk.Frame(sidebar, style="Sidebar.TFrame")
        primary_navigation.pack(fill="x")
        secondary_navigation = ttk.Frame(sidebar, style="Sidebar.TFrame")
        secondary_navigation.pack(side="bottom", fill="x", padx=0, pady=(0, 4))
        SidebarStatusPanel(tk, sidebar, ui_font=self.ui_font).pack(side="bottom", fill="x", padx=12, pady=(12, 10))
        self.history_button = ttk.Button(
            secondary_navigation, text="← Zurück", command=self._go_back, state="disabled",
        )
        self.history_button.pack(fill="x", padx=12, pady=(0, 8))
        for name in _SIDEBAR_PRIMARY + _SIDEBAR_SECONDARY:
            button = SidebarNavItem(
                tk, primary_navigation if name in _SIDEBAR_PRIMARY else secondary_navigation,
                text=nav_labels[name], ui_font=self.ui_font,
                command=lambda value=name: self._show_page(value),
            )
            button.pack(fill="x", padx=11, pady=2)
            self.nav_buttons[name] = button

        frame = self.pages["Analyzer"]
        analyzer_header = ttk.Frame(frame, style="Content.TFrame")
        analyzer_header.pack(fill="x", pady=(0, 12))
        ttk.Label(analyzer_header, text="Improve Analyzer", style="PageTitle.TLabel").pack(side="left")
        ttk.Label(analyzer_header, textvariable=self.status, style="StatusBadge.TLabel").pack(side="right")
        ttk.Label(frame, text="Detaillierte Match-Analyse auf Basis deiner belegten lokalen Demos, Profile und objektiven Regeln.", foreground=_THEME["muted"]).pack(anchor="w", pady=(0, 12))

        # The v1.1 master defines one Analyzer with three workflow tabs.  The
        # tabs only arrange existing local controls; no parser or review path
        # is duplicated here.
        tab_bar = ttk.Frame(frame, style="Content.TFrame")
        tab_bar.pack(fill="x", pady=(0, 12))
        tab_body = ttk.Frame(frame, style="Content.TFrame")
        tab_body.pack(fill="both", expand=True)
        self.analyzer_tabs: dict[str, ttk.Frame] = {}
        self.analyzer_tab_buttons: dict[str, ttk.Button] = {}
        for label in ("Übersicht", "Analyse", "Review"):
            tab = ttk.Frame(tab_body, style="Content.TFrame")
            self.analyzer_tabs[label] = tab
            button = ttk.Button(tab_bar, text=label, command=lambda value=label: self._show_analyzer_tab(value))
            button.pack(side="left", padx=(0, 6))
            self.analyzer_tab_buttons[label] = button
        overview_tab = self.analyzer_tabs["Übersicht"]
        analysis_tab = self.analyzer_tabs["Analyse"]
        review_tab = self.analyzer_tabs["Review"]
        self.analyzer_active_tab = "Übersicht"

        analyzer_top = ttk.Frame(analysis_tab, style="Content.TFrame")
        analyzer_top.pack(fill="x")
        self.analyzer_top = analyzer_top
        source_card = ttk.Frame(analyzer_top, style="Card.TFrame", padding=16)
        source_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(source_card, text="FILTER & DATENQUELLE", style="Card.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        source_actions = ttk.Frame(source_card, style="CardInner.TFrame")
        source_actions.pack(fill="x", pady=(8, 0))
        ttk.Button(source_actions, text="Demo auswählen", style="Primary.TButton", command=self._choose_demo).pack(fill="x")
        ttk.Button(source_actions, text="Vorhandene Analyse öffnen", command=self._open_existing).pack(fill="x", pady=5)
        ttk.Button(
            source_actions,
            text="Demo-Übersicht öffnen",
            command=lambda: self._show_analyzer_tab("Übersicht"),
        ).pack(fill="x", pady=(0, 5))
        self.link_button = ttk.Button(source_actions, text="Quelldemo zuordnen", command=self._link_source, state="disabled")
        self.link_button.pack(fill="x")
        ttk.Label(source_card, textvariable=self.identity, style="Muted.TLabel", wraplength=470, justify="left").pack(anchor="w", pady=(10, 0))
        ttk.Label(source_card, textvariable=self.demo_preflight, style="Card.TLabel", wraplength=470, justify="left").pack(anchor="w", pady=(4, 0))

        teams = ttk.Frame(analyzer_top, style="Content.TFrame")
        teams.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.ct = ttk.LabelFrame(teams, text="CT LINE-UP", padding=10)
        self.ct.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.t = ttk.LabelFrame(teams, text="T LINE-UP", padding=10)
        self.t.pack(side="left", fill="both", expand=True, padx=(4, 0))

        selection_card = ttk.Frame(analysis_tab, style="Card.TFrame", padding=16)
        selection_card.pack(fill="x", pady=(12, 0))
        self.analyzer_selection_card = selection_card
        ttk.Label(selection_card, text="ANALYSE REGELN & SPIELERAUSWAHL", style="Card.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        controls = ttk.Frame(selection_card, style="CardInner.TFrame")
        controls.pack(fill="x", pady=(10, 4))
        self.workflow_widgets = []
        for text, command in (("Full Demo", self._full), ("CT", lambda: self._team("CT")), ("T", lambda: self._team("T")), ("Reset", self._reset)):
            button = ttk.Button(controls, text=text, command=command, state="disabled")
            button.pack(side="left", padx=4 if text != "Full Demo" else 0)
            self.workflow_widgets.append(button)
        player_controls = ttk.Frame(selection_card, style="CardInner.TFrame")
        player_controls.pack(fill="x", pady=(2, 4))
        ttk.Label(player_controls, text="Spieler", style="Muted.TLabel").pack(side="left")
        self.player = ttk.Combobox(player_controls, state="disabled", width=32)
        self.player.pack(side="left", padx=(10, 4))
        self.add_button = ttk.Button(player_controls, text="+ Add Player", command=self._add, state="disabled")
        self.add_button.pack(side="left")
        self.workflow_widgets.extend((self.player, self.add_button))

        profile_row = ttk.Frame(selection_card, style="CardInner.TFrame")
        profile_row.pack(fill="x", pady=6)
        ttk.Label(profile_row, text="Analyseprofil").pack(side="left")
        self.profile = ttk.Combobox(profile_row, state="disabled", width=24, values=tuple(controller.profiles))
        self.profile.set("review_v1")
        self.profile.pack(side="left", padx=8)
        self.profile.bind("<<ComboboxSelected>>", self._select_profile)
        self.workflow_widgets.append(self.profile)
        self.rules = ttk.Label(profile_row, text="Objektive V1-Regeln · Details per Profil")
        self.rules.pack(side="left", padx=8)
        self.profile_criteria = ttk.Label(profile_row, style="StatusBadge.TLabel")
        self.profile_criteria.pack(side="right")

        self.chosen = ttk.Label(selection_card, text="Full Demo", style="Muted.TLabel")
        self.chosen.pack(anchor="w", pady=(4, 0))

        # Keep the primary workflow action immediately below the selection
        # controls.  Rules remain available as configuration context, but a
        # loaded real demo must not require scrolling past the whole ruleset
        # before the user can start the existing analysis.
        review_strip = ttk.Frame(analysis_tab, style="Content.TFrame")
        review_strip.pack(fill="x", pady=(12, 0))
        self.analyzer_review_strip = review_strip
        actions = ttk.Frame(review_strip, style="Card.TFrame", padding=14)
        actions.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(actions, text="ANALYSE & REVIEW", style="Card.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(0, 8))
        action_row = ttk.Frame(actions, style="CardInner.TFrame")
        action_row.pack(fill="x")
        self.analyze_button = ttk.Button(action_row, text="Analyse starten", command=self._analyze, state="disabled")
        self.analyze_button.pack(side="left")
        self.cs2_button = ttk.Button(action_row, text="CS2 prüfen", command=self._preflight, state="disabled")
        self.cs2_button.pack(side="left", padx=8)
        self.workflow_widgets.extend((self.analyze_button, self.cs2_button))
        self.review_button = ttk.Button(action_row, text="Review anzeigen", command=self._open_review, state="disabled")
        self.review_button.pack(side="left")
        self.analysis_action_status = tk.StringVar(value="Analyse starten wird nach einem erfolgreichen lokalen Demo-Import verfügbar.")
        ttk.Label(actions, textvariable=self.analysis_action_status, style="Muted.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(9, 0))
        preflight = ttk.LabelFrame(review_strip, text="CS2-READINESS", padding=12)
        preflight.pack(side="left", fill="both", expand=True, padx=(6, 0))
        for variable in (self.netcon_status, self.demo_status, self.filename_status, self.preflight_message):
            ttk.Label(preflight, textvariable=variable).pack(anchor="w")

        rules_frame = ttk.LabelFrame(analysis_tab, text="Objektive Szenenanker V1", padding=18)
        ttk.Label(analysis_tab, text="REGELSET", style="SectionTitle.TLabel").pack(anchor="w", pady=(16, 0))
        ttk.Label(analysis_tab, text="Profile kombinieren belegte Marker; einzelne schwache Hinweise erzeugen keine Standard-Szene.", foreground=_THEME["muted"]).pack(anchor="w", pady=(2, 14))
        rules_frame.pack(fill="x", pady=5)
        rules_frame.columnconfigure(0, weight=1, uniform="rules")
        rules_frame.columnconfigure(1, weight=1, uniform="rules")
        self.rule_vars: dict[str, tk.BooleanVar] = {}
        self.rule_checks = []
        labels = {
            "objective_kill": "Kill", "objective_multi_kill": "Multi-Kill", "objective_headshot": "Headshot",
            "objective_wallbang": "Wallbang", "objective_smoke_kill": "Smoke-Kill",
            "objective_blind_kill": "Blind-Kill", "objective_entry": "Entry",
        }
        for index, rule_id in enumerate(OBJECTIVE_RULES):
            variable = tk.BooleanVar(value=True)
            check = ttk.Checkbutton(rules_frame, text=labels[rule_id], variable=variable, command=self._save_custom_rules, style="Rule.TCheckbutton")
            check.grid(row=index // 2, column=index % 2, sticky="ew", padx=(0, 12), pady=5)
            check.bind("<Double-Button-1>", lambda _event, value=rule_id: self._show_rule_details(value))
            self.rule_vars[rule_id] = variable
            self.rule_checks.append(check)
        self.workflow_widgets.extend(self.rule_checks)
        architecture = ttk.Frame(analysis_tab, style="Card.TFrame", padding=16)
        architecture.pack(fill="x", pady=(12, 0))
        ttk.Label(architecture, text="INDIKATOREN  →  REGELKOMBINATIONEN  →  ANALYSEPROFIL  →  SZENEN", style="Card.TLabel", font=("Segoe UI Semibold", 10)).pack(anchor="w")
        ttk.Label(architecture, text="Standardprofile erzeugen Szenen nur aus vollständig definierten objektiven Kombinationen.", style="Muted.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(analysis_tab, text=f"Lokale Profile: {controller.profile_store.root}", foreground=_THEME["muted"]).pack(anchor="w", pady=(10, 5))

        self._build_analyzer_result_projection(review_tab)
        self._build_embedded_review(review_tab)
        self._build_dashboard_page()
        self._build_my_improvement_page()
        self._build_demo_analyzer_page(overview_tab)
        self._build_reports_page()
        self._build_settings_page()
        self._build_system_page()
        self._build_tactical_page()
        self._build_benchmark_page()
        self._select_profile()
        self._load_saved_system_scan()
        self._show_analyzer_tab("Übersicht")
        self._show_page("Analyzer", record_history=False)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build_analyzer_result_projection(self, parent) -> None:
        """Build the reference-locked Analyzer result hierarchy.

        The widgets remain deliberately neutral until a validated workflow is
        loaded.  They are then filled from ``analysis-flow.json`` by
        ``_render_analyzer_result_projection``; no score or coaching result is
        invented merely to resemble the visual master.
        """
        section = self.ttk.Frame(parent, style="Content.TFrame")
        section.pack(fill="x", pady=(18, 0))
        self.analyzer_result_section = section
        header = self.ttk.Frame(section, style="Content.TFrame")
        header.pack(fill="x", pady=(0, 8))
        self.ttk.Label(header, text="ANALYSE", style="SectionTitle.TLabel").pack(side="left")
        self.analyzer_result_state = self.tk.StringVar(value="Demo und objektive Szenen noch nicht geladen")
        self.ttk.Label(header, textvariable=self.analyzer_result_state, style="StatusBadge.TLabel").pack(side="right")
        self.analyzer_projection_review_button = self.ttk.Button(
            header, text="Review öffnen", command=self._open_review, state="disabled"
        )
        self.analyzer_projection_review_button.pack(side="right", padx=(0, 8))
        self.analyzer_projection_setup_button = self.ttk.Button(
            header, text="Analyse konfigurieren", command=self._show_analyzer_setup
        )
        self.analyzer_projection_setup_button.pack(side="right", padx=(0, 8))

        # This is deliberately a presentation-only flow rail.  It makes the
        # already existing analysis -> embedded review transition visible in
        # the result state without inventing a second Analyzer or any values.
        flow_rail = self.ttk.Frame(section, style="Card.TFrame", padding=(14, 10))
        flow_rail.pack(fill="x", pady=(0, 12))
        self.ttk.Label(flow_rail, text="ANALYSE", style="StatusBadge.TLabel").pack(side="left")
        self.ttk.Label(flow_rail, text="→", style="Muted.TLabel").pack(side="left", padx=8)
        self.ttk.Label(flow_rail, text="REVIEW", style="Card.TLabel", font=(self.display_font, 9, "bold")).pack(side="left")
        self.analyzer_flow_context = self.tk.StringVar(value="Demo und Analyseprofil noch nicht geladen")
        self.ttk.Label(flow_rail, textvariable=self.analyzer_flow_context, style="Muted.TLabel", justify="right").pack(side="right")

        top = self.ttk.Frame(section, style="Content.TFrame")
        top.pack(fill="x")
        overview = self.ttk.Frame(top, style="Card.TFrame", padding=16)
        overview.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.ttk.Label(overview, text="ÜBERSICHT", style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.analyzer_overview = self.tk.StringVar(value="Noch keine belastbare Demoanalyse verfügbar.")
        self.ttk.Label(overview, textvariable=self.analyzer_overview, style="Muted.TLabel", justify="left", wraplength=240).pack(anchor="w", pady=(10, 0))

        findings = self.ttk.Frame(top, style="Card.TFrame", padding=16)
        findings.pack(side="left", fill="both", expand=True, padx=6)
        self.ttk.Label(findings, text="SCHLÜSSELBEFUNDE", style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.analyzer_findings = self.tk.StringVar(value="Nur objektiv belegte Szenenanker werden hier aufgeführt.")
        self.ttk.Label(findings, textvariable=self.analyzer_findings, style="Muted.TLabel", justify="left", wraplength=240).pack(anchor="w", pady=(10, 0))

        patterns = self.ttk.Frame(top, style="Card.TFrame", padding=16)
        patterns.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.ttk.Label(patterns, text="WIEDERKEHRENDE MUSTER", style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.analyzer_patterns = self.tk.StringVar(value="Keine Musterbewertung, solange keine dafür definierte Regel vorliegt.")
        self.ttk.Label(patterns, textvariable=self.analyzer_patterns, style="Muted.TLabel", justify="left", wraplength=240).pack(anchor="w", pady=(10, 0))

        middle = self.ttk.Frame(section, style="Content.TFrame")
        middle.pack(fill="x", pady=(12, 0))
        situations = self.ttk.Frame(middle, style="Card.TFrame", padding=16)
        situations.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.ttk.Label(situations, text="ERKANNTE SITUATIONEN", style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.analyzer_situations = self.tk.StringVar(value="Nach der Analyse stehen hier die ersten zusammengeführten Szenen.")
        self.ttk.Label(situations, textvariable=self.analyzer_situations, style="Muted.TLabel", justify="left", wraplength=340).pack(anchor="w", pady=(10, 0))
        self.analyzer_projection_scenes_button = self.ttk.Button(
            situations, text="Szenen im Review öffnen", command=self._open_review, state="disabled"
        )
        self.analyzer_projection_scenes_button.pack(anchor="w", pady=(12, 0))

        next_steps = self.ttk.Frame(middle, style="Card.TFrame", padding=16)
        next_steps.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.ttk.Label(next_steps, text="NÄCHSTE SCHRITTE", style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.analyzer_next_steps = self.tk.StringVar(value="Review öffnen, eine Szene auswählen und den belegten Tick lokal prüfen.")
        self.ttk.Label(next_steps, textvariable=self.analyzer_next_steps, style="Muted.TLabel", justify="left", wraplength=340).pack(anchor="w", pady=(10, 0))

        lower = self.ttk.Frame(section, style="Content.TFrame")
        lower.pack(fill="x", pady=(12, 0))
        strengths = self.ttk.Frame(lower, style="Card.TFrame", padding=14)
        strengths.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.ttk.Label(strengths, text="STÄRKEN", style="Card.TLabel", font=(self.display_font, 9, "bold")).pack(anchor="w")
        self.analyzer_strengths = self.tk.StringVar(value="Nicht automatisch abgeleitet")
        self.ttk.Label(strengths, textvariable=self.analyzer_strengths, style="Muted.TLabel", wraplength=210).pack(anchor="w", pady=(8, 0))
        weaknesses = self.ttk.Frame(lower, style="Card.TFrame", padding=14)
        weaknesses.pack(side="left", fill="both", expand=True, padx=4)
        self.ttk.Label(weaknesses, text="SCHWÄCHEN", style="Card.TLabel", font=(self.display_font, 9, "bold")).pack(anchor="w")
        self.analyzer_weaknesses = self.tk.StringVar(value="Nicht automatisch abgeleitet")
        self.ttk.Label(weaknesses, textvariable=self.analyzer_weaknesses, style="Muted.TLabel", wraplength=210).pack(anchor="w", pady=(8, 0))
        ruleset = self.ttk.Frame(lower, style="Card.TFrame", padding=14)
        ruleset.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.ttk.Label(ruleset, text="REGELSET & KONTEXT", style="Card.TLabel", font=(self.display_font, 9, "bold")).pack(anchor="w")
        self.analyzer_ruleset = self.tk.StringVar(value="Objektive V1-Regeln · Profil wird nach dem Laden angezeigt")
        self.ttk.Label(ruleset, textvariable=self.analyzer_ruleset, style="Muted.TLabel", wraplength=240).pack(anchor="w", pady=(8, 0))

    def _show_analyzer_setup(self) -> None:
        """Open the existing configuration controls in the unified Analyse tab."""
        self.analyzer_setup_expanded = True
        self._show_analyzer_tab("Analyse")
        self.analyzer_canvas.yview_moveto(0)

    def _set_analyzer_result_mode(self, result: ShellResult) -> None:
        """Preserve the user's chosen Analyzer tab after a local result update."""
        del result

    def _show_analyzer_tab(self, tab_name: str) -> None:
        """Switch the unified Analyzer without creating a second workflow."""
        if tab_name not in self.analyzer_tabs:
            raise ValueError(f"unknown analyzer tab: {tab_name}")
        for name, tab in self.analyzer_tabs.items():
            if name == tab_name:
                tab.pack(fill="both", expand=True)
            else:
                tab.pack_forget()
        self.analyzer_active_tab = tab_name
        for name, button in self.analyzer_tab_buttons.items():
            button.configure(style="Primary.TButton" if name == tab_name else "TButton")
        if hasattr(self, "analyzer_canvas"):
            self.root.after_idle(lambda: self.analyzer_canvas.yview_moveto(0.0))

    def _render_analyzer_result_projection(self, result: ShellResult) -> None:
        if result.status != "READY_FOR_REVIEW":
            self.analyzer_result_state.set("Auswahl bereit · Szenen entstehen erst nach Analyse")
            self.analyzer_flow_context.set("Demo laden → Auswahl → objektive Analyse → eingebettetes Review")
            self.analyzer_overview.set("Demo ist eingelesen. Nach der expliziten Analyse werden hier nur belegte Daten gezeigt.")
            self.analyzer_findings.set("Noch keine zusammengeführten Szenen vorhanden.")
            self.analyzer_situations.set("Keine analysierten Szenen vorhanden.")
            self.analyzer_patterns.set("Keine Musterbewertung ohne definierte Regel und belastbare Evidenz.")
            return
        try:
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            flow_path = result.manifest_path.parent / str(manifest["artifacts"]["analysis_flow"])
            projection = analyzer_result_projection(result, json.loads(flow_path.read_text(encoding="utf-8")))
        except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
            self.analyzer_result_state.set("Ergebnisdaten nicht verfügbar")
            self.analyzer_flow_context.set("Analyse bleibt lokal · Ergebnisdaten nicht darstellbar")
            self.analyzer_overview.set(f"Die Analyse bleibt unverändert; Ergebnisprojektion konnte nicht geladen werden: {error}")
            self.analyzer_findings.set("Keine nicht verifizierten Ersatzwerte angezeigt.")
            self.analyzer_situations.set("Keine Szenenprojektion verfügbar.")
            return
        self.analyzer_result_state.set(f"{projection['scene_count']} Szenen · lokal verifiziert")
        self.analyzer_flow_context.set(
            f"{projection['map_id']} · {projection['round_count']} Runden · "
            f"Profil {projection['profile_id']} · {projection['scene_count']} Szenen"
        )
        self.analyzer_overview.set(
            f"{projection['map_id']}\n{projection['round_count']} Runden · {projection['player_count']} Spieler\n"
            f"{projection['event_count']} grundlegende Events · keine Gesamtscore-Bewertung"
        )
        anchors = projection["anchor_summary"]
        self.analyzer_findings.set(
            f"{projection['scene_count']} zusammengeführte Szenen\n" +
            (" · ".join(f"{item['anchor']}: {item['count']}" for item in anchors) if anchors else "Keine benannten Szenenanker")
        )
        situations = projection["situations"]
        self.analyzer_situations.set(
            "\n".join(f"{item['title']} · {item['detail']}" for item in situations)
            if situations else "Die Auswahl erzeugte keine Szene."
        )
        self.analyzer_patterns.set(
            "V1 fasst objektive Marker zu Szenen zusammen. Wiederkehrende Muster, Stärken und Schwächen werden nicht ohne eigene Regel abgeleitet."
        )
        self.analyzer_strengths.set("Nicht automatisch abgeleitet · keine Coachingbewertung im aktiven Profil")
        self.analyzer_weaknesses.set("Nicht automatisch abgeleitet · keine negative Bewertung aus einzelnen Markern")
        self.analyzer_ruleset.set(
            f"Profil {projection['profile_id']} · {analysis_profile_criteria_view(self.controller.profiles[self.controller.profile_id])['text']}\n"
            "Objektive Regeln · lokale Datenquelle"
        )

    def _build_embedded_review(self, parent) -> None:
        review = self.ttk.Frame(parent, style="Content.TFrame", padding=(0, 0, 0, 0))
        self.embedded_review_frame = review
        header = self.ttk.Frame(review, style="Content.TFrame")
        header.pack(fill="x")
        self.ttk.Button(header, text="← Analyse", command=self._close_embedded_review).pack(side="left")
        self.ttk.Label(header, text="Analyzer Review", style="PageTitle.TLabel").pack(side="left", padx=16)
        self.ttk.Label(header, text="LOCAL · EINGEBETTET", style="StatusBadge.TLabel").pack(side="right")
        self.ttk.Label(
            review,
            text="Szenen, Evidenz und Notizen aus derselben Analyse · Tick-Sprung über den geprüften lokalen Coordinator",
            foreground=_THEME["muted"],
        ).pack(anchor="w", pady=(4, 14))
        self.embedded_review_boundary = self.tk.StringVar(value="FAKTEN / HINWEISE / DATENLIMITS / NÄCHSTE SCHRITTE: Review noch nicht geladen · SYSTEM CHECK: UNKNOWN / NOT AVAILABLE")
        self.ttk.Label(review, textvariable=self.embedded_review_boundary, style="Muted.TLabel", justify="left", wraplength=940).pack(anchor="w", pady=(0, 12))

        body = self.ttk.Frame(review, style="Content.TFrame")
        body.pack(fill="both", expand=True)
        left = self.ttk.Frame(body, style="Card.TFrame", padding=14)
        left.pack(side="left", fill="y", padx=(0, 10))
        self.ttk.Label(left, text="SZENEN", style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.embedded_scene_list = self.tk.Listbox(
            left, width=36, height=25, background=_THEME["deep"], foreground=_THEME["ink"],
            selectbackground=_THEME["metal"], selectforeground=_THEME["ink"],
            borderwidth=0, highlightthickness=1, highlightbackground=_THEME["line_soft"],
            highlightcolor=_THEME["ice"], activestyle="none", font=("Segoe UI", 10),
        )
        self.embedded_scene_list.pack(fill="y", expand=True, pady=(10, 0))
        self.embedded_scene_list.bind("<<ListboxSelect>>", self._select_embedded_scene)

        detail = self.ttk.Frame(body, style="Card.TFrame", padding=20)
        detail.pack(side="left", fill="both", expand=True)
        self.ttk.Label(detail, textvariable=self.embedded_scene_title, style="Card.TLabel", font=(self.display_font, 14, "bold")).pack(anchor="w")
        self.ttk.Label(detail, textvariable=self.embedded_scene_context, style="Muted.TLabel", wraplength=440, justify="left").pack(anchor="w", pady=(8, 0))
        self.ttk.Label(detail, textvariable=self.embedded_scene_players, style="Card.TLabel", wraplength=440, justify="left").pack(anchor="w", pady=(14, 0))
        self.ttk.Label(detail, textvariable=self.embedded_scene_rules, style="Muted.TLabel", wraplength=440, justify="left").pack(anchor="w", pady=(6, 16))

        state_row = self.ttk.Frame(detail, style="CardInner.TFrame")
        state_row.pack(fill="x")
        self.ttk.Label(state_row, text="Review-Status", style="Card.TLabel").pack(side="left")
        self.embedded_state = self.ttk.Combobox(
            state_row, state="readonly", width=18,
            values=("unreviewed", "reviewed", "follow-up", "discarded", "clip-worthy"),
        )
        self.embedded_state.pack(side="left", padx=10)
        self.ttk.Label(detail, text="Notiz", style="Card.TLabel").pack(anchor="w", pady=(16, 6))
        self.embedded_note = self.tk.Text(
            detail, height=7, wrap="word", background=_THEME["deep"], foreground=_THEME["ink"],
            insertbackground=_THEME["ice"], selectbackground=_THEME["metal"],
            borderwidth=0, relief="flat", highlightthickness=1, highlightbackground=_THEME["line_soft"],
            font=("Segoe UI", 10),
        )
        self.embedded_note.pack(fill="x")
        buttons = self.ttk.Frame(detail, style="CardInner.TFrame")
        buttons.pack(fill="x", pady=(14, 0))
        for column in range(3):
            buttons.columnconfigure(column, weight=1)
        self.ttk.Button(buttons, text="Status & Notiz speichern", command=self._save_embedded_review).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.ttk.Button(buttons, text="In CS2 ansehen", style="Primary.TButton", command=self._open_embedded_in_cs2).grid(row=0, column=1, sticky="ew", padx=4)
        self.ttk.Button(buttons, text="Tactical Replay", command=self._open_tactical_from_review).grid(row=0, column=2, sticky="ew", padx=(4, 0))
        self.ttk.Button(buttons, text="← Vorherige", command=lambda: self._step_embedded_scene(-1)).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.ttk.Button(buttons, text="Nächste →", command=lambda: self._step_embedded_scene(1)).grid(row=1, column=2, sticky="e", pady=(8, 0))
        self.ttk.Label(
            detail, textvariable=self.embedded_cs2_status, style="Muted.TLabel", wraplength=440, justify="left"
        ).pack(anchor="w", pady=(18, 0))
        self.ttk.Button(
            detail, text="HTML-Export im Browser (Fallback)", command=self._open_review_fallback
        ).pack(anchor="w", pady=(12, 0))

    def _show_page(self, name: str, *, record_history: bool = True) -> None:
        if name not in self.page_hosts:
            raise ValueError(f"unknown page: {name}")
        if record_history and self.current_page and self.current_page != name:
            self.page_history.append(self.current_page)
        self.current_page = name
        self.page_hosts[name].tkraise()
        if hasattr(self, "optimizer_master_canvas"):
            if name == "System Check / Optimizer":
                self._show_optimizer_master_overlay()
            else:
                self.optimizer_master_canvas.place_forget()
        if name == "Dashboard":
            self.root.after_idle(lambda: self.dashboard_canvas.yview_moveto(0.0))
        elif name == "System Check / Optimizer" and self.system_canvas is not None:
            self.root.after_idle(lambda: self.system_canvas.yview_moveto(0.0))
        elif name == "Tactical Replay" and self.embedded_tactical is None:
            self._show_tactical_empty_state()
        for page_name, button in self.nav_buttons.items():
            button.set_active(page_name == name)
        self.history_button.configure(state="normal" if self.page_history else "disabled")

    def _go_back(self) -> None:
        """Return across ordinary top-level pages without replacing special flows."""
        if not self.page_history:
            return
        previous = self.page_history.pop()
        self._show_page(previous, record_history=False)

    def _show_analyzer_overview(self) -> None:
        """Enter the one Analyzer workflow at its honest demo-preflight step."""
        self._show_page("Analyzer")
        self._show_analyzer_tab("Übersicht")

    def _build_dashboard_page(self) -> None:
        page = self.pages["Dashboard"]
        home_line = self.tk.Canvas(page, height=10, background=_THEME["night"], highlightthickness=0, bd=0)
        home_line.pack(fill="x", pady=(0, 10))
        home_line.bind("<Configure>", lambda event: self._draw_home_tech_line(home_line, event.width, event.height))
        header = self.ttk.Frame(page, style="Content.TFrame")
        header.pack(fill="x", pady=(0, 12))
        greeting = self.ttk.Frame(header, style="Content.TFrame")
        greeting.pack(side="left", fill="x", expand=True)
        self.ttk.Label(greeting, text="LOCAL PERFORMANCE LAB  /  COMMAND CENTER", style="HomeKicker.TLabel").pack(anchor="w", pady=(0, 3))
        self.ttk.Label(greeting, text="Willkommen zurück!", font=(self.display_font, 22, "bold")).pack(anchor="w")
        self.ttk.Label(
            greeting, text="Dein lokales Command Center für Analyse, Review und kontinuierliche Verbesserung.",
            foreground=_THEME["muted"],
        ).pack(anchor="w", pady=(2, 0))
        stats = self.ttk.Frame(header, style="Content.TFrame")
        stats.pack(side="right")
        self.dashboard_header = header
        self.dashboard_greeting = greeting
        self.dashboard_stats = stats
        stat_accents = ("#23d8bb", "#30aef4", "#a687ff", "#ffcf5a")
        for index, (variable, accent) in enumerate(zip((self.dashboard_readiness, self.dashboard_rounds, self.dashboard_players, self.dashboard_scenes), stat_accents)):
            card = RoundedHomeSurface(
                self.tk, self.ttk, stats, style="HomeStat.TFrame", fill=_THEME["panel"], outline=_THEME["border"], padding=(0, 7), min_height=58, min_width=104 if index == 0 else 62,
            )
            card.pack(side="left", padx=(6, 0))
            self._home_accent(card.body, accent)
            self.ttk.Label(card.body, textvariable=variable, style="HomeStat.TLabel", justify="center", font=(self.ui_font, 9, "bold")).pack(pady=(4, 0))

        modules = self.ttk.Frame(page, style="Content.TFrame")
        modules.pack(fill="x")
        self.dashboard_module_grid = modules
        self.dashboard_module_cards = []
        module_specs = (
            ("◎", "IMPROVE\nANALYZER", "Demos, Szenen und Evidenz aus einer gemeinsamen lokalen Replay-Wahrheit prüfen.", "Analyzer öffnen", "Analyzer", True, "#2bdcbb", "HomeTeal.TButton"),
            ("♙", "DEMO\nWORKFLOW", "Demo laden, Parserstatus und Line-ups innerhalb des Analyzer prüfen.", "Demo laden", "Analyzer", True, "#a687ff", "HomeViolet.TButton"),
            ("⚔", "2D\nTACTICAL", "Rundenpositionen aus derselben Replay-Wahrheit ansehen.", "Replay öffnen", "Tactical Replay", True, "#2db8ff", "HomePrimary.TButton"),
            ("◉", "IMPROVE\nOPTIMIZER", "Systemfakten sicher und read-only erfassen.", "System prüfen", "System Check / Optimizer", True, "#ffcc54", "HomeGold.TButton"),
            ("▥", "IMPROVE\nBENCHMARK", "Separater, derzeit geparkter Arbeitsstrang.", "Nicht in diesem Slice", "", False, "#6587a0", "HomePrimary.TButton"),
            ("◯", "MY\nIMPROVEMENT", "Lokale Reports und aktuelle Analyseartefakte öffnen.", "Übersicht öffnen", "My Improvement", True, "#238ffc", "HomePrimary.TButton"),
        )
        for column, (icon, title, detail, action, target, enabled, accent, button_style) in enumerate(module_specs):
            modules.columnconfigure(column, weight=1, uniform="home-modules")
            card = RoundedHomeSurface(
                self.tk, self.ttk, modules, style="HomeModule.TFrame", fill=_THEME["panel"], outline=_THEME["border"], padding=7, min_height=196, radius=8,
            )
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 3, 0 if column == 5 else 3))
            card.columnconfigure(0, weight=1)
            # One shared vertical grid keeps every action in the same card row.
            # Description height may vary; only the spacer absorbs that variance.
            card.rowconfigure(3, weight=1)
            self.dashboard_module_cards.append(card)
            self._home_accent(card.body, accent, pack=False).grid(row=0, column=0, sticky="ew")
            icon_row = self.ttk.Frame(card.body, style="HomeModule.TFrame")
            icon_row.grid(row=1, column=0, sticky="ew", pady=(5, 6))
            self._home_module_icon(icon_row, icon, accent).pack(side="left", padx=(0, 8))
            self.ttk.Label(icon_row, text=title, style="HomeModule.TLabel", font=(self.display_font, 9, "bold"), justify="left").pack(side="left", anchor="w")
            self.ttk.Label(card.body, text=detail, style="HomeMuted.TLabel", wraplength=150, justify="left").grid(row=2, column=0, sticky="ew", pady=(2, 10))
            self.ttk.Frame(card.body, style="HomeModule.TFrame").grid(row=3, column=0, sticky="nsew")
            RoundedHomeAction(
                self.tk, card.body, text=action, accent=accent,
                command=(self._show_analyzer_overview if target == "Analyzer" else lambda value=target: self._show_page(value)), enabled=enabled,
                font=(self.ui_font, 9, "bold"),
            ).grid(row=4, column=0, sticky="ew")

        overview = self.ttk.Frame(page, style="Content.TFrame")
        overview.pack(fill="x", pady=(12, 0))
        overview.columnconfigure(0, weight=5, uniform="home-overview")
        overview.columnconfigure(1, weight=5, uniform="home-overview")
        overview.columnconfigure(2, weight=6, uniform="home-overview")

        system_scan = RoundedHomeSurface(
            self.tk, self.ttk, overview, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"], padding=15, min_height=184,
        )
        system_scan.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._home_accent(system_scan.body, "#0A9AE7")
        self.ttk.Label(system_scan.body, text="LETZTER SYSTEMSCAN", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.ttk.Label(system_scan.body, textvariable=self.dashboard_system_scan_time, style="HomePanelMuted.TLabel", wraplength=210, justify="left").pack(anchor="w", pady=(5, 4))
        system_grid = self.ttk.Frame(system_scan.body, style="HomeInner.TFrame")
        system_grid.pack(fill="x", pady=(2, 5))
        system_labels = (("cpu", "CPU"), ("gpu", "GPU"), ("memory", "RAM"), ("windows", "Windows"), ("drivers", "Treiber"), ("display", "Monitor"))
        for index, (key, label) in enumerate(system_labels):
            cell = self.ttk.Frame(system_grid, style="HomeMetric.TFrame", padding=(5, 3))
            column = index % 3
            cell.grid(row=index // 3, column=column, sticky="ew", padx=(0 if column == 0 else 2, 0 if column == 2 else 2), pady=2)
            self.ttk.Label(cell, text=label, style="HomeMetricLabel.TLabel", font=(self.ui_font, 7, "bold")).pack(anchor="w")
            self.ttk.Label(cell, textvariable=self.dashboard_system_scan_cells[key], style="HomeMetricValue.TLabel", wraplength=62, justify="left", font=(self.ui_font, 7)).pack(anchor="w")
            system_grid.columnconfigure(column, weight=1, uniform="system-scan")
        self.ttk.Label(system_scan.body, textvariable=self.dashboard_system_scan_overall, style="HomePanel.TLabel", wraplength=210, justify="left", font=(self.ui_font, 7, "bold")).pack(anchor="w", pady=(1, 4))
        self.dashboard_system_scan_details_button = self.ttk.Button(system_scan.body, text="Systemdetails anzeigen", style="HomePrimary.TButton", command=lambda: self._show_page("System Check / Optimizer"))
        self.dashboard_system_scan_details_button.pack(fill="x")
        self.dashboard_system_scan_attention_label = self.ttk.Label(system_scan.body, textvariable=self.dashboard_system_scan_attention, style="HomePanelMuted.TLabel", wraplength=210, justify="left", font=(self.ui_font, 7))

        progress = RoundedHomeSurface(
            self.tk, self.ttk, overview, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"], padding=15, min_height=184,
        )
        progress.grid(row=0, column=1, sticky="nsew", padx=5)
        self._home_accent(progress.body, "#2bdcbb")
        self.ttk.Label(progress.body, text="DEIN FORTSCHRITT – ÜBERBLICK", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        progress_body = self.ttk.Frame(progress.body, style="HomeInner.TFrame")
        progress_body.pack(fill="x", pady=(7, 5))
        self._home_progress_gauge(progress_body).pack(side="left", padx=(0, 9))
        self.ttk.Label(progress_body, textvariable=self.dashboard_progress_summary, style="HomePanelMuted.TLabel", wraplength=160, justify="left").pack(side="left", fill="x", expand=True)
        dimension_grid = self.ttk.Frame(progress.body, style="HomeInner.TFrame")
        dimension_grid.pack(fill="x", pady=(0, 6))
        for index, (label, variable) in enumerate(self.dashboard_progress_dimensions.items()):
            cell = self.ttk.Frame(dimension_grid, style="HomeMetric.TFrame", padding=(5, 3))
            column = index % 3
            cell.grid(row=index // 3, column=column, sticky="ew", padx=(0 if column == 0 else 2, 0 if column == 2 else 2), pady=2)
            self.ttk.Label(cell, text=label, style="HomeMetricLabel.TLabel", font=(self.ui_font, 7, "bold")).pack(anchor="w")
            self.ttk.Label(cell, textvariable=variable, style="HomeMetricValue.TLabel", font=(self.ui_font, 7)).pack(anchor="w")
            dimension_grid.columnconfigure(column, weight=1, uniform="progress-dimensions")
        # Keep the progress action in the same clearly selected, outlined
        # action language as the six primary module cards.
        self.dashboard_progress_action = RoundedHomeAction(
            self.tk, progress.body, text="Zum Analyzer", accent="#2bdcbb",
            command=self._show_analyzer_overview, enabled=True,
            font=(self.ui_font, 9, "bold"),
        )
        self.dashboard_progress_action.pack(fill="x")

        recent = RoundedHomeSurface(
            self.tk, self.ttk, overview, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"], padding=15, min_height=184,
        )
        recent.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        self._home_accent(recent.body, "#a687ff")
        self.ttk.Label(recent.body, text="LETZTE ANALYSEN", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.ttk.Label(recent.body, textvariable=self.dashboard_recent, style="HomePanelMuted.TLabel", wraplength=230, justify="left").pack(anchor="w", pady=(10, 8))
        self.ttk.Label(recent.body, textvariable=self.overview_status, style="HomePanel.TLabel", wraplength=230, justify="left").pack(anchor="w")

        lower = self.ttk.Frame(page, style="Content.TFrame")
        lower.pack(fill="x", pady=(12, 16))
        lower.columnconfigure(0, weight=1, uniform="home-lower")
        lower.columnconfigure(1, weight=1, uniform="home-lower")
        idea = RoundedHomeSurface(
            self.tk, self.ttk, lower, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"], padding=15, min_height=116,
        )
        idea.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._home_accent(idea.body, "#2bdcbb")
        self.ttk.Label(idea.body, text="◉  DIE IDEE HINTER IMPROVE YOURSELF", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.ttk.Label(
            idea.body,
            text="Datenbasierte Analyse, gemeinsame Replay-Wahrheit und transparente lokale Werkzeuge begleiten dich Schritt für Schritt – ohne erfundene Ergebnisse.",
            style="HomePanelMuted.TLabel", wraplength=360, justify="left",
        ).pack(anchor="w", pady=(8, 0))
        community = RoundedHomeSurface(
            self.tk, self.ttk, lower, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"], padding=15, min_height=116,
        )
        community.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._home_accent(community.body, "#a687ff")
        self.ttk.Label(community.body, text="◇  COMMUNITY & IDEEN", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.ttk.Label(
            community.body,
            text="Der geschützte Kern bleibt lokal, nachvollziehbar und sicher. Community-Funktionen werden erst mit einem belegten Produktumfang ergänzt.",
            style="HomePanelMuted.TLabel", wraplength=360, justify="left",
        ).pack(anchor="w", pady=(8, 0))
        self.dashboard_modules = modules
        self.dashboard_overview = overview
        self.dashboard_lower = lower
        page.bind("<Configure>", lambda event: self._layout_dashboard(event.width))

    def _home_accent(self, parent: object, color: str, *, pack: bool = True) -> object:
        """Add the thin illuminated edge used throughout the Home master."""
        accent = self.tk.Frame(parent, height=3, background=color, borderwidth=0, highlightthickness=0)
        if pack:
            accent.pack(fill="x", anchor="n")
        return accent

    def _home_module_icon(self, parent: object, glyph: str, color: str) -> object:
        canvas = self.tk.Canvas(parent, width=31, height=31, background=_THEME["card"], highlightthickness=0, bd=0)
        canvas.create_oval(3, 3, 28, 28, outline=_THEME["border"], width=2)
        canvas.create_oval(7, 7, 24, 24, outline=color, width=1)
        canvas.create_line(15, 1, 15, 6, fill=color, width=1)
        canvas.create_line(15, 25, 15, 30, fill=color, width=1)
        canvas.create_text(15, 15, text=glyph, fill="#edf9ff", font=("Segoe UI Symbol", 11, "bold"))
        return canvas

    def _home_progress_gauge(self, parent: object) -> object:
        canvas = self.tk.Canvas(parent, width=56, height=56, background=_THEME["panel"], highlightthickness=0, bd=0)
        canvas.create_oval(4, 4, 52, 52, outline=_THEME["border"], width=4)
        canvas.create_arc(4, 4, 52, 52, start=88, extent=214, style="arc", outline="#2bdcbb", width=3)
        canvas.create_arc(10, 10, 46, 46, start=305, extent=82, style="arc", outline="#2d9fe8", width=2)
        canvas.create_text(28, 25, text="LOCAL", fill="#dff8ff", font=(self.display_font, 7))
        canvas.create_text(28, 35, text="FLOW", fill="#75b8d7", font=(self.display_font, 7))
        return canvas

    def _draw_home_tech_line(self, canvas: object, width: int, height: int) -> None:
        canvas.delete("all")
        baseline = max(1, height // 2)
        canvas.create_line(0, baseline, width, baseline, fill="#0B2638", width=1)
        for offset in range(-20, width + 40, 42):
            canvas.create_line(offset, height, offset + 18, 0, fill="#071B29", width=1)
            canvas.create_line(offset + 20, height, offset + 38, 0, fill="#061622", width=1)
        for x in range(12, width, 96):
            canvas.create_oval(x, baseline - 2, x + 4, baseline + 2, fill=_THEME["accent"], outline="")

    def _resize_scrollable_page(self, canvas: object, item: int, page: object, scrollbar: object, width: int) -> None:
        canvas.itemconfigure(item, width=width)
        self.root.after_idle(lambda: self._sync_scrollable_page(canvas, page, scrollbar))

    def _sync_scrollable_page(self, canvas: object, page: object, scrollbar: object) -> None:
        bounds = canvas.bbox("all")
        if bounds is None:
            return
        canvas.configure(scrollregion=bounds)
        needs_scroll = (bounds[3] - bounds[1]) > canvas.winfo_height() + 1
        shown = bool(scrollbar.winfo_manager())
        if needs_scroll and not shown:
            scrollbar.pack(side="right", fill="y")
        elif shown and not needs_scroll:
            scrollbar.pack_forget()
            canvas.yview_moveto(0.0)

    def _layout_dashboard(self, width: int) -> None:
        compact, module_height, overview_height, lower_height, gap = dashboard_layout_metrics(
            width, self.dashboard_canvas.winfo_height()
        )
        self.dashboard_compact = compact
        self.dashboard_greeting.pack_forget()
        self.dashboard_stats.pack_forget()
        if compact:
            self.dashboard_greeting.pack(fill="x")
            self.dashboard_stats.pack(anchor="w", pady=(10, 0))
        else:
            self.dashboard_greeting.pack(side="left", fill="x", expand=True)
            self.dashboard_stats.pack(side="right")
        columns = 3 if compact else 6
        for column in range(6):
            self.dashboard_module_grid.columnconfigure(column, weight=0, uniform="")
        for column in range(columns):
            self.dashboard_module_grid.columnconfigure(column, weight=1, uniform="home-modules")
        for index, card in enumerate(self.dashboard_module_cards):
            row, column = divmod(index, columns)
            card.grid_configure(
                row=row, column=column, sticky="nsew",
                padx=(0 if column == 0 else 3, 0 if column == columns - 1 else 3),
                pady=(0 if row == 0 else 6, 0),
            )
        self.dashboard_modules.rowconfigure(0, minsize=module_height)
        self.dashboard_modules.rowconfigure(1, minsize=module_height if compact else 0)
        self.dashboard_overview.rowconfigure(0, minsize=overview_height)
        self.dashboard_lower.rowconfigure(0, minsize=lower_height)
        self.dashboard_header.pack_configure(pady=(0, gap))
        self.dashboard_overview.pack_configure(pady=(gap, 0))
        self.dashboard_lower.pack_configure(pady=(gap, gap + 4))

    def _build_reports_page(self) -> None:
        page = self.pages["Reports"]
        self.ttk.Label(page, text="Reports", style="PageTitle.TLabel").pack(anchor="w")
        self.ttk.Label(page, text="Nachvollziehbare Ergebnisse aus der aktuellen lokalen Analyse", foreground=_THEME["muted"]).pack(anchor="w", pady=(2, 14))
        card = self.ttk.Frame(page, style="Card.TFrame", padding=20)
        card.pack(fill="x")
        self.ttk.Label(card, text="ANALYSEBERICHT", style="Card.TLabel", font=(self.display_font, 11, "bold")).pack(anchor="w")
        self.ttk.Label(card, textvariable=self.report_status, style="Muted.TLabel", wraplength=800, justify="left").pack(anchor="w", pady=(8, 14))
        actions = self.ttk.Frame(card, style="CardInner.TFrame")
        actions.pack(fill="x")
        self.report_button = self.ttk.Button(actions, text="Report JSON öffnen", command=lambda: self._open_artifact("report"), state="disabled")
        self.report_button.pack(side="left")
        self.timeline_button = self.ttk.Button(actions, text="Timeline JSON öffnen", command=lambda: self._open_artifact("timeline"), state="disabled")
        self.timeline_button.pack(side="left", padx=8)

    def _reference_page_header(self, page, title: str, subtitle: str) -> None:
        """Shared MASTER-screen heading; content remains deliberately truthful."""
        header = self.ttk.Frame(page, style="Content.TFrame")
        header.pack(fill="x", pady=(0, 16))
        self.ttk.Label(header, text=title, style="PageTitle.TLabel").pack(anchor="w")
        self.ttk.Label(header, text=subtitle, style="Muted.TLabel", wraplength=1100, justify="left").pack(anchor="w", pady=(3, 0))

    def _reference_info_card(
        self,
        parent,
        *,
        title: str,
        text: str | None = None,
        textvariable: object | None = None,
        accent: str = "#13A7E8",
        min_height: int = 148,
    ) -> object:
        card = RoundedHomeSurface(
            self.tk, self.ttk, parent, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"],
            padding=16, min_height=min_height, radius=10,
        )
        self._home_accent(card.body, accent)
        self.ttk.Label(card.body, text=title, style="HomePanel.TLabel", font=(self.display_font, 9, "bold")).pack(anchor="w", pady=(8, 0))
        label_options: dict[str, object] = {"style": "HomePanelMuted.TLabel", "wraplength": 310, "justify": "left"}
        if textvariable is not None:
            label_options["textvariable"] = textvariable
        else:
            label_options["text"] = text or ""
        self.ttk.Label(card.body, **label_options).pack(anchor="w", pady=(10, 0))
        return card

    def _build_my_improvement_page(self) -> None:
        page = self.pages["My Improvement"]
        header = self.ttk.Frame(page, style="Content.TFrame")
        header.pack(fill="x", pady=(0, 10))
        self.ttk.Label(header, text="Meine Entwicklung", style="PageTitle.TLabel").pack(side="left")
        evidence_state = self.ttk.Frame(header, style="CardInner.TFrame", padding=(12, 7))
        evidence_state.pack(side="right")
        self.ttk.Label(evidence_state, text="VERGLEICHSEVIDENZ", style="PageKicker.TLabel").pack(anchor="w")
        self.ttk.Label(evidence_state, text="Noch nicht verfügbar", style="Muted.TLabel").pack(anchor="w", pady=(2, 0))
        self.ttk.Label(
            page,
            text="Echte Entwicklung wird erst aus mehreren lokalen Analysen abgeleitet. Bis dahin bleiben Trends, Scores und Fokusbereiche ausdrücklich unbekannt.",
            style="Muted.TLabel", wraplength=1100, justify="left",
        ).pack(anchor="w", pady=(0, 10))
        period = self.ttk.Frame(page, style="Content.TFrame")
        period.pack(fill="x", pady=(0, 12))
        self.ttk.Label(period, text="ZEITRAUM", style="PageKicker.TLabel").pack(side="left", padx=(0, 10))
        self.ttk.Label(period, text="Lokale Analysen erforderlich", style="StatusBadge.TLabel").pack(side="left")
        summary = self.ttk.Frame(page, style="Content.TFrame")
        summary.pack(fill="x")
        self.improvement_summary = summary
        self.improvement_summary_cards: list[object] = []
        cards = (
            ("AIM", "#13A7E8"),
            ("DUELS", "#E25B5B"),
            ("UTILITY", "#A782E8"),
            ("POSITIONING / GAME SENSE", "#2BDCB9"),
            ("PERFORMANCE", "#E5B854"),
        )
        for index, (title, accent) in enumerate(cards):
            card = RoundedHomeSurface(
                self.tk, self.ttk, summary, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"],
                padding=(10, 14), min_height=230, radius=10,
            )
            self.improvement_summary_cards.append(card)
            self._home_accent(card.body, accent)
            self.ttk.Label(card.body, text=title, style="HomePanel.TLabel", font=(self.display_font, 9, "bold"), wraplength=190, justify="left").pack(anchor="w", pady=(8, 7))
            self.ttk.Label(card.body, text="Noch nicht bewertet", style="HomePanelMuted.TLabel").pack(anchor="w")
            self.ttk.Label(
                card.body, text="Verlauf erst mit vergleichbarer lokaler Evidenz.", style="HomePanelMuted.TLabel",
                wraplength=190, justify="left",
            ).pack(anchor="w", pady=(8, 14))
            metric_row = self.ttk.Frame(card.body, style="HomeInner.TFrame")
            metric_row.pack(fill="x", side="bottom")
            for metric_index, (metric_title, metric_value) in enumerate((("AKTUELL", "–"), ("VERGLEICH", "–"))):
                metric_row.columnconfigure(metric_index, weight=1, uniform="improvement-metrics")
                metric = self.ttk.Frame(metric_row, style="HomeInner.TFrame", padding=(2, 6))
                metric.grid(row=0, column=metric_index, sticky="nsew", padx=(0, 1) if metric_index == 0 else (1, 0))
                self.ttk.Label(metric, text=metric_title, style="PageKicker.TLabel").pack(anchor="w")
                self.ttk.Label(metric, text=metric_value, style="HomePanel.TLabel", font=(self.display_font, 12, "bold")).pack(anchor="w", pady=(2, 0))
        summary.bind("<Configure>", lambda event: self._layout_my_improvement_cards(event.width))
        self.root.after_idle(lambda: self._layout_my_improvement_cards(summary.winfo_width()))
        lower = self.ttk.Frame(page, style="Content.TFrame")
        lower.pack(fill="x", pady=(14, 0))
        for index, (title, text, accent) in enumerate((
            ("DEINE STÄRKEN", "Eine belastbare Stärkenbewertung benötigt mehrere echte lokale Analysen.", "#58D69A"),
            ("DEINE SCHWÄCHEN", "Keine Schwächen werden ohne nachvollziehbare lokale Analyse abgeleitet.", "#E25B5B"),
            ("NÄCHSTE FOKUS-BEREICHE", "Nach einer echten Analyse erscheinen hier nur belegte, nicht erfundene nächste Schritte.", "#13A7E8"),
        )):
            lower.columnconfigure(index, weight=1, uniform="improvement-lower")
            self._reference_info_card(lower, title=title, text=text, accent=accent, min_height=166).grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 5, 0 if index == 2 else 5))
        influenced = self._reference_info_card(
            page,
            title="SZENEN, DIE DEINE BEWERTUNG BEEINFLUSSEN",
            text="Noch keine bewertete Vergleichsbasis. Szenen werden erst gezeigt, wenn ihr Einfluss aus mehreren echten lokalen Analysen transparent abgeleitet werden kann.",
            accent="#13A7E8",
            min_height=132,
        )
        influenced.pack(fill="x", pady=(14, 0))

    def _layout_my_improvement_cards(self, width: int) -> None:
        """Keep comparison labels readable instead of squeezing five cards."""
        columns = 5 if width >= 1_000 else 3
        for column in range(5):
            self.improvement_summary.columnconfigure(
                column, weight=1 if column < columns else 0, uniform="improvement" if column < columns else ""
            )
        for index, card in enumerate(self.improvement_summary_cards):
            column, row = index % columns, index // columns
            card.grid(
                row=row, column=column, sticky="nsew",
                padx=(0 if column == 0 else 4, 0 if column == columns - 1 else 4),
                pady=(0 if row == 0 else 8, 0),
            )

    def _build_demo_analyzer_page(self, page) -> None:
        """Build the Overview tab of the unified Analyzer.

        The established demo-library controls stay local and fail closed; only
        their placement changes from a separate route to the documented
        Overview → Analyse → Review workflow.
        """
        self.ttk.Label(page, text="DEMO → ANALYSE → REVIEW", style="PageKicker.TLabel").pack(anchor="w", pady=(0, 4))
        self.ttk.Label(page, text="Demo-Bibliothek & ausgewählte Demo", style="SectionTitle.TLabel").pack(anchor="w")
        self.ttk.Label(page, text="Lokale CS2-Demos bewusst auswählen, belegte Fakten prüfen und danach mit demselben Replay analysieren.", style="Muted.TLabel").pack(anchor="w", pady=(4, 14))
        layout = self.ttk.Frame(page, style="Content.TFrame")
        layout.pack(fill="both", expand=True)
        self.demo_library_text = self.tk.StringVar(value="Keine lokale Demo ist automatisch ausgewählt. Wähle eine echte .dem oder .dem.zst bewusst aus.")
        library = self._reference_info_card(
            layout,
            title="DEMO BIBLIOTHEK",
            textvariable=self.demo_library_text,
            accent="#A782E8",
            min_height=204,
        )
        library.pack(side="left", fill="both", expand=True, padx=(0, 7))
        self.ttk.Button(library.body, text="Echte CS2-Demo auswählen", style="Primary.TButton", command=self._choose_demo).pack(fill="x", pady=(16, 0))
        self.demo_selected_text = self.tk.StringVar(value="Noch keine bestätigte lokale Demodatei geladen. Import- und Analyse-Status bleiben bis dahin ausdrücklich offen.")
        selected = self._reference_info_card(layout, title="AUSGEWÄHLTE DEMO", textvariable=self.demo_selected_text, accent="#13A7E8")
        selected.pack(side="left", fill="both", expand=True, padx=(7, 0))
        readiness = self.ttk.Frame(page, style="Content.TFrame")
        readiness.pack(fill="x", pady=(14, 0))
        self.demo_import_text = self.tk.StringVar(value="Keine Demo importiert.")
        self.demo_analysis_text = self.tk.StringVar(value="Keine Analyse gestartet.")
        self.demo_ready_text = self.tk.StringVar(value="Erfordert eine erfolgreich geladene echte Demo.")
        for index, (title, variable, accent) in enumerate((
            ("IMPORT-STATUS", self.demo_import_text, "#687789"),
            ("ANALYSE-STATUS", self.demo_analysis_text, "#687789"),
            ("BEREIT ZUR ANALYSE", self.demo_ready_text, "#58D69A"),
        )):
            readiness.columnconfigure(index, weight=1, uniform="demo-ready")
            self._reference_info_card(readiness, title=title, textvariable=variable, accent=accent).grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 5, 0 if index == 2 else 5))
        self.demo_overview_text = self.tk.StringVar(value="Nach dem bestätigten Import erscheinen hier ausschließlich aus dem Workflow belegte Demo-Fakten.")
        overview = self._reference_info_card(
            page,
            title="DEMO-ÜBERSICHT",
            textvariable=self.demo_overview_text,
            accent="#13A7E8",
            min_height=248,
        )
        overview.pack(fill="x", pady=(14, 0))
        demo_actions = self.ttk.Frame(overview.body, style="HomeInner.TFrame")
        demo_actions.pack(fill="x", pady=(14, 0))
        self.ttk.Button(demo_actions, text="Analyse konfigurieren", command=self._show_analyzer_setup).pack(side="left")
        self.demo_review_button = self.ttk.Button(demo_actions, text="Szenen im Review", command=self._open_review, state="disabled")
        self.demo_review_button.pack(side="left", padx=8)

    def _render_demo_analyzer_page(self, result: ShellResult) -> None:
        self.demo_library_text.set("Die aktuelle Auswahl stammt aus dem lokalen, fail-closed Workflow. Es werden keine Demos automatisch importiert oder kopiert.")
        self.demo_selected_text.set(
            f"{result.source_demo_name or 'Lokaler Workflow'}\n{result.map_id} · {result.round_count} Runden · {len(result.players)} Spieler\n"
            f"SHA-256 {result.source_sha256[:12]}…"
        )
        self.demo_import_text.set(f"Import bestätigt · Parser {result.parser_status}")
        if result.status == "READY_FOR_REVIEW":
            self.demo_analysis_text.set(f"Analyse abgeschlossen · {result.scene_count} zusammengeführte Szenen")
            self.demo_ready_text.set("Bereit für den lokalen Review; Tick-Sprung bleibt separat abgesichert.")
            self.demo_overview_text.set(
                f"{result.map_id} · {result.round_count} Runden · {len(result.players)} Spieler · "
                f"{result.basic_event_count} grundlegende Events · {result.scene_count} zusammengeführte Szenen\n"
                "Kein Match-Score, K/D oder Performancevergleich vorhanden: Diese Werte werden nicht geschätzt."
            )
            self.demo_review_button.configure(state="normal")
        else:
            self.demo_analysis_text.set("Auswahl bereit · Analyse wurde noch nicht ausdrücklich gestartet.")
            self.demo_ready_text.set("Bereit für eine explizite Analyse im Improve Analyzer.")
            self.demo_overview_text.set(
                f"{result.map_id} · {result.round_count} Runden · {len(result.players)} Spieler · "
                f"{result.basic_event_count} grundlegende Events\n"
                "Szenen und Review entstehen erst nach der expliziten Analyse."
            )
            self.demo_review_button.configure(state="disabled")

    def _build_benchmark_page(self) -> None:
        page = self.pages["Benchmark"]
        self._reference_page_header(
            page, "Improve Benchmark",
            "Reproduzierbare, präzise und vergleichbare Performance-Tests erscheinen erst nach einer freigegebenen realen Map und einem tatsächlichen Lauf.",
        )
        top = self.ttk.Frame(page, style="Content.TFrame")
        top.pack(fill="x")
        top.columnconfigure(0, weight=3)
        top.columnconfigure(1, weight=5)
        top.columnconfigure(2, weight=4)

        start = RoundedHomeSurface(
            self.tk, self.ttk, top, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"],
            padding=16, min_height=266, radius=10,
        )
        start.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._home_accent(start.body, "#13A7E8")
        self.ttk.Label(start.body, text="BENCHMARK STARTEN", style="HomePanel.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w", pady=(8, 12))
        self.ttk.Label(start.body, text="Kein freigegebener Lauf", style="HomePanelMuted.TLabel").pack(anchor="w")
        self.ttk.Label(
            start.body,
            text="Der Test bleibt gesperrt, bis eine real gebaute Map und ein reproduzierbarer Ablauf bestätigt sind.",
            style="HomePanelMuted.TLabel", wraplength=260, justify="left",
        ).pack(anchor="w", pady=(8, 16))
        locked_action = self.ttk.Frame(start.body, style="HomeInner.TFrame", padding=(10, 8))
        locked_action.pack(fill="x", pady=(0, 10))
        self.ttk.Label(locked_action, text="LAUF GESPERRT", style="Muted.TLabel", justify="center").pack(anchor="center")
        profile = self.ttk.Frame(start.body, style="HomeInner.TFrame", padding=(10, 8))
        profile.pack(fill="x")
        self.ttk.Label(profile, text="TESTPROFIL", style="PageKicker.TLabel").pack(anchor="w")
        self.ttk.Label(profile, text="Nicht verfügbar", style="HomePanel.TLabel").pack(anchor="w", pady=(3, 0))

        result = RoundedHomeSurface(
            self.tk, self.ttk, top, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"],
            padding=16, min_height=266, radius=10,
        )
        result.grid(row=0, column=1, sticky="nsew", padx=6)
        self._home_accent(result.body, "#13A7E8")
        result_header = self.ttk.Frame(result.body, style="HomeInner.TFrame")
        result_header.pack(fill="x", pady=(8, 12))
        self.ttk.Label(result_header, text="AKTUELLES ERGEBNIS", style="HomePanel.TLabel", font=(self.display_font, 10, "bold")).pack(side="left")
        self.ttk.Label(result_header, text="Kein Lauf", style="Muted.TLabel").pack(side="right")
        metrics = self.ttk.Frame(result.body, style="HomeInner.TFrame")
        metrics.pack(fill="x")
        for index, title in enumerate(("Ø FPS", "1% LOW", "FRAMETIME (Ø)")):
            metrics.columnconfigure(index, weight=1, uniform="benchmark-metrics")
            metric = self.ttk.Frame(metrics, style="HomeInner.TFrame", padding=(10, 8))
            metric.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 4, 0 if index == 2 else 4))
            self.ttk.Label(metric, text=title, style="PageKicker.TLabel").pack(anchor="w")
            self.ttk.Label(metric, text="–", style="HomePanel.TLabel", font=(self.display_font, 18, "bold")).pack(anchor="w", pady=(7, 0))
            self.ttk.Label(metric, text="Nicht gemessen", style="HomePanelMuted.TLabel").pack(anchor="w", pady=(2, 0))
        chart = self.ttk.Frame(result.body, style="HomeInner.TFrame", padding=(10, 9))
        chart.pack(fill="x", pady=(12, 0))
        self.ttk.Label(chart, text="FPS-VERLAUF", style="PageKicker.TLabel").pack(anchor="w")
        self.ttk.Label(chart, text="Kein gemessener Verlauf verfügbar.", style="HomePanelMuted.TLabel", wraplength=450, justify="left").pack(anchor="w", pady=(5, 0))

        map_card = RoundedHomeSurface(
            self.tk, self.ttk, top, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"],
            padding=16, min_height=266, radius=10,
        )
        map_card.grid(row=0, column=2, sticky="nsew", padx=(6, 0))
        self._home_accent(map_card.body, "#E5B854")
        self.ttk.Label(map_card.body, text="BENCHMARK MAP", style="HomePanel.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w", pady=(8, 12))
        map_placeholder = self.ttk.Frame(map_card.body, style="HomeInner.TFrame", padding=14)
        map_placeholder.pack(fill="x")
        self.ttk.Label(map_placeholder, text="Keine Kartenbasis", style="HomePanel.TLabel").pack(anchor="w")
        self.ttk.Label(
            map_placeholder,
            text="Die bestehende Benchmark-Arbeit bleibt außerhalb dieses UI-Passes unverändert. Es wird kein Kartenbild oder Map-Status vorgetäuscht.",
            style="HomePanelMuted.TLabel", wraplength=280, justify="left",
        ).pack(anchor="w", pady=(8, 0))
        self.ttk.Label(map_card.body, text="VERSION / DATUM / API: nicht bestätigt", style="Muted.TLabel", wraplength=280, justify="left").pack(anchor="w", pady=(12, 0))

        middle = RoundedHomeSurface(
            self.tk, self.ttk, page, style="HomePanel.TFrame", fill=_THEME["panel"], outline=_THEME["border"],
            padding=16, min_height=172, radius=10,
        )
        middle.pack(fill="x", pady=(14, 0))
        self._home_accent(middle.body, "#13A7E8")
        self.ttk.Label(middle.body, text="BENCHMARK SZENEN – TESTABLAUF", style="HomePanel.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w", pady=(8, 7))
        self.ttk.Label(
            middle.body,
            text="Kein gebauter oder freigegebener Szenenablauf verfügbar. Reproduzierbare Schritte, Dauer und Resultate werden erst nach dem realen Build dargestellt.",
            style="HomePanelMuted.TLabel", wraplength=1050, justify="left",
        ).pack(anchor="w")
        self.ttk.Label(middle.body, text="Gesamtdauer: nicht gemessen", style="Muted.TLabel").pack(anchor="w", pady=(13, 0))

        explain = self.ttk.Frame(page, style="Content.TFrame")
        explain.pack(fill="x", pady=(14, 0))
        explain.columnconfigure(0, weight=3)
        explain.columnconfigure(1, weight=1)
        why = self._reference_info_card(
            explain, title="WARUM IMPROVE BENCHMARK?",
            text="Reproduzierbar, präzise und vergleichbar: Erst reale, identische Bedingungen können eine belastbare Messung und spätere Einordnung ermöglichen.",
            accent="#13A7E8", min_height=130,
        )
        why.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tip = self._reference_info_card(
            explain, title="HINWEIS",
            text="Keine Aktion wird ausgelöst.",
            accent="#E5B854", min_height=130,
        )
        tip.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    def _build_settings_page(self) -> None:
        page = self.pages["Settings"]
        self.ttk.Label(page, text="Settings", style="PageTitle.TLabel").pack(anchor="w")
        card = self.ttk.Frame(page, style="Card.TFrame", padding=20)
        card.pack(fill="x", pady=(18, 0))
        self.ttk.Label(card, text="DARSTELLUNG", style="Card.TLabel", font=(self.display_font, 11, "bold")).pack(anchor="w")
        self.ttk.Label(card, text="Midnight / Metallic Blue · verbindliches Standarddesign", style="Muted.TLabel").pack(anchor="w", pady=(8, 0))
        self.ttk.Label(card, text="Keine weiteren Einstellungen werden angeboten, solange keine reale konfigurierbare Funktion dahintersteht.", style="Muted.TLabel", wraplength=800, justify="left").pack(anchor="w", pady=(6, 0))

    def _build_system_page(self) -> None:
        page = self.pages["System Check / Optimizer"]
        self.optimizer_active_domain = "SYSTEM_OPTIMIZER"
        self.optimizer_view_data: dict[str, object] | None = None
        self.optimizer_system_result_view: dict[str, object] | None = None
        self.optimizer_evidence_view_data: dict[str, object] | None = None
        self.optimizer_selected_model: dict[str, object] | None = None
        self.optimizer_detail_models: dict[str, dict[str, object]] = {}
        self.optimizer_hardware_values = {
            "OS": "Nicht verfügbar", "CPU": "Nicht verfügbar",
            "RAM": "Nicht verfügbar", "GPU": "Nicht verfügbar",
        }
        self.optimizer_search_var = self.tk.StringVar()
        self.optimizer_filter_var = self.tk.StringVar(value="Alle Status")

        # This is a complete Optimizer workspace, not a reordered continuation
        # of the former long developer page.  The two frames deliberately map
        # one-to-one to the approved overview and System Optimizer detail
        # composition while reusing the existing read-only adapters.
        self.optimizer_workspace = self.ttk.Frame(page, style="Content.TFrame")
        self.optimizer_workspace.pack(fill="both", expand=True)
        self.optimizer_overview_view = self.ttk.Frame(self.optimizer_workspace, style="Content.TFrame")
        self.optimizer_detail_view = self.ttk.Frame(self.optimizer_workspace, style="Content.TFrame")
        self._build_optimizer_overview_view()
        self._build_optimizer_detail_view()
        self._show_optimizer_overview()
        self._create_optimizer_master_overlay()

    def _create_optimizer_master_overlay(self) -> None:
        """Render the approved Optimizer MASTER separately from legacy shell chrome.

        The canvas owns only the visual composition. Existing data adapters,
        actions and read-only safety behaviour remain behind this presentation
        layer and are called through the small interaction map below.
        """
        self.optimizer_master_mode = "overview"
        self.optimizer_master_canvas = self.tk.Canvas(
            self.root, background="#02070d", highlightthickness=0, borderwidth=0, bd=0,
        )
        self.optimizer_master_canvas.bind("<Button-1>", self._activate_optimizer_master)
        self.optimizer_master_canvas.bind("<Configure>", self._draw_optimizer_master)

    def _show_optimizer_master_overlay(self) -> None:
        self.optimizer_master_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.optimizer_master_canvas.lift()
        self._draw_optimizer_master()

    def _master_rect(self, x1, y1, x2, y2, *, fill, outline="#152b3d", width=1, radius=10, tag="master") -> None:
        canvas = self.optimizer_master_canvas
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline="", tags=tag)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline="", tags=tag)
        for box, start in (((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 90), ((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 180), ((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 270), ((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 0)):
            canvas.create_arc(*box, start=start, extent=90, fill=fill, outline=outline, width=width, tags=tag)
        canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline, width=width, tags=tag)
        canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=outline, width=width, tags=tag)
        canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=outline, width=width, tags=tag)
        canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=outline, width=width, tags=tag)

    def _master_text(self, x, y, text, *, size=12, color="#E7EEF5", anchor="w", bold=False, width=0, tag="master") -> None:
        self.optimizer_master_canvas.create_text(
            x, y, text=text, fill=color, anchor=anchor, width=width or 0,
            font=(self.ui_font, size, "bold" if bold else "normal"), tags=tag,
        )

    def _draw_optimizer_master_shell(self) -> tuple[float, float]:
        canvas = self.optimizer_master_canvas
        canvas.delete("master")
        width, height = max(canvas.winfo_width(), 1), max(canvas.winfo_height(), 1)
        scale = min(width / 1536, height / 1024)
        ox, oy = (width - 1536 * scale) / 2, (height - 1024 * scale) / 2
        canvas.create_rectangle(0, 0, width, height, fill="#02070d", outline="", tags="master")
        canvas.create_rectangle(ox, oy, ox + 243 * scale, oy + 1024 * scale, fill="#06121f", outline="", tags="master")
        canvas.create_line(ox + 243 * scale, oy, ox + 243 * scale, oy + 1024 * scale, fill="#13293a", tags="master")
        self._master_text(ox + 38 * scale, oy + 48 * scale, "IMPROVE", size=max(12, int(29 * scale)), color="#F4F8FC", bold=True)
        self._master_text(ox + 39 * scale, oy + 80 * scale, "YOURSELF", size=max(10, int(20 * scale)), color="#EAF4FD", bold=False)
        self._master_text(ox + 210 * scale, oy + 111 * scale, "v1.0.0", size=max(7, int(11 * scale)), color="#95A6B7", anchor="e")
        nav = (("⌂", "Dashboard"), ("⚙", "Optimizer"), ("▣", "Analyzer"), ("◌", "Tactical Viewer"), ("▧", "System Info"), ("♧", "Benchmark"), ("▤", "Monitor"), ("☑", "Tools"), ("♙", "Profiles"))
        for index, (icon, label) in enumerate(nav):
            y = 169 + index * 54
            if label == "Optimizer":
                self._master_rect(ox + 4 * scale, oy + (y - 26) * scale, ox + 218 * scale, oy + (y + 26) * scale, fill="#0A2135", outline="#1676C1", radius=max(5, int(8 * scale)))
            self._master_text(ox + 28 * scale, oy + y * scale, icon, size=max(9, int(18 * scale)), color="#36A8FF" if label == "Optimizer" else "#A5B8CA")
            self._master_text(ox + 60 * scale, oy + y * scale, label, size=max(8, int(15 * scale)), color="#D8E7F2" if label == "Optimizer" else "#B2C1CF", bold=label == "Optimizer")
        self._master_text(ox + 28 * scale, oy + 873 * scale, "⚙", size=max(9, int(18 * scale)), color="#A5B8CA")
        self._master_text(ox + 60 * scale, oy + 873 * scale, "Settings", size=max(8, int(15 * scale)), color="#B2C1CF")
        self._master_text(ox + 28 * scale, oy + 920 * scale, "ⓘ", size=max(9, int(18 * scale)), color="#A5B8CA")
        self._master_text(ox + 60 * scale, oy + 920 * scale, "About Improve", size=max(8, int(15 * scale)), color="#B2C1CF")
        self._master_rect(ox + 18 * scale, oy + 950 * scale, ox + 210 * scale, oy + 1012 * scale, fill="#071725", outline="#183044", radius=max(5, int(8 * scale)))
        self._master_text(ox + 34 * scale, oy + 973 * scale, "✓", size=max(9, int(18 * scale)), color="#21D07A")
        self._master_text(ox + 57 * scale, oy + 971 * scale, "System bereit", size=max(8, int(14 * scale)), color="#2BE07E", bold=True)
        self._master_text(ox + 57 * scale, oy + 994 * scale, "Alle Dienste aktiv", size=max(7, int(12 * scale)), color="#AAB9C5")
        self._master_text(ox + 272 * scale, oy + 40 * scale, "Optimizer", size=max(13, int(25 * scale)), color="#F3F7FB", bold=True)
        for index, label in enumerate(("Windows", "CPU", "RAM", "GPU")):
            x = 764 + index * 160
            self._master_rect(ox + x * scale, oy + 22 * scale, ox + (x + 150) * scale, oy + 58 * scale, fill="#061321", outline="#17334A", radius=max(4, int(7 * scale)))
            value = list(self.optimizer_hardware_values.values())[index]
            self._master_text(ox + (x + 12) * scale, oy + 33 * scale, label, size=max(6, int(8 * scale)), color="#8297A9")
            self._master_text(ox + (x + 12) * scale, oy + 47 * scale, value, size=max(7, int(10 * scale)), color="#D7E2EA", width=122 * scale)
        self._master_rect(ox + 1423 * scale, oy + 22 * scale, ox + 1459 * scale, oy + 58 * scale, fill="#061321", outline="#17334A", radius=max(4, int(7 * scale)))
        self._master_text(ox + 1441 * scale, oy + 40 * scale, "•••", size=max(8, int(13 * scale)), color="#D9E6EF", anchor="center")
        self._master_text(ox + 1497 * scale, oy + 40 * scale, "×", size=max(13, int(26 * scale)), color="#D9E6EF", anchor="center")
        return ox, oy

    def _draw_optimizer_master(self, _event=None) -> None:
        ox, oy = self._draw_optimizer_master_shell()
        canvas = self.optimizer_master_canvas
        width, height = max(canvas.winfo_width(), 1), max(canvas.winfo_height(), 1)
        scale = min(width / 1536, height / 1024)
        S = lambda value: value * scale
        if self.optimizer_master_mode == "detail":
            self._draw_optimizer_master_detail(ox, oy, S)
            return
        self._master_rect(ox + S(258), oy + S(82), ox + S(1016), oy + S(368), fill="#071827", outline="#1A4663", radius=max(7, int(S(12))))
        self._master_text(ox + S(284), oy + S(113), "IMPROVE EMPFEHLUNGEN", size=max(10, int(S(18))), color="#43B4FF", bold=True)
        self._master_text(ox + S(284), oy + S(145), "Auf Basis deines Systems und unserer geprüften Optimierungsregeln", size=max(8, int(S(14))), color="#B7C6D4")
        self._master_text(ox + S(372), oy + S(239), "ALLE\n4 BEREICHE\nANALYSIERT\n✓", size=max(9, int(S(15))), color="#E8F0F5", anchor="center", bold=True)
        canvas.create_oval(ox + S(290), oy + S(176), ox + S(456), oy + S(343), outline="#10D678", width=max(2, int(S(11))), tags="master")
        canvas.create_arc(ox + S(290), oy + S(176), ox + S(456), oy + S(343), start=30, extent=125, style="arc", outline="#22A7FF", width=max(2, int(S(11))), tags="master")
        counts = self.optimizer_view_data.get("counts", {}) if isinstance(self.optimizer_view_data, dict) else {}
        metric_data = (("♜", str(counts.get("recommended", "—")), "EMPFEHLUNGEN\ngesamt", "#2A9DF4"), ("✓", str(counts.get("already", "—")), "Automatisch\numsetzbar", "#20D77A"), ("✋", str(counts.get("manual_bios", "—")), "BIOS-Empfehlungen\nerfordern deine Mithilfe", "#EE941B"))
        for index, (icon, value, text, color) in enumerate(metric_data):
            x = 495 + index * 157
            self._master_text(ox + S(x), oy + S(220), icon, size=max(12, int(S(27))), color=color, anchor="center")
            self._master_text(ox + S(x + 34), oy + S(208), value, size=max(12, int(S(25))), color="#F0F5FA", bold=True)
            self._master_text(ox + S(x + 34), oy + S(245), text, size=max(7, int(S(11))), color="#B8C7D5", width=S(110))
        self._master_rect(ox + S(484), oy + S(296), ox + S(990), oy + S(345), fill="#0B2034", outline="#197FC2", radius=max(5, int(S(7))))
        self._master_text(ox + S(737), oy + S(320), "Empfehlungen prüfen", size=max(10, int(S(18))), color="#F1F6FA", anchor="center", bold=True)
        self._master_text(ox + S(967), oy + S(320), "›", size=max(14, int(S(28))), color="#5FC0FF", anchor="center")
        cards = optimizer_domain_overview(self.optimizer_view_data)
        positions = ((258, 380), (641, 380), (258, 619), (641, 619))
        for item, (x, y) in zip(cards, positions):
            accent = _OPTIMIZER_DOMAIN_ACCENTS[str(item["domain"])]
            self._master_rect(ox + S(x), oy + S(y), ox + S(x + 375), oy + S(y + 227), fill="#071725", outline="#19364A", radius=max(7, int(S(10))))
            self._master_rect(ox + S(x + 19), oy + S(y + 45), ox + S(x + 88), oy + S(y + 114), fill="#092337", outline=accent, radius=max(6, int(S(10))))
            self._master_text(ox + S(x + 54), oy + S(y + 80), "◉", size=max(12, int(S(30))), color=accent, anchor="center")
            self._master_text(ox + S(x + 105), oy + S(y + 32), str(item["title"]).upper(), size=max(9, int(S(16))), color="#EEF4F8", bold=True)
            self._master_text(ox + S(x + 105), oy + S(y + 60), str(item["description"]), size=max(7, int(S(13))), color="#B4C2D0", width=S(230))
            self._master_text(ox + S(x + 105), oy + S(y + 119), str(item["state"]), size=max(7, int(S(12))), color=accent, width=S(235))
            self._master_rect(ox + S(x + 14), oy + S(y + 175), ox + S(x + 360), oy + S(y + 212), fill="#071B2C", outline="#195E91", radius=max(4, int(S(7))))
            self._master_text(ox + S(x + 187), oy + S(y + 194), "Details ansehen", size=max(8, int(S(14))), color="#67C6FF", anchor="center")
        self._master_rect(ox + S(258), oy + S(858), ox + S(1016), oy + S(1012), fill="#071725", outline="#19364A", radius=max(7, int(S(10))))
        self._master_text(ox + S(280), oy + S(894), "LETZTER OPTIMIERUNGSLAUF", size=max(9, int(S(16))), color="#33A9FF", bold=True)
        self._master_text(ox + S(280), oy + S(940), "Kein abgeschlossener lokaler Optimierungslauf vorhanden.", size=max(8, int(S(14))), color="#C0CDD8")
        self._master_text(ox + S(280), oy + S(966), "Read-only: Ergebnisse und Wiederherstellung werden erst nach belegten lokalen Vorgängen angezeigt.", size=max(7, int(S(12))), color="#8FA4B5")
        self._draw_optimizer_master_right(ox, oy, S)

    def _draw_optimizer_master_right(self, ox, oy, S) -> None:
        selected = next(item for item in optimizer_domain_overview(self.optimizer_view_data) if item["domain"] == self.optimizer_active_domain)
        self._master_rect(ox + S(1030), oy + S(82), ox + S(1520), oy + S(1012), fill="#061522", outline="#18364B", radius=max(7, int(S(12))))
        self._master_text(ox + S(1054), oy + S(114), "DETAILS & ERKLÄRUNG", size=max(10, int(S(17))), color="#37ADFF", bold=True)
        self._master_text(ox + S(1488), oy + S(114), "×", size=max(12, int(S(24))), color="#B9C9D7", anchor="center")
        self._master_text(ox + S(1085), oy + S(165), str(selected["title"]), size=max(10, int(S(18))), color="#F0F5F9", bold=True)
        self._master_text(ox + S(1085), oy + S(194), str(selected["description"]), size=max(8, int(S(13))), color="#B9C7D4")
        self._master_text(ox + S(1055), oy + S(232), "Aktuell: Nicht verfügbar", size=max(8, int(S(12))), color="#C6D3DD")
        self._master_text(ox + S(1200), oy + S(232), "Empfohlen: —", size=max(8, int(S(12))), color="#53C98B")
        self._master_text(ox + S(1360), oy + S(232), "Keine Änderung", size=max(8, int(S(12))), color="#E6A33B")
        headings = (("WAS IST DAS?", "Die Übersicht zeigt nur vorhandene lokale Fakten. Fehlende Bewertungen bleiben sichtbar unbekannt."), ("WARUM EMPFIEHLT IMPROVE DAS?", "Eine Empfehlung wird erst bei vorhandener lokaler Evidenz angezeigt."), ("EVIDENZ & GÜLTIGKEIT", "Nicht verfügbar."), ("ÄNDERUNG & WIEDERHERSTELLUNG", "Read-only · es wird keine Änderung ausgeführt."), ("NÄCHSTER SCHRITT", "Starte die vorhandene Prüfung nur bewusst über „Empfehlungen prüfen“ ."))
        y = 286
        for heading, value in headings:
            self._master_text(ox + S(1055), oy + S(y), heading, size=max(8, int(S(13))), color="#37ADFF", bold=True)
            self._master_text(ox + S(1055), oy + S(y + 31), value, size=max(7, int(S(12))), color="#BAC8D4", width=S(408))
            y += 126

    def _draw_optimizer_master_detail(self, ox, oy, S) -> None:
        self._master_rect(ox + S(242), oy + S(76), ox + S(1075), oy + S(252), fill="#071725", outline="#18364B", radius=max(7, int(S(10))))
        self._master_text(ox + S(272), oy + S(107), "←", size=max(14, int(S(28))), color="#BFD0DD")
        self._master_text(ox + S(319), oy + S(108), "System Optimizer", size=max(13, int(S(25))), color="#F4F8FB", bold=True)
        self._master_text(ox + S(319), oy + S(137), "Windows & System", size=max(8, int(S(14))), color="#C0CDD8")
        self._master_rect(ox + S(900), oy + S(96), ox + S(1061), oy + S(130), fill="#092034", outline="#1769A2", radius=max(4, int(S(7))))
        self._master_text(ox + S(980), oy + S(113), "Zurück zur Übersicht", size=max(7, int(S(12))), color="#DAEAF4", anchor="center")
        counts = self.optimizer_view_data.get("counts", {}) if isinstance(self.optimizer_view_data, dict) else {}
        metrics = (("⚙", "Einstellungen geprüft", counts.get("checked", "—"), "#199CFF"), ("✓", "Bereits optimal", counts.get("already", "—"), "#1FD47A"), ("●", "Änderungen empfohlen", counts.get("recommended", "—"), "#F18C1B"), ("◌", "Nicht relevant", counts.get("conditional", "—"), "#9BAABA"))
        for index, (icon, label, value, color) in enumerate(metrics):
            x = 259 + index * 212
            self._master_rect(ox + S(x), oy + S(162), ox + S(x + 208), oy + S(235), fill="#071725", outline="#19364A", radius=max(5, int(S(8))))
            self._master_text(ox + S(x + 28), oy + S(198), icon, size=max(11, int(S(25))), color=color, anchor="center")
            self._master_text(ox + S(x + 68), oy + S(187), str(value), size=max(11, int(S(23))), color="#F1F6FA", bold=True)
            self._master_text(ox + S(x + 68), oy + S(211), label, size=max(7, int(S(11))), color="#C0CDD8")
        self._master_rect(ox + S(242), oy + S(253), ox + S(1075), oy + S(1010), fill="#061522", outline="#18364B", radius=max(7, int(S(10))))
        self._master_rect(ox + S(259), oy + S(264), ox + S(487), oy + S(298), fill="#04111C", outline="#19364A", radius=max(4, int(S(6))))
        self._master_text(ox + S(274), oy + S(281), "⌕  Einstellung suchen...", size=max(7, int(S(12))), color="#AAB9C5")
        self._master_rect(ox + S(498), oy + S(264), ox + S(615), oy + S(298), fill="#071B2C", outline="#19364A", radius=max(4, int(S(6))))
        self._master_text(ox + S(556), oy + S(281), "Alle Status⌄", size=max(7, int(S(12))), color="#D5E1EA", anchor="center")
        headers = (("Einstellung", 275), ("Aktuell", 640), ("Empfehlung", 742), ("Status", 872))
        for text, x in headers:
            self._master_text(ox + S(x), oy + S(324), text, size=max(7, int(S(12))), color="#D2DEE7")
        visible = optimizer_visible_models(self.optimizer_view_data, self.optimizer_active_domain, query=self.optimizer_search_var.get(), status_filter=self.optimizer_filter_var.get())
        if visible:
            y = 365
            for model in visible[:12]:
                self._master_rect(ox + S(258), oy + S(y - 21), ox + S(1061), oy + S(y + 15), fill="#071725", outline="#173044", radius=max(2, int(S(3))))
                label, semantic = status_presentation(model.get("status"))
                color = {"ready": "#24D47B", "conditional": "#F1A21E", "unknown": "#99A9B8", "evidence": "#2FA8FF"}[semantic]
                self._master_text(ox + S(275), oy + S(y - 3), str(model.get("title") or "Unbenannte Einstellung"), size=max(7, int(S(12))), color="#E7EEF5")
                self._master_text(ox + S(640), oy + S(y - 3), optimizer_table_cell(model.get("current_state"), maximum=18), size=max(7, int(S(11))), color="#CBD7E0")
                self._master_text(ox + S(742), oy + S(y - 3), optimizer_table_cell(model.get("improve_recommendation"), maximum=18), size=max(7, int(S(11))), color=color)
                self._master_text(ox + S(872), oy + S(y - 3), optimizer_table_cell(label, maximum=16), size=max(7, int(S(11))), color=color)
                y += 38
        else:
            self._master_text(ox + S(660), oy + S(500), "Keine bestätigten lokalen Einstellungen verfügbar.", size=max(8, int(S(14))), color="#8FA4B5", anchor="center")
        self._draw_optimizer_master_right(ox, oy, S)

    def _activate_optimizer_master(self, event) -> None:
        width, height = max(self.optimizer_master_canvas.winfo_width(), 1), max(self.optimizer_master_canvas.winfo_height(), 1)
        scale = min(width / 1536, height / 1024)
        x, y = event.x / scale, event.y / scale
        if self.optimizer_master_mode == "detail":
            if 242 <= x <= 1075 and 76 <= y <= 145:
                self.optimizer_master_mode = "overview"
                self._show_optimizer_overview()
                self.optimizer_master_canvas.lift()
                self._draw_optimizer_master()
            return
        if 258 <= x <= 1016 and 380 <= y <= 846:
            column = 0 if x < 641 else 1
            row = 0 if y < 619 else 1
            domain = (("SYSTEM_OPTIMIZER", "GRAPHICS_OPTIMIZER"), ("NETWORK_OPTIMIZER", "BIOS_OPTIMIZER"))[row][column]
            self.optimizer_master_mode = "detail"
            self._show_optimizer_detail_screen(domain)
            self.optimizer_master_canvas.lift()
            self._draw_optimizer_master()
        elif 484 <= x <= 990 and 296 <= y <= 345:
            self._run_system_check()


    def _optimizer_header(self, parent, *, title: str, back_command: Callable[[], None] | None = None):
        header = self.ttk.Frame(parent, style="Content.TFrame")
        header.pack(fill="x", pady=(0, 14))
        if back_command is not None:
            self.ttk.Button(header, text="← Zurück zur Übersicht", command=back_command).pack(side="left", padx=(0, 13))
        self.ttk.Label(header, text=title, style="PageTitle.TLabel").pack(side="left")
        chips = self.ttk.Frame(header, style="Content.TFrame")
        chips.pack(side="right")
        self.optimizer_header_chip_hosts.append(chips)
        self._render_optimizer_hardware_chips()
        return header

    def _build_optimizer_overview_view(self) -> None:
        self.optimizer_header_chip_hosts: list[object] = []
        self._optimizer_header(self.optimizer_overview_view, title="Optimizer")
        content = self.ttk.Frame(self.optimizer_overview_view, style="Content.TFrame")
        content.pack(fill="both", expand=True)
        left = self.ttk.Frame(content, style="Content.TFrame")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right_surface = RoundedOptimizerSurface(
            self.tk, self.ttk, content, style="OptimizerDetail.TFrame", fill=_OPTIMIZER_THEME["surface_detail"],
            padding=22, min_height=760, min_width=430,
        )
        right_surface.pack(side="right", fill="y")
        right_surface.canvas.pack_propagate(False)
        right = right_surface.body
        self.optimizer_overview_details = right_surface

        hero_surface = RoundedOptimizerSurface(
            self.tk, self.ttk, left, style="OptimizerHero.TFrame", fill=_OPTIMIZER_THEME["surface_hero"],
            padding=26, min_height=286,
        )
        hero_surface.pack(fill="x")
        self.optimizer_overview_hero = hero_surface.body
        hero_header = self.ttk.Frame(self.optimizer_overview_hero, style="OptimizerHero.TFrame")
        hero_header.pack(fill="x")
        self.ttk.Label(hero_header, text="IMPROVE EMPFEHLUNGEN", style="OptimizerHero.TLabel", font=(self.display_font, 12, "bold")).pack(side="left")
        self.optimizer_overview_badge = self.ttk.Label(hero_header, text="READ-ONLY", style="StatusBadge.TLabel")
        self.optimizer_overview_badge.pack(side="right")
        hero_body = self.ttk.Frame(self.optimizer_overview_hero, style="OptimizerHero.TFrame")
        hero_body.pack(fill="x", pady=(9, 0))
        self.optimizer_overview_ring = self.tk.Canvas(
            hero_body, width=150, height=150, background=_OPTIMIZER_THEME["surface_hero"],
            highlightthickness=0, borderwidth=0, bd=0,
        )
        self.optimizer_overview_ring.pack(side="left", padx=(0, 26))
        self.optimizer_overview_ring.bind("<Configure>", self._draw_optimizer_overview_ring)
        hero_copy = self.ttk.Frame(hero_body, style="OptimizerHero.TFrame")
        hero_copy.pack(side="left", fill="both", expand=True)
        self.optimizer_overview_summary = self.ttk.Label(
            hero_copy,
            text="Ein System Check liefert lokale Fakten. Fehlende oder nicht sichere Werte bleiben sichtbar als unbekannt oder bedingt.",
            style="OptimizerHeroMuted.TLabel", wraplength=560, justify="left",
        )
        self.optimizer_overview_summary.pack(anchor="w", pady=(0, 11))
        metrics = self.ttk.Frame(hero_copy, style="OptimizerHero.TFrame")
        metrics.pack(fill="x")
        self.optimizer_overview_metric_values: dict[str, object] = {}
        for index, (key, label) in enumerate((("checked", "GEPRÜFT"), ("already", "BEREITS PASSEND"), ("conditional", "ZU PRÜFEN"))):
            metrics.columnconfigure(index, weight=1, uniform="optimizer-summary")
            metric_surface = RoundedOptimizerSurface(
                self.tk, self.ttk, metrics, style="OptimizerMetric.TFrame", fill=_OPTIMIZER_THEME["surface_raised"],
                padding=(12, 10), min_height=82, radius=9,
            )
            metric_surface.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 4, 0 if index == 2 else 4))
            metric = metric_surface.body
            self.ttk.Label(metric, text=label, style="OptimizerMetricMuted.TLabel", font=(self.ui_font, 7, "bold")).pack(anchor="w")
            metric_color = (_OPTIMIZER_THEME["accent"], _OPTIMIZER_THEME["success"], _OPTIMIZER_THEME["warning"])[index]
            value = self.ttk.Label(metric, text="—", style="OptimizerMetric.TLabel", foreground=metric_color, font=(self.display_font, 15, "bold"))
            value.pack(anchor="w", pady=(3, 0))
            self.optimizer_overview_metric_values[key] = value
        self.optimizer_overview_run_action = RoundedOptimizerAction(
            self.tk, hero_copy, text="System Check ausführen", command=self._run_system_check,
            primary=True, font=(self.ui_font, 9, "bold"),
        )
        self.optimizer_overview_run_action.canvas.configure(background=_OPTIMIZER_THEME["surface_hero"])
        self.optimizer_overview_run_action.pack(anchor="w", pady=(12, 0))
        self.ttk.Label(hero_copy, textvariable=self.system_status, style="OptimizerHeroMuted.TLabel", wraplength=560, justify="left").pack(anchor="w", pady=(7, 0))

        self.ttk.Label(left, text="OPTIMIZER BEREICHE", style="PageKicker.TLabel").pack(anchor="w", pady=(18, 7))
        self.optimizer_domain_grid = self.ttk.Frame(left, style="Content.TFrame")
        self.optimizer_domain_grid.pack(fill="x")
        for index in range(2):
            self.optimizer_domain_grid.columnconfigure(index, weight=1, uniform="optimizer-domains")
        # The final row is part of the approved Overview hierarchy. It stays
        # explicitly empty until an actual local optimization run exists.
        last_run_surface = RoundedOptimizerSurface(
            self.tk, self.ttk, left, style="OptimizerArea.TFrame", fill=_OPTIMIZER_THEME["surface"],
            padding=(20, 16), min_height=126, radius=12,
        )
        last_run_surface.pack(fill="x", pady=(14, 0))
        last_run = last_run_surface.body
        self.ttk.Label(last_run, text="LETZTER OPTIMIERUNGSLAUF", style="OptimizerArea.TLabel", foreground=_OPTIMIZER_THEME["accent"], font=(self.display_font, 9, "bold")).pack(anchor="w")
        self.ttk.Label(last_run, text="Kein abgeschlossener lokaler Optimierungslauf vorhanden.", style="OptimizerAreaMuted.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(8, 0))
        self.ttk.Label(last_run, text="Read-only: Ergebnisse und Wiederherstellung werden erst nach belegten lokalen Vorgängen angezeigt.", style="OptimizerAreaMuted.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(4, 0))
        self._build_optimizer_explanation_panel(right)
        self._render_optimizer_overview()

    def _build_optimizer_explanation_panel(self, panel) -> None:
        self.ttk.Label(panel, text="DETAILS & ERKLÄRUNG", style="OptimizerDetail.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.optimizer_overview_detail_title = self.ttk.Label(panel, text="System Optimizer", style="OptimizerDetail.TLabel", font=(self.ui_font, 12, "bold"))
        self.optimizer_overview_detail_title.pack(anchor="w", pady=(16, 4))
        self.optimizer_overview_detail_text = self.ttk.Label(
            panel,
            text="Wähle einen Optimizer-Bereich. Die Detailansicht zeigt ausschließlich vorhandene lokale Fakten, Bewertungen und Unsicherheiten.",
            style="OptimizerDetailMuted.TLabel", wraplength=380, justify="left",
        )
        self.optimizer_overview_detail_text.pack(anchor="w", pady=(0, 14))
        self.optimizer_overview_detail_status = self.ttk.Label(panel, text="Keine Bewertung geladen", style="OptimizerDetail.TLabel", foreground=_THEME["cyan"], wraplength=380, justify="left")
        self.optimizer_overview_detail_status.pack(anchor="w", pady=(0, 12))
        self.ttk.Label(panel, text="WAS IST DAS?", style="OptimizerDetailMuted.TLabel", foreground=_OPTIMIZER_THEME["accent"], font=(self.ui_font, 7, "bold")).pack(anchor="w", pady=(8, 3))
        self.ttk.Label(panel, text="Die Übersicht zeigt nur vorhandene lokale Fakten und die vier festen read-only Bereiche. Eine fehlende Bewertung ist keine Empfehlung.", style="OptimizerDetailMuted.TLabel", wraplength=380, justify="left").pack(anchor="w")
        self.optimizer_overview_open_action = RoundedOptimizerAction(
            self.tk, panel, text="System Optimizer öffnen", primary=True,
            command=lambda: self._show_optimizer_detail_screen(self.optimizer_active_domain), font=(self.ui_font, 9, "bold"),
        )
        self.optimizer_overview_open_action.canvas.configure(background=_OPTIMIZER_THEME["surface_detail"])
        self.optimizer_overview_open_action.pack(fill="x")
        self.ttk.Label(panel, text="Technische Evidenz und Provenance bleiben erst in den Detailinformationen einer Einstellung sichtbar.", style="OptimizerDetailMuted.TLabel", wraplength=380, justify="left").pack(anchor="w", pady=(18, 0))

    def _build_optimizer_detail_view(self) -> None:
        self._optimizer_header(self.optimizer_detail_view, title="Optimizer", back_command=self._show_optimizer_overview)
        self.optimizer_detail_screen_title = self.ttk.Label(self.optimizer_detail_view, text="System Optimizer", style="PageTitle.TLabel")
        self.optimizer_detail_screen_title.pack(anchor="w")
        self.ttk.Label(self.optimizer_detail_view, text="Windows & System · read-only Evidenz", style="PageKicker.TLabel").pack(anchor="w", pady=(2, 12))
        metrics = self.ttk.Frame(self.optimizer_detail_view, style="Content.TFrame")
        metrics.pack(fill="x")
        self.optimizer_detail_metric_values: dict[str, object] = {}
        for index, (key, label) in enumerate((("checked", "EINSTELLUNGEN GEPRÜFT"), ("already", "BEREITS PASSEND"), ("recommended", "ÄNDERUNG EMPFOHLEN"), ("conditional", "ZU PRÜFEN"))):
            metrics.columnconfigure(index, weight=1, uniform="optimizer-detail-metrics")
            metric_surface = RoundedOptimizerSurface(
                self.tk, self.ttk, metrics, style="OptimizerMetric.TFrame", fill=_OPTIMIZER_THEME["surface_raised"],
                padding=(14, 11), min_height=84, radius=9,
            )
            metric_surface.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 4, 0 if index == 3 else 4))
            metric = metric_surface.body
            self.ttk.Label(metric, text=label, style="OptimizerMetricMuted.TLabel", font=(self.ui_font, 7, "bold")).pack(anchor="w")
            metric_color = (_OPTIMIZER_THEME["accent"], _OPTIMIZER_THEME["success"], _OPTIMIZER_THEME["warning"], _OPTIMIZER_THEME["unknown"])[index]
            value = self.ttk.Label(metric, text="—", style="OptimizerMetric.TLabel", foreground=metric_color, font=(self.display_font, 16, "bold"))
            value.pack(anchor="w", pady=(4, 0))
            self.optimizer_detail_metric_values[key] = value

        controls = self.ttk.Frame(self.optimizer_detail_view, style="Content.TFrame")
        controls.pack(fill="x", pady=(16, 10))
        self.ttk.Label(controls, text="EINSTELLUNGEN", style="PageKicker.TLabel").pack(side="left")
        self.optimizer_filter = self.ttk.Combobox(controls, textvariable=self.optimizer_filter_var, style="Optimizer.TCombobox", state="readonly", width=24, values=("Alle Status", "RECOMMENDED", "ALREADY_RECOMMENDED", "CONDITIONAL", "INSUFFICIENT_EVIDENCE", "NO_CHANGE", "EXCLUSION"))
        self.optimizer_filter.pack(side="right")
        self.optimizer_filter.bind("<<ComboboxSelected>>", lambda _event: self._render_optimizer_detail_table())
        self.optimizer_search = self.ttk.Entry(controls, textvariable=self.optimizer_search_var, style="Optimizer.TEntry", width=30)
        self.optimizer_search.pack(side="right", padx=(0, 8))
        self.optimizer_search.bind("<KeyRelease>", lambda _event: self._render_optimizer_detail_table())

        content = self.ttk.Frame(self.optimizer_detail_view, style="Content.TFrame")
        content.pack(fill="both", expand=True)
        table_surface = RoundedOptimizerSurface(
            self.tk, self.ttk, content, style="OptimizerArea.TFrame", fill=_OPTIMIZER_THEME["surface_input"],
            padding=0, min_height=420, radius=12,
        )
        table_surface.pack(side="left", fill="both", expand=True, padx=(0, 12))
        table_card = table_surface.body
        detail_surface = RoundedOptimizerSurface(
            self.tk, self.ttk, content, style="OptimizerDetail.TFrame", fill=_OPTIMIZER_THEME["surface_detail"],
            padding=22, min_height=620, min_width=435,
        )
        detail_surface.pack(side="right", fill="y")
        detail_surface.canvas.pack_propagate(False)
        # The explanation column can legitimately be taller than the table
        # viewport (especially for Graphics/Network evidence).  It therefore
        # owns an explicit local scroll surface instead of silently clipping
        # the lower sections inside the fixed rounded card.
        detail_host = detail_surface.body
        detail_canvas = self.tk.Canvas(
            detail_host, background=_OPTIMIZER_THEME["surface_detail"],
            borderwidth=0, highlightthickness=0,
        )
        detail_scrollbar = self.ttk.Scrollbar(detail_host, orient="vertical", command=detail_canvas.yview)
        detail_canvas.configure(yscrollcommand=detail_scrollbar.set)
        detail_scrollbar.pack(side="right", fill="y")
        detail_canvas.pack(side="left", fill="both", expand=True)
        detail = self.ttk.Frame(detail_canvas, style="OptimizerDetail.TFrame")
        detail_window = detail_canvas.create_window((0, 0), window=detail, anchor="nw")
        detail.bind(
            "<Configure>",
            lambda _event, canvas=detail_canvas: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        detail_canvas.bind(
            "<Configure>",
            lambda event, canvas=detail_canvas, item=detail_window: canvas.itemconfigure(item, width=event.width),
        )
        detail_canvas.bind(
            "<MouseWheel>",
            lambda event, canvas=detail_canvas: canvas.yview_scroll(int(-event.delta / 120), "units"),
        )
        detail.bind(
            "<MouseWheel>",
            lambda event, canvas=detail_canvas: canvas.yview_scroll(int(-event.delta / 120), "units"),
        )
        self.optimizer_detail_scroll_canvas = detail_canvas
        self.optimizer_detail_scrollbar = detail_scrollbar
        self.optimizer_detail_card = detail_surface
        self.optimizer_detail_tree = self.ttk.Treeview(table_card, style="Optimizer.Treeview", columns=("current", "recommendation", "status", "open"), show="tree headings", selectmode="browse")
        self.optimizer_detail_tree.heading("#0", text="EINSTELLUNG")
        self.optimizer_detail_tree.heading("current", text="AKTUELLER ZUSTAND")
        self.optimizer_detail_tree.heading("recommendation", text="IMPROVE EMPFEHLUNG")
        self.optimizer_detail_tree.heading("status", text="STATUS")
        self.optimizer_detail_tree.heading("open", text="")
        self.optimizer_detail_tree.column("#0", width=158, minwidth=130, anchor="w")
        self.optimizer_detail_tree.column("current", width=142, minwidth=112, anchor="w")
        self.optimizer_detail_tree.column("recommendation", width=150, minwidth=120, anchor="w")
        self.optimizer_detail_tree.column("status", width=98, minwidth=88, anchor="w")
        self.optimizer_detail_tree.column("open", width=28, minwidth=24, anchor="center", stretch=False)
        self.optimizer_detail_tree.tag_configure("ready", foreground=_OPTIMIZER_THEME["success"])
        self.optimizer_detail_tree.tag_configure("evidence", foreground=_OPTIMIZER_THEME["accent"])
        self.optimizer_detail_tree.tag_configure("conditional", foreground=_OPTIMIZER_THEME["warning"])
        self.optimizer_detail_tree.tag_configure("unknown", foreground=_OPTIMIZER_THEME["unknown"])
        self.optimizer_detail_tree.tag_configure("section", foreground=_OPTIMIZER_THEME["accent"], font=(self.ui_font, 8, "bold"))
        self.optimizer_detail_tree.pack(fill="both", expand=True)
        self.optimizer_detail_tree.bind("<<TreeviewSelect>>", self._select_optimizer_setting)
        self.ttk.Label(detail, text="DETAILS & ERKLÄRUNG", style="OptimizerDetail.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.optimizer_detail_title = self.ttk.Label(detail, text="Keine Einstellung ausgewählt", style="OptimizerDetail.TLabel", font=(self.ui_font, 12, "bold"), wraplength=380, justify="left")
        self.optimizer_detail_title.pack(anchor="w", pady=(16, 5))
        self.optimizer_detail_state = self.ttk.Label(detail, text="Aktueller Zustand: —", style="OptimizerDetailMuted.TLabel", wraplength=380, justify="left")
        self.optimizer_detail_state.pack(anchor="w")
        self.optimizer_detail_status = self.ttk.Label(detail, text="Status: —", style="OptimizerDetail.TLabel", foreground=_OPTIMIZER_THEME["accent"], wraplength=380, justify="left")
        self.optimizer_detail_status.pack(anchor="w", pady=(4, 12))
        self.optimizer_detail_sections: dict[str, object] = {}
        for key, heading in (("what", "WAS IST DAS?"), ("why", "WARUM FÜR DIESES SYSTEM?"), ("effect", "MÖGLICHER EFFEKT"), ("evidence", "EVIDENZ & GÜLTIGKEIT"), ("change", "ÄNDERUNG & WIEDERHERSTELLUNG")):
            self.ttk.Label(detail, text=heading, style="OptimizerDetailMuted.TLabel", foreground=_OPTIMIZER_THEME["accent"], font=(self.ui_font, 7, "bold")).pack(anchor="w", pady=(8, 2))
            value = self.ttk.Label(detail, text="—", style="OptimizerDetailMuted.TLabel", wraplength=380, justify="left")
            value.pack(anchor="w")
            self.optimizer_detail_sections[key] = value
        self.optimizer_detail_technical_action = RoundedOptimizerAction(
            self.tk, detail, text="Technische Details", command=self._toggle_optimizer_technical_detail,
            font=(self.ui_font, 9, "bold"),
        )
        self.optimizer_detail_technical_action.canvas.configure(background=_OPTIMIZER_THEME["surface_detail"])
        self.optimizer_detail_technical_action.pack(fill="x", pady=(10, 0))
        self.optimizer_detail_technical_text = self.ttk.Label(detail, text="", style="OptimizerDetailMuted.TLabel", wraplength=380, justify="left")
        self.optimizer_detail_technical_visible = False

    def _render_optimizer_hardware_chips(self) -> None:
        for host in getattr(self, "optimizer_header_chip_hosts", []):
            for child in host.winfo_children():
                child.destroy()
            for label, value in self.optimizer_hardware_values.items():
                OptimizerHardwareChip(self.tk, host, label=label, value=value, ui_font=self.ui_font).pack(side="left", padx=(5, 0))

    def _draw_optimizer_overview_ring(self, _event=None) -> None:
        """Draw the MASTER-style status ring without implying a result we lack."""
        canvas = self.optimizer_overview_ring
        width, height = max(canvas.winfo_width(), 1), max(canvas.winfo_height(), 1)
        inset = 11
        canvas.delete("all")
        canvas.create_oval(inset, inset, width - inset, height - inset, outline=_OPTIMIZER_THEME["border"], width=8)
        canvas.create_arc(inset, inset, width - inset, height - inset, start=62, extent=252, style="arc", outline=_OPTIMIZER_THEME["accent"], width=7)
        canvas.create_arc(inset + 11, inset + 11, width - inset - 11, height - inset - 11, start=160, extent=120, style="arc", outline=_OPTIMIZER_THEME["success"], width=2)
        canvas.create_text(width // 2, height // 2 - 13, text="4", fill=_OPTIMIZER_THEME["text"], font=(self.display_font, 24, "bold"))
        canvas.create_text(width // 2, height // 2 + 12, text="BEREICHE", fill=_OPTIMIZER_THEME["secondary"], font=(self.ui_font, 7, "bold"))
        canvas.create_text(width // 2, height // 2 + 26, text="VERFÜGBAR", fill=_OPTIMIZER_THEME["secondary"], font=(self.ui_font, 7, "bold"))

    def _show_optimizer_overview(self) -> None:
        self.optimizer_detail_view.pack_forget()
        self.optimizer_overview_view.pack(fill="both", expand=True)
        self._render_optimizer_overview(self.optimizer_view_data)
        if hasattr(self, "optimizer_master_canvas") and self.optimizer_master_canvas.winfo_ismapped():
            self.optimizer_master_mode = "overview"
            self.optimizer_master_canvas.lift()
            self._draw_optimizer_master()
        if self.system_canvas is not None:
            self.root.after_idle(lambda: self.system_canvas.yview_moveto(0.0))

    def _show_optimizer_detail_screen(self, domain: str) -> None:
        self.optimizer_active_domain = domain
        self.optimizer_overview_view.pack_forget()
        self.optimizer_detail_view.pack(fill="both", expand=True)
        selected = next(item for item in optimizer_domain_overview(self.optimizer_view_data) if item["domain"] == domain)
        self.optimizer_detail_screen_title.configure(text=str(selected["title"]).upper())
        self._render_optimizer_detail_table()
        if hasattr(self, "optimizer_master_canvas") and self.optimizer_master_canvas.winfo_ismapped():
            self.optimizer_master_mode = "detail"
            self.optimizer_master_canvas.lift()
            self._draw_optimizer_master()
        if self.system_canvas is not None:
            self.root.after_idle(lambda: self.system_canvas.yview_moveto(0.0))

    def _render_optimizer_overview(self, view: dict[str, object] | None = None) -> None:
        for child in self.optimizer_domain_grid.winfo_children():
            child.destroy()
        cards = optimizer_domain_overview(view)
        selected = next(item for item in cards if item["domain"] == self.optimizer_active_domain)
        counts = view.get("counts", {}) if isinstance(view, dict) else {}
        self.optimizer_overview_summary.configure(text=(
            "Lokale Fakten und Bewertungen bleiben getrennt. Fehlende Evidenz erzeugt keine positive Empfehlung."
            if view is not None else
            "Noch kein bestätigter lokaler Optimizer-Datensatz. Ein System Check erfasst Fakten read-only; unbekannte Werte bleiben unbekannt."
        ))
        for key, widget in self.optimizer_overview_metric_values.items():
            widget.configure(text=str(counts.get(key, "—")))
        self._draw_optimizer_overview_ring()
        self.optimizer_overview_detail_title.configure(text=str(selected["title"]))
        self.optimizer_overview_detail_text.configure(text=str(selected["description"]))
        self.optimizer_overview_detail_status.configure(text=str(selected["state"]))
        self.optimizer_overview_open_action.text = f"{selected['title']} öffnen"
        self.optimizer_overview_open_action.command = lambda value=selected["domain"]: self._show_optimizer_detail_screen(value)
        self.optimizer_overview_open_action._draw()
        for index, item in enumerate(cards):
            active = item["domain"] == self.optimizer_active_domain
            card_surface = RoundedOptimizerSurface(
                self.tk, self.ttk, self.optimizer_domain_grid,
                style="OptimizerAreaActive.TFrame" if active else "OptimizerArea.TFrame",
                fill=_OPTIMIZER_THEME["surface_raised"] if active else _OPTIMIZER_THEME["surface"],
                padding=(16, 14), min_height=192, radius=12,
            )
            card_surface.grid(row=index // 2, column=index % 2, sticky="nsew", padx=(0 if index % 2 == 0 else 5, 5 if index % 2 == 0 else 0), pady=(0 if index < 2 else 10, 10 if index < 2 else 0))
            card = card_surface.body
            label_style = "OptimizerAreaActive.TLabel" if active else "OptimizerArea.TLabel"
            muted_style = "OptimizerAreaActiveMuted.TLabel" if active else "OptimizerAreaMuted.TLabel"
            # The approved MASTER gives each fixed area a compact identity
            # accent without changing any evidence-derived semantic status.
            accent = _OPTIMIZER_DOMAIN_ACCENTS[str(item["domain"])]
            self.ttk.Label(card, text="●", style=label_style, foreground=accent, font=(self.display_font, 17, "bold")).pack(anchor="w")
            self.ttk.Label(card, text="AKTIV" if active else "OPTIMIZER BEREICH", style=muted_style, foreground=accent, font=(self.ui_font, 7, "bold")).pack(anchor="w", pady=(2, 0))
            self.ttk.Label(card, text=item["title"], style=label_style, font=(self.display_font, 10, "bold")).pack(anchor="w", pady=(6, 3))
            self.ttk.Label(card, text=item["description"], style=muted_style, wraplength=270, justify="left").pack(anchor="w")
            self.ttk.Label(card, text=item["state"], style=label_style, foreground=accent, wraplength=270, justify="left", font=(self.ui_font, 8, "bold")).pack(anchor="w", pady=(12, 12))
            action = RoundedOptimizerAction(self.tk, card, text="Details ansehen", primary=active, command=lambda value=item["domain"]: self._show_optimizer_detail_screen(value), font=(self.ui_font, 9, "bold"))
            action.canvas.configure(background=_OPTIMIZER_THEME["surface_raised"] if active else _OPTIMIZER_THEME["surface"])
            action.pack(fill="x")

    def _render_optimizer_detail_table(self) -> None:
        for item in self.optimizer_detail_tree.get_children():
            self.optimizer_detail_tree.delete(item)
        self.optimizer_detail_models.clear()
        visible = optimizer_visible_models(
            self.optimizer_view_data, self.optimizer_active_domain,
            query=self.optimizer_search_var.get(), status_filter=self.optimizer_filter_var.get(),
        )
        counts = self.optimizer_view_data.get("counts", {}) if isinstance(self.optimizer_view_data, dict) else {}
        for key, widget in self.optimizer_detail_metric_values.items():
            widget.configure(text=str(counts.get(key, "—")))
        if visible:
            self.optimizer_detail_tree.insert("", "end", iid="section-system", text="SYSTEM CHECK & READ-ONLY-EVIDENZ", values=("", "", "", ""), tags=("section",), open=True)
        for index, model in enumerate(visible):
            iid = f"setting-{index}"
            self.optimizer_detail_models[iid] = model
            status_label, semantic = status_presentation(model.get("status"))
            self.optimizer_detail_tree.insert(
                "section-system", "end", iid=iid, text="◉  " + str(model.get("title") or "Unbenannte Einstellung"),
                values=(
                    optimizer_table_cell(model.get("current_state")),
                    optimizer_table_cell(model.get("improve_recommendation")),
                    optimizer_table_cell(status_label, maximum=20),
                    "›",
                ),
                tags=(semantic,),
            )
        if visible:
            self.optimizer_detail_tree.selection_set("setting-0")
            self._set_optimizer_detail(visible[0])
        else:
            self._set_optimizer_detail(None)

    def _select_optimizer_setting(self, _event=None) -> None:
        selection = self.optimizer_detail_tree.selection()
        self._set_optimizer_detail(self.optimizer_detail_models.get(selection[0]) if selection else None)

    def _set_optimizer_detail(self, model: dict[str, object] | None) -> None:
        self.optimizer_selected_model = model
        self.optimizer_detail_scroll_canvas.yview_moveto(0.0)
        self.optimizer_detail_technical_visible = False
        self.optimizer_detail_technical_text.pack_forget()
        self.optimizer_detail_technical_action.text = "Technische Details"
        self.optimizer_detail_technical_action.enabled = model is not None
        self.optimizer_detail_technical_action._draw()
        sections = optimizer_user_detail_sections(model)
        if model is None:
            self.optimizer_detail_title.configure(text="Keine passende Einstellung")
            self.optimizer_detail_state.configure(text=sections["state"])
            self.optimizer_detail_status.configure(text="Status: keine Bewertung")
            for key, widget in self.optimizer_detail_sections.items():
                widget.configure(text=sections[key])
            return
        self.optimizer_detail_title.configure(text=str(model.get("title") or "Unbenannte Einstellung"))
        status_label, _semantic = status_presentation(model.get("status"))
        self.optimizer_detail_state.configure(text=f"Aktueller Zustand: {sections['state']}")
        self.optimizer_detail_status.configure(text=f"Status: {optimizer_table_cell(status_label, maximum=56)}")
        for key, widget in self.optimizer_detail_sections.items():
            widget.configure(text=sections[key])
        guidance = model.get("guidance") if isinstance(model.get("guidance"), dict) else {}
        explainability = model.get("explainability") if isinstance(model.get("explainability"), dict) else {}
        self.optimizer_detail_technical_text.configure(text=(
            f"Rohwerte: current_state={model.get('current_state') or 'Nicht verfügbar'}; "
            f"recommendation={model.get('improve_recommendation') or 'Nicht verfügbar'}; "
            f"status={model.get('status') or 'UNKNOWN'}\n"
            f"Evidenz & Gültigkeit: {model.get('evidence_validity') or 'Nicht verfügbar'}\n"
            f"Restore-/Änderungsinformation: {model.get('restore_change_information') or 'Nicht verfügbar'}\n"
            f"Guidance: {guidance}\nProvenance / Explainability: {explainability}"
        ))

    def _toggle_optimizer_technical_detail(self) -> None:
        if self.optimizer_selected_model is None:
            return
        self.optimizer_detail_technical_visible = not self.optimizer_detail_technical_visible
        if self.optimizer_detail_technical_visible:
            self.optimizer_detail_technical_text.pack(anchor="w", pady=(12, 0))
            self.optimizer_detail_technical_action.text = "Technische Details ausblenden"
        else:
            self.optimizer_detail_technical_text.pack_forget()
            self.optimizer_detail_technical_action.text = "Technische Details"
        self.optimizer_detail_technical_action._draw()

    def _build_tactical_page(self) -> None:
        page = self.pages["Tactical Replay"]
        header = self.ttk.Frame(page, style="Content.TFrame")
        header.pack(fill="x")
        self.tactical_back_button = self.ttk.Button(header, text="← Zurück zum Review", command=self._return_to_embedded_review, state="disabled")
        self.tactical_back_button.pack(side="left")
        self.ttk.Label(header, text="2D Tactical", style="PageTitle.TLabel").pack(side="left", padx=16)
        self.ttk.Label(header, text="GEMEINSAME REPLAY-WAHRHEIT", style="StatusBadge.TLabel").pack(side="right")
        context_bar = self.ttk.Frame(page, style="Card.TFrame", padding=(14, 10))
        context_bar.pack(fill="x", pady=(10, 10))
        self.ttk.Label(context_bar, textvariable=self.tactical_scene_title, style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(side="left")
        self.ttk.Label(context_bar, textvariable=self.tactical_scene_context, style="Muted.TLabel").pack(side="right")
        self.ttk.Label(page, textvariable=self.tactical_scene_note, foreground=_THEME["muted"]).pack(anchor="w", pady=(0, 8))

        self.tactical_empty_state = self.ttk.Frame(page, style="Card.TFrame", padding=24)
        self.ttk.Label(self.tactical_empty_state, text="REPLAY BEREITMACHEN", style="Card.TLabel", font=(self.display_font, 11, "bold")).pack(anchor="w")
        self.ttk.Label(self.tactical_empty_state, text="Tactical Replay verwendet keine eigene Demo-Interpretation. Öffne zuerst eine echte Analyse und übergib anschließend eine ausgewählte Review-Szene.", style="Muted.TLabel", wraplength=820, justify="left").pack(anchor="w", pady=(8, 14))
        for step in ("1 · Demo im Analyzer analysieren", "2 · Szene im Match Review auswählen", "3 · Tactical Replay aus dem Review öffnen"):
            self.ttk.Label(self.tactical_empty_state, text=step, style="Card.TLabel", foreground=_THEME["ice"], font=(self.ui_font, 9, "bold")).pack(anchor="w", pady=3)
        self.ttk.Label(self.tactical_empty_state, text="Erst dann stehen bestätigte Szene, Tick und Replay-Frames zur Verfügung.", style="Muted.TLabel", wraplength=820, justify="left").pack(anchor="w", pady=(12, 0))
        self.tactical_empty_state.pack(fill="x", pady=(12, 0))
        body = self.ttk.Frame(page, style="Content.TFrame")
        self.tactical_runtime_body = body
        scene_panel = self.ttk.Frame(body, style="Card.TFrame", padding=12)
        scene_panel.pack(side="left", fill="y", padx=(0, 8))
        self.ttk.Label(scene_panel, text="SZENEN", style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.tactical_scene_list = self.tk.Listbox(
            scene_panel, width=25, background=_THEME["deep"], foreground=_THEME["ink"],
            selectbackground=_THEME["metal"], selectforeground=_THEME["ink"],
            borderwidth=0, highlightthickness=1, highlightbackground=_THEME["line_soft"],
            activestyle="none", font=("Segoe UI", 9),
        )
        self.tactical_scene_list.pack(fill="both", expand=True, pady=(8, 0))
        self.tactical_scene_list.bind("<<ListboxSelect>>", self._select_tactical_scene)

        # The MASTER's right-hand information rail is retained without
        # inventing a synthetic event timeline.  It projects only the selected
        # review scene, its confirmed frame/tick and the locally stored note.
        detail_panel = self.ttk.Frame(body, style="Card.TFrame", padding=14, width=280)
        detail_panel.pack(side="right", fill="y", padx=(8, 0))
        detail_panel.pack_propagate(False)
        self.ttk.Label(detail_panel, text="SZENENDETAILS", style="Card.TLabel", font=(self.display_font, 10, "bold")).pack(anchor="w")
        self.tactical_detail_title = self.ttk.Label(
            detail_panel, textvariable=self.tactical_scene_title, style="Card.TLabel", wraplength=240, justify="left"
        )
        self.tactical_detail_title.pack(anchor="w", pady=(12, 5))
        self.tactical_detail_context = self.ttk.Label(
            detail_panel, textvariable=self.tactical_scene_context, style="Muted.TLabel", wraplength=240, justify="left"
        )
        self.tactical_detail_context.pack(anchor="w", pady=(0, 12))
        self.ttk.Label(detail_panel, text="FRAME / TICK", style="PageKicker.TLabel").pack(anchor="w")
        self.ttk.Label(detail_panel, textvariable=self.tactical_frame_status, style="Card.TLabel", wraplength=240, justify="left").pack(anchor="w", pady=(4, 12))
        self.ttk.Label(detail_panel, text="REVIEW-NOTIZ", style="PageKicker.TLabel").pack(anchor="w")
        self.ttk.Label(detail_panel, textvariable=self.tactical_scene_note, style="Muted.TLabel", wraplength=240, justify="left").pack(anchor="w", pady=(4, 12))
        self.ttk.Label(
            detail_panel,
            text="Ereignis-Timeline und Kartenbasis werden nur gezeigt, wenn sie in der gemeinsamen Replay-Wahrheit belegt sind.",
            style="Muted.TLabel", wraplength=240, justify="left",
        ).pack(anchor="w", pady=(8, 0))

        map_panel = self.ttk.Frame(body, style="Card.TFrame", padding=8)
        map_panel.pack(side="left", fill="both", expand=True)
        frame_row = self.ttk.Frame(map_panel, style="CardInner.TFrame")
        frame_row.pack(fill="x", pady=(0, 8))
        self.ttk.Label(frame_row, text="POSITIONSFRAME", style="Card.TLabel").pack(side="left")
        self.ttk.Label(frame_row, text="Kartenbasis: nur bei belegtem Asset", style="Muted.TLabel").pack(side="left", padx=(10, 0))
        self.tactical_frame = self.ttk.Scale(frame_row, from_=0, to=0, command=self._set_tactical_frame)
        self.tactical_frame.pack(side="left", fill="x", expand=True, padx=10)
        self.ttk.Label(frame_row, textvariable=self.tactical_frame_status, style="Muted.TLabel").pack(side="right")

        self.tactical_canvas = self.tk.Canvas(
            map_panel, background=_THEME["deep"], borderwidth=0, relief="flat",
            highlightthickness=1, highlightbackground=_THEME["line_soft"], cursor="fleur",
        )
        self.tactical_canvas.pack(fill="both", expand=True)
        self.tactical_canvas.bind("<Configure>", lambda _event: self._draw_tactical_canvas())
        self.tactical_canvas.bind("<MouseWheel>", self._wheel_tactical)
        self.tactical_canvas.bind("<ButtonPress-1>", self._start_tactical_pan)
        self.tactical_canvas.bind("<B1-Motion>", self._drag_tactical_pan)

        controls = self.ttk.Frame(page, style="Card.TFrame", padding=(12, 10))
        self.tactical_controls = controls
        self.tactical_prev_button = self.ttk.Button(controls, text="Vorherige Szene", command=lambda: self._step_tactical_scene(-1), state="disabled")
        self.tactical_prev_button.pack(side="left")
        self.tactical_next_button = self.ttk.Button(controls, text="Nächste Szene", command=lambda: self._step_tactical_scene(1), state="disabled")
        self.tactical_next_button.pack(side="left", padx=6)
        self.ttk.Button(controls, text="In CS2 ansehen", style="Primary.TButton", command=self._open_tactical_in_cs2).pack(side="left", padx=(12, 0))
        self.ttk.Button(controls, text="−", command=lambda: self._zoom_tactical(0.85)).pack(side="left", padx=(18, 4))
        self.ttk.Button(controls, text="+", command=lambda: self._zoom_tactical(1.18)).pack(side="left")
        self.ttk.Button(controls, text="Ansicht zurücksetzen", command=self._reset_tactical_view).pack(side="left", padx=6)
        secondary = self.ttk.Frame(page, style="Content.TFrame")
        self.tactical_secondary = secondary
        self.tactical_button = self.ttk.Button(
            secondary, text="HTML-Export im Browser (Fallback)", command=lambda: self._open_artifact("tactical_replay"), state="disabled"
        )
        self.tactical_button.pack(side="right")
        self.ttk.Label(secondary, textvariable=self.tactical_action_status, foreground=_THEME["muted"]).pack(side="left")

    def _show_tactical_empty_state(self) -> None:
        if self.embedded_tactical is not None:
            return
        for widget in (self.tactical_runtime_body, self.tactical_controls, self.tactical_secondary):
            widget.pack_forget()
        if not self.tactical_empty_state.winfo_manager():
            self.tactical_empty_state.pack(fill="x", pady=(12, 0))

    def _show_tactical_runtime(self) -> None:
        self.tactical_empty_state.pack_forget()
        if not self.tactical_runtime_body.winfo_manager():
            self.tactical_runtime_body.pack(fill="both", expand=True)
        if not self.tactical_controls.winfo_manager():
            self.tactical_controls.pack(fill="x", pady=(10, 0))
        if not self.tactical_secondary.winfo_manager():
            self.tactical_secondary.pack(fill="x", pady=(5, 0))

    def run(self) -> None:
        self.root.mainloop()

    def _choose_demo(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(filetypes=[("CS2 Demo", "*.dem *.dem.zst"), ("Alle Dateien", "*.*")])
        if path:
            demo = Path(path)
            self.controller.begin_import()
            self._mark_demo_import_started(demo)
            self._background(
                "Demo wird lokal geparst …",
                lambda: self.controller.import_demo(demo),
                on_error=lambda message, selected=demo: self._mark_demo_import_failed(selected, message),
            )

    def _set_analysis_controls_available(self, available: bool) -> None:
        for widget in self.workflow_widgets:
            if not available:
                widget.configure(state="disabled")
            elif widget in (self.player, self.profile):
                widget.configure(state="readonly")
            else:
                widget.configure(state="normal")
        self.link_button.configure(state="normal" if available else "disabled")

    def _mark_demo_import_started(self, demo: Path) -> None:
        """Project an explicit, non-actionable parsing state into all tabs."""
        self._stop_import_status_timer()
        self._import_started_at = time.monotonic()
        self._set_analysis_controls_available(False)
        self.review_button.configure(state="disabled")
        self.demo_review_button.configure(state="disabled")
        self.analyzer_projection_review_button.configure(state="disabled")
        self.analyzer_projection_scenes_button.configure(state="disabled")
        self.identity.set(f"Ausgewählte Demo: {demo.name} · lokaler Import und Parse laufen …")
        self.demo_preflight.set("Analyse, Review und Tick-Sprung bleiben gesperrt, bis der Parser diese Demo bestätigt.")
        self.analysis_action_status.set("Parser läuft für die ausgewählte Demo. Analyse starten wird erst nach erfolgreichem Import freigegeben.")
        self.demo_library_text.set(f"Ausgewählte Datei: {demo.name}\nLokaler Import und Parse laufen. Keine vorherige Demo bleibt aktiv.")
        self.demo_selected_text.set(f"{demo.name}\nImport-/Parse-Status: läuft\nNoch keine bestätigten Match-Fakten verfügbar.")
        self.demo_import_text.set("Datei ausgewählt · Parser läuft · 0 Sekunden verstrichen.")
        self.demo_analysis_text.set("Analyse gesperrt · Import/Parse noch nicht bestätigt.")
        self.demo_ready_text.set("Noch nicht analysebereit · auf Parser-Ergebnis warten.")
        self.demo_overview_text.set("Die ausgewählte Demo wird lokal geprüft. Ergebnisse werden erst nach einem erfolgreichen Parse angezeigt.")
        self._refresh_import_status_timer()

    def _refresh_import_status_timer(self) -> None:
        """Keep a long local parse observable without inventing progress values."""
        if self._import_started_at is None:
            return
        elapsed = max(0, int(time.monotonic() - self._import_started_at))
        self.status.set(f"Demo wird lokal geparst · {elapsed} Sekunden verstrichen")
        self.demo_import_text.set(f"Datei ausgewählt · Parser läuft · {elapsed} Sekunden verstrichen.")
        self._import_status_after = self.root.after(1000, self._refresh_import_status_timer)

    def _stop_import_status_timer(self) -> None:
        if self._import_status_after is not None:
            self.root.after_cancel(self._import_status_after)
            self._import_status_after = None
        self._import_started_at = None

    def _mark_demo_import_failed(self, demo: Path, message: str) -> None:
        self._stop_import_status_timer()
        self._set_analysis_controls_available(False)
        self.review_button.configure(state="disabled")
        self.demo_review_button.configure(state="disabled")
        self.analyzer_projection_review_button.configure(state="disabled")
        self.analyzer_projection_scenes_button.configure(state="disabled")
        self.status.set(f"Import fehlgeschlagen: {message}")
        self.identity.set(f"Keine bestätigte Demo geladen · {demo.name} konnte nicht importiert werden.")
        self.demo_preflight.set("Analyse, Review und Tick-Sprung bleiben gesperrt. Eine gültige .dem oder .dem.zst erneut auswählen.")
        self.analysis_action_status.set("Analyse starten nicht verfügbar: Der lokale Demo-Import wurde nicht bestätigt.")
        self.demo_library_text.set(f"Letzter Importversuch: {demo.name}\nFehlgeschlagen: {message}")
        self.demo_selected_text.set(f"{demo.name}\nImport-/Parse-Status: fehlgeschlagen\nKeine Demo ist analysebereit.")
        self.demo_import_text.set(f"Import fehlgeschlagen · {message}")
        self.demo_analysis_text.set("Keine Analyse gestartet.")
        self.demo_ready_text.set("Nicht analysebereit · gültige Demo auswählen und Import wiederholen.")
        self.demo_overview_text.set("Für diese Auswahl liegen keine bestätigten Demo-Fakten vor. Es werden keine Ergebnisse geschätzt oder übernommen.")

    def _open_existing(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="demo-workflow.json öffnen",
            filetypes=[("Improve Yourself Analyse", "demo-workflow.json"), ("JSON", "*.json")],
        )
        if path:
            self._background(
                "Vorhandene Analyse wird lokal geprüft …",
                lambda: self.controller.open_existing_workflow(Path(path)),
            )

    def _link_source(self) -> None:
        from tkinter import filedialog

        if self.controller.result is None:
            self.status.set("Fehler: zuerst eine vorhandene Analyse öffnen")
            return
        path = filedialog.askopenfilename(
            title="Passende Quelldemo zuordnen",
            filetypes=[("CS2 Demo", "*.dem *.dem.zst"), ("Alle Dateien", "*.*")],
        )
        if path:
            self._background(
                "Quelldemo wird per SHA-256 geprüft …",
                lambda: self.controller.link_source_demo(Path(path)),
                recheck=True,
            )

    def _background(
        self, message: str, operation: Callable[[], ShellResult], *, recheck: bool = False,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self.status.set(message)

        def worker() -> None:
            try:
                result = operation()
            except Exception as error:
                error_message = str(error)
                if on_error is None:
                    self.root.after(0, lambda text=error_message: self.status.set(f"Fehler: {text}"))
                else:
                    self.root.after(0, lambda text=error_message: on_error(text))
            else:
                self.root.after(0, lambda: self._finish_background(result, recheck))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_background(self, result: ShellResult, recheck: bool) -> None:
        self._stop_import_status_timer()
        self.analyzer_setup_expanded = False
        self._draw(result)
        if recheck:
            self._preflight()

    def _draw(self, result: ShellResult) -> None:
        self._set_analysis_controls_available(True)
        for box in (self.ct, self.t):
            for child in box.winfo_children():
                child.destroy()
        for item in result.players:
            box = self.ct if item.initial_team == "CT" else self.t
            self.ttk.Label(box, text=item.display_name).pack(anchor="w")
        available = self.controller.available_players()
        self.player_by_label = {f"{item.display_name} · {item.initial_team}": item.player_id for item in available}
        self.player["values"] = tuple(self.player_by_label)
        if self.player_by_label:
            self.player.current(0)
        selected_names = [item.display_name for item in result.players if item.player_id in self.controller.selected_ids]
        selection_text = "Full Demo" if self.controller.selection_mode == "full_demo" else (
            "Gewählt: " + ", ".join(selected_names) if selected_names else "Player Select · keine Spieler gewählt"
        )
        self.chosen.configure(text=selection_text)
        source_name = result.source_demo_name or "nicht zugeordnet"
        self.identity.set(f"Workflow: {result.manifest_path.name} · Quelle: {source_name} · SHA-256: {result.source_sha256[:12]}…")
        self.demo_preflight.set(
            f"Demo-Preflight: {result.parser_status} · {result.map_id} · {result.round_count} Runden · "
            f"{len(result.players)} Spieler · {result.basic_event_count} grundlegende Events"
        )
        phase = "Auswahl bereit" if result.status == "READY_FOR_SELECTION" else f"{result.scene_count} Szenen · Review bereit"
        self.analysis_action_status.set(
            "Demo und Parser-Fakten bestätigt. Analyseprofil und Spielerauswahl prüfen, dann Analyse starten."
            if result.status == "READY_FOR_SELECTION" else
            "Analyse abgeschlossen. Review, Szenen und vorhandener 2D-Pfad sind für diese bestätigte Demo verfügbar."
        )
        self.status.set(f"{result.map_id} · {phase}")
        self.overview_status.set(
            f"{result.source_demo_name or 'Lokaler Workflow'} · {result.map_id} · {result.round_count} Runden · "
            f"{len(result.players)} Spieler · {phase}"
        )
        self.dashboard_rounds.set(f"{result.round_count}\nRunden")
        self.dashboard_players.set(f"{len(result.players)}\nSpieler")
        self.dashboard_scenes.set(f"{result.scene_count}\nSzenen")
        self.dashboard_readiness.set("BEREIT\nReview lokal" if result.status == "READY_FOR_REVIEW" else "BEREIT\nAuswahl lokal")
        self.dashboard_pipeline.set(
            f"{result.map_id} · Parser {result.parser_status}\n"
            f"Auswahl {self.controller.selection_mode}  ·  Szenen {result.scene_count}  ·  {phase}"
        )
        self.dashboard_recent.set(
            f"{result.source_demo_name or result.manifest_path.name}\n"
            f"SHA-256 {result.source_sha256[:12]}… · lokaler Workflow"
        )
        self._render_demo_analyzer_page(result)
        ready = result.status == "READY_FOR_REVIEW"
        self.report_status.set(
            f"{result.scene_count} zusammengeführte Szenen · Quelle {result.source_sha256[:12]}…"
            if ready else "Demo ist gelesen. Report und Timeline entstehen erst nach der expliziten Analyse."
        )
        for button in (self.report_button, self.timeline_button, self.tactical_button):
            button.configure(state="normal" if ready else "disabled")
        self.cs2_button.configure(state="normal" if result.status == "READY_FOR_REVIEW" else "disabled")
        self.review_button.configure(state="normal" if ready else "disabled")
        self.analyzer_projection_review_button.configure(state="normal" if ready else "disabled")
        self.analyzer_projection_scenes_button.configure(state="normal" if ready else "disabled")
        self._render_analyzer_result_projection(result)
        self._set_analyzer_result_mode(result)
        self._close_embedded_review()
        self.embedded_review = None
        self.embedded_scene_id = None
        self._select_profile()
        self._reset_preflight()

    def _select_profile(self, _event=None) -> None:
        self.controller.select_profile(self.profile.get())
        profile = self.controller.profiles[self.controller.profile_id]
        rules = profile.enabled_rule_ids if profile.enabled_rule_ids is not None else ("alle objektiven V1-Regeln",)
        self.rules.configure(text=f"{profile.purpose.title()} · " + ", ".join(rules))
        self.profile_criteria.configure(text=analysis_profile_criteria_view(profile)["text"])
        enabled = set(OBJECTIVE_RULES if profile.enabled_rule_ids is None else profile.enabled_rule_ids)
        for rule_id, variable in self.rule_vars.items():
            variable.set(rule_id in enabled)
        for check in self.rule_checks:
            check.configure(state="normal" if profile.purpose == "custom" else "disabled")

    def _save_custom_rules(self) -> None:
        enabled = tuple(rule_id for rule_id, variable in self.rule_vars.items() if variable.get())
        path = self.controller.update_custom_rules(enabled)
        self.rules.configure(text=f"Custom · lokal gespeichert: {path.name}")
        self.profile_criteria.configure(text=analysis_profile_criteria_view(self.controller.profiles[self.controller.profile_id])["text"])

    def _show_rule_details(self, rule_id: str) -> None:
        dialog = self.tk.Toplevel(self.root)
        dialog.title("Improve Yourself – Regeldetails")
        dialog.configure(background=_THEME["night"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        _enable_dark_titlebar(dialog)
        if self.app_icon is not None:
            dialog.iconphoto(True, self.app_icon)
        card = self.ttk.Frame(dialog, style="Card.TFrame", padding=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        self.ttk.Label(card, text="Regeldetails", style="Card.TLabel", font=("Segoe UI Semibold", 16)).pack(anchor="w")
        self.ttk.Label(card, text=rule_id, style="Muted.TLabel").pack(anchor="w", pady=(4, 14))
        self.ttk.Label(
            card,
            text=("Objektiver, aus der Demo belegter Szenenanker. Mehrere Marker derselben "
                  "Situation werden zu einer Szene zusammengeführt. Die Interpretation bleibt beim Nutzer."),
            style="Card.TLabel", wraplength=460, justify="left",
        ).pack(anchor="w")
        self.ttk.Button(card, text="Schließen", style="Primary.TButton", command=dialog.destroy).pack(anchor="e", pady=(18, 0))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - dialog.winfo_reqwidth()) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - dialog.winfo_reqheight()) // 2)
        dialog.geometry(f"+{x}+{y}")

    def _full(self) -> None:
        self.controller.set_full_demo()
        self._draw(self.controller.result)

    def _reset(self) -> None:
        self.controller.reset_players()
        self._draw(self.controller.result)

    def _team(self, team: str) -> None:
        self.controller.add_team(team)
        self._draw(self.controller.result)

    def _add(self) -> None:
        player_id = self.player_by_label.get(self.player.get())
        if player_id:
            self.controller.add_player(player_id)
            self._draw(self.controller.result)

    def _analyze(self) -> None:
        self._background("Auswahl wird aus demselben Replay neu berechnet …", self.controller.analyze_selection)

    def _open_review(self) -> None:
        try:
            manifest_path = self.controller.validate_current_workflow()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            coordinator = self._coordinator()
            self.embedded_review = EmbeddedReviewSession(
                manifest_path.parent / manifest["artifacts"]["analysis_flow"],
                manifest_path.parent / "review-state.json",
                str(manifest["source_sha256"]),
                coordinator,
            )
            self.embedded_scene_list.delete(0, self.tk.END)
            for scene in self.embedded_review.scenes:
                marker_count = len(scene.anchor_types)
                self.embedded_scene_list.insert(
                    self.tk.END,
                    f"Runde {scene.round_number:02d} · Tick {scene.review_tick} · {marker_count} Marker",
                )
            self._show_analyzer_tab("Review")
            self.embedded_review_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.embedded_review_frame.tkraise()
            self._refresh_embedded_review_boundary()
            if self.embedded_review.scenes:
                self.embedded_scene_list.selection_set(0)
                self.embedded_scene_list.activate(0)
                self._draw_embedded_scene(0)
            else:
                self.embedded_scene_title.set("Keine Szenen für diese Auswahl")
                self.embedded_scene_context.set("Analyse und Review bleiben gültig; die gewählten Kriterien erzeugten keine Szene.")
            self.embedded_cs2_status.set("Review lokal geladen. CS2-Bereitschaft wird beim Tick-Sprung erneut geprüft.")
        except Exception as error:
            self.status.set(f"Fehler: {error}")

    def _close_embedded_review(self) -> None:
        self.embedded_review_frame.place_forget()

    def _refresh_embedded_review_boundary(self) -> None:
        try:
            presentation = self.controller.review_presentation(getattr(self, "review_system_check_payload", None))
            analysis = presentation["analysis"]
            system = presentation["system_check"]
            self.embedded_review_boundary.set(
                f"FAKTEN: {' · '.join(analysis['facts'])}\n"
                f"PRÜFHINWEISE: {' · '.join(analysis['hints'])}\n"
                f"DATENLIMITS: {' · '.join(analysis['limits'])}\n"
                f"NÄCHSTE SCHRITTE: {' · '.join(analysis['next_steps'])}\n"
                f"SYSTEM CHECK (getrennte Quelle): {system['availability']}"
            )
        except (RuntimeError, ValueError):
            self.embedded_review_boundary.set("FAKTEN / HINWEISE / DATENLIMITS / NÄCHSTE SCHRITTE: UNKNOWN / NOT AVAILABLE · SYSTEM CHECK: getrennt und unbekannt")

    def _select_embedded_scene(self, _event=None) -> None:
        selection = self.embedded_scene_list.curselection()
        if selection:
            self._draw_embedded_scene(int(selection[0]))

    def _draw_embedded_scene(self, index: int) -> None:
        if self.embedded_review is None or not 0 <= index < len(self.embedded_review.scenes):
            return
        scene = self.embedded_review.scenes[index]
        self.embedded_scene_id = scene.scene_id
        anchors = ", ".join(scene.anchor_types) or "keine Anker"
        self.embedded_scene_title.set(
            f"Runde {scene.round_number} · Tick {scene.review_tick} · {scene.timecode}"
        )
        self.embedded_scene_context.set(
            f"Kontext {scene.start_tick}–{scene.end_tick} · Marker {', '.join(map(str, scene.marker_ticks))} · {anchors}"
        )
        self.embedded_scene_players.set("Spieler: " + (", ".join(scene.player_names) or "nicht belegt"))
        self.embedded_scene_rules.set("Regeln: " + (", ".join(scene.rule_ids) or "nicht belegt"))
        review = self.embedded_review.review(scene.scene_id)
        self.embedded_state.set(review["state"])
        self.embedded_note.delete("1.0", self.tk.END)
        self.embedded_note.insert("1.0", review["note"])

    def _step_embedded_scene(self, delta: int) -> None:
        if self.embedded_review is None or not self.embedded_review.scenes:
            return
        current = self.embedded_scene_list.curselection()
        index = int(current[0]) if current else 0
        index = max(0, min(len(self.embedded_review.scenes) - 1, index + delta))
        self.embedded_scene_list.selection_clear(0, self.tk.END)
        self.embedded_scene_list.selection_set(index)
        self.embedded_scene_list.activate(index)
        self.embedded_scene_list.see(index)
        self._draw_embedded_scene(index)

    def _save_embedded_review(self) -> None:
        if self.embedded_review is None or self.embedded_scene_id is None:
            return
        try:
            self.embedded_review.save_review(
                self.embedded_scene_id,
                self.embedded_state.get(),
                self.embedded_note.get("1.0", "end-1c"),
            )
            self.embedded_cs2_status.set("Review-Status und Notiz lokal gespeichert.")
        except Exception as error:
            self.embedded_cs2_status.set(f"Nicht gespeichert: {error}")

    def _open_embedded_in_cs2(self) -> None:
        if self.embedded_review is None or self.embedded_scene_id is None:
            return
        self._save_embedded_review()
        scene_id = self.embedded_scene_id
        self.embedded_cs2_status.set("Prüfe CS2, aktive Demo und erlaubten Szenen-Tick …")

        def worker() -> None:
            try:
                result = self.embedded_review.open_in_cs2(scene_id) if self.embedded_review else None
                if result is None:
                    raise RuntimeError("Embedded Review ist nicht geladen")
                message = f"In CS2 geöffnet: {result['demo_name']} · Tick {result['tick']}"
            except Exception as error:
                message = f"Nicht in CS2 geöffnet: {error}"
            self.root.after(0, lambda: self.embedded_cs2_status.set(message))

        threading.Thread(target=worker, daemon=True).start()

    def _open_review_fallback(self) -> None:
        try:
            self._start_review(self._coordinator())
        except Exception as error:
            self.embedded_cs2_status.set(f"Browser-Fallback nicht geöffnet: {error}")

    def _open_tactical_from_review(self) -> None:
        if self.embedded_review is None or self.embedded_scene_id is None:
            return
        self._save_embedded_review()
        try:
            manifest_path = self.controller.validate_current_workflow()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.embedded_tactical = EmbeddedTacticalSession(
                manifest_path.parent / manifest["artifacts"]["replay_v2"],
                manifest_path.parent / manifest["artifacts"]["analysis_flow"],
                str(manifest["source_sha256"]),
            )
            self.embedded_tactical.select_scene(self.embedded_scene_id)
            self.tactical_frame_index = 0
            self.tactical_zoom = 1.0
            self.tactical_pan = [0.0, 0.0]
            self.tactical_back_button.configure(state="normal")
            self.tactical_prev_button.configure(state="normal")
            self.tactical_next_button.configure(state="normal")
            self.tactical_action_status.set("Szene aus dem Analyzer Review übernommen; keine neue Analyse ausgeführt.")
            self._show_tactical_runtime()
            self._show_page("Tactical Replay")
            self._draw_tactical_scene()
        except Exception as error:
            self.embedded_cs2_status.set(f"Tactical Replay nicht geöffnet: {error}")

    def _return_to_embedded_review(self) -> None:
        if self.embedded_tactical and self.embedded_tactical.selected_scene_id:
            self._sync_review_scene(self.embedded_tactical.selected_scene_id)
        self._show_page("Analyzer", record_history=False)
        self._show_analyzer_tab("Review")
        self.embedded_review_frame.tkraise()

    def _sync_review_scene(self, scene_id: str) -> None:
        if self.embedded_review is None:
            return
        index = next(
            (position for position, scene in enumerate(self.embedded_review.scenes) if scene.scene_id == scene_id),
            None,
        )
        if index is None:
            raise ValueError("tactical scene is not present in embedded review")
        self.embedded_scene_list.selection_clear(0, self.tk.END)
        self.embedded_scene_list.selection_set(index)
        self.embedded_scene_list.activate(index)
        self.embedded_scene_list.see(index)
        self._draw_embedded_scene(index)

    def _step_tactical_scene(self, delta: int) -> None:
        if self.embedded_tactical is None:
            return
        scene = self.embedded_tactical.step_scene(delta)
        self._sync_review_scene(scene["scene_id"])
        self.tactical_frame_index = 0
        self._draw_tactical_scene()

    def _select_tactical_scene(self, _event=None) -> None:
        if self.tactical_ignore_selection_event:
            self.tactical_ignore_selection_event = False
            return
        if self.embedded_tactical is None or self.tactical_syncing_selection:
            return
        selected = self.tactical_scene_list.curselection()
        if not selected:
            return
        scene = self.embedded_tactical.scenes[selected[0]]
        self.embedded_tactical.select_scene(scene["scene_id"])
        self._sync_review_scene(scene["scene_id"])
        self.tactical_frame_index = 0
        self._draw_tactical_scene()

    def _draw_tactical_scene(self) -> None:
        if self.embedded_tactical is None:
            return
        scene = self.embedded_tactical.selected_scene()
        scenes = self.embedded_tactical.scenes
        if self.tactical_scene_list.size() != len(scenes):
            self.tactical_scene_list.delete(0, self.tk.END)
            for item in scenes:
                self.tactical_scene_list.insert(
                    self.tk.END,
                    f"R{item['round_number']} · Tick {item['requested_tick']}",
                )
        selected_index = next(index for index, item in enumerate(scenes) if item["scene_id"] == scene["scene_id"])
        if self.tactical_scene_list.curselection() != (selected_index,):
            self.tactical_syncing_selection = True
            self.tactical_ignore_selection_event = True
            try:
                self.tactical_scene_list.selection_clear(0, self.tk.END)
                self.tactical_scene_list.selection_set(selected_index)
                self.tactical_scene_list.see(selected_index)
            finally:
                self.tactical_syncing_selection = False
        frames = scene.get("frames", ())
        self.tactical_frame.configure(to=max(0, len(frames) - 1))
        self.tactical_frame.set(min(self.tactical_frame_index, max(0, len(frames) - 1)))
        self.tactical_frame_index = min(self.tactical_frame_index, max(0, len(frames) - 1))
        review_scene = next(
            item for item in self.embedded_review.scenes if item.scene_id == scene["scene_id"]
        ) if self.embedded_review else None
        if review_scene:
            self.tactical_scene_title.set(
                f"Runde {review_scene.round_number} · Tick {review_scene.review_tick} · {review_scene.timecode}"
            )
            review = self.embedded_review.review(review_scene.scene_id)
            selection = self.embedded_tactical.flow.get("selection", {})
            profile = self.embedded_tactical.flow.get("profile", {})
            self.tactical_scene_context.set(
                f"{self.embedded_tactical.flow.get('source', {}).get('map_id', 'Map nicht belegt')} · "
                f"Szene {review_scene.scene_id} · Spieler {', '.join(review_scene.player_names) or 'nicht belegt'} · "
                f"Profil {profile.get('profile_id', 'nicht belegt')} · Auswahl {selection.get('mode', 'nicht belegt')} · "
                f"Review {review['state']}"
            )
            self.tactical_scene_note.set(
                f"Review-Notiz: {review['note']}" if review.get("note") else "Review-Notiz: keine"
            )
        self._draw_tactical_canvas()

    def _set_tactical_frame(self, value: str) -> None:
        self.tactical_frame_index = int(round(float(value)))
        self._draw_tactical_canvas()

    def _draw_tactical_canvas(self) -> None:
        canvas = getattr(self, "tactical_canvas", None)
        if canvas is None:
            return
        canvas.delete("all")
        width, height = max(canvas.winfo_width(), 2), max(canvas.winfo_height(), 2)
        for x in range(0, width, 80):
            canvas.create_line(x, 0, x, height, fill="#183149")
        for y in range(0, height, 80):
            canvas.create_line(0, y, width, y, fill="#183149")
        if self.embedded_tactical is None:
            canvas.create_text(width / 2, height / 2, text="Szene im Analyzer Review auswählen", fill=_THEME["muted"])
            return
        scene = self.embedded_tactical.selected_scene()
        frames = scene.get("frames", ())
        if not frames:
            canvas.create_text(width / 2, height / 2, text="Keine belegten Positionsframes für diese Szene", fill=_THEME["muted"])
            self.tactical_frame_status.set("Keine Positionsframes")
            return
        self.tactical_frame_index = max(0, min(self.tactical_frame_index, len(frames) - 1))
        frame = frames[self.tactical_frame_index]
        players = frame.get("players", ())
        self.tactical_frame_status.set(
            f"Tick {frame['tick']} · Frame {self.tactical_frame_index + 1}/{len(frames)}"
        )
        if not players:
            canvas.create_text(width / 2, height / 2, text="Keine vollständigen Spielerpositionen in diesem Frame", fill=_THEME["muted"])
            return
        xs, ys = [float(player["x"]) for player in players], [float(player["y"]) for player in players]
        min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
        span = max(max_x - min_x, max_y - min_y, 1.0)
        base_scale = min(width, height) * 0.72 / span
        scale = base_scale * self.tactical_zoom
        center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
        focus = scene.get("focus_player_id")
        for player in players:
            x = width / 2 + (float(player["x"]) - center_x) * scale + self.tactical_pan[0]
            y = height / 2 - (float(player["y"]) - center_y) * scale + self.tactical_pan[1]
            color = "#55aaff" if str(player.get("side", "")).upper() == "CT" else "#ff9f43"
            radius = 10 if player.get("player_id") != focus else 14
            yaw = math.radians(float(player.get("yaw", 0.0)))
            canvas.create_line(x, y, x + math.cos(yaw) * 34, y - math.sin(yaw) * 34, fill=color, width=3)
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline=_THEME["ice"] if radius == 14 else color, width=2)
            canvas.create_text(x + 14, y - 14, text=str(player.get("name", "")), fill=_THEME["ink"], anchor="sw", font=("Segoe UI", 9))

    def _zoom_tactical(self, factor: float) -> None:
        self.tactical_zoom = max(0.5, min(4.0, self.tactical_zoom * factor))
        self._draw_tactical_canvas()

    def _wheel_tactical(self, event) -> None:
        self._zoom_tactical(1.12 if event.delta > 0 else 0.89)

    def _reset_tactical_view(self) -> None:
        self.tactical_zoom = 1.0
        self.tactical_pan = [0.0, 0.0]
        self._draw_tactical_canvas()

    def _start_tactical_pan(self, event) -> None:
        self.tactical_drag_origin = (event.x, event.y)

    def _drag_tactical_pan(self, event) -> None:
        if self.tactical_drag_origin is None:
            return
        previous_x, previous_y = self.tactical_drag_origin
        self.tactical_pan[0] += event.x - previous_x
        self.tactical_pan[1] += event.y - previous_y
        self.tactical_drag_origin = (event.x, event.y)
        self._draw_tactical_canvas()

    def _open_tactical_in_cs2(self) -> None:
        if self.embedded_tactical is None or self.embedded_review is None:
            return
        scene_id = self.embedded_tactical.selected_scene()["scene_id"]
        self.tactical_action_status.set("Prüfe CS2, aktive Demo und erlaubten Szenen-Tick …")

        def worker() -> None:
            try:
                result = self.embedded_review.open_in_cs2(scene_id)
                message = f"In CS2 geöffnet: {result['demo_name']} · Tick {result['tick']}"
            except Exception as error:
                message = f"Nicht in CS2 geöffnet: {error}"
            self.root.after(0, lambda: self.tactical_action_status.set(message))

        threading.Thread(target=worker, daemon=True).start()

    def _open_artifact(self, name: str) -> None:
        try:
            manifest_path = self.controller.validate_current_workflow()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            relative = manifest.get("artifacts", {}).get(name)
            if name in {"review", "tactical_replay"} and (
                name == "review" or not isinstance(relative, str)
            ):
                ensure_tactical_replay_export(manifest_path)
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                relative = manifest.get("artifacts", {}).get(name)
            if not isinstance(relative, str):
                raise ValueError(f"Artefakt ist nicht verfügbar: {name}")
            artifact = (manifest_path.parent / relative).resolve()
            if manifest_path.parent != artifact and manifest_path.parent not in artifact.parents:
                raise ValueError("Artefakt liegt außerhalb des lokalen Workflows")
            if not artifact.is_file():
                raise ValueError(f"Artefaktdatei fehlt: {name}")
            webbrowser.open(artifact.as_uri())
        except Exception as error:
            self.status.set(f"Fehler: {error}")

    def _run_system_check(self) -> None:
        self.system_status.set("Lokale Systemfakten werden read-only erfasst …")

        def worker() -> None:
            try:
                output = run_system_check(self.controller.output_root / "system-check.json")
                payload = json.loads(output.read_text(encoding="utf-8"))
                summary = payload["summary"]
                message = (
                    f"Abgeschlossen: {summary['OK']} OK · {summary['REVIEW']} zu prüfen · "
                    f"{summary['ACTION_REQUIRED']} Handlungsbedarf · keine Änderungen angewendet."
                )
                self.root.after(0, lambda: self._apply_system_scan(payload, message))
            except Exception as error:
                message = f"System Check fehlgeschlagen: {error}"
                self.root.after(0, lambda: self.system_status.set(message))

        threading.Thread(target=worker, daemon=True).start()

    def _load_saved_system_scan(self) -> None:
        path = self.controller.output_root / "system-check.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self._apply_system_scan(payload, "Vorhandener lokaler Systemscan geladen.")

    def _apply_system_scan(self, payload: dict[str, object], status_message: str) -> None:
        view = system_scan_home_view(payload)
        if view is None:
            self.system_status.set("Systemscan-Daten konnten nicht als iy.system_check/v1 bestätigt werden.")
            return
        entries = view["entries"]
        for key in _SYSTEM_SCAN_HOME_FIELDS:
            _label, value, _status = entries[key]
            self.dashboard_system_scan_cells[key].set(value)
        self.dashboard_system_scan_time.set(f"Letzter Scan: {view['generated_at_utc']}")
        self.dashboard_system_scan_overall.set(view["overall"])
        self.dashboard_system_scan_attention.set(view["attention"])
        self.dashboard_system_scan_attention_label.pack(before=self.dashboard_system_scan_details_button, anchor="w", pady=(1, 4))
        self.optimizer_hardware_values = {
            "OS": str(entries["windows"][1]), "CPU": str(entries["cpu"][1]),
            "RAM": str(entries["memory"][1]), "GPU": str(entries["gpu"][1]),
        }
        self._render_optimizer_hardware_chips()
        self._render_system_check_results(payload)
        self.review_system_check_payload = payload
        if self.embedded_review is not None:
            self._refresh_embedded_review_boundary()
        self._render_optimizer_evidence(payload)
        profile = profile_from_system_check(payload)
        if profile is not None:
            try:
                self._render_optimizer_product(optimizer_product_view(profile, rules=matrix_pack_01_rules()))
            except RulePackValidationError:
                self._clear_optimizer_product()
                status_message += " Matrix Pack 01 konnte nicht fail-closed validiert werden; keine Optimizerbewertung angezeigt."
        self.system_status.set(status_message)

    def _render_system_check_results(self, payload: dict[str, object]) -> None:
        view = system_check_result_view(payload)
        if view is None:
            return
        self.optimizer_system_result_view = view

    def _render_optimizer_evidence(self, payload: dict[str, object]) -> None:
        view = optimizer_evidence_view(payload)
        if view is None:
            return
        # Preserve the existing evidence adapter, but do not make its matrix
        # a layout surface.  Technical data is only exposed from a selected
        # setting's right-hand detail panel.
        self.optimizer_evidence_view_data = view

    def _render_optimizer_product(self, view: dict[str, object], domain_filter: str | None = None) -> None:
        self.optimizer_view_data = view
        if domain_filter:
            self.optimizer_active_domain = domain_filter
        self._render_optimizer_overview(view)
        if self.optimizer_detail_view.winfo_ismapped():
            self._render_optimizer_detail_table()

    def _clear_optimizer_product(self) -> None:
        self.optimizer_view_data = None
        self._render_optimizer_overview()
        if self.optimizer_detail_view.winfo_ismapped():
            self._render_optimizer_detail_table()

    def _show_optimizer_detail(self, model: dict[str, object]) -> None:
        self._show_optimizer_detail_screen(str(model.get("domain") or self.optimizer_active_domain))
        self._set_optimizer_detail(model)

    def _coordinator(self) -> Cs2ReviewCoordinator:
        manifest_path = self.controller.validate_current_workflow()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        flow_path = manifest_path.parent / manifest["artifacts"]["analysis_flow"]
        return Cs2ReviewCoordinator(flow_path, str(manifest.get("source_demo_name") or ""))

    def _preflight(self, open_after: bool = False) -> None:
        self._reset_preflight()
        self.preflight_message.set("Prüfe lokale CS2-Bereitschaft …")

        def worker() -> None:
            try:
                coordinator = self._coordinator()
                result = coordinator.preflight()
            except Exception as error:
                message = str(error)
                self.root.after(0, lambda: self._fail_preflight(message))
            else:
                self.root.after(0, lambda: self._finish_preflight(result, coordinator, open_after))

        threading.Thread(target=worker, daemon=True).start()

    def _fail_preflight(self, message: str) -> None:
        self._reset_preflight()
        self.preflight_message.set(f"Nicht bereit: {message}")

    def _finish_preflight(
        self, preflight: ReviewPreflight, coordinator: Cs2ReviewCoordinator, open_after: bool
    ) -> None:
        self.netcon_status.set(
            ("✓" if preflight.netcon_reachable else "✗") + " Lokale CS2-Verbindung: "
            + ("erreichbar" if preflight.netcon_reachable else "nicht erreichbar")
        )
        self.demo_status.set(
            ("✓" if preflight.demo_active else "✗") + " Demo-Modus: "
            + ("aktiv" if preflight.demo_active else "nicht belegt")
        )
        active = preflight.active_demo_name or "nicht erkannt"
        self.filename_status.set(
            ("✓" if preflight.filename_matches else "✗")
            + f" Dateiname: erwartet {preflight.expected_demo_name} · aktiv {active}"
        )
        self.preflight_message.set(preflight.message)
        self.embedded_cs2_status.set(preflight.message)
        if preflight.ready and open_after:
            self._start_review(coordinator)

    def _start_review(self, coordinator: Cs2ReviewCoordinator) -> None:
        result = self.controller._require_result()
        if self.review_server:
            self.review_server.close()
        self.review_server = ReviewCoordinatorServer(result.review_path, coordinator)
        self.review_server.start()
        webbrowser.open(self.review_server.url)

    def _reset_preflight(self) -> None:
        self.netcon_status.set("○ Lokale CS2-Verbindung: noch nicht geprüft")
        self.demo_status.set("○ Demo-Modus: noch nicht geprüft")
        self.filename_status.set("○ Dateiname: noch nicht geprüft")
        self.preflight_message.set("Vor dem Review CS2 prüfen.")

    def _close(self) -> None:
        if self.review_server:
            self.review_server.close()
        self.root.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Open the local real-demo Analyzer shell")
    parser.add_argument("--output", type=Path, default=default_output_root())
    parser.add_argument(
        "--workflow", type=Path,
        help="Open one explicitly selected, fail-closed validated demo-workflow.json at startup",
    )
    args = parser.parse_args()
    controller = AnalyzerShellController(args.output)
    app = AnalyzerShellApp(controller)
    if args.workflow is not None:
        app._draw(controller.open_existing_workflow(args.workflow))
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
