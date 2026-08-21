from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
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
    "night": "#07111e", "deep": "#0b1727", "panel": "#102033",
    "metal": "#264766", "line": "#386384", "ice": "#8edbff",
    "ink": "#edf7ff", "muted": "#a9c7dc", "success": "#76ddb0",
}


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
        icon_path = Path(__file__).with_name("assets") / "improve-yourself-icon-v3.png"
        try:
            self.app_icon = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self.app_icon)
        except tk.TclError:
            self.app_icon = None
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=_THEME["panel"], foreground=_THEME["ink"], fieldbackground=_THEME["deep"], font=("Segoe UI", 10))
        style.configure("TFrame", background=_THEME["night"])
        style.configure("Content.TFrame", background=_THEME["night"])
        style.configure("Card.TFrame", background=_THEME["panel"], relief="solid", borderwidth=1, bordercolor=_THEME["line"])
        style.configure("CardInner.TFrame", background=_THEME["panel"], relief="flat", borderwidth=0)
        style.configure("Sidebar.TFrame", background=_THEME["deep"])
        style.configure("TLabel", background=_THEME["night"], foreground=_THEME["ink"])
        style.configure("Card.TLabel", background=_THEME["panel"], foreground=_THEME["ink"])
        style.configure("Muted.TLabel", background=_THEME["panel"], foreground=_THEME["muted"])
        style.configure("TLabelframe", background=_THEME["panel"], foreground=_THEME["ink"], relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", background=_THEME["panel"], foreground=_THEME["ice"], font=("Segoe UI Semibold", 10))
        style.configure("TButton", background="#19334d", foreground="#dcefff", padding=(12, 8), borderwidth=1, bordercolor=_THEME["line"])
        style.map("TButton", background=[("active", _THEME["metal"]), ("pressed", _THEME["line"]), ("disabled", _THEME["deep"])], foreground=[("disabled", _THEME["muted"])])
        style.configure("Primary.TButton", background=_THEME["ice"], foreground="#06101a", font=("Segoe UI Semibold", 10))
        style.configure(
            "TCombobox", background=_THEME["deep"], fieldbackground=_THEME["deep"],
            foreground=_THEME["ink"], arrowcolor=_THEME["ice"], bordercolor=_THEME["line"],
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
            indicatorcolor=_THEME["deep"], indicatormargin=4,
        )
        style.map(
            "TCheckbutton",
            background=[("active", _THEME["panel"]), ("disabled", _THEME["panel"])],
            foreground=[("disabled", _THEME["muted"])],
            indicatorcolor=[("selected", _THEME["ice"]), ("disabled", _THEME["metal"])],
        )
        style.configure("Nav.TButton", anchor="w", background=_THEME["deep"], foreground=_THEME["muted"], padding=(18, 12), borderwidth=0)
        style.configure("NavActive.TButton", anchor="w", background=_THEME["metal"], foreground=_THEME["ink"], padding=(18, 12), borderwidth=0)
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
        self.report_status = tk.StringVar(value="Nach einer Analyse stehen Report und Timeline lokal bereit.")
        self.system_status = tk.StringVar(value="System Check wurde noch nicht ausgeführt.")

        shell = ttk.Frame(self.root, style="Content.TFrame")
        shell.pack(fill="both", expand=True)
        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", width=245)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
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
        self.nav_buttons: dict[str, ttk.Button] = {}
        for name in UI_REFERENCE_STATUS:
            page = ttk.Frame(content, style="Content.TFrame")
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.pages[name] = page
            button = ttk.Button(sidebar, text=name, style="Nav.TButton", command=lambda value=name: self._show_page(value))
            button.pack(fill="x", padx=8, pady=1)
            self.nav_buttons[name] = button
        tk.Label(sidebar, text="LOCAL · PRIVATE · READ-ONLY WHERE MARKED", background=_THEME["deep"], foreground=_THEME["muted"], wraplength=205, justify="left", font=("Segoe UI", 8)).pack(side="bottom", anchor="w", padx=18, pady=18)

        frame = self.pages["Analyzer / Review"]
        ttk.Label(frame, text="Analyzer / Review", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Demo → Parser → Auswahl → Profil → Regeln → Szenen → Review", foreground=_THEME["muted"]).pack(anchor="w", pady=(2, 3))
        ttk.Label(frame, textvariable=self.status, foreground=_THEME["ice"]).pack(anchor="w", pady=(0, 14))
        source_actions = ttk.Frame(frame)
        source_actions.pack(fill="x")
        ttk.Button(source_actions, text="Demo auswählen", style="Primary.TButton", command=self._choose_demo).pack(side="left")
        ttk.Button(source_actions, text="Vorhandene Analyse öffnen", command=self._open_existing).pack(side="left", padx=8)
        self.link_button = ttk.Button(source_actions, text="Quelldemo zuordnen", command=self._link_source, state="disabled")
        self.link_button.pack(side="left")
        ttk.Label(frame, textvariable=self.identity).pack(anchor="w", pady=(8, 0))
        ttk.Label(frame, textvariable=self.demo_preflight).pack(anchor="w", pady=(2, 4))

        teams = ttk.Frame(frame)
        teams.pack(fill="x", pady=14)
        self.ct = ttk.LabelFrame(teams, text="CT", padding=10)
        self.ct.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.t = ttk.LabelFrame(teams, text="T", padding=10)
        self.t.pack(side="left", fill="both", expand=True, padx=(6, 0))

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=8)
        self.workflow_widgets = []
        for text, command in (("Full Demo", self._full), ("CT", lambda: self._team("CT")), ("T", lambda: self._team("T")), ("Reset", self._reset)):
            button = ttk.Button(controls, text=text, command=command, state="disabled")
            button.pack(side="left", padx=4 if text != "Full Demo" else 0)
            self.workflow_widgets.append(button)
        self.player = ttk.Combobox(controls, state="disabled", width=32)
        self.player.pack(side="left", padx=(18, 4))
        self.add_button = ttk.Button(controls, text="+ Add Player", command=self._add, state="disabled")
        self.add_button.pack(side="left")
        self.workflow_widgets.extend((self.player, self.add_button))

        profile_row = ttk.Frame(frame)
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
        self.rule_vars: dict[str, tk.BooleanVar] = {}
        self.rule_checks = []
        labels = {
            "objective_kill": "Kill", "objective_multi_kill": "Multi-Kill", "objective_headshot": "Headshot",
            "objective_wallbang": "Wallbang", "objective_smoke_kill": "Smoke-Kill",
            "objective_blind_kill": "Blind-Kill", "objective_entry": "Entry",
        }
        for rule_id in OBJECTIVE_RULES:
            variable = tk.BooleanVar(value=True)
            check = ttk.Checkbutton(rules_frame, text=labels[rule_id], variable=variable, command=self._save_custom_rules)
            check.pack(anchor="w", pady=4)
            check.bind("<Double-Button-1>", lambda _event, value=rule_id: self._show_rule_details(value))
            self.rule_vars[rule_id] = variable
            self.rule_checks.append(check)
        self.workflow_widgets.extend(self.rule_checks)
        ttk.Label(self.pages["Rules"], text=f"Lokale Profile: {controller.profile_store.root}", foreground=_THEME["muted"]).pack(anchor="w", pady=(10, 5))

        self.chosen = ttk.Label(frame, text="Full Demo")
        self.chosen.pack(anchor="w", pady=8)
        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=8)
        self.analyze_button = ttk.Button(actions, text="Analyse starten", command=self._analyze, state="disabled")
        self.analyze_button.pack(side="left")
        self.cs2_button = ttk.Button(actions, text="CS2 prüfen", command=self._preflight, state="disabled")
        self.cs2_button.pack(side="left", padx=8)
        self.workflow_widgets.extend((self.analyze_button, self.cs2_button))
        self.review_button = ttk.Button(actions, text="Review öffnen", command=self._open_review, state="disabled")
        self.review_button.pack(side="left")
        preflight = ttk.LabelFrame(frame, text="CS2-Readiness", padding=10)
        preflight.pack(fill="x", pady=10)
        for variable in (self.netcon_status, self.demo_status, self.filename_status, self.preflight_message):
            ttk.Label(preflight, textvariable=variable).pack(anchor="w")
        self._build_dashboard_page()
        self._build_reports_page()
        self._build_settings_page()
        self._build_system_page()
        self._build_tactical_page()
        self._show_page("Analyzer / Review")
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _show_page(self, name: str) -> None:
        self.pages[name].tkraise()
        for page_name, button in self.nav_buttons.items():
            button.configure(style="NavActive.TButton" if page_name == name else "Nav.TButton")

    def _build_dashboard_page(self) -> None:
        page = self.pages["Dashboard"]
        self.ttk.Label(page, text="Dashboard", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        self.ttk.Label(page, text="Lokaler Einstieg und aktueller Arbeitsstand", foreground=_THEME["muted"]).pack(anchor="w", pady=(2, 14))
        grid = self.ttk.Frame(page, style="Content.TFrame")
        grid.pack(fill="x")
        for column, (title, detail, target) in enumerate((
            ("Demo Analyzer", "Echte Demo lesen, Spieler wählen und Szenen erzeugen.", "Analyzer / Review"),
            ("Tactical Replay", "Erzeugte Situationen aus derselben Replay-Wahrheit prüfen.", "Tactical Replay"),
            ("System Check", "Lokale Systemfakten read-only erfassen.", "System Check / Optimizer"),
        )):
            grid.columnconfigure(column, weight=1, uniform="modules")
            card = self.ttk.Frame(grid, style="Card.TFrame", padding=20)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0 if column == 2 else 6))
            self.ttk.Label(card, text=title, style="Card.TLabel", font=("Segoe UI Semibold", 14)).pack(anchor="w")
            self.ttk.Label(card, text=detail, style="Muted.TLabel", wraplength=250, justify="left").pack(anchor="w", pady=(8, 16))
            self.ttk.Button(card, text="Öffnen", command=lambda value=target: self._show_page(value)).pack(anchor="w")
        recent = self.ttk.Frame(page, style="Card.TFrame", padding=20)
        recent.pack(fill="x", pady=(16, 0))
        self.ttk.Label(recent, text="Aktueller lokaler Stand", style="Card.TLabel", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        self.ttk.Label(recent, textvariable=self.overview_status, style="Muted.TLabel", wraplength=800, justify="left").pack(anchor="w", pady=(8, 0))

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
        self.ttk.Label(page, text="Tactical Replay", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        card = self.ttk.Frame(page, style="Card.TFrame", padding=24)
        card.pack(fill="x", pady=(18, 0))
        self.ttk.Label(card, text="Eine gemeinsame Replay-Wahrheit", style="Card.TLabel", font=("Segoe UI Semibold", 15)).pack(anchor="w")
        self.ttk.Label(card, text="Nach der Analyse wird der echte Tactical-Replay-HTML-Export zusammen mit Timeline, Report und CS2-Ticks erzeugt. Der Review-Einstieg bleibt im Analyzer freigegeben, sobald die lokale CS2-Prüfung bestanden ist.", style="Muted.TLabel", wraplength=800, justify="left").pack(anchor="w", pady=(8, 0))
        self.tactical_button = self.ttk.Button(card, text="Tactical Replay öffnen", command=lambda: self._open_artifact("tactical_replay"), state="disabled")
        self.tactical_button.pack(anchor="w", pady=(14, 0))

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
        ready = result.status == "READY_FOR_REVIEW"
        self.report_status.set(
            f"{result.scene_count} zusammengeführte Szenen · Quelle {result.source_sha256[:12]}…"
            if ready else "Demo ist gelesen. Report und Timeline entstehen erst nach der expliziten Analyse."
        )
        for button in (self.report_button, self.timeline_button, self.tactical_button):
            button.configure(state="normal" if ready else "disabled")
        self.cs2_button.configure(state="normal" if result.status == "READY_FOR_REVIEW" else "disabled")
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
        self._preflight(open_after=True)

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
        self.review_button.configure(state="normal" if preflight.ready else "disabled")
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
        self.review_button.configure(state="disabled")

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
