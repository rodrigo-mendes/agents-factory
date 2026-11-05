# Getting started

This page takes you from a fresh clone to running your first command.

## Before you start

- **Claude Code** installed and signed in.
- **Python 3** on the PATH. The post-install scripts and the documentation generator use only the
  standard library.
- **`apm` CLI**, optional. You only need it to regenerate `.claude/` after editing `packages/`.
- **Windows only:** run `git config --global core.longpaths true` before installing the Vercel
  package, which has deep paths.

## 1. Clone and open

```
git clone <repository-url> agents-factory
cd agents-factory
```

Open Claude Code in this folder. The generated `.claude/` directory is committed, so every
command works immediately, with no network access and no `apm` CLI.

## 2. Run your first three commands

```
/researching-technical-frameworks FastAPI 0.115
```
Researches a technology with version pinning and source checks. The agent shows a plan and waits for
your approval before it writes the research file. It reports the file's path at the end.

```
/skill-creator <path-reported-by-the-previous-run>
```
Turns the research file into a skill. For example, a file named `research_FastAPI_v0.115.md`.

```
/skill-best-practices-validator .claude/skills/
```
Checks the skills against the quality conventions and lists what to fix.

Each entry point has a page with arguments, outputs and examples. Start from
[Entry points](entry-points/README.md).

## 3. Change something

Edit files under `packages/`, never under `.claude/`. Then regenerate:

```
apm install --target claude
python scripts/restore-rule-metadata.py
python scripts/fix-cross-package-links.py
python scripts/gen-docs-catalog.py
python scripts/gen-docs-catalog.py --check
```

Commit `packages/`, `.claude/` and the regenerated documentation together. The full list of what is
generated is in [Maintaining the docs](reference/maintaining-docs.md).

## 4. Use one package in another project

Install a single package or a bundle with `apm install` in the target project. Bundles are
described in [Packages](packages/README.md#bundles). To produce a sellable export of a bundle, use
`scripts/export-bundle.py`, which also runs the sensitive-data detectors before packaging.

## Common problems

| Symptom | Likely cause | What to do |
|---|---|---|
| A `/command` is not listed | `.claude/` was not regenerated after a change | Run the regeneration steps above. |
| `apm install` fails on Windows with a path error | Long paths are disabled | Set `core.longpaths` as described above. |
| The documentation check reports a stale block | A package changed without regenerating the docs | Run `python scripts/gen-docs-catalog.py`. |
