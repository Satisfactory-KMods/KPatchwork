#!/usr/bin/env python3
"""Decide whether a PR changes only packs owned by its author."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def run_git(*args: str) -> list[str]:
    result = subprocess.run(["git", *args], check=True, text=True, capture_output=True)
    return [line for line in result.stdout.splitlines() if line]


def write_output(key: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"{key}={value}\n")


def load_contributors(revision: str, filename: str) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{revision}:{filename}"],
            check=True,
            text=True,
            capture_output=True,
        )
        data = yaml.safe_load(result.stdout)
    except (subprocess.CalledProcessError, yaml.YAMLError):
        return None

    value = data.get("contributer") if isinstance(data, dict) else None
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list):
        return None
    return [item.strip() for item in values if isinstance(item, str)]


def manifest_for(path: Path, root: Path) -> Path | None:
    current = path.parent
    while True:
        manifest = current / "pack.yml"
        if manifest.is_file():
            return manifest
        if current == root:
            break
        if root not in current.parents:
            break
        current = current.parent
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    root = args.root / "KDataForge"
    changed = run_git("diff", "--name-only", f"{args.base}...{args.head}")
    owned = True
    reasons: list[str] = []
    manifests: set[Path] = set()

    for filename in changed:
        path = Path(filename)
        if not filename.startswith("KDataForge/"):
            owned = False
            reasons.append(f"outside KDataForge: {filename}")
            continue
        absolute = args.root / path
        manifest = manifest_for(absolute, root)
        if manifest is None:
            owned = False
            reasons.append(f"no owning pack.yml: {filename}")
            continue
        manifests.add(manifest)

    for manifest in manifests:
        manifest_filename = manifest.relative_to(args.root).as_posix()
        base_contributors = load_contributors(args.base, manifest_filename)
        head_contributors = load_contributors(args.head, manifest_filename)
        if base_contributors != head_contributors:
            owned = False
            reasons.append(f"{manifest}: contributer field changed")

        try:
            data: dict[str, Any] = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            owned = False
            reasons.append(f"cannot read {manifest}: {exc}")
            continue
        contributor = data.get("contributer") if isinstance(data, dict) else None
        contributors = [contributor] if isinstance(contributor, str) else contributor
        normalized = {
            item.casefold()
            for item in contributors or []
            if isinstance(item, str)
        }
        if args.author.casefold() not in normalized:
            owned = False
            reasons.append(f"{manifest}: contributer list does not include {args.author}")

    eligible = "true" if owned and bool(manifests) else "false"
    write_output("eligible", eligible)
    write_output("reason", "; ".join(reasons) or "all changed packs belong to PR author")
    print(f"auto_merge_eligible={eligible}")
    print("reason=" + ("; ".join(reasons) or "all changed packs belong to PR author"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
