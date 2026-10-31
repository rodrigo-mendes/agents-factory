---
name: cleaning-up-oci-resources
description: "Guides teardown of all OCI resources in a compartment using the parametrized oci-cleanup.py script. Use when decommissioning a PoC, clearing a test environment, or removing a serverless stack from OCI."
argument-hint: "[--dry-run] (compartment from OCI_COMPARTMENT_OCID)"
context: fork
agent: oci-terraform
disable-model-invocation: true
---

# Cleaning Up OCI Resources

## Version Context

**Technology**: OCI CLI + Python 3 (standard library only; Linux, macOS, Windows)  
**CLI Version**: OCI CLI >= 3.x  
**Target Services**: Functions, API Gateway, Vault/KMS, Object Storage, Networking, IAM, OCIR (8 phases)  
**Support Status**: Active  

## Function

Tears down all OCI resources in a target compartment across 8 ordered phases. The script is fully
parametrized — no OCIDs, namespaces, or profile names are hardcoded. All values are injected via
environment variables with validation at startup.

## Quick Navigation

- **[Script](./scripts/oci-cleanup.py)** — parametrized cleanup script (offline tests: `python3 tests/run_tests.py`)
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Always Do](#-always-do) / [Ask First](#️-ask-first) / [Never Do](#-never-do)** — guardrails below

## Blueprints & Guardrails

- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md) — five scenarios: dry-run, missing env var, live-run gate, scheduled deletion, empty filters.
- Guardrails: the Always Do, Ask First and Never Do sections at the end of this file.

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
export OCI_PROJECT_FILTER="myproject"    # regex for IAM + tenancy-level OCIR filter (no default: empty matches nothing)
export VAULT_DELETE_DAYS=14              # min 7
export SECRET_DELETE_DAYS=3             # min 2

# 3. Preview (no deletions)
python3 scripts/oci-cleanup.py --dry-run

# 4. Execute: the USER runs this and types DELETE (an agent never does)
python3 scripts/oci-cleanup.py
```

Exit status (unchanged from the former `oci-cleanup.sh`): `0` only for a live run that deleted
something with no failure, or when aborted at the prompt; `1` for a dry-run, missing env vars, or a live
run with failures or nothing deleted.

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
| 8 | Container images, then repositories | Searches tenancy level if compartment returns empty, only when `OCI_PROJECT_FILTER` is set |

## ✅ Always Do

- Run `--dry-run` first and review output before live execution.
- Set `OCI_COMPARTMENT_NAME` and `OCI_PROJECT_FILTER` explicitly so phase 7 filters correctly. Neither has a default: an empty filter matches nothing (no tenancy policy or dynamic group is selected, and an empty `OCI_PROJECT_FILTER` also skips the tenancy-level OCIR search); the former bash version treated an empty filter as match-all (changed 2026-10-29).
- Confirm Vault/Secret pending-deletion windows (`VAULT_DELETE_DAYS` >= 7, `SECRET_DELETE_DAYS` >= 2) before running live.
- Store OCIDs in a `.env` file or a secrets manager — never inline them in scripts or commit them to source control.

## ⚠️ Ask First

- **The live run itself**: an agent only runs `--dry-run` and returns its output. The live run needs the user's own explicit approval naming the compartment OCID, and the user runs it and types `DELETE` (it deletes cloud resources; Vault and Secret deletions cannot be stopped after their window).

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
| An agent types or pipes `DELETE` (e.g. `echo DELETE \| python3 scripts/oci-cleanup.py`) on the user's behalf | Run `--dry-run`, return the output, and let the user run the live command |
