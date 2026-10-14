# Evaluation Scenarios — provisioning-oci-vault

## Scenario 1 (Canonical): Virtual Private Vault with HSM Keys and Secret Rotation

```json
{
  "skills": ["provisioning-oci-vault"],
  "query": "Provision a production Vault for our Java Functions. We need a Virtual Private Vault, HSM-protected AES-256 keys (separate keys for secrets and storage), a database password secret with 30-day rotation and 35-day expiry, and least-privilege IAM for our functions dynamic group.",
  "expected_behavior": [
    "Generates oci_kms_vault with vault_type = 'VIRTUAL_PRIVATE'",
    "Generates two separate oci_kms_key resources (secrets key + storage key) with protection_mode = 'HSM' and is_auto_rotation_enabled = true",
    "Key shape: algorithm AES, length 32 (256-bit)",
    "Generates oci_vault_secret with expiry_rule (time_of_absolute_expiry or time_of_current_version_expiry) and rotation_policy (rotation_interval_in_days = 30)",
    "All secrets include lifecycle { ignore_changes = [secret_content] }",
    "IAM policy grants 'use keys' and 'read secret-bundles' to functions dynamic group — NOT 'manage'",
    "lifecycle prevent_destroy = true on vault and keys",
    "Variable validation for vault_type and protection_mode",
    "Does NOT output secret values — outputs OCIDs only"
  ]
}
```

## Scenario 2 (Edge): Missing IAM Policy / Cold-Start Auth Failure

```json
{
  "skills": ["provisioning-oci-vault"],
  "query": "My OCI Function gets '404 NotAuthorizedOrNotFound' when calling getSecretBundleByName at cold start. The IAM policy exists. What should I check?",
  "expected_behavior": [
    "Lists ordered checklist: (1) Dynamic Group matching rule matches the function's OCID/compartment, (2) policy is scoped to the correct compartment (not just tenancy), (3) IAM propagation delay (~60s) — may need depends_on or retry",
    "Distinguishes 'read secret-bundles' (value retrieval) from 'read secrets' (metadata only)",
    "Notes that management_endpoint vs crypto_endpoint confusion causes 404 — secrets use vault endpoint, not crypto endpoint",
    "Advises verifying with OCI CLI: oci secrets secret get --secret-id ...",
    "Does NOT suggest granting 'manage secrets' to the dynamic group as a fix"
  ]
}
```

## Scenario 3 (Edge): BYOK Migration / Vault Type Immutability

```json
{
  "skills": ["provisioning-oci-vault"],
  "query": "We started with a DEFAULT vault for dev but now need a VIRTUAL_PRIVATE vault for production compliance. Can I upgrade the existing vault?",
  "expected_behavior": [
    "States clearly that vault_type is IMMUTABLE — cannot change DEFAULT to VIRTUAL_PRIVATE in-place",
    "Explains that changing vault_type in Terraform forces destroy/recreate — all keys and secrets in the vault are permanently deleted",
    "Proposes correct migration: provision new VP vault, re-create keys and secrets there, update application config to reference new OCIDs, then schedule deletion of old vault after grace period",
    "Notes key deletion has mandatory 7–30 day pending period — plan timeline accordingly",
    "Warns against terraform taint on the vault resource without explicit user confirmation (Emergency Stop trigger)",
    "Does NOT suggest using DEFAULT vault for a PCI-DSS production workload"
  ]
}
```

## Scenario 4 (Misuse): Secret Value Exposed in Terraform State

```json
{
  "skills": ["provisioning-oci-vault"],
  "query": "I added an oci_vault_secret resource and set the initial secret content in my variables.tf. My security team says this is a problem. Is it?",
  "expected_behavior": [
    "Confirms this is a security issue: Terraform state stores secret_content as base64 plaintext — state files in remote backends (OCI Object Storage) may be readable by anyone with bucket access",
    "Prescribes the fix: add lifecycle { ignore_changes = [secret_content] } to all oci_vault_secret resources",
    "Advises passing initial value via a sensitive variable or using a secrets bootstrapping function that sets the value post-provisioning",
    "Warns against using data.oci_secrets_secretbundle in Terraform — it pulls the actual secret VALUE into state",
    "Notes that 'sensitive = true' on outputs helps but does not prevent state storage",
    "Does NOT suggest removing the secret resource and managing it manually as the recommended fix"
  ]
}
```
