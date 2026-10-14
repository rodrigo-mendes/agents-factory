# Evaluation Scenarios — designing-oci-vault-security

## Scenario 1: Canonical — Virtual Private Vault vs Default Vault

```json
{
  "skills": ["designing-oci-vault-security"],
  "query": "We are building a payment processing service on OCI Functions that must comply with PCI-DSS. Should we use a Default Vault or Virtual Private Vault for our encryption keys?",
  "expected_behavior": [
    "Recommends Virtual Private Vault for PCI-DSS: single-tenant HSM partition, FIPS 140-2 Level 3, dedicated crypto throughput (1000+ req/sec vs 200 for Default)",
    "Explains that Default Vault uses shared HSM partitions — acceptable for internal workloads but not sufficient for PCI-DSS dedicated HSM requirements",
    "Warns that Virtual Private Vault carries a significant fixed monthly cost — advises verifying current rate on oracle.com/cloud/pricing before commitment",
    "Notes that protection mode (HSM vs SOFTWARE) is IMMUTABLE after key creation — must choose HSM from the start for regulated workloads",
    "Asks whether FIPS 140-2 Level 3 is explicitly required by the compliance framework before recommending Virtual Private Vault",
    "Does NOT recommend SOFTWARE protection mode for payment card data regardless of cost constraints"
  ]
}
```

## Scenario 2: Canonical — HSM vs Software Key for Application Encryption

```json
{
  "skills": ["designing-oci-vault-security"],
  "query": "Our OCI Function needs to encrypt user PII before storing it in Object Storage. The data is not subject to PCI or HIPAA, just our internal security policy. Should we use an HSM key or software key?",
  "expected_behavior": [
    "Presents the trade-off: HSM keys are hardware-backed and non-exportable (higher security assurance) vs SOFTWARE keys are exportable and lower-cost",
    "For internal PII without regulatory mandate, acknowledges SOFTWARE keys are acceptable if the threat model does not require non-exportability",
    "Asks whether the internal policy requires non-exportable keys or FIPS compliance before making a final recommendation",
    "Confirms both HSM and SOFTWARE keys support AES-256 symmetric encryption and envelope encryption via GenerateDataEncryptionKey",
    "Reminds that the choice is IMMUTABLE after key creation — if requirements tighten later, a new key must be created and data re-encrypted",
    "Does NOT recommend Oracle-managed keys (SSE-Oracle) for PII — customer loses control over lifecycle and cannot perform crypto-shred"
  ]
}
```

## Scenario 3: Edge — BYOK with External KMS

```json
{
  "skills": ["designing-oci-vault-security"],
  "query": "Our security policy requires that encryption keys never leave our on-premises Thales HSM appliance. We want to encrypt OCI Object Storage buckets and Autonomous DB. Is this possible?",
  "expected_behavior": [
    "Confirms OCI External KMS (EKMS) supports this pattern: OCI holds only the key reference (OCID), crypto operations are delegated to the external HSM",
    "Explains the EKMS architecture: OCI API calls are forwarded to the external HSM endpoint configured in the ExternalKeyManager resource",
    "Notes that EKMS adds latency to every crypto operation (network round-trip to on-premises HSM) — asks about acceptable latency SLA",
    "Warns that if the on-premises HSM is unreachable, OCI services requiring that key will fail — recommends HA/DR planning for the HSM appliance",
    "Asks which external HSM vendor is in use (Thales, Entrust, etc.) to confirm EKMS connector compatibility",
    "Does NOT recommend mirroring the key material into OCI as a workaround — that defeats the BYOK isolation requirement"
  ]
}
```

## Scenario 4: Edge — Envelope Encryption for Large Payloads

```json
{
  "skills": ["designing-oci-vault-security"],
  "query": "Our OCI Function receives JSON payloads up to 10 MB that must be encrypted with our Vault master key before writing to Object Storage. A developer proposes calling the Vault Encrypt API directly with the payload.",
  "expected_behavior": [
    "Rejects direct Encrypt API call for payloads > 4 KB — the Vault Encrypt API has a 4 KB plaintext size limit",
    "Prescribes envelope encryption: call GenerateDataEncryptionKey to get a plaintext DEK + encrypted (wrapped) DEK, encrypt the payload locally with the plaintext DEK using AES-256-GCM, store encrypted DEK alongside ciphertext, then immediately discard the plaintext DEK from memory",
    "Confirms the correct endpoint is the crypto_endpoint (not management_endpoint) for GenerateDataEncryptionKey and Decrypt operations",
    "Notes the decryption path: retrieve encrypted DEK + ciphertext from Object Storage, call Vault Decrypt with encrypted DEK to get plaintext DEK, decrypt payload locally, discard plaintext DEK",
    "Warns: do NOT persist the plaintext DEK to any storage — a persisted DEK negates the protection of the master key"
  ]
}
```

## Scenario 5: Misuse — Granting manage keys to Application Dynamic Group

```json
{
  "skills": ["designing-oci-vault-security"],
  "query": "To simplify IAM, a developer wants to grant the OCI Functions dynamic group 'manage keys' in the Vault compartment so the function can create and rotate its own keys.",
  "expected_behavior": [
    "Rejects manage keys for application dynamic groups — this grants full CRUD including create, disable, schedule-deletion, and restore of keys; an application should never self-manage its own encryption keys",
    "Explains the correct least-privilege grants: dynamic group needs 'use keys' for encrypt/decrypt/sign/verify/GenerateDEK operations only",
    "Separates key admin duties: key creation and rotation scheduling belong to an admin group operated by security personnel, not automated workloads",
    "Notes that a compromised function with 'manage keys' could disable or schedule deletion of its own master key, causing a complete service outage and potential data loss",
    "Flags this as the Never Do pattern: Granting manage keys to application workloads",
    "Offers the correct IAM statement: 'Allow dynamic-group <fn-dg> to use keys in compartment <compartment> where target.key.id = <specific-key-ocid>'"
  ]
}
```
