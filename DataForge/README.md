# DataForge packs

Create a pack directory at any depth below `DataForge/`:

```text
DataForge/**/<pack-name>/pack.yml
```

`pack.yml` requires `ref`, `name`, `version`, `description`, and `contributer`. Patchwork places the
player-facing `description` on its ficsit.app page automatically. `contributer` accepts one GitHub
login or a non-empty list of co-maintainers. The pull-request author must appear in that value for
automatic merging.
