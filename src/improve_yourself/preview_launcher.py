from __future__ import annotations

import argparse
import sys
from threading import Timer
import webbrowser
from pathlib import Path

from improve_yourself.analyzer_server import main as analyzer_main
from improve_yourself.optimizer_input import export_optimizer_input
from improve_yourself.system_check import run_system_check


def _choose_demo() -> Path | None:
    """Select a local CS2 demo without requiring a command-line workflow."""
    try:
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askopenfilename(
            title="Counter-Strike-2-Demo auswählen",
            filetypes=[("CS2 demos", "*.dem *.dem.zst *.dem.bz2"), ("Alle Dateien", "*.*")],
        )
        root.destroy()
    except Exception as error:
        raise RuntimeError(f"Die lokale Demoauswahl konnte nicht geöffnet werden: {error}") from error
    return Path(selected) if selected else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Start Improve Yourself Preview V1 locally")
    parser.add_argument("--demo", type=Path, help="Optional demo to preload; otherwise choose it in the preview workflow.")
    parser.add_argument("--port", type=int, default=8880)
    parser.add_argument("--system-check", action="store_true", help="Run the bundled read-only System Check and Optimizer Input export.")
    parser.add_argument("--data-directory", type=Path, default=Path("Improve Yourself Data"), help="Local output directory for --system-check.")
    args, remaining = parser.parse_known_args()
    if args.system_check:
        args.data_directory.mkdir(parents=True, exist_ok=True)
        system_path = run_system_check(args.data_directory / "system-check.json")
        optimizer_path = export_optimizer_input(system_path, args.data_directory / "optimizer-input.json")
        print(f"System Check: {system_path}")
        print(f"Optimizer Input: {optimizer_path}")
        return 0
    demo = args.demo or _choose_demo()
    if demo is None:
        return 0
    # Let the loopback server bind before asking the default browser to load it.
    Timer(0.75, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}/analyzer.html")).start()
    sys.argv = [sys.argv[0], str(demo), "--port", str(args.port), *remaining]
    return analyzer_main()


if __name__ == "__main__":
    raise SystemExit(main())
