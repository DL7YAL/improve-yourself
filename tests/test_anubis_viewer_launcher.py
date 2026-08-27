import importlib.util
from pathlib import Path
from types import SimpleNamespace

from improve_yourself.replay_controller import ReplayController
from test_replay_controller import _store


def test_launcher_passes_exact_store_and_selection_to_2d_export(monkeypatch, tmp_path):
    path = Path(__file__).parents[1] / "tools/dev/Run-AnubisViewerDemo.py"
    spec = importlib.util.spec_from_file_location("anubis_launcher_test", path)
    module = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
    store = _store(tmp_path); controller = ReplayController(store)
    selection = SimpleNamespace(context=controller.snapshot(), player=SimpleNamespace(player_id="steam:7", position=SimpleNamespace(), team="CT", weapon="knife"))
    args = SimpleNamespace(replay=Path("ignored.json"), two_d_output=tmp_path / "viewer.html", manifest=tmp_path / "missing.json", round_number=1, tick=10, player="steam:7")
    received = {}
    monkeypatch.setattr(module, "_parse_args", lambda: args)
    monkeypatch.setattr(module, "ReplayStore", lambda _: store)
    monkeypatch.setattr(module, "ReplayController", lambda value: controller if value is store else (_ for _ in ()).throw(AssertionError("second controller")))
    monkeypatch.setattr(module, "select_viewer_demo_state", lambda *a, **k: selection)
    monkeypatch.setattr(module, "write_selected_2d_viewer", lambda actual_store, output, actual_selection: received.update(store=actual_store, selection=actual_selection) or output)
    monkeypatch.setattr(module, "assess_map_asset", lambda *_: SimpleNamespace(availability="missing", reason="test gate"))
    assert module.main() == 0
    assert received == {"store": store, "selection": selection}
