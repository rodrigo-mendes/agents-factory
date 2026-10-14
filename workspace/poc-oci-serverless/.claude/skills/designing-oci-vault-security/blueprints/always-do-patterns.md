### ✅ Always Do

**1. Customer-Managed Encryption Keys (CMEK) for All Data at Rest**: Customer control over encryption keys for data sovereignty, compliance audit trails, and the ability to crypto-shred data by destroying keys.

**Requirements**:
- Create encryption keys in OCI Vault with customer control
- Reference CMK (`kms_key_id`) when creating storage resources (Object Storage, Block Volumes, Autonomous DB)
- Use AES-256 (`algorithm = "AES"`, `length = 32`) as default for data encryption
- Enable auto-rotation with appropriate interval (60–365 days)
- Use HSM protection mode for production

**Why it is mandatory**: Oracle-managed keys provide encryption but no customer control over key lifecycle, rotation, or crypto-shred capability. Compliance frameworks (PCI-DSS, HIPAA, GDPR Article 32) require customer-controlled encryption.
**Failure if omitted**: Inability to crypto-shred data, compliance violations, no control over key rotation schedule.
**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

> 📎 **Implementation**: For Terraform provisioning of Vaults, Keys, and Secrets, use the skill `provisioning-oci-vault`.

---

**2. Secrets Retrieved via Resource Principals — Never Hardcoded**: Functions must access secrets from OCI Vault at runtime using Resource Principal authentication. NEVER store credentials in code, environment variables, function config, or container images.

**Required IAM setup**:
- Dynamic Group for Functions: `ALL {resource.type = 'fnfunc', resource.compartment.id = '<compartment_ocid>'}`
- Policy: `Allow dynamic-group <fn-dg> to read secret-bundles in compartment <name>`
- Function code uses `ResourcePrincipalAuthenticationDetailsProvider` (Java) or equivalent signer

**What goes WHERE**:
- **OCI Vault Secrets**: Passwords, API keys, tokens, certificates, connection strings — anything whose exposure causes a security incident
- **Function Config Variables**: Non-sensitive configuration only — OCIDs, bucket names, environment names, feature flags, service URLs

**Why it is mandatory**: Hardcoded credentials create static attack surfaces, prevent rotation, and violate least-privilege. Resource Principals enable credential-free service-to-service authentication.
**Failure if omitted**: Credential exposure in source control, CI/CD logs, Terraform state, and OCI Console.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm

> 📎 **Implementation**: For Java secret retrieval and caching patterns, use skills `developing-oci-functions-java` and `invoking-rest-apis-from-oci-functions`. For Terraform IAM provisioning, use `provisioning-oci-iam`.

---

**3. Automated Secret Rotation with Defined Intervals**: Eliminate long-lived static credentials with scheduled rotation. OCI Best Practices 2024 recommends maximum 90-day credential lifetime for production.

**Requirements**:
- Configure `rotation_config` on all production secrets
- Use rotation interval appropriate to sensitivity (recommended: 30 days for DB passwords, 90 days for API keys)
- Set `secret_rules` with `SECRET_EXPIRY_RULE` to enforce expiration (e.g., 5 days after rotation)
- Use OCI Functions as rotation target for custom rotation logic

**Why it is mandatory**: Long-lived static credentials increase blast radius of compromise. Industry standards (NIST 800-63B, PCI-DSS) mandate credential rotation.
**Failure if omitted**: Extended credential exposure window, compliance violations, inability to prove credential freshness in audit.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm

---

**4. Least-Privilege IAM for Vault Access**: Separate IAM permissions by operation type. Workload dynamic groups get minimum necessary — NEVER `manage`.

**IAM permission model**:
| Who | Verb | Resource Type | Purpose |
|-----|------|--------------|---------|
| Admin groups (humans) | `manage` | `vaults`, `keys`, `secrets` | Full lifecycle management |
| Workload dynamic groups | `use` | `keys` | Encrypt/Decrypt/Sign/Verify/GenerateDEK |
| Workload dynamic groups | `read` | `secret-bundles` | Retrieve secret values |
| Audit/monitoring | `read` | `vaults`, `keys`, `secrets` | List/Get metadata |
| Minimal visibility | `inspect` | `vaults`, `keys`, `secrets` | List OCIDs only |

**🚫 NEVER**: `Allow dynamic-group <workload> to manage keys in tenancy` — a compromised function could delete ALL keys, permanently destroying ALL encrypted data.

**Why it is mandatory**: Compromised function with `manage keys` could delete keys (destroying all encrypted data permanently), create unauthorized keys, or exfiltrate all secrets.
**Failure if omitted**: Data destruction via key deletion, unauthorized decryption, secret exfiltration.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm

---

**5. Purpose-Specific Keys with Separation**: Use separate keys per purpose/service with different rotation intervals. Never use a single key for all encryption.

**Recommended key separation**:
- **Storage encryption key** (AES-256, HSM, 90-day rotation) — for Object Storage, Block Volumes
- **Secrets encryption key** (AES-256, HSM, 60-day rotation) — for encrypting Vault secrets
- **Signing key** (ECDSA P-256, HSM, 180-day rotation) — for JWT/API token signing

**Why it is mandatory**: Single key for everything increases blast radius — key compromise affects ALL services. Prevents granular rotation schedules per sensitivity level. Makes audit attribution impossible.
**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingkeys.htm

---

**6. Secret Caching in Functions (Sidecar Pattern)**: Minimize secret retrieval overhead while maintaining freshness. Cache secrets in function memory with TTL-based invalidation.

**How it works**:
- On cold start: retrieve secret from Vault (~50-100ms)
- On warm invocations: use cached value (0ms)
- TTL-based invalidation: re-fetch after configurable interval (e.g., 5 minutes)
- Use `static` or class-level fields in function code — survives within container lifecycle

**Why it is mandatory**: Fetching secrets on every invocation adds ~50-100ms latency and generates excessive Vault API calls.
**Failure if omitted**: Unnecessary latency, excessive Vault API calls, higher costs.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsconcepts.htm

> 📎 **Implementation**: For Java caching pattern code, use `developing-oci-functions-java`.

---

