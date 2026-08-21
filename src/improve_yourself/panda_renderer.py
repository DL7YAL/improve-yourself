from __future__ import annotations

from pathlib import Path

from .map_assets import assess_map_asset
from .renderer import ReplayRenderer, ViewMode, first_person_camera, third_person_camera
from .replay_contract import ReplayFrame
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
        self._disposed = False

    def _require_live(self) -> None:
        if self._disposed:
            raise RuntimeError("renderer is disposed")

    def load_map(self, manifest_path: Path) -> None:
        self._require_live()
        assessment = assess_map_asset(manifest_path, "de_anubis")
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
        self._visibility = TriVisibilityMesh.from_verified_manifest(manifest_path, "de_anubis")

    def set_frame(self, frame: ReplayFrame) -> None:
        self._require_live()
        self._frame = frame
        self._camera_pose = None

    def set_camera_player(self, player_id: str) -> None:
        self._require_live()
        self._player_id = player_id
        self._camera_pose = None

    def set_view_mode(self, mode: ViewMode) -> None:
        self._require_live()
        if mode not in ("first_person", "third_person"):
            raise ValueError(f"unsupported V1 view mode: {mode}")
        self._view_mode = mode
        self._camera_pose = None

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
            self._base.destroy()
            self._disposed = True
