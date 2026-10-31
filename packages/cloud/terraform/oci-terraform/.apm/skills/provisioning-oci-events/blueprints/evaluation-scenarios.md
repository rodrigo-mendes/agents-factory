# Evaluation Scenarios — provisioning-oci-events

## Scenario 1: Canonical — Object Storage event triggers a Function

```json
{
  "skills": ["provisioning-oci-events"],
  "query": "Create an OCI Events rule that triggers my VirusScanFunction whenever any object is uploaded to the 'uploads' bucket in the 'processing' compartment.",
  "expected_behavior": [
    "Creates oci_events_rule scoped to the 'processing' compartment (not root)",
    "Uses condition = jsonencode({ eventType = ['com.oraclecloud.objectstorage.createobject'], data = { bucketName = ['uploads'] } })",
    "Sets action_type = 'FAAS' with function_id referencing the Function resource or output",
    "Creates oci_identity_policy granting 'cloudevents' service principal 'use fn-invocation' in the compartment",
    "Does NOT hardcode the function OCID — uses Terraform resource reference",
    "Sets is_enabled = true (or discusses staged rollout with is_enabled = false for production)"
  ]
}
```

## Scenario 2: Edge — IAM policy missing for cloudevents service principal

```json
{
  "skills": ["provisioning-oci-events"],
  "query": "My event rule is ACTIVE and shows EventsMatched > 0 in metrics, but the Function is never invoked. The Function works via direct OCI CLI invocation.",
  "expected_behavior": [
    "Identifies missing IAM policy for 'cloudevents' service principal as root cause",
    "Points to required policy: 'allow service cloudevents to use fn-invocation in compartment <name>'",
    "Warns that events are fire-and-forget — events that fired during the IAM gap are permanently lost (no replay)",
    "Explains 60s propagation delay after adding the policy before invocations resume",
    "Does NOT suggest modifying Function code or event condition as a workaround"
  ]
}
```

## Scenario 3: Edge — Idempotency: multiple actions with at-least-once delivery

```json
{
  "skills": ["provisioning-oci-events"],
  "query": "I have an event rule with both a FAAS action (process the event) and an OSS action (audit stream). My processor is seeing occasional duplicate processing. Is this a configuration problem?",
  "expected_behavior": [
    "Explains that OCI Events uses at-least-once delivery semantics — duplicates are expected, not a configuration error",
    "Recommends the idempotency pattern: include a deduplicate key in the event payload (e.g., eventId + resourceId) and use a transactional store to detect and skip duplicates",
    "Confirms that multiple actions per rule each receive independent at-least-once delivery",
    "Does NOT suggest removing the OSS action or reducing rule triggers as a deduplication fix"
  ]
}
```

## Scenario 4: Edge — Event rule in root compartment unintentional scope

```json
{
  "skills": ["provisioning-oci-events"],
  "query": "I set compartment_id = var.tenancy_ocid on my event rule to make sure it catches events from all compartments. Is that correct?",
  "expected_behavior": [
    "Flags this as a 'Never Do' pattern: event rule in root compartment",
    "Explains that root compartment rules capture events from ALL child compartments in the tenancy, violating least-privilege",
    "Asks which compartments actually need to be monitored and recommends creating one scoped rule per compartment",
    "Warns about Function concurrency exhaustion and cost explosion from over-broad rules",
    "Does NOT generate or accept compartment_id = var.tenancy_ocid unless explicitly justified"
  ]
}
```

## Scenario 5: Misuse — Empty condition capturing all events in production

```json
{
  "skills": ["provisioning-oci-events"],
  "query": "For debugging, I temporarily set my event rule condition to '{}' to capture everything. Can I deploy this to production to avoid missing any events?",
  "expected_behavior": [
    "Identifies empty condition as the most critical anti-pattern in this skill",
    "Explains consequences: captures ALL compartment events including IAM, networking, audit — Function invoked for every event",
    "Quantifies risk: Function concurrency exhaustion (60 concurrent limit), unbounded cost, unrecoverable data loss when concurrency limit hit",
    "Shows how to enumerate specific eventTypes using jsonencode({ eventType = ['...'] })",
    "References the module variables.tf validation guard that rejects empty eventType arrays",
    "Does NOT generate a production event rule with condition = '{}' or condition = jsonencode({})"
  ]
}
```
