# KPatchwork

KPatchwork is a community-maintained collection of KDataForge patch packs for Satisfactory.

## Layout

```text
KPatchwork.uplugin
KDataForge/
  <github-user>/
    <pack-name>/
      pack.yml
      *.yml
```

Each pack lives below its contributor directory. Its `pack.yml` must contain the contributor's GitHub
login in the intentionally stable field `contributer`:

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

## Contributing

Direct pushes to `main` are disabled. Create a branch, make changes, and open a pull request. See
[CONTRIBUTING.md](CONTRIBUTING.md).
