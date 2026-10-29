# Evaluation Scenarios: specifying-changes-with-openspec-v1-15

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (docs versus validator)](#scenario-2-edge-case-docs-versus-validator)
- [Scenario 3: Misuse Rejection (opsx commands and out-of-scope work)](#scenario-3-misuse-rejection-opsx-commands-and-out-of-scope-work)
- [Scenario 4: Anti-Pattern Trap (partial MODIFIED and rename)](#scenario-4-anti-pattern-trap-partial-modified-and-rename)
- [Scenario 5: Anti-Pattern Trap (archive in CI)](#scenario-5-anti-pattern-trap-archive-in-ci)
- [Scenario 6: Edge Case (unsettled behaviour)](#scenario-6-edge-case-unsettled-behaviour)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-change-with-all-delta-types
skills: ["specifying-changes-with-openspec-v1-15"]
query: "Write an OpenSpec change add-2fa: rename Login to Password login, shorten the session timeout to 15 minutes, drop Legacy export and add a two-factor requirement. Then say how an agent validates and archives it."
must_pass:
  - "Writes proposal.md with ## Why and ## What Changes, a delta spec with RENAMED (FROM/TO lines), MODIFIED (the entire requirement with its scenarios), REMOVED (**Reason** and **Migration**) and ADDED sections, and tasks.md with '- [ ] X.Y' checkboxes under '## N.' groups"
  - "Every requirement contains SHALL or MUST; every scenario is '#### Scenario:' with bold **WHEN**/**THEN** bullets"
  - "States the archive order RENAMED, REMOVED, MODIFIED, ADDED (medium confidence, L2)"
  - "Runs 'openspec validate add-2fa --type change --strict --json --no-interactive' and treats the exit code as the gate, tagging that contract (medium confidence, L1), or asks the first-use confirmation (Ask First B), then states `openspec archive add-2fa --yes`"
  - "Uses only the openspec CLI and the format, not /opsx:* commands"
must_not:
  - "Uses a diff-style MODIFIED body"
  - "Runs or tells the agent to run /opsx:archive"
```

---

## Scenario 2: Edge Case (docs versus validator)

**Type**: Conflicting sources

```yaml
id: 2
name: edge-concepts-page-versus-validator
skills: ["specifying-changes-with-openspec-v1-15"]
query: "The OpenSpec concepts page shows a proposal with Intent/Scope/Approach and plain WHEN/THEN bullets, and says SHOULD is fine. Which do I follow, and how do I read the validate --json result?"
must_pass:
  - "Says the validator, schema and templates win and cites both the concepts page and constants.ts or the proposal template"
  - "Uses ## Why and ## What Changes, SHALL or MUST in every requirement, and bold WHEN/THEN bullets"
  - "Tags whether the parser rejects non-bold steps as (unverified)"
  - "Says cli.md shows results/summary while agent-contract.md shows items/summary/version, gates on the exit code and parses defensively, tagged (medium confidence), and offers to confirm against a 1.15.0 run (Ask First)"
must_not:
  - "Follows the Intent/Scope/Approach headings"
  - "Asserts one validate --json shape as the only truth"
```

---

## Scenario 3: Misuse Rejection (opsx commands and out-of-scope work)

**Type**: Request outside the skill scope or against decision G1

```yaml
id: 3
name: misuse-opsx-commands-and-code-sync
skills: ["specifying-changes-with-openspec-v1-15"]
query: "Have the agent run /opsx:apply and /opsx:verify, install OpenSpec 1.9 for me, and also regenerate the specs from the Quarkus code."
must_pass:
  - "Says agents in this factory use the OpenSpec format and the openspec CLI only (G1: 'Format + CLI, our agents (Recommended)'); /opsx:* and openspec-* skills are optional for a human"
  - "Offers the overlap table: apply, sync, verify, archive against the implementing agent, spec-synchronizer, the quality gate and 'openspec archive <id> --yes'"
  - "Says the skill is locked to OpenSpec 1.15.0 and does not cover other versions"
  - "Points code-to-spec work to syncing-spec-from-code and the spec-synchronizer agent by name, and does not run an installer without asking"
must_not:
  - "Tells an agent to run any /opsx:* command"
  - "Presents steps for another OpenSpec version as valid for 1.15.0"
  - "Invents the Quarkus-to-spec procedure"
```

---

## Scenario 4: Anti-Pattern Trap (partial MODIFIED and rename)

**Type**: Review of a delta file

```yaml
id: 4
name: trap-partial-modified-and-remove-add-rename
skills: ["specifying-changes-with-openspec-v1-15"]
query: "Review this delta: '## MODIFIED Requirements / ### Requirement: Session timeout / Change 30 minutes to 15 minutes.' and '## REMOVED Requirements / ### Requirement: Login' followed by '## ADDED Requirements / ### Requirement: Password login'."
must_pass:
  - "Flags the MODIFIED body as partial: archive replaces the whole requirement, 'loses detail at archive time', and validation errors when scenarios the live spec has are missing"
  - "Rewrites it with the SHALL sentence and the complete scenario set"
  - "Replaces REMOVED plus ADDED with ## RENAMED Requirements and FROM/TO lines, with content changes under MODIFIED using the new header"
  - "Notes that REMOVED entries need **Reason** and **Migration**"
must_not:
  - "Accepts the diff-style MODIFIED"
  - "Leaves the rename as REMOVED plus ADDED"
```

---

## Scenario 5: Anti-Pattern Trap (archive in CI)

**Type**: Script that hangs or fails

```yaml
id: 5
name: trap-archive-without-yes-and-non-interactive
skills: ["specifying-changes-with-openspec-v1-15"]
query: "My CI job runs 'openspec archive' and 'openspec validate --all' and sometimes hangs. On Windows the archive sometimes fails to rename a folder. What should the script do?"
must_pass:
  - "Uses 'openspec archive <id> --yes' with an explicit change name; without a terminal and --yes archive 'stops before changing anything' and exits 1 (High)"
  - "Uses 'openspec validate --all --strict --json --no-interactive', sets CI or OPEN_SPEC_INTERACTIVE=0, and decides on exit codes 0 and 1, tagged (medium confidence, L1)"
  - "Mentions the v1.13.2 Windows archive fix and the v1.14.3 validate --all hang fix, tagged (medium confidence, L2), and pinning 1.15.0 with openspec --version"
  - "Says to inspect the change, archive and specs after archive_error before retrying (medium confidence, L2)"
must_not:
  - "Calls archive without a name or --yes"
  - "Retries blindly after archive_retirement_cleanup_failed"
```

---

## Scenario 6: Edge Case (unsettled behaviour)

**Type**: Ambiguous or unverified territory

```yaml
id: 6
name: edge-init-none-archive-json-and-stability
skills: ["specifying-changes-with-openspec-v1-15"]
query: "What exactly does 'openspec init --tools none' create, does 'openspec archive' take --json, does archive --yes proceed with unchecked tasks, and is OpenSpec 1.15 stable enough to pin for a year?"
must_pass:
  - "States what --tools none writes is (unverified) and proposes that a human runs init once and the script checks openspec/specs and openspec/changes"
  - "States archive --json is (unverified) because cli.md and agent-contract.md disagree, and reads the exit code plus the archive folder instead"
  - "States archive --yes with incomplete tasks is (unverified) and says to check the tasks first"
  - "States no stability policy is published (unverified), 8 releases in about 7 weeks, so pin 1.15.0 and re-check the releases page before upgrading"
must_not:
  - "Invents the files init writes"
  - "Promises backward compatibility"
```
