"""Read one installed CS2 overview through an explicitly selected local converter.

No game files are modified and no game asset is shipped or retained in the repo.
Map revision compatibility with a recorded demo remains unproven.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import math
from pathlib import Path
import re
import subprocess
import tempfile

from .viewer import _verified_radar_transform, world_to_radar

SUPPORTED_MAPS = frozenset({"de_ancient", "de_mirage", "de_anubis", "de_dust2"})


@dataclass(frozen=True)
class LocalMinimap:
    map_id: str
    image: object
    transform: tuple[float, float, float]
    archive_index_sha256: str
    descriptor_sha256: str
    image_sha256: str
    compatibility: str = "unknown"


def overview_transform(text: str, map_id: str) -> tuple[float, float, float]:
    """Accept only the simple, single-level overview format used by this slice."""
    if map_id not in SUPPORTED_MAPS:
        raise ValueError("Für diese Map ist noch keine Kartenbasis geprüft.")
    text = re.sub(r"//[^\n]*", "", text)
    match = re.fullmatch(r'\s*"' + re.escape(map_id) + r'"\s*\{([^{}]*)\}\s*', text)
    if match is None:
        raise ValueError("Kartenbeschreibung passt nicht zur Map oder enthält unbekannte Ebenen.")
    body = match[1]
    tokens = re.findall(r'"([^"\\]*)"', body)
    if len(tokens) % 2 or re.sub(r'"[^"\\]*"', '', body).strip():
        raise ValueError("Kartenbeschreibung ist unvollständig.")
    keys = tokens[::2]
    if len(set(keys)) != len(keys):
        raise ValueError("Kartenbeschreibung enthält doppelte Angaben.")
    fields = dict(zip(keys, tokens[1::2]))
    if fields.get("material") != "overviews/" + map_id:
        raise ValueError("Kartenmaterial passt nicht zur ausgewählten Map.")
    try:
        values = tuple(float(fields[name]) for name in ("pos_x", "pos_y", "scale"))
    except (KeyError, ValueError) as error:
        raise ValueError("Koordinatenzuordnung fehlt oder ist ungültig.") from error
    if not all(math.isfinite(value) for value in values) or values[2] <= 0:
        raise ValueError("Koordinatenzuordnung ist ungültig.")
    if values != _verified_radar_transform(map_id):
        raise ValueError("Die installierte Kartenprojektion hat sich geändert; erneute Prüfung erforderlich.")
    # Native north-up image presentation. A Source rotate flag is not an
    # intrinsic coordinate rotation; image and markers remain north-up together.
    return values


def resolve_archive(directory: Path) -> Path:
    for relative in ("game/csgo/pak01_dir.vpk", "csgo/pak01_dir.vpk", "pak01_dir.vpk"):
        candidate = directory / relative
        if candidate.is_file():
            return candidate.resolve()
    raise ValueError("Keine CS2-Kartenressourcen im ausgewählten Ordner gefunden.")


def load_local_minimap(directory: Path, converter: Path, map_id: str) -> LocalMinimap:
    from PIL import Image

    if map_id not in SUPPORTED_MAPS:
        raise ValueError("Für diese Map ist noch keine Kartenbasis geprüft.")
    archive = resolve_archive(directory)
    converter = converter.resolve()
    if not converter.is_file():
        raise ValueError("Source 2 Viewer CLI wurde nicht gefunden.")
    if archive.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Kartenarchiv-Index überschreitet die unterstützte Größe.")
    index_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="iy-minimap-") as temporary:
        root = Path(temporary)
        descriptor = root / "overview.txt"
        image_path = root / "overview.png"
        for member, output in (
            (f"resource/overviews/{map_id}.txt", descriptor),
            (f"panorama/images/overheadmaps/{map_id}_radar_psd.vtex_c", image_path),
        ):
            args = [str(converter), "-i", str(archive), "--vpk_filepath", member, "-o", str(output)]
            if output == image_path:
                args.append("-d")
            try:
                result = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        timeout=90, check=False)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ValueError("Lokale Kartenkonvertierung konnte nicht abgeschlossen werden.") from error
            if result.returncode or not output.is_file():
                raise ValueError("Kartenressource fehlt oder konnte nicht gelesen werden.")
        if descriptor.stat().st_size > 65536 or image_path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Kartenressource überschreitet die unterstützte Größe.")
        raw_descriptor = descriptor.read_bytes()
        transform = overview_transform(raw_descriptor.decode("utf-8-sig"), map_id)
        raw_image = image_path.read_bytes()
        with Image.open(io.BytesIO(raw_image)) as image:
            if image.format != "PNG" or image.size != (1024, 1024):
                raise ValueError("Kartenbild hat ein nicht unterstütztes Format oder eine andere Größe.")
            decoded = image.convert("RGBA")
    if index_hash != hashlib.sha256(archive.read_bytes()).hexdigest():
        raise ValueError("CS2-Ressourcen wurden beim Laden aktualisiert; bitte erneut laden.")
    return LocalMinimap(map_id, decoded, transform, index_hash,
                        hashlib.sha256(raw_descriptor).hexdigest(), hashlib.sha256(raw_image).hexdigest())


def viewport(width: int, height: int, zoom: float, pan: tuple[float, float]) -> tuple[float, float, float]:
    scale = min(width, height) / 1024 * zoom
    return (width / 2 - 512 * scale + pan[0], height / 2 - 512 * scale + pan[1], scale)


def project_point(minimap: LocalMinimap, x: float, y: float,
                  view: tuple[float, float, float]) -> tuple[float, float]:
    px, py = world_to_radar(x, y, *minimap.transform)
    left, top, scale = view
    return left + px * scale, top + py * scale
