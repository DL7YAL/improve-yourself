from __future__ import annotations

import argparse
import hashlib
import json
import re
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .cs2_review_coordinator import Cs2ReviewCoordinator, ReviewCoordinatorServer, ReviewPreflight
from .demo_workflow import rerender_demo_workflow, run_demo_workflow
from .replay_store import ReplayStore


_SOURCE_HASH = re.compile(r"[0-9a-f]{64}")
_REQUIRED_ARTIFACTS = (
    "analysis", "replay_v2", "analysis_flow", "timeline", "review", "cs2_review_commands"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_existing_workflow(manifest_path: Path) -> Path:
    """Fail-closed validation for an explicitly selected local workflow."""
    manifest_path = manifest_path.resolve()
    if manifest_path.name != "demo-workflow.json" or not manifest_path.is_file():
        raise ValueError("select an existing demo-workflow.json file")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != "iy.demo_workflow/v1":
        raise ValueError("expected iy.demo_workflow/v1 manifest")
    if manifest.get("status") != "READY_FOR_REVIEW":
        raise ValueError("workflow is not READY_FOR_REVIEW")
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
    for name in _REQUIRED_ARTIFACTS:
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
    for round_number in store.round_numbers:
        store.load_round(round_number)

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


class AnalyzerShellController:
    def __init__(
        self,
        output_root: Path,
        *,
        runner: Callable[..., Path] = run_demo_workflow,
        rerenderer: Callable[..., Path] = rerender_demo_workflow,
    ) -> None:
        self.output_root = output_root
        self._runner = runner
        self._rerenderer = rerenderer
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
        manifest = self._rerenderer(result.manifest_path, player_ids=tuple(self.selected_ids))
        self.result = self._load(manifest)
        return self.result

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
        flow = json.loads((root / manifest["artifacts"]["analysis_flow"]).read_text(encoding="utf-8"))
        players = tuple(
            ShellPlayer(item["player_id"], item["display_name"], item["initial_team"])
            for item in flow["roster"]
        )
        return ShellResult(
            manifest_path=manifest_path,
            review_path=root / manifest["artifacts"]["review"],
            players=players,
            selected_ids=tuple(flow["selection"]["player_ids"]),
            selection_mode=flow["selection"]["mode"],
            scene_count=len(flow["scenes"]),
            map_id=str(flow["source"].get("map_id") or "unknown"),
            source_demo_name=str(manifest.get("source_demo_name") or ""),
        )


class AnalyzerShellApp:
    def __init__(self, controller: AnalyzerShellController) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("Improve Yourself — Demo Analyzer")
        self.root.geometry("860x620")
        self.status = tk.StringVar(value="Echte CS2-Demo auswählen")
        self.player_by_label: dict[str, str] = {}
        self.review_server: ReviewCoordinatorServer | None = None
        self.netcon_status = tk.StringVar(value="○ Lokale CS2-Verbindung: noch nicht geprüft")
        self.demo_status = tk.StringVar(value="○ Demo-Modus: noch nicht geprüft")
        self.filename_status = tk.StringVar(value="○ Dateiname: noch nicht geprüft")
        self.preflight_message = tk.StringVar(value="Vor dem Review CS2 prüfen.")

        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Demo Analyzer", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.status).pack(anchor="w", pady=(4, 14))
        source_actions = ttk.Frame(frame)
        source_actions.pack(fill="x")
        ttk.Button(source_actions, text="Demo auswählen", command=self._choose_demo).pack(side="left")
        ttk.Button(source_actions, text="Vorhandene Analyse öffnen", command=self._open_existing).pack(side="left", padx=8)
        ttk.Button(source_actions, text="Quelldemo zuordnen", command=self._link_source).pack(side="left")

        teams = ttk.Frame(frame)
        teams.pack(fill="x", pady=14)
        self.ct = ttk.LabelFrame(teams, text="CT", padding=10)
        self.ct.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.t = ttk.LabelFrame(teams, text="T", padding=10)
        self.t.pack(side="left", fill="both", expand=True, padx=(6, 0))

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=8)
        ttk.Button(controls, text="Full Demo", command=self._full).pack(side="left")
        ttk.Button(controls, text="CT", command=lambda: self._team("CT")).pack(side="left", padx=4)
        ttk.Button(controls, text="T", command=lambda: self._team("T")).pack(side="left", padx=4)
        ttk.Button(controls, text="Reset", command=self._reset).pack(side="left", padx=4)
        self.player = ttk.Combobox(controls, state="readonly", width=36)
        self.player.pack(side="left", padx=(18, 4))
        ttk.Button(controls, text="+ Add Player", command=self._add).pack(side="left")

        self.chosen = ttk.Label(frame, text="Full Demo")
        self.chosen.pack(anchor="w", pady=8)
        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Analyse starten", command=self._analyze).pack(side="left")
        ttk.Button(actions, text="CS2 prüfen", command=self._preflight).pack(side="left", padx=8)
        self.review_button = ttk.Button(actions, text="Review öffnen", command=self._open_review, state="disabled")
        self.review_button.pack(side="left")
        preflight = ttk.LabelFrame(frame, text="CS2-Readiness", padding=10)
        preflight.pack(fill="x", pady=10)
        for variable in (self.netcon_status, self.demo_status, self.filename_status, self.preflight_message):
            ttk.Label(preflight, textvariable=variable).pack(anchor="w")
        self.root.protocol("WM_DELETE_WINDOW", self._close)

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
        self.status.set(f"{result.map_id} · {len(result.players)} Spieler · {result.scene_count} Szenen")
        self._reset_preflight()

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

    def _coordinator(self) -> Cs2ReviewCoordinator:
        result = self.controller._require_result()
        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        flow_path = result.manifest_path.parent / manifest["artifacts"]["analysis_flow"]
        return Cs2ReviewCoordinator(flow_path, result.source_demo_name)

    def _preflight(self, open_after: bool = False) -> None:
        self.review_button.configure(state="disabled")
        self.preflight_message.set("Prüfe lokale CS2-Bereitschaft …")
        try:
            coordinator = self._coordinator()
        except Exception as error:
            self.preflight_message.set(f"Nicht bereit: {error}")
            return

        def worker() -> None:
            result = coordinator.preflight()
            self.root.after(0, lambda: self._finish_preflight(result, coordinator, open_after))

        threading.Thread(target=worker, daemon=True).start()

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
    parser.add_argument("--output", type=Path, default=Path("results/analyzer-shell"))
    args = parser.parse_args()
    AnalyzerShellApp(AnalyzerShellController(args.output)).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
