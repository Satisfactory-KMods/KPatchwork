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
   Describe what changed in the game, for example: "Added the missing costs for Base Tech
   Augmentation recipes." These notes replace summaries of the same PR's commits. Commits without
   release notes use their subjects as a fallback, so give them specific, readable titles.
6. Open a pull request into `main`.

CI lints every KDataForge schema construct, renders a ficsit.app page preview, creates the distributable
ZIP, generates a commit changelog, and checks ownership. A pull request changing only packs whose
`contributer` string/list contains the author is rebase-merged after successful CI. Push and manual
release checks release only when packaged content changed since latest Git tag.
Changes outside author-owned packs stay open until a maintainer approves them.

Release notes list each change once. New and updated packs keep their names and contributor credits.
The "For pack authors" section appears only for changes to CI, author documentation, or pack tooling;
gameplay changes appear under "Changes". Empty sections are omitted.

Ownership results requiring review appear in the reporting job summary and a bot comment. If GitHub
denies the comment with HTTP 403, the job emits a warning and keeps the summary available; this does
not make the pull request eligible for auto-merge.

Workflow regression tests require Node.js 24 and the locked Python dependencies:

```text
uv run --locked python -m unittest discover -s ci/tests -v
```

`main` is protected for everyone, including repository administrators. Do not push directly.
