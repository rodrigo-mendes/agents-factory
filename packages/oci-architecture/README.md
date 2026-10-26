# oci-architecture

OCI serverless architecture package — knowledge skills and agents for designing and implementing
OCI Functions + API Gateway + IAM + Networking + Vault + Streaming architectures.

Part of the OCI package family. Depends on `factory-core` and `oci-core`.

## Contents

### Agents

| Agent | Role | Route via |
|---|---|---|
| `oci-serverless-architect` | Advisory architect — designs architectures, produces ADRs and handoff work-orders. No code generation. | `/design-oci-architecture` |
| `oci-serverless-stack` | Full-stack deployer — executes work-orders (stream-a/b/c) in one shot, coordinating Java and Terraform streams in parallel + sequential order. | `/provision-oci-serverless-stack` |

### Routing Skills (action-command, invoke via `/`)

| Skill | Agent | Purpose |
|---|---|---|
| `design-oci-architecture` | `oci-serverless-architect` | Design or review a serverless architecture, produce handoff plan |
| `provision-oci-serverless-stack` | `oci-serverless-stack` | Execute an approved implementation plan end-to-end |

### Knowledge Skills (auto-invocable)

| Skill | Domain |
|---|---|
| `architecting-oci-serverless` | Patterns, guardrails, and integration guides for OCI Functions + API Gateway |
| `designing-oci-api-gateway` | API Gateway architecture: auth, routing, rate limiting, CORS, security |
| `designing-oci-networking` | VCN, subnets, NSGs, Service Gateway, connectivity |
| `designing-oci-object-storage` | Object Storage integration patterns |
| `designing-oci-vault-security` | Vault secrets management, encryption, least-privilege IAM |
| `designing-oci-event-driven-pubsub` | Event-driven pub/sub: Functions + Streaming + Service Connector Hub |

### PoC Worked Examples (in blueprints)

The following blueprints contain short, path-cited code/pattern examples from the validated reference
PoC (`workspace/poc-oci-serverless/`):

| Blueprint | PoC Source | Pattern |
|---|---|---|
| `architecting-oci-serverless/blueprints/poc-worked-examples.md` | `services/func-api-facade/`, `services/func-rr-rest-proxy/` | Cold-start init, handler dispatch, secret retrieval, observability |
| `designing-oci-api-gateway/blueprints/poc-worked-examples.md` | `services/func-api-facade/`, `services/func-rr-rest-proxy/`, `docs/patterns/01-request-reply/reference/rest-proxy/` | API Facade routing, REST Proxy multi-backend, OTel correlation |
| `designing-oci-event-driven-pubsub/blueprints/poc-worked-examples.md` | `docs/patterns/02-event-driven/02-event-driven-pub-sub.md`, `services/func-event-producer/` | SCH public pool constraint, producer func.yaml, cross-stream tracing, IAM policies |

### Instructions (scoped rules)

| File | Rules | Scope |
|---|---|---|
| `oci-architecture-guardrails.instructions.md` | OCI-R34–R54, R65–R71, R73–R81, R86–R88, R93–R103, R107–R110 | Platform, API Gateway, networking, Vault/IAM |
| `oci-architecture-data-events-guardrails.instructions.md` | OCI-R55–R64, R72, R82–R85, R89–R92, R104–R106, R111–R115 | Object Storage, event-driven pub/sub |

Both apply to `**/oci/**/*.tf`, `**/*oci*/**/*.tf` and `docs/handoff/**`; each rule cites its ID
and governing skill and does not duplicate skill content.

## Shared Knowledge Base

- `workspace/oci/_family_rules_v2026.md` — numbered rule IDs: `OCI-R01`–`OCI-R33` (functions/Java)
  and `OCI-R34`–`OCI-R115` (Architecture Rules: 31 Always, 28 Never, 23 Ask First), each with its
  source skill. The agent cites these IDs in its anti-pattern checks.

## Agent Constraints

- **Advisory only** — no `.tf` or `.java` generation; the only files written are handoff
  work-orders under `docs/handoff/<capability>/`
- **Non-interactive** — returns numbered questions (`Status: NEEDS-INPUT`) when context is missing; never assumes
- **Source-bound** — states no OCI facts of its own; preserves `(unverified)` / `(medium confidence)`
  tags and lists them in a final Questions / Limitations section
- **Handoff targets** — two alternative paths, run ONE, never both (streams would run twice):
  `/provision-oci-serverless-stack <capability-slug>` (one-shot), or per stream
  `/develop-java-function` (Java) + `/provision-oci-infra` (infrastructure). Work-orders use
  `status: pending`; the user must approve before any command runs
- **Capability slug** — kebab-case `[a-z0-9-]+`; required only to write work-orders (P6), not for the design
- **Write scope is prompt-enforced** — the agent has the `Write` tool, so the restriction to
  `docs/handoff/<capability>/` is an instruction, not a technical sandbox
- **Flat** — no sub-agent spawning, no plan mode; tools: `Read, Grep, Glob, Write`

## Typical workflow

```
1. /design-oci-architecture full-stack <capability-slug>
   → @oci-serverless-architect produces docs/handoff/<capability>/ work-orders (status: pending)

2. User approves, then run ONE path:
   (a) one-shot: /provision-oci-serverless-stack <capability-slug>
       → executes Stream A (Java) + Stream B (Terraform infra) in parallel,
         Stream C (Terraform integration) after synchronization
   (b) per stream: /develop-java-function (A) + /provision-oci-infra (B, then C)
   Never run (a) and (b) for the same work-orders.
```

## Dependencies

```yaml
dependencies:
  apm:
    - path: ../factory-core   # base rules, skill-frontmatter, agent-frontmatter
    - path: ../oci-core       # shared OCI provisioning skills (provisioning-oci-*)
```

Skills in this package reference provisioning skills from `oci-core` and `oci-terraform` (e.g.,
`provisioning-oci-api-gateway`, `provisioning-oci-streaming`) — those are cross-package links and
are expected to appear as unresolved in isolated verification runs.

## Validation

```bash
python .claude/skills/building-agent-packages/scripts/verify_package.py packages/oci-architecture
```

Cross-package links to `oci-terraform`, `oci-functions-java`, `oci-observability` skills are
expected and listed as informational — they are resolved at runtime when those packages are installed.
