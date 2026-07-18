# KPatchwork

KPatchwork makes mods compatible with each other through small, conditional data patches.

## What it does

Packs can change recipes or add assets only when a specific combination of mods is loaded. For
example, a SatisfactoryPlus + RSS pack can change recipes so they use SatisfactoryPlus items.

Each pack should focus on one compatibility case and keep its changes in readable YAML files.

## Working on KPatchwork

KPatchwork is developed in the public repository:

https://github.com/Satisfactory-KMods/KPatchwork

Anyone can contribute a compatibility pack through a pull request. Changes that stay inside the
author's own pack are linted, packaged, and may be merged automatically by CI. Release checks run
hourly; a release is created only when packaged content changed since latest Git tag.

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
2. Keep `pack.yml` complete and list every maintainer in its `contributer` field.
3. Put the actual data changes in focused YAML files next to `pack.yml`.
4. Explain which mod combination the pack supports.
5. Add optional player-facing release notes below `## Changelog` in the pull-request description.
6. Run the repository lint before opening the pull request:

```text
uv run --locked Lint/lint_packs.py --root DataForge
```

Changes to shared tooling, CI, or the KPatchwork plugin metadata should be kept separate from pack
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
Hourly release checks compare those packaged paths against latest tag. A detected change receives
`<year>.<quarter>.<CI-build-number>`, creates a GitHub Release with ZIP and changelog, and uploads
through ficsit-CLI. Pushes never release directly.

## Contributing

Direct pushes to `main` are disabled. Create a branch, make changes, and open a pull request. See
[CONTRIBUTING.md](CONTRIBUTING.md).
