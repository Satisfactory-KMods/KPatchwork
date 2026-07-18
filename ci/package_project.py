#!/usr/bin/env python3
"""Create the distributable KPatchwork ZIP."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PLATFORM_TARGETS = ("Windows", "LinuxServer", "WindowsServer")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("dist/KPatchwork.zip"))
    args = parser.parse_args()

    root = args.root.resolve()
    plugin = root / "KPatchwork.uplugin"
    dataforge = root / "DataForge"
    config = root / "Config"
    if not plugin.is_file():
        raise SystemExit(f"missing plugin descriptor: {plugin}")
    if not dataforge.is_dir():
        raise SystemExit(f"missing DataForge directory: {dataforge}")
    if not config.is_dir():
        raise SystemExit(f"missing Config directory: {config}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED) as archive:
        for platform in PLATFORM_TARGETS:
            archive.write(plugin, f"{platform}/{plugin.name}")
            for source_root in (dataforge, config):
                for path in sorted(source_root.rglob("*")):
                    if path.is_symlink():
                        raise SystemExit(f"symlinks are not allowed in release content: {path}")
                    if path.is_file() and path.name != "Alpakit.ini":
                        relative_path = path.relative_to(root).as_posix()
                        archive.write(path, f"{platform}/{relative_path}")
    print(f"created {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
