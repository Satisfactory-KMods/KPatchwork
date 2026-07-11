#!/usr/bin/env python3
"""Generate a player-friendly and technically traceable KPatchwork changelog."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

COMMIT = re.compile(r"^(?P<sha>[^\t]+)\t(?P<date>[^\t]+)\t(?P<author>[^\t]+)\t(?P<subject>.*)$")
PREFIX = re.compile(r"^(?P<kind>feat|fix|perf|refactor|docs|chore|ci|build|test)(?:\([^)]*\))?:\s*", re.IGNORECASE)


def git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=True)
    return [line for line in result.stdout.splitlines() if line]


def version(root: Path) -> str:
    plugin = root / "KPatchwork.uplugin"
    try:
        data = json.loads(plugin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "development"
    return str(data.get("VersionName") or data.get("SemVersion") or "development")


def changed_files(root: Path, sha: str) -> list[str]:
    return git(root, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha)


def diff_stats(root: Path, range_spec: str) -> list[tuple[str, str, str]]:
    stats: list[tuple[str, str, str]] = []
    for line in git(root, "diff", "--numstat", range_spec):
        additions, deletions, path = line.split("\t", 2)
        stats.append((path, additions, deletions))
    return stats


def player_area(paths: list[str]) -> str:
    if any(path.startswith("DataForge/") for path in paths):
        return "KDataForge patch content"
    if any(path == "KPatchwork.uplugin" for path in paths):
        return "Mod metadata"
    if any(path.startswith("Config/") for path in paths):
        return "Mod configuration"
    return "Mod infrastructure"


def player_sentence(kind: str, subject: str, area: str) -> str:
    text = subject.strip()
    verbs = {
        "feat": "Added",
        "fix": "Fixed",
        "perf": "Improved",
        "refactor": "Updated",
    }
    prefix = verbs.get(kind, "Updated")
    lowered = text.casefold()
    for leading in ("add ", "adds ", "added ", "fix ", "fixed ", "update ", "updated ", "improve ", "improved "):
        if lowered.startswith(leading):
            text = text[len(leading):]
            break
    return f"{prefix} {text} ({area})."


def parse_commit(line: str) -> tuple[str, str, str, str]:
    match = COMMIT.match(line)
    if not match:
        raise ValueError(f"unexpected git log row: {line!r}")
    return match["sha"], match["date"], match["author"], match["subject"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"))
    args = parser.parse_args()

    base = args.base
    if not base or set(base) == {"0"}:
        base = f"{args.head}~1"
    range_spec = f"{base}..{args.head}"
    raw_commits = git(
        args.root,
        "log",
        "--reverse",
        "--date=short",
        "--format=%h%x09%ad%x09%an%x09%s",
        range_spec,
    )
    stats = diff_stats(args.root, range_spec)

    records: list[tuple[str, str, str, str, list[str], str]] = []
    player_changes: list[str] = []
    pack_author_changes: list[str] = []
    for raw in raw_commits:
        sha, date, author, subject = parse_commit(raw)
        files = changed_files(args.root, sha)
        match = PREFIX.match(subject)
        kind = match["kind"].casefold() if match else "change"
        clean_subject = PREFIX.sub("", subject, count=1).strip()
        area = player_area(files)
        records.append((sha, date, author, subject, files, kind))
        if kind in {"feat", "fix", "perf", "refactor"}:
            sentence = player_sentence(kind, clean_subject, area)
            if any(path.startswith("DataForge/") or path == "KPatchwork.uplugin" for path in files):
                player_changes.append(sentence)
            if any(path.startswith("DataForge/") for path in files):
                pack_author_changes.append(sentence)

    lines = [f"# KPatchwork {version(args.root)}", "", "## Changes for players", ""]
    if player_changes:
        lines.extend(f"- {change}" for change in player_changes)
    else:
        lines.append("- No player-facing changes in this build.")
    lines.extend(["", "## Changes for pack authors", ""])
    if pack_author_changes:
        lines.extend(f"- {change}" for change in pack_author_changes)
    else:
        lines.append("- No pack-facing changes in this build.")
    lines.extend(["", "## Diff summary", ""])
    lines.append(f"Compared range: `{range_spec}`.")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if repository:
        lines.append(f"Compare changes on GitHub: https://github.com/{repository}/compare/{base}...{args.head}")
    lines.append("")
    if stats:
        lines.append("| File | Added | Removed |")
        lines.append("| --- | ---: | ---: |")
        for path, additions, deletions in stats:
            lines.append(f"| `{path}` | {additions} | {deletions} |")
    else:
        lines.append("- No file diff in this range.")
    lines.extend(["", "## Technical commit history", ""])
    if records:
        for sha, date, author, subject, files, _kind in records:
            lines.append(f"### `{sha}` {subject}")
            lines.append(f"Committed by **{author}** on {date}.")
            if files:
                lines.append("Changed files:")
                lines.extend(f"- `{path}`" for path in files)
            else:
                lines.append("Changed files: none recorded.")
            lines.append("")
    else:
        lines.append("- No commits in range.")
    lines.extend([f"Generated from `{range_spec}`.", ""])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"created {args.output} ({len(records)} commit(s), {len(player_changes)} player change(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
