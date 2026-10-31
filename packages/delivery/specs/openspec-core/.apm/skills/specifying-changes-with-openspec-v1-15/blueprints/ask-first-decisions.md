# Ask-First Decisions (OpenSpec 1.15.0)

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Default per user decision G1: agents drive, OpenSpec supplies format and CLI.

## Contents

- [C1 Repo bootstrap](#c1-repo-bootstrap)
- [C2 Install channel and pinning](#c2-install-channel-and-pinning)
- [C3 Sync before archive or archive only](#c3-sync-before-archive-or-archive-only)
- [C4 Change without spec impact](#c4-change-without-spec-impact)
- [C5 Profile and delivery for a human](#c5-profile-and-delivery-for-a-human)
- [/opsx overlap table](#opsx-overlap-table)

## C1 Repo bootstrap

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A `openspec init --tools none` | Agents never depend on generated skills; skips tool configuration | A human loses `/opsx:*` | G1 default |
| B `openspec init --tools claude` | A human gets `/opsx:*` helpers | Writes `.claude/skills/openspec-*/SKILL.md` and `.claude/commands/opsx/<id>.md`; may overlap our agents | A human also works the flow by hand |
| C create `openspec/specs/` and `openspec/changes/` by hand | No CLI run at setup | Whether the CLI accepts a root with no `config.yaml` is (unverified) | Not recommended |

- `--tools` makes `init` non-interactive; `--force` auto-cleans legacy files without prompting; `init` is listed among the human-only commands ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)). Default delivery is `both` and default profile is `core` ([supported-tools](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/supported-tools.md)).
- What `--tools none` writes (for example `openspec/config.yaml`, which folders) is (unverified); the migration guide says init and update write `openspec/config.yaml` with a default `schema:` but not whether that holds for `none`. Workaround: a human runs `init` once, then the script checks that `openspec/specs` and `openspec/changes` exist.
- Whether `init --tools claude` touches `CLAUDE.md` is (unverified): the supported-tools page does not mention it.
- Since v1.13.1 generated workflows never create an `openspec/` folder, so `init` must have run first (medium confidence, L2: condensed release highlights; [releases](https://github.com/Fission-AI/OpenSpec/releases)).

Ask: "Does a human also want the `/opsx:*` helpers (B) or agents only (A, default per G1)?"

## C2 Install channel and pinning

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A standalone binary, PowerShell `irm https://raw.githubusercontent.com/Fission-AI/OpenSpec/main/scripts/binary/install.ps1 \| iex` | No Node.js; download checked against `SHA256SUMS`; installs to `%LOCALAPPDATA%\Programs\openspec` and adds it to the user `PATH` | Runs a remote script from `main`, not from the tag | Workstations without Node |
| B npm `npm install -g @fission-ai/openspec@latest` | Package-manager pinning; CI-friendly | Needs Node 20.19.0 or later | CI images that already have Node |
| C manual download of `openspec-windows-x64.exe` or `-arm64.exe`, renamed to `openspec.exe` and put on `PATH` | Full control, auditable | Manual PATH and updates | Locked-down machines |

Source: [installation.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/installation.md).

- The standalone installer takes the variable `OPENSPEC_VERSION=v1.15.0`. A PowerShell form such as `$env:OPENSPEC_VERSION='v1.15.0'; irm ... | iex` is (medium confidence): the page names the variable and shows no PowerShell syntax.
- `npm install -g @fission-ai/openspec@1.15.0` uses standard npm version syntax and is (medium confidence): the page documents only `@latest`.

Ask: "Which channel? May I run it?" Agents never run an installer without that answer.

## C3 Sync before archive or archive only

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A archive only: `openspec archive <id> --yes` | One CLI-owned merge with validation | Live specs lag until archive | Default for agents |
| B sync during the change (the `/opsx:sync` skill, "without archiving") | Live specs current mid-change | No CLI subcommand is documented in cli.md (medium confidence, absence of evidence); our own merge logic must follow the [archive order](./delta-format-and-archive.md#archive-merge-order) | Long changes needing early spec truth |
| C `openspec archive <id> --skip-specs` | Archives docs-only or tooling changes | Specs not updated | Changes with `skip_specs: true` |

Sources: [opsx.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/opsx.md), [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md), [cli-archive spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md). Ask: "Must live specs reflect this change before archive?"

## C4 Change without spec impact

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A add a delta | Traceability | Artificial requirements | Behaviour actually changes |
| B `skip_specs: true` in `.openspec.yaml` | Honest no-spec refactors | No spec trail | Pure refactor, tooling, docs |

- Zero deltas fail validation unless `skip_specs: true`; `skip_specs` together with files under `specs/` is an error ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md), [constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)).
- `validate --strict` fails on unrecognized `.openspec.yaml` keys; top-level `x-` keys are ignored (medium confidence, L2: condensed release highlights; [releases](https://github.com/Fission-AI/OpenSpec/releases)).

Ask: "Does the change alter observable behaviour?"

## C5 Profile and delivery for a human

- Core profile workflows: `propose, explore, apply, update, sync, archive`. Expanded: `new, continue, ff, verify, bulk-archive, onboard` ([supported-tools](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/supported-tools.md), [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)).
- Switch with `openspec config profile [preset]`, then `openspec update`; `openspec update --dry-run --json` previews without writing (new in v1.15.0).
- The config key for delivery (skills, commands, both) and the Windows global config path are (unverified); a human runs `openspec config path` and `openspec config list`.

Ask only if a human wants `/opsx:verify` or other expanded workflows.

## /opsx overlap table

Optional human tools versus our agents ([opsx.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/opsx.md), [releases](https://github.com/Fission-AI/OpenSpec/releases)). Do not run both. The generated `/opsx:*` commands and `openspec-*` skills are regenerated and pruned by `openspec update` per profile (medium confidence, L1: paraphrase of [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md), no verbatim quote recorded).

| `/opsx:*` workflow (human, optional) | What it does | Our side (agents) |
|---|---|---|
| `/opsx:apply` | Works through tasks, checks them off, updates artifacts when needed | The implementing agent edits `tasks.md` checkboxes itself |
| `/opsx:sync` | Merges delta specs into `openspec/specs/` without archiving; REMOVED requirements deleted, RENAMED retitled in place | The `spec-synchronizer` agent, following the [archive order](./delta-format-and-archive.md#archive-merge-order) |
| `/opsx:verify` (expanded profile) | Validates the implementation against the artifacts; the detailed checks are (unverified) | Our quality gate, which defines its own checks, plus `openspec validate --strict` |
| `/opsx:archive` | Finalizes the change and offers to sync first | `openspec archive <id> --yes` |

Workflow-to-skill names other than `/opsx:apply` to `openspec-apply-change` are inferred (medium confidence): `openspec-propose`, `openspec-sync-specs`, `openspec-archive-change`, `openspec-verify-change`.
