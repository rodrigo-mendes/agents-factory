---
name: design-oci-architecture
description: "Routes to the OCI Serverless Architect for designing and reviewing OCI serverless architectures (advisory only — produces ADRs, diagrams, and handoff work-orders; no code). Use when designing a new serverless capability, reviewing an existing architecture, or generating the implementation handoff work-orders (executed afterwards via /provision-oci-serverless-stack, or /develop-java-function + /provision-oci-infra)."
argument-hint: "<scope: full-stack | api-surface | security-model | network-topology | object-storage | event-driven-pubsub> [capability-slug]"
context: fork
agent: oci-serverless-architect
disable-model-invocation: true
---

# design-oci-architecture

Routes to `@oci-serverless-architect` — the advisory-only OCI Serverless Solution Architect.

## What the agent does

- Analyzes the existing codebase (`.tf`, `.java`, `func.yaml`, `pom.xml`) to map the current architecture.
- Designs serverless solutions following OCI Best Practices (Functions + API Gateway + IAM + Networking + Vault).
- Produces Architecture Decision Records (ADRs), component diagrams (Mermaid preferred, ASCII fallback), and implementation roadmaps.
- Generates structured work-order records under `docs/handoff/<capability>/` (the only files it writes; needs a capability slug, kebab-case). Execute with ONE path: `/provision-oci-serverless-stack <capability-slug>` (one-shot), or per stream `/develop-java-function` + `/provision-oci-infra` — never both.
- Is non-interactive: when context is missing it returns numbered questions with `Status: NEEDS-INPUT` and writes nothing.

## Agent does NOT do

- Generate `.tf` or `.java` implementation code.
- Edit files in the workspace beyond `docs/handoff/`.

## Scopes

| Argument | Agent focus |
|---|---|
| `full-stack` | Complete serverless solution: Functions + API Gateway + IAM + Networking |
| `api-surface` | Set of API routes, auth strategy, throttling, CORS |
| `security-model` | Secrets management (Vault), encryption, least-privilege IAM |
| `network-topology` | VCN design, subnets, NSGs, Service Gateway connectivity |
| `object-storage` | Buckets, tiers, data protection, access patterns, object events |
| `event-driven-pubsub` | Streaming, Service Connector Hub, consumers, fan-out |

The optional second argument is the capability slug (`[a-z0-9-]+`); it is only required to write work-orders.

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
