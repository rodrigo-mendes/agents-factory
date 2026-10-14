# Evaluation Scenarios — provisioning-oci-streaming

## Scenario 1 (Canonical): Private Stream Pool with Multiple Streams

```json
{
  "skills": ["provisioning-oci-streaming"],
  "query": "Provision a private Stream Pool in a VCN subnet with a KMS key and three streams: 'events' (5 partitions, 48h retention), 'audit' (3 partitions, 168h retention), 'notifications' (1 partition, 24h retention).",
  "expected_behavior": [
    "Generates oci_streaming_stream_pool with private_endpoint_settings (subnet_id, nsg_ids)",
    "References customer-managed KMS key on the pool (custom_encryption_key)",
    "Uses for_each over a map variable to create all three streams",
    "All streams reference stream_pool_id — NOT compartment_id directly",
    "Includes lifecycle ignore_changes = [kafka_settings[0].bootstrap_servers] on pool",
    "Outputs: stream_pool_id, stream_pool_endpoint, kafka_bootstrap_servers, stream_ids, stream_messages_endpoints",
    "Freeform or defined tags on all resources",
    "Does NOT use compartment_id and stream_pool_id together on any stream"
  ]
}
```

## Scenario 2 (Edge): Missing IAM Policy / Quota Reached

```json
{
  "skills": ["provisioning-oci-streaming"],
  "query": "After applying the Streaming module I get 'TopicAuthorizationException' when a function tries to produce. What is missing?",
  "expected_behavior": [
    "Identifies missing IAM policy: 'Allow dynamic-group X to use stream-push in compartment Y'",
    "Distinguishes stream-push (produce) from stream-pull (consume) verbs",
    "Notes the tenancy-level limit of 500 total partitions — advises checking current usage before planning more streams",
    "Does NOT suggest changing the stream pool to PUBLIC as a workaround",
    "Provides exact OCI CLI command to verify partition counts: oci streaming admin stream list ..."
  ]
}
```

## Scenario 3 (Edge): Partition Count and Retention — Immutability Constraints

```json
{
  "skills": ["provisioning-oci-streaming"],
  "query": "I created a stream with 2 partitions and 24h retention. Traffic grew and I need 10 partitions and 72h retention. How do I change this with Terraform?",
  "expected_behavior": [
    "States clearly that both partitions and retention_in_hours are IMMUTABLE after creation",
    "Explains that changing partitions forces destroy/recreate with DATA LOSS",
    "Proposes correct migration path: create new stream alongside old, shift consumers, decommission old",
    "Shows Terraform plan approach: add new stream resource, drain old, then remove old with state rm",
    "Does NOT suggest using terraform taint or just updating the attribute in-place",
    "Recommends over-provisioning partitions slightly at creation to defer migrations"
  ]
}
```

## Scenario 4 (Misuse): Public Stream Pool for Service Connector Hub

```json
{
  "skills": ["provisioning-oci-streaming"],
  "query": "I am using OCI Service Connector Hub to route logs into a stream. My architect says the stream pool must be private, but the SCH documentation implies public pools work fine. Who is correct?",
  "expected_behavior": [
    "Acknowledges both sides: SCH can target PUBLIC pools and it works technically",
    "States the skill's default is PRIVATE for production because a public pool exposes the Kafka endpoint to the internet",
    "Cross-references the provisioning-oci-event-driven-pubsub skill note about SCH + public pool as an accepted exception in some architectures",
    "Presents the trade-off: PUBLIC simplifies SCH wiring but removes network-level access control",
    "Recommends confirming compliance requirements (PCI-DSS / SOC2) before choosing PUBLIC",
    "Does NOT silently output a public pool when a private pool was the project default"
  ]
}
```
