# OCI Service Mocking Patterns

Complete mock setup examples for each OCI service integration with FnTestingRule v1.1.x.

---

## Object Storage

```java
@Before
public void setup() {
    testing.addSharedClass(MockOciClients.class);
    testing.addSharedClassPrefix("com.eci.functions.mocks.");
    testing.addSharedClassPrefix("com.oracle.bmc.");  // Required for BmcException catch

    ObjectStorageClient mock = mock(ObjectStorageClient.class);

    // getObject
    when(mock.getObject(any(GetObjectRequest.class)))
        .thenReturn(GetObjectResponse.builder()
            .contentLength(100L)
            .inputStream(new ByteArrayInputStream("content".getBytes(UTF_8)))
            .build());

    // putObject
    when(mock.putObject(any(PutObjectRequest.class)))
        .thenReturn(PutObjectResponse.builder().eTag("etag-123").build());

    // listObjects (paginated)
    when(mock.listObjects(any(ListObjectsRequest.class)))
        .thenReturn(ListObjectsResponse.builder()
            .listObjects(ListObjects.builder()
                .objects(List.of(ObjectSummary.builder()
                    .name("file.json").size(100L).build()))
                .build())
            .build());

    MockOciClients.objectStorageClient = mock;
}
```

---

## Vault / Secrets

```java
@Before
public void setupVault() {
    SecretsClient mock = mock(SecretsClient.class);

    String encodedSecret = Base64.getEncoder()
        .encodeToString("my-secret-value".getBytes());

    when(mock.getSecretBundle(any(GetSecretBundleRequest.class)))
        .thenReturn(GetSecretBundleResponse.builder()
            .secretBundle(SecretBundle.builder()
                .secretBundleContent(Base64SecretBundleContentDetails.builder()
                    .content(encodedSecret)
                    .build())
                .build())
            .build());

    MockOciClients.secretsClient = mock;
}
```

---

## Streaming

```java
@Before
public void setupStreaming() {
    StreamClient mock = mock(StreamClient.class);

    // Success — null error field means success
    PutMessagesResultEntry success = PutMessagesResultEntry.builder()
        .offset(100L).partition("0").build();

    when(mock.putMessages(any(PutMessagesRequest.class)))
        .thenReturn(PutMessagesResponse.builder()
            .putMessagesResult(PutMessagesResult.builder()
                .entries(List.of(success))
                .build())
            .build());

    MockOciClients.streamClient = mock;
}

// Test partial failure
@Test
public void testStreamingPartialFailure() {
    PutMessagesResultEntry fail = PutMessagesResultEntry.builder()
        .error("MessageTooLarge")
        .errorMessage("Exceeds 1MB limit")
        .build();

    when(MockOciClients.streamClient.putMessages(any()))
        .thenReturn(PutMessagesResponse.builder()
            .putMessagesResult(PutMessagesResult.builder()
                .entries(List.of(fail)).build())
            .build());

    testing.givenEvent()
        .withHeader("content-type", "application/json")
        .withBody("{\"action\":\"publish\",\"message\":\"large\"}")
        .enqueue();
    testing.thenRun(PublisherFunction.class, "handleRequest");

    FnResult result = testing.getOnlyResult();
    assertTrue(result.getBodyAsString().contains("error"));
}
```

---

## Notifications (ONS)

```java
@Before
public void setupNotifications() {
    NotificationDataPlaneClient mock = mock(NotificationDataPlaneClient.class);

    when(mock.publishMessage(any(PublishMessageRequest.class)))
        .thenReturn(PublishMessageResponse.builder()
            .publishResult(PublishResult.builder()
                .messageId("msg-12345")
                .timeStamp(new Date())
                .build())
            .build());

    MockOciClients.notificationClient = mock;
}
```

---

## Queue

```java
@Before
public void setupQueue() {
    QueueClient mock = mock(QueueClient.class);

    when(mock.putMessages(any(PutMessagesRequest.class)))
        .thenReturn(PutMessagesResponse.builder()
            .putMessages(PutMessages.builder()
                .messages(List.of(PutMessagesDetailsEntry.builder()
                    .id(1L).build()))
                .build())
            .build());

    MockOciClients.queueClient = mock;
}
```

---

## Monitoring (Custom Metrics)

```java
@Before
public void setupMonitoring() {
    MonitoringClient mock = mock(MonitoringClient.class);

    when(mock.postMetricData(any(PostMetricDataRequest.class)))
        .thenReturn(PostMetricDataResponse.builder()
            .postMetricDataResponseDetails(
                PostMetricDataResponseDetails.builder()
                    .failedMetricsCount(0)
                    .failedMetrics(Collections.emptyList())
                    .build())
            .build());

    MockOciClients.monitoringClient = mock;
}

// Verify metric was emitted
@Test
public void testMetricEmission() {
    testing.givenEvent()
        .withHeader("content-type", "application/json")
        .withBody("{\"action\":\"process\"}")
        .enqueue();
    testing.thenRun(MetricsFunction.class, "handleRequest");

    verify(MockOciClients.monitoringClient)
        .postMetricData(any(PostMetricDataRequest.class));
}
```

---

## BmcException Error Path Testing

⚠️ **Prerequisite**: You MUST share OCI SDK classes for BmcException catch blocks to work across FnTestingRule's classloader boundary:
```java
testing.addSharedClassPrefix("com.oracle.bmc.");
```
Without this, `catch (BmcException e)` won't match exceptions thrown from mocked services (different class identity across classloaders).

### BmcException Constructors (SDK 3.86+)

```java
import com.oracle.bmc.model.BmcException;
import java.net.SocketTimeoutException;

// Status code error (404, 429, 500, etc.)
new BmcException(int statusCode, String serviceCode, String message, String opcRequestId)

// Client-side timeout — isTimeout() returns true when cause is SocketTimeoutException
new BmcException(boolean isClientSide, String message, Throwable cause, String opcRequestId)
// Example: new BmcException(true, "Timeout", new SocketTimeoutException("connect timed out"), "opc-req-1")

// Alternative: mock for full control over isTimeout()
BmcException timeout = mock(BmcException.class);
when(timeout.isTimeout()).thenReturn(true);
when(timeout.getStatusCode()).thenReturn(408);
when(timeout.getOpcRequestId()).thenReturn("opc-req-1");
```

### Error Code Examples

Test all error codes your function handles:

```java
// 404 — Not Found
when(mock.getObject(any()))
    .thenThrow(new BmcException(404, "ObjectNotFound", "Not found", "opc-req-1"));

// 429 — Rate Limited
when(mock.putObject(any()))
    .thenThrow(new BmcException(429, "TooManyRequests", "Rate limited", "opc-req-2"));

// Timeout
BmcException timeout = mock(BmcException.class);
when(timeout.isTimeout()).thenReturn(true);
when(timeout.getOpcRequestId()).thenReturn("opc-req-3");
when(mock.getObject(any())).thenThrow(timeout);

// 401/403 — Auth failures (indicates IAM misconfiguration)
when(mock.putObject(any()))
    .thenThrow(new BmcException(403, "NotAuthorized", "Permission denied", "opc-req-4"));
```

---

## MockOciClients Template

```java
package com.eci.functions.mocks;

import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.secrets.SecretsClient;
import com.oracle.bmc.streaming.StreamClient;
import com.oracle.bmc.ons.NotificationDataPlaneClient;
import com.oracle.bmc.queue.QueueClient;
import com.oracle.bmc.monitoring.MonitoringClient;

/**
 * Static mock holder — shared across FnTestingRule class loader boundary.
 * Use with testing.addSharedClass(MockOciClients.class).
 */
public class MockOciClients {
    public static ObjectStorageClient objectStorageClient;
    public static SecretsClient secretsClient;
    public static StreamClient streamClient;
    public static NotificationDataPlaneClient notificationClient;
    public static QueueClient queueClient;
    public static MonitoringClient monitoringClient;
    public static String namespace = "test-namespace";

    public static void reset() {
        objectStorageClient = null;
        secretsClient = null;
        streamClient = null;
        notificationClient = null;
        queueClient = null;
        monitoringClient = null;
        namespace = "test-namespace";
    }
}
```

---

## Interface Abstraction Alternative

For complex functions (3+ services), prefer interface abstraction over addSharedClass:

```java
// Interface
public interface StorageService {
    String putObject(String bucket, String name, byte[] data);
    byte[] getObject(String bucket, String name);
}

// Production
public class OciStorageService implements StorageService { /* real SDK calls */ }

// Test
public class MockServiceHolder {
    public static StorageService storageService;
}

// Setup
testing.addSharedClass(MockServiceHolder.class);
testing.addSharedClass(StorageService.class);
testing.addSharedClassPrefix("com.eci.functions.services.");
testing.addSharedClassPrefix("com.oracle.bmc.");  // Required for BmcException catch
MockServiceHolder.storageService = mock(StorageService.class);
```
