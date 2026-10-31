---
name: provisioning-oci-vault
description: Provisions and configures OCI Vault resources (Vaults, Keys, Secrets, Rotation, Replication) with Terraform OCI Provider v6.x+. Use when provisioning Vault infrastructure for serverless architectures.
---

## Version Context

**Technology**: Terraform OCI Provider — Vault (oci_kms_vault, oci_kms_key, oci_vault_secret)
**Cloud Provider**: OCI (Oracle Cloud Infrastructure)
**Target Service**: Vault — Key Management Service (KMS) & Secrets Management
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest/docs
**Support Status**: Active — continuous releases (current stable)

**Immutable Properties (cannot change after creation — plan carefully)**:
- `vault_type` — DEFAULT or VIRTUAL_PRIVATE (forces destroy/recreate)
- `protection_mode` — HSM, SOFTWARE, or EXTERNAL
- `key_shape` — algorithm + length (AES/RSA/ECDSA)

**Vault Types**:
- **DEFAULT** — multi-tenant HSM, 10 keys max, 200 ops/sec, $0, no cross-region replication
- **VIRTUAL_PRIVATE** — dedicated HSM partition, 1000 keys, 1000+ ops/sec, ~$530/month, cross-region replication

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider v6.x+ with Terraform >= 1.7.
Key deletion is **PERMANENT** — all data encrypted with that key becomes unrecoverable.
Never grant `manage keys` or `manage vaults` to workload dynamic groups.
Secret content appears in Terraform state — always use `lifecycle { ignore_changes = [secret_content] }`.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Module Architecture](#module-architecture)** — Terraform module composition
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Provider Version Constraint** — Pin `>= 6.0, < 9.0` to prevent force-replacement of immutable resources
- **Virtual Private Vault for Production** — DEFAULT is multi-tenant, 10 keys max, no DR. `vault_type` is IMMUTABLE
- **Purpose-Specific Keys with HSM + Auto-Rotation** — Separate keys per purpose (secrets, storage, signing). `protection_mode` and `key_shape` are IMMUTABLE
- **Secrets with Rotation, Expiry Rules, and State Protection** — Always use `lifecycle { ignore_changes = [secret_content] }`. Secret content is stored in state as base64 plaintext
- **Least-Privilege IAM** — Workloads get `use keys` + `read secret-bundles` only. `manage` is for human admin groups only
- **Variable Validation for Immutable Properties** — Validate `vault_type`, `protection_mode`, `algorithm` at plan-time
- **State Isolation** — Vault resources in separate Terraform state from application resources

---

### ⚠️ Ask First

5 architecture decisions with immutable properties — see [Ask First Decisions](./blueprints/ask-first-decisions.md):
1. **Vault Type Selection** (IMMUTABLE) — DEFAULT vs VIRTUAL_PRIVATE
2. **Key Protection Mode** (IMMUTABLE) — HSM vs SOFTWARE vs EXTERNAL
3. **Key Algorithm Selection** (IMMUTABLE) — AES-256 vs RSA-4096 vs ECDSA
4. **Secret Rotation Strategy** — ADB Native vs Function-based vs Manual vs Auto-generation
5. **Single vs. Multiple Vaults** — Per-environment isolation strategy

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Secret Content Without State Protection** — Never hardcode secrets or omit `lifecycle { ignore_changes = [secret_content] }`. State stores values as plaintext
- **`manage keys`/`manage vaults` for Workloads** — Workload dynamic groups must NEVER get `manage` permissions. Compromised function = permanent data loss
- **`data.oci_secrets_secretbundle` in Terraform** — Retrieves actual secret VALUE into state. Only output OCIDs, retrieve values at runtime via SDK
- **Default Vault for Production** — 10 keys max, shared HSM, no DR. `vault_type` is IMMUTABLE
- **Vault/Key Without `prevent_destroy`** — Deletion is PERMANENT and IRREVERSIBLE
- **Secrets Without Expiry Rules** — Long-lived static credentials violate NIST 800-63B and PCI-DSS

---

## Integration Patterns

For complete integration patterns with code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Available integrations**:
- **Terraform ↔ OCI Functions** — Secret OCID in Function config, runtime retrieval via SDK + Resource Principal
- **Terraform ↔ Object Storage (CMEK)** — Customer-managed key encryption with service-level IAM policy
- **Terraform ↔ OCI Events** — Alert on key deletion, vault deletion, rotation failures via ONS
- **Terraform ↔ Network** — Service Gateway for private Vault access (no internet exposure)
- **Terraform ↔ Cross-Region Replication (DR)** — Secrets replicated to DR region (requires VP vault + keys in both regions)

---

## Module Architecture

For the complete reusable Terraform module, see [Vault Module Blueprint](./blueprints/vault-module.tf).

**Standard Module Structure**:
```
modules/vault/
├── main.tf          # Vault, Keys, Secrets resources
├── variables.tf     # Input variables with validation
├── outputs.tf       # Vault endpoints, Key OCIDs, Secret OCIDs
├── versions.tf      # Provider constraints
├── iam.tf           # IAM policies for vault access
└── README.md
```

**Root Module Usage**:
```hcl
# ✅ CORRECT: Module composition — Terraform OCI Provider v6.x+
module "vault" {
  source = "./modules/vault"

  compartment_ocid           = var.compartment_ocid
  compartment_name           = var.compartment_name
  project_name               = var.project_name
  environment                = var.environment
  vault_type                 = "VIRTUAL_PRIVATE"
  key_protection_mode        = "HSM"
  key_rotation_interval_days = 90

  functions_dynamic_group_name = module.iam.dynamic_group_functions_name

  secrets = {
    "db-password" = {
      description          = "Database master password"
      initial_value        = var.initial_db_password
      sensitivity          = "high"
      expiry_interval      = "P35D"
      rotation_interval    = "P30D"
      rotation_function_id = module.functions.rotation_function_id
    }
  }

  tags       = local.tags
  depends_on = [module.iam]
}

# Object Storage using vault key for CMEK
resource "oci_objectstorage_bucket" "data" {
  compartment_id = var.compartment_ocid
  name           = "data-${var.project_name}-${var.environment}"
  namespace      = var.namespace
  kms_key_id     = module.vault.key_storage_id
}
```

---

## Verification Loop

The agent MUST execute after provisioning vault infrastructure:

### 1. Terraform Validate
```bash
terraform init -upgrade && terraform fmt -recursive -check=true && terraform validate
# Exit code: 0 (valid) | 1 (invalid configuration)
# Expected: "Success! The configuration is valid."
```
**Expected output**: Exit code 0, no formatting issues.

### 2. Plan & State Verification
```bash
terraform plan -out=tfplan -var-file="environments/prod.tfvars"
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
terraform show tfplan | grep -E "oci_kms_vault|oci_kms_key|oci_vault_secret"
# Exit code: 0 (match found) | 1 (no match)
# Expected: Resources listed with correct vault_type, protection_mode
```

### 3. Vault Type and Key Protection (Post-Apply)
```bash
oci kms vault get --vault-id $(terraform output -raw vault_id) | jq '{
# Exit code: 0 (success) | 1 (error)
  vault_type: .data["vault-type"],
  state: .data["lifecycle-state"]
}'
# Expected: vault_type = "VIRTUAL_PRIVATE", state = "ACTIVE"

KEY_ID=$(terraform output -raw key_secrets_id)
# Exit code: 0 (success) | 1 (error)
MGMT_ENDPOINT=$(terraform output -raw vault_management_endpoint)
# Exit code: 0 (success) | 1 (error)
oci kms key get --key-id "$KEY_ID" --endpoint "$MGMT_ENDPOINT" | jq '{
# Exit code: 0 (success) | 1 (auth/network error)
  protection_mode: .data["protection-mode"],
  algorithm: .data["key-shape"].algorithm,
  auto_rotation: .data["is-auto-rotation-enabled"]
}'
# Expected: protection_mode = "HSM", algorithm = "AES", auto_rotation = true
```

### 4. IAM Policy Audit
```bash
oci iam policy list --compartment-id <tenancy-ocid> --all | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[].statements[]' | grep -i "manage.*keys\|manage.*vault\|manage.*all-resources"
  # Exit code: 0 (match found) | 1 (no match)
# Expected: Only for admin groups, NEVER for dynamic groups
```

### 5. Security Scanning
```bash
tfsec . --format sarif
# Exit code: 0 (no issues) | 1 (issues found)
# Expected: No CRITICAL or HIGH findings

checkov -d . --framework terraform --quiet
# Exit code: 0 (passed) | 1 (failed checks)
# Expected: Passed checks > Failed checks
```

### 6. Destroy Protection Test
```bash
terraform plan -destroy 2>&1 | grep "prevent_destroy"
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
# Expected: Error — "has lifecycle.prevent_destroy set"
```

**Troubleshooting**:
- `404 NotAuthorizedOrNotFound` → Check Dynamic Group matching rule and IAM policy compartment scope
- `429 TooManyRequests` → Management API limit: 10 req/sec per tenancy; crypto: 200 (Default) or 1000+ (VP)
- `ServiceError: KeyNotFound` → Verify key OCID and management_endpoint match the correct vault
- IAM policy propagation delay → Wait 60s or use `depends_on` for downstream resources

---

## Quick Reference

**Service Limits**:
| Limit | Default | Notes |
|-------|---------|-------|
| Vaults per compartment | 10 (Default) + 10 (VP) | Can request increase |
| Keys per vault | 10 (Default), 1000 (VP) | Default very limited |
| Key versions per key | 50 | Plan rotation frequency |
| Secrets per compartment | 150 | Can request increase |
| Secret size | 25 KB | Base64-encoded content limit |
| Replication targets per secret | 3 | Maximum 3 DR regions |
| Auto-rotation interval (keys) | 60–365 days | Cannot be < 60 days |
| Secret rotation interval | 1–360 days | ISO 8601 (e.g., "P30D") |
| Key deletion pending period | 7–30 days | MANDATORY grace period |
| Crypto API rate (Default) | 200 req/sec | Per vault |
| Crypto API rate (VP) | 1000+ req/sec | Per vault |
| Management API rate | 10 req/sec | Per tenancy |

**IAM Policy Verbs**:
| Verb | Resource Type | Grants | Who |
|------|--------------|--------|-----|
| `manage` | `vaults`, `keys`, `secrets` | Full CRUD including delete | Admin groups only |
| `use` | `keys` | Encrypt/Decrypt/Sign/Verify/GenerateDEK | Workload dynamic groups |
| `read` | `secret-bundles` | Retrieve secret values | Workload dynamic groups |
| `read` | `vaults`, `keys`, `secrets` | List/Get metadata only | Audit/monitoring |

**Key Terraform Resources**:
| Resource | Purpose |
|----------|---------|
| `oci_kms_vault` | Create vault (DEFAULT or VIRTUAL_PRIVATE) |
| `oci_kms_key` | Create master encryption key (AES/RSA/ECDSA) |
| `oci_vault_secret` | Create secret with rotation/expiry |
| `oci_kms_vault_replication` | Cross-region vault replication |
| `oci_events_rule` | Alert on critical vault operations |

**Import Commands**:
```bash
terraform import oci_kms_vault.main "ocid1.vault.oc1..."
terraform import oci_kms_key.secrets "managementEndpoint/https://xxx-management.kms.region.oraclecloud.com/keys/ocid1.key.oc1..."
terraform import oci_vault_secret.db_password "ocid1.vaultsecret.oc1..."
```

**Cost Reference**:
| Component | Cost |
|-----------|------|
| Default Vault | $0 (up to 20 key versions) |
| Virtual Private Vault | ~$530/month per vault |
| HSM Key Operations | ~$0.03–$0.05 per 10K ops |
| Secrets | $0 (charges via key operations) |

**DR Emergency Runbook**:
```bash
# Key accidentally disabled
oci kms key update --key-id <key-ocid> --endpoint <mgmt-endpoint> --is-enabled true

# Key deletion scheduled — CANCEL within grace period
oci kms key cancel-deletion --key-id <key-ocid> --endpoint <mgmt-endpoint>

# Secret rotation failed — manual rotation
oci vault secret update-secret-content --secret-id <secret-ocid> \
  --content-type BASE64 --content $(echo -n "NewPassword" | base64)
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Virtual Private Vault for prod, Default for dev
- HSM protection mode + auto-rotation on all keys
- `prevent_destroy` on Vaults and Keys
- `lifecycle { ignore_changes = [secret_content] }` on all secrets
- IAM: `use keys` + `read secret-bundles` for workloads
- Variable validation for immutable properties
- Tags on all resources
- Module output definitions

### Medium Confidence (Validate with user)
- Vault type selection (compliance/cost dependent)
- Key algorithm selection (use-case dependent)
- Rotation interval values (60–365 for keys, 1–360 for secrets)
- Cross-region replication configuration
- Secret auto-generation templates

### Emergency Stop
- **HALT** if `terraform destroy` targets `oci_kms_vault` or `oci_kms_key` without explicit user confirmation
- **HALT** if secret values appear in Terraform outputs without `sensitive = true`
- **HALT** if `manage keys` or `manage vaults` is being granted to workload dynamic groups
- **HALT** if `data.oci_secrets_secretbundle` is used in code (values will be in state)
- **HALT** if `vault_type = "DEFAULT"` is used for production environment
- **HALT** if `prevent_destroy` is missing on production vault/key resources

---

## Deployment Workflow

```
Provisioning Progress:
- [ ] terraform init -upgrade
- [ ] terraform fmt -recursive -check (exit 0)
- [ ] terraform validate (exit 0)
- [ ] terraform plan -out=tfplan (review)
- [ ] terraform apply tfplan
- [ ] Verify resources via OCI CLI
- [ ] Validate immutable properties (vault_type, protection_mode, key_shape)
- [ ] Confirm prevent_destroy on vault and key resources
- [ ] Commit state and tag release
```

## External Resources

### Terraform Resources
- [oci_kms_vault](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/kms_vault) — Vault resource docs (verified 2026-07-26)
- [oci_kms_key](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/kms_key) — Key resource docs (verified 2026-07-26)
- [oci_vault_secret](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/vault_secret) — Secret resource docs (verified 2026-07-26)
- [oci_kms_vault_replication](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/kms_vault_replication) — Vault replication (verified 2026-07-26)
- [Terraform Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules) (verified 2026-07-26)
- [Terraform Lifecycle Meta-Arguments](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle) (verified 2026-07-26)
- [Terraform State Sensitive Data](https://developer.hashicorp.com/terraform/language/state/sensitive-data) (verified 2026-07-26)

### Official OCI Documentation
- [OCI Vault — Key Management Overview](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/home.htm) (verified 2026-07-26)
- [OCI Key Concepts](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm) (verified 2026-07-26)
- [OCI Secrets Management](https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm) (verified 2026-07-26)
- [OCI Key Management Tasks](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingkeys.htm) (verified 2026-07-26)

### Security & IAM
- [OCI IAM Policy Reference — KMS](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/keypolicyreference.htm) (verified 2026-07-26)
- [OCI Functions — Accessing Resources](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm) (verified 2026-07-26)
- [OCI Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Security/Concepts/security_guide.htm) (verified 2026-07-26)

### Network & Monitoring
- [OCI Service Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm) (verified 2026-07-26)
- [OCI Events Overview](https://docs.oracle.com/en-us/iaas/Content/Events/Concepts/eventsoverview.htm) (verified 2026-07-26)
- [OCI Object Storage Encryption](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/managingencryption.htm) (verified 2026-07-26)

### Pricing & Examples
- [OCI Key Management Pricing](https://www.oracle.com/security/cloud-security/key-management/) (verified 2026-07-26)
- [OCI Provider KMS Examples](https://github.com/oracle/terraform-provider-oci/tree/master/examples/kms) (verified 2026-07-26)
