# KDataForge packs

Create one contributor directory per GitHub user, then one directory per pack:

```text
KDataForge/<github-user>/<pack-name>/pack.yml
```

`pack.yml` requires `ref`, `name`, `version`, and `contributer`. The `contributer` value must match
the contributor directory and the GitHub login of the pull-request author for automatic merging.
