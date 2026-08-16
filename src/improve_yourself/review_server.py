from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .review_state import load_or_create_review_state, scene_id, validate_review_state, write_review_state

MAX_REQUEST_BYTES = 128 * 1024


class ReviewServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], directory: Path, source_hash: str, scenes: list[dict[str, Any]]):
        self.directory = directory
        self.source_hash = source_hash
        self.scenes = scenes
        self.expected_scene_ids = {scene_id(scene) for scene in scenes}
        self.state_path = directory / "review-state.json"
        load_or_create_review_state(self.state_path, source_hash, scenes)
        super().__init__(address, ReviewHandler)


class ReviewHandler(SimpleHTTPRequestHandler):
    server: ReviewServer

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=str(args[2].directory), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        parsed = urlparse(origin)
        return parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == self.server.server_port

    def do_GET(self) -> None:
        if self.path == "/api/review-state":
            payload = load_or_create_review_state(
                self.server.state_path, self.server.source_hash, self.server.scenes
            )
            self._json(HTTPStatus.OK, payload)
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/review-state":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if not self._same_origin():
            self._json(HTTPStatus.FORBIDDEN, {"error": "origin not allowed"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid request size"})
            return
        try:
            raw = json.loads(self.rfile.read(length))
            payload = validate_review_state(raw, self.server.source_hash, self.server.expected_scene_ids)
            write_review_state(self.server.state_path, payload)
        except (ValueError, json.JSONDecodeError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        self._json(HTTPStatus.OK, payload)


def load_workflow(workflow_path: Path) -> tuple[Path, str, list[dict[str, Any]]]:
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    if workflow.get("schema") != "iy.workflow/v1":
        raise ValueError("expected iy.workflow/v1")
    directory = workflow_path.resolve().parent
    replay_path = directory / workflow["artifacts"]["replay"]
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    if replay.get("source_sha256") != workflow.get("source_sha256"):
        raise ValueError("workflow and replay source hashes differ")
    return directory, workflow["source_sha256"], replay["scenes"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the local Improve Yourself review UI and state API")
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        directory, source_hash, scenes = load_workflow(args.workflow)
        server = ReviewServer(("127.0.0.1", args.port), directory, source_hash, scenes)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(f"Review: http://127.0.0.1:{server.server_port}/review.html")
    print("Only this local machine can connect. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
