"""Local read-only System Check and Optimizer-input review page."""

from __future__ import annotations

import argparse
import html
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


_CLASSIFICATION = {
    "reliably_automatically_checked": "Zuverlässig automatisch geprüft",
    "reliably_evaluated": "Zuverlässig bewertet",
    "recognized_only": "Nur erkannt",
    "technically_investigated_not_reliably_readable": "Technisch untersucht, nicht belastbar auslesbar",
    "not_implemented": "Noch nicht implementiert",
}


def _load(path: Path, schema: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise ValueError(f"expected {schema}")
    return value


def render_system_review(system_path: Path, optimizer_path: Path, output_path: Path) -> Path:
    system = _load(system_path, "iy.system_check/v1")
    optimizer = _load(optimizer_path, "iy.optimizer_input/v1")
    cards = "".join(
        "<article><h3>{label}</h3><p><strong>{status}</strong> · {classification}</p>"
        "<p>{summary}</p><p class=muted>{relevance}</p><p><strong>Nächster Schritt:</strong> {action}</p></article>".format(
            label=html.escape(str(check.get("label", "Unbenannte Prüfung"))),
            status=html.escape(str((check.get("user_view") or {}).get("status", "Nicht prüfbar / unbekannt"))),
            classification=html.escape(_CLASSIFICATION.get(str(check.get("classification")), "Noch nicht implementiert")),
            summary=html.escape(str(check.get("summary", "Nicht verfügbar."))),
            relevance=html.escape(str((check.get("user_view") or {}).get("relevance", ""))),
            action=html.escape(str((check.get("user_view") or {}).get("action", "Keine automatische Änderung wurde vorgenommen."))),
        ) for check in system.get("checks", []) if isinstance(check, dict)
    )
    readiness = optimizer.get("optimizer_readiness") or {}
    unknown = ", ".join(html.escape(str(item)) for item in readiness.get("unknown_or_unreadable_items", [])) or "keine"
    page = f'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Improve Yourself – System Check</title><style>body{{font-family:system-ui,sans-serif;background:#08111e;color:#edf3fb;margin:0;padding:24px}}main{{max-width:1060px;margin:auto}}h1{{margin:0}}.muted{{color:#b7c6d9}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}}article,section{{background:#111f32;border:1px solid #273a54;border-radius:12px;padding:16px;margin-top:16px}}article{{margin-top:0;border-left:4px solid #ffca62}}h3{{margin:0 0 8px}}p{{line-height:1.45}}code{{word-break:break-all}}@media(max-width:640px){{body{{padding:14px}}}}</style>
<main><h1>Improve Yourself · System Check</h1><p class="muted">Lokale read-only Diagnosebasis für die spätere Optimizer-Planung. Keine Einstellung wurde geändert.</p>
<section><h2>Optimizer-Eingang</h2><p><strong>Planungsinput bereit.</strong> Automatisches Apply/Restore: <strong>nein</strong>. Technisch unbekannt oder nicht belastbar auslesbar: <code>{unknown}</code>.</p><p class="muted">Der Optimizer erhält Ist-Zustand, Bewertung, Priorität, Empfehlung und Evidenz. Unbekannte Werte bleiben unbekannt.</p></section>
<section><h2>System-Check-Ergebnisse</h2><div class="cards">{cards}</div></section>
<section><h2>Grenze</h2><p>Diese Ansicht ist getrennt von Demo Analyzer, 2D Tactical Replay und einer späteren 3D-Ansicht. Sie führt keine Treiber-, Registry-, AMD-/NVIDIA-, BIOS-/UEFI- oder Windows-Änderung aus.</p></section></main></html>'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")
    return output_path


def _serve(directory: Path, port: int) -> None:
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(directory), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Review: http://127.0.0.1:{server.server_port}/system-review.html")
    print("Only this local machine can connect. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render or serve the local System Check / Optimizer Input review")
    parser.add_argument("system_check", type=Path)
    parser.add_argument("optimizer_input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/system-review/system-review.html"))
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8879)
    args = parser.parse_args()
    try:
        output = render_system_review(args.system_check, args.optimizer_input, args.output)
        print(output)
        if args.serve:
            _serve(output.resolve().parent, args.port)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
