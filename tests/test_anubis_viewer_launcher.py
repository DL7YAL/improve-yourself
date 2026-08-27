import runpy
from pathlib import Path

def test_launcher_passes_existing_store_to_2d_export(monkeypatch, tmp_path):
    path=Path(__file__).parents[1]/'tools/dev/Run-AnubisViewerDemo.py'
    text=path.read_text(encoding='utf-8')
    assert 'write_selected_2d_viewer(store, args.two_d_output, selection)' in text
