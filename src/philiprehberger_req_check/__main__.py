"""CLI entry point: python -m philiprehberger_req_check [path]"""

from __future__ import annotations

import sys
from pathlib import Path

from philiprehberger_req_check import check


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    unused = check(path)

    if unused:
        print("Unused packages:")
        for pkg in sorted(unused):
            print(f"  - {pkg}")
        sys.exit(1)
    else:
        print("No unused packages found.")


if __name__ == "__main__":
    main()
