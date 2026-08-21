from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from improve_yourself.panda_renderer import PandaReplayRenderer
from improve_yourself.replay_contract import replay_frame_from_dict
from improve_yourself.replay_store import ReplayStore
from improve_yourself.sightlines import evaluate_sightline, present_sightline
from improve_yourself.visibility_mesh import TriVisibilityMesh


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--seconds", type=float, default=12.0)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--round-number", type=int)
    parser.add_argument("--tick", type=int)
    parser.add_argument("--player")
    parser.add_argument("--target", action="append", default=[])
    args = parser.parse_args()
    store = ReplayStore(args.replay)
    if (args.round_number is None) != (args.tick is None):
        parser.error("--round-number and --tick must be supplied together")
    chosen = (
        replay_frame_from_dict(store.exact_frame(args.round_number, args.tick))
        if args.round_number is not None
        else None
    )
    if chosen is None:
        for round_number in store.round_numbers:
            for raw in store.load_round(round_number)["frames"]:
                candidate = replay_frame_from_dict(raw)
                if any(p.active and p.alive is not False and p.position and p.view_yaw_deg is not None and p.view_pitch_deg is not None for p in candidate.players):
                    chosen = candidate
                    break
            if chosen:
                break
    if chosen is None:
        raise RuntimeError("replay contains no complete canonical camera frame")
    player = next(
        p for p in chosen.players
        if (args.player is None or p.player_id == args.player)
        and p.active and p.alive is not False and p.position
        and p.view_yaw_deg is not None and p.view_pitch_deg is not None
    )
    geometry = TriVisibilityMesh.from_verified_manifest(args.manifest, store.manifest["source"]["map_id"])
    results = tuple(evaluate_sightline(chosen, player.player_id, target, geometry) for target in args.target)
    segments = tuple(segment for result in results if (segment := present_sightline(chosen, result)) is not None)

    root = tk.Tk()
    root.title("Improve Yourself — Slice D native embed spike")
    root.geometry("1100x700")
    viewport = tk.Frame(root, background="#090c10")
    viewport.pack(fill="both", expand=True)
    root.update_idletasks()
    renderer = PandaReplayRenderer(viewport.winfo_id())
    renderer.load_map(args.manifest)
    renderer.set_frame(chosen)
    renderer.set_camera_player(player.player_id)
    renderer.set_view_mode("third_person")
    renderer.set_sightlines(segments)
    sizes = []
    views = ["third_person"]

    def draw():
        if not root.winfo_exists():
            return
        renderer.resize(max(1, viewport.winfo_width()), max(1, viewport.winfo_height()))
        size = (viewport.winfo_width(), viewport.winfo_height())
        if not sizes or sizes[-1] != size:
            sizes.append(size)
        renderer.render()
        root.after(16, draw)

    def close():
        renderer.dispose()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    root.after(2000, lambda: root.geometry("900x560"))
    root.after(3000, lambda: (renderer.set_view_mode("first_person"), views.append("first_person")))
    root.after(4000, lambda: (renderer.set_view_mode("third_person"), views.append("third_person")))
    if args.screenshot:
        def screenshot():
            from panda3d.core import Filename

            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            renderer._base.win.saveScreenshot(Filename.fromOsSpecific(str(args.screenshot.resolve())))

        root.after(5000, screenshot)
    root.after(int(args.seconds * 1000), close)
    root.after(0, draw)
    root.mainloop()
    pose = renderer._camera_pose
    print(json.dumps({"status": "PASS", "tick": chosen.tick, "player_id": player.player_id, "views": views, "sightlines": [{"target": result.target_player_id, "result": result.result, "geometry": result.geometry_state, "smoke": result.smoke_state} for result in results], "obstruction_state": pose.obstruction_state, "camera_adjusted": pose.camera_adjusted, "sizes": sizes, "resize": len(sizes) >= 2, "dispose": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
