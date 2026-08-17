"""Canonical Preview V1 brand fragments and theme tokens."""

from __future__ import annotations

from pathlib import Path

ASSET_ROOT = Path(__file__).with_name("assets")
THEME_TOKENS = "--iy-night:#07111e;--iy-panel:#102033;--iy-metal:#264766;--iy-ice:#8edbff;--iy-ink:#edf7ff;"


def brand_markup() -> str:
    return '<a class="brand" href="/analyzer.html" aria-label="Improve Yourself Preview V1.1"><img src="/assets/improve-yourself-wordmark-v3.png" alt="Improve Yourself"></a>'
