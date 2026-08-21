from __future__ import annotations

import json
import re
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


@dataclass(frozen=True)
class DemoReadiness:
    connected: bool
    demo_name: str | None
    evidence: str


@dataclass(frozen=True)
class ReviewPreflight:
    netcon_reachable: bool
    demo_active: bool
    filename_matches: bool
    expected_demo_name: str
    active_demo_name: str | None
    message: str

    @property
    def ready(self) -> bool:
        return self.netcon_reachable and self.demo_active and self.filename_matches


class NetconClient:
    def __init__(self, port: int = 21212, *, timeout: float = 1.5) -> None:
        self.port = port
        self.timeout = timeout

    def readiness(self) -> DemoReadiness:
        output = self._exchange(("status", "demo_info"))
        connected = "Client:  Connected [DEMO]" in output or "Client: Connected [DEMO]" in output
        match = re.search(r"Demo contents for\s+(.+?\.dem):", output, re.IGNORECASE)
        return DemoReadiness(connected, match.group(1).strip() if match else None, output)

    def goto_tick(self, tick: int) -> None:
        self._exchange((f"demo_gototick {tick}",), collect=False)

    def _exchange(self, commands: tuple[str, ...], *, collect: bool = True) -> str:
        chunks: list[bytes] = []
        with socket.create_connection(("127.0.0.1", self.port), timeout=self.timeout) as connection:
            connection.settimeout(self.timeout)
            for command in commands:
                connection.sendall(command.encode("ascii") + b"\n")
                time.sleep(0.08)
            if collect:
                deadline = time.monotonic() + self.timeout
                while time.monotonic() < deadline:
                    try:
                        chunk = connection.recv(65536)
                    except TimeoutError:
                        break
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if len(chunk) < 65536:
                        time.sleep(0.05)
        return b"".join(chunks).decode("utf-8", errors="replace")


def cs2_process_running() -> bool | None:
    """Return whether CS2 is running on Windows, or None when it cannot be determined."""
    try:
        result = subprocess.run(
            ("tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"),
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return any(line.lstrip().lower().startswith('"cs2.exe"') for line in result.stdout.splitlines())


class Cs2ReviewCoordinator:
    def __init__(
        self,
        flow_path: Path,
        expected_demo_name: str,
        *,
        netcon: NetconClient | None = None,
        process_probe=cs2_process_running,
    ) -> None:
        flow = json.loads(flow_path.read_text(encoding="utf-8"))
        self.scenes = {scene["scene_id"]: int(scene["review"]["tick"]) for scene in flow["scenes"]}
        if not expected_demo_name:
            raise ValueError("workflow does not disclose the expected demo filename")
        self.expected_demo_name = expected_demo_name
        self.netcon = netcon or NetconClient()
        self.process_probe = process_probe

    def preflight(self) -> ReviewPreflight:
        try:
            readiness = self.netcon.readiness()
        except OSError:
            running = self.process_probe()
            if running is True:
                message = (
                    "CS2 läuft, aber NetCon ist nicht erreichbar. Unter Windows CS2 über die Workshop Tools "
                    "mit -usercon -netconport 21212 starten."
                )
            elif running is False:
                message = (
                    "CS2/NetCon ist nicht erreichbar. CS2 über die Workshop Tools mit "
                    "-usercon -netconport 21212 starten."
                )
            else:
                message = (
                    "Lokale CS2-Verbindung nicht erreichbar. Unter Windows CS2 über die Workshop Tools "
                    "mit -usercon -netconport 21212 starten."
                )
            return ReviewPreflight(
                False, False, False, self.expected_demo_name, None,
                message,
            )
        demo_active = readiness.connected and readiness.demo_name is not None
        filename_matches = demo_active and (
            Path(readiness.demo_name or "").name.casefold() == Path(self.expected_demo_name).name.casefold()
        )
        if not readiness.connected:
            message = "CS2 ist erreichbar, meldet aber keine aktive Demo-Wiedergabe."
        elif not readiness.demo_name:
            message = "CS2 meldet Demo-Modus, aber keinen prüfbaren Demo-Dateinamen."
        elif not filename_matches:
            message = f"Falsche Demo aktiv: erwartet {self.expected_demo_name}, erkannt {readiness.demo_name}."
        else:
            message = f"Bereit: {readiness.demo_name} ist aktiv und eindeutig zugeordnet."
        return ReviewPreflight(
            True, demo_active, filename_matches, self.expected_demo_name, readiness.demo_name, message
        )

    def open_scene(self, scene_id: str, tick: int) -> dict[str, object]:
        expected_tick = self.scenes.get(scene_id)
        if expected_tick is None or expected_tick != tick:
            raise ValueError("scene/tick pair is not present in the generated analysis flow")
        preflight = self.preflight()
        if not preflight.ready:
            raise RuntimeError(preflight.message)
        self.netcon.goto_tick(tick)
        return {"status": "sent", "scene_id": scene_id, "tick": tick, "demo_name": preflight.active_demo_name}


class ReviewCoordinatorServer:
    def __init__(self, review_path: Path, coordinator: Cs2ReviewCoordinator, *, port: int = 0) -> None:
        self.review_path = review_path.resolve()
        self.coordinator = coordinator
        handler = self._handler()
        self.server = ThreadingHTTPServer(("127.0.0.1", port), handler)
        self.thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}/"

    def start(self) -> None:
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        if self.thread:
            self.thread.join(timeout=2)

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        review_path = self.review_path
        coordinator = self.coordinator

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path != "/":
                    self.send_error(404)
                    return
                body = review_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:
                if self.path != "/api/cs2/tick":
                    self.send_error(404)
                    return
                expected_origin = f"http://127.0.0.1:{self.server.server_port}"
                if self.headers.get("Origin") != expected_origin:
                    self._json(403, {"status": "error", "error": "origin rejected"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0 or length > 1024:
                    self._json(413, {"status": "error", "error": "request size rejected"})
                    return
                try:
                    payload = json.loads(self.rfile.read(length))
                    result = coordinator.open_scene(str(payload["scene_id"]), int(payload["tick"]))
                except (KeyError, TypeError, ValueError, RuntimeError, OSError) as error:
                    self._json(409, {"status": "error", "error": str(error)})
                    return
                self._json(200, result)

            def _json(self, status: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        return Handler
