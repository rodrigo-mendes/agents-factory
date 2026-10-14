---
name: design-oci-architecture
description: "Routes to the OCI Serverless Architect for designing and reviewing OCI serverless architectures (advisory only — produces ADRs, diagrams, and handoff work-orders; no code). Use when designing a new serverless capability, reviewing an existing architecture, or generating the implementation handoff plan for @oci-serverless-stack."
argument-hint: "<scope> (e.g. full-stack | api-surface | security-model | network-topology)"
context: fork
agent: oci-serverless-architect
disable-model-invocation: true
---

# design-oci-architecture

Routes to `@oci-serverless-architect` — the advisory-only OCI Serverless Solution Architect.

## What the agent does

- Analyzes the existing codebase (`.tf`, `.java`, `func.yaml`, `pom.xml`) to map the current architecture.
- Designs serverless solutions following OCI Best Practices (Functions + API Gateway + IAM + Networking + Vault).
- Produces Architecture Decision Records (ADRs), ASCII component diagrams, and implementation roadmaps.
- Generates structured work-order records under `docs/handoff/<capability>/` for hand-off to `@oci-serverless-stack`.

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

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
