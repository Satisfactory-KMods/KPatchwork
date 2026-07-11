# KPatchwork

KPatchwork is a community-maintained collection of KDataForge patch packs for Satisfactory.

## Layout

```text
KPatchwork.uplugin
KDataForge/
  **/
    <pack-name>/
      pack.yml
      *.yml
```

Each pack lives below `KDataForge/`. Its `pack.yml` must contain the contributor's GitHub login in
the intentionally stable field `contributer`:

```yaml
ref: MyPack
name: My Pack
version: 1.0.0
contributer: github-user
enabled: true
```

Every pack is linted in CI. Pull requests that only change packs owned by the pull-request author may
auto-merge after CI passes. Changes to another contributor's pack, plugin metadata, or repository
configuration require an explicit maintainer approval.

CI creates a release ZIP containing `KPatchwork.uplugin`, `KDataForge/`, and `Config/` (excluding
`Config/Alpakit.ini`) and generates `CHANGELOG.md` from the commit range. Main releases receive
`<year>.<quarter>.<CI-build-number>` and upload through ficsit-CLI.

## Contributing

Direct pushes to `main` are disabled. Create a branch, make changes, and open a pull request. See
[CONTRIBUTING.md](CONTRIBUTING.md).
