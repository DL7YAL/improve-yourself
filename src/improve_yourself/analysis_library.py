"""Explicit, local navigation index for completed analyses; never workflow truth."""
from __future__ import annotations

import json
import os
import hashlib
import secrets
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable


LIBRARY_SCHEMA = "iy.local_analysis_library/v1"
_V2_SCHEMA = "iy.demo_workflow/v1"
_V1_SCHEMA = "iy.workflow/v1"


class LocalAnalysisLibrary:
    """Persist only explicit workflow references and presentation metadata.

    Entries are inert until the supplied canonical validator accepts their
    manifest again.  This class never searches directories, parses demos, or
    copies workflow artifacts.
    """

    def __init__(self, index_path: Path, validator: Callable[[Path], Path]) -> None:
        self.index_path = index_path.resolve()
        self._validator = validator

    def register(self, manifest_path: Path) -> dict[str, object]:
        manifest_path = self._validator(manifest_path).resolve()
        manifest = self._read_manifest(manifest_path)
        if manifest.get("schema") != _V2_SCHEMA or manifest.get("status") != "READY_FOR_REVIEW":
            raise ValueError("only a validated READY_FOR_REVIEW V2 workflow can be registered")
        entry = self._metadata(manifest_path, manifest)
        entry["registration_seal"] = self._seal(entry)
        document = self._load_document()
        entries = [item for item in document["entries"] if item.get("manifest_path") != entry["manifest_path"]]
        entries.append(entry)
        document["entries"] = entries
        self._write_document(document)
        return dict(entry, state="READY", reason="Validated local workflow")

    def remove(self, manifest_path: Path) -> None:
        reference = str(manifest_path.resolve())
        document = self._load_document()
        document["entries"] = [item for item in document["entries"] if item.get("manifest_path") != reference]
        self._write_document(document)

    def entries(self) -> tuple[dict[str, object], ...]:
        result: list[dict[str, object]] = []
        for raw in self._load_document()["entries"]:
            if not isinstance(raw, dict):
                continue
            result.append(self._inspect(raw))
        return tuple(result)

    def _inspect(self, entry: dict[str, object]) -> dict[str, object]:
        view = {key: entry.get(key) for key in ("manifest_path", "demo_basename", "map_id", "source_hash_prefix", "scene_count", "workflow_type")}
        if not isinstance(entry.get("registration_seal"), str) or not secrets.compare_digest(entry["registration_seal"], self._seal(entry)):
            return dict(view, state="INVALID", reason="Registration evidence is invalid")
        reference = entry.get("manifest_path")
        if not isinstance(reference, str) or not reference:
            return dict(view, state="INVALID", reason="Malformed library reference")
        path = Path(reference)
        if ".." in path.parts:
            return dict(view, state="INVALID", reason="Malformed library reference")
        if not path.is_file():
            return dict(view, state="UNAVAILABLE", reason="Registered workflow is unavailable")
        try:
            manifest = self._read_manifest(path)
        except (OSError, ValueError, json.JSONDecodeError):
            return dict(view, state="INVALID", reason="Registered manifest is invalid")
        if manifest.get("schema") == _V1_SCHEMA:
            return dict(view, state="LEGACY V1", reason="Legacy workflow is not routed to V2")
        if path.name != "demo-workflow.json":
            return dict(view, state="INVALID", reason="Unsupported workflow filename")
        if manifest.get("schema") != _V2_SCHEMA:
            return dict(view, state="INVALID", reason="Unsupported workflow schema")
        try:
            self._validator(path)
        except (OSError, ValueError, json.JSONDecodeError):
            return dict(view, state="TAMPERED", reason="Canonical workflow validation failed")
        source_name = manifest.get("source_demo_name")
        if not isinstance(source_name, str) or not source_name:
            return dict(view, state="MISSING SOURCE LINK", reason="Source-link metadata requires safe relink")
        return dict(view, state="READY", reason="Validated local workflow")

    def _load_document(self) -> dict[str, object]:
        try:
            value = json.loads(self.index_path.read_text(encoding="utf-8"))
            if isinstance(value, dict) and value.get("schema") == LIBRARY_SCHEMA and isinstance(value.get("entries"), list):
                return {"schema": LIBRARY_SCHEMA, "entries": value["entries"]}
        except (OSError, json.JSONDecodeError):
            pass
        return {"schema": LIBRARY_SCHEMA, "entries": []}

    def _write_document(self, document: dict[str, object]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(prefix=self.index_path.name + ".", suffix=".tmp", dir=self.index_path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(document, stream, ensure_ascii=False, indent=2)
                stream.flush(); os.fsync(stream.fileno())
            temporary.replace(self.index_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _seal(self, entry: dict[str, object]) -> str:
        payload = {key: value for key, value in entry.items() if key != "registration_seal"}
        return hashlib.sha256(self._registration_token() + json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def _registration_token(self) -> bytes:
        path = self.index_path.with_suffix(self.index_path.suffix + ".registration")
        try:
            token = path.read_bytes()
            if len(token) == 32:
                return token
        except OSError:
            pass
        path.parent.mkdir(parents=True, exist_ok=True)
        token = secrets.token_bytes(32)
        handle, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(token); stream.flush(); os.fsync(stream.fileno())
            temporary.replace(path)
        finally:
            if temporary.exists(): temporary.unlink()
        return token

    @staticmethod
    def _read_manifest(path: Path) -> dict[str, object]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("manifest must be an object")
        return value

    @staticmethod
    def _metadata(path: Path, manifest: dict[str, object]) -> dict[str, object]:
        counts = manifest.get("counts") if isinstance(manifest.get("counts"), dict) else {}
        preflight = manifest.get("preflight") if isinstance(manifest.get("preflight"), dict) else {}
        return {
            "manifest_path": str(path), "demo_basename": str(manifest.get("source_demo_name") or "unknown"),
            "map_id": str(preflight.get("map_id") or "unknown"),
            "source_hash_prefix": str(manifest.get("source_sha256") or "")[:12],
            "scene_count": counts.get("scenes") if isinstance(counts.get("scenes"), int) else None,
            "workflow_type": "V2", "last_observed_utc": datetime.now(UTC).isoformat(),
        }
