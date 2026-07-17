# Contributing

1. Create a branch from `main`.
2. Put pack files under any depth below `DataForge/`.
3. Add `pack.yml` with `contributer: <your-github-login>` or a list of co-maintainers.
4. Run the local lint command:

   ```text
   uv run Lint/lint_packs.py
   ```

5. Add optional player-facing release notes below `## Changelog` in the pull-request description.
   CI copies visible content from that section into the next GitHub and ficsit.app changelog.
6. Open a pull request into `main`.

CI lints every KDataForge schema construct, creates the distributable ZIP, generates a commit
changelog, and checks ownership. A pull request changing only packs whose `contributer` string/list
contains the author is rebase-merged after successful CI. Releases are checked hourly and occur only
when packaged content changed since latest Git tag.
Changes outside author-owned packs stay open until a maintainer approves them.

`main` is protected for everyone, including repository administrators. Do not push directly.
