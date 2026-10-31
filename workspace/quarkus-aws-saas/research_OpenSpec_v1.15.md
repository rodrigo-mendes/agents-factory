# Research — OpenSpec v1.15.0 (format + CLI, driven by our own agents)

> Unit U9 → future skill `specifying-changes-with-openspec-v1-15` (package `handoff-core`).
> G1 decision (user, verbatim): "Format + CLI, our agents (Recommended)". Our orchestrator,
> the spec-synchronizer agent and the handoff scripts drive the process. OpenSpec contributes
> the folder/delta **format** and the `openspec` **CLI**. The `/opsx:*` commands and the
> `openspec-*` skills are documented here only as optional tools for a human.
> All sources were read on **2026-10-28**. Source IDs `[Sn]` resolve in the Source Bibliography.
> Most pages were read through a summarizing fetch. Text in backticks or quotes is verbatim.
> Everything else is a faithful paraphrase. Pages read only in part are flagged in the Bibliography.
> Family facts and rules applied: `_family_facts_v3.40.md` (OpenSpec row) and `_family_rules_v3.40.md` rules 8–12.

## Metadata

```yaml
Full_Name: OpenSpec (Fission-AI/OpenSpec), npm package @fission-ai/openspec
Target_Version: 1.15.0
Release_Date: 2026-10-24            # tags page [S27]; releases page shows "24 Oct" without a year [S3][S22]
Support_Status: Active — v1.15.0 carries the GitHub "Latest" badge on 2026-10-28 [S22]; no LTS/EOL policy is published (unverified)
License: MIT                         # [S1][S24][S25]
Node_Requirement: ">=20.19.0" for npm/pnpm/yarn/bun installs; the standalone binary needs no Node.js  # [S9][S24][S25]
Primary_Docs: https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/docs   # mirrored at openspec.dev/docs [S1]
Official_Repo: https://github.com/Fission-AI/OpenSpec
Registry: https://registry.npmjs.org/@fission-ai/openspec/1.15.0
Research_Date: 2026-10-28
Domain_Complexity: Standard          # file format + CLI contract + CI usage; no auth/crypto surface
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 7
Unverified_Count: 6
Irresolvable_Count: 5
Research_Quality_Score: 90%          # ≈ (≈110 claims − 6 unverified − 5 irresolvable) / ≈110; the claim count is an estimate
```

## Executive Summary

OpenSpec is a spec-driven development (SDD) tool. It keeps living specs under `openspec/specs/<capability>/spec.md`. Each proposed change lives in `openspec/changes/<change-name>/`, with `proposal.md`, `design.md`, `tasks.md`, an optional `.openspec.yaml`, and delta specs under `specs/<capability>/spec.md` [S5][S11]. `openspec archive` applies the deltas to the live specs and moves the change folder to `openspec/changes/archive/YYYY-MM-DD-<change-name>/` [S14][S6]. For our use, the binding parts are the **file format** (requirements, scenarios, delta sections) and the **CLI contract** (`validate`, `list`, `show`, `status`, `instructions`, `archive`). The CLI contract has one-JSON-document-per-call output and exit codes 0, 1 and 130 [S4][S7]. The `/opsx:*` slash commands and the `openspec-*` skills that `openspec init` writes for Claude Code (`.claude/skills/openspec-*/SKILL.md`, `.claude/commands/opsx/<id>.md`) are optional for humans [S8]. `openspec init --tools none` skips all tool configuration [S4][S8].

**What changed between v1.13 and v1.15.0** [S3][S22]:
- **v1.13.x hardened archive:**
  - v1.13.0 stopped rewriting fenced code and made `*`/`+` removals and renames take effect.
  - v1.13.1 refuses mismatched `RENAMED` FROM/TO lines and case-only name differences.
  - v1.13.2 fixed archive on Windows (no leftover `.openspec-archive.lock`; completes instead of rolling back when Windows blocks a rename).
- **v1.14.x added and tightened tooling:**
  - v1.14.0 added `list --archived/--all`, requirement and scenario names in `show --json`, and stricter `validate --strict` on unknown `.openspec.yaml` keys.
  - v1.14.1 turned over-500-character requirements into a warning, so `--strict` fails on them.
  - v1.14.2 made "delta text would be dropped" a warning that also fails `--strict`.
  - v1.14.3 fixed `validate --all` hanging in pre-commit hooks; `OPEN_SPEC_INTERACTIVE=0`/`CI` turn off the spinner.
- **v1.15.0:**
  - Standalone binaries that need no Node.js, for macOS, Linux and Windows on x64/arm64, with `SHA256SUMS`.
  - `openspec update --dry-run [--json]`.
  - Faster `--json` startup.
  - `/opsx:verify` matches REMOVED requirements to their baseline by exact name.

No release in that range is labelled as breaking [S3].

**Three critical patterns:**
1. Write requirements as `### Requirement: <name>` containing `SHALL` or `MUST`, each with at least one `#### Scenario:` that uses `- **WHEN**` / `- **THEN**` / `- **AND**` bullets [S15][S20][S13].
2. In deltas, use `## ADDED|MODIFIED|REMOVED|RENAMED Requirements`. A MODIFIED entry is the complete requirement, with every scenario, never a diff. A REMOVED entry carries `**Reason**` and `**Migration**`. RENAMED uses `- FROM:` / `- TO:` lines [S13][S15][S6][S17].
3. Automate with `openspec validate --all --strict --json --no-interactive` and `openspec archive <change> --yes`. Decide on exit codes, not prose [S4][S7][S28].

The tier is **Standard**: there is a strict text format, a CLI with a JSON/exit-code contract, and CI interactivity pitfalls, but no security-critical surface beyond telemetry and the install supply chain.

> **Family fact reconciliation.** The OpenSpec row in `_family_facts_v3.40.md` tags "MODIFIED/REMOVED delta sections" as unverified. This research **confirms** them, plus RENAMED, from [S13], [S15], [S6] and [S17]. That resolves the open item rather than contradicting the fact. The rest of the row (MIT; the layout; `.claude/skills/openspec-*` and `/opsx:<id>`) agrees with [S1], [S5] and [S8]. The family file was not edited.

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**A1. Live spec skeleton: `## Purpose` + `## Requirements`**
> Confidence: 🟢 High | [✓✓ Triangulated | S5 concepts.md (2026-10-28) + S20 constants.ts GUIDE_MISSING_SPEC_SECTIONS (2026-10-28)]
- Why: the validator errors with "Missing required sections. Expected headers: \"## Purpose\" and \"## Requirements\"" [S20][S17]. "Purpose section is too brief (less than 50 characters)" is a warning [S20]. "Spec must have at least one requirement" is an error [S20].
- Code (OpenSpec 1.15.0):
  ```markdown
  # Orders Specification

  ## Purpose
  Accepts, prices and tracks customer orders for a single tenant end to end.

  ## Requirements

  ### Requirement: Order creation
  The system SHALL create an order when a valid cart is submitted.

  #### Scenario: Valid cart
  - **WHEN** a tenant user submits a cart with at least one item
  - **THEN** the system creates an order in status PENDING
  - **AND** returns the order id
  ```
- Source: [S5], [S20], [S17] (2026-10-28). The spec title form `# <Name> Specification` comes from [S5] and [S13].

**A2. Requirement wording must contain `SHALL` or `MUST`**
> Confidence: 🟢 High | [✓✓ Triangulated | S20 constants.ts (2026-10-28) + S15 schema.yaml specs instruction (2026-10-28)]
- Why: the validator message is "Requirement must contain SHALL or MUST keyword" [S20]. A requirement body without the literal English keywords produces a warning, which fails `--strict` [S17]. [S6] and [S5] also allow SHOULD/MAY as RFC 2119 words, but only SHALL/MUST satisfy the check. Use SHALL/MUST in every requirement, and put SHOULD/MAY nuance into additional sentences.
- Code:
  ```markdown
  ### Requirement: Session timeout
  The system SHALL expire a session after 30 minutes of inactivity.
  ```
- Source: [S20], [S15], [S6] (2026-10-28).

**A3. Scenarios use exactly `####` and bold step keywords**
> Confidence: 🟢 High for `#### Scenario:` [✓✓ S15 + S20]; 🟡 Medium for the bold markup being *enforced*
- Why: [S15] says "CRITICAL: Scenarios MUST use exactly 4 hashtags (`####`)". Bullets without a scenario header produce the warning "Scenarios must use '#### Scenario:' headers" [S17]. "Requirement must have at least one scenario" is an error [S20].
- Markup: the shipped template, the validator guides and the repo's own specs all use `- **WHEN** …`, `- **THEN** …`, `- **AND** …` [S15][S20][S13][S14]. Whether the parser *rejects* non-bold steps is **(unverified)**; see contradiction C1. The bold form is the safe superset.
- Code:
  ```markdown
  #### Scenario: Idle timeout
  - **WHEN** 30 minutes pass with no activity
  - **THEN** the session is invalidated
  - **AND** the user must re-authenticate
  ```
- Source: [S15], [S20], [S13], [S17] (2026-10-28).

**A4. Delta sections and their exact content**
> Confidence: 🟢 High | [✓✓ Triangulated | S13 openspec-conventions spec + S15 schema.yaml + S6 writing-specs.md (all 2026-10-28)]
- Headers: `## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements`, `## RENAMED Requirements` [S13][S15][S20 GUIDE_NO_DELTAS].
- ADDED: full requirement blocks with scenarios [S5][S13].
- MODIFIED: "include the complete modified requirement (not a diff)" [S13]. [S15] says MODIFIED "must include the full updated requirement block" and warns "Common pitfall: Using MODIFIED with partial content loses detail at archive time." Validation errors when a MODIFIED requirement omits scenarios the main spec still has [S17][S28].
- REMOVED: the requirement header, plus `**Reason**:` and `**Migration**:` lines [S15]. [S13] says "include reason for removal" and "document any migration path if applicable".
- RENAMED: `- FROM: \`### Requirement: Old Name\`` / `- TO: \`### Requirement: New Name\``. If the content also changes, add the requirement under MODIFIED using the **new** header [S13]. Since v1.13.1, archive refuses mismatched FROM/TO lines [S3].
- New capability: the delta may open with `## Purpose` (at least 50 characters). It seeds the live spec's Purpose and is ignored for an existing spec. If it is missing, archive writes a `TBD - created by archiving change …` placeholder [S6][S15][S20].
- Code (OpenSpec 1.15.0 delta file `openspec/changes/<id>/specs/auth/spec.md`):
  ```markdown
  ## RENAMED Requirements
  - FROM: `### Requirement: Login`
  - TO: `### Requirement: Password login`

  ## MODIFIED Requirements

  ### Requirement: Session timeout
  The system SHALL expire a session after 15 minutes of inactivity.

  #### Scenario: Idle timeout
  - **WHEN** 15 minutes pass with no activity
  - **THEN** the session is invalidated

  ## REMOVED Requirements

  ### Requirement: Legacy export
  **Reason**: Replaced by new export system
  **Migration**: Use new export endpoint at /api/v2/export

  ## ADDED Requirements

  ### Requirement: Two-factor login
  The system MUST require a second factor for administrator accounts.

  #### Scenario: Admin login
  - **WHEN** an administrator submits valid credentials
  - **THEN** the system requests a one-time code
  ```
- Source: [S13], [S15], [S6], [S17], [S3] (2026-10-28). The REMOVED Reason/Migration lines are quoted from [S15]. The FROM/TO lines are quoted from [S13].

**A5. Know the archive merge order**
> Confidence: 🟢 High | [✓✓ Triangulated | S13 openspec-conventions (order) + S6 writing-specs.md (append/replace/drop semantics) (2026-10-28)]
- Order: (1) RENAMED first; (2) REMOVED by normalized header match; (3) MODIFIED replaced by normalized header match, using the new names if renamed; (4) ADDED appended. All MODIFIED headers must exist in the current spec [S13].
- Further rules from [S14]:
  - A delta that would create duplicate headers aborts.
  - A main spec that already has duplicate headers is rejected before anything is applied.
  - The target folder is named `YYYY-MM-DD-[change-name]` using the current date. A name that already has a date prefix is kept. An existing target fails instead of being overwritten.
- Capability retirement: removing a capability's last requirement deletes `openspec/specs/<capability>/spec.md` only when `.openspec.yaml` has `retire_capabilities: true`; otherwise archive aborts. Retirement is also refused if the spec has extra content such as `## Notes` [S6][S4].
- Source: [S13], [S6], [S14], [S4] (2026-10-28).

**A6. Proposal uses `## Why` + `## What Changes`**
> Confidence: 🟢 High | [✓✓ Triangulated | S18 templates/proposal.md + S20 constants.ts (2026-10-28)]
- Why: the validator requires "## Why" and "## What Changes" (GUIDE_MISSING_CHANGE_SECTIONS) [S20][S17]. "Why section must be at least 50 characters". A Why over 1000 characters gets "should not exceed" [S20]. "What Changes section cannot be empty" [S20]. The template headings are `# Proposal`, `## Why`, `## What Changes`, `## Capabilities` (`### New Capabilities`, `### Modified Capabilities`), `## Impact` [S18]. See contradiction C2 about [S5].
- Code:
  ```markdown
  # Proposal

  ## Why
  Administrators need stronger login protection after the Q3 security review findings.

  ## What Changes
  - Add a second factor for administrator logins.

  ## Capabilities
  ### New Capabilities
  ### Modified Capabilities
  - auth

  ## Impact
  Auth service and login UI.
  ```
- Source: [S18], [S20], [S17] (2026-10-28).

**A7. `tasks.md` checkbox format**
> Confidence: 🟢 High | [✓✓ Triangulated | S15 schema.yaml tasks instruction + S5 concepts.md + S14 cli-archive (2026-10-28)]
- Rule: "Each tracked task MUST be a checkbox: `- [ ] X.Y Task description`" [S15]. Groups go under numbered `## N. <Group>` headings [S5][S15]. A box containing only `x`, in either case and with any spacing, counts as done. `- [~]` and `- []` count as unfinished [S15]. Archive lists incomplete `- [ ]` tasks and asks for confirmation (default No) [S14]. `openspec validate --archived` fails if an archived change has unchecked tasks [S4][S28]. The source tree has `task-checkboxes.ts` and `task-numbering.ts` validators [S19].
- Code:
  ```markdown
  # Tasks

  ## 1. Auth backend
  - [x] 1.1 Add TOTP secret column (verify: migration test passes)
  - [ ] 1.2 Enforce second factor for admins (verify: scenario "Admin login" test)

  ## Workflow follow-up
  - Archive after merge
  ```
- Source: [S15], [S5], [S14], [S4] (2026-10-28). The `## Workflow follow-up` plain-bullet section comes from [S15].

**A8. Machine use = `--json` + `--no-interactive` + exit codes**
> Confidence: 🟢 High | [✓✓ Triangulated | S4 cli.md + S7 agent-contract.md (2026-10-28)]
- Contract:
  - In `--json` mode stdout holds exactly one pretty-printed JSON document. Prose and spinners go to stderr [S7].
  - JSON mode is strictly non-interactive [S7].
  - Exit codes: `0` success, `1` error (including validation failures, missing files, no root, and `archive` with no terminal and no `--yes`), `130` for `config profile` cancelled with Ctrl+C [S4]; [S7] agrees.
  - `show` and `validate` accept `--no-interactive`. `OPEN_SPEC_INTERACTIVE=0` or a non-TTY stdin also suppresses prompts [S4][S17][S3].
- Code (representative):
  ```bash
  # Representative — adapt to your environment (OpenSpec 1.15.0)
  openspec validate --all --strict --json --no-interactive > validate.json
  echo "exit=$?"        # 0 = all items valid; 1 = at least one invalid item or error
  ```
- Source: [S4], [S7], [S17] (2026-10-28).

### ⚠️ Conditional Patterns

**B1. How to initialise a repo for agent-driven use (no tool integrations)**
> Confidence: 🟡 Medium
- Options:
  - A) `openspec init --tools none` (skip tool configuration) [S4][S8].
  - B) `openspec init --tools claude` (writes `.claude/skills/openspec-*/SKILL.md` and `.claude/commands/opsx/<id>.md`; the default delivery is `both` and the default profile is `core`) [S4][S8].
  - C) Create `openspec/specs/` and `openspec/changes/` by hand, with no `init` (unverified that the CLI accepts a root with no `config.yaml`; [S7] says root detection is "nearest ancestor with `openspec/`").
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A `--tools none` | Agents never depend on generated skills; no `.claude/` writes | Humans lose `/opsx:*` | G1 default: our agents drive |
  | B `--tools claude` | Humans get `/opsx:*` helpers | Adds 6 core skills/commands to `.claude/`, which can overlap our agents | A human also works the flow by hand |
  | C manual folders | No CLI run at setup | Unverified root/config behaviour | Not recommended |

- Notes:
  - [S4] lists `init` among the "Human-only commands". `--tools` makes it non-interactive, and `--force` "auto-clean[s] legacy files without prompting" [S4][S26].
  - Whether `--tools none` still writes `openspec/config.yaml` is **(unverified)**. [S26] says init/update write `openspec/config.yaml` "with a default `schema:`" but does not say whether that applies with `none`.
  - Since v1.13.1 the generated workflows "never create an `openspec/` folder", so `init` must have run first [S3].
- Agent: "Ask the user whether a human also wants the `/opsx:*` helpers (B) or agents only (A, default per G1)."
- Source: [S4], [S8], [S26], [S3], [S7] (2026-10-28).

**B2. Install channel (Windows user)**
> Confidence: 🟢 High for the commands; 🟡 Medium for the PowerShell pinning syntax
- Options:
  - A) Standalone binary, Windows PowerShell: `irm https://raw.githubusercontent.com/Fission-AI/OpenSpec/main/scripts/binary/install.ps1 | iex`. It installs to `%LOCALAPPDATA%\Programs\openspec` and adds that folder to the user `PATH`. No Node.js is needed. The installer verifies the download against `SHA256SUMS` [S9][S1][S22].
  - B) npm: `npm install -g @fission-ai/openspec@latest` (Node ≥ 20.19.0) [S1][S9][S25].
  - C) Manual download of `openspec-windows-x64.exe` / `openspec-windows-arm64.exe` (Windows 10+), renamed to `openspec.exe` and added to `PATH` [S9].
- Pinning:
  - The standalone installer takes `OPENSPEC_VERSION=v1.15.0` [S9]. A PowerShell form such as `$env:OPENSPEC_VERSION='v1.15.0'; irm … | iex` is **(medium confidence)**: [S9] names the variable but shows no PowerShell syntax.
  - For npm, `@fission-ai/openspec@1.15.0` uses standard npm version syntax. [S9] documents only `@latest` **(medium confidence)**.
  - The installer script itself is fetched from the `main` branch, not the tag [S9].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A standalone | No Node; checksum-verified | `irm … | iex` runs a remote script from `main` | Workstations without Node |
  | B npm | Version-pinned via package manager; CI-friendly | Requires Node ≥ 20.19.0 | CI images that already have Node |
  | C manual | Full control; auditable | Manual PATH/update | Locked-down machines |

- Agent: "Ask which channel. Never run the installer yourself (hard constraint: do not install anything)."
- Source: [S9], [S1], [S22], [S25] (2026-10-28).

**B3. Sync before archive vs archive-only**
> Confidence: 🟡 Medium
- Options:
  - A) Archive only. `openspec archive <id> --yes` applies the deltas and moves the folder [S14][S6].
  - B) Sync during the change (the `/opsx:sync` skill merges deltas into `openspec/specs/` "without archiving — the change stays active") [S10]. This is a **skill**, not a documented CLI subcommand in [S4], so our spec-synchronizer would have to re-implement it.
  - C) `openspec archive <id> --skip-specs` moves the change without touching specs [S4][S14].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A archive | One CLI-owned merge with validation | Live specs lag until archive | Default for agents |
  | B sync | Live specs current mid-change | No CLI command; our own merge logic must match [S13] order | Long-running changes needing early spec truth |
  | C skip-specs | Archives docs-only/tooling changes | Specs not updated | Changes with `skip_specs: true` |

- Agent: "Ask whether live specs must reflect an in-flight change before archive."
- Source: [S10], [S14], [S4], [S6], [S13] (2026-10-28).

**B4. Changes with no spec impact**
> Confidence: 🟢 High | [S4 + S20]
- Options: A) add a delta anyway; B) set `skip_specs: true` in the change's `.openspec.yaml`.
- Rules:
  - A change with zero deltas fails validation unless `skip_specs: true` [S4][S20].
  - If `skip_specs` is set but spec files exist under `specs/`, that is an error [S20].
  - `--strict` fails on unrecognized `.openspec.yaml` keys [S3]. Top-level `x-` keys are ignored [S3][S5].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A delta | Traceability | Artificial requirements | Behaviour actually changes |
  | B skip_specs | Honest no-spec refactors | No spec trail | Pure refactor, tooling, docs |

- Agent: "Ask whether the change alters observable behaviour."
- Source: [S4], [S20], [S3], [S5] (2026-10-28).

**B5. Profile and delivery for humans who opt in**
> Confidence: 🟡 Medium
- Core profile workflows: `propose, explore, apply, update, sync, archive`. Expanded workflows: `new, continue, ff, verify, bulk-archive, onboard` [S8][S4].
- Switch with `openspec config profile [preset]`, then `openspec update` [S1][S4].
- `openspec update --dry-run --json` previews without writing (new in v1.15.0) [S4][S22].
- The config key name for "delivery" (skills/commands/both) is not documented on any page read **(unverified)**.
- Agent: "Ask only if a human wants `/opsx:verify` or other expanded workflows."
- Source: [S4], [S8], [S1], [S22] (2026-10-28).

### 🚫 Forbidden Patterns

**N1. Partial MODIFIED deltas (diff-style)**
> Severity: Critical
> Confidence: 🟢 High | [S13 + S15 + S17]
- Why: MODIFIED **replaces** the whole requirement at archive [S6][S13]. "Using MODIFIED with partial content loses detail at archive time" [S15].
- Impact: lost scenarios. Validation errors when MODIFIED omits scenarios the main spec has, and archive refuses the change [S17][S28].
- ❌ Wrong:
  ```markdown
  ## MODIFIED Requirements
  ### Requirement: Session timeout
  Change 30 minutes to 15 minutes.
  ```
- ✅ Correct:
  ```markdown
  ## MODIFIED Requirements
  ### Requirement: Session timeout
  The system SHALL expire a session after 15 minutes of inactivity.

  #### Scenario: Idle timeout
  - **WHEN** 15 minutes pass with no activity
  - **THEN** the session is invalidated
  ```
- Source: [S13], [S15], [S17], [S28] (2026-10-28).

**N2. Renaming via REMOVED + ADDED, or MODIFIED under the old name**
> Severity: High
> Confidence: 🟢 High | [S13 + S3]
- Why: renames are a dedicated `## RENAMED Requirements` section, applied first. A content change after a rename goes under MODIFIED with the **new** header [S13]. Archive refuses mismatched FROM/TO lines (v1.13.1) [S3].
- Impact: a lost requirement history, or an archive refusal.
- ❌ Wrong:
  ```markdown
  ## REMOVED Requirements
  ### Requirement: Login
  ## ADDED Requirements
  ### Requirement: Password login
  ```
- ✅ Correct:
  ```markdown
  ## RENAMED Requirements
  - FROM: `### Requirement: Login`
  - TO: `### Requirement: Password login`
  ```
- Source: [S13], [S3] (2026-10-28).

**N3. Running `archive` from scripts without `--yes` / a change name**
> Severity: High
> Confidence: 🟢 High | [S4 + S14 + S28]
- Why: without a terminal and without `--yes`, archive "stops before changing anything" and exits 1 [S4]. A missing change name in non-interactive mode exits non-zero [S14].
- Impact: CI jobs fail. Older output showed `User force closed the prompt with 0 null` [S28].
- ❌ Wrong:
  ```bash
  openspec archive
  ```
- ✅ Correct:
  ```bash
  # Representative — OpenSpec 1.15.0
  openspec archive add-2fa --yes
  ```
- Source: [S4], [S14], [S28] (2026-10-28).

**N4. Agents depending on generated `/opsx:*` commands or `openspec-*` skills**
> Severity: High (for our architecture)
> Confidence: 🟢 High that these are generated, profile-dependent files [S8][S4][S26]
- Why:
  - They are regenerated and pruned by `openspec update` per profile [S4][S26].
  - Skills are "detected at startup", so changes need an IDE restart [S26].
  - Since v1.13.1 they "name only the workflows your profile installs" [S3].
  - G1 assigns orchestration to our own agents.
- Impact: agent behaviour drifts with the profile or update, and duplicates our spec-synchronizer.
- ❌ Wrong (agent prompt): `Run /opsx:archive to finish the change.`
- ✅ Correct (agent prompt): `Run "openspec validate <id> --strict --json --no-interactive"; if exit 0, run "openspec archive <id> --yes".`
- Source: [S8], [S4], [S26], [S3] (2026-10-28).

**N5. Requirements without SHALL/MUST, or scenarios without `####` headers**
> Severity: Medium
> Confidence: 🟢 High | [S20 + S17]
- Why: "Requirement must contain SHALL or MUST keyword" [S20]. Bullets without `#### Scenario:` give a warning that fails `--strict` [S17].
- ❌ Wrong:
  ```markdown
  ### Requirement: Export
  Users can export data.
  - WHEN user clicks Export
  - THEN a CSV downloads
  ```
- ✅ Correct:
  ```markdown
  ### Requirement: Export
  The system SHALL let users export their data as CSV.

  #### Scenario: Successful export
  - **WHEN** user clicks "Export" button
  - **THEN** system downloads a CSV file with all user data
  ```
- Source: [S20], [S17], [S15] (2026-10-28).

**N6. Using `concepts.md` example headings for proposals**
> Severity: Medium
> Confidence: 🟢 High | [S18 + S20]
- Why: the validator requires `## Why` and `## What Changes`. The `## Intent/Scope/Approach` example in [S5] would fail validation (see C2).
- ❌ Wrong:
  ```markdown
  # Proposal: Add 2FA
  ## Intent
  ## Scope
  ## Approach
  ```
- ✅ Correct:
  ```markdown
  # Proposal
  ## Why
  ## What Changes
  ## Capabilities
  ## Impact
  ```
- Source: [S18], [S20], [S5] (2026-10-28).

**N7. Using deprecated `openspec change …` / `openspec spec …` subcommands in automation**
> Severity: Medium
> Confidence: 🟡 Medium (deprecation stated in [S7]; the validator guide text in [S20] still mentions `openspec change show`)
- Why: [S7] Known inconsistency 8 says "Deprecated `change`/`spec` subcommands emit unenveloped payloads". [S4] documents `show [item] --type change|spec` instead.
- ❌ Wrong: `openspec change show add-2fa --json --deltas-only`
- ✅ Correct: `openspec show add-2fa --type change --json --deltas-only --no-interactive`
- Source: [S7], [S4], [S20] (2026-10-28).

## Migration Guide

> Confidence: 🟢 High | Sources: releases [S3] (2026-10-28) + release v1.15.0 [S22] (2026-10-28) + docs/migration-guide.md [S26] (2026-10-28)

**Breaking Changes:** no release from v1.13.0 to v1.15.0 is labelled breaking [S3]. Behaviour that became stricter and matters to automation:
- v1.13.1: archive refuses names that differ only in case, and mismatched `RENAMED` FROM/TO lines. Validate reports requirements written outside a delta section and scenarios with no body [S3]. ⚠️ Migration Note.
- v1.14.0: `validate --strict` fails on unrecognized `.openspec.yaml` keys. `show --json` includes requirement and scenario names. Archive stops when spec sync reports a blocking condition [S3]. ⚠️ Migration Note.
- v1.14.1: requirements over 500 characters are a warning, so `--strict` fails on them. `view` no longer lists archived changes [S3]. ⚠️ Migration Note.
- v1.14.2: validate and archive warn when delta text would be dropped, and these warnings fail `--strict`. Top-level `x-` keys in `.openspec.yaml` are ignored [S3]. ⚠️ Migration Note.
- v1.14.3: `list`/`show`/`validate`/`archive` accept symlinked `spec.md` files inside the project. Links resolving outside are still refused [S3].
- v1.15.0: standalone binaries; `update --dry-run [--json]`; faster `--json`; `/opsx:verify` REMOVED matching by exact name; `openspec feedback` [S22].

**Windows-relevant fixes:** v1.13.2 makes archive on Windows leave no `.openspec-archive.lock` behind and finish instead of rolling back when Windows blocks a rename [S3]. v1.15.0 ships Windows x64/arm64 binaries and a PowerShell installer [S22][S9]. The npm global bin dir must be on `PATH` (`npm prefix -g`) [S28]. Shell completion supports `powershell` [S4].

**Legacy layout migration** [S26]:
- `openspec/project.md` → `openspec/config.yaml` (`context:` + per-artifact `rules:`). `project.md` is not auto-deleted.
- `openspec/AGENTS.md` is deleted as obsolete.
- OpenSpec marker blocks in root `CLAUDE.md`/`AGENTS.md` are stripped; "everything you wrote stays".
- Legacy `.claude/commands/openspec/` is removed.
- `/openspec:proposal|apply|archive` map to `/opsx:propose|apply|archive`.
- v1.14.0 init guides the `project.md` → `config.yaml` move [S3].

**Upgrade Steps** (representative; do not run here):
1. Standalone: rerun the installer, or run `openspec install` [S1][S9]. npm: `npm install -g @fission-ai/openspec@1.15.0` (pin form: medium confidence) [S1].
2. `openspec --version` should print the version. For the standalone binary, `openspec version` prints `OpenSpec <version> (standalone)` [S9].
3. In each project: `openspec update --dry-run --json` to preview, then `openspec update` [S4][S22].
4. `openspec validate --all --strict --json --no-interactive` to surface the stricter v1.14.x rules [S4][S3].

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Node.js (npm/pnpm/yarn/bun installs) | 20.19.0 | not stated | `engines.node ">=20.19.0"` [S25][S24]; standalone needs none [S9] |
| Windows | 10 | — | `openspec-windows-x64.exe` / `-arm64.exe` [S9] |
| macOS | 13 | — | [S9] |
| Linux glibc | 2.17 | — | Alpine 3.17+ musl, with `apk add libstdc++ libgcc` [S9] |
| Yarn | 1.x only | 1.x | Yarn 2+ removed `global` [S9] |

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | S5 concepts.md + S11 getting-started.md + S14 cli-archive spec]

**Layout (OpenSpec 1.15.0)** [S5][S11][S14]:
```text
openspec/
  config.yaml                      # optional project config: schema, context, rules, operations [S11][S23]
  specs/<capability>/spec.md       # live source of truth
  changes/<change-name>/
    proposal.md
    design.md
    tasks.md
    .openspec.yaml                 # optional: schema, created, skip_specs, retire_capabilities, x-* [S5]
    specs/<capability>/spec.md     # delta specs
  changes/archive/YYYY-MM-DD-<change-name>/   # archived change, all artifacts kept [S5][S14]
  schemas/<name>/schema.yaml       # optional custom schemas [S5]
```
Change names must be lowercase kebab-case, and a leading number is allowed (`openspec new change <name>`) [S4]. The built-in schema `spec-driven` has artifacts proposal → specs (requires proposal), design (requires proposal), tasks (requires specs and design), and apply tracks `tasks.md` [S15]. Schema resolution order is `--schema` → `.openspec.yaml` → `openspec/config.yaml` → `spec-driven` [S23].

**Lifecycle driven by our agents (CLI only, no `/opsx:*`)**:
```bash
# Representative — adapt to your environment (OpenSpec 1.15.0)
# 0. one-time, by a human (init is listed as human-only in [S4]):
openspec init --tools none
# 1. scaffold a change (or write the folder directly)
openspec new change add-2fa --description "Admin 2FA" --json
# 2. agents write proposal.md, specs/<cap>/spec.md deltas, design.md, tasks.md
#    optional per-artifact guidance:
openspec instructions specs --change add-2fa --json
openspec status --change add-2fa --json   # first artifact with status "ready" = next to write [S7]
# 3. gate
openspec validate add-2fa --type change --strict --json --no-interactive
# 4. inspect parsed deltas
openspec show add-2fa --type change --deltas-only --json --no-interactive
# 5. after implementation and tasks checked: archive (merge deltas + move folder)
openspec archive add-2fa --yes
# 6. confirm live specs
openspec validate --specs --strict --json --no-interactive
openspec list --archived --json           # archived changes visible (v1.14.0+) [S3]
```
The flags come from [S4]. `instructions archive` is read-only and does not archive [S4][S7]. `openspec instructions apply --change <id> --json` returns `state` (`blocked|all_done|ready`), `progress`, `tasks` and `missingArtifacts` [S7].

**CLI inventory relevant to automation (v1.15.0)** [S4]:

| Command | Flags |
|---|---|
| `init [path]` | `--tools all\|none\|<ids>`, `--language`, `--force`, `--profile core\|custom`, `--no-animation`, `--copilot-cloud/--no-copilot-cloud` |
| `update [path]` | `--force`, `--dry-run`, `--json` (with `--dry-run`) |
| `list` | `--specs` / `--changes` (default), `--sort recent\|name`, `--json`; plus `--archived`/`--all` since v1.14.0 [S3] (not shown in [S4]'s list) |
| `view` | interactive dashboard, human-only |
| `show [item]` | `--type change\|spec`, `--json`, `--no-interactive`, `--deltas-only` (change), `--requirements`, `--no-scenarios`, `-r/--requirement <n>` (spec) |
| `validate [item]` | `--all`, `--changes`, `--specs`, `--archived`, `--type`, `--strict`, `--json`, `--concurrency <n>` (default 6 / `OPENSPEC_CONCURRENCY`), `--no-interactive` |
| `archive [change]` | `-y/--yes`, `--skip-specs`, `--no-validate` (requires confirmation; also disables capability retirement) |
| `new change <name>` | `--description`, `--goal`, `--schema`, `--store`, `--json` |
| `status` | `--change <id>`, `--schema`, `--json` |
| `instructions [artifact]` | `--change <id>` (required non-interactively), `--schema`, `--json` |
| `templates` / `schemas` | `--schema`, `--json` / `--json`, `--store` |
| `schema init\|fork\|validate\|which` | see [S4] |
| `config` | `path`, `list`, `get`, `set [--string]`, `unset`, `reset --all --yes`, `edit`, `profile [preset]` |
| `completion generate\|install\|uninstall [shell]` | `bash`, `zsh`, `fish`, `powershell` |
| `feedback <message>` | `--body`; needs authenticated `gh` |

- **No `diff` command** appears in the v1.15.0 CLI reference [S4]. Treat `openspec diff` as nonexistent **(unverified absence)**.
- Stores and worksets are **beta**: "Command names, flags, and JSON shapes may change between releases" [S4]. Out of scope.

**What the `/opsx:*` workflows do (overlap note, human-only)** [S10][S8]:
- `/opsx:apply`: works through tasks, checking them off, and updates artifacts when needed.
- `/opsx:sync`: merges the change's delta specs into `openspec/specs/` without archiving; REMOVED requirements are deleted and RENAMED are retitled in place.
- `/opsx:verify` (expanded profile): validates the implementation against the artifacts. The detailed checks are not documented **(unverified)**. Per v1.13.2 it no longer reports skipped checks as passing; per v1.14.2 it reports unverified when a REMOVED requirement's original text cannot be read; per v1.15.0 it matches REMOVED requirements by exact name [S3][S22].
- `/opsx:archive`: finalizes the change and offers to sync first [S10].
- Overlap with our agents: `apply` ≈ our implementer, `sync` ≈ our spec-synchronizer, `verify` ≈ our quality gate. Do not run both [G1].

**Claude Code integration written by `init --tools claude`** [S8][S26]:
- Skills: `.claude/skills/openspec-*/SKILL.md`, e.g. `openspec-propose`, `openspec-apply-change`, `openspec-sync-specs`, `openspec-archive-change`, `openspec-verify-change`. Except for `/opsx:apply` → `openspec-apply-change`, the workflow-to-skill mapping is inferred from names in [S8] **(medium confidence)**.
- Commands: `.claude/commands/opsx/<id>.md` → `/opsx:<id>`.
- [S8] does not mention `CLAUDE.md` writes. [S26] says only OpenSpec marker blocks in `CLAUDE.md`/`AGENTS.md` are removed during migration.

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (OpenSpec 1.15.0); not executed in this research
openspec --version                                   # expected: 1.15.0 [S4][S9]
openspec validate --all --strict --json --no-interactive
# expected stdout: one JSON document; exit 0 if every item valid, 1 otherwise [S7][S17]
openspec validate --archived --no-interactive        # fails if an archived change has unchecked tasks [S4]
openspec show <change> --type change --deltas-only --json --no-interactive
```

**JSON shape for `validate --json`:** sources disagree (contradiction C3).
- [S7] and [S17] give top-level `items`, `summary`, `version: "1.0"`. Each item has `id`, `type`, `valid`, `issues[]` (`level` ERROR/WARNING/INFO, `path`, `message`) and `durationMs`.
- [S4] gives `version`, `results` (`name`, `valid`, `warnings`) and `summary` (`total`, `valid`, `invalid`).
- Parse defensively: gate on the **exit code**, then read `items` and fall back to `results` **(medium confidence)**.

**Validation thresholds** (constants.ts [S20]):
- `MIN_PURPOSE_LENGTH = 50` (warning)
- `MIN_WHY_SECTION_LENGTH = 50` (error)
- `MAX_WHY_SECTION_LENGTH = 1000`
- `MAX_REQUIREMENT_TEXT_LENGTH = 500` (warning → fails `--strict` [S3])
- `MAX_DELTAS_PER_CHANGE = 10` ("Consider splitting…"; its severity is **(unverified)**)

**Mocking:** OpenSpec has no SDK. For our scripts, test against fixture folders under a temp directory and assert on the exit code and JSON. Do not mock the CLI's text output. (This is a recommendation, not an OpenSpec claim.)
```bash
# Representative — fixture-based check of a known-bad delta (expects exit 1)
openspec validate bad-change --type change --strict --json --no-interactive; test $? -eq 1
```

## Production Readiness

- **Performance:**
  - v1.14.1: `--version`/`--help` load 24 modules instead of 485.
  - v1.15.0: `--json` commands start faster because they no longer load the spinner.
  - Bulk validation concurrency defaults to 6 (`OPENSPEC_CONCURRENCY`) [S3][S22][S4].
- **Scalability:** consider splitting changes with more than 10 deltas [S20]. Brace globs deeper than 16 levels or expanding past 1,024 paths are rejected [S3].
- **CI/non-interactive:**
  - Set `CI` or `OPEN_SPEC_INTERACTIVE=0`; the spinner is off and `validate --all` no longer hangs with zero-column terminals (v1.14.3) [S3].
  - With `CI` set, the update check and telemetry are disabled [S4][S1].
  - Always pass a change name and `--yes` to archive [S4][S28].
  - Redirected or agent-run archive output stays clean, and confirmations are read as plain text when stdout is not a TTY [S28].
- **Archive recovery:** `archive_retirement_cleanup_failed` means the change was archived but cleanup failed; inspect, and do not retry. `archive_error` means files may or may not have changed; inspect the change, archive and specs before retrying. `archive: null` does not guarantee files are unchanged [S7].
- **Security:**
  - Telemetry collects command names and version only. Opt out with `openspec config set telemetry.enabled false`, `OPENSPEC_TELEMETRY=0` or `DO_NOT_TRACK=1` [S1][S4].
  - Since v1.13.1, `config.yaml` values cannot inject directives into agent instructions, and a repo `.npmrc` cannot redirect the update check [S3].
  - v1.14.3 dropped the unpatched `braces` package and refuses glob or symlink paths that leave the change directory [S3].
  - Standalone downloads are checked against `SHA256SUMS` [S9].
  - `config.yaml` `context` is capped at 50KB [S26].
- **Stability:** no versioning or stability policy is published for the core CLI **(unverified)**. Stores and worksets are explicitly beta [S4]. [S7] lists "Known inconsistencies (not yet fixed)": mixed snake_case/camelCase keys, only `validate` carrying `version`, and deprecated `change`/`spec` payloads.

## Reference Implementations

- The repo's own `openspec/specs/` (36+ capabilities, e.g. `openspec-conventions`, `cli-archive`, `cli-validate`, `specs-sync-skill`, `opsx-verify-skill`) at v1.15.0 is a real-world format example [S12][S13][S14][S17].
- The built-in schema and templates: `schemas/spec-driven/schema.yaml`, `templates/spec.md`, `templates/proposal.md` [S15][S16][S18].
- The worked example "add-dark-mode" in docs/getting-started.md [S11].
- docs/examples.md, editing-changes.md, reviewing-changes.md, team-workflow.md and existing-projects.md exist at the tag but were **not read** [S2].
- Spec Kit and other SDD tools are out of scope.

## Source Bibliography

**Primary** (all read 2026-10-28; tag v1.15.0 = 2026-10-24 [S27]):

| ID | Source | Read status |
|---|---|---|
| S1 | https://github.com/Fission-AI/OpenSpec/blob/v1.15.0/README.md | full, summarizing fetch |
| S2 | https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/docs | listing only |
| S3 | https://github.com/Fission-AI/OpenSpec/releases (v1.13.0–v1.15.0 notes) | condensed highlights; full per-release pages not read except v1.15.0 → **partly read** |
| S4 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md | full, summarizing fetch |
| S5 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md | full, summarizing fetch |
| S6 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/writing-specs.md | full, summarizing fetch |
| S7 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md | condensed (long page) → **partly read** for exact JSON field shapes |
| S8 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/supported-tools.md | Claude Code row verbatim; rest summarized |
| S9 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/installation.md | full, summarizing fetch |
| S10 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/opsx.md | full, summarizing fetch |
| S11 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/getting-started.md | code blocks summarized → **partly read** |
| S12 | https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/openspec/specs | listing; may be truncated ("View all files") |
| S13 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md | excerpts only → **partly read** |
| S14 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md | paraphrased scenarios → **partly read** |
| S15 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml | summarized + short verbatim snippets → **partly read** |
| S16 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/templates/spec.md | structure only, no verbatim → **partly read** |
| S17 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-validate/spec.md | full, summarizing fetch |
| S18 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/templates/proposal.md | headings verbatim |
| S19 | https://github.com/Fission-AI/OpenSpec/tree/v1.15.0/src/core/validation | listing |
| S20 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts | constants and messages verbatim |
| S21 | https://www.npmjs.com/package/@fission-ai/openspec/v/1.15.0 | **HTTP 403, not read** |
| S22 | https://github.com/Fission-AI/OpenSpec/releases/tag/v1.15.0 | notes summarized; asset names not listed |
| S23 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/customization.md | full, summarizing fetch |
| S24 | https://registry.npmjs.org/@fission-ai/openspec/1.15.0 | version/license/engines/bin/tarball |
| S25 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/package.json | name/version/license/engines/bin/type |
| S26 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/migration-guide.md | full, summarizing fetch |
| S27 | https://github.com/Fission-AI/OpenSpec/tags | dates with year |
| S28 | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/troubleshooting.md | full, summarizing fetch |

**Validation:** no community sources were used (source hierarchy: official only).

**Contradictions found (both URLs reported):**
- **C1, scenario step markup.** [S5] concepts.md and [S6] writing-specs.md show plain `- GIVEN/- WHEN/- THEN` bullets. [S15] schema.yaml, [S20] constants.ts guides, [S13] and [S14] use bold `- **WHEN**`/`- **THEN**`/`- **AND**`. Whether the parser enforces bold is unverified. Use bold.
- **C2, proposal sections.** [S5] concepts.md shows `## Intent/## Scope/## Approach`. [S20] constants.ts, [S17] cli-validate and [S18] proposal.md require `## Why` + `## What Changes`. The validator wins.
- **C3, `validate --json` shape.** [S4] cli.md says `results`/`summary{total,valid,invalid}`. [S7] agent-contract.md and [S17] cli-validate say `items`/`summary`/`version`.
- **C4, archive with incomplete tasks.** [S28] troubleshooting.md says archive "won't *block*… but it warns you". [S14] cli-archive says it prompts with default "No", and declining aborts non-zero. Both hold if read as warn + confirm. With `--yes` the behaviour is presumably to proceed **(unverified)**.
- **C5, RFC 2119 words.** [S6] and [S5] accept SHOULD/MAY. [S20] requires SHALL or MUST in every requirement.
- **C6, `archive --json`.** [S4] lists no `--json` flag for `archive`. [S7] documents an `archive` JSON object, and [S3] v1.14.1 mentions `archive_retirement_cleanup_failed` "in `--json`". Unverified.
- **Minor:** [S3] dates v1.14.1 as 06 Oct, while [S27] says Oct 5, 2026 (likely a timezone difference). There are no contradictions with `_family_facts_v3.40.md`; its MODIFIED/REMOVED unverified tag is now resolved.

## Research Gaps

```
Gap: Whether the v1.15.0 parser rejects non-bold WHEN/THEN scenario steps (C1)
Impact: Low if we always emit bold (safe superset)
Workaround: Always emit "- **WHEN**"/"- **THEN**"/"- **AND**"
Follow-up: src/core/parsers/* at tag v1.15.0
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Whether `openspec archive` accepts --json in v1.15.0 (C6)
Impact: Medium — the archive result must be read from the exit code + filesystem if not
Workaround: Gate on exit code; then check openspec/changes/archive/<date>-<id>/ exists
Follow-up: src/cli/index.ts (archive command options) at tag v1.15.0
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Whether `openspec init --tools none` creates openspec/config.yaml and which folders
Impact: Medium for the bootstrap script
Workaround: Human runs init once; the script then checks openspec/specs and openspec/changes exist
Follow-up: openspec/specs/cli-init/spec.md at tag v1.15.0
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Exact checks performed by /opsx:verify
Impact: Low (human-only per G1)
Workaround: Our quality gate defines its own checks
Follow-up: openspec/specs/opsx-verify-skill/spec.md at tag v1.15.0
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Global config key for delivery mode (skills/commands/both) and the Windows global config path
Impact: Low (only for humans opting in to /opsx:*)
Workaround: `openspec config path` / `openspec config list` on the user's machine
Follow-up: openspec/specs/global-config/spec.md at tag v1.15.0
§7-ref: Iteration 3 — IRRESOLVABLE
```
Further unverified items (not looped): a stability/versioning policy for the core CLI; the severity of `MAX_DELTAS_PER_CHANGE`; `--yes` behaviour with incomplete tasks; the PowerShell `$env:OPENSPEC_VERSION` syntax and the npm `@1.15.0` pin (medium); the absence of `openspec diff`; the workflow-to-skill name mapping other than apply (medium); and npm page metadata (S21 returned 403; S24/S25 used instead).

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails A4 | RENAMED section syntax (absent from concepts/writing-specs) | Resolved — FROM:/TO: lines + MODIFIED under new header | [S13] (2026-10-28) |
| 1 | Guardrails A4 | REMOVED entry format | Resolved — `**Reason**:` / `**Migration**:` | [S15] (2026-10-28) |
| 1 | Guardrails A5 | Archive merge order (absent from concepts) | Resolved — RENAMED→REMOVED→MODIFIED→ADDED | [S13] (2026-10-28) |
| 2 | Guardrails A6 | Required proposal sections (C2) | Resolved — `## Why` + `## What Changes` | [S20][S18] (2026-10-28) |
| 2 | Guardrails A2 | SHALL/MUST enforcement | Resolved — validator message quoted | [S20] (2026-10-28) |
| 2 | Metadata | Node requirement / license (npm page 403) | Resolved via registry JSON + package.json | [S24][S25] (2026-10-28) |
| 3 | Metadata | Release year | Resolved — 2026-10-24 | [S27] (2026-10-28) |
| 3 | Gaps | Bold WHEN/THEN enforcement | ⚠️ IRRESOLVABLE — parser source not fetched within MAX_ITERATIONS=3 | — |
| 3 | Gaps | `archive --json` | ⚠️ IRRESOLVABLE — docs disagree; CLI source not fetched | — |
| 3 | Gaps | `init --tools none` outputs | ⚠️ IRRESOLVABLE — not stated in cli.md/supported-tools/migration-guide | — |
| 3 | Gaps | `/opsx:verify` checks | ⚠️ IRRESOLVABLE — opsx.md gives one line only | — |
| 3 | Gaps | Delivery config key / Windows config path | ⚠️ IRRESOLVABLE — customization.md silent | — |

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (install/Node, init, layout, spec format, delta format, tasks, CLI, non-interactive, /opsx overlap, changelog 1.13–1.15, Windows)
- [x] Pattern counts driven by domain needs (8 mandatory, 5 conditional, 7 forbidden)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative (none executed — hard constraint)
- [x] Integration examples complete (agent-driven CLI lifecycle)
- [x] Sources dated and linked
- [x] Security documented (telemetry, injection fix, checksums, braces)
- [x] 1+ copy-paste working example (spec + delta + tasks markdown)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep) or downgraded to 🟡 Medium (A3 bold markup downgraded)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7

## Agent Operation Notes

- **High Confidence (execute without asking):** A1, A2, A4, A5, A6, A7 and A8 (triangulated); the CLI flags in the inventory table from [S4]; exit codes 0/1/130; the archive folder name `YYYY-MM-DD-<change-name>`; the Claude Code paths `.claude/skills/openspec-*/SKILL.md` and `.claude/commands/opsx/<id>.md`; `init --tools none`; Node ≥ 20.19.0 for npm; MIT.
- **Medium Confidence (validate with user):** whether bold WHEN/THEN is *enforced* (A3); the `validate --json` field names (C3); the PowerShell/npm pinning syntax; the skill-name mapping beyond apply; deprecated `change`/`spec` subcommands (N7).
- **Low Confidence (must ask human):** the IRRESOLVABLE items in Research Gaps (archive `--json`, `init --tools none` outputs, verify checks, delivery key, Windows config path); stability policy.
- **Edge Cases (pause):** v1.15.0 was released 2026-10-24, **4 days** before research (<30 days). The docs at the tag are complete, but patch releases are frequent (8 releases in ~7 weeks [S27][S3]). Re-check for v1.15.x before skill authoring. No active CVE found; v1.14.3 removed an unpatched `braces` dependency [S3].
- **Emergency Stop:** not triggered. All sources are official (repo at tag, releases, npm registry).
- **Family rules applied:** rule 9 (Never-Do ✅ alternatives name only High options; pinning syntax kept in Ask-First B2); rule 10 (thresholds stated per constant); rule 11 (`schema: spec-driven` is "the default schema" per [S23]; the example config in [S23] is called an example); rule 12 applies to the downstream blueprints.
