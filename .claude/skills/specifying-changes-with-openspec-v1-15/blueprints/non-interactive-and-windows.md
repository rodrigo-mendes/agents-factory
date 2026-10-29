# Non-Interactive Use, CI and Windows (OpenSpec 1.15.0)

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md).

## Contents

- [Non-interactive switches](#non-interactive-switches)
- [JSON and result reading](#json-and-result-reading)
- [Archive recovery](#archive-recovery)
- [Validation thresholds](#validation-thresholds)
- [Windows](#windows)
- [Security and telemetry](#security-and-telemetry)

## Non-interactive switches

Sources: [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md), [agent-contract.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md), [releases](https://github.com/Fission-AI/OpenSpec/releases), [troubleshooting](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/troubleshooting.md).

- `show` and `validate` accept `--no-interactive`. `OPEN_SPEC_INTERACTIVE=0` or a non-TTY stdin also suppresses prompts (medium confidence, L1: summarising fetch, no recorded quote).
- With `CI` set or `OPEN_SPEC_INTERACTIVE=0` the spinner is off, and since v1.14.3 `validate --all` no longer hangs in pre-commit hooks or zero-column terminals (medium confidence, L2: condensed release highlights).
- With `CI` set, telemetry is disabled (medium confidence, L1: cli.md summary); the update check is disabled too (medium confidence, L2).
- Always pass a change name and `--yes` to `archive` ("stops before changing anything" and exits 1 without a terminal and without `--yes`; High, quote in the register). Redirected or agent-run archive output stays clean and confirmations are read as plain text when stdout is not a TTY (medium confidence, L2).
- `--json` commands start faster in v1.15.0 because they no longer load the spinner (medium confidence, L2).
- Exit codes: `0` success, `1` error (validation failures, missing files, no root, and `archive` with no terminal and no `--yes`), `130` for `config profile` cancelled with Ctrl+C (medium confidence, L1: summarising fetch, no recorded quote; the `archive` case alone is High).
- Root detection is the nearest ancestor that has an `openspec/` folder (agent-contract.md).

## JSON and result reading

`validate --json` has two documented shapes (conflict C3, [conflicts](./doc-vs-validator-conflicts.md#c3-validate---json-shape)):

| Page | Shape |
|---|---|
| agent-contract.md and cli-validate spec | top-level `items`, `summary`, `version: "1.0"`; each item has `id`, `type`, `valid`, `issues[]` (`level` ERROR/WARNING/INFO, `path`, `message`) and `durationMs` |
| cli.md | `version`, `results` (`name`, `valid`, `warnings`) and `summary` (`total`, `valid`, `invalid`) |

Parse defensively: gate on the **exit code** (medium confidence, L1), then read `items` and fall back to `results` (medium confidence, M1). Confirm both once against a real 1.15.0 run (Ask First).

`archive --json`: cli.md lists no `--json` flag for `archive`, agent-contract.md documents an `archive` JSON object, and the v1.14.1 release note mentions `archive_retirement_cleanup_failed` "in `--json`". Whether `archive` accepts `--json` in 1.15.0 is (unverified). Read the result from the exit code, then check that `openspec/changes/archive/<date>-<id>/` exists.

`archive` with incomplete tasks: troubleshooting says it "won't block" but warns; the cli-archive spec says it prompts with default No and declining aborts non-zero. With `--yes` the behaviour is presumably to proceed (unverified). Finish the checkboxes before archiving.

Deprecated subcommands: agent-contract.md says "Deprecated `change`/`spec` subcommands emit unenveloped payloads" (known inconsistency 8), while the validator guide text in constants.ts still mentions `openspec change show`. Prefer `openspec show <id> --type change --json --deltas-only --no-interactive` over `openspec change show <id> ...` (medium confidence). Other known inconsistencies listed there: mixed snake_case and camelCase keys, and only `validate` carries `version`.

## Archive recovery

(medium confidence, L2: condensed page, no recorded quote) From [agent-contract.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md):

- `archive_retirement_cleanup_failed`: the change was archived but cleanup failed. Inspect; do not retry.
- `archive_error`: files may or may not have changed. Inspect the change, the archive and the specs before retrying.
- `archive: null` does not guarantee that files are unchanged.

## Validation thresholds

Per constant, from [constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts):

| Constant | Value | Severity |
|---|---|---|
| `MIN_PURPOSE_LENGTH` | 50 | warning |
| `MIN_WHY_SECTION_LENGTH` | 50 | error |
| `MAX_WHY_SECTION_LENGTH` | 1000 | "should not exceed" |
| `MAX_REQUIREMENT_TEXT_LENGTH` | 500 | warning; `--strict` fails on it since v1.14.1 (medium confidence, L2) |
| `MAX_DELTAS_PER_CHANGE` | 10 | "Consider splitting..."; severity (unverified) |

`--strict` also fails on warnings about delta text that would be dropped (v1.14.2) and on unrecognized `.openspec.yaml` keys (v1.14.0) ([releases](https://github.com/Fission-AI/OpenSpec/releases)). Brace globs deeper than 16 levels or expanding past 1,024 paths are rejected. These statements are (medium confidence, L2): condensed release highlights.

## Windows

Sources: [installation.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/installation.md), [releases](https://github.com/Fission-AI/OpenSpec/releases), [troubleshooting](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/troubleshooting.md).

- Standalone binaries for Windows x64 and arm64 ship with v1.15.0, with a PowerShell installer and `SHA256SUMS`; Windows 10 or later. Install choices and pin syntax: [ask-first C2](./ask-first-decisions.md#c2-install-channel-and-pinning).
- With npm, the global bin directory must be on `PATH` (`npm prefix -g`).
- v1.13.2: archive on Windows leaves no `.openspec-archive.lock` behind and completes instead of rolling back when Windows blocks a rename (medium confidence, L2).
- v1.14.3: `list`, `show`, `validate` and `archive` accept symlinked `spec.md` files inside the project; links resolving outside are refused (medium confidence, L2).
- Shell completion supports `powershell`. The Windows global config path is (unverified); run `openspec config path`.
- Yarn 1.x only (Yarn 2 and later removed `global`).

## Security and telemetry

- Telemetry collects command names and version only. Opt out with `openspec config set telemetry.enabled false`, `OPENSPEC_TELEMETRY=0` or `DO_NOT_TRACK=1` (medium confidence, L1: cli.md summary).
- Since v1.13.1, `config.yaml` values cannot inject directives into agent instructions and a repo `.npmrc` cannot redirect the update check (medium confidence, L2).
- v1.14.3 dropped the unpatched `braces` package and refuses glob or symlink paths that leave the change directory (medium confidence, L2).
- Standalone downloads are checked against `SHA256SUMS`.
