# oci-terraform

OCI Terraform domain package — knowledge skills, a provisioning agent, and operational scripts for
OCI serverless infrastructure authored in Terraform. Part of the OCI package family.

## Package Contents

### Agent

| Agent | Purpose |
|---|---|
| `oci-terraform` | Provisions OCI serverless resources via Terraform (P0–P5 workflow) |

### Skills (20 total)

**Provisioning skills (knowledge — load on demand):**

| Skill | Covers |
|---|---|
| `provisioning-oci-functions` | OCI Functions Application + Function |
| `provisioning-oci-api-gateway` | API Gateway + Deployment (JWT, CORS, rate limiting) |
| `provisioning-oci-networking` | VCN, Subnets, NSGs, Route Tables, Gateways |
| `provisioning-oci-iam` | Dynamic Groups, Policies |
| `provisioning-oci-vault` | KMS Vault, Keys, Secrets |
| `provisioning-oci-streaming` | Stream Pool, Stream (Kafka-compatible) |
| `provisioning-oci-connector-hub` | Service Connector Hub (fan-out to Functions) |
| `provisioning-oci-events` | OCI Events (event rules, triggers) |
| `provisioning-oci-event-driven-pubsub` | End-to-end pub/sub pattern |
| `provisioning-oci-object-storage` | Buckets, versioning, lifecycle policies |
| `provisioning-oci-logging` | Log Groups, Service Logs |
| `provisioning-oci-apm` | APM Domain, data keys, alarms |
| `provisioning-oci-serverless-stack` | Full serverless stack composition |
| `provisioning-custom-dashboard-oci-observability` | Custom OCI Management Dashboards |

**Engineering and management skills:**

| Skill | Covers |
|---|---|
| `engineering-terraform-oci` | Terraform code engineering patterns |
| `managing-terraform-cicd` | Azure DevOps pipeline standards |
| `managing-terraform-state` | State management, backends, isolation |
| `testing-terraform-modules` | Native Terraform testing (.tftest.hcl) |

**Action commands:**

| Skill | Routes to | Purpose |
|---|---|---|
| `provision-oci-infra` | `oci-terraform` | Fork-to-agent entry point for provisioning requests |
| `cleaning-up-oci-resources` | `oci-terraform` | Teardown of OCI compartment resources via script |

### Instructions (8 — auto-loaded on `.tf`, `.tfvars`, `.hcl`, pipeline YAML)

| Instruction | Trigger scope |
|---|---|
| `terraform-standards` | `**/*.tf`, `**/*.tfvars`, `**/*.hcl` |
| `terraform-project-config` | `**/*.tf`, `**/*.tfvars`, `**/*.hcl` |
| `terraform-modules` | `**/*.tf`, `**/*.tfvars`, `**/*.hcl` |
| `terraform-multi-function` | `**/*.tf`, `**/*.tfvars`, `**/*.hcl` |
| `terraform-state-backend` | `**/*.tf`, `**/*.tfvars`, `**/*.hcl` |
| `terraform-testing` | `**/*.tf`, `**/*.tfvars`, `**/*.hcl` |
| `terraform-skills` | `**/*.tf`, `**/*.tfvars`, `**/*.hcl` |
| `terraform-cicd` | `**/*.tf`, `**/*.tfvars`, `**/*.hcl`, `**/azure-pipelines*.yml` |

### Scripts

| Script | Purpose |
|---|---|
| `cleaning-up-oci-resources/scripts/oci-cleanup.sh` | Parametrized 8-phase OCI compartment teardown |

## Quick Start

```bash
# Provision OCI infrastructure (forks to oci-terraform agent)
/provision-oci-infra <capability-slug> [service-scope]

# Clean up an OCI compartment (review first)
export OCI_COMPARTMENT_OCID="ocid1.compartment.oc1...<value>"
export OCI_TENANCY_OCID="ocid1.tenancy.oc1...<value>"
export OCI_NAMESPACE="<your-namespace>"
./.apm/skills/cleaning-up-oci-resources/scripts/oci-cleanup.sh --dry-run
```

## Dependencies

```yaml
dependencies:
  apm:
    - path: ../factory-core
    - path: ../oci-core
```

## Reference PoC

The blueprints in each provisioning skill contain short HCL worked examples sourced from
`workspace/poc-oci-serverless/infra/modules/`. Each snippet is annotated with its source path
(e.g. `# from infra/modules/function-app/main.tf`) and key patterns to observe.

## Version Targets

- Terraform: >= 1.7 (native test support)
- OCI Provider: `oracle/oci` >= 6.0, < 9.0
- OCI CLI: >= 3.x (for cleanup script)
