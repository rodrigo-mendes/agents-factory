# Evaluation Scenarios — publishing-events-from-oci-functions

## Scenario 1 (Canonical): Streaming Producer with Partition Key and Error Checking

```json
{
  "skills": ["publishing-events-from-oci-functions"],
  "query": "Write a Java OCI Function that publishes order events to OCI Streaming. Each event should use the order ID as the partition key to guarantee per-order ordering. Check for per-message errors in the response.",
  "expected_behavior": [
    "Initializes StreamClient with ResourcePrincipalAuthenticationDetailsProvider in @FnConfiguration",
    "Sets stream messages endpoint from config (ctx.getConfigurationByKey) — not hardcoded",
    "Encodes message value as byte[] (base64-compatible)",
    "Sets partition key via PutMessagesDetailsEntry.builder().key(orderId.getBytes())",
    "Calls streamClient.putMessages() and checks PutMessagesResult.getEntries() for per-entry errors",
    "Throws or logs on partial failure — does NOT treat HTTP 200 as guaranteed success",
    "StreamClient is initialized once in @FnConfiguration, not inside the handler method",
    "Does NOT use API keys or config file — Resource Principal only"
  ]
}
```

## Scenario 2 (Edge): Missing IAM Policy Causing BmcException 401

```json
{
  "skills": ["publishing-events-from-oci-functions"],
  "query": "My function throws BmcException with status 401 when calling putMessages on Streaming. Resource Principal is configured. What IAM policy is missing?",
  "expected_behavior": [
    "Identifies required policy: 'allow dynamic-group <dg> to use stream-push in compartment <comp>'",
    "Distinguishes stream-push (producer) from stream-pull (consumer) — wrong verb also causes 401",
    "Checks that Dynamic Group matching rule covers the function's OCID or app compartment",
    "Notes IAM propagation delay (~60s) — policy may not be effective immediately after creation",
    "Provides OCI CLI verification: fn inspect function <app> <fn> to confirm dynamic group is matched",
    "Does NOT suggest downgrading to 'manage streams' as a broader workaround"
  ]
}
```

## Scenario 3 (Edge): Cold Start Latency — SDK Client Initialization

```json
{
  "skills": ["publishing-events-from-oci-functions"],
  "query": "My function takes 3 seconds on first invocation but only 20ms on subsequent calls. It publishes to both Streaming and Notifications. How can I reduce cold start latency?",
  "expected_behavior": [
    "Confirms cold start overhead is caused by SDK client TLS handshake + Resource Principal token fetch (~500ms per client)",
    "Confirms that initializing StreamClient and NotificationClient in @FnConfiguration (not handler) is the correct pattern — clients are reused across warm invocations",
    "Advises verifying both clients are annotated fields initialized in @FnConfiguration, not local variables in handleRequest",
    "Does NOT suggest initializing clients in a static initializer block (no access to FDK config)",
    "Mentions that GraalVM native image can reduce cold start but requires significant build changes — ask first before recommending"
  ]
}
```

## Scenario 4 (Misuse): Wrong Service Selection — Using Streaming Instead of Notifications for Fan-out)

```json
{
  "skills": ["publishing-events-from-oci-functions"],
  "query": "I need to notify 5 downstream systems (email, webhook, another function, PagerDuty, Slack) every time an order is placed. I was told to publish to OCI Streaming. Is that the right choice?",
  "expected_behavior": [
    "Identifies this as a fan-out pattern — Streaming is NOT the right tool for fan-out delivery",
    "Explains that Streaming is ordered partitioned log: all 5 consumers would read the SAME stream independently and must be coded separately",
    "Recommends OCI Notifications (ONS) instead: one publishMessage() delivers to all subscriptions (email, HTTPS, Function, PagerDuty via webhook) automatically",
    "Presents trade-off table: Streaming (ordered, replay, high throughput) vs Notifications (fan-out, push delivery, 60 TPM/topic limit)",
    "Notes ONS 60 TPM limit per topic — if order volume exceeds this, a combination (Streaming → Connector Hub → ONS) may be needed",
    "Does NOT generate a Streaming implementation for a pure fan-out use case without flagging the mismatch"
  ]
}
```
