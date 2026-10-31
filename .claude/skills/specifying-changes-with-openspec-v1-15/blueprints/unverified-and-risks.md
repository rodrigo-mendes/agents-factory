# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 90%, a deep run using all 3 iterations, 7 triangulated claims, 6 unverified and 5 irresolvable items (the score rests on an estimated claim count). Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Resolved items](#resolved-items)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- OpenSpec 1.15.0 was tagged 2026-10-24 and carries the GitHub "Latest" badge on 2026-10-28 (High; https://github.com/Fission-AI/OpenSpec/releases/tag/v1.15.0). No v1.15.1 or later existed on 2026-10-28 (family fact).
- 8 releases in about 7 weeks (medium confidence, L2: releases page read as condensed highlights; https://github.com/Fission-AI/OpenSpec/tags and https://github.com/Fission-AI/OpenSpec/releases). Pin 1.15.0 (confirm with `openspec --version`, medium confidence, L1), and re-check for a v1.15.x release before authoring against a newer version.
- No versioning or stability policy is published for the core CLI (U1). No release from v1.13.0 to v1.15.0 is labelled breaking, but several made validation stricter ([migration notes](./migration-notes.md#stricter-behaviour-that-matters-to-automation)).
- Stores and worksets are beta: "Command names, flags, and JSON shapes may change between releases" (High; https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md). Out of scope.
- Known inconsistencies not yet fixed (High; https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md): mixed snake_case and camelCase keys, only `validate` carries `version`, deprecated `change`/`spec` payloads.
- No active CVE was found (medium confidence, absence of evidence); v1.14.3 removed an unpatched `braces` dependency (medium confidence, L2: releases page, condensed highlights).
- The standalone installer script is fetched from the `main` branch, not the tag (High; https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/installation.md).

## Unverified items

5 unverified items (do not assert them). The research listed 6; its U4 (absence of an `openspec diff` command) is an absence-of-evidence claim and is carried as M7 below, so the id U4 is retired.

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | A versioning or stability policy for the core CLI | Pin the version; re-check releases before upgrading |
| U2 | Severity of `MAX_DELTAS_PER_CHANGE = 10` ("Consider splitting...") | Split changes with more than 10 deltas anyway |
| U3 | Behaviour of `archive --yes` with incomplete `- [ ]` tasks (C4) | Check every task before archiving |
| U5 | Whether the CLI accepts a root with no `openspec/config.yaml` (hand-made folders) | Have a human run `openspec init --tools none` once |
| U6 | Whether `openspec init --tools claude` writes to `CLAUDE.md` (supported-tools is silent) | Inspect the diff after a human runs `init` |

## Irresolvable items

5 irresolvable items. The research could not settle them within its 3 iterations (the sources are silent or disagree and the source files were not fetched). In the skill text they carry the tag (unverified); they are not repeated under unverified items.

| ID | Item | Impact and workaround |
|---|---|---|
| I1 | Whether the 1.15.0 parser rejects non-bold WHEN/THEN steps (C1). Follow-up: `src/core/parsers/*` at tag v1.15.0 | Low: always emit bold |
| I2 | Whether `openspec archive` accepts `--json` in 1.15.0 (C6). Follow-up: `src/cli/index.ts` at the tag | Moderate: gate on the exit code, then check `openspec/changes/archive/<date>-<id>/` exists |
| I3 | Whether `openspec init --tools none` creates `openspec/config.yaml` and which folders. Follow-up: `openspec/specs/cli-init/spec.md` at the tag | Moderate for a bootstrap script: a human runs `init` once; the script checks that `openspec/specs` and `openspec/changes` exist |
| I4 | The exact checks performed by `/opsx:verify`. Follow-up: `openspec/specs/opsx-verify-skill/spec.md` at the tag | Low (human-only per G1): our quality gate defines its own checks |
| I5 | The global config key for delivery mode (skills, commands, both) and the Windows global config path. Follow-up: `openspec/specs/global-config/spec.md` at the tag | Low: `openspec config path` and `openspec config list` on the machine |

## Medium-confidence items

7 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | `validate --json` field names (`items` vs `results`) | cli.md and agent-contract.md disagree (C3); parse defensively |
| M2 | PowerShell form `$env:OPENSPEC_VERSION='v1.15.0'; irm ... \| iex` | installation.md names the variable but shows no PowerShell syntax |
| M3 | `npm install -g @fission-ai/openspec@1.15.0` | installation.md documents only `@latest`; the pin is standard npm syntax |
| M4 | Workflow-to-skill name mapping other than `/opsx:apply` to `openspec-apply-change` | Inferred from names in supported-tools |
| M5 | Deprecation of `openspec change ...` / `openspec spec ...` subcommands | agent-contract.md states it; the validator guide in constants.ts still mentions `openspec change show` |
| M6 | No documented CLI subcommand for sync (absence of evidence) | `/opsx:sync` is a skill; cli.md lists no sync subcommand |
| M7 | No `openspec diff` command (absence of evidence; formerly U4). Workaround: `show --deltas-only` | The v1.15.0 CLI reference lists none |

## Coverage limits

5 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | Most pages were read through a summarising fetch tool; text in quotes or backticks is verbatim, other wording is a paraphrase by the tool. A claim that rests on such a paraphrase with no recorded quote (for example the exit-code contract of `validate`: `0` success, `1` error) carries (medium confidence, L1). Exception: the quote "stops before changing anything" for `archive` without a terminal and without `--yes` is recorded in the research (N3, source S4), so that claim is High |
| L2 | Read only in part: releases (condensed highlights; per-release pages not read except v1.15.0), agent-contract.md (condensed), getting-started.md (code blocks summarized), openspec-conventions spec (excerpts), cli-archive spec (paraphrased scenarios), schema.yaml (summarized plus short verbatim snippets), templates/spec.md (structure only). Claims taken from these partly read or condensed pages without a recorded verbatim quote (`--json` stdout contract, archive merge, requirement-length strictness since v1.14.1, FROM/TO checks since v1.13.1, every statement taken from the releases page) carry (medium confidence, L2), per family rule 13. The REMOVED/RENAMED entry format is not in this list: it is a High family fact verified by the orchestrator on 2026-10-28 |
| L3 | https://www.npmjs.com/package/@fission-ai/openspec/v/1.15.0 returned HTTP 403 and was not read; version, license and engines come from the registry JSON and package.json |
| L4 | docs/examples.md, editing-changes.md, reviewing-changes.md, team-workflow.md and existing-projects.md exist at the tag and were not read (directory listing only) |
| L5 | The listing of `openspec/specs` at the tag may be truncated ("View all files"); the source tree `src/core/validation` was a listing only |

## Resolved items

- Verbatim quote recorded in the research (research_OpenSpec_v1.15.md, N3, source S4, cli.md): without a terminal and without `--yes`, archive "stops before changing anything" and exits 1. The claim is High in every file of this skill.
- The REMOVED `**Reason**:`/`**Migration**:` and RENAMED `- FROM:`/`- TO:` entry format is a High family fact (schema.yaml, verified by the orchestrator 2026-10-28); it is stated High everywhere.
- The OpenSpec row of the family facts tagged MODIFIED and REMOVED delta sections as unverified. The research confirms them, and RENAMED, from schema.yaml, the conventions spec, writing-specs.md and the cli-validate spec; the family file was not edited.
- Conflicts C2 (proposal headings) and C5 (RFC 2119 words) are resolved by the validator-wins rule. C4 is read as warn plus confirm; only the `--yes` branch stays open (U3). See [conflicts](./doc-vs-validator-conflicts.md).
- Release year: 2026-10-24, from the tags page. The Node requirement and licence (MIT) come from the registry JSON and package.json.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) stability policy | SKILL.md Version Context and risk; migration-notes | U1 |
| (unverified) severity of the 10-delta limit | SKILL.md Quick Reference; non-interactive thresholds | U2 |
| (unverified) `archive --yes` with incomplete tasks | SKILL.md Ask First; non-interactive; conflicts C4 | U3 |
| (unverified) root without `config.yaml` | SKILL.md Ask First (repo bootstrap, option C); ask-first C1 | U5 |
| (unverified) `init --tools claude` writes `CLAUDE.md` | ask-first C1 | U6 |
| (unverified) parser rejects non-bold steps | SKILL.md Quick Reference; always-do 4; conflicts C1 | I1 |
| (unverified) `archive --json` | SKILL.md Ask First; non-interactive; conflicts C6 | I2 |
| (unverified) what `init --tools none` writes | SKILL.md Ask First; ask-first C1 | I3 |
| (unverified) `/opsx:verify` checks | ask-first overlap table | I4 |
| (unverified) delivery config key, Windows config path | SKILL.md Ask First; ask-first C5; non-interactive Windows | I5 |
| (medium confidence) `validate --json` field names | SKILL.md Ask First; always-do 8; non-interactive; conflicts C3 | M1 |
| (medium confidence) PowerShell pin syntax | SKILL.md Ask First; ask-first C2 | M2 |
| (medium confidence) npm `@1.15.0` pin | SKILL.md Ask First; ask-first C2; migration-notes | M3 |
| (medium confidence) workflow-to-skill names | ask-first overlap table | M4 |
| (medium confidence) deprecated `change`/`spec` subcommands | non-interactive | M5 |
| (medium confidence, absence of evidence) no CLI sync subcommand | SKILL.md Ask First; ask-first C3 | M6 |
| (medium confidence, absence of evidence) no `openspec diff` command | cli-lifecycle | M7 |
| (medium confidence, L2) condensed or partly read page, no recorded quote | SKILL.md Version Context, Ask First (reading validate results) and Quick Reference (requirement text maximum, archive target); always-do 8 and 9; never-do F2 (applied-first order); delta-format-and-archive (RENAMED checks, Archive merge order); evaluation 1 and 5; never-do F2, F4; ask-first C1, C4; non-interactive (switches, thresholds, Windows, Archive recovery, security); migration-notes (all release rows) | L2 |
| (medium confidence, L1) summarising-fetch paraphrase, no recorded quote | SKILL.md Ask First (validate command form and version check; reading validate results), Never Do (validate alternative) and Quick Reference (exit codes, validate command, version check, `--concurrency`, non-interactive switches, telemetry); always-do 8; never-do F4; non-interactive (JSON reading, exit codes); cli-lifecycle verification loop; conflicts C3; ask-first overlap table (`openspec update` regeneration and pruning) | L1 |
| (unverified) and (medium confidence) tags inside scenario expectations | evaluation-scenarios | I1, I2, I3, U1, U3, M1 |

## Source Bibliography

All read 2026-10-28; tag v1.15.0 dated 2026-10-24 (tags page). Community sources: none used (official only). Base for raw pages: `https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/`.

| ID | Source | Read status |
|---|---|---|
| S1 | https://github.com/Fission-AI/OpenSpec/blob/v1.15.0/README.md | full, summarizing fetch |
| S2 | https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/docs | listing only |
| S3 | https://github.com/Fission-AI/OpenSpec/releases (v1.13.0 to v1.15.0 notes) | condensed highlights, partly read (L2) |
| S4 | base + `docs/cli.md` | full, summarizing fetch |
| S5 | base + `docs/concepts.md` | full, summarizing fetch |
| S6 | base + `docs/writing-specs.md` | full, summarizing fetch |
| S7 | base + `docs/agent-contract.md` | condensed, partly read (L2) |
| S8 | base + `docs/supported-tools.md` | Claude Code row verbatim, rest summarized |
| S9 | base + `docs/installation.md` | full, summarizing fetch |
| S10 | base + `docs/opsx.md` | full, summarizing fetch |
| S11 | base + `docs/getting-started.md` | code blocks summarized, partly read (L2) |
| S12 | https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/openspec/specs | listing, may be truncated (L5) |
| S13 | base + `openspec/specs/openspec-conventions/spec.md` | excerpts only, partly read (L2) |
| S14 | base + `openspec/specs/cli-archive/spec.md` | paraphrased scenarios, partly read (L2) |
| S15 | base + `schemas/spec-driven/schema.yaml` | summarized plus short verbatim snippets, partly read (L2) |
| S16 | base + `schemas/spec-driven/templates/spec.md` | structure only, partly read (L2) |
| S17 | base + `openspec/specs/cli-validate/spec.md` | full, summarizing fetch |
| S18 | base + `schemas/spec-driven/templates/proposal.md` | headings verbatim |
| S19 | https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/src/core/validation | listing (includes `task-checkboxes.ts`, `task-numbering.ts`) |
| S20 | base + `src/core/validation/constants.ts` | constants and messages verbatim |
| S21 | https://www.npmjs.com/package/@fission-ai/openspec/v/1.15.0 | HTTP 403, not read (L3) |
| S22 | https://github.com/Fission-AI/OpenSpec/releases/tag/v1.15.0 | notes summarized; asset names not listed |
| S23 | base + `docs/customization.md` | full, summarizing fetch |
| S24 | https://registry.npmjs.org/@fission-ai/openspec/1.15.0 | version, license, engines, bin, tarball |
| S25 | base + `package.json` | name, version, license, engines, bin, type |
| S26 | base + `docs/migration-guide.md` | full, summarizing fetch |
| S27 | https://github.com/Fission-AI/OpenSpec/tags | dates with year |
| S28 | base + `docs/troubleshooting.md` | full, summarizing fetch |

**Family facts (orchestrator-verified 2026-10-28)**: https://github.com/Fission-AI/OpenSpec/blob/v1.15.0/schemas/spec-driven/schema.yaml and https://github.com/Fission-AI/OpenSpec/releases (delta format; no v1.15.1 or later); the docs-versus-validator rule C1 to C6. User decision G1, verbatim: "Format + CLI, our agents (Recommended)".
