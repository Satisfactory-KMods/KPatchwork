# Repository policy

`main` must be protected with pull-request-only changes. Disable direct pushes, force-pushes, and
branch deletion for everyone, including administrators. Require the `KPatchwork CI / Lint packs and
package project` check before merge.

The CI uses an ARC runner labelled `arc-runner`. It lints every `*.yml`/`*.yaml` below `KDataForge`,
creates `KPatchwork.zip` containing `KPatchwork.uplugin` and `KDataForge/`, and enables squash
auto-merge only when all changed files belong to packs whose `contributer` matches the pull-request
author.

Changes outside author-owned packs remain open for explicit maintainer approval. This conditional
approval rule is enforced by the CI decision; branch protection still blocks all direct writes to
`main`.
