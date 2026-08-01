# Contributing

1. Create a branch from `main`.
2. Put pack files under any depth below `DataForge/`.
3. Add `pack.yml` with a concise player-facing `description` plus
   `contributer: <your-github-login>` or a list of co-maintainers. CI includes the description in
   the ficsit.app page for Patchwork: Cross-Mod Compatibility Packs.
4. Run the local lint command:

   ```text
   uv run --locked kdataforge-linter lint DataForge --schema-dir ci/schemas --allow-schema-override
   ```

5. Add optional player-facing release notes below `## Changelog` in the pull-request description.
   CI copies visible content from that section into the next GitHub and ficsit.app changelog.
6. Open a pull request into `main`.

CI lints every KDataForge schema construct, renders a ficsit.app page preview, creates the distributable
ZIP, generates a commit changelog, and checks ownership. A pull request changing only packs whose
`contributer` string/list contains the author is rebase-merged after successful CI. Push and manual
release checks release only when packaged content changed since latest Git tag.
Changes outside author-owned packs stay open until a maintainer approves them.

`main` is protected for everyone, including repository administrators. Do not push directly.
