from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .demo_workflow import rerender_demo_workflow, run_demo_workflow


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

        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Demo Analyzer", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.status).pack(anchor="w", pady=(4, 14))
        ttk.Button(frame, text="Demo auswählen", command=self._choose_demo).pack(anchor="w")

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
        ttk.Button(actions, text="Review öffnen", command=self._open_review).pack(side="left", padx=8)

    def run(self) -> None:
        self.root.mainloop()

    def _choose_demo(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(filetypes=[("CS2 Demo", "*.dem *.dem.zst"), ("Alle Dateien", "*.*")])
        if path:
            self._background("Demo wird lokal geparst …", lambda: self.controller.import_demo(Path(path)))

    def _background(self, message: str, operation: Callable[[], ShellResult]) -> None:
        self.status.set(message)

        def worker() -> None:
            try:
                result = operation()
            except Exception as error:
                self.root.after(0, lambda: self.status.set(f"Fehler: {error}"))
            else:
                self.root.after(0, lambda: self._draw(result))

        threading.Thread(target=worker, daemon=True).start()

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
        result = self.controller._require_result()
        webbrowser.open(result.review_path.as_uri())


def main() -> int:
    parser = argparse.ArgumentParser(description="Open the local real-demo Analyzer shell")
    parser.add_argument("--output", type=Path, default=Path("results/analyzer-shell"))
    args = parser.parse_args()
    AnalyzerShellApp(AnalyzerShellController(args.output)).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
