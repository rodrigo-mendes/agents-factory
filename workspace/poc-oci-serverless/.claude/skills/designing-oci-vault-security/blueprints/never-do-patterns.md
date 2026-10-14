### 🚫 Never Do

**1. Hardcoded Credentials in Application Code or Config**: Credentials in code, env vars, or function config are extractable via source control, CI/CD logs, container images, and OCI Console.

**Correct approach**: Retrieve from OCI Vault at runtime using Resource Principal. Store only OCIDs as references in function config.

**Detection**:
```bash
# Scan Function config for suspicious variables
oci fn application get --application-id <app_ocid> | jq '.data.config' | grep -i "password\|secret\|key\|token"
# Expected: No matches for actual credential values (OCIDs are acceptable)
```

**Actual impact**: Data breach, credential compromise, lateral movement, compliance violation (PCI-DSS 3.4, SOC2 CC6.1).
**Source**: https://docs.oracle.com/en-us/iaas/Content/Security/Reference/configuration_security.htm

---

**2. Using Default (Oracle-Managed) Keys for Regulated Data**: Oracle-managed keys provide encryption but no customer control over lifecycle, rotation, or crypto-shred.

**Correct approach**: Specify Customer-Managed Key (CMK) from OCI Vault for all storage resources (`kms_key_id` on buckets, volumes, databases).

**Detection**:
```bash
# Find Object Storage buckets without CMK
oci os bucket list --compartment-id <comp-ocid> | jq '.data[] | select(.["kms-key-id"] == null) | .name'
# Find Block Volumes without CMK
oci bv volume list --compartment-id <comp-ocid> | jq '.data[] | select(.["kms-key-id"] == null) | .["display-name"]'
# Expected: empty (all should have CMK)
```

**Actual impact**: Compliance violation, inability to crypto-shred, reduced data sovereignty.
**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

**3. Wildcard IAM Policies for Key/Vault/Secret Access**: `manage all-resources in tenancy` or `manage keys in tenancy` for dynamic groups enables complete compromise of encryption infrastructure.

**Correct approach**: Scope to compartment, use minimal verbs (`use keys`, `read secret-bundles`), add resource-level conditions where possible.

**Detection**:
```bash
# Find overly permissive vault policies
oci iam policy list --compartment-id <tenancy-ocid> --all | \
  jq '.data[].statements[]' | grep -i "manage.*keys\|manage.*vault\|manage.*secret\|manage.*all-resources"
# Expected: Only for admin groups, NEVER for dynamic groups
```

**Actual impact**: Data destruction (key deletion = permanent data loss), unauthorized decryption, secret exfiltration.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm

---

**4. Single Encryption Key for All Purposes**: One key for everything increases blast radius — key compromise affects ALL services.

**Correct approach**: Separate keys per purpose (storage, secrets, signing) with different rotation intervals.

**Actual impact**: Over-broad blast radius, inability to rotate independently per service, audit confusion.
**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingkeys.htm

---

**5. No Secret Expiration or Rotation Configured**: Secrets without rotation become long-lived static credentials. Compromised credentials remain valid indefinitely.

**Correct approach**: Configure `rotation_config` with rotation interval and `SECRET_EXPIRY_RULE` for expiration.

**Detection**:
```bash
# Find secrets without rotation config
oci vault secret list --compartment-id <comp-ocid> | \
  jq '.data[] | select(.["rotation-config"] == null) | .["secret-name"]'
```

**Actual impact**: Extended credential exposure window, compliance violation (NIST 800-63B, PCI-DSS).
**Source**: https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm

---

