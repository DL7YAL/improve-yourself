from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


root = Path(SPEC).resolve().parent.parent
assets = root / "src" / "improve_yourself" / "assets"
hiddenimports = collect_submodules("awpy")

a = Analysis(
    [str(root / "packaging" / "experimental_entry.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[
        (str(assets / "improve-yourself-wordmark-v3.png"), "improve_yourself/assets"),
        (str(assets / "improve-yourself-icon-v3.png"), "improve_yourself/assets"),
        (str(assets / "fonts"), "improve_yourself/assets/fonts"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Improve Yourself Experimental",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(assets / "improve-yourself-icon-v3.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="Improve Yourself Experimental",
)
