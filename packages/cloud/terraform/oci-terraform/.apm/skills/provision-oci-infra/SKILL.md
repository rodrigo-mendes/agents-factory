---
name: provision-oci-infra
description: "Provisions OCI serverless infrastructure with Terraform by invoking the oci-terraform agent. Use when adding or modifying OCI resources (Functions, API Gateway, IAM, Networking, Vault, Streaming, Events) via Terraform code generation."
argument-hint: "<capability-slug> [streaming|functions|api-gateway|vault|networking|iam|events|full-stack]"
context: fork
agent: oci-terraform
disable-model-invocation: true
---

# Provision OCI Infrastructure

## Function

Routes infrastructure provisioning requests to the `oci-terraform` agent, which follows a mandatory
P0–P5 workflow (Verify → Analyze → Consult → Propose → Implement → Validate) and delegates all
pattern knowledge to the appropriate `provisioning-oci-*` skill.

## Usage

```
/provision-oci-infra <capability-slug> [service-scope]
```

Examples:

```
/provision-oci-infra event-pubsub streaming
/provision-oci-infra api-handler functions api-gateway
/provision-oci-infra serverless-full full-stack
```

## What the Agent Does

1. **P0** — reads any existing handoff records for the capability and loads the relevant skill(s)
2. **P1** — scans existing `.tf` files for provider version, module structure, and provisioned resources
3. **P2** — extracts ✅ Always Do / 🚫 Never Do / ⚠️ Ask First rules from the loaded skills
4. **P3** — presents a plan (resources, naming, module structure, dependencies) and waits for approval
5. **P4** — generates `.tf` files following skill patterns; respects layer order (Network → IAM → Service → Events)
6. **P5** — runs `terraform fmt -check` and `terraform validate`; writes a handoff report

## Service-to-Skill Mapping

| Service scope | Skill loaded |
|---|---|
| `functions` | `provisioning-oci-functions` |
| `api-gateway` | `provisioning-oci-api-gateway` |
| `iam` | `provisioning-oci-iam` |
| `networking` | `provisioning-oci-networking` |
| `vault` | `provisioning-oci-vault` |
| `streaming` | `provisioning-oci-streaming` |
| `events` | `provisioning-oci-events` |
| `connector-hub` | `provisioning-oci-connector-hub` |
| `full-stack` | `provisioning-oci-serverless-stack` |

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
