# Handoff Protocol

This directory is the **single hub for all agent-to-agent handoffs** in the OCI serverless lifecycle. Every transition between the 6 subagents (`@oci-serverless-architect`, `@oci-serverless-stack`, `@oci-functions-java`, `@oci-terraform`, `@oci-deployer`, `@oci-debugger`) passes context through a **structured record file** here — never through lossy prose.

The protocol is **user-mediated**: an agent finishes its work, writes a record, and tells the user which slash-command to run next. It does not auto-chain (the one exception is the existing `@oci-serverless-stack → @oci-functions-java / @oci-terraform` parallel fan-out, which is programmatic — see [Invocation Vocabulary](#invocation-vocabulary)).

## Why

Without structured handoff, context (image tag, OCIDs, root cause, evidence, files changed) is lost at each hop. A re-invoked deployer redoes discovery blind; the stack orchestrator parses freeform prose instead of a schema. Records fix that: each agent reads what the previous one recorded and skips re-analysis.

---

## Directory Layout (per-capability)

Records are namespaced by **capability slug** (= the function name, e.g. `func-api-facade`). This lets multiple capabilities be in flight at once and preserves history — records within a capability are overwritten on each new cycle, but different capabilities never collide.

```
docs/handoff/
  README.md                          # this file — the protocol spec
  _templates/                        # skeletons agents copy (reduce drift)
    work-order.md
    report.md
    deploy-report.md
    diagnosis-report.md
  <capability-slug>/                 # e.g. func-api-facade/
    stream-a-java.md                 # architect → java        (work-order)
    stream-b-terraform-infra.md      # architect → terraform   (work-order)
    stream-c-terraform-integration.md
    report-java.md                   # java → stack            (report)
    report-terraform-infra.md        # terraform → stack       (report)
    report-terraform-integration.md
    deploy-report.md                 # deployer → debugger/user (report)
    diagnosis-report.md              # debugger → deployer/tf   (report)
```

---

## Record Kinds

There are two kinds of record, distinguished by the `kind:` frontmatter field.

### 1. Work-order (forward handoff — "someone must DO X")

Produced when work is being requested. The 3 architect streams are work-orders.

Frontmatter:

```yaml
---
kind: work-order
from: "@oci-serverless-architect"
to: "@oci-functions-java"          # target agent
capability: func-api-facade         # slug = function name
stream: a-java                      # a-java | b-terraform-infra | c-terraform-integration
dependsOn: none                     # none | [stream-a, stream-b]
status: pending                     # pending | in-progress | completed
createdAt: <ISO 8601>               # placeholder OK if the writer has no Bash (a downstream Bash-capable agent stamps it)
---
```

Body sections: **Scope**, **Components** (checklist), **Constraints**, **Dependencies** (what must already exist), **Acceptance Criteria** (checklist).

### 2. Report (backward handoff — "someone DID X, here's the outcome")

Produced when an agent finishes and hands results back or forward. Every leaf agent writes one.

Frontmatter:

```yaml
---
kind: report
from: "@oci-functions-java"
to: "@oci-serverless-stack"         # who consumes this next
capability: func-api-facade
refs: stream-a-java.md              # the work-order / report this answers
outcome: success                    # success | partial | failed
createdAt: <ISO 8601>
---
```

Body sections:

- **What changed** — files created/modified (paths)
- **Resources / OCIDs** — image tag, function OCID, vault/bucket/api-deployment OCIDs
- **Validation** — commands run + results (`mvn compile`, `terraform validate`, smoke HTTP status)
- **Acceptance status** — each acceptance criterion marked ✅ / ❌
- **Next action** — recommended agent + slash-command + one-line why
- **Open issues / blockers** — anything unresolved

Two specialized reports reuse this schema with a fixed body focus:

| Record | Written by | Consumed by | Body focus |
|---|---|---|---|
| `deploy-report.md` | `@oci-deployer` (P5/P6) | `@oci-debugger`, user | image tag deployed, tfvars diff, `terraform plan` summary, smoke HTTP status+body, observability-validation result, outcome |
| `diagnosis-report.md` | `@oci-debugger` (P4) | `@oci-deployer` / `@oci-terraform` / `@oci-functions-java` | symptom, root cause, evidence (CLI output), exact fix (file + change), classification (code / config / infra), `to` target + slash-command |

---

## Standard Handshake (every agent)

Every agent **closes** with the same 3-part block:

1. **Write** its report record to `docs/handoff/<capability>/`.
2. **State** the outcome + the single next action.
3. **Point** the user at the record file so the next agent reads it as P0/P1 context.

Single phrasing — this replaces all "direct the user to / instruct the user to invoke / suggest @X" variants:

> **Hand off:** run `/<command>` (`@<agent>`) — `<one-line why>`. Context: `docs/handoff/<cap>/<record>.md`

Every agent's **intake** (P0/P1) is standardized too:

> Read any existing work-order / report for this capability in `docs/handoff/<capability>/` first. Use it as context. Skip re-analysis of anything already recorded there.

This is what closes the deploy↔debug loop: the debugger reads `deploy-report.md` (image tag, OCIDs, smoke result already captured) and skips rediscovery; the deployer reads `diagnosis-report.md` (root cause + exact fix already found) and applies it directly.

---

## Invocation Vocabulary

Two distinct mechanisms — keep them distinct in agent instructions:

| Phrase | Meaning | Where used |
|---|---|---|
| **"Delegate to @X"** | Programmatic — the agent invokes the sub-agent itself, no return to the user. Mechanism per tool: Claude Code = the `Agent` tool; GitHub Copilot = the `agent` tool. | ONLY the `@oci-serverless-stack → @oci-functions-java / @oci-terraform` parallel fan-out. |
| **"Hand off: run `/cmd` (@X)"** | User-mediated — the agent writes a record and points the user to the next step. Mechanism per tool: a slash-command / prompt (`/deploy-function`), an `@`-mention of the target agent, or a Copilot `handoffs:` button. | Every leaf→next transition (architect→stack, java→deployer, terraform→deployer, deployer→debugger, debugger→deployer/terraform). |

The **file records are the source of truth** and are identical across tools; only the invocation mechanism differs. See [Per-tool mechanism](#per-tool-mechanism) below.

## Per-tool mechanism

The protocol is tool-neutral: the `docs/handoff/<capability>/` records and their schema are the shared contract. Each tool realizes the abstract steps (intake-read, delegate, hand-off, record-write) with its own primitives:

| Abstract step | Claude Code | GitHub Copilot (IDE: VS Code/VS/JetBrains) | GitHub Copilot (cloud agent / CLI) |
|---|---|---|---|
| Sub-agent definition | `.claude/agents/*.md` | `.github/agents/*.agent.md` (also reads `.claude/agents`) | not supported — agents collapse into instructions |
| Intake-read / record-write | Read / Write tools | `search` / `editFiles` tools | file read/write per the path-scoped instructions (`.github/instructions/handoff-protocol.instructions.md`, `applyTo: "**"`) |
| Programmatic delegation | `Agent` tool | `agent` tool | not available — user drives each step |
| User-mediated hand-off | prose "run `/cmd`" | `handoffs:` frontmatter button, `@`-mention, or `/prompt` | prose "run `/cmd`" in the record's **Next action** |
| Command / skill entry point | `.claude/skills/*` (`context: fork` + `agent:`) | `.github/prompts/*.prompt.md` (`agent:` routes to a custom agent) | n/a (no prompt files) |

On surfaces without agents/prompt files (GitHub.com cloud agent, CLI), the file records **are** the entire mechanism: the agent reads the latest record, does the work, writes the next record, and states the next action in prose. No feature is lost — only the clickable UX.

---

## Full Flow

```
                         BUILD SIDE
@oci-serverless-architect (P6)
  └── writes work-orders → docs/handoff/<cap>/stream-{a,b,c}.md
                │  hand off: /add-serverless-stack
                ▼
@oci-serverless-stack (P4)
  ├── reads stream-a-java.md ──── delegate ──► @oci-functions-java ─► report-java.md
  ├── reads stream-b-*.md ─────── delegate ──► @oci-terraform ──────► report-terraform-infra.md
  │        └────── barrier: both reports present ──────┘
  └── reads stream-c-*.md ─────── delegate ──► @oci-terraform ──────► report-terraform-integration.md
                │  hand off: /deploy-function
                ▼
                          RUN SIDE
@oci-deployer (P0–P6)
  ├── reads diagnosis-report.md (if present) → applies recorded fix, skips rediscovery
  └── writes deploy-report.md  (image tag, smoke result, OCIDs, outcome)
                │  on failure → hand off: /debug-function
                ▼
@oci-debugger (P0–P4)
  ├── reads deploy-report.md → skips P0–P1 rediscovery
  └── writes diagnosis-report.md (root cause, exact fix, classification, target)
                │  hand off: /deploy-function (code/config) or @oci-terraform (infra)
                └──────────────► back to RUN SIDE (loop closes)
```

---

## Worked Examples

### Work-order (`docs/handoff/func-api-facade/stream-a-java.md`)

```markdown
---
kind: work-order
from: "@oci-serverless-architect"
to: "@oci-functions-java"
capability: func-api-facade
stream: a-java
dependsOn: none
status: pending
createdAt: 2026-07-02T10:00:00Z
---

## Scope
Create the `services/func-api-facade/` Java project (handler + DTOs + tests).

## Components
- [ ] `ApiFacadeHandler` — API Gateway event handler
- [ ] `pom.xml` — FDK 1.1.x + httpclient-jersey
- [ ] `func.yaml` — 256MB / 60s timeout
- [ ] Unit tests (FnTestingRule)

## Constraints
- Handler must implement the initError pattern.
- Dockerfile must include CMD.

## Dependencies
- None (can start immediately, parallel with stream-b).

## Acceptance Criteria
- [ ] `mvn compile` passes
- [ ] `mvn test` passes
- [ ] Dockerfile has CMD
```

### Report (`docs/handoff/func-api-facade/report-java.md`)

```markdown
---
kind: report
from: "@oci-functions-java"
to: "@oci-serverless-stack"
refs: stream-a-java.md
capability: func-api-facade
outcome: success
createdAt: 2026-07-02T10:20:00Z
---

## What changed
- Created `services/func-api-facade/src/main/java/.../ApiFacadeHandler.java`
- Created `pom.xml`, `func.yaml`, `Dockerfile`

## Resources / OCIDs
- (none — no infra created; image not yet built)

## Validation
- `mvn compile` → ✅
- `mvn test` → ✅ 4 passing

## Acceptance status
- [x] mvn compile passes
- [x] mvn test passes
- [x] Dockerfile has CMD

## Next action
Ready for deploy. Hand off: run `/deploy-function` (`@oci-deployer`).

## Open issues / blockers
- None.
```

### deploy-report (`docs/handoff/func-api-facade/deploy-report.md`)

```markdown
---
kind: report
from: "@oci-deployer"
to: "@oci-debugger"
refs: report-java.md
capability: func-api-facade
outcome: failed
createdAt: 2026-07-02T10:40:00Z
---

## What changed
- Built + pushed `gru.ocir.io/<ns>/serverless-app/func-api-facade:0.0.1`
- Updated `infra/environments/dev/terraform.tfvars` image ref
- `terraform apply` — 1 change (function image)

## Resources / OCIDs
- Image: `func-api-facade:0.0.1`
- Function OCID: `ocid1.fnfunc.oc1.sa-saopaulo-1.aaaa...`
- App OCID: `ocid1.fnapp.oc1.sa-saopaulo-1.bbbb...`
- Endpoint: `https://<gw>/api/facade`

## Validation
- Smoke test → **HTTP 500** body: `{"erro":"Function init failed","detalhe":"...No http provider available"}`
- Observability validation → not run (deploy failed)

## Acceptance status
- [ ] Smoke test 2xx/400 → ❌ (500)

## Next action
Hand off: run `/debug-function` (`@oci-debugger`) — init failure needs diagnosis. Context: this file.

## Open issues / blockers
- Auto-fix cycle 1 attempted (added CMD) — did not resolve. Escalating.
```

### diagnosis-report (`docs/handoff/func-api-facade/diagnosis-report.md`)

```markdown
---
kind: report
from: "@oci-debugger"
to: "@oci-deployer"
refs: deploy-report.md
capability: func-api-facade
outcome: success
createdAt: 2026-07-02T10:55:00Z
---

## What changed
- (diagnosis only — no code changed; @oci-debugger never edits code)

## Root cause
Missing OCI SDK HTTP transport → init crash on first Vault call.

## Evidence
- `grep httpclient-jersey pom.xml` → no match
- deploy-report smoke body: `No http provider available`

## Exact fix
Add to `services/func-api-facade/pom.xml`:
```xml
<dependency>
  <groupId>com.oracle.oci.sdk</groupId>
  <artifactId>oci-java-sdk-common-httpclient-jersey</artifactId>
</dependency>
```

## Classification
code (pom.xml dependency)

## Next action
Hand off: run `/deploy-function` (`@oci-deployer`) — apply pom.xml fix, rebuild, redeploy. Context: this file.

## Open issues / blockers
- None.
```

---

## Lifecycle & Rules

1. **Work-orders** generated by `@oci-serverless-architect` (P6) after user approval, under `docs/handoff/<capability>/`.
2. **Reports** written by each agent at the end of its workflow, before the hand-off line.
3. **Intake first** — every agent reads existing records for the capability before analyzing.
4. **`status`** on work-orders progresses `pending → in-progress → completed`.
5. **Stream C** must not start until stream A and B reports are both present with `outcome: success`.
6. The architect **creates** work-orders and never edits source code.
7. The stack agent **reads and mediates** — sub-agents receive context from the stack, and write their reports back.
8. Records are **overwritten** within a capability on each new cycle; different capabilities are isolated by slug.

## Keep the two agent mirrors in sync

The 6 agents are defined twice — `.claude/agents/*.md` (Claude Code) and `.github/agents/*.agent.md` (GitHub Copilot). They **must stay behaviorally identical**; only the tool vocabulary differs (Claude: `Agent`/`Read`/`Write`; Copilot: `agent`/`search`/`editFiles` + native `handoffs:` frontmatter). When you change any handoff-relevant part of one, mirror it in the other:

- **Intake step** — the P0 "read `docs/handoff/<capability>/…`" instruction.
- **Close step** — the report/record write (`report-*.md`, `deploy-report.md`, `diagnosis-report.md`) + the standard hand-off line.
- **Delegation contract** — stack's "require a report back"; architect's work-order schema.
- **Copilot-only** — `handoffs:` frontmatter targets must name existing agents.

Cross-surface instructions live in `.github/instructions/handoff-protocol.instructions.md` (`applyTo: "**"`, honored by VS Code + cloud agent + CLI) and, for Claude, the pointer in `CLAUDE.md`. This spec (`docs/handoff/README.md`) is the shared, tool-neutral source of truth for both.
