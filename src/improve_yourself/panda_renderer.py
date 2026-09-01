from __future__ import annotations

from pathlib import Path

from .map_assets import assess_map_asset
from .owned_tactical_representation import (
    OwnedTacticalRepresentation,
    load_owned_tactical_representation,
    player_marker_instructions,
)
from .owned_scene_presentation import OwnedScenePresentation, load_owned_scene_presentation
from .renderer import ReplayRenderer, ViewMode, first_person_camera, third_person_camera
from .replay_contract import ReplayFrame
from .sightlines import SightlineSegment
from .visibility_mesh import TriVisibilityMesh


class PandaReplayRenderer:
    """Disposable Slice-D backend proving the renderer boundary and native hosting."""

    def __init__(self, parent_window_handle: int) -> None:
        try:
            from direct.showbase.ShowBase import ShowBase
            from panda3d.core import NativeWindowHandle, WindowProperties, loadPrcFileData
        except ImportError as error:
            raise RuntimeError("Panda3D spike dependencies are not installed") from error
        loadPrcFileData("", "window-type none\naudio-library-name null\nframebuffer-multisample 1\nmultisamples 4")
        self._base = ShowBase(windowType="none")
        properties = WindowProperties()
        properties.setParentWindow(NativeWindowHandle.makeInt(parent_window_handle))
        properties.setSize(960, 540)
        if not self._base.openDefaultWindow(props=properties):
            self._base.destroy()
            raise RuntimeError("Panda3D could not open the embedded native viewport")
        self._base.setBackgroundColor(0.035, 0.045, 0.06, 1.0)
        self._frame: ReplayFrame | None = None
        self._player_id: str | None = None
        self._view_mode: ViewMode = "first_person"
        self._map = None
        self._visibility = None
        self._camera_pose = None
        self._sightline_node = None
        self._owned_representation: OwnedTacticalRepresentation | None = None
        self._owned_marker_node = None
        self._owned_scene_presentation: OwnedScenePresentation | None = None
        self._disposed = False

    def _require_live(self) -> None:
        if self._disposed:
            raise RuntimeError("renderer is disposed")

    def load_map(self, manifest_path: Path, replay_map_id: str = "de_anubis") -> None:
        self._require_live()
        assessment = assess_map_asset(manifest_path, replay_map_id)
        if assessment.availability != "available" or assessment.manifest is None:
            raise RuntimeError(f"map asset unavailable: {assessment.availability}: {assessment.reason}")
        descriptor = assessment.manifest["render_mesh"]
        model_path = manifest_path.resolve().parent / descriptor["path"]
        from panda3d.core import Filename

        model = self._base.loader.loadModel(Filename.fromOsSpecific(str(model_path)), noCache=True)
        if model.isEmpty():
            raise RuntimeError("Panda3D did not load the verified render mesh")
        model.reparentTo(self._base.render)
        model.setColor(0.30, 0.70, 0.86, 1.0)
        model.setRenderModeWireframe()
        model.setTwoSided(True)
        self._base.camLens.setNearFar(1.0, 20000.0)
        self._map = model
        self._visibility = TriVisibilityMesh.from_verified_manifest(manifest_path, replay_map_id)

    def load_owned_tactical_representation(self, descriptor_path: Path, replay_map_id: str = "de_anubis") -> None:
        """Load only a strict own procedural presentation descriptor.

        This is intentionally a Panda-specific, presentation-only extension.
        It does not change the backend-neutral replay renderer contract, map
        gate, canonical frame, camera calculation, or visibility geometry.
        """
        self._require_live()
        self._owned_representation = load_owned_tactical_representation(descriptor_path, replay_map_id)
        self._update_owned_markers()

    def load_owned_scene_presentation(self, descriptor_path: Path, replay_map_id: str = "de_anubis") -> None:
        """Load visual-readiness status without changing map or replay truth."""
        self._require_live()
        self._owned_scene_presentation = load_owned_scene_presentation(descriptor_path, replay_map_id)

    @property
    def owned_presentation_status(self) -> dict[str, str] | None:
        """Expose reserved presentation states without creating progression truth."""
        if self._owned_representation is None:
            return None
        return {
            "badge_anchor": self._owned_representation.badge_anchor_state,
            "outbox": self._owned_representation.outbox_state,
            "discovery": self._owned_representation.discovery_state,
        }

    @property
    def owned_scene_status(self) -> dict[str, str] | None:
        """Expose visual readiness only; never expose it as map availability."""
        if self._owned_scene_presentation is None:
            return None
        scene = self._owned_scene_presentation
        return {
            "visual_scene": scene.output_state,
            "neutral_spatial_reference": scene.neutral_spatial_reference_state,
            "badge": scene.badge_state,
            "outbox": scene.outbox_state,
            "discovery": scene.discovery_state,
        }

    def set_frame(self, frame: ReplayFrame) -> None:
        self._require_live()
        self._frame = frame
        self._camera_pose = None
        self._update_owned_markers()

    def set_camera_player(self, player_id: str) -> None:
        self._require_live()
        self._player_id = player_id
        self._camera_pose = None
        self._update_owned_markers()

    def set_view_mode(self, mode: ViewMode) -> None:
        self._require_live()
        if mode not in ("first_person", "third_person"):
            raise ValueError(f"unsupported V1 view mode: {mode}")
        self._view_mode = mode
        self._camera_pose = None
        self._update_owned_markers()

    def _clear_owned_markers(self) -> None:
        if self._owned_marker_node is not None:
            self._owned_marker_node.removeNode()
            self._owned_marker_node = None

    def _update_owned_markers(self) -> None:
        """Render own procedural markers from canonical frame values only."""
        self._clear_owned_markers()
        if self._owned_representation is None or self._frame is None:
            return
        from panda3d.core import LineSegs

        root = self._base.render.attachNewNode("owned-improve-procedural-markers")
        for marker in player_marker_instructions(
            self._owned_representation,
            self._frame,
            selected_player_id=self._player_id,
            view_mode=self._view_mode,
        ):
            x, y, z = marker.position.x, marker.position.y, marker.position.z
            lines = LineSegs(f"owned-marker-{marker.player_id}")
            lines.setColor(*marker.color)
            lines.setThickness(3.0)
            # An own vertical diamond/cross: position is canonical; geometry is not map truth.
            lines.moveTo(x - 14.0, y, z + 32.0); lines.drawTo(x, y, z + 52.0)
            lines.drawTo(x + 14.0, y, z + 32.0); lines.drawTo(x, y, z + 12.0)
            lines.drawTo(x - 14.0, y, z + 32.0)
            lines.moveTo(x, y - 14.0, z + 32.0); lines.drawTo(x, y + 14.0, z + 32.0)
            if marker.forward_xy is not None:
                dx, dy = marker.forward_xy
                lines.moveTo(x, y, z + 32.0); lines.drawTo(x + dx * 30.0, y + dy * 30.0, z + 32.0)
            marker_node = root.attachNewNode(lines.create())
            # The empty child is the future badge anchor, never a badge/reward itself.
            badge_anchor = marker_node.attachNewNode("future-badge-anchor-not-available")
            badge_anchor.setPos(x, y, z + 72.0)
            badge_anchor.setTag("presentation_state", marker.badge_anchor_state)
        self._owned_marker_node = root

    def set_sightlines(self, sightlines: tuple[SightlineSegment, ...]) -> None:
        self._require_live()
        if self._sightline_node is not None:
            self._sightline_node.removeNode()
            self._sightline_node = None
        if not sightlines:
            return
        from panda3d.core import LineSegs

        lines = LineSegs("canonical-sightlines")
        lines.setThickness(3.0)
        for sightline in sightlines:
            lines.setColor(*sightline.color)
            lines.moveTo(sightline.start.x, sightline.start.y, sightline.start.z)
            lines.drawTo(sightline.end.x, sightline.end.y, sightline.end.z)
        self._sightline_node = self._base.render.attachNewNode(lines.create())

    def render(self) -> None:
        self._require_live()
        if self._map is None or self._frame is None or self._player_id is None:
            raise RuntimeError("map, canonical frame and camera player are required before render")
        if self._camera_pose is None:
            self._camera_pose = (
                first_person_camera(self._frame, self._player_id)
                if self._view_mode == "first_person"
                else third_person_camera(
                    self._frame, self._player_id, visibility_geometry=self._visibility
                )
            )
        pose = self._camera_pose
        camera = self._base.camera
        camera.setPos(pose.origin.x, pose.origin.y, pose.origin.z)
        camera.lookAt(pose.target.x, pose.target.y, pose.target.z)
        self._base.taskMgr.step()

    def resize(self, width: int, height: int) -> None:
        self._require_live()
        if width <= 0 or height <= 0:
            return
        from panda3d.core import WindowProperties

        properties = WindowProperties()
        properties.setSize(width, height)
        self._base.win.requestProperties(properties)

    def dispose(self) -> None:
        if not self._disposed:
            self._clear_owned_markers()
            self._base.destroy()
            self._disposed = True
