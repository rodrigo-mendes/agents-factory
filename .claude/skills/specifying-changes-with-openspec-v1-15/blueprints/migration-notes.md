# Migration Notes: 1.13.0 to 1.15.0 (OpenSpec)

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Sources: [releases](https://github.com/Fission-AI/OpenSpec/releases) (condensed highlights, coverage limit L2), [v1.15.0 release](https://github.com/Fission-AI/OpenSpec/releases/tag/v1.15.0), [migration-guide](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/migration-guide.md).

## Contents

- [Breaking changes](#breaking-changes)
- [Stricter behaviour that matters to automation](#stricter-behaviour-that-matters-to-automation)
- [Legacy layout migration](#legacy-layout-migration)
- [Upgrade steps](#upgrade-steps)
- [Compatibility matrix](#compatibility-matrix)

## Breaking changes

No release from v1.13.0 to v1.15.0 is labelled breaking (medium confidence, L2: condensed release highlights). There is no published stability policy for the core CLI (unverified).

## Stricter behaviour that matters to automation

Every row below comes from the releases page, read as condensed highlights: each is (medium confidence, L2).

| Release | Change | Effect on agents |
|---|---|---|
| v1.13.0 | archive stops rewriting fenced code; `*` and `+` removals and renames take effect | none to author |
| v1.13.1 | archive refuses mismatched `RENAMED` FROM/TO lines and case-only name differences; validate reports requirements written outside a delta section and scenarios with no body; generated workflows name only the workflows the profile installs; `config.yaml` values cannot inject directives | re-validate old deltas |
| v1.13.2 | archive on Windows leaves no `.openspec-archive.lock`, completes instead of rolling back when Windows blocks a rename | Windows hosts |
| v1.14.0 | `list --archived/--all`; requirement and scenario names in `show --json`; `validate --strict` fails on unrecognized `.openspec.yaml` keys; archive stops when spec sync reports a blocking condition; init guides the `project.md` to `config.yaml` move | keep `.openspec.yaml` keys to the known set |
| v1.14.1 | requirements over 500 characters are a warning, so `--strict` fails on them; `view` no longer lists archived changes; `--version`/`--help` load 24 modules instead of 485 | split long requirements |
| v1.14.2 | validate and archive warn when delta text would be dropped, and these warnings fail `--strict`; top-level `x-` keys in `.openspec.yaml` are ignored; `/opsx:verify` reports unverified when a REMOVED requirement's original text cannot be read | fix the delta, do not suppress |
| v1.14.3 | `validate --all` no longer hangs in pre-commit hooks; `OPEN_SPEC_INTERACTIVE=0`/`CI` turn off the spinner; symlinked `spec.md` accepted inside the project; unpatched `braces` dropped | CI and hooks |
| v1.15.0 | standalone binaries (macOS, Linux, Windows; x64 and arm64; `SHA256SUMS`); `openspec update --dry-run [--json]`; faster `--json` startup; `/opsx:verify` matches REMOVED requirements by exact name; `openspec feedback` | install channel |

## Legacy layout migration

From the migration guide:

- `openspec/project.md` becomes `openspec/config.yaml` (`context:` plus per-artifact `rules:`); `project.md` is not auto-deleted.
- `openspec/AGENTS.md` is deleted as obsolete.
- OpenSpec marker blocks in root `CLAUDE.md` or `AGENTS.md` are stripped; "everything you wrote stays".
- Legacy `.claude/commands/openspec/` is removed.
- `/openspec:proposal|apply|archive` map to `/opsx:propose|apply|archive`.

## Upgrade steps

Representative; do not run in this skill's authoring.

1. Standalone: rerun the installer with `OPENSPEC_VERSION=v1.15.0`. npm: `npm install -g @fission-ai/openspec@1.15.0` (pin form is (medium confidence), see [ask-first C2](./ask-first-decisions.md#c2-install-channel-and-pinning)).
2. `openspec --version` should print the version.
3. In each project: `openspec update --dry-run --json` to preview, then `openspec update`.
4. `openspec validate --all --strict --json --no-interactive` to surface the stricter v1.14.x rules.

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Node.js (npm, pnpm, yarn, bun installs) | 20.19.0 | not stated | `engines.node ">=20.19.0"`; standalone needs none |
| Windows | 10 | not stated | `openspec-windows-x64.exe` / `-arm64.exe` |
| macOS | 13 | not stated | installation.md |
| Linux glibc | 2.17 | not stated | Alpine 3.17+ musl needs `apk add libstdc++ libgcc` |
| Yarn | 1.x | 1.x | Yarn 2 and later removed `global` |

Sources: [installation.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/installation.md), [package.json](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/package.json), [registry](https://registry.npmjs.org/@fission-ai/openspec/1.15.0).
