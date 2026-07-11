# Repository policy

`main` must be protected with pull-request-only changes. Disable direct pushes, force-pushes, and
branch deletion for everyone, including administrators. Require one approving review, require review
from `CODEOWNERS`, and require the `KPatchwork CI / Lint packs and package project` check before
merge.

The CI uses an ARC runner labelled `arc-runner`. It lints every `*.yml`/`*.yaml` below `KDataForge`,
creates `KPatchwork.zip` containing `KPatchwork.uplugin` and `KDataForge/`, and enables squash
auto-merge only when all changed files belong to packs whose `contributer` matches the pull-request
author.

Author-owned pack PRs receive a CI approval after linting and may auto-merge. Changes outside
author-owned packs receive no CI approval and remain blocked until a CODEOWNER explicitly approves.
Branch protection blocks all direct writes to `main`.
