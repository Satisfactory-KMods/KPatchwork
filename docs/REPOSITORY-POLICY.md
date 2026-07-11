# Repository policy

`main` must be protected with pull-request-only changes. Disable direct pushes, force-pushes, and
branch deletion for everyone, including administrators. Require one approving review, require review
from `CODEOWNERS`, and require the `KPatchwork CI / Lint packs and package project` check before
merge.

The CI uses an ARC runner labelled `arc-runner` and `uv` for Python tooling. It lints every supported
KDataForge schema construct below `KDataForge`, creates `KPatchwork.zip` containing
`KPatchwork.uplugin`, `KDataForge/`, and `Config/` (excluding `Config/Alpakit.ini`), and enables squash
auto-merge only when all changed files belong to packs whose `contributer` matches the pull-request
author. Main releases set the plugin version to `<year>.<quarter>.<CI-build-number>`, publish
`CHANGELOG.md` generated from commits, and upload the ZIP through ficsit-CLI.

Author-owned pack PRs receive a CI approval after linting and may auto-merge. Changes outside
author-owned packs receive no CI approval and remain blocked until a CODEOWNER explicitly approves.
Branch protection blocks all direct writes to `main`.
