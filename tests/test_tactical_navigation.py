"""Exercise the actual shell navigation handler without a display server."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from improve_yourself.analyzer_shell import AnalyzerShellApp


def shell(status="READY_FOR_REVIEW"):
    app = object.__new__(AnalyzerShellApp)
    app.controller = SimpleNamespace(result=SimpleNamespace(status=status))
    app.embedded_tactical = None
    app.embedded_review = None
    app.embedded_scene_id = None
    app._show_page = Mock()
    app._show_tactical_empty_state = Mock()
    app._open_tactical_from_review = Mock()
    app.status = Mock()
    app.tactical_scene_note = Mock()

    def open_review():
        app.embedded_review = object()
        app.embedded_scene_id = "scene-1"

    app._open_review = Mock(side_effect=open_review)
    return app


def test_ready_match_navigation_initializes_review_then_tactical_without_parsing():
    app = shell()
    app._navigate_page("Tactical Replay")
    app._open_review.assert_called_once_with()
    app._open_tactical_from_review.assert_called_once_with()
    assert app.embedded_scene_id == "scene-1"
    app._show_page.assert_not_called()  # real Tactical opener owns presentation


def test_existing_review_selection_is_preserved():
    app = shell()
    app.embedded_review = object()
    app.embedded_scene_id = "selected-scene-8"
    app._navigate_page("Tactical Replay")
    app._open_review.assert_not_called()
    app._open_tactical_from_review.assert_called_once_with()
    assert app.embedded_scene_id == "selected-scene-8"


def test_existing_tactical_is_resumed_without_losing_map_or_timeline():
    app = shell()
    session = app.embedded_tactical = object()
    app.tactical_minimap = object()
    app.tactical_frame_index = 8
    app._navigate_page("Tactical Replay")
    assert app.embedded_tactical is session
    assert app.tactical_frame_index == 8
    app._show_page.assert_called_once_with("Tactical Replay")
    app._open_review.assert_not_called()
    app._open_tactical_from_review.assert_not_called()


@pytest.mark.parametrize("status", [None, "READY_FOR_SELECTION", "FAILED"])
def test_unready_match_clears_old_tactical_and_shows_explanation(status):
    app = shell(status)
    if status is None:
        app.controller.result = None
    app.embedded_tactical = object()
    app.tactical_minimap = object()
    app._navigate_page("Tactical Replay")
    assert app.embedded_tactical is None
    assert app.tactical_minimap is None
    app._open_review.assert_not_called()
    app._open_tactical_from_review.assert_not_called()
    app.tactical_scene_note.set.assert_called_once()


def test_empty_or_rejected_review_does_not_open_tactical():
    app = shell()
    app._open_review = Mock()  # no valid scene produced
    app._navigate_page("Tactical Replay")
    app._open_tactical_from_review.assert_not_called()
    app.status.set.assert_called_once()


def test_other_navigation_keeps_existing_behavior():
    app = shell()
    app._navigate_page("Dashboard")
    app._show_page.assert_called_once_with("Dashboard")
    app._open_review.assert_not_called()
