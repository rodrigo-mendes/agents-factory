---
kind: work-order
from: "@oci-serverless-architect"
to: "@oci-terraform"
capability: func-api-facade
stream: b-terraform-infra
dependsOn: none
status: completed
createdAt: 2026-05-18T00:00:00Z
---

## Scope

Provision independent infrastructure resources required by the API Facade pattern that do NOT reference the function OCID. This includes the Vault module (currently missing) and an Object Storage bucket for the `/store` route.

## Components

- [ ] `infra/modules/vault/` — New module: Vault + Master Encryption Key + Secrets management
  - `main.tf` — `oci_kms_vault`, `oci_kms_key` (AES 256), `oci_vault_secret` (optional)
  - `variables.tf` — compartment_ocid, vault_name, key_name, environment, tags
  - `outputs.tf` — vault_id, key_id, vault_crypto_endpoint, vault_management_endpoint
  - `versions.tf` — terraform >= 1.5, oracle/oci >= 6.0
  - `README.md` — Module documentation
- [ ] Object Storage bucket resource (add to existing module or root composition)
  - Bucket name: `bucket-api-facade-{environment}`
  - Namespace: data source `oci_objectstorage_namespace`
  - Versioning: enabled
  - Auto-tiering: enabled for cost optimization
- [ ] Verify IAM policies cover Vault access (`read secret-bundles` — already exists ✅)
- [ ] Verify IAM policies cover Object Storage access (`manage objects` — already exists ✅)

## Constraints

### Vault Module Design

| Resource | Configuration |
|----------|--------------|
| `oci_kms_vault` | Type: `DEFAULT` (shared partition, no cost), display_name: `vault-{project_name}-{environment}` |
| `oci_kms_key` | Algorithm: AES, Length: 32 (256-bit), Protection mode: `SOFTWARE` (dev) / `HSM` (prod) |
| Naming | Follow pattern: `vault-{project_name}-{environment}`, `key-{project_name}-{environment}` |
| Tags | Apply `freeform_tags = var.tags` to all resources |

### Object Storage Bucket

| Attribute | Value |
|-----------|-------|
| Name | `bucket-api-facade-{environment}` |
| Access type | `NoPublicAccess` |
| Storage tier | `Standard` |
| Versioning | Enabled |
| Auto-tiering | `InfrequentAccess` |

### Module Standards

- Use `oracle/oci` provider (never `hashicorp/oci`)
- Follow existing module structure patterns from `infra/modules/network/`, `infra/modules/iam/`
- All resources must have `freeform_tags`
- Follow instructions in `.github/instructions/terraform-modules.instructions.md`
- Follow skill `provisioning-oci-vault/SKILL.md` for Vault provisioning

## Dependencies

- No external dependencies — this stream can start immediately
- Existing IAM policies already cover `read secret-bundles` and `manage objects`
- VCN and subnets already provisioned by `modules/network/`

## Acceptance Criteria

- [ ] `cd infra && terraform validate` passes
- [ ] `terraform fmt -check -recursive` passes
- [ ] New `modules/vault/` module created with proper structure
- [ ] Object Storage bucket resource added
- [ ] No changes to existing IAM policies needed (already sufficient)
- [ ] Module outputs expose `vault_id`, `key_id`, `bucket_name` for Stream C consumption
