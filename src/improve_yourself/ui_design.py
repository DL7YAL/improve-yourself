"""Canva revision 25 presentation contract for the local product shell.

This module contains presentation facts only.  It must never become a source
for runtime values, feature availability, analysis results or optimizer
recommendations.
"""

from __future__ import annotations


CANVA_UI_AUTHORITY = {
    "design_id": "DAHUBn5D2aM",
    "revision": 25,
    "title": "Versuch.nr1",
    "manifest": "docs/design/CANVA_UI_AUTHORITY_MANIFEST.json",
}


# Page 1 establishes the shared midnight shell.  Module colors stay accents;
# large surfaces remain dark so every route reads as one application.
CANVA_THEME = {
    "night": "#010914",
    "deep": "#031321",
    "panel": "#041626",
    "panel_high": "#071D31",
    "panel_hover": "#0A2740",
    "card": "#041626",
    "sidebar": "#010B16",
    "border": "#0A2B45",
    "border_soft": "#071E31",
    "border_active": "#087DD0",
    "metal": "#0877C9",
    "cyan": "#00B7F4",
    "line": "#00A9E8",
    "line_soft": "#082338",
    "accent": "#0877C9",
    "accent_bright": "#00B7F4",
    "accent_strong": "#086DB5",
    "ice": "#EAF3FA",
    "ink": "#EAF3FA",
    "secondary": "#A7B5C3",
    "muted": "#718397",
    "success": "#27D89A",
    "warning": "#F2BF3F",
    "danger": "#E05A66",
    "violet": "#A546E8",
}


CANVA_MODULE_ACCENTS = {
    "ANALYZER": "#20D99A",
    "DEMO": "#A546E8",
    "TACTICAL": "#00B7F4",
    "SYSTEM_OPTIMIZER": "#F2BF3F",
    "GRAPHICS_OPTIMIZER": "#20D99A",
    "NETWORK_OPTIMIZER": "#A546E8",
    "BIOS_OPTIMIZER": "#F29B38",
    "BENCHMARK": "#00B7F4",
    "IMPROVEMENT": "#2588FF",
}


# Optimizer components use the same shell scale.  The extra semantic keys are
# aliases for component roles, not a separate theme or second application.
CANVA_OPTIMIZER_THEME = {
    "page": CANVA_THEME["night"],
    "surface": CANVA_THEME["panel"],
    "surface_raised": CANVA_THEME["panel_high"],
    "surface_hero": CANVA_THEME["panel"],
    "surface_detail": CANVA_THEME["deep"],
    "surface_input": "#02101D",
    "surface_hover": CANVA_THEME["panel_hover"],
    "border": CANVA_THEME["border"],
    "border_soft": CANVA_THEME["border_soft"],
    "border_bright": CANVA_THEME["border_active"],
    "accent": CANVA_THEME["cyan"],
    "accent_soft": "#07527B",
    "text": CANVA_THEME["ink"],
    "secondary": CANVA_THEME["secondary"],
    "muted": CANVA_THEME["muted"],
    "success": CANVA_THEME["success"],
    "warning": CANVA_THEME["warning"],
    "unknown": "#95A7B7",
}


CANVA_SHELL_STATUS = (
    ("LOCAL", "Keine Cloud-Pflicht"),
    ("PRIVATE", "Daten bleiben lokal"),
    ("V1 PREVIEW", "Lokaler Prüfstand"),
    ("CANVA R25", "Visuelle Autorität"),
)


CANVA_PAGE_PRESENTATION = {
    "Dashboard": {
        "page": 1,
        "nav": "Home",
        "title": "Willkommen zurück!",
        "subtitle": "Dein lokales Command Center für Analyse, Review und kontinuierliche Verbesserung.",
    },
    "Analyzer": {
        "page": 2,
        "nav": "Improve Analyzer",
        "title": "Improve Analyzer",
        "subtitle": "Detaillierte Match-Analyse auf Basis belegter lokaler Demos und objektiver Regeln.",
    },
    "Benchmark": {
        "page": 3,
        "nav": "Improve Benchmark",
        "title": "Improve Benchmark",
        "subtitle": "Reproduzierbare Messungen erscheinen erst nach freigegebenem Build und tatsächlichem Lauf.",
    },
    "My Improvement": {
        "page": 4,
        "nav": "My Improvement",
        "title": "My Improvement",
        "subtitle": "Entwicklung wird nur aus vergleichbarer lokaler Evidenz sichtbar gemacht.",
    },
    "Tactical Replay": {
        "page": 5,
        "nav": "2D Tactical",
        "title": "2D Tactical Replay",
        "subtitle": "Positionen, Szenen und Ticks aus derselben kanonischen Replay-Wahrheit.",
    },
    "System Check / Optimizer": {
        "page": 6,
        "nav": "Improve Optimizer",
        "title": "Improve Optimizer",
        "subtitle": "Lokale Systemfakten sicher prüfen und read-only einordnen.",
    },
    "Settings": {
        "page": 7,
        "nav": "Einstellungen",
        "title": "Einstellungen",
        "subtitle": "Lokales Profil, Datenschutz und belegte Darstellungsoptionen.",
    },
    "Reports": {
        "page": 1,
        "nav": "Reports",
        "title": "Reports",
        "subtitle": "Nachvollziehbare Artefakte aus der aktuellen lokalen Analyse.",
    },
}


def page_presentation(page_key: str) -> dict[str, object]:
    """Return a copy so callers cannot mutate the shared visual contract."""
    return dict(CANVA_PAGE_PRESENTATION[page_key])
