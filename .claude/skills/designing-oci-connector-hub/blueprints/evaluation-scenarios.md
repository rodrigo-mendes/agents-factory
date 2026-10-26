# Evaluation Scenarios — designing-oci-connector-hub

## Scenario 1: Canonical — Log Archival Pipeline to Object Storage

```json
{
  "skills": ["designing-oci-connector-hub"],
  "query": "Design a Connector Hub pipeline to archive all API Gateway access logs from the prod compartment to an Object Storage bucket for 90-day compliance retention. Include IAM and tagging.",
  "expected_behavior": [
    "Scopes Logging source to the specific log group (not entire compartment) via log_group_id",
    "Sets object_name_prefix with convention {domain}/{purpose}/{env}/ (e.g., api-logs/access/prod/)",
    "Creates IAM policy for service serviceconnectors BEFORE the connector resource via depends_on",
    "Applies minimum required IAM verbs: read log-content in source compartment + manage objects in target compartment with bucket condition",
    "Tags connector with Environment, Owner, and CostCenter",
    "Recommends deploying an ErrorCount > 0 OCI Monitoring alarm on the connector",
    "Does NOT scope the Logging source to ALL compartment logs (no omission of log_group_id)"
  ]
}
```

## Scenario 2: Edge Case — Connector Enters FAILED State After Apply

```json
{
  "skills": ["designing-oci-connector-hub"],
  "query": "After terraform apply completes successfully, the OCI Console shows the connector in FAILED state with lifecycle-details 'Authorization failed'. What are the design steps to diagnose and fix this?",
  "expected_behavior": [
    "Runs verification loop: oci sch service-connector get --query 'data.{state,details}' to read lifecycle-details",
    "Identifies root cause as IAM policy not created before connector activation (depends_on missing or policy statement wrong)",
    "Checks oci iam policy list to verify the serviceconnectors service principal policy exists",
    "Corrects policy statement syntax: allow service serviceconnectors to read log-content / manage objects",
    "Adds depends_on = [oci_identity_policy.connector_policy] to prevent recurrence",
    "Reactivates connector with oci sch service-connector activate after policy correction",
    "Does NOT suggest deleting and recreating the connector as first step"
  ]
}
```

## Scenario 3: Edge Case — Queue Source Plugin for Worker Pipeline

```json
{
  "skills": ["designing-oci-connector-hub"],
  "query": "I want to drain an OCI Queue using Connector Hub and route messages to a processing Function. What source type and configuration do I use?",
  "expected_behavior": [
    "Identifies source.kind = 'plugin' (QueueSource plugin) — available in API v20200909+",
    "Warns that this feature requires API v20200909 and is NOT available with pre-plugin connector patterns",
    "Configures Functions as the target (not Streaming) for direct worker invocation",
    "Recommends tuning batch_size_in_kbs and batch_time_in_sec to avoid thousands of tiny cold-start invocations",
    "Scopes IAM to allow service serviceconnectors to use queues in the source compartment",
    "Does NOT recommend writing a custom consumer daemon when the plugin can handle queue draining"
  ]
}
```

## Scenario 4: Misuse Case — Connector Loop Anti-Pattern

```json
{
  "skills": ["designing-oci-connector-hub"],
  "query": "I want to create a connector that reads from my application log group and writes back to another log group in the same compartment for enrichment. Is this safe?",
  "expected_behavior": [
    "Flags this as a CRITICAL anti-pattern: Logging source + Logging target in the same compartment creates a connector loop",
    "Explains the mechanism: target log group events re-trigger the source connector, causing exponential log amplification",
    "Warns of tenancy-wide cost explosion from unbounded log ingestion",
    "Proposes safe alternatives: route to Object Storage for enrichment via Functions, or use a Functions target for in-flight transformation without writing back to Logging",
    "Does NOT proceed to design the loop connector without raising the critical risk",
    "Recommends setting log_group_id on the source to the most specific possible scope as a general guard"
  ]
}
```

## Scenario 5: Edge Case — Streaming Source TRIM_HORIZON on Reactivation

```json
{
  "skills": ["designing-oci-connector-hub"],
  "query": "My Streaming-source connector was deactivated for 3 days for maintenance. I'm about to reactivate it with TRIM_HORIZON cursor strategy. What should I warn the team about?",
  "expected_behavior": [
    "Warns that TRIM_HORIZON replays ALL retained Streaming data (up to 7 days) from the oldest available offset",
    "Estimates the data volume that will be replayed based on 3-day downtime",
    "Confirms downstream systems must be idempotent to handle replayed events without duplicate side effects",
    "Offers LATEST cursor as an alternative if replaying historical data is not required (discards events from downtime period)",
    "Documents the trade-off: TRIM_HORIZON = no data loss but duplicates; LATEST = no duplicates but gap",
    "Does NOT activate the connector without surfacing the replay risk"
  ]
}
```
