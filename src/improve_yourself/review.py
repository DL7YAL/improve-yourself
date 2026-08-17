from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .review_state import scene_id


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value


def _status_class(value: str) -> str:
    return {
        "OK": "ok", "Hinweis": "review", "Verbesserung empfohlen": "action", "Problem": "action",
        "Nicht prüfbar / unbekannt": "review", "REVIEW": "review", "ACTION_REQUIRED": "action",
    }.get(value, "review")


def _user_quality_warnings(quality: dict[str, Any]) -> list[str]:
    warnings = [str(value) for value in quality.get("warnings", [])]
    readable = [
        value for value in warnings
        if not any(token in value for token in ("KeyError", "Traceback", "Exception"))
    ]
    if warnings and not readable:
        return ["Ein optionaler Datenkanal konnte nicht geladen werden; die betroffene Analyse bleibt eingeschränkt."]
    return readable


def _system_user_view(item: dict[str, Any]) -> dict[str, str]:
    view = item.get("user_view")
    if isinstance(view, dict):
        return {key: str(view.get(key, "")) for key in ("status", "priority", "relevance", "action")}
    return {
        "status": str(item.get("status", "REVIEW")), "priority": "informativ",
        "relevance": "Technische Detailansicht; Nutzerbewertung liegt nicht vor.", "action": "Keine automatische Änderung wurde vorgenommen.",
    }


def _system_evidence_details(item: dict[str, Any]) -> str:
    """Expose only review-safe provenance fields, never arbitrary inventory data."""
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    labels = {
        "chipset": "Plattform", "installed_package_version": "Installierte Software", "installed_version": "Installierte Software",
        "official_version": "Offizieller Stand", "official_source": "Quelle", "checked_at_utc": "Geprüft (UTC)",
    }
    return " ".join(
        f"<small><strong>{label}:</strong> {html.escape(str(evidence[key]))}</small>"
        for key, label in labels.items() if evidence.get(key) not in (None, "")
    )


def render_review_surface(
    system_path: Path | None,
    analysis_path: Path,
    replay_path: Path,
    viewer_path: Path,
    output_path: Path,
    *,
    preflight_path: Path | None = None,
) -> Path:
    analysis = _load(analysis_path)
    replay = _load(replay_path)
    preflight = _load(preflight_path) if preflight_path is not None else {}
    system = _load(system_path) if system_path is not None else None
    if system is not None and system.get("schema") != "iy.system_check/v1":
        raise ValueError("expected iy.system_check/v1")
    if analysis.get("schema") != "iy.analysis/v1":
        raise ValueError("expected iy.analysis/v1")
    if replay.get("schema") != "iy.replay/v1":
        raise ValueError("expected iy.replay/v1")
    if analysis.get("source_sha256") != replay.get("source_sha256"):
        raise ValueError("analysis and replay source hashes differ")
    if preflight and preflight.get("source_sha256") != analysis.get("source_sha256"):
        raise ValueError("preflight and analysis source hashes differ")

    system_cards = "".join(
        f'<article class="check {_status_class(view["status"])}">'
        f'<div><strong>{html.escape(str(item.get("label", "")))}</strong>'
        f'<span>{html.escape(view["status"]) } · {html.escape(view["priority"])}</span></div>'
        f'<p><strong>Ergebnis:</strong> {html.escape(str(item.get("summary", "Nicht verfügbar.")))}</p>'
        f'<p>{html.escape(view["relevance"])}</p>{_system_evidence_details(item)}'
        f'<p><strong>Nächster Schritt:</strong> {html.escape(view["action"])}</p></article>'
        for item in (system or {}).get("checks", [])
        for view in [_system_user_view(item)]
    )
    next_steps = (system or {}).get("user_summary", {}).get("next_steps", [])
    system_actions = "".join(
        f'<li><strong>{html.escape(str(item.get("priority", "wichtig")).title())}: '
        f'{html.escape(str(item.get("label", "")))}</strong> — {html.escape(str(item.get("action", "")))}</li>'
        for item in next_steps
    ) or "<li>Keine wichtige oder kritische Aktion aus dem System Check.</li>"
    readiness = (system or {}).get("user_summary", {}).get("anti_cheat_readiness", {})
    readiness_criteria = "".join(
        f'<li>{html.escape(str(item.get("label", "")))}: <strong>{html.escape(str(item.get("status", "Nicht prüfbar / unbekannt")))}</strong></li>'
        for item in readiness.get("criteria", [])
    ) or "<li>Secure Boot und TPM 2.0 konnten nicht zusammengefasst werden.</li>"
    viewer_href = html.escape(viewer_path.relative_to(output_path.parent).as_posix(), quote=True)
    scene_index = {(int(scene.get("round_number", 0)), str(scene.get("marker_player", "")), int(scene.get("start_tick", 0))): index for index, scene in enumerate(replay.get("scenes", []))}
    scene_markers = ", ".join(html.escape(str(scene.get("marker_player", ""))) for scene in replay.get("scenes", []))
    grouped: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for hint in analysis.get("review_hints", []):
        facts = hint.get("observed_facts", {}) if isinstance(hint, dict) else {}
        player = str(facts.get("player", "Unbekannt"))
        grouped.setdefault(player, {}).setdefault(int(facts.get("round_number", 0)), []).append(hint)
    demo_command_name = str(preflight.get("source_name", analysis.get("source_name", "demo"))).removesuffix(".zst").removesuffix(".dem")
    review_groups = []
    for player in sorted(grouped, key=str.casefold):
        rounds = []
        for round_number, hints in sorted(grouped[player].items()):
            entries = []
            for hint in sorted(hints, key=lambda value: int(value.get("observed_facts", {}).get("first_tick", 0))):
                facts = hint.get("observed_facts", {})
                tick = int(facts.get("first_tick", 0))
                index = scene_index.get((round_number, player, tick))
                tactical = f'<a class="button small" href="{viewer_href}?scene={index}">Tactical Replay öffnen</a>' if index is not None else '<span class="muted">Kein 2D-Szenenartefakt verfügbar.</span>'
                command = f'playdemo "{demo_command_name}"; demo_gototick {tick}'
                entries.append(f'<li class="hint"><strong>Tick {tick}</strong> · {html.escape(str(hint.get("criterion_label", "Review-Hinweis")))}<br><span>{html.escape(str(hint.get("message", "Vorhandene Fakten im Kontext prüfen.")))}</span><div class="actions">{tactical}<button class="copy" data-command="{html.escape(command, quote=True)}">CS2-Befehl kopieren</button></div><small>Originaldemo: Demo in den von CS2 verwendeten Demo-Ordner legen, CS2 starten und diesen vollständigen Konsolenbefehl ausführen. Die Tick-Navigation bleibt bewusst manuell prüfbar.</small></li>')
            rounds.append(f'<section class="round-group"><h3>Runde {round_number}</h3><ul>{"".join(entries)}</ul></section>')
        review_groups.append(f'<section class="player-group"><h2>{html.escape(player)}</h2>{"".join(rounds)}</section>')
    scenes = "".join(review_groups) or '<p class="empty">Keine Review-Hinweise aus den aktiv bewertbaren Kriterien.</p>'
    quality = analysis.get("data_quality") or {}
    warnings = "".join(f"<li>{html.escape(value)}</li>" for value in _user_quality_warnings(quality))
    if not warnings:
        warnings = "<li>Keine Parserwarnung gemeldet.</li>"
    analyzer_view = analysis.get("user_view") if isinstance(analysis.get("user_view"), dict) else {}
    review_profile = analysis.get("review_profile") if isinstance(analysis.get("review_profile"), dict) else {}
    assessment = analyzer_view.get("assessment") if isinstance(analyzer_view.get("assessment"), dict) else {}
    analysis_facts = "".join(f"<li>{html.escape(str(value))}</li>" for value in analyzer_view.get("facts", []))
    analysis_indicators = "".join(f"<li>{html.escape(str(value))}</li>" for value in analyzer_view.get("indicators", []))
    analysis_limits = "".join(f"<li>{html.escape(str(value))}</li>" for value in analyzer_view.get("limitations", []))

    system_section = ""
    if system is not None:
        system_section = _SYSTEM_SECTION.format(
            system_actions=system_actions,
            anti_cheat_status=html.escape(str(readiness.get("status", "Nicht vollständig bestätigbar"))),
            anti_cheat_message=html.escape(str(readiness.get("message", "Anti-Cheat-Readiness konnte nicht vollständig bestätigt werden."))),
            anti_cheat_criteria=readiness_criteria,
            system_cards=system_cards,
        )

    document = _TEMPLATE.format(
        map_name=html.escape(str(analysis.get("map_name", "Unbekannte Karte"))),
        source_hash=html.escape(str(analysis.get("source_sha256", ""))[:12]),
        source_hash_full=html.escape(str(analysis.get("source_sha256", "")), quote=True),
        kill_count=len(analysis.get("kills", [])),
        scene_count=len(replay.get("scenes", [])),
        quality_status=html.escape(str(assessment.get("status", quality.get("status", "Nicht prüfbar / unbekannt")))),
        quality_message=html.escape(str(assessment.get("message", "Datenqualität wird in den Details gezeigt."))),
        quality_action=html.escape(str(assessment.get("action", "Keine automatische Änderung wurde vorgenommen."))),
        system_section=system_section,
        warnings=warnings,
        analysis_facts=analysis_facts or "<li>Keine Zusammenfassung verfügbar.</li>",
        analysis_indicators=analysis_indicators or "<li>Keine zusätzlichen Hinweise verfügbar.</li>",
            analysis_limits=analysis_limits or warnings,
            scenes=scenes,
            scene_markers=scene_markers,
            viewer_href=viewer_href,
            review_profile=html.escape(f"{review_profile.get('label', 'Kein Profil')} ({review_profile.get('version', '—')})"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return output_path


_SYSTEM_SECTION = '''<section class="card"><h2>Was jetzt wichtig ist</h2><ul>{system_actions}</ul></section>
<section class="card boundary"><h2>Anti-Cheat-Readiness</h2><p><strong>{anti_cheat_status}</strong> — {anti_cheat_message}</p><ul>{anti_cheat_criteria}</ul></section>
<section class="card"><h2>System Check</h2><div class="checks">{system_cards}</div></section>'''


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
.scene{{padding:11px 0;border-bottom:1px solid #26374d}}.scene-head{{display:grid;grid-template-columns:90px 1fr auto;gap:12px;align-items:center}}
.scene-review{{display:grid;grid-template-columns:150px 1fr;gap:10px;margin-top:9px}}select,textarea{{background:#0b1727;color:#edf3fb;border:1px solid #334966;border-radius:7px;padding:8px}}textarea{{resize:vertical}}
.button{{display:inline-block;background:#58a6ff;color:#07111e;text-decoration:none;font-weight:800;border-radius:9px;padding:11px 16px}}
.button.small,.copy{{padding:7px 10px;font-size:13px;border:0;cursor:pointer;background:#58a6ff;color:#07111e;font-weight:800;border-radius:7px}}.player-group{{border-top:1px solid #334966;padding-top:10px;margin-top:14px}}.round-group{{margin:10px 0 0 12px}}.round-group h3{{font-size:15px}}.hint{{margin:8px 0;padding:10px;border-left:3px solid #ffca62;background:#0b1727;list-style:none}}.hint span,.hint small{{color:#b7c6d9;line-height:1.4}}.actions{{display:flex;gap:8px;margin:9px 0;flex-wrap:wrap}}
.boundary{{border-color:#8b6b2d;background:#211c12;line-height:1.5}}#save{{border:0;cursor:pointer}}#save-status{{margin-left:12px}}@media(max-width:760px){{.layout{{grid-template-columns:1fr}}.scene-head,.scene-review{{grid-template-columns:1fr}}}}
</style></head><body><main><header><div><h1>Improve Yourself · Match Review</h1>
<div class="muted">{map_name} · Quelle {source_hash}</div></div><a class="button" href="{viewer_href}">Tactical Replay öffnen</a></header>
<section class="metrics"><article class="metric"><strong>{kill_count}</strong><span class="muted">erkannte Kills</span></article>
<article class="metric"><strong>{scene_count}</strong><span class="muted">Review-Szenen</span></article>
<article class="metric"><strong>{quality_status}</strong><span class="muted">Datenqualität</span></article></section>
<section class="card"><strong>Aktives Analyseprofil:</strong> {review_profile}</section>
{system_section}
<div class="layout"><section class="card"><h2>Sicher beobachtet</h2><ul>{analysis_facts}</ul><h2>Hinweise zur Prüfung</h2><ul>{analysis_indicators}</ul></section>
<section class="card"><h2>Datenqualität und Grenzen</h2><p>{quality_message}</p><p><strong>Empfehlung:</strong> {quality_action}</p><ul>{analysis_limits}</ul></section></div>
<section class="card"><h2>Technische Details</h2><p class="muted">Parserhinweise:</p><ul>{warnings}</ul></section>
<section class="card"><h2>Review-Hinweise</h2><p class="muted">Nach Spieler, Runde und Tick gruppiert. Ein Hinweis beschreibt vorhandene Fakten, keine Schuld oder Absicht.</p><div class="scenes">{scenes}</div><small class="muted">Szenenmarker: {scene_markers}</small></section>
<section class="card"><button id="save" class="button" type="button">Review-Stand speichern</button><span id="save-status" class="muted">Lokaler Review-Dienst wird geprüft …</span></section>
<section class="card boundary"><strong>Menschliche Prüfung erforderlich.</strong> Automatische Marker sind Review-Hinweise und kein Cheat-Nachweis. Sichtlinie, Sound, Utility, Calls, Timing und Gegnerperspektive müssen im Kontext geprüft werden.</section>
</main><script>const SOURCE_HASH="{source_hash_full}";const statusEl=document.querySelector('#save-status');
function controls(){{return [...document.querySelectorAll('.scene')].map(el=>({{el,scene_id:el.dataset.sceneId,state:el.querySelector('select').value,note:el.querySelector('textarea').value}}))}}
async function loadState(){{try{{const response=await fetch('/api/review-state',{{cache:'no-store'}});if(!response.ok)throw new Error('API nicht verfügbar');const data=await response.json();const byId=new Map(data.scenes.map(x=>[x.scene_id,x]));for(const c of controls()){{const item=byId.get(c.scene_id);if(item){{c.el.querySelector('select').value=item.state;c.el.querySelector('textarea').value=item.note}}}}statusEl.textContent='Gespeicherter lokaler Review-Stand geladen.'}}catch(error){{statusEl.textContent='Zum Speichern über iy-review-server öffnen; die statische Ansicht bleibt lesbar.'}}}}
document.querySelector('#save').onclick=async()=>{{statusEl.textContent='Speichert …';const payload={{schema:'iy.review_state/v1',source_sha256:SOURCE_HASH,scenes:controls().map(c=>({{scene_id:c.scene_id,state:c.state,note:c.note}}))}};try{{const response=await fetch('/api/review-state',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});const data=await response.json();if(!response.ok)throw new Error(data.error||'Speichern fehlgeschlagen');statusEl.textContent='Review-Stand lokal gespeichert.'}}catch(error){{statusEl.textContent='Speichern nicht möglich: '+error.message}}}};document.querySelectorAll('.copy').forEach(button=>button.onclick=async()=>{{try{{await navigator.clipboard.writeText(button.dataset.command);button.textContent='Befehl kopiert';}}catch(error){{button.textContent=button.dataset.command;}}}});loadState();</script></body></html>'''
