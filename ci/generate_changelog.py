#!/usr/bin/env python3
"""Generate a changelog for Patchwork: Cross-Mod Compatibility Packs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

COMMIT = re.compile(r"^(?P<sha>[^\t]+)\t(?P<date>[^\t]+)\t(?P<author>[^\t]+)\t(?P<subject>.*)$")
PREFIX = re.compile(r"^(?P<kind>feat|fix|perf|refactor|docs|chore|ci|build|test)(?:\([^)]*\))?:\s*", re.IGNORECASE)
CHANGELOG_HEADING = re.compile(r"^[ \t]{0,3}##[ \t]+changelog[ \t]*#*[ \t]*$", re.IGNORECASE)
SECTION_HEADING = re.compile(r"^[ \t]{0,3}#{1,2}(?:[ \t]+|$)")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class PullRequestChangelog:
    number: int
    title: str
    author: str
    url: str
    text: str
    commits: frozenset[str]


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


def release_sentence(kind: str, subject: str) -> str:
    text = subject.strip()
    actions = {
        "add": "Added", "adds": "Added", "fix": "Fixed", "fixes": "Fixed",
        "update": "Updated", "updates": "Updated", "improve": "Improved",
        "remove": "Removed", "rename": "Renamed", "restore": "Restored",
        "clean": "Cleaned", "correct": "Corrected", "make": "Made", "create": "Created",
        "allow": "Allowed", "enable": "Enabled", "disable": "Disabled",
        "prevent": "Prevented", "handle": "Handled", "use": "Used",
    }
    first, separator, rest = text.partition(" ")
    if first.casefold() in actions and separator:
        text = f"{actions[first.casefold()]} {rest}"
    elif first.casefold() not in {action.casefold() for action in actions.values()}:
        prefix = {"feat": "Added", "fix": "Fixed", "perf": "Improved"}.get(kind)
        if prefix:
            text = f"{prefix} {text}"
    text = text[:1].upper() + text[1:]
    return text if text.endswith((".", "!", "?")) else f"{text}."


def note_key(text: str) -> str:
    return " ".join(text.strip().lstrip("-* ").rstrip(".!?").casefold().split())


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


def pull_request_changelogs(path: Path | None) -> list[PullRequestChangelog]:
    if path is None:
        return []
    try:
        raw_records = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"unable to read pull request changelogs from {path}: {error}") from error
    if not isinstance(raw_records, list):
        raise SystemExit(f"pull request changelog input must contain a JSON array: {path}")

    changelogs: list[PullRequestChangelog] = []
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
        raw_commits = record.get("commits")
        commits = (
            frozenset(sha for sha in raw_commits if isinstance(sha, str))
            if isinstance(raw_commits, list) else frozenset()
        )
        changelogs.append(PullRequestChangelog(number, title, author, url, changelog, commits))
    return sorted(changelogs, key=lambda entry: entry.number)


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
        "--format=%H%x09%ad%x09%an%x09%s",
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
    covered_commits = {sha for entry in authored_changelogs for sha in entry.commits}
    seen_notes = {note_key(line) for entry in authored_changelogs for line in entry.text.splitlines() if line.strip()}
    player_changes: list[str] = []
    pack_author_changes: list[str] = []
    for raw in raw_commits:
        sha, _date, _author, subject = parse_commit(raw)
        if sha in covered_commits:
            continue
        files = changed_files(args.root, sha)
        match = PREFIX.match(subject)
        kind = match["kind"].casefold() if match else "change"
        clean_subject = PREFIX.sub("", subject, count=1).strip()
        changes_packaged_content = any(
            path.startswith(("Config/", "DataForge/")) or path == "KPatchwork.uplugin"
            for path in files
        )
        changes_tooling = any(
            path.startswith(("ci/", ".github/")) or path in {"CONTRIBUTING.md", "pyproject.toml", "uv.lock"}
            for path in files
        )
        if kind == "test" and not changes_packaged_content:
            continue
        if changes_packaged_content or changes_tooling:
            sentence = release_sentence(kind, clean_subject)
            key = note_key(sentence)
            if key not in seen_notes:
                target = player_changes if changes_packaged_content else pack_author_changes
                target.append(sentence)
                seen_notes.add(key)

    lines = [f"# Patchwork: Cross-Mod Compatibility Packs {version(args.root)}"]
    if new_packs:
        lines.extend(["", "## New packs", ""])
        for pack_name, pack_ref, contributors in new_packs:
            lines.append(f"- {pack_name} (`{pack_ref}`), by {format_contributors(contributors)}.")
    if updated_packs:
        lines.extend(["", "## Updated packs", ""])
        for pack_name, pack_ref, contributors in updated_packs:
            lines.append(f"- {pack_name} (`{pack_ref}`), maintained by {format_contributors(contributors)}.")
    if authored_changelogs:
        lines.extend(["", "## Release notes"])
        for entry in authored_changelogs:
            pull_request = f"[#{entry.number}]({entry.url})" if entry.url else f"#{entry.number}"
            lines.extend(["", f"### {entry.title} ({pull_request}) by @{entry.author}", "", entry.text])
    if player_changes:
        lines.extend(["", "## Changes", ""])
        lines.extend(f"- {change}" for change in player_changes)
    if pack_author_changes:
        lines.extend(["", "## For pack authors", ""])
        lines.extend(f"- {change}" for change in pack_author_changes)
    lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"created {args.output} ({len(raw_commits)} commit(s), {len(player_changes)} player change(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
