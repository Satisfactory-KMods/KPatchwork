#!/usr/bin/env python3
"""Generate a concise Markdown changelog from a Git commit range."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=True)
    return [line for line in result.stdout.splitlines() if line]


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
    commits = git(args.root, "log", "--reverse", "--date=short", "--format=%h%x09%ad%x09%an%x09%s", range_spec)
    changed = git(args.root, "diff", "--name-only", range_spec)

    lines = ["# KPatchwork Changelog", "", f"Generated from `{range_spec}`.", ""]
    lines.append("## Commits")
    if commits:
        for commit in commits:
            short_sha, date, author, subject = commit.split("\t", 3)
            lines.append(f"- `{short_sha}` {subject} — {author} ({date})")
    else:
        lines.append("- No commits in range.")

    lines.extend(["", "## Changed files"])
    if changed:
        lines.extend(f"- `{path}`" for path in changed)
    else:
        lines.append("- No changed files.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"created {args.output} ({len(commits)} commit(s), {len(changed)} changed file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
