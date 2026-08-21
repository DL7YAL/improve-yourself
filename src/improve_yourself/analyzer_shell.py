from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import re
import sys
import threading
import webbrowser
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from .analysis_flow import AnalysisProfile
from .cs2_review_coordinator import Cs2ReviewCoordinator, ReviewCoordinatorServer, ReviewPreflight
from .demo_workflow import preflight_demo_workflow, rerender_demo_workflow
from .embedded_review import EmbeddedReviewSession
from .embedded_tactical import EmbeddedTacticalSession
from .local_profiles import OBJECTIVE_RULES, LocalProfileStore
from .replay_store import ReplayStore
from .system_check import run_system_check


_SOURCE_HASH = re.compile(r"[0-9a-f]{64}")
_BASE_ARTIFACTS = ("analysis", "replay_v2")
_REVIEW_ARTIFACTS = (
    "analysis_flow", "timeline", "review", "cs2_review_commands"
)

UI_REFERENCE_STATUS = {
    "Dashboard": "IMPLEMENTED",
    "Analyzer / Review": "IMPLEMENTED",
    "Rules": "IMPLEMENTED",
    "Reports": "IMPLEMENTED",
    "System Check / Optimizer": "PARTIAL_REFERENCE",
    "Settings": "IMPLEMENTED",
    "Tactical Replay": "IMPLEMENTED",
}

_THEME = {
    "night": "#030914", "deep": "#071321", "panel": "#0b1b2c",
    "panel_high": "#10263b", "metal": "#173c5d", "line": "#1f5f8e",
    "line_soft": "#143550", "accent": "#058cff", "ice": "#8edbff",
    "ink": "#f1f7fc", "muted": "#8ca9bd", "success": "#58d69a",
}

_UI_FONT = "Inter"
_DISPLAY_FONT = "Orbitron"
_PRIVATE_FONT_FLAG = 0x10


def _register_private_fonts(root, assets: Path) -> tuple[str, str]:
    """Register the packaged V1 font files for this process only.

    The portable build must not depend on a machine-wide font installation.
    Windows keeps FR_PRIVATE registrations local to the running application;
    other platforms retain their safe system sans fallback.
    """
    if os.name != "nt" or not hasattr(ctypes, "windll"):
        return "Segoe UI", "Segoe UI"
    add_font = ctypes.windll.gdi32.AddFontResourceExW
    for filename in ("Inter-Variable.ttf", "Orbitron-Variable.ttf"):
        font_path = assets / "fonts" / filename
        if font_path.is_file():
            add_font(str(font_path), _PRIVATE_FONT_FLAG, None)
    families = set(root.tk.call("font", "families"))
    return (
        _UI_FONT if _UI_FONT in families else "Segoe UI",
        _DISPLAY_FONT if _DISPLAY_FONT in families else "Segoe UI",
    )


def dashboard_layout_metrics(content_width: int, viewport_height: int) -> tuple[bool, int, int, int, int]:
    """Return responsive Home metrics without scaling the whole interface."""
    compact = content_width < 1000
    extra_height = max(0, min(300, viewport_height - 650))
    return (
        compact,
        196 + extra_height // 12,
        184 + extra_height // 3,
        116 + extra_height // 4,
        12 + extra_height // 20,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def default_output_root() -> Path:
    """Use a stable user-writable root in packaged Windows builds."""
    if getattr(sys, "frozen", False) and os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Improve Yourself" / "Experimental" / "results"
    return Path("results/analyzer-shell")


def _enable_dark_titlebar(root) -> None:
    if not hasattr(ctypes, "windll"):
        return
    root.update_idletasks()
    enabled = ctypes.c_int(1)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        ctypes.windll.user32.GetParent(root.winfo_id()), 20, ctypes.byref(enabled), ctypes.sizeof(enabled)
    )


def validate_existing_workflow(manifest_path: Path) -> Path:
    """Fail-closed validation for an explicitly selected local workflow."""
    manifest_path = manifest_path.resolve()
    if manifest_path.name != "demo-workflow.json" or not manifest_path.is_file():
        raise ValueError("select an existing demo-workflow.json file")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != "iy.demo_workflow/v1":
        raise ValueError("expected iy.demo_workflow/v1 manifest")
    status = manifest.get("status")
    if status not in {"READY_FOR_SELECTION", "READY_FOR_REVIEW"}:
        raise ValueError("workflow is not READY_FOR_SELECTION or READY_FOR_REVIEW")
    source_hash = manifest.get("source_sha256")
    if not isinstance(source_hash, str) or _SOURCE_HASH.fullmatch(source_hash) is None:
        raise ValueError("source_sha256 must be 64 lowercase hexadecimal characters")
    policy = manifest.get("policy")
    if not isinstance(policy, dict) or policy.get("real_demo_required") is not True or policy.get("fake_results") is not False or policy.get("local_only") is not True:
        raise ValueError("workflow policy does not prove a local real-demo result")

    root = manifest_path.parent
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("workflow artifacts must be an object")
    resolved: dict[str, Path] = {}
    required = _BASE_ARTIFACTS + (_REVIEW_ARTIFACTS if status == "READY_FOR_REVIEW" else ())
    optional = tuple(name for name in ("tactical_replay", "report") if name in artifacts)
    for name in required + optional:
        relative = artifacts.get(name)
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"required artifact is missing: {name}")
        candidate = Path(relative)
        if candidate.is_absolute():
            raise ValueError(f"artifact must use a relative local path: {name}")
        path = (root / candidate).resolve()
        if root != path and root not in path.parents:
            raise ValueError(f"artifact escapes workflow root: {name}")
        if not path.is_file():
            raise ValueError(f"required artifact file is missing: {name}")
        resolved[name] = path

    analysis = json.loads(resolved["analysis"].read_text(encoding="utf-8"))
    if analysis.get("schema") != "iy.analysis/v1" or analysis.get("source_sha256") != source_hash:
        raise ValueError("analysis source metadata differs from workflow")
    store = ReplayStore(resolved["replay_v2"])
    if store.manifest["source"]["sha256"] != source_hash:
        raise ValueError("replay source metadata differs from workflow")
    loaded_chunks = [store.load_round(round_number) for round_number in store.round_numbers]

    if status == "READY_FOR_SELECTION":
        preflight = manifest.get("preflight")
        if not isinstance(preflight, dict) or preflight.get("parser_status") != "PASS":
            raise ValueError("workflow demo preflight is not valid")
        if preflight.get("map_id") != store.manifest["source"]["map_id"] or preflight.get("rounds") != len(store.round_numbers):
            raise ValueError("workflow demo preflight differs from replay")
        roster = preflight.get("roster")
        if not isinstance(roster, list) or {item.get("player_id") for item in roster if isinstance(item, dict)} != {item["player_id"] for item in store.manifest["players"]}:
            raise ValueError("workflow demo preflight roster differs from replay")
        event_count = sum(len(frame.get("events", [])) for chunk in loaded_chunks for frame in chunk["frames"])
        if preflight.get("basic_event_count") != event_count:
            raise ValueError("workflow demo preflight event count differs from replay")
        return manifest_path

    flow = json.loads(resolved["analysis_flow"].read_text(encoding="utf-8"))
    if flow.get("schema") != "iy.analysis_flow/v1" or flow.get("source", {}).get("sha256") != source_hash:
        raise ValueError("analysis flow source metadata differs from workflow")
    timeline = json.loads(resolved["timeline"].read_text(encoding="utf-8"))
    if timeline.get("source", {}).get("sha256") != source_hash or not isinstance(timeline.get("timeline"), list):
        raise ValueError("timeline source metadata differs from workflow")
    if manifest.get("selection") != flow.get("selection"):
        raise ValueError("workflow selection differs from analysis flow")
    counts = manifest.get("counts", {})
    if counts.get("players") != len(flow.get("roster", [])) or counts.get("scenes") != len(flow.get("scenes", [])):
        raise ValueError("workflow counts differ from analysis flow")
    if not resolved["review"].read_text(encoding="utf-8").strip():
        raise ValueError("review artifact is empty")
    if "report" in resolved:
        report = json.loads(resolved["report"].read_text(encoding="utf-8"))
        if report.get("schema") != "iy.analysis_report/v1" or report.get("source", {}).get("sha256") != source_hash:
            raise ValueError("report source metadata differs from workflow")
    if "tactical_replay" in resolved and not resolved["tactical_replay"].read_text(encoding="utf-8").strip():
        raise ValueError("tactical replay artifact is empty")
    return manifest_path


@dataclass(frozen=True)
class ShellPlayer:
    player_id: str
    display_name: str
    initial_team: str


@dataclass(frozen=True)
class ShellResult:
    manifest_path: Path
    review_path: Path
    players: tuple[ShellPlayer, ...]
    selected_ids: tuple[str, ...]
    selection_mode: str
    scene_count: int
    map_id: str
    source_demo_name: str
    source_sha256: str
    status: str
    round_count: int
    basic_event_count: int
    parser_status: str
    profile_id: str


class AnalyzerShellController:
    def __init__(
        self,
        output_root: Path,
        *,
        runner: Callable[..., Path] = preflight_demo_workflow,
        rerenderer: Callable[..., Path] = rerender_demo_workflow,
        profile_store: LocalProfileStore | None = None,
    ) -> None:
        self.output_root = output_root
        self._runner = runner
        self._rerenderer = rerenderer
        self.profile_store = profile_store or LocalProfileStore(output_root / "profiles")
        self.profiles = {profile.profile_id: profile for profile in self.profile_store.list_profiles()}
        self.profile_id = "review_v1"
        self.result: ShellResult | None = None
        self.selected_ids: list[str] = []
        self.selection_mode = "full_demo"

    def import_demo(self, demo: Path, *, max_bytes: int = 2_000_000_000) -> ShellResult:
        demo = demo.resolve()
        if demo.suffix.lower() != ".dem" and not demo.name.lower().endswith(".dem.zst"):
            raise ValueError("select a .dem or .dem.zst file")
        manifest = self._runner(demo, self.output_root, max_bytes=max_bytes)
        self.selected_ids.clear()
        self.selection_mode = "full_demo"
        self.result = self._load(manifest)
        return self.result

    def open_existing_workflow(self, manifest_path: Path) -> ShellResult:
        manifest = validate_existing_workflow(manifest_path)
        self.result = self._load(manifest)
        self.selected_ids = list(self.result.selected_ids)
        self.selection_mode = self.result.selection_mode
        return self.result

    def link_source_demo(self, demo: Path) -> ShellResult:
        result = self._require_result()
        manifest_path = validate_existing_workflow(result.manifest_path)
        demo = demo.resolve()
        if not demo.is_file() or (demo.suffix.lower() != ".dem" and not demo.name.lower().endswith(".dem.zst")):
            raise ValueError("select an existing .dem or .dem.zst file")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if _sha256_file(demo) != manifest["source_sha256"]:
            raise ValueError("selected demo SHA-256 differs from workflow source")
        manifest["source_demo_name"] = demo.name
        temporary = manifest_path.with_name("demo-workflow.json.tmp")
        try:
            temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(manifest_path)
        finally:
            if temporary.exists():
                temporary.unlink()
        self.result = self._load(manifest_path)
        return self.result

    def set_full_demo(self) -> None:
        self._require_result()
        self.selected_ids.clear()
        self.selection_mode = "full_demo"

    def reset_players(self) -> None:
        self._require_result()
        self.selected_ids.clear()
        self.selection_mode = "player_select"

    def add_player(self, player_id: str) -> None:
        result = self._require_result()
        known = {player.player_id for player in result.players}
        if player_id not in known:
            raise ValueError(f"unknown player: {player_id}")
        if player_id not in self.selected_ids:
            self.selected_ids.append(player_id)
        self.selection_mode = "player_select"

    def add_team(self, team: str) -> None:
        result = self._require_result()
        if team not in {"CT", "T"}:
            raise ValueError("team must be CT or T")
        for player in result.players:
            if player.initial_team == team and player.player_id not in self.selected_ids:
                self.selected_ids.append(player.player_id)
        self.selection_mode = "player_select"

    def available_players(self) -> tuple[ShellPlayer, ...]:
        result = self._require_result()
        selected = set(self.selected_ids)
        return tuple(player for player in result.players if player.player_id not in selected)

    def analyze_selection(self) -> ShellResult:
        result = self._require_result()
        if self.selection_mode == "player_select" and not self.selected_ids:
            raise ValueError("Player Select requires at least one player")
        manifest_path = self.validate_current_workflow()
        manifest = self._rerenderer(
            manifest_path, player_ids=tuple(self.selected_ids), profile=self.profiles[self.profile_id]
        )
        self.result = self._load(manifest)
        return self.result

    def select_profile(self, profile_id: str) -> None:
        if profile_id not in self.profiles:
            raise ValueError(f"unknown local analysis profile: {profile_id}")
        self.profile_id = profile_id

    def update_custom_rules(self, enabled_rule_ids: tuple[str, ...]) -> Path:
        profile = self.profiles.get(self.profile_id)
        if profile is None or profile.purpose != "custom":
            raise ValueError("rule toggles are editable only for a Custom profile")
        updated = replace(profile, enabled_rule_ids=tuple(rule for rule in OBJECTIVE_RULES if rule in enabled_rule_ids))
        path = self.profile_store.save(updated)
        self.profiles[updated.profile_id] = updated
        return path

    def validate_current_workflow(self) -> Path:
        return validate_existing_workflow(self._require_result().manifest_path)

    def _require_result(self) -> ShellResult:
        if self.result is None:
            raise RuntimeError("import a demo first")
        return self.result

    @staticmethod
    def _load(manifest_path: Path) -> ShellResult:
        manifest_path = manifest_path.resolve()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != "iy.demo_workflow/v1":
            raise ValueError("expected iy.demo_workflow/v1 manifest")
        root = manifest_path.parent
        if manifest["status"] == "READY_FOR_REVIEW":
            flow = json.loads((root / manifest["artifacts"]["analysis_flow"]).read_text(encoding="utf-8"))
            roster, scenes, selection = flow["roster"], flow["scenes"], flow["selection"]
            map_id = flow["source"].get("map_id")
            round_count = len(flow.get("rounds", ())) or int(manifest.get("counts", {}).get("rounds", 0))
        else:
            preflight = manifest["preflight"]
            roster, scenes, selection = preflight["roster"], [], manifest["selection"]
            map_id, round_count = preflight["map_id"], int(preflight["rounds"])
        players = tuple(
            ShellPlayer(item["player_id"], item["display_name"], item["initial_team"])
            for item in roster
        )
        return ShellResult(
            manifest_path=manifest_path,
            review_path=root / manifest["artifacts"].get("review", "review.html"),
            players=players,
            selected_ids=tuple(selection["player_ids"]), selection_mode=selection["mode"],
            scene_count=len(scenes), map_id=str(map_id or "unknown"),
            source_demo_name=str(manifest.get("source_demo_name") or ""),
            source_sha256=str(manifest["source_sha256"]), status=str(manifest["status"]),
            round_count=round_count,
            basic_event_count=int(manifest.get("preflight", {}).get("basic_event_count", 0)),
            parser_status=str(manifest.get("preflight", {}).get("parser_status", "PASS")),
            profile_id=str((manifest.get("profile") or {}).get("profile_id") or ""),
        )


class AnalyzerShellApp:
    def __init__(self, controller: AnalyzerShellController) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("Improve Yourself – Experimental")
        self.root.geometry("1360x860")
        self.root.minsize(1080, 720)
        self.root.configure(background=_THEME["night"])
        _enable_dark_titlebar(self.root)
        assets_path = Path(__file__).with_name("assets")
        self.ui_font, self.display_font = _register_private_fonts(self.root, assets_path)
        self.root.option_add("*Font", f"{self.ui_font} 10")
        icon_path = assets_path / "improve-yourself-icon-v3.png"
        try:
            self.app_icon = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self.app_icon)
        except tk.TclError:
            self.app_icon = None
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            ".", background=_THEME["panel"], foreground=_THEME["ink"],
            fieldbackground=_THEME["deep"], font=(self.ui_font, 10),
            bordercolor=_THEME["line_soft"], lightcolor=_THEME["panel_high"],
            darkcolor=_THEME["deep"], focuscolor=_THEME["accent"],
        )
        style.configure("TFrame", background=_THEME["night"])
        style.configure("Content.TFrame", background=_THEME["night"])
        style.configure("Card.TFrame", background=_THEME["panel"], relief="flat", borderwidth=1, bordercolor=_THEME["line_soft"])
        style.configure("CardInner.TFrame", background=_THEME["panel"], relief="flat", borderwidth=0)
        # Home deliberately has its own component family.  The command-centre
        # layout is shared with the rest of the shell, while these styles keep
        # its cards from falling back to the generic/native looking controls.
        style.configure("HomeStat.TFrame", background="#091a2b", relief="flat", borderwidth=1, bordercolor="#1d5d87")
        style.configure("HomeModule.TFrame", background="#0a1d30", relief="flat", borderwidth=1, bordercolor="#1b537b")
        style.configure("HomePanel.TFrame", background="#091a2b", relief="flat", borderwidth=1, bordercolor="#1b5279")
        style.configure("HomeInner.TFrame", background="#091a2b", relief="flat", borderwidth=0)
        style.configure("HomeStat.TLabel", background="#091a2b", foreground=_THEME["ice"])
        style.configure("HomeModule.TLabel", background="#0a1d30", foreground=_THEME["ink"])
        style.configure("HomePanel.TLabel", background="#091a2b", foreground=_THEME["ink"])
        style.configure("HomeMuted.TLabel", background="#0a1d30", foreground="#93b4c9")
        style.configure("HomePanelMuted.TLabel", background="#091a2b", foreground="#93b4c9")
        style.configure("HomeKicker.TLabel", background=_THEME["night"], foreground="#3bbaff", font=(self.display_font, 9))
        style.configure("HomePrimary.TButton", background="#075f96", foreground="#f7fbff", padding=(13, 8), borderwidth=1, bordercolor="#27b8ff", relief="flat", font=(self.ui_font, 9, "bold"))
        style.map("HomePrimary.TButton", background=[("active", "#078bd1"), ("pressed", "#064d7e"), ("disabled", "#0b2232")], bordercolor=[("active", "#a5e4ff"), ("disabled", "#1a3a50")])
        style.configure("HomeTeal.TButton", background="#07574f", foreground="#ecfffb", padding=(13, 8), borderwidth=1, bordercolor="#20d0b0", relief="flat", font=(self.ui_font, 9, "bold"))
        style.map("HomeTeal.TButton", background=[("active", "#087b70"), ("pressed", "#06463f"), ("disabled", "#0b2232")], bordercolor=[("active", "#9fffe9"), ("disabled", "#1a3a50")])
        style.configure("HomeViolet.TButton", background="#38285e", foreground="#f6f0ff", padding=(13, 8), borderwidth=1, bordercolor="#a684ff", relief="flat", font=(self.ui_font, 9, "bold"))
        style.map("HomeViolet.TButton", background=[("active", "#564090"), ("pressed", "#2c2049"), ("disabled", "#171d2b")], bordercolor=[("active", "#dfd1ff"), ("disabled", "#30384b")])
        style.configure("HomeGold.TButton", background="#6b5014", foreground="#fff8e5", padding=(13, 8), borderwidth=1, bordercolor="#e3b940", relief="flat", font=(self.ui_font, 9, "bold"))
        style.map("HomeGold.TButton", background=[("active", "#927123"), ("pressed", "#513d10"), ("disabled", "#272417")], bordercolor=[("active", "#ffdc77"), ("disabled", "#3b3520")])
        style.configure("Sidebar.TFrame", background="#050f1c", borderwidth=0)
        style.configure("TLabel", background=_THEME["night"], foreground=_THEME["ink"])
        style.configure("Card.TLabel", background=_THEME["panel"], foreground=_THEME["ink"])
        style.configure("Muted.TLabel", background=_THEME["panel"], foreground=_THEME["muted"])
        style.configure("TLabelframe", background=_THEME["panel"], foreground=_THEME["ink"], relief="flat", borderwidth=1, bordercolor=_THEME["line_soft"])
        style.configure("TLabelframe.Label", background=_THEME["panel"], foreground=_THEME["ice"], font=("Segoe UI Semibold", 9))
        style.configure(
            "TButton", background="#102b43", foreground="#dcefff", padding=(14, 9),
            borderwidth=1, bordercolor="#245b82", relief="flat", font=(self.ui_font, 9, "bold"),
            focusthickness=0,
        )
        style.map(
            "TButton",
            background=[("active", "#174b70"), ("pressed", "#0d78c7"), ("disabled", "#091725")],
            bordercolor=[("active", _THEME["ice"]), ("pressed", _THEME["accent"]), ("disabled", _THEME["line_soft"])],
            foreground=[("disabled", "#587184")],
        )
        style.configure(
            "Primary.TButton", background="#087dcc", foreground="#ffffff",
            bordercolor="#35b8ff", font=(self.ui_font, 9, "bold"), padding=(16, 9),
        )
        style.map("Primary.TButton", background=[("active", "#0ba3f2"), ("pressed", "#0568ae"), ("disabled", "#0b2437")])
        style.configure(
            "TCombobox", background=_THEME["deep"], fieldbackground=_THEME["deep"],
            foreground=_THEME["ink"], arrowcolor=_THEME["ice"], bordercolor="#245b82",
            lightcolor=_THEME["deep"], darkcolor=_THEME["deep"], padding=(8, 6),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", _THEME["deep"]), ("disabled", _THEME["deep"])],
            foreground=[("readonly", _THEME["ink"]), ("disabled", _THEME["muted"])],
            selectbackground=[("readonly", _THEME["deep"])],
            selectforeground=[("readonly", _THEME["ink"])],
        )
        style.configure(
            "TCheckbutton", background=_THEME["panel"], foreground=_THEME["ink"],
            indicatorcolor=_THEME["deep"], indicatormargin=6, padding=(4, 4),
        )
        style.map(
            "TCheckbutton",
            background=[("active", _THEME["panel"]), ("disabled", _THEME["panel"])],
            foreground=[("disabled", _THEME["muted"])],
            indicatorcolor=[("selected", _THEME["ice"]), ("disabled", _THEME["metal"])],
        )
        style.configure(
            "Rule.TCheckbutton", indicatoron=False, anchor="w", background="#0a1a2a",
            foreground=_THEME["muted"], padding=(12, 10), borderwidth=1,
            bordercolor=_THEME["line_soft"], font=(self.ui_font, 9, "bold"),
        )
        style.map(
            "Rule.TCheckbutton",
            background=[("selected", "#0d3d60"), ("active", "#102d46"), ("disabled", "#091725")],
            foreground=[("selected", "#ffffff"), ("active", "#ffffff"), ("disabled", "#587184")],
            bordercolor=[("selected", _THEME["accent"]), ("active", _THEME["line"]), ("disabled", _THEME["line_soft"])],
        )
        style.configure(
            "Nav.TButton", anchor="w", background="#050f1c", foreground=_THEME["muted"],
            padding=(18, 13), borderwidth=1, bordercolor="#050f1c", font=(self.ui_font, 9),
        )
        style.map("Nav.TButton", background=[("active", "#0a2033")], foreground=[("active", _THEME["ink"])], bordercolor=[("active", _THEME["line_soft"])])
        style.configure(
            "NavActive.TButton", anchor="w", background="#0b3150", foreground="#ffffff",
            padding=(18, 13), borderwidth=1, bordercolor="#168ddd", font=(self.ui_font, 9, "bold"),
        )
        style.configure(
            "Horizontal.TScale", background=_THEME["panel"], troughcolor="#06111d",
            bordercolor=_THEME["line_soft"], lightcolor="#20a9ff", darkcolor="#0876be",
            slidercolor="#20a9ff", gripcount=0, borderwidth=0,
        )
        self.status = tk.StringVar(value="Echte CS2-Demo auswählen")
        self.identity = tk.StringVar(value="Keine lokale Analyse geladen")
        self.demo_preflight = tk.StringVar(value="Demo-Preflight ausstehend")
        self.player_by_label: dict[str, str] = {}
        self.review_server: ReviewCoordinatorServer | None = None
        self.netcon_status = tk.StringVar(value="○ Lokale CS2-Verbindung: noch nicht geprüft")
        self.demo_status = tk.StringVar(value="○ Demo-Modus: noch nicht geprüft")
        self.filename_status = tk.StringVar(value="○ Dateiname: noch nicht geprüft")
        self.preflight_message = tk.StringVar(value="Vor dem Review CS2 prüfen.")
        self.overview_status = tk.StringVar(value="Noch keine Demo geladen")
        self.dashboard_rounds = tk.StringVar(value="—\nRunden")
        self.dashboard_players = tk.StringVar(value="—\nSpieler")
        self.dashboard_scenes = tk.StringVar(value="—\nSzenen")
        self.dashboard_readiness = tk.StringVar(value="BEREIT\nLokaler Modus")
        self.dashboard_pipeline = tk.StringVar(value="Demo nicht geladen\nParser —  ·  Auswahl —  ·  Szenen —  ·  Review —")
        self.dashboard_recent = tk.StringVar(value="Noch keine lokale Analyse geöffnet.")
        self.report_status = tk.StringVar(value="Nach einer Analyse stehen Report und Timeline lokal bereit.")
        self.system_status = tk.StringVar(value="System Check wurde noch nicht ausgeführt.")
        self.embedded_review: EmbeddedReviewSession | None = None
        self.embedded_scene_id: str | None = None
        self.embedded_cs2_status = tk.StringVar(value="CS2-Bereitschaft noch nicht geprüft.")
        self.embedded_scene_title = tk.StringVar(value="Keine Szene ausgewählt")
        self.embedded_scene_context = tk.StringVar(value="")
        self.embedded_scene_players = tk.StringVar(value="")
        self.embedded_scene_rules = tk.StringVar(value="")
        self.embedded_tactical: EmbeddedTacticalSession | None = None
        self.tactical_scene_title = tk.StringVar(value="Keine Szene ausgewählt")
        self.tactical_scene_context = tk.StringVar(value="")
        self.tactical_scene_note = tk.StringVar(value="Keine Review-Notiz")
        self.tactical_frame_status = tk.StringVar(value="")
        self.tactical_action_status = tk.StringVar(value="Tactical Replay wird aus einer Review-Szene geöffnet.")
        self.tactical_frame_index = 0
        self.tactical_zoom = 1.0
        self.tactical_pan = [0.0, 0.0]
        self.tactical_drag_origin: tuple[int, int] | None = None
        self.tactical_syncing_selection = False
        self.tactical_ignore_selection_event = False

        shell = ttk.Frame(self.root, style="Content.TFrame")
        shell.pack(fill="both", expand=True)
        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", width=245)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Frame(sidebar, width=1, background=_THEME["line_soft"]).pack(side="right", fill="y")
        brand_path = Path(__file__).with_name("assets") / "improve-yourself-wordmark-v3.png"
        try:
            self.brand_image = tk.PhotoImage(file=str(brand_path)).subsample(3, 3)
            tk.Label(sidebar, image=self.brand_image, background=_THEME["deep"]).pack(anchor="w", padx=18, pady=(22, 6))
        except tk.TclError:
            ttk.Label(sidebar, text="IMPROVE YOURSELF", style="Card.TLabel", font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=18, pady=(24, 6))
        tk.Label(sidebar, text="EXPERIMENTAL BUILD", background=_THEME["deep"], foreground=_THEME["ice"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=19, pady=(0, 20))
        content = ttk.Frame(shell, style="Content.TFrame", padding=(24, 18, 24, 24))
        content.pack(side="left", fill="both", expand=True)
        self.pages: dict[str, ttk.Frame] = {}
        self.page_hosts: dict[str, ttk.Frame] = {}
        self.nav_buttons: dict[str, ttk.Button] = {}
        nav_labels = {
            "Dashboard": "⌂   Dashboard",
            "Analyzer / Review": "◎   Analyzer / Review",
            "Rules": "◇   Rules",
            "Reports": "▤   Reports",
            "System Check / Optimizer": "◈   System Check / Optimizer",
            "Settings": "⚙   Settings",
            "Tactical Replay": "⌖   Tactical Replay",
        }
        for name in UI_REFERENCE_STATUS:
            host = ttk.Frame(content, style="Content.TFrame")
            host.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.page_hosts[name] = host
            if name in {"Analyzer / Review", "Dashboard"}:
                canvas = tk.Canvas(
                    host, background=_THEME["night"], borderwidth=0, highlightthickness=0,
                )
                scrollbar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=scrollbar.set)
                canvas.pack(side="left", fill="both", expand=True)
                page = ttk.Frame(canvas, style="Content.TFrame")
                page_window = canvas.create_window((0, 0), window=page, anchor="nw")
                page.bind("<Configure>", lambda _event, target=canvas, body=page, bar=scrollbar: self._sync_scrollable_page(target, body, bar))
                canvas.bind(
                    "<Configure>",
                    lambda event, target=canvas, item=page_window, body=page, bar=scrollbar: self._resize_scrollable_page(target, item, body, bar, event.width),
                )
                canvas.bind(
                    "<MouseWheel>",
                    lambda event, target=canvas: target.yview_scroll(int(-event.delta / 120), "units"),
                )
                page.bind(
                    "<MouseWheel>",
                    lambda event, target=canvas: target.yview_scroll(int(-event.delta / 120), "units"),
                )
                if name == "Analyzer / Review":
                    self.analyzer_canvas = canvas
                else:
                    self.dashboard_canvas = canvas
                    self.dashboard_scrollbar = scrollbar
            else:
                page = ttk.Frame(host, style="Content.TFrame")
                page.pack(fill="both", expand=True)
            self.pages[name] = page
            button = ttk.Button(sidebar, text=nav_labels[name], style="Nav.TButton", command=lambda value=name: self._show_page(value))
            button.pack(fill="x", padx=8, pady=1)
            self.nav_buttons[name] = button
        tk.Label(sidebar, text="LOCAL · PRIVATE · READ-ONLY WHERE MARKED", background=_THEME["deep"], foreground=_THEME["muted"], wraplength=205, justify="left", font=("Segoe UI", 8)).pack(side="bottom", anchor="w", padx=18, pady=18)

        frame = self.pages["Analyzer / Review"]
        analyzer_header = ttk.Frame(frame, style="Content.TFrame")
        analyzer_header.pack(fill="x", pady=(0, 12))
        ttk.Label(analyzer_header, text="Analyzer / Review", font=("Segoe UI", 24, "bold")).pack(side="left")
        ttk.Label(analyzer_header, textvariable=self.status, foreground=_THEME["ice"]).pack(side="right")
        ttk.Label(frame, text="Demo → Parser → Auswahl → Profil → Regeln → Szenen → Review", foreground=_THEME["muted"]).pack(anchor="w", pady=(0, 12))

        analyzer_top = ttk.Frame(frame, style="Content.TFrame")
        analyzer_top.pack(fill="x")
        source_card = ttk.Frame(analyzer_top, style="Card.TFrame", padding=16)
        source_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(source_card, text="DEMO & DATENQUELLE", style="Card.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        source_actions = ttk.Frame(source_card, style="CardInner.TFrame")
        source_actions.pack(fill="x", pady=(8, 0))
        ttk.Button(source_actions, text="Demo auswählen", style="Primary.TButton", command=self._choose_demo).pack(fill="x")
        ttk.Button(source_actions, text="Vorhandene Analyse öffnen", command=self._open_existing).pack(fill="x", pady=5)
        self.link_button = ttk.Button(source_actions, text="Quelldemo zuordnen", command=self._link_source, state="disabled")
        self.link_button.pack(fill="x")
        ttk.Label(source_card, textvariable=self.identity, style="Muted.TLabel", wraplength=470, justify="left").pack(anchor="w", pady=(10, 0))
        ttk.Label(source_card, textvariable=self.demo_preflight, style="Card.TLabel", wraplength=470, justify="left").pack(anchor="w", pady=(4, 0))

        teams = ttk.Frame(analyzer_top, style="Content.TFrame")
        teams.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.ct = ttk.LabelFrame(teams, text="CT LINE-UP", padding=10)
        self.ct.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.t = ttk.LabelFrame(teams, text="T LINE-UP", padding=10)
        self.t.pack(side="left", fill="both", expand=True, padx=(4, 0))

        selection_card = ttk.Frame(frame, style="Card.TFrame", padding=16)
        selection_card.pack(fill="x", pady=(12, 0))
        ttk.Label(selection_card, text="SPIELERAUSWAHL & ANALYSEPROFIL", style="Card.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        controls = ttk.Frame(selection_card, style="CardInner.TFrame")
        controls.pack(fill="x", pady=(10, 4))
        self.workflow_widgets = []
        for text, command in (("Full Demo", self._full), ("CT", lambda: self._team("CT")), ("T", lambda: self._team("T")), ("Reset", self._reset)):
            button = ttk.Button(controls, text=text, command=command, state="disabled")
            button.pack(side="left", padx=4 if text != "Full Demo" else 0)
            self.workflow_widgets.append(button)
        player_controls = ttk.Frame(selection_card, style="CardInner.TFrame")
        player_controls.pack(fill="x", pady=(2, 4))
        ttk.Label(player_controls, text="Spieler", style="Muted.TLabel").pack(side="left")
        self.player = ttk.Combobox(player_controls, state="disabled", width=32)
        self.player.pack(side="left", padx=(10, 4))
        self.add_button = ttk.Button(player_controls, text="+ Add Player", command=self._add, state="disabled")
        self.add_button.pack(side="left")
        self.workflow_widgets.extend((self.player, self.add_button))

        profile_row = ttk.Frame(selection_card, style="CardInner.TFrame")
        profile_row.pack(fill="x", pady=6)
        ttk.Label(profile_row, text="Analyseprofil").pack(side="left")
        self.profile = ttk.Combobox(profile_row, state="disabled", width=24, values=tuple(controller.profiles))
        self.profile.set("review_v1")
        self.profile.pack(side="left", padx=8)
        self.profile.bind("<<ComboboxSelected>>", self._select_profile)
        self.workflow_widgets.append(self.profile)
        self.rules = ttk.Label(profile_row, text="Objektive V1-Regeln · Details per Profil")
        self.rules.pack(side="left", padx=8)
        rules_frame = ttk.LabelFrame(self.pages["Rules"], text="Objektive Szenenanker V1", padding=18)
        ttk.Label(self.pages["Rules"], text="Rules", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ttk.Label(self.pages["Rules"], text="Profile kombinieren belegte Marker; einzelne schwache Hinweise erzeugen keine Standard-Szene.", foreground=_THEME["muted"]).pack(anchor="w", pady=(2, 14))
        rules_frame.pack(fill="x", pady=5)
        rules_frame.columnconfigure(0, weight=1, uniform="rules")
        rules_frame.columnconfigure(1, weight=1, uniform="rules")
        self.rule_vars: dict[str, tk.BooleanVar] = {}
        self.rule_checks = []
        labels = {
            "objective_kill": "Kill", "objective_multi_kill": "Multi-Kill", "objective_headshot": "Headshot",
            "objective_wallbang": "Wallbang", "objective_smoke_kill": "Smoke-Kill",
            "objective_blind_kill": "Blind-Kill", "objective_entry": "Entry",
        }
        for index, rule_id in enumerate(OBJECTIVE_RULES):
            variable = tk.BooleanVar(value=True)
            check = ttk.Checkbutton(rules_frame, text=labels[rule_id], variable=variable, command=self._save_custom_rules, style="Rule.TCheckbutton")
            check.grid(row=index // 2, column=index % 2, sticky="ew", padx=(0, 12), pady=5)
            check.bind("<Double-Button-1>", lambda _event, value=rule_id: self._show_rule_details(value))
            self.rule_vars[rule_id] = variable
            self.rule_checks.append(check)
        self.workflow_widgets.extend(self.rule_checks)
        architecture = ttk.Frame(self.pages["Rules"], style="Card.TFrame", padding=16)
        architecture.pack(fill="x", pady=(12, 0))
        ttk.Label(architecture, text="INDIKATOREN  →  REGELKOMBINATIONEN  →  ANALYSEPROFIL  →  SZENEN", style="Card.TLabel", font=("Segoe UI Semibold", 10)).pack(anchor="w")
        ttk.Label(architecture, text="Standardprofile erzeugen Szenen nur aus vollständig definierten objektiven Kombinationen.", style="Muted.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(self.pages["Rules"], text=f"Lokale Profile: {controller.profile_store.root}", foreground=_THEME["muted"]).pack(anchor="w", pady=(10, 5))

        self.chosen = ttk.Label(selection_card, text="Full Demo", style="Muted.TLabel")
        self.chosen.pack(anchor="w", pady=(4, 0))
        review_strip = ttk.Frame(frame, style="Content.TFrame")
        review_strip.pack(fill="x", pady=(12, 0))
        actions = ttk.Frame(review_strip, style="Card.TFrame", padding=14)
        actions.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(actions, text="ANALYSE & REVIEW", style="Card.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(0, 8))
        self.analyze_button = ttk.Button(actions, text="Analyse starten", command=self._analyze, state="disabled")
        self.analyze_button.pack(side="left")
        self.cs2_button = ttk.Button(actions, text="CS2 prüfen", command=self._preflight, state="disabled")
        self.cs2_button.pack(side="left", padx=8)
        self.workflow_widgets.extend((self.analyze_button, self.cs2_button))
        self.review_button = ttk.Button(actions, text="Review anzeigen", command=self._open_review, state="disabled")
        self.review_button.pack(side="left")
        preflight = ttk.LabelFrame(review_strip, text="CS2-READINESS", padding=12)
        preflight.pack(side="left", fill="both", expand=True, padx=(6, 0))
        for variable in (self.netcon_status, self.demo_status, self.filename_status, self.preflight_message):
            ttk.Label(preflight, textvariable=variable).pack(anchor="w")
        self._build_embedded_review(frame)
        self._build_dashboard_page()
        self._build_reports_page()
        self._build_settings_page()
        self._build_system_page()
        self._build_tactical_page()
        self._show_page("Analyzer / Review")
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build_embedded_review(self, parent) -> None:
        review = self.ttk.Frame(parent, style="Content.TFrame", padding=(0, 0, 0, 0))
        self.embedded_review_frame = review
        header = self.ttk.Frame(review, style="Content.TFrame")
        header.pack(fill="x")
        self.ttk.Button(header, text="← Analyse", command=self._close_embedded_review).pack(side="left")
        self.ttk.Label(header, text="Analyzer Review", font=("Segoe UI", 24, "bold")).pack(side="left", padx=16)
        self.ttk.Label(
            header, text="LOCAL · EINGEBETTET", foreground=_THEME["ice"], font=("Segoe UI Semibold", 9)
        ).pack(side="right")
        self.ttk.Label(
            review,
            text="Szenen, Evidenz und Notizen aus derselben Analyse · Tick-Sprung über den geprüften lokalen Coordinator",
            foreground=_THEME["muted"],
        ).pack(anchor="w", pady=(4, 14))

        body = self.ttk.Frame(review, style="Content.TFrame")
        body.pack(fill="both", expand=True)
        left = self.ttk.Frame(body, style="Card.TFrame", padding=14)
        left.pack(side="left", fill="y", padx=(0, 10))
        self.ttk.Label(left, text="Szenen", style="Card.TLabel", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        self.embedded_scene_list = self.tk.Listbox(
            left, width=36, height=25, background=_THEME["deep"], foreground=_THEME["ink"],
            selectbackground=_THEME["metal"], selectforeground=_THEME["ink"],
            borderwidth=0, highlightthickness=1, highlightbackground=_THEME["line_soft"],
            highlightcolor=_THEME["ice"], activestyle="none", font=("Segoe UI", 10),
        )
        self.embedded_scene_list.pack(fill="y", expand=True, pady=(10, 0))
        self.embedded_scene_list.bind("<<ListboxSelect>>", self._select_embedded_scene)

        detail = self.ttk.Frame(body, style="Card.TFrame", padding=20)
        detail.pack(side="left", fill="both", expand=True)
        self.ttk.Label(detail, textvariable=self.embedded_scene_title, style="Card.TLabel", font=("Segoe UI Semibold", 17)).pack(anchor="w")
        self.ttk.Label(detail, textvariable=self.embedded_scene_context, style="Muted.TLabel", wraplength=720, justify="left").pack(anchor="w", pady=(8, 0))
        self.ttk.Label(detail, textvariable=self.embedded_scene_players, style="Card.TLabel", wraplength=720, justify="left").pack(anchor="w", pady=(14, 0))
        self.ttk.Label(detail, textvariable=self.embedded_scene_rules, style="Muted.TLabel", wraplength=720, justify="left").pack(anchor="w", pady=(6, 16))

        state_row = self.ttk.Frame(detail, style="CardInner.TFrame")
        state_row.pack(fill="x")
        self.ttk.Label(state_row, text="Review-Status", style="Card.TLabel").pack(side="left")
        self.embedded_state = self.ttk.Combobox(
            state_row, state="readonly", width=18,
            values=("unreviewed", "reviewed", "follow-up", "discarded", "clip-worthy"),
        )
        self.embedded_state.pack(side="left", padx=10)
        self.ttk.Label(detail, text="Notiz", style="Card.TLabel").pack(anchor="w", pady=(16, 6))
        self.embedded_note = self.tk.Text(
            detail, height=7, wrap="word", background=_THEME["deep"], foreground=_THEME["ink"],
            insertbackground=_THEME["ice"], selectbackground=_THEME["metal"],
            borderwidth=0, relief="flat", highlightthickness=1, highlightbackground=_THEME["line_soft"],
            font=("Segoe UI", 10),
        )
        self.embedded_note.pack(fill="x")
        buttons = self.ttk.Frame(detail, style="CardInner.TFrame")
        buttons.pack(fill="x", pady=(14, 0))
        self.ttk.Button(buttons, text="Status & Notiz speichern", command=self._save_embedded_review).pack(side="left")
        self.ttk.Button(buttons, text="In CS2 ansehen", style="Primary.TButton", command=self._open_embedded_in_cs2).pack(side="left", padx=8)
        self.ttk.Button(buttons, text="Tactical Replay", command=self._open_tactical_from_review).pack(side="left")
        self.ttk.Button(buttons, text="Vorherige", command=lambda: self._step_embedded_scene(-1)).pack(side="left", padx=(16, 4))
        self.ttk.Button(buttons, text="Nächste", command=lambda: self._step_embedded_scene(1)).pack(side="left")
        self.ttk.Label(
            detail, textvariable=self.embedded_cs2_status, style="Muted.TLabel", wraplength=720, justify="left"
        ).pack(anchor="w", pady=(18, 0))
        self.ttk.Button(
            detail, text="HTML-Export im Browser (Fallback)", command=self._open_review_fallback
        ).pack(anchor="w", pady=(12, 0))

    def _show_page(self, name: str) -> None:
        self.page_hosts[name].tkraise()
        if name == "Dashboard":
            self.root.after_idle(lambda: self.dashboard_canvas.yview_moveto(0.0))
        for page_name, button in self.nav_buttons.items():
            button.configure(style="NavActive.TButton" if page_name == name else "Nav.TButton")

    def _build_dashboard_page(self) -> None:
        page = self.pages["Dashboard"]
        home_line = self.tk.Canvas(page, height=10, background=_THEME["night"], highlightthickness=0, bd=0)
        home_line.pack(fill="x", pady=(0, 10))
        home_line.bind("<Configure>", lambda event: self._draw_home_tech_line(home_line, event.width, event.height))
        header = self.ttk.Frame(page, style="Content.TFrame")
        header.pack(fill="x", pady=(0, 12))
        greeting = self.ttk.Frame(header, style="Content.TFrame")
        greeting.pack(side="left", fill="x", expand=True)
        self.ttk.Label(greeting, text="LOCAL PERFORMANCE LAB  /  COMMAND CENTER", style="HomeKicker.TLabel").pack(anchor="w", pady=(0, 3))
        self.ttk.Label(greeting, text="Willkommen zurück!", font=(self.display_font, 22, "bold")).pack(anchor="w")
        self.ttk.Label(
            greeting, text="Dein lokales Command Center für Analyse, Review und kontinuierliche Verbesserung.",
            foreground=_THEME["muted"],
        ).pack(anchor="w", pady=(2, 0))
        stats = self.ttk.Frame(header, style="Content.TFrame")
        stats.pack(side="right")
        self.dashboard_header = header
        self.dashboard_greeting = greeting
        self.dashboard_stats = stats
        stat_accents = ("#23d8bb", "#30aef4", "#a687ff", "#ffcf5a")
        for variable, accent in zip((self.dashboard_readiness, self.dashboard_rounds, self.dashboard_players, self.dashboard_scenes), stat_accents):
            card = self.ttk.Frame(stats, style="HomeStat.TFrame", padding=(10, 7))
            card.pack(side="left", padx=(6, 0))
            self._home_accent(card, accent)
            self.ttk.Label(card, textvariable=variable, style="HomeStat.TLabel", justify="center", font=(self.ui_font, 9, "bold")).pack(pady=(4, 0))

        modules = self.ttk.Frame(page, style="Content.TFrame")
        modules.pack(fill="x")
        self.dashboard_module_grid = modules
        self.dashboard_module_cards = []
        module_specs = (
            ("◎", "IMPROVE\nANALYZER", "Szenen und Evidenz aus einer echten Demo prüfen.", "Review öffnen", "Analyzer / Review", True, "#2bdcbb", "HomeTeal.TButton"),
            ("♙", "DEMO\nANALYZER", "Demo laden, Parserstatus und Line-ups kontrollieren.", "Demo laden", "Analyzer / Review", True, "#a687ff", "HomeViolet.TButton"),
            ("⚔", "2D\nTACTICAL", "Rundenpositionen aus derselben Replay-Wahrheit ansehen.", "Replay öffnen", "Tactical Replay", True, "#2db8ff", "HomePrimary.TButton"),
            ("◉", "IMPROVE\nOPTIMIZER", "Systemfakten sicher und read-only erfassen.", "System prüfen", "System Check / Optimizer", True, "#ffcc54", "HomeGold.TButton"),
            ("▥", "IMPROVE\nBENCHMARK", "Separater, derzeit geparkter Arbeitsstrang.", "Nicht in diesem Slice", "", False, "#6587a0", "HomePrimary.TButton"),
            ("◯", "MY\nIMPROVEMENT", "Lokale Reports und aktuelle Analyseartefakte öffnen.", "Übersicht öffnen", "Reports", True, "#238ffc", "HomePrimary.TButton"),
        )
        for column, (icon, title, detail, action, target, enabled, accent, button_style) in enumerate(module_specs):
            modules.columnconfigure(column, weight=1, uniform="home-modules")
            card = self.ttk.Frame(modules, style="HomeModule.TFrame", padding=13)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 3, 0 if column == 5 else 3))
            self.dashboard_module_cards.append(card)
            self._home_accent(card, accent)
            icon_row = self.ttk.Frame(card, style="HomeModule.TFrame")
            icon_row.pack(fill="x", pady=(5, 6))
            self._home_module_icon(icon_row, icon, accent).pack(side="left", padx=(0, 8))
            self.ttk.Label(icon_row, text=title, style="HomeModule.TLabel", font=(self.display_font, 9, "bold"), justify="left").pack(side="left", anchor="w")
            self.ttk.Label(card, text=detail, style="HomeMuted.TLabel", wraplength=150, justify="left").pack(anchor="w", pady=(2, 10), fill="x")
            button = self.ttk.Button(card, text=action, style=button_style, command=(lambda value=target: self._show_page(value)))
            button.configure(state="normal" if enabled else "disabled")
            button.pack(fill="x")

        overview = self.ttk.Frame(page, style="Content.TFrame")
        overview.pack(fill="x", pady=(12, 0))
        overview.columnconfigure(0, weight=5, uniform="home-overview")
        overview.columnconfigure(1, weight=5, uniform="home-overview")
        overview.columnconfigure(2, weight=6, uniform="home-overview")

        progress = self.ttk.Frame(overview, style="HomePanel.TFrame", padding=15)
        progress.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._home_accent(progress, "#2bdcbb")
        self.ttk.Label(progress, text="DEIN FORTSCHRITT – ÜBERBLICK", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        progress_body = self.ttk.Frame(progress, style="HomeInner.TFrame")
        progress_body.pack(fill="x", pady=(8, 9))
        self._home_progress_gauge(progress_body).pack(side="left", padx=(0, 9))
        self.ttk.Label(progress_body, textvariable=self.dashboard_pipeline, style="HomePanelMuted.TLabel", wraplength=180, justify="left").pack(side="left", fill="x", expand=True)
        self.ttk.Button(progress, text="Zum Analyzer", style="HomeTeal.TButton", command=lambda: self._show_page("Analyzer / Review")).pack(fill="x")

        recent = self.ttk.Frame(overview, style="HomePanel.TFrame", padding=15)
        recent.grid(row=0, column=1, sticky="nsew", padx=5)
        self._home_accent(recent, "#a687ff")
        self.ttk.Label(recent, text="LETZTE ANALYSEN", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.ttk.Label(recent, textvariable=self.dashboard_recent, style="HomePanelMuted.TLabel", wraplength=230, justify="left").pack(anchor="w", pady=(10, 8))
        self.ttk.Label(recent, textvariable=self.overview_status, style="HomePanel.TLabel", wraplength=230, justify="left").pack(anchor="w")

        quick = self.ttk.Frame(overview, style="HomePanel.TFrame", padding=15)
        quick.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        self._home_accent(quick, "#238ffc")
        self.ttk.Label(quick, text="SCHNELLZUGRIFF", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        quick_grid = self.ttk.Frame(quick, style="HomeInner.TFrame")
        quick_grid.pack(fill="x", pady=(8, 0))
        for index, (label, target) in enumerate((
            ("Analyse öffnen  ›", "Analyzer / Review"), ("Demo laden  ›", "Analyzer / Review"),
            ("2D Tactical  ›", "Tactical Replay"), ("System prüfen  ›", "System Check / Optimizer"),
            ("Reports  ›", "Reports"), ("Einstellungen  ›", "Settings"),
        )):
            button = self.ttk.Button(quick_grid, text=label, style="HomePrimary.TButton", command=lambda value=target: self._show_page(value))
            button.grid(row=index // 2, column=index % 2, sticky="ew", padx=(0 if index % 2 == 0 else 4, 4 if index % 2 == 0 else 0), pady=3)
            quick_grid.columnconfigure(index % 2, weight=1, uniform="quick")

        lower = self.ttk.Frame(page, style="Content.TFrame")
        lower.pack(fill="x", pady=(12, 16))
        lower.columnconfigure(0, weight=1, uniform="home-lower")
        lower.columnconfigure(1, weight=1, uniform="home-lower")
        idea = self.ttk.Frame(lower, style="HomePanel.TFrame", padding=15)
        idea.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._home_accent(idea, "#2bdcbb")
        self.ttk.Label(idea, text="◉  DIE IDEE HINTER IMPROVE YOURSELF", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.ttk.Label(
            idea,
            text="Datenbasierte Analyse, gemeinsame Replay-Wahrheit und transparente lokale Werkzeuge begleiten dich Schritt für Schritt – ohne erfundene Ergebnisse.",
            style="HomePanelMuted.TLabel", wraplength=360, justify="left",
        ).pack(anchor="w", pady=(8, 0))
        community = self.ttk.Frame(lower, style="HomePanel.TFrame", padding=15)
        community.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._home_accent(community, "#a687ff")
        self.ttk.Label(community, text="◇  COMMUNITY & IDEEN", style="HomePanel.TLabel", font=(self.display_font, 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.ttk.Label(
            community,
            text="Der geschützte Kern bleibt lokal, nachvollziehbar und sicher. Community-Funktionen werden erst mit einem belegten Produktumfang ergänzt.",
            style="HomePanelMuted.TLabel", wraplength=360, justify="left",
        ).pack(anchor="w", pady=(8, 0))
        self.dashboard_modules = modules
        self.dashboard_overview = overview
        self.dashboard_lower = lower
        page.bind("<Configure>", lambda event: self._layout_dashboard(event.width))

    def _home_accent(self, parent: object, color: str) -> None:
        """Add the thin illuminated edge used throughout the Home master."""
        accent = self.tk.Frame(parent, height=3, background=color, borderwidth=0, highlightthickness=0)
        accent.pack(fill="x", anchor="n")

    def _home_module_icon(self, parent: object, glyph: str, color: str) -> object:
        canvas = self.tk.Canvas(parent, width=31, height=31, background="#0a1d30", highlightthickness=0, bd=0)
        canvas.create_oval(3, 3, 28, 28, outline="#183a54", width=2)
        canvas.create_oval(7, 7, 24, 24, outline=color, width=1)
        canvas.create_line(15, 1, 15, 6, fill=color, width=1)
        canvas.create_line(15, 25, 15, 30, fill=color, width=1)
        canvas.create_text(15, 15, text=glyph, fill="#edf9ff", font=("Segoe UI Symbol", 11, "bold"))
        return canvas

    def _home_progress_gauge(self, parent: object) -> object:
        canvas = self.tk.Canvas(parent, width=56, height=56, background="#091a2b", highlightthickness=0, bd=0)
        canvas.create_oval(4, 4, 52, 52, outline="#12364f", width=4)
        canvas.create_arc(4, 4, 52, 52, start=88, extent=214, style="arc", outline="#2bdcbb", width=3)
        canvas.create_arc(10, 10, 46, 46, start=305, extent=82, style="arc", outline="#2d9fe8", width=2)
        canvas.create_text(28, 25, text="LOCAL", fill="#dff8ff", font=(self.display_font, 7))
        canvas.create_text(28, 35, text="FLOW", fill="#75b8d7", font=(self.display_font, 7))
        return canvas

    def _draw_home_tech_line(self, canvas: object, width: int, height: int) -> None:
        canvas.delete("all")
        baseline = max(1, height // 2)
        canvas.create_line(0, baseline, width, baseline, fill="#103d5c", width=1)
        for offset in range(-20, width + 40, 42):
            canvas.create_line(offset, height, offset + 18, 0, fill="#0c2c43", width=1)
            canvas.create_line(offset + 20, height, offset + 38, 0, fill="#0a2135", width=1)
        for x in range(12, width, 96):
            canvas.create_oval(x, baseline - 2, x + 4, baseline + 2, fill="#2daff2", outline="")

    def _resize_scrollable_page(self, canvas: object, item: int, page: object, scrollbar: object, width: int) -> None:
        canvas.itemconfigure(item, width=width)
        self.root.after_idle(lambda: self._sync_scrollable_page(canvas, page, scrollbar))

    def _sync_scrollable_page(self, canvas: object, page: object, scrollbar: object) -> None:
        bounds = canvas.bbox("all")
        if bounds is None:
            return
        canvas.configure(scrollregion=bounds)
        needs_scroll = (bounds[3] - bounds[1]) > canvas.winfo_height() + 1
        shown = bool(scrollbar.winfo_manager())
        if needs_scroll and not shown:
            scrollbar.pack(side="right", fill="y")
        elif shown and not needs_scroll:
            scrollbar.pack_forget()
            canvas.yview_moveto(0.0)

    def _layout_dashboard(self, width: int) -> None:
        compact, module_height, overview_height, lower_height, gap = dashboard_layout_metrics(
            width, self.dashboard_canvas.winfo_height()
        )
        self.dashboard_compact = compact
        self.dashboard_greeting.pack_forget()
        self.dashboard_stats.pack_forget()
        if compact:
            self.dashboard_greeting.pack(fill="x")
            self.dashboard_stats.pack(anchor="w", pady=(10, 0))
        else:
            self.dashboard_greeting.pack(side="left", fill="x", expand=True)
            self.dashboard_stats.pack(side="right")
        columns = 3 if compact else 6
        for column in range(6):
            self.dashboard_module_grid.columnconfigure(column, weight=0, uniform="")
        for column in range(columns):
            self.dashboard_module_grid.columnconfigure(column, weight=1, uniform="home-modules")
        for index, card in enumerate(self.dashboard_module_cards):
            row, column = divmod(index, columns)
            card.grid_configure(
                row=row, column=column, sticky="nsew",
                padx=(0 if column == 0 else 3, 0 if column == columns - 1 else 3),
                pady=(0 if row == 0 else 6, 0),
            )
        self.dashboard_modules.rowconfigure(0, minsize=module_height)
        self.dashboard_modules.rowconfigure(1, minsize=module_height if compact else 0)
        self.dashboard_overview.rowconfigure(0, minsize=overview_height)
        self.dashboard_lower.rowconfigure(0, minsize=lower_height)
        self.dashboard_header.pack_configure(pady=(0, gap))
        self.dashboard_overview.pack_configure(pady=(gap, 0))
        self.dashboard_lower.pack_configure(pady=(gap, gap + 4))

    def _build_reports_page(self) -> None:
        page = self.pages["Reports"]
        self.ttk.Label(page, text="Reports", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        self.ttk.Label(page, text="Nachvollziehbare Ergebnisse aus der aktuellen lokalen Analyse", foreground=_THEME["muted"]).pack(anchor="w", pady=(2, 14))
        card = self.ttk.Frame(page, style="Card.TFrame", padding=20)
        card.pack(fill="x")
        self.ttk.Label(card, text="Analysebericht", style="Card.TLabel", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        self.ttk.Label(card, textvariable=self.report_status, style="Muted.TLabel", wraplength=800, justify="left").pack(anchor="w", pady=(8, 14))
        actions = self.ttk.Frame(card, style="CardInner.TFrame")
        actions.pack(fill="x")
        self.report_button = self.ttk.Button(actions, text="Report JSON öffnen", command=lambda: self._open_artifact("report"), state="disabled")
        self.report_button.pack(side="left")
        self.timeline_button = self.ttk.Button(actions, text="Timeline JSON öffnen", command=lambda: self._open_artifact("timeline"), state="disabled")
        self.timeline_button.pack(side="left", padx=8)

    def _build_settings_page(self) -> None:
        page = self.pages["Settings"]
        self.ttk.Label(page, text="Settings", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        card = self.ttk.Frame(page, style="Card.TFrame", padding=20)
        card.pack(fill="x", pady=(18, 0))
        self.ttk.Label(card, text="Darstellung", style="Card.TLabel", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        self.ttk.Label(card, text="Midnight / Metallic Blue · verbindliches Standarddesign", style="Muted.TLabel").pack(anchor="w", pady=(8, 0))
        self.ttk.Label(card, text="Keine weiteren Einstellungen werden angeboten, solange keine reale konfigurierbare Funktion dahintersteht.", style="Muted.TLabel", wraplength=800, justify="left").pack(anchor="w", pady=(6, 0))

    def _build_system_page(self) -> None:
        page = self.pages["System Check / Optimizer"]
        self.ttk.Label(page, text="System Check / Optimizer", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        self.ttk.Label(page, text="Read-only Evidenz · keine automatische Firmware-, Treiber-, Registry- oder Windows-Änderung", foreground=_THEME["muted"]).pack(anchor="w", pady=(2, 14))
        card = self.ttk.Frame(page, style="Card.TFrame", padding=24)
        card.pack(fill="x")
        self.ttk.Label(card, text="System Check", style="Card.TLabel", font=("Segoe UI Semibold", 15)).pack(anchor="w")
        self.ttk.Label(card, text="Erkannte Systemwerte, Bewertung und Hinweise bleiben getrennt. Nicht sicher belegbare Werte werden als zu prüfen angezeigt.", style="Muted.TLabel", wraplength=780, justify="left").pack(anchor="w", pady=(8, 0))
        self.ttk.Label(card, text="Optimizer-Empfehlungen erscheinen erst, wenn eine reale, sichere Funktion dahintersteht.", style="Muted.TLabel").pack(anchor="w", pady=(8, 12))
        self.ttk.Button(card, text="System Check ausführen", style="Primary.TButton", command=self._run_system_check).pack(anchor="w")
        self.ttk.Label(card, textvariable=self.system_status, style="Muted.TLabel", wraplength=800, justify="left").pack(anchor="w", pady=(10, 0))

    def _build_tactical_page(self) -> None:
        page = self.pages["Tactical Replay"]
        header = self.ttk.Frame(page, style="Content.TFrame")
        header.pack(fill="x")
        self.tactical_back_button = self.ttk.Button(header, text="← Zurück zum Review", command=self._return_to_embedded_review, state="disabled")
        self.tactical_back_button.pack(side="left")
        self.ttk.Label(header, text="Tactical Replay", font=("Segoe UI", 24, "bold")).pack(side="left", padx=16)
        self.ttk.Label(header, text="GEMEINSAME REPLAY-WAHRHEIT", foreground=_THEME["ice"], font=("Segoe UI Semibold", 9)).pack(side="right")
        context_bar = self.ttk.Frame(page, style="Card.TFrame", padding=(14, 10))
        context_bar.pack(fill="x", pady=(10, 10))
        self.ttk.Label(context_bar, textvariable=self.tactical_scene_title, style="Card.TLabel", font=("Segoe UI Semibold", 12)).pack(side="left")
        self.ttk.Label(context_bar, textvariable=self.tactical_scene_context, style="Muted.TLabel").pack(side="right")
        self.ttk.Label(page, textvariable=self.tactical_scene_note, foreground=_THEME["muted"]).pack(anchor="w", pady=(0, 8))

        body = self.ttk.Frame(page, style="Content.TFrame")
        body.pack(fill="both", expand=True)
        scene_panel = self.ttk.Frame(body, style="Card.TFrame", padding=12)
        scene_panel.pack(side="left", fill="y", padx=(0, 8))
        self.ttk.Label(scene_panel, text="SZENEN", style="Card.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.tactical_scene_list = self.tk.Listbox(
            scene_panel, width=25, background=_THEME["deep"], foreground=_THEME["ink"],
            selectbackground=_THEME["metal"], selectforeground=_THEME["ink"],
            borderwidth=0, highlightthickness=1, highlightbackground=_THEME["line_soft"],
            activestyle="none", font=("Segoe UI", 9),
        )
        self.tactical_scene_list.pack(fill="both", expand=True, pady=(8, 0))
        self.tactical_scene_list.bind("<<ListboxSelect>>", self._select_tactical_scene)

        map_panel = self.ttk.Frame(body, style="Card.TFrame", padding=8)
        map_panel.pack(side="left", fill="both", expand=True)
        frame_row = self.ttk.Frame(map_panel, style="CardInner.TFrame")
        frame_row.pack(fill="x", pady=(0, 8))
        self.ttk.Label(frame_row, text="SZENENFRAME", style="Card.TLabel").pack(side="left")
        self.tactical_frame = self.ttk.Scale(frame_row, from_=0, to=0, command=self._set_tactical_frame)
        self.tactical_frame.pack(side="left", fill="x", expand=True, padx=10)
        self.ttk.Label(frame_row, textvariable=self.tactical_frame_status, style="Muted.TLabel").pack(side="right")

        self.tactical_canvas = self.tk.Canvas(
            map_panel, background=_THEME["deep"], borderwidth=0, relief="flat",
            highlightthickness=1, highlightbackground=_THEME["line_soft"], cursor="fleur",
        )
        self.tactical_canvas.pack(fill="both", expand=True)
        self.tactical_canvas.bind("<Configure>", lambda _event: self._draw_tactical_canvas())
        self.tactical_canvas.bind("<MouseWheel>", self._wheel_tactical)
        self.tactical_canvas.bind("<ButtonPress-1>", self._start_tactical_pan)
        self.tactical_canvas.bind("<B1-Motion>", self._drag_tactical_pan)

        controls = self.ttk.Frame(page, style="Card.TFrame", padding=(12, 10))
        controls.pack(fill="x", pady=(10, 0))
        self.tactical_prev_button = self.ttk.Button(controls, text="Vorherige Szene", command=lambda: self._step_tactical_scene(-1), state="disabled")
        self.tactical_prev_button.pack(side="left")
        self.tactical_next_button = self.ttk.Button(controls, text="Nächste Szene", command=lambda: self._step_tactical_scene(1), state="disabled")
        self.tactical_next_button.pack(side="left", padx=6)
        self.ttk.Button(controls, text="In CS2 ansehen", style="Primary.TButton", command=self._open_tactical_in_cs2).pack(side="left", padx=(12, 0))
        self.ttk.Button(controls, text="−", command=lambda: self._zoom_tactical(0.85)).pack(side="left", padx=(18, 4))
        self.ttk.Button(controls, text="+", command=lambda: self._zoom_tactical(1.18)).pack(side="left")
        self.ttk.Button(controls, text="Ansicht zurücksetzen", command=self._reset_tactical_view).pack(side="left", padx=6)
        secondary = self.ttk.Frame(page, style="Content.TFrame")
        secondary.pack(fill="x", pady=(5, 0))
        self.tactical_button = self.ttk.Button(
            secondary, text="HTML-Export im Browser (Fallback)", command=lambda: self._open_artifact("tactical_replay"), state="disabled"
        )
        self.tactical_button.pack(side="right")
        self.ttk.Label(secondary, textvariable=self.tactical_action_status, foreground=_THEME["muted"]).pack(side="left")

    def run(self) -> None:
        self.root.mainloop()

    def _choose_demo(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(filetypes=[("CS2 Demo", "*.dem *.dem.zst"), ("Alle Dateien", "*.*")])
        if path:
            self._background("Demo wird lokal geparst …", lambda: self.controller.import_demo(Path(path)))

    def _open_existing(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="demo-workflow.json öffnen",
            filetypes=[("Improve Yourself Analyse", "demo-workflow.json"), ("JSON", "*.json")],
        )
        if path:
            self._background(
                "Vorhandene Analyse wird lokal geprüft …",
                lambda: self.controller.open_existing_workflow(Path(path)),
            )

    def _link_source(self) -> None:
        from tkinter import filedialog

        if self.controller.result is None:
            self.status.set("Fehler: zuerst eine vorhandene Analyse öffnen")
            return
        path = filedialog.askopenfilename(
            title="Passende Quelldemo zuordnen",
            filetypes=[("CS2 Demo", "*.dem *.dem.zst"), ("Alle Dateien", "*.*")],
        )
        if path:
            self._background(
                "Quelldemo wird per SHA-256 geprüft …",
                lambda: self.controller.link_source_demo(Path(path)),
                recheck=True,
            )

    def _background(
        self, message: str, operation: Callable[[], ShellResult], *, recheck: bool = False
    ) -> None:
        self.status.set(message)

        def worker() -> None:
            try:
                result = operation()
            except Exception as error:
                self.root.after(0, lambda: self.status.set(f"Fehler: {error}"))
            else:
                self.root.after(0, lambda: self._finish_background(result, recheck))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_background(self, result: ShellResult, recheck: bool) -> None:
        self._draw(result)
        if recheck:
            self._preflight()

    def _draw(self, result: ShellResult) -> None:
        for widget in self.workflow_widgets:
            widget.configure(state="readonly" if widget in (self.player, self.profile) else "normal")
        self.link_button.configure(state="normal")
        for box in (self.ct, self.t):
            for child in box.winfo_children():
                child.destroy()
        for item in result.players:
            box = self.ct if item.initial_team == "CT" else self.t
            self.ttk.Label(box, text=item.display_name).pack(anchor="w")
        available = self.controller.available_players()
        self.player_by_label = {f"{item.display_name} · {item.initial_team}": item.player_id for item in available}
        self.player["values"] = tuple(self.player_by_label)
        if self.player_by_label:
            self.player.current(0)
        selected_names = [item.display_name for item in result.players if item.player_id in self.controller.selected_ids]
        selection_text = "Full Demo" if self.controller.selection_mode == "full_demo" else (
            "Gewählt: " + ", ".join(selected_names) if selected_names else "Player Select · keine Spieler gewählt"
        )
        self.chosen.configure(text=selection_text)
        source_name = result.source_demo_name or "nicht zugeordnet"
        self.identity.set(f"Workflow: {result.manifest_path.name} · Quelle: {source_name} · SHA-256: {result.source_sha256[:12]}…")
        self.demo_preflight.set(
            f"Demo-Preflight: {result.parser_status} · {result.map_id} · {result.round_count} Runden · "
            f"{len(result.players)} Spieler · {result.basic_event_count} grundlegende Events"
        )
        phase = "Auswahl bereit" if result.status == "READY_FOR_SELECTION" else f"{result.scene_count} Szenen · Review bereit"
        self.status.set(f"{result.map_id} · {phase}")
        self.overview_status.set(
            f"{result.source_demo_name or 'Lokaler Workflow'} · {result.map_id} · {result.round_count} Runden · "
            f"{len(result.players)} Spieler · {phase}"
        )
        self.dashboard_rounds.set(f"{result.round_count}\nRunden")
        self.dashboard_players.set(f"{len(result.players)}\nSpieler")
        self.dashboard_scenes.set(f"{result.scene_count}\nSzenen")
        self.dashboard_readiness.set("BEREIT\nReview lokal" if result.status == "READY_FOR_REVIEW" else "BEREIT\nAuswahl lokal")
        self.dashboard_pipeline.set(
            f"{result.map_id} · Parser {result.parser_status}\n"
            f"Auswahl {self.controller.selection_mode}  ·  Szenen {result.scene_count}  ·  {phase}"
        )
        self.dashboard_recent.set(
            f"{result.source_demo_name or result.manifest_path.name}\n"
            f"SHA-256 {result.source_sha256[:12]}… · lokaler Workflow"
        )
        ready = result.status == "READY_FOR_REVIEW"
        self.report_status.set(
            f"{result.scene_count} zusammengeführte Szenen · Quelle {result.source_sha256[:12]}…"
            if ready else "Demo ist gelesen. Report und Timeline entstehen erst nach der expliziten Analyse."
        )
        for button in (self.report_button, self.timeline_button, self.tactical_button):
            button.configure(state="normal" if ready else "disabled")
        self.cs2_button.configure(state="normal" if result.status == "READY_FOR_REVIEW" else "disabled")
        self.review_button.configure(state="normal" if ready else "disabled")
        self._close_embedded_review()
        self.embedded_review = None
        self.embedded_scene_id = None
        self._select_profile()
        self._reset_preflight()

    def _select_profile(self, _event=None) -> None:
        self.controller.select_profile(self.profile.get())
        profile = self.controller.profiles[self.controller.profile_id]
        rules = profile.enabled_rule_ids if profile.enabled_rule_ids is not None else ("alle objektiven V1-Regeln",)
        self.rules.configure(text=f"{profile.purpose.title()} · " + ", ".join(rules))
        enabled = set(OBJECTIVE_RULES if profile.enabled_rule_ids is None else profile.enabled_rule_ids)
        for rule_id, variable in self.rule_vars.items():
            variable.set(rule_id in enabled)
        for check in self.rule_checks:
            check.configure(state="normal" if profile.purpose == "custom" else "disabled")

    def _save_custom_rules(self) -> None:
        enabled = tuple(rule_id for rule_id, variable in self.rule_vars.items() if variable.get())
        path = self.controller.update_custom_rules(enabled)
        self.rules.configure(text=f"Custom · lokal gespeichert: {path.name}")

    def _show_rule_details(self, rule_id: str) -> None:
        dialog = self.tk.Toplevel(self.root)
        dialog.title("Improve Yourself – Regeldetails")
        dialog.configure(background=_THEME["night"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        _enable_dark_titlebar(dialog)
        if self.app_icon is not None:
            dialog.iconphoto(True, self.app_icon)
        card = self.ttk.Frame(dialog, style="Card.TFrame", padding=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        self.ttk.Label(card, text="Regeldetails", style="Card.TLabel", font=("Segoe UI Semibold", 16)).pack(anchor="w")
        self.ttk.Label(card, text=rule_id, style="Muted.TLabel").pack(anchor="w", pady=(4, 14))
        self.ttk.Label(
            card,
            text=("Objektiver, aus der Demo belegter Szenenanker. Mehrere Marker derselben "
                  "Situation werden zu einer Szene zusammengeführt. Die Interpretation bleibt beim Nutzer."),
            style="Card.TLabel", wraplength=460, justify="left",
        ).pack(anchor="w")
        self.ttk.Button(card, text="Schließen", style="Primary.TButton", command=dialog.destroy).pack(anchor="e", pady=(18, 0))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - dialog.winfo_reqwidth()) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - dialog.winfo_reqheight()) // 2)
        dialog.geometry(f"+{x}+{y}")

    def _full(self) -> None:
        self.controller.set_full_demo()
        self._draw(self.controller.result)

    def _reset(self) -> None:
        self.controller.reset_players()
        self._draw(self.controller.result)

    def _team(self, team: str) -> None:
        self.controller.add_team(team)
        self._draw(self.controller.result)

    def _add(self) -> None:
        player_id = self.player_by_label.get(self.player.get())
        if player_id:
            self.controller.add_player(player_id)
            self._draw(self.controller.result)

    def _analyze(self) -> None:
        self._background("Auswahl wird aus demselben Replay neu berechnet …", self.controller.analyze_selection)

    def _open_review(self) -> None:
        try:
            manifest_path = self.controller.validate_current_workflow()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            coordinator = self._coordinator()
            self.embedded_review = EmbeddedReviewSession(
                manifest_path.parent / manifest["artifacts"]["analysis_flow"],
                manifest_path.parent / "review-state.json",
                str(manifest["source_sha256"]),
                coordinator,
            )
            self.embedded_scene_list.delete(0, self.tk.END)
            for scene in self.embedded_review.scenes:
                anchors = ", ".join(scene.anchor_types) or "Kontext"
                self.embedded_scene_list.insert(
                    self.tk.END, f"Runde {scene.round_number:02d} · {scene.timecode} · {anchors}"
                )
            self.embedded_review_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.embedded_review_frame.tkraise()
            if self.embedded_review.scenes:
                self.embedded_scene_list.selection_set(0)
                self.embedded_scene_list.activate(0)
                self._draw_embedded_scene(0)
            else:
                self.embedded_scene_title.set("Keine Szenen für diese Auswahl")
                self.embedded_scene_context.set("Analyse und Review bleiben gültig; die gewählten Kriterien erzeugten keine Szene.")
            self.embedded_cs2_status.set("Review lokal geladen. CS2-Bereitschaft wird beim Tick-Sprung erneut geprüft.")
        except Exception as error:
            self.status.set(f"Fehler: {error}")

    def _close_embedded_review(self) -> None:
        self.embedded_review_frame.place_forget()

    def _select_embedded_scene(self, _event=None) -> None:
        selection = self.embedded_scene_list.curselection()
        if selection:
            self._draw_embedded_scene(int(selection[0]))

    def _draw_embedded_scene(self, index: int) -> None:
        if self.embedded_review is None or not 0 <= index < len(self.embedded_review.scenes):
            return
        scene = self.embedded_review.scenes[index]
        self.embedded_scene_id = scene.scene_id
        anchors = ", ".join(scene.anchor_types) or "keine Anker"
        self.embedded_scene_title.set(
            f"Runde {scene.round_number} · Tick {scene.review_tick} · {scene.timecode}"
        )
        self.embedded_scene_context.set(
            f"Kontext {scene.start_tick}–{scene.end_tick} · Marker {', '.join(map(str, scene.marker_ticks))} · {anchors}"
        )
        self.embedded_scene_players.set("Spieler: " + (", ".join(scene.player_names) or "nicht belegt"))
        self.embedded_scene_rules.set("Regeln: " + (", ".join(scene.rule_ids) or "nicht belegt"))
        review = self.embedded_review.review(scene.scene_id)
        self.embedded_state.set(review["state"])
        self.embedded_note.delete("1.0", self.tk.END)
        self.embedded_note.insert("1.0", review["note"])

    def _step_embedded_scene(self, delta: int) -> None:
        if self.embedded_review is None or not self.embedded_review.scenes:
            return
        current = self.embedded_scene_list.curselection()
        index = int(current[0]) if current else 0
        index = max(0, min(len(self.embedded_review.scenes) - 1, index + delta))
        self.embedded_scene_list.selection_clear(0, self.tk.END)
        self.embedded_scene_list.selection_set(index)
        self.embedded_scene_list.activate(index)
        self.embedded_scene_list.see(index)
        self._draw_embedded_scene(index)

    def _save_embedded_review(self) -> None:
        if self.embedded_review is None or self.embedded_scene_id is None:
            return
        try:
            self.embedded_review.save_review(
                self.embedded_scene_id,
                self.embedded_state.get(),
                self.embedded_note.get("1.0", "end-1c"),
            )
            self.embedded_cs2_status.set("Review-Status und Notiz lokal gespeichert.")
        except Exception as error:
            self.embedded_cs2_status.set(f"Nicht gespeichert: {error}")

    def _open_embedded_in_cs2(self) -> None:
        if self.embedded_review is None or self.embedded_scene_id is None:
            return
        self._save_embedded_review()
        scene_id = self.embedded_scene_id
        self.embedded_cs2_status.set("Prüfe CS2, aktive Demo und erlaubten Szenen-Tick …")

        def worker() -> None:
            try:
                result = self.embedded_review.open_in_cs2(scene_id) if self.embedded_review else None
                if result is None:
                    raise RuntimeError("Embedded Review ist nicht geladen")
                message = f"In CS2 geöffnet: {result['demo_name']} · Tick {result['tick']}"
            except Exception as error:
                message = f"Nicht in CS2 geöffnet: {error}"
            self.root.after(0, lambda: self.embedded_cs2_status.set(message))

        threading.Thread(target=worker, daemon=True).start()

    def _open_review_fallback(self) -> None:
        try:
            self._start_review(self._coordinator())
        except Exception as error:
            self.embedded_cs2_status.set(f"Browser-Fallback nicht geöffnet: {error}")

    def _open_tactical_from_review(self) -> None:
        if self.embedded_review is None or self.embedded_scene_id is None:
            return
        self._save_embedded_review()
        try:
            manifest_path = self.controller.validate_current_workflow()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.embedded_tactical = EmbeddedTacticalSession(
                manifest_path.parent / manifest["artifacts"]["replay_v2"],
                manifest_path.parent / manifest["artifacts"]["analysis_flow"],
                str(manifest["source_sha256"]),
            )
            self.embedded_tactical.select_scene(self.embedded_scene_id)
            self.tactical_frame_index = 0
            self.tactical_zoom = 1.0
            self.tactical_pan = [0.0, 0.0]
            self.tactical_back_button.configure(state="normal")
            self.tactical_prev_button.configure(state="normal")
            self.tactical_next_button.configure(state="normal")
            self.tactical_action_status.set("Szene aus dem Analyzer Review übernommen; keine neue Analyse ausgeführt.")
            self._show_page("Tactical Replay")
            self._draw_tactical_scene()
        except Exception as error:
            self.embedded_cs2_status.set(f"Tactical Replay nicht geöffnet: {error}")

    def _return_to_embedded_review(self) -> None:
        if self.embedded_tactical and self.embedded_tactical.selected_scene_id:
            self._sync_review_scene(self.embedded_tactical.selected_scene_id)
        self._show_page("Analyzer / Review")
        self.embedded_review_frame.tkraise()

    def _sync_review_scene(self, scene_id: str) -> None:
        if self.embedded_review is None:
            return
        index = next(
            (position for position, scene in enumerate(self.embedded_review.scenes) if scene.scene_id == scene_id),
            None,
        )
        if index is None:
            raise ValueError("tactical scene is not present in embedded review")
        self.embedded_scene_list.selection_clear(0, self.tk.END)
        self.embedded_scene_list.selection_set(index)
        self.embedded_scene_list.activate(index)
        self.embedded_scene_list.see(index)
        self._draw_embedded_scene(index)

    def _step_tactical_scene(self, delta: int) -> None:
        if self.embedded_tactical is None:
            return
        scene = self.embedded_tactical.step_scene(delta)
        self._sync_review_scene(scene["scene_id"])
        self.tactical_frame_index = 0
        self._draw_tactical_scene()

    def _select_tactical_scene(self, _event=None) -> None:
        if self.tactical_ignore_selection_event:
            self.tactical_ignore_selection_event = False
            return
        if self.embedded_tactical is None or self.tactical_syncing_selection:
            return
        selected = self.tactical_scene_list.curselection()
        if not selected:
            return
        scene = self.embedded_tactical.scenes[selected[0]]
        self.embedded_tactical.select_scene(scene["scene_id"])
        self._sync_review_scene(scene["scene_id"])
        self.tactical_frame_index = 0
        self._draw_tactical_scene()

    def _draw_tactical_scene(self) -> None:
        if self.embedded_tactical is None:
            return
        scene = self.embedded_tactical.selected_scene()
        scenes = self.embedded_tactical.scenes
        if self.tactical_scene_list.size() != len(scenes):
            self.tactical_scene_list.delete(0, self.tk.END)
            for item in scenes:
                self.tactical_scene_list.insert(
                    self.tk.END,
                    f"R{item['round_number']} · Tick {item['requested_tick']}",
                )
        selected_index = next(index for index, item in enumerate(scenes) if item["scene_id"] == scene["scene_id"])
        if self.tactical_scene_list.curselection() != (selected_index,):
            self.tactical_syncing_selection = True
            self.tactical_ignore_selection_event = True
            try:
                self.tactical_scene_list.selection_clear(0, self.tk.END)
                self.tactical_scene_list.selection_set(selected_index)
                self.tactical_scene_list.see(selected_index)
            finally:
                self.tactical_syncing_selection = False
        frames = scene.get("frames", ())
        self.tactical_frame.configure(to=max(0, len(frames) - 1))
        self.tactical_frame.set(min(self.tactical_frame_index, max(0, len(frames) - 1)))
        self.tactical_frame_index = min(self.tactical_frame_index, max(0, len(frames) - 1))
        review_scene = next(
            item for item in self.embedded_review.scenes if item.scene_id == scene["scene_id"]
        ) if self.embedded_review else None
        if review_scene:
            self.tactical_scene_title.set(
                f"Runde {review_scene.round_number} · Tick {review_scene.review_tick} · {review_scene.timecode}"
            )
            review = self.embedded_review.review(review_scene.scene_id)
            selection = self.embedded_tactical.flow.get("selection", {})
            profile = self.embedded_tactical.flow.get("profile", {})
            self.tactical_scene_context.set(
                f"{self.embedded_tactical.flow.get('source', {}).get('map_id', 'Map nicht belegt')} · "
                f"Szene {review_scene.scene_id} · Spieler {', '.join(review_scene.player_names) or 'nicht belegt'} · "
                f"Profil {profile.get('profile_id', 'nicht belegt')} · Auswahl {selection.get('mode', 'nicht belegt')} · "
                f"Review {review['state']}"
            )
            self.tactical_scene_note.set(
                f"Review-Notiz: {review['note']}" if review.get("note") else "Review-Notiz: keine"
            )
        self._draw_tactical_canvas()

    def _set_tactical_frame(self, value: str) -> None:
        self.tactical_frame_index = int(round(float(value)))
        self._draw_tactical_canvas()

    def _draw_tactical_canvas(self) -> None:
        canvas = getattr(self, "tactical_canvas", None)
        if canvas is None:
            return
        canvas.delete("all")
        width, height = max(canvas.winfo_width(), 2), max(canvas.winfo_height(), 2)
        for x in range(0, width, 80):
            canvas.create_line(x, 0, x, height, fill="#183149")
        for y in range(0, height, 80):
            canvas.create_line(0, y, width, y, fill="#183149")
        if self.embedded_tactical is None:
            canvas.create_text(width / 2, height / 2, text="Szene im Analyzer Review auswählen", fill=_THEME["muted"])
            return
        scene = self.embedded_tactical.selected_scene()
        frames = scene.get("frames", ())
        if not frames:
            canvas.create_text(width / 2, height / 2, text="Keine belegten Positionsframes für diese Szene", fill=_THEME["muted"])
            self.tactical_frame_status.set("Keine Positionsframes")
            return
        self.tactical_frame_index = max(0, min(self.tactical_frame_index, len(frames) - 1))
        frame = frames[self.tactical_frame_index]
        players = frame.get("players", ())
        self.tactical_frame_status.set(
            f"Tick {frame['tick']} · Frame {self.tactical_frame_index + 1}/{len(frames)}"
        )
        if not players:
            canvas.create_text(width / 2, height / 2, text="Keine vollständigen Spielerpositionen in diesem Frame", fill=_THEME["muted"])
            return
        xs, ys = [float(player["x"]) for player in players], [float(player["y"]) for player in players]
        min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
        span = max(max_x - min_x, max_y - min_y, 1.0)
        base_scale = min(width, height) * 0.72 / span
        scale = base_scale * self.tactical_zoom
        center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
        focus = scene.get("focus_player_id")
        for player in players:
            x = width / 2 + (float(player["x"]) - center_x) * scale + self.tactical_pan[0]
            y = height / 2 - (float(player["y"]) - center_y) * scale + self.tactical_pan[1]
            color = "#55aaff" if str(player.get("side", "")).upper() == "CT" else "#ff9f43"
            radius = 10 if player.get("player_id") != focus else 14
            yaw = math.radians(float(player.get("yaw", 0.0)))
            canvas.create_line(x, y, x + math.cos(yaw) * 34, y - math.sin(yaw) * 34, fill=color, width=3)
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline=_THEME["ice"] if radius == 14 else color, width=2)
            canvas.create_text(x + 14, y - 14, text=str(player.get("name", "")), fill=_THEME["ink"], anchor="sw", font=("Segoe UI", 9))

    def _zoom_tactical(self, factor: float) -> None:
        self.tactical_zoom = max(0.5, min(4.0, self.tactical_zoom * factor))
        self._draw_tactical_canvas()

    def _wheel_tactical(self, event) -> None:
        self._zoom_tactical(1.12 if event.delta > 0 else 0.89)

    def _reset_tactical_view(self) -> None:
        self.tactical_zoom = 1.0
        self.tactical_pan = [0.0, 0.0]
        self._draw_tactical_canvas()

    def _start_tactical_pan(self, event) -> None:
        self.tactical_drag_origin = (event.x, event.y)

    def _drag_tactical_pan(self, event) -> None:
        if self.tactical_drag_origin is None:
            return
        previous_x, previous_y = self.tactical_drag_origin
        self.tactical_pan[0] += event.x - previous_x
        self.tactical_pan[1] += event.y - previous_y
        self.tactical_drag_origin = (event.x, event.y)
        self._draw_tactical_canvas()

    def _open_tactical_in_cs2(self) -> None:
        if self.embedded_tactical is None or self.embedded_review is None:
            return
        scene_id = self.embedded_tactical.selected_scene()["scene_id"]
        self.tactical_action_status.set("Prüfe CS2, aktive Demo und erlaubten Szenen-Tick …")

        def worker() -> None:
            try:
                result = self.embedded_review.open_in_cs2(scene_id)
                message = f"In CS2 geöffnet: {result['demo_name']} · Tick {result['tick']}"
            except Exception as error:
                message = f"Nicht in CS2 geöffnet: {error}"
            self.root.after(0, lambda: self.tactical_action_status.set(message))

        threading.Thread(target=worker, daemon=True).start()

    def _open_artifact(self, name: str) -> None:
        try:
            manifest_path = self.controller.validate_current_workflow()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            relative = manifest.get("artifacts", {}).get(name)
            if not isinstance(relative, str):
                raise ValueError(f"Artefakt ist nicht verfügbar: {name}")
            artifact = (manifest_path.parent / relative).resolve()
            if manifest_path.parent != artifact and manifest_path.parent not in artifact.parents:
                raise ValueError("Artefakt liegt außerhalb des lokalen Workflows")
            if not artifact.is_file():
                raise ValueError(f"Artefaktdatei fehlt: {name}")
            webbrowser.open(artifact.as_uri())
        except Exception as error:
            self.status.set(f"Fehler: {error}")

    def _run_system_check(self) -> None:
        self.system_status.set("Lokale Systemfakten werden read-only erfasst …")

        def worker() -> None:
            try:
                output = run_system_check(self.controller.output_root / "system-check.json")
                payload = json.loads(output.read_text(encoding="utf-8"))
                summary = payload["summary"]
                message = (
                    f"Abgeschlossen: {summary['OK']} OK · {summary['REVIEW']} zu prüfen · "
                    f"{summary['ACTION_REQUIRED']} Handlungsbedarf · keine Änderungen angewendet."
                )
            except Exception as error:
                message = f"System Check fehlgeschlagen: {error}"
            self.root.after(0, lambda: self.system_status.set(message))

        threading.Thread(target=worker, daemon=True).start()

    def _coordinator(self) -> Cs2ReviewCoordinator:
        manifest_path = self.controller.validate_current_workflow()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        flow_path = manifest_path.parent / manifest["artifacts"]["analysis_flow"]
        return Cs2ReviewCoordinator(flow_path, str(manifest.get("source_demo_name") or ""))

    def _preflight(self, open_after: bool = False) -> None:
        self._reset_preflight()
        self.preflight_message.set("Prüfe lokale CS2-Bereitschaft …")

        def worker() -> None:
            try:
                coordinator = self._coordinator()
                result = coordinator.preflight()
            except Exception as error:
                message = str(error)
                self.root.after(0, lambda: self._fail_preflight(message))
            else:
                self.root.after(0, lambda: self._finish_preflight(result, coordinator, open_after))

        threading.Thread(target=worker, daemon=True).start()

    def _fail_preflight(self, message: str) -> None:
        self._reset_preflight()
        self.preflight_message.set(f"Nicht bereit: {message}")

    def _finish_preflight(
        self, preflight: ReviewPreflight, coordinator: Cs2ReviewCoordinator, open_after: bool
    ) -> None:
        self.netcon_status.set(
            ("✓" if preflight.netcon_reachable else "✗") + " Lokale CS2-Verbindung: "
            + ("erreichbar" if preflight.netcon_reachable else "nicht erreichbar")
        )
        self.demo_status.set(
            ("✓" if preflight.demo_active else "✗") + " Demo-Modus: "
            + ("aktiv" if preflight.demo_active else "nicht belegt")
        )
        active = preflight.active_demo_name or "nicht erkannt"
        self.filename_status.set(
            ("✓" if preflight.filename_matches else "✗")
            + f" Dateiname: erwartet {preflight.expected_demo_name} · aktiv {active}"
        )
        self.preflight_message.set(preflight.message)
        self.embedded_cs2_status.set(preflight.message)
        if preflight.ready and open_after:
            self._start_review(coordinator)

    def _start_review(self, coordinator: Cs2ReviewCoordinator) -> None:
        result = self.controller._require_result()
        if self.review_server:
            self.review_server.close()
        self.review_server = ReviewCoordinatorServer(result.review_path, coordinator)
        self.review_server.start()
        webbrowser.open(self.review_server.url)

    def _reset_preflight(self) -> None:
        self.netcon_status.set("○ Lokale CS2-Verbindung: noch nicht geprüft")
        self.demo_status.set("○ Demo-Modus: noch nicht geprüft")
        self.filename_status.set("○ Dateiname: noch nicht geprüft")
        self.preflight_message.set("Vor dem Review CS2 prüfen.")

    def _close(self) -> None:
        if self.review_server:
            self.review_server.close()
        self.root.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Open the local real-demo Analyzer shell")
    parser.add_argument("--output", type=Path, default=default_output_root())
    parser.add_argument(
        "--workflow", type=Path,
        help="Open one explicitly selected, fail-closed validated demo-workflow.json at startup",
    )
    args = parser.parse_args()
    controller = AnalyzerShellController(args.output)
    app = AnalyzerShellApp(controller)
    if args.workflow is not None:
        app._draw(controller.open_existing_workflow(args.workflow))
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
