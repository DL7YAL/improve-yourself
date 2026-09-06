from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

from improve_yourself.ui_design import (
    CANVA_OPTIMIZER_THEME,
    CANVA_PAGE_PRESENTATION,
    CANVA_THEME,
    CANVA_UI_AUTHORITY,
)


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "docs" / "design" / "CANVA_UI_AUTHORITY_MANIFEST.json"
RUNTIME_REVIEW_MANIFEST = ROOT / "docs" / "design" / "CANVA_UI_RUNTIME_REVIEW_MANIFEST.json"


def _png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    assert header[12:16] == b"IHDR"
    return struct.unpack(">II", header[16:24])


def test_canva_revision_25_export_is_complete_and_hash_bound() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema"] == "iy.ui.canva_authority/v1"
    assert manifest["status"] == "BINDING_VISUAL_AUTHORITY"
    assert manifest["design_id"] == CANVA_UI_AUTHORITY["design_id"] == "DAHUBn5D2aM"
    assert manifest["revision"] == CANVA_UI_AUTHORITY["revision"] == 25
    assert [page["page_number"] for page in manifest["pages"]] == list(range(1, 9))
    assert len({page["page_id"] for page in manifest["pages"]}) == 8

    for page in manifest["pages"]:
        export = MANIFEST.parent / page["file"]
        assert export.is_file()
        assert _png_dimensions(export) == (page["width"], page["height"])
        assert hashlib.sha256(export.read_bytes()).hexdigest() == page["sha256"]


def test_canva_runtime_review_covers_every_route_and_viewport() -> None:
    manifest = json.loads(RUNTIME_REVIEW_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema"] == "iy.ui.canva_runtime_review/v1"
    assert manifest["status"] == "READY_FOR_TRISTAN_REVIEW"
    assert manifest["authority"] == {
        "design_id": "DAHUBn5D2aM",
        "revision": 25,
        "manifest": "CANVA_UI_AUTHORITY_MANIFEST.json",
    }
    expected_pages = set(CANVA_PAGE_PRESENTATION)
    expected_viewports = {(1536, 1024), (1080, 720)}
    screenshots = manifest["screenshots"]
    assert len(screenshots) == len(expected_pages) * len(expected_viewports)
    assert {entry["runtime_page"] for entry in screenshots} == expected_pages
    for page in expected_pages:
        assert {
            (entry["width"], entry["height"])
            for entry in screenshots
            if entry["runtime_page"] == page
        } == expected_viewports
    for entry in screenshots:
        screenshot = RUNTIME_REVIEW_MANIFEST.parent / entry["file"]
        assert screenshot.is_file()
        assert _png_dimensions(screenshot) == (entry["width"], entry["height"])
        assert hashlib.sha256(screenshot.read_bytes()).hexdigest() == entry["sha256"]


def test_every_old_ui_manifest_is_superseded() -> None:
    manifests = (
        ROOT / "docs" / "design" / "ui-reference" / "UI_REFERENCE_MANIFEST.json",
        ROOT / "Data" / "UI" / "Optimizer" / "MASTER_MANIFEST.json",
    )
    for path in manifests:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["status"] == "SUPERSEDED"
        entries = document.get("files", document.get("source_exports", ()))
        assert entries
        assert {entry["status"] for entry in entries} == {"SUPERSEDED"}


def test_canva_page_mapping_covers_every_runtime_route() -> None:
    assert {key: value["page"] for key, value in CANVA_PAGE_PRESENTATION.items()} == {
        "Dashboard": 1,
        "Analyzer": 2,
        "Benchmark": 3,
        "My Improvement": 4,
        "Tactical Replay": 5,
        "System Check / Optimizer": 6,
        "Settings": 7,
        "Reports": 1,
    }
    assert CANVA_PAGE_PRESENTATION["Dashboard"]["nav"] == "Home"
    assert CANVA_PAGE_PRESENTATION["Tactical Replay"]["nav"] == "2D Tactical"
    assert CANVA_PAGE_PRESENTATION["Settings"]["nav"] == "Einstellungen"


def test_optimizer_uses_the_shared_canva_shell_palette() -> None:
    assert CANVA_OPTIMIZER_THEME["page"] == CANVA_THEME["night"]
    assert CANVA_OPTIMIZER_THEME["surface"] == CANVA_THEME["panel"]
    assert CANVA_OPTIMIZER_THEME["surface_raised"] == CANVA_THEME["panel_high"]
    assert CANVA_OPTIMIZER_THEME["accent"] == CANVA_THEME["cyan"]


def test_optimizer_full_window_master_is_not_activated() -> None:
    source = (ROOT / "src" / "improve_yourself" / "analyzer_shell.py").read_text(encoding="utf-8")
    build = source[source.index("def _build_system_page"):source.index("def _optimizer_header")]
    show_page = source[source.index("def _show_page"):source.index("def _go_back")]
    assert "optimizer_master_canvas" not in build
    assert "optimizer_master_canvas" not in show_page
    assert 'self._show_page("Dashboard", record_history=False)' in source
    assert "class CanvaSurface" in source
    assert "class CanvaAction" in source
