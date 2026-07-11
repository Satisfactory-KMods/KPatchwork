# Contributing

1. Create a branch from `main`.
2. Put pack files under `KDataForge/<your-github-login>/<pack-name>/`.
3. Add `pack.yml` with `contributer: <your-github-login>`.
4. Run the local lint command:

   ```text
   python ci/lint_packs.py
   ```

5. Open a pull request into `main`.

CI lints every YAML document, creates the distributable ZIP, and checks ownership. A pull request
changing only packs whose `contributer` matches the author can be auto-merged after successful CI.
Changes outside author-owned packs stay open until a maintainer approves them.

`main` is protected for everyone, including repository administrators. Do not push directly.
