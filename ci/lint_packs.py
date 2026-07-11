#!/usr/bin/env python3
"""Validate every KDataForge pack and YAML document."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_MANIFEST_FIELDS = ("ref", "name", "version", "contributer")


def fail(message: str) -> None:
    raise ValueError(message)


def require_string(data: dict[str, Any], field: str, path: Path) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(f"{path}: {field} must be a non-empty string")
    return value.strip()


def find_pack_root(path: Path, root: Path) -> Path | None:
    current = path.parent
    while True:
        manifest = current / "pack.yml"
        if manifest.is_file():
            return current
        if current == root:
            break
        if root not in current.parents:
            break
        current = current.parent
    return None


def lint(root: Path) -> int:
    if not root.is_dir():
        fail(f"KDataForge root does not exist: {root}")

    manifests = sorted(root.rglob("pack.yml"))
    if not manifests:
        fail(f"no pack.yml found below {root}")

    refs: dict[str, Path] = {}
    document_count = 0
    for manifest in manifests:
        relative = manifest.relative_to(root)
        if len(relative.parts) < 3:
            fail(f"{manifest}: expected a nested KDataForge/<group>/<pack>/pack.yml layout")
        pack_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        if not isinstance(pack_data, dict):
            fail(f"{manifest}: manifest must be a YAML mapping")
        for field in REQUIRED_MANIFEST_FIELDS:
            require_string(pack_data, field, manifest)
        ref = pack_data["ref"].strip().casefold()
        if ref in refs:
            fail(f"duplicate pack ref {pack_data['ref']!r}: {refs[ref]} and {manifest}")
        refs[ref] = manifest

    for document in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml")):
        if document.name == "pack.yml":
            continue
        if find_pack_root(document, root) is None:
            fail(f"{document}: YAML document is not inside a pack with pack.yml")
        try:
            documents = list(yaml.safe_load_all(document.read_text(encoding="utf-8")))
        except yaml.YAMLError as exc:
            fail(f"{document}: invalid YAML: {exc}")
        if not documents or all(item is None for item in documents):
            fail(f"{document}: empty YAML document")
        document_count += len([item for item in documents if item is not None])

    print(f"lint passed: {len(manifests)} pack(s), {document_count} YAML document(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("KDataForge"))
    args = parser.parse_args()
    try:
        return lint(args.root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"lint failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
