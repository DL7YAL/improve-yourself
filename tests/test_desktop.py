import sys
from threading import Event
from types import SimpleNamespace

from improve_yourself.desktop import run_desktop_app


def test_desktop_shell_uses_loopback_window_and_stops_cleanly(tmp_path, monkeypatch) -> None:
    captured = {}

    def create_window(title, url, **kwargs):
        captured.update(title=title, url=url, kwargs=kwargs)
        shown, closed = Event(), Event()
        shown.set(); closed.set()
        return SimpleNamespace(events=SimpleNamespace(shown=shown, closed=closed))

    fake_webview = SimpleNamespace(create_window=create_window, start=lambda **kwargs: captured.update(start=kwargs))
    monkeypatch.setitem(sys.modules, "webview", fake_webview)

    assert run_desktop_app(tmp_path / "desktop-data") == 0
    assert captured["title"] == "IMPROVE YOURSELF · PREVIEW V1"
    assert captured["url"].startswith("http://127.0.0.1:")
    assert captured["kwargs"]["js_api"] is not None
    assert captured["start"]["gui"] == "edgechromium"
