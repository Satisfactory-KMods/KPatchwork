# Contributing

1. Create a branch from `main`.
2. Put pack files under any depth below `DataForge/`.
3. Add `pack.yml` with `contributer: <your-github-login>` or a list of co-maintainers.
4. Download the CLI from the latest
   [KDataForge Linter release](https://github.com/Satisfactory-KMods/KDataForge-Linter/releases/latest),
   then run the local lint command:

   ```text
   kdataforge-linter lint DataForge
   ```

5. Open a pull request into `main`.

CI lints every KDataForge schema construct, creates the distributable ZIP, generates a commit
changelog, and checks ownership. A pull request changing only packs whose `contributer` string/list
contains the author is rebase-merged after successful CI. Releases are checked hourly and occur only
when packaged content changed since latest Git tag.
Changes outside author-owned packs stay open until a maintainer approves them.

`main` is protected for everyone, including repository administrators. Do not push directly.
