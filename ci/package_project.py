#!/usr/bin/env python3
"""Create the distributable KPatchwork ZIP."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("dist/KPatchwork.zip"))
    args = parser.parse_args()

    root = args.root.resolve()
    plugin = root / "KPatchwork.uplugin"
    dataforge = root / "KDataForge"
    if not plugin.is_file():
        raise SystemExit(f"missing plugin descriptor: {plugin}")
    if not dataforge.is_dir():
        raise SystemExit(f"missing DataForge directory: {dataforge}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED) as archive:
        archive.write(plugin, plugin.relative_to(root).as_posix())
        for path in sorted(dataforge.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    print(f"created {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
