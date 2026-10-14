# Evaluation Scenarios — provisioning-oci-connector-hub

## Scenario 1: Canonical — Log archival pipeline (Logging → Object Storage)

```json
{
  "skills": ["provisioning-oci-connector-hub"],
  "query": "Provision an OCI Service Connector Hub that routes API Gateway access logs from a specific log group to an Object Storage bucket for 90-day WORM compliance archival.",
  "expected_behavior": [
    "Creates oci_sch_service_connector with source.kind = 'logging' scoped to a specific log_group_id",
    "Sets target.kind = 'objectStorage' with bucket and object_name_prefix following '{domain}/{purpose}/{env}/' convention",
    "Creates oci_identity_policy granting 'serviceconnectors' read on log-content and manage on objects in the target bucket",
    "Uses depends_on = [oci_identity_policy.connector_policy] on the connector resource",
    "Pins provider with version = '~> 8.0' and required_version = '>= 1.7'",
    "Sets state = 'ACTIVE' on the connector resource",
    "Deploys an OCI Monitoring alarm for ErrorCount[1m].sum() > 0 alongside the connector",
    "Does NOT omit log_group_id — source is scoped to the specific group, not all compartment logs"
  ]
}
```

## Scenario 2: Edge — Connector enters FAILED state after apply (missing IAM)

```json
{
  "skills": ["provisioning-oci-connector-hub"],
  "query": "My terraform apply succeeded but the connector shows lifecycle-state = FAILED with lifecycle-details mentioning authorization. No data is flowing to Object Storage.",
  "expected_behavior": [
    "Identifies missing or incorrectly scoped IAM policy as the root cause",
    "Points to required policy: 'allow service serviceconnectors to read log-content in compartment <src>' and 'allow service serviceconnectors to manage objects in compartment <tgt>'",
    "Explains that FAILED state silently drops all data — no replay or buffering",
    "Recommends restoring the policy then running: oci sch service-connector activate --service-connector-id <OCID>",
    "Recommends adding depends_on to the connector to prevent this on future applies",
    "References Verification Loop step 2 (connector lifecycle state check)"
  ]
}
```

## Scenario 3: Edge — Logging source without log_group_id scope in production

```json
{
  "skills": ["provisioning-oci-connector-hub"],
  "query": "I want to forward all logs from my production compartment to Logging Analytics. My source block omits log_group_id to catch everything.",
  "expected_behavior": [
    "Flags this as a 'Never Do' pattern: Logging source without log_group_id in production",
    "Explains that omitting log_group_id ingests ALL compartment logs including _Audit, VCN flow logs, and child compartments",
    "Warns about cross-team data leakage and unbounded ingestion cost",
    "Asks which specific log groups should be included and recommends listing explicit log_group_ids",
    "Does NOT generate a source block without log_group_id for a production connector"
  ]
}
```

## Scenario 4: Edge — Source-target combination: Logging loop anti-pattern

```json
{
  "skills": ["provisioning-oci-connector-hub"],
  "query": "Can I create a connector from OCI Logging as source to OCI Logging as target within the same compartment to create a centralized log copy?",
  "expected_behavior": [
    "Identifies this as a critical anti-pattern: connector loop causing exponential log amplification",
    "Explains that Logging target events in the same compartment re-trigger the Logging source, creating infinite amplification",
    "Proposes correct alternatives: Logging → Object Storage for archival, or Logging → Logging Analytics for centralized search",
    "Does NOT generate a connector with both source and target pointing to OCI Logging in the same compartment"
  ]
}
```

## Scenario 5: Misuse — Fan-out to multiple targets via single connector

```json
{
  "skills": ["provisioning-oci-connector-hub"],
  "query": "I need to send the same logs to both Object Storage and Logging Analytics. Can I add two targets to a single connector resource?",
  "expected_behavior": [
    "Clarifies the service limit: one source and one target per connector (no multi-target native support)",
    "Presents the fan-out pattern: either parallel connectors (N connectors sharing the same source) or Streaming hub (1 connector to Stream, then N connectors from Stream to each target)",
    "Asks whether routing logic is static (parallel connectors are simpler) or conditional (Streaming hub + Functions routing)",
    "Does NOT generate a single oci_sch_service_connector with multiple target blocks"
  ]
}
```
