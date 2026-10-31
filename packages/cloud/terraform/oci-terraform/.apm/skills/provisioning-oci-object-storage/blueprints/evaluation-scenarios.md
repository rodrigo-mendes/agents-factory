# Evaluation Scenarios — provisioning-oci-object-storage

## Scenario 1: Canonical — Private bucket with CMEK, lifecycle policy, and event pipeline

```json
{
  "skills": ["provisioning-oci-object-storage"],
  "query": "Create an OCI Object Storage bucket for a regulated document processing pipeline. It should be private, encrypted with a customer-managed key, emit events on object upload, and have a lifecycle policy that aborts incomplete multipart uploads after 7 days.",
  "expected_behavior": [
    "Creates oci_objectstorage_bucket with access_type = 'NoPublicAccess' explicitly set",
    "Sets kms_key_id to an OCI Vault master key OCID via variable",
    "Sets object_events_enabled = true to enable OCI Events integration",
    "Creates oci_objectstorage_object_lifecycle_policy with an ABORT rule targeting 'multipart-uploads' with time_amount = 7 and time_unit = 'DAYS'",
    "Adds depends_on = [oci_objectstorage_bucket.main] on the lifecycle policy resource",
    "Uses data.oci_objectstorage_namespace.ns.namespace — does NOT hardcode namespace string",
    "Applies defined tags including data-classification, environment, cost-center",
    "Uses ignore_changes = [defined_tags['Oracle-Tags.CreatedBy']] to prevent drift"
  ]
}
```

## Scenario 2: Edge — Versioned bucket without lifecycle rule on previous-object-versions

```json
{
  "skills": ["provisioning-oci-object-storage"],
  "query": "Enable versioning on my existing bucket to protect against accidental deletes. I'll set versioning = 'Enabled' in Terraform.",
  "expected_behavior": [
    "Enables versioning as requested",
    "Proactively adds a lifecycle rule targeting 'previous-object-versions' with a DELETE action",
    "Explains that without this rule, version history accumulates silently with unbounded storage cost",
    "Recommends a retention window of 30–90 days for previous versions based on recovery SLA",
    "Does NOT enable versioning without the companion previous-object-versions lifecycle rule",
    "Reminds that oci_objectstorage_object_lifecycle_policy uses CreateOrReplace semantics — all existing rules must be included in the same resource block"
  ]
}
```

## Scenario 3: Edge — Immutable storage tier choice

```json
{
  "skills": ["provisioning-oci-object-storage"],
  "query": "Should I use Archive tier or Standard tier with a lifecycle transition for long-term log retention (18-month compliance requirement)?",
  "expected_behavior": [
    "Asks about access pattern: will logs ever need to be read during the 18-month window, or only at end of retention for audit?",
    "If read-never-needed: recommends Archive tier directly (lowest cost, 90-day minimum duration honored for compliance)",
    "If occasional-reads-needed: recommends Standard tier with a lifecycle rule transitioning objects to Archive after 90 days",
    "Warns that storage_tier is immutable after bucket creation — wrong choice requires destroy/recreate of the bucket",
    "Confirms Archive restore SLA is 1 hour (not instant) — relevant for incident response scenarios",
    "Does NOT skip the immutability warning for storage tier decisions"
  ]
}
```

## Scenario 4: Edge — Function in private subnet cannot access Object Storage

```json
{
  "skills": ["provisioning-oci-object-storage"],
  "query": "My OCI Function in a private subnet fails to access Object Storage. The error is: 'connection timed out' when calling ObjectStorageClient.putObject.",
  "expected_behavior": [
    "Identifies missing Service Gateway as the root cause",
    "Confirms that Object Storage traffic must route through Service Gateway — not NAT Gateway (which bills per-GB egress and exposes data to internet routing)",
    "Checks that the private subnet route table has a rule for the OCI 'All <region> Services In Oracle Services Network' service CIDR pointing to the Service Gateway",
    "Verifies NSG allows egress TCP 443 to the OCI service CIDR",
    "Does NOT suggest switching to NAT Gateway or adding a public IP to the Function subnet"
  ]
}
```

## Scenario 5: Misuse — PAR with AnyObjectReadWrite and far-future expiry

```json
{
  "skills": ["provisioning-oci-object-storage"],
  "query": "I need to share bucket access with an external partner. Can I create a Pre-Authenticated Request with AnyObjectReadWrite and expiry set to 5 years from now?",
  "expected_behavior": [
    "Flags PAR with AnyObjectReadWrite + far-future expiry as a critical 'Never Do' anti-pattern",
    "Explains that AnyObjectReadWrite grants unrestricted bucket write access — partner can overwrite or flood the bucket",
    "Points out there is no revocation path except explicit PAR deletion by OCID, which may not be audited",
    "Recommends scoping to the minimum needed: specific object-level PAR with ObjectRead only, short expiry (days, not years)",
    "Proposes alternatives for long-term partner access: OCI IAM federated identity or temporary STS-equivalent via resource principal",
    "Does NOT generate a PAR resource with AnyObjectReadWrite and expiry > 30 days without explicit justification and a documented revocation plan"
  ]
}
```
