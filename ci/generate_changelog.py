#!/usr/bin/env python3
"""Generate a player-friendly and technically traceable KPatchwork changelog."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import yaml

COMMIT = re.compile(r"^(?P<sha>[^\t]+)\t(?P<date>[^\t]+)\t(?P<author>[^\t]+)\t(?P<subject>.*)$")
PREFIX = re.compile(r"^(?P<kind>feat|fix|perf|refactor|docs|chore|ci|build|test)(?:\([^)]*\))?:\s*", re.IGNORECASE)
CHANGELOG_HEADING = re.compile(r"^[ \t]{0,3}##[ \t]+changelog[ \t]*#*[ \t]*$", re.IGNORECASE)
SECTION_HEADING = re.compile(r"^[ \t]{0,3}#{1,2}(?:[ \t]+|$)")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def git(root: Path, *args: str) -> list[str]:
    return [line for line in git_output(root, *args).splitlines() if line]


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=True)
    return result.stdout


def version(root: Path) -> str:
    plugin = root / "KPatchwork.uplugin"
    try:
        data = json.loads(plugin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "development"
    return str(data.get("VersionName") or data.get("SemVersion") or "development")


def changed_files(root: Path, sha: str) -> list[str]:
    return git(root, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha)


def added_pack_manifests(root: Path, base: str, head: str) -> list[str]:
    paths = git(root, "diff", "--diff-filter=A", "--name-only", base, head)
    return sorted(path for path in paths if path.startswith("DataForge/") and path.endswith("/pack.yml"))


def updated_pack_manifests(root: Path, base: str, head: str, added_manifests: list[str]) -> list[str]:
    manifests = [
        path
        for path in git(root, "ls-tree", "-r", "--name-only", head, "--", "DataForge")
        if path.endswith("/pack.yml")
    ]
    changed_paths = git(root, "diff", "--name-only", base, head, "--", "DataForge")
    added = set(added_manifests)
    updated: set[str] = set()
    for changed_path in changed_paths:
        owners = [
            manifest
            for manifest in manifests
            if changed_path == manifest or changed_path.startswith(f"{Path(manifest).parent.as_posix()}/")
        ]
        if owners:
            owner = max(owners, key=len)
            if owner not in added:
                updated.add(owner)
    return sorted(updated)


def pack_at_revision(root: Path, revision: str, manifest: str) -> tuple[str, str, list[str]]:
    data = yaml.safe_load(git_output(root, "show", f"{revision}:{manifest}"))
    mapping = data if isinstance(data, dict) else {}
    pack_ref = str(mapping.get("ref") or Path(manifest).parent.name).strip()
    pack_name = str(mapping.get("name") or pack_ref).strip()
    raw_contributors = mapping.get("contributer")
    contributors = [raw_contributors] if isinstance(raw_contributors, str) else raw_contributors
    normalized = [str(contributor).strip() for contributor in contributors or [] if str(contributor).strip()]
    return pack_name, pack_ref, normalized


def format_contributors(contributors: list[str]) -> str:
    names = [f"@{contributor.lstrip('@')}" for contributor in contributors]
    if not names:
        return "an unknown contributor"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


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


def extract_changelog_section(body: str) -> str | None:
    lines = body.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    for index, line in enumerate(lines):
        if not CHANGELOG_HEADING.match(line):
            continue
        section: list[str] = []
        for candidate in lines[index + 1:]:
            if SECTION_HEADING.match(candidate):
                break
            section.append(candidate)
        visible = HTML_COMMENT.sub("", "\n".join(section)).strip()
        return visible or None
    return None


def pull_request_changelogs(path: Path | None) -> list[tuple[int, str, str, str, str]]:
    if path is None:
        return []
    try:
        raw_records = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"unable to read pull request changelogs from {path}: {error}") from error
    if not isinstance(raw_records, list):
        raise SystemExit(f"pull request changelog input must contain a JSON array: {path}")

    changelogs: list[tuple[int, str, str, str, str]] = []
    for record in raw_records:
        if not isinstance(record, dict):
            continue
        body = str(record.get("body") or "")
        changelog = extract_changelog_section(body)
        if not changelog:
            continue
        try:
            number = int(record["number"])
        except (KeyError, TypeError, ValueError):
            continue
        title = str(record.get("title") or f"Pull request #{number}").strip()
        author = str(record.get("author") or "unknown").strip().lstrip("@")
        url = str(record.get("url") or "").strip()
        changelogs.append((number, title, author, url, changelog))
    return sorted(changelogs, key=lambda entry: entry[0])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--pull-requests", type=Path)
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
    added_manifests = added_pack_manifests(args.root, base, args.head)
    new_packs = [
        pack_at_revision(args.root, args.head, path)
        for path in added_manifests
    ]
    updated_packs = [
        pack_at_revision(args.root, args.head, path)
        for path in updated_pack_manifests(args.root, base, args.head, added_manifests)
    ]
    authored_changelogs = pull_request_changelogs(args.pull_requests)
    player_changes: list[str] = []
    pack_author_changes: list[str] = []
    for raw in raw_commits:
        sha, date, author, subject = parse_commit(raw)
        files = changed_files(args.root, sha)
        match = PREFIX.match(subject)
        kind = match["kind"].casefold() if match else "change"
        clean_subject = PREFIX.sub("", subject, count=1).strip()
        area = player_area(files)
        changes_packaged_content = any(
            path.startswith(("Config/", "DataForge/")) or path == "KPatchwork.uplugin"
            for path in files
        )
        if changes_packaged_content:
            sentence = player_sentence(kind, clean_subject, area)
            player_changes.append(sentence)
            if any(path.startswith("DataForge/") for path in files):
                pack_author_changes.append(sentence)

    lines = [
        "Automated release changelog generated from the included commits.",
        "",
        f"# KPatchwork {version(args.root)}",
        "",
        "## New packs",
        "",
    ]
    if new_packs:
        for pack_name, pack_ref, contributors in new_packs:
            lines.append(f"- Added **{pack_name}** (`{pack_ref}`) by {format_contributors(contributors)}.")
    else:
        lines.append("- No new packs in this build.")
    lines.extend(["", "## Updated packs", ""])
    if updated_packs:
        for pack_name, pack_ref, contributors in updated_packs:
            lines.append(f"- Updated **{pack_name}** (`{pack_ref}`), maintained by {format_contributors(contributors)}.")
    else:
        lines.append("- No existing packs were updated in this build.")
    lines.extend(["", "## Pack author changelogs", ""])
    if authored_changelogs:
        for number, title, author, url, changelog in authored_changelogs:
            pull_request = f"[#{number}]({url})" if url else f"#{number}"
            lines.extend([f"### {title} ({pull_request}) by @{author}", "", changelog, ""])
        if lines[-1] == "":
            lines.pop()
    else:
        lines.append("- No pack author changelogs were provided in this build.")
    lines.extend([
        "",
        "## Changes for players",
        "",
    ])
    if player_changes:
        lines.extend(f"- {change}" for change in player_changes)
    elif new_packs:
        lines.append("- New pack additions are listed above.")
    else:
        lines.append("- No player-facing changes in this build.")
    lines.extend(["", "## Changes for pack authors", ""])
    if pack_author_changes:
        lines.extend(f"- {change}" for change in pack_author_changes)
    elif new_packs:
        lines.append("- New pack additions and their contributors are listed above.")
    else:
        lines.append("- No pack-facing changes in this build.")
    lines.extend(["", f"Generated from `{range_spec}`.", ""])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"created {args.output} ({len(raw_commits)} commit(s), {len(player_changes)} player change(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
