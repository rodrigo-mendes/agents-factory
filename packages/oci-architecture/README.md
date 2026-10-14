# oci-architecture

OCI serverless architecture package — knowledge skills and agents for designing and implementing
OCI Functions + API Gateway + IAM + Networking + Vault + Streaming architectures.

Part of the OCI package family. Depends on `factory-core` and `oci-core`.

## Contents

### Agents

| Agent | Role | Route via |
|---|---|---|
| `oci-serverless-architect` | Advisory architect — designs architectures, produces ADRs and handoff work-orders. No code generation. | `/design-oci-architecture` |
| `oci-serverless-stack` | Full-stack deployer — executes work-orders by coordinating `@oci-functions-java` and `@oci-terraform` in parallel + sequential streams. | `/provision-oci-serverless-stack` |

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

## Typical workflow

```
1. /design-oci-architecture full-stack
   → @oci-serverless-architect produces docs/handoff/<capability>/ work-orders

2. /provision-oci-serverless-stack <capability-slug>
   → @oci-serverless-stack executes:
       Stream A (@oci-functions-java) + Stream B (@oci-terraform) in parallel
       Stream C (@oci-terraform) after synchronization
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
