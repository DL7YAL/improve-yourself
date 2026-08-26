from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable, Literal

from .replay_store import ReplayStore

PlayState = Literal["paused", "playing"]
ViewMode = Literal["tactical_2d", "first_person", "analysis_third_person"]

PLAYBACK_SPEEDS = (0.25, 0.5, 1.0, 2.0)
VIEW_MODES = ("tactical_2d", "first_person", "analysis_third_person")


class PlaybackTimingUnavailable(RuntimeError):
    """Raised when wall-clock playback is requested without evidenced timing."""


@dataclass(frozen=True)
class ReplayContext:
    current_round: int
    requested_tick: int
    resolved_tick: int
    frame: dict[str, Any]
    play_state: PlayState
    playback_speed: float
    selected_player_id: str | None
    selected_scene_id: str | None
    view_mode: ViewMode
    tick_rate: float | None
    timing_available: bool


class ReplayController:
    """The sole mutable playback authority for all replay views."""

    def __init__(self, store: ReplayStore) -> None:
        self._store = store
        self._lock = RLock()
        self._listeners: list[Callable[[ReplayContext], None]] = []
        self._player_ids = {item["player_id"] for item in store.manifest["players"]}
        self._scenes = {item["scene_id"]: item for item in store.manifest.get("scenes", [])}
        self._tick_rate = store.manifest["source"].get("tick_rate")
        first_round = store.round_numbers[0]
        first_tick = store.round_descriptor(first_round)["first_tick"]
        self._round = first_round
        self._requested_tick = first_tick
        self._resolved_tick = first_tick
        self._frame = store.exact_frame(first_round, first_tick)
        self._play_state: PlayState = "paused"
        self._speed = 1.0
        self._selected_player_id: str | None = None
        self._selected_scene_id: str | None = None
        self._view_mode: ViewMode = "tactical_2d"
        self._fractional_ticks = 0.0

    def snapshot(self) -> ReplayContext:
        with self._lock:
            return ReplayContext(
                current_round=self._round,
                requested_tick=self._requested_tick,
                resolved_tick=self._resolved_tick,
                frame=self._frame,
                play_state=self._play_state,
                playback_speed=self._speed,
                selected_player_id=self._selected_player_id,
                selected_scene_id=self._selected_scene_id,
                view_mode=self._view_mode,
                tick_rate=self._tick_rate,
                timing_available=self._tick_rate is not None,
            )

    def subscribe(self, listener: Callable[[ReplayContext], None]) -> Callable[[], None]:
        with self._lock:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe

    def _publish(self) -> ReplayContext:
        context = self.snapshot()
        for listener in tuple(self._listeners):
            listener(context)
        return context

    def seek(self, round_number: int, tick: int) -> ReplayContext:
        frame = self._store.frame_at_or_before(round_number, tick)
        with self._lock:
            self._round = round_number
            self._requested_tick = tick
            self._resolved_tick = frame["tick"]
            self._frame = frame
            self._selected_scene_id = None
            self._fractional_ticks = 0.0
        return self._publish()

    def seek_scene(self, scene_id: str) -> ReplayContext:
        try:
            scene = self._scenes[scene_id]
        except KeyError as error:
            raise KeyError(f"scene {scene_id!r} is not available") from error
        frame = self._store.frame_at_or_before(scene["round_number"], scene["tick"])
        focus = scene.get("focus_player_id")
        with self._lock:
            self._round = scene["round_number"]
            self._requested_tick = scene["tick"]
            self._resolved_tick = frame["tick"]
            self._frame = frame
            self._selected_scene_id = scene_id
            if focus is not None:
                self._selected_player_id = focus
            self._fractional_ticks = 0.0
        return self._publish()

    def select_player(self, player_id: str | None) -> ReplayContext:
        if player_id is not None and player_id not in self._player_ids:
            raise KeyError(f"player {player_id!r} is not available")
        with self._lock:
            self._selected_player_id = player_id
        return self._publish()

    def set_view_mode(self, mode: ViewMode) -> ReplayContext:
        if mode not in VIEW_MODES:
            raise ValueError(f"unsupported view mode: {mode}")
        with self._lock:
            self._view_mode = mode
        return self._publish()

    def set_speed(self, speed: float) -> ReplayContext:
        if speed not in PLAYBACK_SPEEDS:
            raise ValueError(f"unsupported playback speed: {speed}")
        with self._lock:
            self._speed = speed
            self._fractional_ticks = 0.0
        return self._publish()

    def play(self) -> ReplayContext:
        if self._tick_rate is None:
            raise PlaybackTimingUnavailable(
                "playback requires an evidenced positive tick rate; tick navigation remains available"
            )
        with self._lock:
            self._play_state = "playing"
        return self._publish()

    def pause(self) -> ReplayContext:
        with self._lock:
            self._play_state = "paused"
            self._fractional_ticks = 0.0
        return self._publish()

    def advance(self, elapsed_seconds: float) -> ReplayContext:
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must not be negative")
        if self._tick_rate is None:
            raise PlaybackTimingUnavailable("cannot advance without an evidenced tick rate")
        with self._lock:
            if self._play_state != "playing" or elapsed_seconds == 0:
                return self.snapshot()
            total = self._fractional_ticks + elapsed_seconds * self._tick_rate * self._speed
            whole_ticks = int(total)
            self._fractional_ticks = total - whole_ticks
            target = self._requested_tick + whole_ticks
        if whole_ticks == 0:
            return self.snapshot()
        return self._advance_to_tick(target)

    def _advance_to_tick(self, target_tick: int) -> ReplayContext:
        descriptor = self._store.round_descriptor(self._round)
        if target_tick <= descriptor["last_tick"]:
            frame = self._store.frame_at_or_before(self._round, target_tick)
            with self._lock:
                self._requested_tick = target_tick
                self._resolved_tick = frame["tick"]
                self._frame = frame
                if self._round == self._store.round_numbers[-1] and target_tick == descriptor["last_tick"]:
                    self._play_state = "paused"
                    self._fractional_ticks = 0.0
            return self._publish()
        rounds = self._store.round_numbers
        position = rounds.index(self._round)
        if position == len(rounds) - 1:
            frame = self._store.exact_frame(self._round, descriptor["last_tick"])
            with self._lock:
                self._requested_tick = descriptor["last_tick"]
                self._resolved_tick = descriptor["last_tick"]
                self._frame = frame
                self._play_state = "paused"
                self._fractional_ticks = 0.0
            return self._publish()
        next_round = rounds[position + 1]
        next_descriptor = self._store.round_descriptor(next_round)
        if target_tick < next_descriptor["first_tick"]:
            frame = self._store.exact_frame(self._round, descriptor["last_tick"])
            with self._lock:
                self._requested_tick = target_tick
                self._resolved_tick = descriptor["last_tick"]
                self._frame = frame
            return self._publish()
        with self._lock:
            self._round = next_round
            self._selected_scene_id = None
        return self._advance_to_tick(target_tick)

    def step_relevant(self, direction: int) -> ReplayContext:
        if direction not in (-1, 1):
            raise ValueError("direction must be -1 or 1")
        points = self._relevant_points()
        # Keep requested ticks meaningful for scene markers that fall between
        # observed frames; comparing only the resolved tick would revisit the
        # same marker indefinitely.
        current = (self._round, self._requested_tick)
        candidates = [point for point in points if point > current] if direction > 0 else [point for point in points if point < current]
        if not candidates:
            raise KeyError("no relevant event in requested direction")
        round_number, tick = candidates[0] if direction > 0 else candidates[-1]
        return self.seek(round_number, tick)

    def _relevant_points(self) -> list[tuple[int, int]]:
        points: set[tuple[int, int]] = set()
        for round_number in self._store.round_numbers:
            for frame in self._store.load_round(round_number)["frames"]:
                if frame.get("events"):
                    points.add((round_number, frame["tick"]))
        points.update((scene["round_number"], scene["tick"]) for scene in self._scenes.values())
        return sorted(points)
