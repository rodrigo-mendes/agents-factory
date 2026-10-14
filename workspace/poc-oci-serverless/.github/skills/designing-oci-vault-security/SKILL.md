---
name: designing-oci-vault-security
description: Designs and manages OCI Vault security architecture (Keys, Secrets, Rotation, Encryption) for serverless architectures. Use when making Vault security decisions following OCI Best Practices 2024.
---

## Version Context

**Technology**: Oracle Cloud Infrastructure (OCI) Vault — Key Management & Secrets Management
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Architecture Domain**: Security Architecture — Key & Secrets Management
**Target Edition**: OCI Best Practices 2024
**FIPS Certification**: 140-2 Level 3 (HSM-backed keys)
**Support Status**: Active — General Availability

**Key Capabilities in This Edition**:
- OCI Dedicated KMS — single-tenant HSM partitions for high-compliance workloads
- OCI External KMS (EKMS) — bring-your-own-key management via third-party HSMs
- Cross-region secret replication — up to 3 target regions for DR
- Automatic secret rotation — scheduled rotation with OCI Functions for custom logic
- Auto key rotation — configurable intervals (60–365 days)
- Secret auto-generation — configurable templates for passwords and random bytes

⚠️ **CRITICAL — Agent Warning**:
This skill covers **security architecture and design decisions** for OCI Vault. For Terraform implementation, use the skill `provisioning-oci-vault`. For Java integration with Vault (secret retrieval, caching, envelope encryption), use skills `developing-oci-functions-java` and `invoking-rest-apis-from-oci-functions`.

**IMMUTABLE decisions** — cannot be changed after creation:
- Key **protection mode** (HSM vs SOFTWARE vs EXTERNAL) is permanent
- Key **deletion** is irreversible — all data encrypted with that key becomes unrecoverable
- Never grant `manage keys` or `manage vaults` to workload dynamic groups

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](#integration-patterns)** — Cross-service integration examples
- **[Security Architecture](#security-architecture)** — Defense in depth and WAF
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Customer-Managed Encryption Keys (CMEK)** — For all data at rest. Customer control over lifecycle, rotation, crypto-shred
- **Secrets via Resource Principals** — Never hardcoded. Retrieve from Vault at runtime
- **Automatic Key Rotation** — Schedule ≤90 days for compliance (PCI-DSS, HIPAA)
- **IAM Least-Privilege for Vault** — Separate policies for key users vs key admins

---

### ⚠️ Ask First

For complete decision matrices with examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Vault Type Selection** — Virtual (default, shared HSM) vs Private (dedicated HSM, FIPS 140-2 Level 3)
- **Key Protection Mode (IMMUTABLE)** — HSM (hardware-backed) vs SOFTWARE (exportable, lower cost)
- **Secret Storage Strategy** — Vault secrets vs function config for different sensitivity levels
- **Key Algorithm** — AES-256 (symmetric), RSA-2048/4096 (asymmetric), ECDSA (signing)

---

### 🚫 Never Do

For complete anti-patterns with examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Hardcoded Credentials** — Extractable via source control, CI/CD logs, Console. Data breach risk
- **Default (Oracle-Managed) Keys for Regulated Data** — No customer control over lifecycle or crypto-shred
- **Disabling Key Rotation** — Compliance violation, increased blast radius from key compromise
- **Granting `manage keys` to application workloads** — Applications need `use keys` only. Admin separation required

## Integration Patterns

### OCI Vault ↔ OCI Functions

**Network path**: Function in private subnet → Service Gateway → Oracle Services Network → OCI Vault HSM

**Key requirements**:
- Service Gateway must exist with "All Services In Oracle Services Network"
- Route table must route Service CIDR to Service Gateway
- Dynamic Group policy must grant `read secret-bundles` and/or `use keys`
- Function uses Resource Principal for authentication — no credentials needed

> 📎 **Implementation**: For Terraform provisioning of Service Gateway and routes, use `provisioning-oci-networking`. For Java SDK integration, use `developing-oci-functions-java`.

---

### OCI Vault ↔ Envelope Encryption (Application-Level)

**Use case**: Encrypting data > 4KB in application code using vault-managed keys.

**How it works**:
1. Call Vault `GenerateDataEncryptionKey` API with master key OCID
2. Receive plaintext DEK + encrypted (wrapped) DEK
3. Use plaintext DEK for local AES encryption of data
4. Store encrypted DEK alongside ciphertext
5. **Discard plaintext DEK from memory immediately** — do NOT persist
6. To decrypt: send encrypted DEK to Vault `Decrypt` API → get plaintext DEK → decrypt data locally

**⚠️ Common Pitfall**: Do NOT encrypt large payloads directly with the Master Encryption Key via the Encrypt API — it has a 4KB size limit. Always use envelope encryption (GenerateDataEncryptionKey) for data > 4KB.

**Important**: Use `crypto_endpoint` (NOT `management_endpoint`) for crypto operations.

> 📎 **Implementation**: For Java envelope encryption code, use `invoking-rest-apis-from-oci-functions`.

**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

### OCI Vault ↔ Cross-Region DR

**Use case**: Business-critical workloads requiring < 5-minute RTO for secret access in DR region.

**Architecture decisions**:
- Requires Virtual Private Vault in BOTH regions (~$530/month each)
- Maximum 3 replication targets per secret
- **Keys CANNOT be replicated** — must create equivalent keys in each region
- Replication is eventually consistent — brief lag during failover
- Write-forward can be enabled for bidirectional updates (set `is_write_forward_enabled = true`)

> 📎 **Implementation**: For Terraform provisioning of cross-region replication, use `provisioning-oci-vault`.

**Source**: https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm

---

### OCI Vault ↔ Monitoring & Alerting

**Critical events to monitor** (configure Events Rules → Notifications):

| Event Type | Severity | Action |
|-----------|----------|--------|
| `com.oraclecloud.kms.schedulekeydeletion` | CRITICAL | Alert security team immediately |
| `com.oraclecloud.kms.schedulevaultdeletion` | CRITICAL | Alert security team immediately |
| `com.oraclecloud.kms.disablekey` | HIGH | Investigate — may impact dependent services |
| `com.oraclecloud.vault.rotatesecret.end` (status FAILED) | HIGH | Investigate rotation failure |

> 📎 **Implementation**: For Terraform Events Rules, use `provisioning-oci-events`.

**Source**: https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm

---

## Verification Loop

The agent MUST execute after each Vault configuration change:

### 1. Vault Type and Key Protection
```bash
# Verify vault type is VIRTUAL_PRIVATE for production
oci kms vault get --vault-id <vault-ocid> | jq '.data["vault-type"]'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: "VIRTUAL_PRIVATE"

# Verify key protection mode is HSM for production
oci kms key get --key-id <key-ocid> --endpoint <mgmt-endpoint> | jq '.data["protection-mode"]'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: "HSM"
```

### 2. Auto-Rotation
```bash
# Verify auto-rotation is enabled on keys
oci kms key get --key-id <key-ocid> --endpoint <mgmt-endpoint> | jq '.data["is-auto-rotation-enabled"]'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: true

# Verify secret rotation config exists
oci vault secret get --secret-id <secret-ocid> | jq '.data["rotation-config"]'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: non-null with rotation_interval
```

### 3. IAM Policy Audit
```bash
# Detect overly permissive policies for dynamic groups
oci iam policy list --compartment-id <tenancy-ocid> --all | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[].statements[]' | grep -i "manage.*keys\|manage.*vault\|manage.*all-resources"
  # Exit code: 0 (match found) | 1 (no match)
# Expected: Only for admin groups, NEVER for dynamic groups
```

### 4. CMK Coverage Scan
```bash
# Find storage without CMK
oci os bucket list --compartment-id <comp-ocid> | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[] | select(.["kms-key-id"] == null) | .name'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
# Expected: empty

oci bv volume list --compartment-id <comp-ocid> | \
  jq '.data[] | select(.["kms-key-id"] == null) | .["display-name"]'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
# Expected: empty
```

### 5. Secret Rotation Coverage
```bash
oci vault secret list --compartment-id <comp-ocid> | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[] | select(.["rotation-config"] == null) | .["secret-name"]'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
# Expected: empty for production secrets
```

### 6. Network Path
```bash
# Verify Service Gateway exists for Vault access
oci network service-gateway list --compartment-id <comp-ocid> --vcn-id <vcn-ocid> | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[].services[].["service-name"]'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
# Expected: "All <region> Services In Oracle Services Network"
```

**Troubleshooting**:
- `404 NotAuthorizedOrNotFound` → Check Dynamic Group matching rule and IAM policy compartment scope
- `429 TooManyRequests` → Vault API rate limits: management 10 req/sec, crypto 200 req/sec (Default) or 1000+ (Virtual Private)
- `ServiceError: KeyNotFound` → Verify key OCID and management_endpoint match the correct vault

---

## Quick Reference

### Service Limits

| Limit | Default | Notes |
|-------|---------|-------|
| Vaults per compartment | 10 (Default) + 10 (Virtual Private) | Can request increase |
| Keys per vault | 10 (Default), 1000 (Virtual Private) | Default vault is very limited |
| Key versions per key | 50 | Plan rotation frequency accordingly |
| Secrets per compartment | 150 | Can request increase |
| Secret size | 25 KB | Base64-encoded content limit |
| Replication targets per secret | 3 | Maximum 3 DR regions |
| Auto-rotation interval (keys) | 60–365 days | Cannot be < 60 days |
| Secret rotation interval | 1–360 days | ISO 8601 duration (e.g., "P30D") |
| Key deletion pending period | 7–30 days | Mandatory grace period |
| Crypto API rate (Default Vault) | 200 req/sec | Per vault |
| Crypto API rate (Virtual Private) | 1000+ req/sec | Per vault |
| Management API rate | 10 req/sec | Per tenancy |

### IAM Verbs Reference

| Verb | Resource Type | Grants | Who |
|------|--------------|--------|-----|
| `manage` | `vaults`, `keys`, `secrets` | Full CRUD | Admin groups only |
| `use` | `keys` | Encrypt/Decrypt/Sign/Verify/GenerateDEK | Workload dynamic groups |
| `read` | `secret-bundles` | Retrieve secret values | Workload dynamic groups |
| `read` | `vaults`, `keys`, `secrets` | List/Get metadata | Audit/monitoring |
| `inspect` | `vaults`, `keys`, `secrets` | List OCIDs only | Minimal visibility |

### Cost Reference

| Component | Cost |
|-----------|------|
| Default Vault | $0 (up to 20 key versions) |
| Virtual Private Vault | ~$530/month per vault |
| HSM Key Operations | ~$0.03–$0.05 per 10,000 ops |
| Software Key Operations | Lower than HSM |
| Secrets | $0 (charges via key operations) |

---

## Skill Cross-References

| Need | Use Skill |
|------|-----------|
| Terraform: Vault, Keys, Secrets, Rotation, Replication | `provisioning-oci-vault` |
| Terraform: IAM Dynamic Groups and Policies for Vault access | `provisioning-oci-iam` |
| Terraform: Service Gateway for private Vault access | `provisioning-oci-networking` |
| Terraform: Events Rules for Vault monitoring | `provisioning-oci-events` |
| Java: Secret retrieval with Resource Principal | `developing-oci-functions-java` |
| Java: Vault API calls, envelope encryption | `invoking-rest-apis-from-oci-functions` |
| Serverless architecture (Functions + API GW + Vault) | `architecting-oci-serverless` |

---

## Architecture Review Checklist

```
Architecture Validation:
- [ ] Verify network topology (VCN, subnets, NSGs)
- [ ] Verify IAM policies (dynamic groups, least-privilege)
- [ ] Verify security controls (encryption, auth, CORS)
- [ ] Verify observability (logging, monitoring, alerts)
- [ ] Verify cost controls (rate limiting, scaling limits)
```

## External Resources

### Official Documentation
- [OCI Vault — Key Management Overview](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/home.htm)
- [OCI Key Concepts](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm)
- [OCI Secrets Management](https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm)
- [OCI Key Management Tasks](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingkeys.htm)
- [OCI External Key Management](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/external_key_management.htm)

### Security & IAM
- [IAM Policy Basics](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm)
- [Functions — Accessing OCI Resources](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm)
- [Security Configuration Reference](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/configuration_security.htm)
- [OCI Security Guide](https://docs.oracle.com/en-us/iaas/Content/Security/Concepts/security_guide.htm)

### Infrastructure
- [Service Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm)
- [Audit Overview](https://docs.oracle.com/en-us/iaas/Content/Audit/Concepts/auditoverview.htm)
- [Monitoring Overview](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm)

### Pricing
- [Key Management Pricing](https://www.oracle.com/security/cloud-security/key-management/)
