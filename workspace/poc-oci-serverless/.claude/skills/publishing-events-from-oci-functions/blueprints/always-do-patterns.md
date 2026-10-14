### ✅ Always Do

## Contents
1. Resource Principal + Client Initialization in @FnConfiguration
2. Publish Messages to OCI Streaming with Per-Message Error Checking
3. Publish Notification to OCI ONS Topic
4. Post Custom Metrics to OCI Monitoring
5. OCI SDK BOM for Version Management

---

**Resource Principal + Client Initialization in @FnConfiguration**: OCI SDK clients must be initialized once during cold start and reused across invocations. Resource Principal is the only acceptable auth method for OCI Functions.

```java
// ✅ CORRECT: Initialize all OCI SDK clients once in @FnConfiguration
// OCI Java SDK v3.36+ — Resource Principal with hot function reuse
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.streaming.StreamClient;
import com.oracle.bmc.ons.NotificationDataPlaneClient;
import com.oracle.bmc.queue.QueueClient;
import com.oracle.bmc.monitoring.MonitoringClient;
import com.oracle.bmc.loggingingestion.LoggingClient;

public class EventPublisher {
    private StreamClient streamClient;
    private NotificationDataPlaneClient notificationClient;
    private QueueClient queueClient;
    private MonitoringClient monitoringClient;
    private LoggingClient loggingClient;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        // ✅ Resource Principal — auto-managed by OCI Functions runtime
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();

        // ✅ Streaming requires the stream's messages_endpoint (from config)
        this.streamClient = StreamClient.builder()
            .endpoint(ctx.getConfigurationByKey("STREAM_ENDPOINT").orElseThrow())
            .build(provider);

        // ✅ Notifications requires the topic's apiEndpoint (from config)
        this.notificationClient = NotificationDataPlaneClient.builder()
            .endpoint(ctx.getConfigurationByKey("NOTIFICATION_ENDPOINT").orElseThrow())
            .build(provider);

        // ✅ Queue uses regional endpoint (auto-resolved by SDK)
        this.queueClient = QueueClient.builder().build(provider);

        // ✅ Monitoring uses telemetry-ingestion endpoint (NOT telemetry)
        this.monitoringClient = MonitoringClient.builder()
            .endpoint(ctx.getConfigurationByKey("MONITORING_ENDPOINT").orElseThrow())
            .build(provider);

        // ✅ Logging uses regional endpoint (auto-resolved by SDK)
        this.loggingClient = LoggingClient.builder().build(provider);
    }
}
```

**Why it is mandatory**: OCI SDK clients involve HTTP connection pools, TLS handshakes, and auth token exchange. Creating per invocation wastes 100–500ms+ and nullifies hot function benefits.
**Failure if omitted**: 100–500ms overhead per invocation, connection pool exhaustion, higher costs.
**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/StreamsExample.java

---

**Publish Messages to OCI Streaming with Per-Message Error Checking**: OCI Streaming is the Kafka-compatible event streaming service. Messages are sent in batch via `putMessages`. The response must be checked per-entry because HTTP 200 does NOT guarantee all messages succeeded.

```java
// ✅ CORRECT: Publish to Streaming with per-message error verification
// OCI Java SDK v3.36+ — PutMessages with partial failure handling
import com.oracle.bmc.streaming.StreamClient;
import com.oracle.bmc.streaming.model.PutMessagesDetails;
import com.oracle.bmc.streaming.model.PutMessagesDetailsEntry;
import com.oracle.bmc.streaming.model.PutMessagesResultEntry;
import com.oracle.bmc.streaming.requests.PutMessagesRequest;
import com.oracle.bmc.streaming.responses.PutMessagesResponse;

import static java.nio.charset.StandardCharsets.UTF_8;
import java.util.ArrayList;
import java.util.List;

public void publishToStream(String streamId, String key, String message) {
    List<PutMessagesDetailsEntry> messages = new ArrayList<>();
    messages.add(
        PutMessagesDetailsEntry.builder()
            .key(key.getBytes(UTF_8))      // determines partition placement
            .value(message.getBytes(UTF_8)) // message payload as bytes
            .build()
    );

    PutMessagesDetails messagesDetails = PutMessagesDetails.builder()
        .messages(messages)
        .build();

    PutMessagesRequest putRequest = PutMessagesRequest.builder()
        .streamId(streamId)
        .putMessagesDetails(messagesDetails)
        .build();

    PutMessagesResponse response = streamClient.putMessages(putRequest);

    // ✅ CRITICAL: Check per-message errors — HTTP 200 ≠ all succeeded
    int failedCount = 0;
    for (PutMessagesResultEntry entry : response.getPutMessagesResult().getEntries()) {
        if (entry.getError() != null) {
            failedCount++;
            logger.error("Message publish failed: {} - {}",
                entry.getError(), entry.getErrorMessage());
        }
    }
    if (failedCount > 0) {
        throw new RuntimeException(failedCount + " messages failed to publish");
    }
}
```

**Why it is mandatory**: Streaming `putMessages` returns HTTP 200 even with partial failures. Each `PutMessagesResultEntry` can have an `error` field indicating individual message failure.
**Failure if omitted**: Silent data loss — events appear published but are actually dropped.
**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/StreamsExample.java

---

**Publish Notification to OCI ONS Topic**: OCI Notifications (ONS) enables fan-out pub/sub for alerts, emails, SMS, and webhooks. `PublishMessage` sends to a topic with subscribers.

```java
// ✅ CORRECT: Publish notification to ONS topic
// OCI Java SDK v3.36+ — NotificationDataPlaneClient
import com.oracle.bmc.ons.NotificationDataPlaneClient;
import com.oracle.bmc.ons.model.MessageDetails;
import com.oracle.bmc.ons.requests.PublishMessageRequest;
import com.oracle.bmc.ons.responses.PublishMessageResponse;

public String publishNotification(String topicId, String title, String body) {
    // ✅ MessageDetails: title = subject line, body = content (max 64KB)
    MessageDetails messageDetails = MessageDetails.builder()
        .title(title)
        .body(body)
        .build();

    PublishMessageRequest request = PublishMessageRequest.builder()
        .topicId(topicId)
        .messageDetails(messageDetails)
        .build();

    PublishMessageResponse response = notificationClient.publishMessage(request);
    return response.getPublishResult().getMessageId();
}
```

**Why it is mandatory**: ONS is the standard OCI service for human-facing notifications and multi-protocol fan-out.
**Failure if omitted**: No alerting capability for high-value events or operational notifications.
**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/NotificationExample.java

---

**Post Custom Metrics to OCI Monitoring**: Custom metrics enable business observability. The endpoint must use `telemetry-ingestion` (not `telemetry`). Timestamps must be within 2h past / 10min future.

```java
// ✅ CORRECT: Post custom metrics using telemetry-ingestion endpoint
// OCI Java SDK v3.36+ — MonitoringClient with PostMetricData
import com.oracle.bmc.monitoring.MonitoringClient;
import com.oracle.bmc.monitoring.model.Datapoint;
import com.oracle.bmc.monitoring.model.MetricDataDetails;
import com.oracle.bmc.monitoring.model.PostMetricDataDetails;
import com.oracle.bmc.monitoring.requests.PostMetricDataRequest;
import com.oracle.bmc.monitoring.responses.PostMetricDataResponse;

import java.util.*;

public void postCustomMetric(String compartmentId, String namespace,
                             String metricName, double value) {
    // ✅ Timestamp must be within 2h past / 10min future
    Datapoint datapoint = Datapoint.builder()
        .timestamp(new Date())
        .value(value)
        .count(1)
        .build();

    Map<String, String> dimensions = new HashMap<>();
    dimensions.put("functionName", "api-handler");
    dimensions.put("environment", "production");

    MetricDataDetails metricData = MetricDataDetails.builder()
        .namespace(namespace)           // e.g., "custom_metrics"
        .compartmentId(compartmentId)
        .name(metricName)               // e.g., "orders_processed"
        .dimensions(dimensions)         // max 20 dimensions
        .datapoints(Collections.singletonList(datapoint))
        .build();

    PostMetricDataDetails postDetails = PostMetricDataDetails.builder()
        .metricData(Collections.singletonList(metricData))
        .batchAtomicity(PostMetricDataDetails.BatchAtomicity.NonAtomic)
        .build();

    PostMetricDataRequest request = PostMetricDataRequest.builder()
        .postMetricDataDetails(postDetails)
        .build();

    PostMetricDataResponse response = monitoringClient.postMetricData(request);
    // ✅ Check for failed metrics
    // response.getPostMetricDataResponseDetails().getFailedMetricsCount()
}
```

**Why it is mandatory**: Custom metrics drive OCI Alarms and dashboards for business observability.
**Failure if omitted**: No visibility into business KPIs, no threshold-based alerting.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/MetricData/PostMetricData

---

**OCI SDK BOM for Version Management**: The BOM ensures consistent versions across all OCI SDK modules, preventing transitive dependency conflicts.

```xml
<!-- ✅ CORRECT: OCI SDK BOM in pom.xml — OCI Java SDK v3.36+ -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-bom</artifactId>
            <version>3.36.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <!-- Add only the modules you need (no version required with BOM) -->
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-common</artifactId>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-streaming</artifactId>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-ons</artifactId>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-queue</artifactId>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-monitoring</artifactId>
    </dependency>
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-loggingingestion</artifactId>
    </dependency>
</dependencies>
```

**Why it is mandatory**: Without the BOM, different OCI SDK module versions can cause classpath conflicts and runtime errors.
**Failure if omitted**: `NoSuchMethodError`, `ClassNotFoundException` at runtime due to version mismatches.
**Source**: https://github.com/oracle/oci-java-sdk

---

