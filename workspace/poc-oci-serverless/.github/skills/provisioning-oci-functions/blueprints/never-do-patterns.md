### 🚫 Never Do

**Anti-Pattern**: Credentials in Function Config

```hcl
# 🚫 WRONG: config is visible in OCI Console, API responses, Terraform state, and logs
# Exposing secrets here is an immediate data leak (OCI Provider v6.x+)
resource "oci_functions_function" "bad" {
  # ...
  config = {
    "DB_PASSWORD"   = "super-secret-123"        # NEVER — visible in state file
    "API_KEY"       = "sk-live-abc123def456"     # NEVER — visible in Console
    "PRIVATE_KEY"   = "-----BEGIN RSA..."        # NEVER — visible in API responses
  }
}

# ✅ CORRECT: Pass Vault OCID references, read secrets at runtime via Resource Principal
resource "oci_functions_function" "good" {
  # ...
  config = {
    "VAULT_SECRET_OCID" = var.db_password_secret_ocid  # Reference only
    "ENVIRONMENT"       = var.environment               # Non-sensitive only
  }
}
# Function code uses Resource Principal → OCI SDK → Vault → GetSecretBundle(secret_ocid)
```
**Why it is prohibited**: `config` is stored in plaintext in Terraform state, visible in OCI Console and API responses. Any secret in config is a credential exposure.
**Actual impact**: CRITICAL — Compromised credentials, unauthorized access to downstream services, compliance violations.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingpolicies.htm

---

**Anti-Pattern**: Application in Public Subnet

```hcl
# 🚫 WRONG: Public subnet allows direct internet access to functions (OCI Provider v6.x+)
# Bypasses API Gateway authentication, rate limiting, and WAF
resource "oci_functions_application" "bad" {
  compartment_id = var.compartment_ocid
  display_name   = "app-exposed"
  subnet_ids     = [var.subnet_public_id]  # PUBLIC — NEVER for Functions
  shape          = "GENERIC_ARM"
}

# ✅ CORRECT: Private subnet + NSGs for microsegmentation
resource "oci_functions_application" "good" {
  compartment_id             = var.compartment_ocid
  display_name               = "app-secure"
  subnet_ids                 = [var.subnet_private_id]  # PRIVATE subnet only
  shape                      = "GENERIC_ARM"
  network_security_group_ids = [var.nsg_functions_id]   # Restrictive NSG
}
```
**Why it is prohibited**: Functions in public subnet receive direct internet traffic, bypassing all API Gateway protections (authentication, rate limiting, WAF).
**Actual impact**: HIGH — Unauthorized invocation, DDoS exposure, authentication bypass.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm

---

**Anti-Pattern**: Updating `image` without `image_digest`

```hcl
# 🚫 WRONG: image updated but image_digest left stale (OCI Provider v6.x+)
# Provider may use cached digest — function continues running old image
resource "oci_functions_function" "bad" {
  # ...
  image = "gru.ocir.io/namespace/repo:v2"  # Updated to v2
  # image_digest not updated — inconsistency!
}

# ✅ CORRECT: Both image and image_digest updated atomically
resource "oci_functions_function" "good" {
  # ...
  image        = "gru.ocir.io/namespace/repo:v2"
  image_digest = "sha256:abc123..."  # BOTH updated together
}
```
**Why it is prohibited**: If only `image` is updated (new tag), the provider may use the cached digest. The function continues running the old image until next invoke, causing non-deterministic behavior.
**Actual impact**: MEDIUM — Deploy inconsistency, function executes wrong image version.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_function

---

**Anti-Pattern**: Over-provisioned Memory Without Profiling

```hcl
# 🚫 WRONG: 2048MB "just in case" — 16x cost multiplier (OCI Provider v6.x+)
resource "oci_functions_function" "bad" {
  # ...
  memory_in_mbs = 2048  # No profiling justification — pure waste
}

# ✅ CORRECT: Start with 256MB baseline, scale based on OOM errors in logs
resource "oci_functions_function" "good" {
  # ...
  memory_in_mbs = 256  # Profile in dev/staging, scale only if needed
}
# Memory → CPU: 128MB=1/8, 256MB=1/4, 512MB=1/2, 1024MB=1, 2048MB=1 vCPU
```
**Why it is prohibited**: `memory_in_mbs` directly determines cost — 2048MB costs 16x more per execution than 128MB. Most APIs operate fine with 256–512MB.
**Actual impact**: MEDIUM — Cost overrun (up to 16x unnecessary multiplier).
**Source**: https://www.oracle.com/cloud/price-list/#functions

---

**Anti-Pattern**: Application Destroy Without Timeout Configuration

```hcl
# 🚫 WRONG: No timeout configured — pipeline fails on known 5-min delay
resource "oci_functions_application" "bad" {
  # ... no timeouts block
}

# ✅ CORRECT: Account for OCI known issue — Application delete takes ~5 minutes
resource "oci_functions_application" "good" {
  # ...

  timeouts {
    delete = "10m"  # Known OCI issue: Application delete delay ~5 minutes
  }
}
```
**Why it is prohibited**: OCI has a known issue where Application destroy takes ~5 minutes even after all functions are deleted. CI/CD pipelines without adequate timeout fail with timeout errors.
**Actual impact**: LOW — Pipeline failure, but no data loss.
**Source**: https://docs.cloud.oracle.com/iaas/Content/Functions/Tasks/functionsdeleting.htm

---

