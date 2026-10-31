# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). OCI specifics are in [handoff-protocol.md](./handoff-protocol.md);
the record kinds belong to the generic skill `coordinating-agent-handoffs` (protocol v1).

## Contents

- [1. One record, one hand-off line](#1-one-record-one-hand-off-line)
- [2. Each role owns its file](#2-each-role-owns-its-file)
- [3. Route a diagnosis by its owner](#3-route-a-diagnosis-by-its-owner)

## 1. One record, one hand-off line

An agent finishes, writes exactly one record to `docs/handoff/<capability>/` of the target project,
states the outcome and closes with a single line. The user runs the next command.

```text
Hand off: run /deploy-oci-function (@oci-deployer) - image pushed, plan reviewed. Context: docs/handoff/func-orders/result-terraform-infra.md
```

The line is the whole routing contract in user-mediated mode. The advisory `NEXT` line of `board.py`
never replaces it.

## 2. Each role owns its file

The profile maps a `report` record to `result-{role}.md`. Every role writes only its own file, so two
agents never overwrite each other within a capability.

| Role | File |
|---|---|
| java | `result-java.md` |
| terraform | `result-terraform-infra.md`, `result-terraform-integration.md` (one per stream) |
| observability | `result-observability.md` |

`oci-observability` used to share `result-terraform-infra.md` with `oci-terraform`; running both for one
capability lost the first record. It now writes `result-observability.md` (decision O16, 2026-10-28).

## 3. Route a diagnosis by its owner

`diagnosis-report.md` names its owner in the `to` field and the slash-command in the Hand off line. The
user routes by that owner: Java code to `@oci-functions-java` (`/develop-java-function`), configuration, dependency or image to `@oci-deployer` (`/deploy-oci-function`),
infrastructure to `@oci-terraform`, an observability gap to `@oci-observability`.

The profile's `next:` rule for a `diagnosis-report` (then `deployer`) is a default for the advisory
`NEXT` line only; it does not override the owner named in the diagnosis.
