from __future__ import annotations

import argparse
from pathlib import Path

from improve_yourself.desktop import run_desktop_app
from improve_yourself.optimizer_input import export_optimizer_input
from improve_yourself.system_check import run_system_check


def main() -> int:
    parser = argparse.ArgumentParser(description="Start Improve Yourself Preview V1 locally")
    parser.add_argument("--demo", type=Path, help="Optional demo to preload; otherwise choose it in the preview workflow.")
    parser.add_argument("--port", type=int, default=0, help="Optional loopback port; standardmäßig wird ein freier lokaler Port gewählt.")
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
    if remaining:
        parser.error(f"unbekannte Argumente: {' '.join(remaining)}")
    return run_desktop_app(Path("Improve Yourself Data"), port=args.port, initial_demo=args.demo)


if __name__ == "__main__":
    raise SystemExit(main())
