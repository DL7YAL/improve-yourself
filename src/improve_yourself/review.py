from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value


def _status_class(value: str) -> str:
    return {"OK": "ok", "REVIEW": "review", "ACTION_REQUIRED": "action"}.get(value, "review")


def _user_quality_warnings(quality: dict[str, Any]) -> list[str]:
    warnings = [str(value) for value in quality.get("warnings", [])]
    readable = [
        value for value in warnings
        if not any(token in value for token in ("KeyError", "Traceback", "Exception"))
    ]
    if warnings and not readable:
        return ["Ein optionaler Datenkanal konnte nicht geladen werden; die betroffene Analyse bleibt eingeschränkt."]
    return readable


def render_review_surface(
    system_path: Path,
    analysis_path: Path,
    replay_path: Path,
    viewer_path: Path,
    output_path: Path,
) -> Path:
    system = _load(system_path)
    analysis = _load(analysis_path)
    replay = _load(replay_path)
    if system.get("schema") != "iy.system_check/v1":
        raise ValueError("expected iy.system_check/v1")
    if analysis.get("schema") != "iy.analysis/v1":
        raise ValueError("expected iy.analysis/v1")
    if replay.get("schema") != "iy.replay/v1":
        raise ValueError("expected iy.replay/v1")
    if analysis.get("source_sha256") != replay.get("source_sha256"):
        raise ValueError("analysis and replay source hashes differ")

    system_cards = "".join(
        f'<article class="check {_status_class(str(item.get("status", "")))}">'
        f'<div><strong>{html.escape(str(item.get("label", "")))}</strong>'
        f'<span>{html.escape(str(item.get("status", "REVIEW")))}</span></div>'
        f'<p>{html.escape(str(item.get("summary", "")))}</p></article>'
        for item in system.get("checks", [])
    )
    scenes = "".join(
        f'<li><span>Runde {int(scene.get("round_number", 0))}</span>'
        f'<strong>{html.escape(str(scene.get("marker_player", "")))}</strong>'
        f'<small>{len(scene.get("frames", []))} Frames · Tick {int(scene.get("start_tick", 0))}–{int(scene.get("end_tick", 0))}</small></li>'
        for scene in replay.get("scenes", [])
    ) or '<li class="empty">Keine Multi-Kill-Szenen in dieser Demo.</li>'
    quality = analysis.get("data_quality") or {}
    warnings = "".join(f"<li>{html.escape(value)}</li>" for value in _user_quality_warnings(quality))
    if not warnings:
        warnings = "<li>Keine Parserwarnung gemeldet.</li>"
    viewer_href = html.escape(viewer_path.relative_to(output_path.parent).as_posix(), quote=True)

    document = _TEMPLATE.format(
        map_name=html.escape(str(analysis.get("map_name", "Unbekannte Karte"))),
        source_hash=html.escape(str(analysis.get("source_sha256", ""))[:12]),
        kill_count=len(analysis.get("kills", [])),
        scene_count=len(replay.get("scenes", [])),
        quality_status=html.escape(str(quality.get("status", "not_assessable"))),
        system_cards=system_cards,
        warnings=warnings,
        scenes=scenes,
        viewer_href=viewer_href,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return output_path


_TEMPLATE = '''<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Improve Yourself – Review</title><style>
:root{{color-scheme:dark;font-family:system-ui,sans-serif;background:#08111e;color:#edf3fb}}*{{box-sizing:border-box}}
body{{margin:0;padding:24px}}main{{max-width:1120px;margin:auto}}header{{display:flex;gap:18px;align-items:center;flex-wrap:wrap}}
h1{{font-size:25px;margin:0 auto 0 0}}h2{{font-size:18px;margin:0 0 14px}}.muted,small{{color:#9eb1c9}}
.metrics,.checks{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}}
.card,.metric,.check{{background:#111f32;border:1px solid #273a54;border-radius:12px;padding:16px;margin-top:16px}}
.metric strong{{display:block;font-size:27px}}.check{{margin:0}}.check div{{display:flex;justify-content:space-between;gap:10px}}
.check span{{font-size:12px;font-weight:700}}.check p{{color:#b7c6d9;margin:10px 0 0;line-height:1.4}}
.ok{{border-left:4px solid #48c78e}}.review{{border-left:4px solid #ffca62}}.action{{border-left:4px solid #ff6b6b}}
.layout{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}ul{{padding-left:20px}}.scenes{{list-style:none;padding:0;margin:0}}
.scenes li{{display:grid;grid-template-columns:110px 1fr auto;gap:12px;padding:11px 0;border-bottom:1px solid #26374d}}
.button{{display:inline-block;background:#58a6ff;color:#07111e;text-decoration:none;font-weight:800;border-radius:9px;padding:11px 16px}}
.boundary{{border-color:#8b6b2d;background:#211c12;line-height:1.5}}@media(max-width:760px){{.layout{{grid-template-columns:1fr}}.scenes li{{grid-template-columns:1fr}}}}
</style></head><body><main><header><div><h1>Improve Yourself · Match Review</h1>
<div class="muted">{map_name} · Quelle {source_hash}</div></div><a class="button" href="{viewer_href}">Tactical Replay öffnen</a></header>
<section class="metrics"><article class="metric"><strong>{kill_count}</strong><span class="muted">erkannte Kills</span></article>
<article class="metric"><strong>{scene_count}</strong><span class="muted">Review-Szenen</span></article>
<article class="metric"><strong>{quality_status}</strong><span class="muted">Datenqualität</span></article></section>
<section class="card"><h2>System Check</h2><div class="checks">{system_cards}</div></section>
<div class="layout"><section class="card"><h2>Datenqualität</h2><ul>{warnings}</ul></section>
<section class="card"><h2>Szenen</h2><ul class="scenes">{scenes}</ul></section></div>
<section class="card boundary"><strong>Menschliche Prüfung erforderlich.</strong> Automatische Marker sind Review-Hinweise und kein Cheat-Nachweis. Sichtlinie, Sound, Utility, Calls, Timing und Gegnerperspektive müssen im Kontext geprüft werden.</section>
</main></body></html>'''
