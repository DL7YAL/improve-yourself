from __future__ import annotations

import argparse
from pathlib import Path

from .service import analyze


def main() -> int:
    parser = argparse.ArgumentParser(description="Improve Yourself CS2 Demo Analyzer")
    parser.add_argument("demo", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--max-mib", type=int, default=2048)
    args = parser.parse_args()
    try:
        result = analyze(args.demo, args.output, args.max_mib * 1024 * 1024)
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))
    print(f"Analyse gespeichert: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
