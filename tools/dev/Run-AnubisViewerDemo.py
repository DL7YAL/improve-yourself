"""Launch a local Anubis 2D + embedded-3D Viewer demonstration.

All input paths are local CLI arguments.  Replay state is selected only through
ReplayController; map availability remains the existing iy.map_asset/v1 gate.
"""

from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from improve_yourself.map_assets import assess_map_asset
from improve_yourself.panda_renderer import PandaReplayRenderer
from improve_yourself.renderer_session import ReplayRendererSession
from improve_yourself.replay_controller import ReplayController
from improve_yourself.replay_store import ReplayStore
from improve_yourself.viewer_demo import select_viewer_demo_state, write_selected_2d_viewer


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the local canonical Anubis Viewer demo")
    parser.add_argument("manifest", type=Path, help="verified iy.map_asset/v1 Anubis manifest")
    parser.add_argument("replay", type=Path, help="canonical iy.replay/v2 manifest")
    parser.add_argument("--round-number", type=int, required=True)
    parser.add_argument("--tick", type=int, required=True)
    parser.add_argument("--player", required=True)
    parser.add_argument("--two-d-output", type=Path, required=True)
    parser.add_argument("--owned-presentation", type=Path, help="strict owned presentation-only descriptor")
    parser.add_argument("--owned-scene-presentation", type=Path, help="strict owned visual-readiness descriptor")
    parser.add_argument("--three-d-screenshot", type=Path)
    parser.add_argument("--seconds", type=float, default=12.0)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    store = ReplayStore(args.replay)
    controller = ReplayController(store)
    selection = select_viewer_demo_state(
        store, controller, round_number=args.round_number, tick=args.tick, player_id=args.player,
    )
    viewer_path = write_selected_2d_viewer(store, controller, args.two_d_output, selection)
    assessment = assess_map_asset(args.manifest, store.manifest["source"]["map_id"])
    base = {
        "tick": selection.context.resolved_tick,
        "player_id": selection.player.player_id,
        "position": selection.player.position.__dict__,
        "team": selection.player.team,
        "weapon": selection.player.weapon,
        "two_d_viewer": str(viewer_path),
    }
    if assessment.availability != "available":
        print(json.dumps({**base, "status": "2D_ONLY", "three_d": "unavailable", "reason": assessment.reason}))
        return 0

    root = tk.Tk()
    root.title("Improve Yourself — Anubis Viewer demo")
    root.geometry("1100x700")
    viewport = tk.Frame(root, background="#090c10")
    viewport.pack(fill="both", expand=True)
    root.update_idletasks()
    renderer = PandaReplayRenderer(viewport.winfo_id())
    renderer.load_map(args.manifest, store.manifest["source"]["map_id"])
    session = ReplayRendererSession(controller, renderer)
    proof_labels = []
    proof_background = None
    if args.owned_presentation is not None:
        renderer.load_owned_tactical_representation(args.owned_presentation, store.manifest["source"]["map_id"])
    if args.owned_scene_presentation is not None:
        renderer.load_owned_scene_presentation(args.owned_scene_presentation, store.manifest["source"]["map_id"])
    if args.owned_presentation is not None or args.owned_scene_presentation is not None:
        from direct.gui.OnscreenText import OnscreenText
        from panda3d.core import CardMaker, TextNode

        card = CardMaker("local-technical-proof-background")
        card.setFrame(-1.31, -0.10, 0.42, 0.99)
        proof_background = renderer._base.aspect2d.attachNewNode(card.generate())
        proof_background.setColor(0.01, 0.025, 0.05, 0.90)
        proof_background.setBin("fixed", 99)
        proof_background.setDepthTest(False)
        proof_background.setDepthWrite(False)
        proof_text = ["LOCAL TECHNICAL PROOF", "OWNED IMPROVE PRESENTATION ONLY"]
        if args.owned_presentation is not None:
            proof_text.extend((
                "TACTICAL REPRESENTATION — NOT MAP/COLLISION AUTHORITY",
                "OUTBOX: NOT AVAILABLE",
            ))
        if args.owned_scene_presentation is not None:
            scene_status = renderer.owned_scene_status
            assert scene_status is not None
            proof_text.append(f"VISUAL SCENE: {scene_status['visual_scene'].upper()} — NOT PRODUCT MAP ART")
        proof_labels = [
            OnscreenText(
                text="\n".join(proof_text), pos=(-1.27, 0.88), align=TextNode.ALeft, scale=0.047,
                fg=(0.78, 0.91, 1.0, 1.0), mayChange=False,
            ),
        ]
        for label in proof_labels:
            label.reparentTo(renderer._base.aspect2d)
            label.setBin("fixed", 100)
            label.setDepthTest(False)
            label.setDepthWrite(False)
    sizes: list[tuple[int, int]] = []

    def draw() -> None:
        if not root.winfo_exists():
            return
        renderer.resize(max(1, viewport.winfo_width()), max(1, viewport.winfo_height()))
        size = (viewport.winfo_width(), viewport.winfo_height())
        if not sizes or sizes[-1] != size:
            sizes.append(size)
        session.render()
        root.after(16, draw)

    def screenshot() -> None:
        if args.three_d_screenshot is None:
            return
        from panda3d.core import Filename

        args.three_d_screenshot.parent.mkdir(parents=True, exist_ok=True)
        renderer._base.win.saveScreenshot(Filename.fromOsSpecific(str(args.three_d_screenshot.resolve())))

    def close() -> None:
        for label in proof_labels:
            label.destroy()
        if proof_background is not None:
            proof_background.removeNode()
        session.dispose()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    root.after(2000, lambda: root.geometry("900x560"))
    root.after(max(100, int(args.seconds * 500)), screenshot)
    root.after(int(args.seconds * 1000), close)
    root.after(0, draw)
    root.mainloop()
    print(json.dumps({
        **base,
        "status": "PASS",
        "three_d": "available",
        "first_person": True,
        "resize": len(sizes) >= 2,
        "owned_presentation": renderer.owned_presentation_status,
        "owned_scene_presentation": renderer.owned_scene_status,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
