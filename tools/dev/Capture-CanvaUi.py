from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageGrab

from improve_yourself.analyzer_shell import AnalyzerShellApp, AnalyzerShellController


PAGES = (
    ("Dashboard", "dashboard"),
    ("Analyzer", "analyzer"),
    ("Tactical Replay", "tactical-replay"),
    ("My Improvement", "my-improvement"),
    ("System Check / Optimizer", "optimizer"),
    ("Benchmark", "benchmark"),
    ("Reports", "reports"),
    ("Settings", "settings"),
)
VIEWPORTS = ((1536, 1024), (1080, 720))


class BitmapInfoHeader(ctypes.Structure):
    _fields_ = (
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    )


class BitmapInfo(ctypes.Structure):
    _fields_ = (("bmiHeader", BitmapInfoHeader), ("bmiColors", wintypes.DWORD * 3))


def redraw_window(app: AnalyzerShellApp) -> None:
    """Force Windows to repaint every Tk child before screen capture."""

    rdw_invalidate = 0x0001
    rdw_erase = 0x0004
    rdw_allchildren = 0x0080
    rdw_updatenow = 0x0100
    ctypes.windll.user32.RedrawWindow(  # type: ignore[attr-defined]
        app.root.winfo_id(), None, None,
        rdw_invalidate | rdw_erase | rdw_allchildren | rdw_updatenow,
    )
    ctypes.windll.dwmapi.DwmFlush()  # type: ignore[attr-defined]


def grab_window(app: AnalyzerShellApp) -> Image.Image:
    """Render the exact Tk client through Win32 instead of sampling the desktop."""

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    gdi32 = ctypes.windll.gdi32  # type: ignore[attr-defined]
    user32.GetDC.argtypes = (wintypes.HWND,)
    user32.GetDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = (wintypes.HWND, wintypes.HDC)
    gdi32.CreateCompatibleDC.argtypes = (wintypes.HDC,)
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleBitmap.argtypes = (wintypes.HDC, ctypes.c_int, ctypes.c_int)
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.SelectObject.argtypes = (wintypes.HDC, wintypes.HGDIOBJ)
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.GetDIBits.argtypes = (
        wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
        ctypes.c_void_p, ctypes.POINTER(BitmapInfo), wintypes.UINT,
    )
    gdi32.DeleteObject.argtypes = (wintypes.HGDIOBJ,)
    gdi32.DeleteDC.argtypes = (wintypes.HDC,)
    user32.PrintWindow.argtypes = (wintypes.HWND, wintypes.HDC, wintypes.UINT)
    hwnd = app.root.winfo_id()
    width = app.root.winfo_width()
    height = app.root.winfo_height()
    source_dc = user32.GetDC(hwnd)
    memory_dc = gdi32.CreateCompatibleDC(source_dc)
    bitmap = gdi32.CreateCompatibleBitmap(source_dc, width, height)
    previous = gdi32.SelectObject(memory_dc, bitmap)
    try:
        # PW_CLIENTONLY | PW_RENDERFULLCONTENT asks Tk/Windows to paint the
        # complete client, including child canvases that have not changed.
        if not user32.PrintWindow(hwnd, memory_dc, 0x00000003):
            raise OSError("Windows could not render the Tk client")
        info = BitmapInfo()
        info.bmiHeader = BitmapInfoHeader(
            ctypes.sizeof(BitmapInfoHeader), width, -height, 1, 32, 0,
            width * height * 4, 0, 0, 0, 0,
        )
        pixels = ctypes.create_string_buffer(width * height * 4)
        if gdi32.GetDIBits(memory_dc, bitmap, 0, height, pixels, ctypes.byref(info), 0) != height:
            raise OSError("Windows could not copy the rendered Tk client")
        return Image.frombuffer("RGB", (width, height), pixels, "raw", "BGRX", 0, 1).copy()
    finally:
        gdi32.SelectObject(memory_dc, previous)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, source_dc)


def evidence_score(image: Image.Image) -> int:
    """Prefer the most completely painted frame from repeated Win32 renders."""

    sample = image.resize((max(1, image.width // 8), max(1, image.height // 8)))
    histogram = sample.histogram()
    return sum((index % 256) * count for index, count in enumerate(histogram))


def grab_visible_client(app: AnalyzerShellApp) -> Image.Image:
    """Capture the topmost client pixels after DWM has presented the frame."""

    x = app.root.winfo_rootx()
    y = app.root.winfo_rooty()
    return ImageGrab.grab(
        bbox=(x, y, x + app.root.winfo_width(), y + app.root.winfo_height()),
        all_screens=True,
    )


def expose_client(app: AnalyzerShellApp) -> None:
    """Cover and uncover the client once so DWM invalidates every pixel."""

    cover = app.tk.Toplevel(app.root)
    cover.overrideredirect(True)
    cover.geometry(
        f"{app.root.winfo_width()}x{app.root.winfo_height()}+"
        f"{app.root.winfo_rootx()}+{app.root.winfo_rooty()}"
    )
    cover.configure(background="#010E18")
    cover.attributes("-topmost", True)
    cover.lift()
    cover.update_idletasks()
    cover.update()
    time.sleep(0.04)
    cover.destroy()
    app.root.attributes("-topmost", True)
    app.root.lift()
    app.root.update_idletasks()
    app.root.update()
    ctypes.windll.dwmapi.DwmFlush()  # type: ignore[attr-defined]


def capture_one(output: Path, page: str, slug: str, width: int, height: int) -> Path:
    """Capture one route in one Tk interpreter for deterministic painting."""

    with tempfile.TemporaryDirectory(prefix="iy-canva-ui-capture-") as result_root:
        app = AnalyzerShellApp(AnalyzerShellController(Path(result_root)))
        try:
            # Tk geometry describes the client viewport. PrintWindow's
            # PW_CLIENTONLY capture below excludes the native title bar.
            app.root.geometry(f"{width}x{height}+0+0")
            app.root.attributes("-topmost", True)
            app.root.lift()
            app.root.update_idletasks()
            app.root.update()
            app._show_page(page, record_history=False)
            app.root.update_idletasks()
            app.root.update()
            # The page hosts are built while hidden. A one-pixel width cycle
            # guarantees that responsive handlers receive mapped geometry.
            app.root.geometry(f"{width + 1}x{height}+0+0")
            app.root.update_idletasks()
            app.root.update()
            app.root.geometry(f"{width}x{height}+0+0")
            app.root.update_idletasks()
            app.root.update()
            time.sleep(0.12)
            app.root.update_idletasks()
            app.root.update()
            expose_client(app)
            best_score = -1
            screenshot: Image.Image | None = None
            for attempt in range(6):
                # Exercise a mapped resize to invalidate child canvases, then
                # always restore the exact contractual viewport before the
                # candidate is captured.  A previous version resized after
                # capture and could retain a width+1 best frame.
                app.root.geometry(f"{width + 1}x{height}+0+0")
                app.root.update_idletasks()
                app.root.update()
                app.root.geometry(f"{width}x{height}+0+0")
                app._refresh_shell_chrome()
                app.root.update_idletasks()
                app.root.update()
                redraw_window(app)
                app.root.update_idletasks()
                app.root.update()
                candidate = grab_visible_client(app)
                score = evidence_score(candidate)
                if score > best_score:
                    best_score = score
                    screenshot = candidate
                else:
                    candidate.close()
                time.sleep(0.04)
            if screenshot is None:
                raise OSError("No runtime screenshot was rendered")
            target = output / f"{slug}-{width}x{height}.png"
            screenshot.save(target, format="PNG", optimize=True)
            screenshot.close()
            return target
        finally:
            if app.root.winfo_exists():
                app.root.attributes("-topmost", False)
                app.root.withdraw()
                app.root.update_idletasks()
                app.root.update()
                ctypes.windll.dwmapi.DwmFlush()  # type: ignore[attr-defined]
            app._close()


def capture(output: Path) -> tuple[Path, ...]:
    output.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    script = Path(__file__).resolve()
    for width, height in VIEWPORTS:
        for page, slug in PAGES:
            subprocess.run(
                (
                    sys.executable, "-B", str(script), "--output", str(output),
                    "--page", page, "--slug", slug,
                    "--width", str(width), "--height", str(height),
                ),
                check=True,
            )
            # Give DWM time to retire the previous topmost Tk surface before
            # the next isolated evidence process maps at the same coordinates.
            time.sleep(0.25)
            created.append(output / f"{slug}-{width}x{height}.png")
    return tuple(created)


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture the Canva-R25 local shell at both review viewports")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--page")
    parser.add_argument("--slug")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    args = parser.parse_args()
    if args.page is not None:
        if args.slug is None or args.width is None or args.height is None:
            parser.error("--page requires --slug, --width and --height")
        print(capture_one(args.output.resolve(), args.page, args.slug, args.width, args.height))
        return 0
    for path in capture(args.output.resolve()):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
