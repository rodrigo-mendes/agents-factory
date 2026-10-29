---
name: specifying-changes-with-openspec-v1-15
description: "Guides OpenSpec v1.15.0 spec-driven changes: openspec/ layout, spec and delta format, tasks.md and the openspec CLI (validate, show, archive) in non-interactive use, incl. Windows. Use when writing or checking OpenSpec specs and changes. Not for /opsx commands, other versions or code sync."
---

# Specifying changes with OpenSpec 1.15

> Version lock: every claim applies to **OpenSpec 1.15.0** (npm `@fission-ai/openspec`, repo `Fission-AI/OpenSpec` at tag `v1.15.0`) only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: the OpenSpec **format** (layout, spec, delta, proposal, tasks) and the **`openspec` CLI**, as used by this factory's own agents. No Quarkus or AWS content. Neighbours, by name only: `coordinating-agent-handoffs` (handoff protocol), `syncing-spec-from-code` (code to spec), the `spec-synchronizer` agent, and `building-quarkus-aws-saas` (the family orchestrator).

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| OpenSpec | 1.15.0, tagged 2026-10-24 (year from the tags page), "Latest" release on 2026-10-28, MIT; no v1.15.1 or later at that date | https://github.com/Fission-AI/OpenSpec/tags ; https://github.com/Fission-AI/OpenSpec/releases |
| Documentation at the tag | `docs/` and `openspec/specs/` at `v1.15.0` | https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/docs |
| Node.js | `>=20.19.0` for npm, pnpm, yarn and bun installs; the standalone binary needs no Node.js | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/installation.md |
| Windows | Windows 10+ binaries `openspec-windows-x64.exe` and `-arm64.exe`, PowerShell installer; no breaking change labelled from v1.13.0 to v1.15.0 (medium confidence, L2) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/installation.md |
| Stability policy | (unverified) | page not recorded; checked the releases page and cli.md, no policy found (https://github.com/Fission-AI/OpenSpec/releases ; https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md) |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- 8 releases in about 7 weeks (medium confidence, L2: releases page read as condensed highlights; https://github.com/Fission-AI/OpenSpec/releases); patch releases are frequent, so pin 1.15.0 and re-check the releases page before an upgrade.
- No versioning or stability policy is published for the core CLI (unverified). Stores and worksets are beta ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Delta format and archive merge order](./blueprints/delta-format-and-archive.md)
- [Ask-first decisions and the /opsx overlap table](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [CLI lifecycle, layout and inventory](./blueprints/cli-lifecycle.md)
- [Verification Loop](./blueprints/cli-lifecycle.md#verification-loop)
- [Non-interactive use, CI and Windows](./blueprints/non-interactive-and-windows.md)
- [Docs versus validator conflicts (C1-C6)](./blueprints/doc-vs-validator-conflicts.md)
- [Migration notes 1.13 to 1.15](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use OpenSpec's format and the `openspec` CLI only; never the generated `/opsx:*` commands or `openspec-*` skills.** User decision G1, verbatim: "Format + CLI, our agents (Recommended)". Overlap table and the update behaviour of those files: [ask-first decisions](./blueprints/ask-first-decisions.md#opsx-overlap-table). See [patterns](./blueprints/always-do-patterns.md#1-format-and-cli-only).
- **Where the docs and the validator or schema conflict, follow `schema.yaml`, the templates and the validator, and cite both.** Family fact verified 2026-10-28 ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)). See [conflicts](./blueprints/doc-vs-validator-conflicts.md).
- **Start every live spec with `## Purpose` and `## Requirements`.** The validator errors without both headers ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)). See [patterns](./blueprints/always-do-patterns.md#2-live-spec-skeleton).
- **Put the literal word `SHALL` or `MUST` in every requirement.** The validator message is "Requirement must contain SHALL or MUST keyword" ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)). See [patterns](./blueprints/always-do-patterns.md#3-shall-or-must).
- **Write each scenario under a `#### Scenario:` header; the schema and the templates use bold `**WHEN**` / `**THEN**` / `**AND**` bullets.** The schema requires exactly 4 hashtags (family fact, orchestrator-verified 2026-10-28: [schema.yaml](https://github.com/Fission-AI/OpenSpec/blob/v1.15.0/schemas/spec-driven/schema.yaml)). See [patterns](./blueprints/always-do-patterns.md#4-scenarios).
- **Open every proposal with `## Why` and `## What Changes`.** The validator requires both ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)). See [patterns](./blueprints/always-do-patterns.md#5-proposal-headings).
- **Write deltas under `## ADDED|MODIFIED|REMOVED|RENAMED Requirements`; a MODIFIED entry is the entire requirement block with all scenarios.** Partial content "loses detail at archive time" ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)). See [delta format](./blueprints/delta-format-and-archive.md).
- **Give REMOVED entries `**Reason**:` and `**Migration**:`, and RENAMED entries `- FROM:` / `- TO:` lines.** Family fact verified 2026-10-28, High ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)). See [delta format](./blueprints/delta-format-and-archive.md#removed).
- **Track tasks as `- [ ] X.Y Task description` checkboxes under numbered `## N.` groups.** ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)). See [patterns](./blueprints/always-do-patterns.md#7-tasks-format).
- **Archive with an explicit change name and `--yes`: `openspec archive <id> --yes`.** Without a terminal and without `--yes`, archive "stops before changing anything" and exits 1 (verbatim quote in the register, [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)). See [patterns](./blueprints/always-do-patterns.md#9-archive).
- **Pin 1.15.0** ([releases/tag](https://github.com/Fission-AI/OpenSpec/releases/tag/v1.15.0)). The pin check is in the [Verification Loop](./blueprints/cli-lifecycle.md#verification-loop).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Repo bootstrap (`init`) | A: `openspec init --tools none`, agents only (G1 default). B: `--tools claude`, adds `.claude/skills/openspec-*` and `.claude/commands/opsx/` for a human. C: create folders by hand (unverified). What `--tools none` writes is (unverified). `init` is listed as human-only. [Details](./blueprints/ask-first-decisions.md#c1-repo-bootstrap) | "Does a human also want the `/opsx:*` helpers, or agents only?" |
| Install channel and pinning | Standalone binary (checksum-verified, no Node), npm (Node 20.19.0+), manual download. PowerShell pin syntax is (medium confidence); npm `@1.15.0` pin is (medium confidence). Never run the installer without an explicit yes. [Details](./blueprints/ask-first-decisions.md#c2-install-channel-and-pinning) | "Which channel, and may I run it?" |
| Sync during a change vs archive only | Archive-only is the default. A sync is the `/opsx:sync` skill and no CLI subcommand is documented for it (medium confidence, absence of evidence). `--skip-specs` moves a change without touching specs. [Details](./blueprints/ask-first-decisions.md#c3-sync-before-archive-or-archive-only) | "Must live specs reflect this change before archive?" |
| Change with no spec impact | Add a delta, or set `skip_specs: true` in the change's `.openspec.yaml`; zero deltas fail validation without it. [Details](./blueprints/ask-first-decisions.md#c4-change-without-spec-impact) | "Does the change alter observable behaviour?" |
| Reading results | `validate --json` field names differ between pages (medium confidence); `archive --json` support is (unverified); `archive --yes` with incomplete tasks is (unverified). [Details](./blueprints/non-interactive-and-windows.md#json-and-result-reading) | "Which result channel does the handoff script read?" |
| Validate before every archive; validate command form and version check (medium confidence, L1) | Validating before every archive is the recommended sequence, not a High rule (see [patterns](./blueprints/always-do-patterns.md#8-machine-use)). Sequence: run validate, and once validation is clean run `openspec archive <id> --yes`. One validate form is used everywhere: `openspec validate <id> --type change --strict --json --no-interactive`, with the exit code as the gate. `openspec --version` confirms the 1.15.0 pin. Both come from cli.md, read through a summarising fetch with no recorded quote. A: use them as written. B: check `openspec validate --help` and `openspec --version` once on the installed CLI first. I recommend B for a first use. [Register](./blueprints/unverified-and-risks.md#tag-to-register-mapping) | "May I use this validate form before it is checked against the installed 1.15.0 CLI?" |
| Reading validate results and exit codes (medium confidence, L1 and L2) | Exit `0` success and `1` error, including validation failure: cli.md was read through a summarising fetch with no recorded quote (medium confidence, L1). In `validate --json` mode stdout is one JSON document: agent-contract.md was read condensed (medium confidence, L2). A: gate on the exit code and read `items`, falling back to `results`. B: also confirm once against a real 1.15.0 run before the handoff script relies on it. I recommend B for a first use, then A. [Register](./blueprints/unverified-and-risks.md) | "May the handoff script rely on the exit code and JSON shape before it is checked against a 1.15.0 run?" |
| Profile and delivery for a human | Core vs expanded workflows; the delivery config key is (unverified). [Details](./blueprints/ask-first-decisions.md#c5-profile-and-delivery-for-a-human) | "Does a human need `/opsx:verify` or other expanded workflows?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Send a MODIFIED delta with only the changed words; archive replaces the whole requirement ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)) | Repeat the entire requirement block with every scenario ([conventions](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md)) |
| Rename a requirement with REMOVED plus ADDED, or put it under MODIFIED with the old name ([conventions](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md)) | Use `## RENAMED Requirements` with FROM/TO; put content changes under MODIFIED with the new header ([conventions](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md)) |
| Run `openspec archive` in a script with no change name or no `--yes`: it "stops before changing anything" and exits 1 ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)) | `openspec archive <id> --yes` ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)) |
| Tell an agent to run `/opsx:archive` or any generated `/opsx:*` command ([supported-tools](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/supported-tools.md)) | `openspec archive <id> --yes` ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)); the validate step before it is in the Ask First row "Validate before every archive; validate command form and version check" |
| Write a requirement without SHALL or MUST, or scenario bullets without a `#### Scenario:` header ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)) | A SHALL or MUST sentence plus `#### Scenario:` with bold WHEN/THEN bullets ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)) |
| Use `## Intent` / `## Scope` / `## Approach` as proposal headings ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)) | `## Why` and `## What Changes` ([proposal template](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/templates/proposal.md)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Live specs | `openspec/specs/<capability>/spec.md` | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md |
| Change folder | `openspec/changes/<change-name>/` with `proposal.md`, `design.md`, `tasks.md`, optional `.openspec.yaml`, `specs/<capability>/spec.md` | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md |
| Archive target | `openspec/changes/archive/YYYY-MM-DD-<change-name>/` (medium confidence, L2: cli-archive read as paraphrased scenarios) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md |
| Validate command | `openspec validate <id> --type change --strict --json --no-interactive` (medium confidence, L1) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md |
| Version check | `openspec --version` (medium confidence, L1) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md |
| Bold WHEN/THEN | schema and templates use it; parser enforcement is (unverified), I1 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml |
| Delta headers | `## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements`, `## RENAMED Requirements` | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml |
| Exit codes | `0` success, `1` error, `130` for `config profile` cancelled with Ctrl+C (medium confidence, L1) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md |
| `validate --concurrency` | default 6, env `OPENSPEC_CONCURRENCY` (medium confidence, L1) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md |
| Non-interactive switches | `--no-interactive` on `show` and `validate`; `OPEN_SPEC_INTERACTIVE=0`; `CI` (medium confidence, L1) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md |
| Purpose minimum | 50 characters, warning | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts |
| Why minimum / maximum | 50 characters (error) / 1000 characters ("should not exceed") | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts |
| Requirement text maximum | 500 characters, warning; `--strict` fails on it since v1.14.1 (medium confidence, L2: releases page read as condensed highlights) | https://github.com/Fission-AI/OpenSpec/releases |
| Deltas per change | 10 ("Consider splitting"); severity (unverified) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts |
| Default schema | `spec-driven` (`openspec/config.yaml` in the customization page is an example) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/customization.md |
| Telemetry opt-out | `openspec config set telemetry.enabled false`, `OPENSPEC_TELEMETRY=0` or `DO_NOT_TRACK=1`; `CI` disables it (medium confidence, L1) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md |

## External Resources

All fetched 2026-10-28.

- Repo and docs at the tag: https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/docs
- CLI reference: https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md
- Agent contract: https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md
- Spec-driven schema: https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml
- Releases: https://github.com/Fission-AI/OpenSpec/releases
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
