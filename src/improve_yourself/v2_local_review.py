"""Fail-closed, loopback-only serving of a completed canonical V2 workflow."""
from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .demo_workflow import _validate_reusable_workflow, ensure_tactical_replay_export


class V2LocalReviewServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], directory: Path, artifacts: set[str]) -> None:
        self.directory = directory
        self.artifacts = artifacts
        super().__init__(address, V2LocalReviewHandler)


class V2LocalReviewHandler(BaseHTTPRequestHandler):
    server: V2LocalReviewServer

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def do_GET(self) -> None:
        requested = unquote(urlparse(self.path).path).lstrip("/") or "review.html"
        if requested not in self.server.artifacts:
            self.send_error(HTTPStatus.NOT_FOUND, "artifact not available")
            return
        path = (self.server.directory / requested).resolve()
        if self.server.directory not in path.parents or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "artifact not available")
            return
        body = path.read_bytes()
        content_type = "text/html; charset=utf-8" if path.suffix == ".html" else "application/json; charset=utf-8"
        if path.suffix == ".txt":
            content_type = "text/plain; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        self.send_error(HTTPStatus.NOT_FOUND, "no mutable API is provided")


def load_v2_review_workflow(manifest_path: Path) -> tuple[Path, dict[str, Any], set[str]]:
    """Load only an intact, READY_FOR_REVIEW V2 workflow with its matching source hash."""
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_hash = manifest.get("source_sha256")
    if manifest.get("schema") != "iy.demo_workflow/v1":
        raise ValueError("V2 review requires an iy.demo_workflow/v1 manifest")
    if manifest.get("status") != "READY_FOR_REVIEW":
        raise ValueError("V2 review requires a workflow completed through READY_FOR_REVIEW")
    if not isinstance(source_hash, str) or len(source_hash) != 64:
        raise ValueError("V2 review requires a 64-character source hash")
    if not _validate_reusable_workflow(manifest_path, source_hash):
        raise ValueError("V2 review rejected the workflow: source-bound artifacts or Replay V2 integrity validation failed")
    root = manifest_path.parent.resolve()
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("workflow artifacts must be an object")
    allowed = {"review.html"}
    for key in ("review", "tactical_replay", "report", "timeline", "analysis_flow", "cs2_review_commands"):
        value = artifacts.get(key)
        if isinstance(value, str) and value and Path(value).name == value:
            allowed.add(value)
    return root, manifest, allowed


def prepare_v2_local_review(manifest_path: Path) -> tuple[Path, set[str]]:
    """Validate first, then lazily produce the existing V2 tactical HTML artifact."""
    root, _manifest, _allowed = load_v2_review_workflow(manifest_path)
    ensure_tactical_replay_export(manifest_path)
    root, _manifest, allowed = load_v2_review_workflow(manifest_path)
    if "tactical-replay.html" not in allowed:
        raise ValueError("V2 tactical replay export was not registered")
    return root, allowed


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve a validated canonical V2 review on loopback only")
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    try:
        directory, artifacts = prepare_v2_local_review(args.workflow)
        if args.prepare_only:
            print(directory / "review.html")
            return 0
        server = V2LocalReviewServer(("127.0.0.1", args.port), directory, artifacts)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
