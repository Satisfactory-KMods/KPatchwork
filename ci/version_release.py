#!/usr/bin/env python3
"""Set release version to <year>.<quarter>.<CI build number>."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin", type=Path, default=Path("KPatchwork.uplugin"))
    parser.add_argument("--build-number", required=True, type=int)
    args = parser.parse_args()

    if args.build_number < 1:
        raise SystemExit("build number must be positive")
    today = date.today()
    year = today.year
    quarter = ((today.month - 1) // 3) + 1
    version = f"{year}.{quarter}.{args.build_number}"

    data = json.loads(args.plugin.read_text(encoding="utf-8"))
    data["Version"] = year
    data["VersionName"] = version
    data["SemVersion"] = version
    args.plugin.write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
    print(f"version={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
