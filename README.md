# Patchwork: Cross-Mod Compatibility Packs

Patchwork makes Satisfactory mods work together through small, conditional data patches. Its mod
reference is `KPatchwork`.

## What Patchwork changes

A pack changes recipes or adds assets only when its required combination of mods is loaded. For
example, a SatisfactoryPlus + RSS pack can update RSS recipes to use SatisfactoryPlus items. Each
pack handles one compatibility case in readable YAML files.

Current packs, required mods, versions, maintainers, and affected content appear on the
[ficsit.app mod page](https://ficsit.app/mod/KPatchwork). Satisfactory Mod Manager installs
KDataForge with Patchwork.

## Contribute a compatibility pack

Development happens in the public [KPatchwork repository](https://github.com/Satisfactory-KMods/KPatchwork).
Anyone can contribute a pack through a pull request. CI lints and packages changes made inside the
author's own pack and may merge them automatically. Push and manual release checks publish only when
packaged content has changed since the latest Git tag. Repository CI also rebuilds the ficsit.app
page from current pack manifests.

The main contribution area is `DataForge/`:

```text
DataForge/
  <category>/
    <pack-name>/
      pack.yml
      *.yml
```

To add or update a pack:

1. Create or edit the pack directory under `DataForge/`.
2. Keep `pack.yml` complete. Write its player-facing `description` and list every maintainer in the
   `contributer` field.
3. Put the actual data changes in focused YAML files next to `pack.yml`.
4. Explain which mod combination the pack supports.
5. Add optional player-facing release notes below `## Changelog` in the pull-request description.
6. Run the repository lint before opening the pull request:

```text
uv run --locked kdataforge-linter lint DataForge --schema-dir ci/schemas --allow-schema-override
```

CI uses the official KDataForge Linter version pinned in `uv.lock`. The repository-local
`ci/schemas/pack.schema.yml` extends its strict pack schema with the required player-facing
`description` used to generate the mod page.

Changes to shared tooling, CI, or `KPatchwork.uplugin` metadata should be kept separate from pack
content where possible and require maintainer review.

## Layout

```text
KPatchwork.uplugin
DataForge/
  **/
    <pack-name>/
      pack.yml
      *.yml
```

Each pack lives below `DataForge/`. Its `pack.yml` must contain one or more contributor GitHub logins
in the intentionally stable field `contributer`:

```yaml
ref: MyPack
name: My Pack
version: 1.0.0
description: Explains player-facing compatibility changes supplied by this pack.
contributer:
  - github-user
  - another-user
enabled: true
```

Every pack is linted in CI. Pull requests that only change packs owned by the pull-request author may
auto-merge after CI passes. Changes to another contributor's pack, plugin metadata, or repository
configuration require an explicit maintainer approval. Changes to the `contributer` field always
require explicit maintainer approval, including changes that add the pull-request author.

CI creates a release ZIP containing identical `KPatchwork.uplugin`, `DataForge/`, and `Config/`
trees under `Windows/`, `LinuxServer/`, and `WindowsServer/` (excluding `Config/Alpakit.ini`) and
generates `CHANGELOG.md` from latest Git tag through current `main`.
Text below `## Changelog` in included pull requests is copied into the GitHub and ficsit.app
changelogs. The section ends at the next level-one or level-two heading; an empty section is ignored.
Push and manual release checks compare those packaged paths against the latest tag. A detected change receives
`<year>.<quarter>.<CI-build-number>`, creates a GitHub Release with ZIP and changelog, and uploads
through ficsit-CLI. Feature-branch pushes never release directly.

CI renders `.github/ficsit-description.template.md` with every enabled pack's name, description,
required mods, version, maintainers, and current YAML content groups. On `main` pushes and manual
runs, Patchwork updates its own ficsit.app metadata and full description through the API. The main
modding repository no longer owns this page. Render it locally without publishing:

```text
uv run --locked ci/ficsit_page.py --root . --output dist/FICSIT_DESCRIPTION.md
```

## Contributing

Direct pushes to `main` are disabled. Create a branch, make changes, and open a pull request. See
[CONTRIBUTING.md](CONTRIBUTING.md).
