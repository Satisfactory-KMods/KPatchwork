#!/usr/bin/env python3
"""Render and deploy the ficsit.app page for Patchwork: Cross-Mod Compatibility Packs."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import yaml

FICSIT_API_URL = "https://api.ficsit.app/v2/query"
PLACEHOLDER = re.compile(r"{{([A-Z0-9_]+)}}")

GET_MOD_ID_QUERY = """
query GetModId($mod: ModReference!) {
  getModByReference(modReference: $mod) {
    id
  }
}
""".strip()

UPDATE_MOD_QUERY = """
mutation UpdateModDescription($modId: ModID!, $mod: UpdateMod!) {
  updateMod(modId: $modId, mod: $mod) {
    id
  }
}
""".strip()

def _multiplayer_badge(label: str, color: str) -> str:
    encoded_label = urllib.parse.quote(label)
    return (
        f'<img src="https://img.shields.io/badge/Multiplayer-{encoded_label}-{color}'
        '?style=for-the-badge&logo=steam&logoColor=white" '
        f'alt="Multiplayer: {label}" />'
    )


MULTIPLAYER_BADGES = {
    "yes": _multiplayer_badge("Supported", "brightgreen"),
    "no": _multiplayer_badge("Not Supported", "red"),
    "not-tested": _multiplayer_badge("Not Tested", "lightgrey"),
    "wip": _multiplayer_badge("WIP", "yellow"),
}

CONTENT_LABELS = {
    "pda": ("data-asset integration", "data-asset integrations"),
    "recipepatches": ("recipe patch", "recipe patches"),
    "recipes": ("recipe patch", "recipe patches"),
    "schematicpatches": ("schematic patch", "schematic patches"),
    "schematics": ("schematic patch", "schematic patches"),
    "trees": ("research tree patch", "research tree patches"),
}

AI_DISCLOSURE_TYPES = {"ai_usage", "no_ai_usage", "runtime_ai_usage"}


class ConfigurationError(ValueError):
    """Raised when page or pack metadata cannot produce a valid page."""


@dataclass(frozen=True)
class ContentSummary:
    label: str
    count: int


@dataclass(frozen=True)
class PackInfo:
    ref: str
    name: str
    version: str
    description: str
    contributors: tuple[str, ...]
    required_mods: tuple[str, ...]
    contents: tuple[ContentSummary, ...]
    enabled: bool


GraphqlRequester = Callable[[str, dict[str, object], str | None], dict[str, object]]


def _load_yaml_mapping(path: Path, context: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ConfigurationError(f"cannot read {context} {path}: {error}") from error
    if not isinstance(loaded, dict):
        raise ConfigurationError(f"{context} must be a YAML mapping: {path}")
    return loaded


def _required_string(mapping: Mapping[str, object], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{context} requires non-empty {key}")
    return " ".join(value.split())


def _string_list(value: object, context: str) -> tuple[str, ...]:
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list) or not values:
        raise ConfigurationError(f"{context} must be a non-empty string or sequence")
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise ConfigurationError(f"{context} entries must be non-empty strings")
    return tuple(item.strip() for item in values)


def _content_label(directory_name: str, count: int) -> str:
    normalized = directory_name.casefold()
    labels = CONTENT_LABELS.get(normalized)
    if labels is None:
        words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", directory_name).replace("_", " ").replace("-", " ")
        singular = words.strip().casefold() or "other patch"
        if singular.endswith("s"):
            plural = singular
        elif singular.endswith(("ch", "sh", "x", "z")):
            plural = f"{singular}es"
        else:
            plural = f"{singular}s"
        labels = (singular, plural)
    return labels[0] if count == 1 else labels[1]


def _summarize_contents(pack_root: Path) -> tuple[ContentSummary, ...]:
    counts: Counter[str] = Counter()
    documents = sorted({*pack_root.rglob("*.yml"), *pack_root.rglob("*.yaml")})
    for document in documents:
        if document.name == "pack.yml":
            continue
        owner = document.parent
        while owner != pack_root and not (owner / "pack.yml").is_file():
            owner = owner.parent
        if owner != pack_root:
            continue
        relative = document.relative_to(pack_root)
        group = relative.parts[0] if len(relative.parts) > 1 else "other patch"
        counts[group] += 1
    summaries = [ContentSummary(_content_label(group, count), count) for group, count in counts.items()]
    return tuple(sorted(summaries, key=lambda item: item.label.casefold()))


def collect_packs(dataforge_root: Path) -> list[PackInfo]:
    """Load all pack manifests and derive current content summaries."""
    if not dataforge_root.is_dir():
        raise ConfigurationError(f"DataForge root does not exist: {dataforge_root}")

    manifests = sorted(dataforge_root.rglob("pack.yml"))
    if not manifests:
        raise ConfigurationError(f"no pack.yml found below {dataforge_root}")

    packs: list[PackInfo] = []
    for manifest in manifests:
        context = manifest.relative_to(dataforge_root).as_posix()
        data = _load_yaml_mapping(manifest, context)
        conditions = data.get("conditions", {})
        if not isinstance(conditions, dict):
            raise ConfigurationError(f"{context} conditions must be a mapping")
        required_mods_value = conditions.get("hasMod", [])
        required_mods = (
            ()
            if required_mods_value == []
            else _string_list(required_mods_value, f"{context} conditions.hasMod")
        )
        contributors = _string_list(data.get("contributer"), f"{context} contributer")
        enabled = data.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ConfigurationError(f"{context} enabled must be boolean")
        packs.append(
            PackInfo(
                ref=_required_string(data, "ref", context),
                name=_required_string(data, "name", context),
                version=_required_string(data, "version", context),
                description=_required_string(data, "description", context),
                contributors=contributors,
                required_mods=required_mods,
                contents=_summarize_contents(manifest.parent),
                enabled=enabled,
            )
        )
    return sorted(packs, key=lambda pack: (pack.name.casefold(), pack.ref.casefold()))


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _render_pack(pack: PackInfo) -> str:
    required_mods = " + ".join(_escape(mod) for mod in pack.required_mods) or "Always active"
    contents = (
        " &middot; ".join(f"{summary.count} {_escape(summary.label)}" for summary in pack.contents)
        or "Manifest only"
    )
    contributors = ", ".join(f"@{_escape(contributor)}" for contributor in pack.contributors)
    return f"""<table width="100%" cellpadding="0" cellspacing="0" style="border:none;margin-bottom:14px">
<tr>
<td style="background:#e8a202;padding:6px 14px;border-radius:6px 6px 0 0;border:none">
<strong style="color:#1a1a2e;font-size:18px">{_escape(pack.name)}</strong>
</td>
</tr>
<tr>
<td style="padding:12px 14px;border:1px solid #3a3a4e;border-top:none;border-radius:0 0 6px 6px">
<p>{_escape(pack.description)}</p>
<table width="100%" cellpadding="3" cellspacing="0" style="border:none">
<tr><td style="border:none"><strong>Required mods</strong></td><td style="border:none">{required_mods}</td></tr>
<tr><td style="border:none"><strong>Included content</strong></td><td style="border:none">{contents}</td></tr>
<tr><td style="border:none"><strong>Pack version</strong></td><td style="border:none">{_escape(pack.version)}</td></tr>
<tr><td style="border:none"><strong>Maintained by</strong></td><td style="border:none">{contributors}</td></tr>
</table>
</td></tr>
</table>"""


def _template_values(config: Mapping[str, object], packs: Sequence[PackInfo]) -> dict[str, str]:
    template_config = config.get("template")
    if not isinstance(template_config, dict):
        raise ConfigurationError("page config requires template mapping")
    multiplayer = _required_string(template_config, "multiplayer", "template")
    if multiplayer not in MULTIPLAYER_BADGES:
        raise ConfigurationError(f"template multiplayer must be one of {sorted(MULTIPLAYER_BADGES)}")
    enabled_packs = [pack for pack in packs if pack.enabled]
    pack_word = "pack" if len(enabled_packs) == 1 else "packs"
    catalog = "\n\n".join(_render_pack(pack) for pack in enabled_packs)
    if not catalog:
        catalog = "No compatibility packs are currently enabled."
    return {
        "DISCORD_URL": _required_string(template_config, "discordUrl", "template"),
        "PATREON_URL": _required_string(template_config, "patreonUrl", "template"),
        "FICSIT_PROFILE_URL": _required_string(template_config, "ficsitProfileUrl", "template"),
        "MULTIPLAYER_BADGE": MULTIPLAYER_BADGES[multiplayer],
        "PACK_COUNT": f"{len(enabled_packs)} compatibility {pack_word}",
        "PACK_CATALOG": catalog,
    }


def render_description(template: str, config: Mapping[str, object], packs: Sequence[PackInfo]) -> str:
    """Render template and reject stale or misspelled placeholders."""
    rendered = template
    for key, value in _template_values(config, packs).items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    unresolved = sorted(set(PLACEHOLDER.findall(rendered)))
    if unresolved:
        raise ConfigurationError(f"unresolved template placeholder(s): {', '.join(unresolved)}")
    return rendered.strip() + "\n"


def load_page_config(path: Path) -> dict[str, Any]:
    config = _load_yaml_mapping(path, "page config")
    _required_string(config, "modReference", "page config")
    _required_string(config, "shortDescription", "page config")
    return config


def build_update_input(config: Mapping[str, object], full_description: str) -> dict[str, object]:
    """Map repository page config to ficsit.app's UpdateMod input."""
    if not full_description.strip():
        raise ConfigurationError("rendered full description is empty")
    update: dict[str, object] = {
        "full_description": full_description,
        "short_description": _required_string(config, "shortDescription", "page config"),
    }
    optional_fields = {
        "name": "name",
        "sourceUrl": "source_url",
        "hidden": "hidden",
        "networkUseDisclosure": "network_use_disclosure",
    }
    for source_key, api_key in optional_fields.items():
        if source_key in config:
            value = config[source_key]
            if source_key == "hidden":
                if not isinstance(value, bool):
                    raise ConfigurationError("page config hidden must be boolean")
                update[api_key] = value
            else:
                update[api_key] = _required_string(config, source_key, "page config")

    disclosure = config.get("aiUseDisclosure")
    if disclosure is not None:
        if not isinstance(disclosure, dict):
            raise ConfigurationError("page config aiUseDisclosure must be a mapping")
        disclosure_type = _required_string(disclosure, "type", "aiUseDisclosure")
        if disclosure_type not in AI_DISCLOSURE_TYPES:
            raise ConfigurationError(f"aiUseDisclosure type must be one of {sorted(AI_DISCLOSURE_TYPES)}")
        api_disclosure: dict[str, object] = {"disclosure_type": disclosure_type}
        if "message" in disclosure:
            api_disclosure["message"] = _required_string(disclosure, "message", "aiUseDisclosure")
        update["ai_use_disclosure"] = api_disclosure
    return update


def graphql_request(query: str, variables: dict[str, object], token: str | None = None) -> dict[str, object]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = token
    request = urllib.request.Request(
        FICSIT_API_URL,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.HTTPError, json.JSONDecodeError) as error:
        raise RuntimeError(f"ficsit.app request failed: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError("ficsit.app returned a non-object response")
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        messages = [str(error.get("message", error)) if isinstance(error, dict) else str(error) for error in errors]
        raise RuntimeError(f"ficsit.app GraphQL error: {'; '.join(messages)}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("ficsit.app response did not contain data")
    return data


def deploy_ficsit_page(
    config: Mapping[str, object],
    full_description: str,
    token: str,
    *,
    requester: GraphqlRequester = graphql_request,
) -> str:
    """Resolve the stable KPatchwork reference and publish page metadata."""
    if not token.strip():
        raise ConfigurationError("FICSIT_TOKEN is empty")
    mod_reference = _required_string(config, "modReference", "page config")
    lookup = requester(GET_MOD_ID_QUERY, {"mod": mod_reference}, None)
    mod = lookup.get("getModByReference")
    mod_id = mod.get("id") if isinstance(mod, dict) else None
    if not isinstance(mod_id, str) or not mod_id:
        raise ConfigurationError(f"ficsit.app mod reference did not resolve: {mod_reference}")
    result = requester(
        UPDATE_MOD_QUERY,
        {"modId": mod_id, "mod": build_update_input(config, full_description)},
        token,
    )
    updated = result.get("updateMod")
    updated_id = updated.get("id") if isinstance(updated, dict) else None
    if not isinstance(updated_id, str) or not updated_id:
        raise RuntimeError("ficsit.app updateMod response did not contain an id")
    return updated_id


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path(".github/ficsit-page.yml"))
    parser.add_argument("--template", type=Path, default=Path(".github/ficsit-description.template.md"))
    parser.add_argument("--description", type=Path, help="Use an already-rendered description")
    parser.add_argument("--output", type=Path, help="Write rendered description to this path")
    parser.add_argument("--deploy", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    config = load_page_config(_resolve(root, args.config))
    if args.description:
        description = _resolve(root, args.description).read_text(encoding="utf-8")
    else:
        template = _resolve(root, args.template).read_text(encoding="utf-8")
        description = render_description(template, config, collect_packs(root / "DataForge"))

    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(description, encoding="utf-8", newline="\n")
        print(f"rendered ficsit.app description: {output}")

    if args.deploy:
        token = os.environ.get("FICSIT_TOKEN", "")
        updated_id = deploy_ficsit_page(config, description, token)
        print(f"updated ficsit.app page: {updated_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
