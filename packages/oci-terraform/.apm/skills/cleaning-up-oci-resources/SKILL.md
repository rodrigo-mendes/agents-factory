---
name: cleaning-up-oci-resources
description: "Guides teardown of all OCI resources in a compartment using the parametrized oci-cleanup.sh script. Use when decommissioning a PoC, clearing a test environment, or removing a serverless stack from OCI."
argument-hint: "<compartment-ocid> [--dry-run]"
context: fork
agent: oci-terraform
disable-model-invocation: true
---

# Cleaning Up OCI Resources

## Version Context

**Technology**: OCI CLI + Bash  
**CLI Version**: OCI CLI >= 3.x  
**Target Services**: Functions, API Gateway, Vault/KMS, Object Storage, Networking, IAM, OCIR (8 phases)  
**Support Status**: Active  

## Function

Tears down all OCI resources in a target compartment across 8 ordered phases. The script is fully
parametrized — no OCIDs, namespaces, or profile names are hardcoded. All values are injected via
environment variables with validation at startup.

## Quick Navigation

- **[Script](./scripts/oci-cleanup.sh)** — parametrized cleanup script
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**

## Usage

```bash
# 1. Set required env vars (NO hardcoded values in the script itself)
export OCI_COMPARTMENT_OCID="ocid1.compartment.oc1...<your-compartment>"
export OCI_TENANCY_OCID="ocid1.tenancy.oc1...<your-tenancy>"
export OCI_NAMESPACE="<your-object-storage-namespace>"

# 2. Optional overrides
export OCI_PROFILE="my-profile"          # default: DEFAULT
export OCI_AUTH="security_token"         # default: api_key
export OCI_REGION="eu-frankfurt-1"       # default: sa-saopaulo-1
export OCI_COMPARTMENT_NAME="my-comp"    # for IAM name filter
export OCI_PROJECT_FILTER="myproject"    # regex for IAM filter
export VAULT_DELETE_DAYS=14              # min 7
export SECRET_DELETE_DAYS=3             # min 2

# 3. Preview (no deletions)
./scripts/oci-cleanup.sh --dry-run

# 4. Execute (requires typing DELETE to confirm)
./scripts/oci-cleanup.sh
```

## Cleanup Phases (order is mandatory — dependencies flow top to bottom)

| Phase | Resources | Notes |
|---|---|---|
| 1 | Monitoring alarms, log groups/logs, ONS topics/subscriptions | Observability first — no data-plane dependencies |
| 2 | API Gateway deployments, then gateways | Deployments before gateways |
| 3 | Functions, then applications | Functions before applications |
| 4 | Vault secrets (scheduled), KMS vaults (scheduled) | Minimum 2d/7d pending-deletion; irreversible |
| 5 | Object Storage objects (bulk), then buckets | Bulk-delete objects before bucket deletion |
| 6 | NSG rules → NSGs → Subnets → Route Tables → Security Lists → Gateways → VCN | Strict dependency order |
| 7 | Compartment-level policies, tenancy-level policies (filtered), dynamic groups | Filtered by `OCI_PROJECT_FILTER` |
| 8 | Container images, then repositories | Searches tenancy level if compartment returns empty |

## ✅ Always Do

- Run `--dry-run` first and review output before live execution.
- Set `OCI_COMPARTMENT_NAME` and `OCI_PROJECT_FILTER` so phase 7 filters correctly — without them, all tenancy-root policies are enumerated but only matched ones are deleted.
- Confirm Vault/Secret pending-deletion windows (`VAULT_DELETE_DAYS` >= 7, `SECRET_DELETE_DAYS` >= 2) before running live.
- Store OCIDs in a `.env` file or a secrets manager — never inline them in scripts or commit them to source control.

## ⚠️ Ask First

- **Streaming streams with `prevent_destroy = true`**: the script deletes by compartment scan, not Terraform state. If a stream has retained messages you need, exclude it manually before running.
- **Shared compartments**: `OCI_COMPARTMENT_OCID` scopes ALL phase deletions. Verify it is the correct isolated compartment before confirming.
- **Tenancy-level IAM**: phase 7 searches the tenancy root for policies whose statements reference `OCI_COMPARTMENT_OCID` or match `OCI_PROJECT_FILTER`. Review the dry-run output carefully — it may surface shared policies.

## 🚫 Never Do

| Incorrect | Correct |
|---|---|
| Hardcode OCIDs, namespace, or profile in the script | Use env vars; the script validates they are set |
| Run live without `--dry-run` review first | Always dry-run, check FOUND count, then confirm |
| Set `VAULT_DELETE_DAYS` < 7 | OCI enforces a 7-day minimum; the API will reject lower values |
| Delete resources in a shared/production compartment | Target only isolated PoC/test compartments |
