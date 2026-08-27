"""Thin local Viewer-demo selection over the canonical Replay V2 runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .replay_contract import PlayerState, ReplayFrame, replay_frame_from_dict
from .replay_controller import ReplayContext, ReplayController
from .replay_store import ReplayStore
from .viewer import render_viewer_state


@dataclass(frozen=True)
class ViewerDemoSelection:
    """Committed canonical state; this object owns neither playback nor camera truth."""

    context: ReplayContext
    frame: ReplayFrame
    player: PlayerState


def select_viewer_demo_state(
    store: ReplayStore,
    controller: ReplayController,
    *,
    round_number: int,
    tick: int,
    player_id: str,
) -> ViewerDemoSelection:
    """Select an exact first-person state through the sole ReplayController."""
    context = controller.seek(round_number, tick)
    context = controller.select_player(player_id)
    context = controller.set_view_mode("first_person")
    frame = replay_frame_from_dict(context.frame)
    player = next((item for item in frame.players if item.player_id == player_id), None)
    if player is None:
        raise ValueError("selected player is absent from the canonical frame")
    if not player.active or player.alive is False:
        raise ValueError("selected player is not active/alive at the resolved tick")
    if player.position is None or player.view_yaw_deg is None or player.view_pitch_deg is None:
        raise ValueError("selected player has incomplete canonical camera state")
    return ViewerDemoSelection(context=context, frame=frame, player=player)


def write_selected_2d_viewer(
    store: ReplayStore, output_path: Path, selection: ViewerDemoSelection
) -> Path:
    """Use the existing 2D viewer with a one-frame canonical scene selection."""
    # The caller already owns the one canonical store/controller/context.
    # Re-opening the manifest here would create a second presentation path.
    return render_viewer_state(store, selection.context, output_path)
