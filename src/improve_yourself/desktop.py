"""Native Preview V1 shell for the local Analyzer server."""

from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Any

from .analyzer_server import AnalyzerServer, create_server
from .branding import ASSET_ROOT


class DesktopBridge:
    def __init__(self, server: AnalyzerServer) -> None:
        # pywebview recursively enumerates public attributes of ``js_api``.
        # Keeping the native WinForms/WebView2 object public makes that
        # enumeration cross the STA boundary during startup.  Only callable
        # bridge methods are part of the JavaScript API.
        self._server = server
        self._window: Any | None = None

    def choose_demo(self) -> dict[str, object]:
        """Open a native local-file dialog; no upload or browser dialog is used."""
        if self._window is None:
            return {"ok": False, "error": "Desktopfenster ist noch nicht bereit."}
        try:
            import webview

            selected = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("CS2 demos (*.dem;*.dem.zst;*.dem.bz2)",),
            )
            if not selected:
                return {"ok": False, "error": "Keine Demo ausgewählt."}
            self._server.select_demo(Path(selected[0]))
            return {"ok": True}
        except (OSError, ValueError, RuntimeError) as error:
            return {"ok": False, "error": str(error)}


def run_desktop_app(output_root: Path, *, port: int = 0, initial_demo: Path | None = None, max_mib: int = 2048, max_frames: int = 256) -> int:
    """Run one native window and stop the dedicated loopback server on close."""
    try:
        import webview
    except ImportError as error:  # pragma: no cover - packaging/runtime diagnostic
        raise RuntimeError("Die Desktop-WebView-Laufzeit ist nicht installiert.") from error

    server = create_server(output_root, port, max_mib=max_mib, max_frames=max_frames)
    if initial_demo is not None:
        server.select_demo(initial_demo)
    worker = Thread(target=server.serve_forever, name="improve-yourself-loopback", daemon=True)
    worker.start()
    bridge = DesktopBridge(server)
    window = webview.create_window(
        "IMPROVE YOURSELF · PREVIEW V1.1", f"http://127.0.0.1:{server.server_port}/analyzer.html", js_api=bridge,
        width=1500, height=980, min_size=(1080, 720), background_color="#07111e", text_select=True,
    )
    bridge._window = window
    try:
        # On Windows the WinForms backend creates its STA UI thread and then
        # returns from start().  The loopback server must therefore live until
        # the native window is actually closed, not merely until that call
        # returns.
        webview.start(
            gui="edgechromium",
            debug=False,
            private_mode=True,
            icon=str(ASSET_ROOT / "improve-yourself-logo-v3.ico"),
        )
        if not window.events.shown.wait(15):
            raise RuntimeError("Das Improve-Yourself-Fenster konnte nicht initialisiert werden.")
        window.events.closed.wait()
    finally:
        server.shutdown(); server.server_close(); worker.join(timeout=5)
    return 0
