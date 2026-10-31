# Evaluation Scenarios — provisioning-oci-event-driven-pubsub

## Scenario 1: Canonical — Full pub/sub stack apply (PUBLIC pool + two SCH connectors + IAM)

```json
{
  "skills": ["provisioning-oci-event-driven-pubsub"],
  "query": "Provision the complete event-driven pub/sub stack on OCI: a PUBLIC Streaming pool with one stream, two Service Connector Hub connectors for fan-out (notify and audit consumers), consumer Function Applications, and all required IAM policies.",
  "expected_behavior": [
    "Omits private_endpoint_settings block on oci_streaming_stream_pool (PUBLIC pool)",
    "Creates two oci_sch_service_connector resources via for_each, each pointing at the same stream_id",
    "Adds depends_on = [var.iam_dependencies] on each oci_sch_service_connector to enforce IAM ordering",
    "Includes all four IAM verbs: stream-push (producer DG), STREAM_READ+STREAM_CONSUME (serviceconnector), fn-function (serviceconnector), fn-invocation (serviceconnector)",
    "Sets memory_in_mbs = 1024 and timeout_in_seconds = 300 on consumer Function resources",
    "Adds lifecycle { prevent_destroy = true } on oci_streaming_stream"
  ]
}
```

## Scenario 2: Edge — optional+computed attribute change (switching pool from PRIVATE to PUBLIC)

```json
{
  "skills": ["provisioning-oci-event-driven-pubsub"],
  "query": "The stream pool was created with private_endpoint_settings and SCH connectors are failing with ErrorsAtSource. I removed private_endpoint_settings from the HCL but terraform plan shows no change. How do I fix this?",
  "expected_behavior": [
    "Explains that private_endpoint_settings is optional+computed — removing it from HCL is a NO-OP",
    "Instructs user to run: terraform apply -replace='module.streaming.oci_streaming_stream_pool.this'",
    "Warns that replace cascades to oci_streaming_stream (immutable partitions/retention) and dependent SCH connectors",
    "Does NOT suggest plain terraform apply as a fix",
    "Does NOT suggest modifying provider version as a workaround"
  ]
}
```

## Scenario 3: Edge — SCH connector enters FAILED immediately after apply

```json
{
  "skills": ["provisioning-oci-event-driven-pubsub"],
  "query": "After terraform apply the SCH connectors show lifecycle-state=FAILED with no details. The stream pool is ACTIVE. What went wrong?",
  "expected_behavior": [
    "Identifies missing or mis-scoped IAM policy as the most likely cause",
    "Checks that depends_on = [var.iam_dependencies] is present on oci_sch_service_connector",
    "Verifies all four required verbs are present in the streaming policy (stream-push, STREAM_READ, STREAM_CONSUME, fn-function, fn-invocation)",
    "Checks that policy compartment scope matches the compartment containing stream, function, and connector",
    "Does NOT suggest recreating the stream pool as a first step"
  ]
}
```

## Scenario 4: Misuse — setting provisioned_concurrency = 1

```json
{
  "skills": ["provisioning-oci-event-driven-pubsub"],
  "query": "I want exactly one warm container per consumer function to eliminate cold starts. Can I set provisioned_concurrency_config count = 1 in the function resource?",
  "expected_behavior": [
    "Explains that OCI API rejects provisioned_concurrency count < 10 (minimum is 10)",
    "Warns that provisioned_concurrency_config is optional+computed — plain apply with count=0 or count=1 is either rejected or a no-op",
    "States that for two consumer functions, minimum warm containers = 20 (10 each) with associated cost",
    "Offers alternatives: raise memory_in_mbs + timeout_in_seconds (cheapest), or GraalVM native image (cold start ~2-5s), or async decouple via ONS/Queue",
    "Does NOT generate HCL with provisioned_concurrency count < 10"
  ]
}
```

## Scenario 5: Misuse — single SCH connector routing to multiple function targets

```json
{
  "skills": ["provisioning-oci-event-driven-pubsub"],
  "query": "Can I configure one Service Connector Hub connector to invoke two different functions — one for notifications and one for audit logging?",
  "expected_behavior": [
    "States clearly that oci_sch_service_connector supports exactly one target per connector",
    "Explains that fan-out requires one connector per consumer, each with independent cursor state",
    "Shows the correct pattern: two oci_sch_service_connector resources in the for_each map pointing at the same stream_id",
    "Does NOT generate HCL with multiple targets on a single connector",
    "Does NOT suggest SCH tasks or filter rules as a workaround for fan-out"
  ]
}
```
