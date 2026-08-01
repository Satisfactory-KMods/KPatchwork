# DataForge packs

Create a pack directory at any depth below `DataForge/`:

```text
DataForge/**/<pack-name>/pack.yml
```

`pack.yml` requires `ref`, `name`, `version`, `description`, and `contributer`. `description` is
the player-facing text included automatically in the ficsit.app page for
Patchwork: Cross-Mod Compatibility Packs.
`contributer` accepts either one GitHub login or a non-empty list of co-maintainers. Automatic merging
requires the pull-request author to appear in that value.
