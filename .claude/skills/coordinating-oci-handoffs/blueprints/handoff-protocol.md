# OCI Handoff Specifics

OCI profile of the generic protocol: skill `coordinating-agent-handoffs` (**protocol v1**) defines
record kinds, handshake, limits and the validation scripts. This file holds only what is specific
to the OCI serverless lifecycle: roster, folder and file names, stream names, invocation
vocabulary. Profile for the scripts: [../assets/handoff-profile.yaml](../assets/handoff-profile.yaml).
Back to [SKILL.md](../SKILL.md).

## Contents

- [Roster](#roster) · [Directory layout](#directory-layout-per-capability) · [OCI record fields](#oci-record-fields)
- [Standard handshake](#standard-handshake-every-agent) · [Invocation vocabulary](#invocation-vocabulary)
- [Full flow](#full-flow) · [Worked example](#worked-example-frontmatter-only) · [Lifecycle & rules](#lifecycle--rules)

The protocol is **user-mediated**: an agent finishes its work, writes a record, and tells the user
which slash-command to run next. It never auto-chains: no agent spawns another, every transition is
a hand-off line (see [Invocation Vocabulary](#invocation-vocabulary)). There is no spec side (no OpenSpec).

## Roster

| Agent | Role in the profile | Writes |
|---|---|---|
| `@oci-serverless-architect` | architect | work-orders `stream-a/b/c` |
| `@oci-serverless-stack` | stack | validates the work-orders; in `--integrate` mode does stream C and writes `result-terraform-integration.md` |
| `@oci-functions-java` | java | `result-java.md` |
| `@oci-terraform` | terraform | `result-terraform-infra.md`, `result-terraform-integration.md` |
| `@oci-deployer` | deployer | `deploy-report.md` |
| `@oci-debugger` | debugger | `diagnosis-report.md` |
| `@oci-observability` | observability | `result-observability.md` (observability resources; its own file, never the terraform one) |

## Directory layout (per capability)

Records are namespaced by **capability slug** (= the function name, e.g. `func-api-facade`), so
several capabilities can be in flight at once. Within a capability records are overwritten on each
new cycle; different capabilities never collide. Templates are in `../assets/`.

```
docs/handoff/<capability-slug>/        # e.g. func-api-facade/
  stream-a-java.md                     # architect -> java        (work-order)
  stream-b-terraform-infra.md          # architect -> terraform   (work-order)
  stream-c-terraform-integration.md    # architect -> terraform   (work-order)
  result-java.md                       # java -> stack            (kind: report)
  result-terraform-infra.md            # terraform -> stack       (kind: report)
  result-terraform-integration.md      # terraform -> stack       (kind: report)
  result-observability.md              # observability -> user    (kind: report)
  deploy-report.md                     # deployer -> debugger/user
  diagnosis-report.md                  # debugger -> deployer/terraform/java/observability
```

**File-name rule:** no record file name starts with `report` (a subagent write guard on such
names was observed, `(unverified)`, register U1). Result records are `result-*.md`; the frontmatter `kind` stays `report`.

## OCI record fields

Common fields and kinds: `blueprints/record-kinds.md` of the skill `coordinating-agent-handoffs`
(referenced by name; it lives in another package). OCI specifics:

- **Work-order** (architect streams): `from: "@oci-serverless-architect"`, `to: "@oci-functions-java"`
  (or `@oci-terraform`), `capability`, `stream: a-java | b-terraform-infra | c-terraform-integration`,
  `dependsOn: none | [stream-a, stream-b]`, `status: pending | in-progress | completed`,
  `createdAt` (a real ISO 8601 UTC timestamp; never a placeholder, because `check_records.py` rejects a non-ISO value).
  Body: **Scope**, **Components** (checklist), **Constraints**, **Dependencies**, **Acceptance Criteria**.
- **Result** (`kind: report`): `from`, `to`, `capability`, `refs: <file this answers>`,
  `outcome: success | partial | failed | needs-input`, `createdAt`. Body: **What changed**, **Resources / OCIDs**,
  **Validation**, **Acceptance status** (checks), **Next action**, **Open issues / blockers**.
- **deploy-report** body focus: image tag deployed, tfvars diff, `terraform plan` summary, smoke
  HTTP status + body, observability-validation result, outcome.
- **diagnosis-report** body focus: symptom, root cause, evidence (CLI output), exact fix (file +
  change), classification (code / config / infra), `to` target + slash-command.

## Standard handshake (every agent)

1. **Intake (P0/P1):** read any existing work-order / result for this capability in
   `docs/handoff/<capability>/` first; skip re-analysis of anything already recorded.
2. **Write** the output record to `docs/handoff/<capability>/`.
3. **State** the outcome and close with the single next action:

> **Hand off:** run `/<command>` (`@<agent>`) — `<one-line why>`. Context: `docs/handoff/<cap>/<record>.md`

This closes the deploy/debug loop: the debugger reads `deploy-report.md` (image tag, OCIDs, smoke
result) and skips rediscovery; the deployer reads `diagnosis-report.md` (root cause + exact fix).

## Invocation vocabulary

| Phrase | Meaning | Where used |
|---|---|---|
| **"Hand off: run `/<command>` (`@<agent>`) — <why>"** | User-mediated: the agent writes a record and points the user to the next step | EVERY transition, including `@oci-serverless-stack` -> streams A/B and back via `--integrate` |

The file records are the source of truth; `.claude/` is the only agent definition surface of this
factory. Command / skill entry points are `.claude/skills/*` with `context: fork` + `agent:`.

## Full flow

```
                         BUILD SIDE
@oci-serverless-architect (P6)
  └── writes work-orders → docs/handoff/<cap>/stream-{a,b,c}-*.md
                │  hand off: /provision-oci-serverless-stack
                ▼
@oci-serverless-stack (P4, default mode: validates the 3 work-orders)
  │  hand off: /develop-java-function (@oci-functions-java) and /provision-oci-infra (@oci-terraform)
  ├── stream-a-java.md ── hand off ──► @oci-functions-java ─► result-java.md
  ├── stream-b-*.md ───── hand off ──► @oci-terraform ──────► result-terraform-infra.md
  │        └────── barrier: both results present with outcome: success ──┘
  │  hand off: /provision-oci-serverless-stack <slug> --integrate
@oci-serverless-stack (--integrate: stream C + cross-domain check)
  └── stream-c-*.md ──────────────────────────────────────► result-terraform-integration.md
                │  hand off: /deploy-oci-function
                ▼
                          RUN SIDE
@oci-deployer (P0–P6)
  ├── reads diagnosis-report.md (if present) → applies a recorded Dockerfile/pom.xml/config fix
  └── writes deploy-report.md
                │  on failure → hand off: /debug-oci-function
                ▼
@oci-debugger (P0–P4)
  ├── reads deploy-report.md → skips rediscovery
  └── writes diagnosis-report.md
                │  hand off: /develop-java-function (@oci-functions-java) (code), /deploy-oci-function (@oci-deployer) (configuration/dependency/image), /provision-oci-infra (@oci-terraform) (infra) or /observe-oci-workload (@oci-observability) (observability gap)
                └──────────────► back to RUN SIDE
```

## Worked example (frontmatter only)

```yaml
# docs/handoff/func-api-facade/stream-a-java.md
kind: work-order
from: "@oci-serverless-architect"
to: "@oci-functions-java"
capability: func-api-facade
stream: a-java
dependsOn: none
status: pending
createdAt: 2026-07-02T10:00:00Z
---
# docs/handoff/func-api-facade/result-java.md
kind: report
from: "@oci-functions-java"
to: "@oci-serverless-stack"
refs: stream-a-java.md
capability: func-api-facade
outcome: success
createdAt: 2026-07-02T10:20:00Z
```

Bodies follow the templates in `../assets/` (`work-order`, `result`, `deploy-report`,
`diagnosis-report`).

## Lifecycle & rules

1. Work-orders are generated by `@oci-serverless-architect` (P6) after user approval.
2. Result records are written by each agent at the end of its workflow, before the hand-off line.
3. Intake first: every agent reads existing records for the capability before analysing.
4. Work-order `status` progresses `pending → in-progress → completed`.
5. Stream C must not start until stream A and B results are both present with `outcome: success`.
6. The architect creates work-orders and never edits source code.
7. The stack agent validates and, in `--integrate` mode, consumes the stream results; the stream agents write their results back.
8. Records are overwritten within a capability on each new cycle; the profile's attempt limits are therefore not meaningful counters. This is stated by the generic protocol (skill `coordinating-agent-handoffs`, blueprint `protocol.md`): "A profile may declare that a family overwrites records per cycle (OCI legacy); then counters that depend on history (limits) are not meaningful" (High).
9. A `diagnosis-report.md` names the owner in its `to` field; the user routes by that owner (Java code to `@oci-functions-java`, configuration, dependency and image to `@oci-deployer`, infrastructure to `@oci-terraform`, an observability gap to `@oci-observability`), as the Hand off line says.
