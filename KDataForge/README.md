# KDataForge packs

Create a pack directory at any depth below `KDataForge/`:

```text
KDataForge/**/<pack-name>/pack.yml
```

`pack.yml` requires `ref`, `name`, `version`, and `contributer`. The `contributer` value is the
GitHub login of the pack owner and must match the pull-request author for automatic merging.
