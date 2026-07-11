# DataForge packs

Create a pack directory at any depth below `DataForge/`:

```text
DataForge/**/<pack-name>/pack.yml
```

`pack.yml` requires `ref`, `name`, `version`, and `contributer`. `contributer` accepts either one
GitHub login or a non-empty list of co-maintainers. Automatic merging requires the pull-request
author to appear in that value.
