### 🚫 Never Do

**Anti-Pattern**: Creating OCI SDK Clients in Handler Method

```java
// 🚫 WRONG: Client creation per invocation — wastes 100-500ms+ per call
// OCI Java SDK v3.x+ — clients are expensive to create (HTTP pools, TLS, auth tokens)
public ApiResponse handleRequest(ApiRequest request) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    var streamClient = StreamClient.builder()
        .endpoint(streamEndpoint)
        .build(provider);  // EXPENSIVE: ~100-500ms per invocation!

    publishToStream(streamClient, request);
    streamClient.close(); // Wasteful — destroys connection pool
    return ApiResponse.ok("done");
}

// ✅ CORRECT: Initialize once in @FnConfiguration, reuse across invocations
private StreamClient streamClient;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    this.streamClient = StreamClient.builder()
        .endpoint(ctx.getConfigurationByKey("STREAM_ENDPOINT").orElseThrow())
        .build(provider);
}

public ApiResponse handleRequest(ApiRequest request) {
    publishToStream(streamClient, request); // Reuses warm client
    return ApiResponse.ok("done");
}
```

**Why it is prohibited**: OCI SDK clients involve HTTP connection pools, TLS handshakes, and auth token exchange. Creating per invocation defeats hot function optimization.
**Actual impact**: 100–500ms overhead per invocation, connection pool exhaustion, 2–5x higher function costs.
**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/StreamsExample.java

---

**Anti-Pattern**: Using Wrong Monitoring Endpoint (`telemetry` instead of `telemetry-ingestion`)

```java
// 🚫 WRONG: Using telemetry endpoint for metric ingestion
// OCI Java SDK v3.x+ — PostMetricData requires telemetry-ingestion
MonitoringClient client = MonitoringClient.builder()
    .endpoint("https://telemetry.us-ashburn-1.oraclecloud.com") // WRONG endpoint!
    .build(provider);
client.postMetricData(request); // 404 or auth error

// ✅ CORRECT: Use telemetry-ingestion endpoint for PostMetricData
MonitoringClient client = MonitoringClient.builder()
    .endpoint("https://telemetry-ingestion.us-ashburn-1.oraclecloud.com")
    .build(provider);
client.postMetricData(request); // Correct!
```

**Why it is prohibited**: `PostMetricData` uses a separate ingestion service. The `telemetry` endpoint is for queries only.
**Actual impact**: 404 Not Found or authentication errors. Metrics silently not published. Monitoring blind spots.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/MetricData/PostMetricData

---

**Anti-Pattern**: Ignoring Per-Message Errors in Streaming Response

```java
// 🚫 WRONG: Assuming HTTP 200 means all messages succeeded
// OCI Java SDK v3.x+ — putMessages can return HTTP 200 with partial failures
PutMessagesResponse response = streamClient.putMessages(putRequest);
// response.getHttpStatusCode() == 200 does NOT mean all messages succeeded!
return ApiResponse.ok("all published"); // WRONG — partial failures possible

// ✅ CORRECT: Check each entry for individual errors
PutMessagesResponse response = streamClient.putMessages(putRequest);
List<String> errors = new ArrayList<>();
for (PutMessagesResultEntry entry : response.getPutMessagesResult().getEntries()) {
    if (entry.getError() != null) {
        errors.add(entry.getError() + ": " + entry.getErrorMessage());
    }
}
if (!errors.isEmpty()) {
    throw new RuntimeException("Partial publish failure: " + String.join(", ", errors));
}
```

**Why it is prohibited**: Streaming `putMessages` returns HTTP 200 even with partial failures. Each `PutMessagesResultEntry` may contain error details.
**Actual impact**: Silent data loss — events appear published but are dropped without any error signal.
**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/StreamsExample.java

---

**Anti-Pattern**: Exceeding Streaming 1MB Message Batch Limit

```java
// 🚫 WRONG: Sending >1MB total in one putMessages call
// OCI Streaming API v20180418 — hard limit of 1MB total per PutMessages request
List<PutMessagesDetailsEntry> messages = new ArrayList<>();
for (String largePayload : payloads) {
    messages.add(PutMessagesDetailsEntry.builder()
        .value(largePayload.getBytes(UTF_8))
        .build());
}
streamClient.putMessages(PutMessagesRequest.builder()
    .streamId(streamId)
    .putMessagesDetails(PutMessagesDetails.builder().messages(messages).build())
    .build()); // HTTP 400 — request too large

// ✅ CORRECT: Batch messages respecting 1MB total limit
private static final int MAX_BATCH_SIZE_BYTES = 1_000_000; // 1MB

public void publishBatched(String streamId, List<String> payloads) {
    List<PutMessagesDetailsEntry> batch = new ArrayList<>();
    int currentSize = 0;

    for (String payload : payloads) {
        byte[] value = payload.getBytes(UTF_8);
        if (currentSize + value.length > MAX_BATCH_SIZE_BYTES) {
            flushBatch(streamId, batch);
            batch = new ArrayList<>();
            currentSize = 0;
        }
        batch.add(PutMessagesDetailsEntry.builder().value(value).build());
        currentSize += value.length;
    }
    if (!batch.isEmpty()) {
        flushBatch(streamId, batch);
    }
}
```

**Why it is prohibited**: `PutMessages` has a hard limit of 1MB total per request. No limit on message count, but total size must be ≤ 1MB.
**Actual impact**: HTTP 400 Bad Request — entire batch rejected, no messages published.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/streaming/20180418/Message/PutMessages

---

**Anti-Pattern**: Hardcoding Service Endpoints

```java
// 🚫 WRONG: Hardcoded endpoint strings
// OCI Java SDK v3.x+ — endpoints are dynamic, assigned at resource creation
StreamClient client = StreamClient.builder()
    .endpoint("https://cell-1.streaming.us-ashburn-1.oci.oraclecloud.com")
    .build(provider);

// ✅ CORRECT: Endpoints from function configuration
@FnConfiguration
public void configure(RuntimeContext ctx) {
    String endpoint = ctx.getConfigurationByKey("STREAM_ENDPOINT").orElseThrow(
        () -> new RuntimeException("STREAM_ENDPOINT config required"));
    this.streamClient = StreamClient.builder().endpoint(endpoint).build(provider);
}
// Set via func.yaml config or application-level config:
// STREAM_ENDPOINT=https://cell-1.streaming.us-ashburn-1.oci.oraclecloud.com
```

**Why it is prohibited**: Stream endpoints are dynamically assigned at creation. Hardcoding breaks when streams are recreated or moved.
**Actual impact**: Function breaks silently on infrastructure changes. Endpoint rotation causes outage.
**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/StreamsExample.java

---

**Anti-Pattern**: Publishing Metrics with Stale Timestamps

```java
// 🚫 WRONG: Using timestamps older than 2 hours
// OCI Monitoring API v20180401 — strict timestamp window
Datapoint datapoint = Datapoint.builder()
    .timestamp(eventTime) // eventTime is 3 hours ago!
    .value(42.0)
    .build();
// PostMetricData will reject — max 2h in the past

// ✅ CORRECT: Use current time or ensure timestamp is within the 2h window
Datapoint datapoint = Datapoint.builder()
    .timestamp(new Date()) // Current time — always valid
    .value(42.0)
    .count(1)
    .build();
```

**Why it is prohibited**: `PostMetricData` requires timestamps within 2 hours in the past and 10 minutes in the future. Out-of-window metrics are silently dropped.
**Actual impact**: Metrics silently dropped. Empty dashboards. Alarms never trigger. Monitoring blind spots.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/MetricData/PostMetricData

---

