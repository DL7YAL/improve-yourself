from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .renderer import ReplayRenderer
from .replay_contract import replay_frame_from_dict
from .replay_controller import ReplayContext, ReplayController

SessionViewMode = Literal["tactical_2d", "first_person", "analysis_third_person"]


@dataclass(frozen=True)
class RendererSessionState:
    active: bool
    requested_tick: int
    resolved_tick: int
    selected_player_id: str | None
    view_mode: SessionViewMode


class ReplayRendererSession:
    """One-way adapter from ReplayController truth to a renderer backend."""

    def __init__(self, controller: ReplayController, renderer: ReplayRenderer) -> None:
        self._controller = controller
        self._renderer = renderer
        self._disposed = False
        self._state: RendererSessionState | None = None
        self._unsubscribe = controller.subscribe(self._apply)
        self._apply(controller.snapshot())

    @property
    def state(self) -> RendererSessionState:
        if self._state is None:
            raise RuntimeError("renderer session has no controller snapshot")
        return self._state

    def _apply(self, context: ReplayContext) -> None:
        if self._disposed:
            return
        if context.frame.get("tick") != context.resolved_tick:
            raise ValueError("controller frame tick differs from resolved_tick")
        frame = replay_frame_from_dict(context.frame)
        self._renderer.set_frame(frame)
        if context.view_mode == "first_person":
            self._renderer.set_view_mode("first_person")
        elif context.view_mode == "analysis_third_person":
            self._renderer.set_view_mode("third_person")
        if context.selected_player_id is not None:
            self._renderer.set_camera_player(context.selected_player_id)
        self._state = RendererSessionState(
            active=context.view_mode in ("first_person", "analysis_third_person")
            and context.selected_player_id is not None,
            requested_tick=context.requested_tick,
            resolved_tick=context.resolved_tick,
            selected_player_id=context.selected_player_id,
            view_mode=context.view_mode,
        )

    def render(self) -> bool:
        if self._disposed:
            raise RuntimeError("renderer session is disposed")
        if not self.state.active:
            return False
        self._renderer.render()
        return True

    def dispose(self) -> None:
        if not self._disposed:
            self._unsubscribe()
            self._renderer.dispose()
            self._disposed = True
