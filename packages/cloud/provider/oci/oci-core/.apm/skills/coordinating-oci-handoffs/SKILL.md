---
name: coordinating-oci-handoffs
description: "OCI profile of the generic handoff protocol v1 for the OCI agent family: roster, record file names in per-capability folders under docs/handoff/ and user-mediated hand-offs. Use when an OCI agent must read prior handoff context, write a result record or route work to a sibling agent."
---

# Coordinating OCI Handoffs

Thin **profile** over the generic skill `coordinating-agent-handoffs` (**protocol v1**). The record
kinds, handshake, validation scripts (`check_records.py`, `board.py`) and rules live there; this
skill adds only what is OCI-specific: the roster, the file names, the capability folder and the
user-mediated mode. There is **no OpenSpec** in this family (`spec.kind: none`).

## Version Context

| Item | Value | Source |
|---|---|---|
| Generic protocol | `coordinating-agent-handoffs`, protocol v1 (package `handoff-core`) | repo skill, not an external page |
| Profile | `profile: oci`, `mode: user-mediated`, `scope_key: capability`, `spec.kind: none` | [handoff-profile.yaml](./assets/handoff-profile.yaml) |
| Authored | 2026-10-28 | this repo |

Version-lifetime risk: this profile follows protocol v1; a protocol v2 would need a new profile
version. Details: [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference) | [Verification Loop](#verification-loop)
- **[OCI handoff specifics](./blueprints/handoff-protocol.md)** - roster, stream names, invocation
  vocabulary, worked examples.
- [Always-do patterns](./blueprints/always-do-patterns.md), [never-do patterns](./blueprints/never-do-patterns.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- **Profile** for the scripts: [assets/handoff-profile.yaml](./assets/handoff-profile.yaml)
- **Templates**: [work-order](./assets/work-order.template.md), [result](./assets/result.template.md)
  (kind `report`), [deploy-report](./assets/deploy-report.template.md),
  [diagnosis-report](./assets/diagnosis-report.template.md).

## Blueprints & Guardrails

### ✅ Always Do

- **Read first.** Read the records of the capability in `docs/handoff/<capability>/` before analysing
  ([specifics](./blueprints/handoff-protocol.md#standard-handshake-every-agent)).
- **Write one record, then one hand-off line.** `Hand off: run /<command> (@<agent>) - <why>. Context: <path>`;
  the user runs the next command ([patterns](./blueprints/always-do-patterns.md#1-one-record-one-hand-off-line)).
- **Write your own file.** Each role owns its record name; `oci-observability` writes `result-observability.md`
  ([patterns](./blueprints/always-do-patterns.md#2-each-role-owns-its-file)).
- **Route a diagnosis by its owner.** The user follows the `to` named in `diagnosis-report.md`; the profile's
  `next:` rule is advisory ([patterns](./blueprints/always-do-patterns.md#3-route-a-diagnosis-by-its-owner)).
- **Write to the target project**, `docs/handoff/<capability>/`, never into a package.

### ⚠️ Ask First

| Decision | Ask |
|---|---|
| A record of an earlier cycle is still open (`status` not `completed`, or `outcome: partial`) and would be overwritten | "Overwrite the previous record or keep it under another capability slug?" |
| The capability slug is unclear | "Which capability (function name) is this for?" |
| Counting attempts toward the profile limits (`build_attempts`, `deploy_cycles`) | "This is attempt N by my own count; continue or stop?" (records are overwritten per cycle, so counters are not meaningful: stated by the generic protocol, skill `coordinating-agent-handoffs`, `protocol.md`) |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Name a result record outside the naming convention | name records `result-<role>.md` (guard rationale: register U1); `deploy-report.md` and `diagnosis-report.md` keep their names; `kind: report` stays inside the frontmatter |
| Auto-chain to the next agent (no exception: `oci-serverless-stack` also hands off per stream) | End with the Hand off line and let the user run the command |
| Write another role's file (for example `oci-observability` into `result-terraform-infra.md`) | Write `result-observability.md` |
| Treat `build_attempts` or `deploy_cycles` as reliable counters: records are overwritten each cycle, and the generic protocol (skill `coordinating-agent-handoffs`, `protocol.md`) says such counters are not meaningful for this family (High) | Keep the attempt number in the record body and ask the user at the limit |
| Write records into this package or the agent factory | Write them to `docs/handoff/<capability>/` of the target project |

Full examples: [always-do](./blueprints/always-do-patterns.md), [never-do](./blueprints/never-do-patterns.md).

## Quick Reference

| Agent | Reads | Writes |
|---|---|---|
| `oci-serverless-architect` | requirements | `stream-a-java.md`, `stream-b-terraform-infra.md`, `stream-c-terraform-integration.md` (work-orders) |
| `oci-serverless-stack` | the 3 work-orders; with `--integrate` the stream A/B results | hands off streams A/B, then does stream C with `--integrate`; consumes `result-*.md` |
| `oci-functions-java` | work-order / diagnosis-report | `result-java.md` |
| `oci-terraform` | work-order / result / diagnosis-report | `result-terraform-infra.md`, `result-terraform-integration.md` |
| `oci-deployer` | result / diagnosis-report | `deploy-report.md` |
| `oci-debugger` | deploy-report | `diagnosis-report.md` |
| `oci-observability` | result / diagnosis-report | `result-observability.md` |

**File-name rule:** no record file name starts with `report` (a subagent write guard on such names was observed, `(unverified)`, register U1). Records are `result-*.md`;
`deploy-report.md` and `diagnosis-report.md` do not start with `report` and keep their names.

**Kind and patterns:** the `deploy-report` and `diagnosis-report` templates carry `kind: report` in their
frontmatter; the profile's `kind_overrides` map them to their own kinds by file name. The `records:` patterns
are guidance, not enforced: role `terraform` writes two files (`result-terraform-infra.md`,
`result-terraform-integration.md`) that the `result-{role}.md` pattern does not match literally.

## Verification Loop

```bash
python <coordinating-agent-handoffs>/scripts/check_records.py docs/handoff/<capability> --profile <this skill>/assets/handoff-profile.yaml
```

Expect `OK: N record(s) valid`. Running the scripts is optional in user-mediated mode.
