### ✅ Always Do

## Contents
1. Initialize ObjectStorageClient in @FnConfiguration with Resource Principal
2. Close GetObject InputStream with try-with-resources
3. Guard Against OOM Before Reading Binary Objects
4. Provide contentLength on PutObject
5. Paginate ListObjects Results
6. Use UploadManager for Large/Variable-Size Files
7. Use Streaming for Large Text Files

---

**1. Initialize ObjectStorageClient in @FnConfiguration with Resource Principal**: The client MUST be created once during cold start and reused across invocations. Resource Principal is the only authentication method supported in OCI Functions. The namespace must be obtained via `getNamespace()` during init.

```java
// ✅ CORRECT: One-time init in @FnConfiguration — OCI SDK v3.x
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.GetNamespaceRequest;

public class FileHandler {
    private ObjectStorageClient objectStorageClient;
    private String namespace;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        // Resource Principal — the ONLY auth method in OCI Functions
        var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
        this.objectStorageClient = ObjectStorageClient.builder().build(provider);

        // Get namespace once during init (avoids per-invocation API call)
        this.namespace = objectStorageClient.getNamespace(
            GetNamespaceRequest.builder().build()
        ).getValue();
    }
}
```

**Why it is mandatory**: Client creation involves Resource Principal token exchange, HTTP connection pool setup, and TLS initialization (~500-1500ms). Reusing across invocations enables connection pooling and eliminates cold-start overhead on warm calls.
**Failure if omitted**: 200-1000ms added latency per invocation; connection pool never warms up.
**Source**: https://github.com/oracle-samples/oracle-functions-samples/blob/master/samples/oci-objectstorage-put-object-java/src/main/java/com/example/fn/ObjectStoragePutObject.java

---

**2. Close GetObject InputStream with try-with-resources**: `GetObject` returns an `InputStream` that MUST be explicitly closed. In hot functions (JVM persists), unclosed streams cause memory leaks and HTTP connection pool exhaustion.

```java
// ✅ CORRECT: Always use try-with-resources — OCI SDK v3.x
import com.oracle.bmc.objectstorage.requests.GetObjectRequest;
import com.oracle.bmc.objectstorage.responses.GetObjectResponse;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public String readObject(String bucketName, String objectName) {
    GetObjectRequest request = GetObjectRequest.builder()
        .namespaceName(namespace)
        .bucketName(bucketName)
        .objectName(objectName)
        .build();

    GetObjectResponse response = objectStorageClient.getObject(request);

    // CRITICAL: Always close the InputStream via try-with-resources
    try (InputStream inputStream = response.getInputStream()) {
        return new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
    } catch (Exception e) {
        throw new RuntimeException("Failed to read object: " + objectName, e);
    }
}
```

**Why it is mandatory**: In hot functions, unclosed streams keep HTTP connections open in the pool. After ~50-200 invocations, the pool is exhausted and new requests fail with timeout or connection refused.
**Failure if omitted**: Connection pool exhaustion → function hangs → 502 to caller.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/GetObject

---

**3. Guard Against OOM Before Reading Binary Objects**: OCI Functions have limited memory (128MB-2048MB). Always check `Content-Length` before reading an entire object into memory. For files >50% of allocated memory, use streaming instead.

```java
// ✅ CORRECT: Check size before in-memory read — OCI SDK v3.x
import com.oracle.bmc.objectstorage.requests.GetObjectRequest;
import com.oracle.bmc.objectstorage.responses.GetObjectResponse;

import java.io.InputStream;

public byte[] readBinaryObject(String bucketName, String objectName) {
    GetObjectRequest request = GetObjectRequest.builder()
        .namespaceName(namespace)
        .bucketName(bucketName)
        .objectName(objectName)
        .build();

    GetObjectResponse response = objectStorageClient.getObject(request);
    long contentLength = response.getContentLength();

    // Guard against OOM — function memory is limited (128MB-2048MB)
    long maxAllowed = Runtime.getRuntime().maxMemory() / 2; // 50% of available
    if (contentLength > maxAllowed) {
        throw new IllegalStateException(
            "Object too large for in-memory read: " + contentLength
            + " bytes, max allowed: " + maxAllowed);
    }

    try (InputStream inputStream = response.getInputStream()) {
        return inputStream.readAllBytes();
    } catch (Exception e) {
        throw new RuntimeException("Failed to read binary object: " + objectName, e);
    }
}
```

**Why it is mandatory**: `readAllBytes()` allocates an array the size of the file. For files exceeding ~50% of allocated memory, this causes `OutOfMemoryError` — the function is killed, returns 502, and no error handling is possible.
**Failure if omitted**: `java.lang.OutOfMemoryError` → function killed → 502 to caller.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/GetObject

---

**4. Provide contentLength on PutObject**: `Content-Length` is a required parameter for the PutObject API. Without it, the SDK fails with validation error or the service rejects with HTTP 400.

```java
// ✅ CORRECT: Always provide contentLength — OCI SDK v3.x
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import com.oracle.bmc.objectstorage.responses.PutObjectResponse;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

public String writeObject(String bucketName, String objectName, String content) {
    byte[] bytes = content.getBytes(StandardCharsets.UTF_8);

    PutObjectRequest request = PutObjectRequest.builder()
        .namespaceName(namespace)
        .bucketName(bucketName)
        .objectName(objectName)
        .contentLength((long) bytes.length)   // REQUIRED by API
        .contentType("application/json")
        .putObjectBody(new ByteArrayInputStream(bytes))
        .build();

    PutObjectResponse response = objectStorageClient.putObject(request);
    return response.getETag();
}
```

**Why it is mandatory**: `Content-Length` is required by the OCI Object Storage PutObject API. For streams of unknown size, use `UploadManager` instead.
**Failure if omitted**: HTTP 400 Bad Request or SDK validation error. Object not written.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/PutObject

---

**5. Paginate ListObjects Results**: `ListObjects` returns a maximum of 1000 objects per page. Without pagination, operations like "process all files" silently process only a fraction of the data.

```java
// ✅ CORRECT: Always paginate through all results — OCI SDK v3.x
import com.oracle.bmc.objectstorage.requests.ListObjectsRequest;
import com.oracle.bmc.objectstorage.responses.ListObjectsResponse;
import com.oracle.bmc.objectstorage.model.ObjectSummary;
import com.oracle.bmc.objectstorage.model.ListObjects;

import java.util.ArrayList;
import java.util.List;

public List<ObjectSummary> listObjects(String bucketName, String prefix) {
    List<ObjectSummary> allObjects = new ArrayList<>();
    String nextStart = null;

    do {
        ListObjectsRequest.Builder requestBuilder = ListObjectsRequest.builder()
            .namespaceName(namespace)
            .bucketName(bucketName)
            .prefix(prefix)                  // filter by virtual "folder"
            .fields("name,size,timeCreated") // include metadata
            .limit(1000);                    // max per page

        if (nextStart != null) {
            requestBuilder.start(nextStart);
        }

        ListObjectsResponse response = objectStorageClient.listObjects(
            requestBuilder.build());
        ListObjects listObjects = response.getListObjects();

        allObjects.addAll(listObjects.getObjects());
        nextStart = listObjects.getNextStartWith();  // null when done

    } while (nextStart != null);

    return allObjects;
}
```

**Why it is mandatory**: `ListObjects` returns max 1000 objects. Without checking `getNextStartWith()`, buckets with >1000 objects are silently truncated.
**Failure if omitted**: Silent data loss — processes only first 1000 objects. Logic appears correct but is incomplete.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/ListObjects

---

**6. Use UploadManager for Large/Variable-Size Files**: `UploadManager` automatically selects between single-put and multipart upload. It handles per-part retry, parallel upload, and auto-abort on failure. Initialize in `@FnConfiguration` for reuse.

```java
// ✅ CORRECT: UploadManager initialized once, reused — OCI SDK v3.x
import com.oracle.bmc.objectstorage.transfer.UploadConfiguration;
import com.oracle.bmc.objectstorage.transfer.UploadManager;
import com.oracle.bmc.objectstorage.transfer.UploadManager.UploadRequest;
import com.oracle.bmc.objectstorage.transfer.UploadManager.UploadResponse;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;

import java.io.InputStream;

private UploadManager uploadManager;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    this.objectStorageClient = ObjectStorageClient.builder().build(provider);

    // Configure for function environment — OCI SDK v3.x
    UploadConfiguration uploadConfig = UploadConfiguration.builder()
        .allowMultipartUploads(true)
        .allowParallelUploads(false)       // single-threaded is safer in functions
        .lengthPerUploadPart(20)           // 20MB per part (suitable for functions)
        .minimumLengthForMultipartUpload(20) // Use multipart above 20MB
        .build();

    this.uploadManager = new UploadManager(objectStorageClient, uploadConfig);
}

public String uploadFile(String bucketName, String objectName,
                         InputStream data, long contentLength) {
    PutObjectRequest putRequest = PutObjectRequest.builder()
        .namespaceName(namespace)
        .bucketName(bucketName)
        .objectName(objectName)
        .contentType("application/octet-stream")
        .build();

    UploadRequest uploadRequest = UploadRequest.builder(data, contentLength)
        .allowOverwrite(true)
        .build(putRequest);

    UploadResponse response = uploadManager.upload(uploadRequest);
    return response.getETag();
}
```

**Why it is mandatory**: Direct `PutObject` has no per-part retry and requires known content length. `UploadManager` auto-aborts incomplete multipart uploads on failure (preventing storage leaks).
**Failure if omitted**: Large file uploads fail without retry; incomplete multipart uploads leak storage.
**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-objectstorage/bmc-objectstorage-extensions/src/main/java/com/oracle/bmc/objectstorage/transfer/UploadManager.java

---

**7. Use Streaming for Large Text Files**: For files larger than ~50% of function memory, process line-by-line instead of loading the entire file into memory.

```java
// ✅ CORRECT: Stream-process large text files — OCI SDK v3.x
import com.oracle.bmc.objectstorage.requests.GetObjectRequest;
import com.oracle.bmc.objectstorage.responses.GetObjectResponse;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

public List<String> processLargeTextFile(String bucketName, String objectName) {
    GetObjectRequest request = GetObjectRequest.builder()
        .namespaceName(namespace)
        .bucketName(bucketName)
        .objectName(objectName)
        .build();

    GetObjectResponse response = objectStorageClient.getObject(request);
    List<String> results = new ArrayList<>();

    // Stream line-by-line — never holds entire file in memory
    try (InputStream is = response.getInputStream();
         BufferedReader reader = new BufferedReader(new InputStreamReader(is))) {

        String line;
        while ((line = reader.readLine()) != null) {
            results.add(processLine(line));
        }
    } catch (Exception e) {
        throw new RuntimeException("Failed to stream object: " + objectName, e);
    }

    return results;
}
```

**Why it is mandatory**: OCI Functions have 128MB-2048MB memory. `readAllBytes()` on a 500MB file in a 256MB function causes immediate OOM kill.
**Failure if omitted**: `OutOfMemoryError` → function killed → 502 → no recovery.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/GetObject

---

## Worked Example (from the reference PoC)

### OciServiceClient — Vault + Object Storage, both clients initialized once
// from services/func-api-facade/src/main/java/com/brx/functions/apifacade/service/OciServiceClient.java

```java
public class OciServiceClient implements OciService {

    private final ObjectStorageClient objectStorageClient;
    private final SecretsClient secretsClient;
    private String namespace;

    public OciServiceClient() {
        AbstractAuthenticationDetailsProvider provider =
                ResourcePrincipalAuthenticationDetailsProvider.builder().build();

        RetryConfiguration retryConfig = RetryConfiguration.builder()
                .terminationStrategy(new MaxAttemptsTerminationStrategy(3))
                .delayStrategy(new ExponentialBackoffDelayStrategyWithJitter(5000))
                .build();

        ClientConfiguration clientConfig = ClientConfiguration.builder()
                .connectionTimeoutMillis(5000)
                .readTimeoutMillis(15000)
                .retryConfiguration(retryConfig)
                .build();

        this.objectStorageClient = ObjectStorageClient.builder()
                .configuration(clientConfig).build(provider);
        this.secretsClient = SecretsClient.builder()
                .configuration(clientConfig).build(provider);

        // Fetch namespace once during init — cached for all warm invocations
        try {
            this.namespace = objectStorageClient.getNamespace(
                    GetNamespaceRequest.builder().build()).getValue();
        } catch (Exception e) {
            this.namespace = null; // non-fatal; putObject will fail with clear error
        }
    }

    @Override
    public void putObject(String bucketName, String objectName, String data) {
        byte[] bytes = data.getBytes(StandardCharsets.UTF_8);
        objectStorageClient.putObject(
                PutObjectRequest.builder()
                        .namespaceName(namespace)
                        .bucketName(bucketName)
                        .objectName(objectName)
                        .contentLength((long) bytes.length)   // REQUIRED
                        .putObjectBody(new ByteArrayInputStream(bytes))
                        .build());
    }

    @Override
    public String getSecret(String secretId) {
        GetSecretBundleResponse response = secretsClient.getSecretBundle(
                GetSecretBundleRequest.builder().secretId(secretId).build());
        Base64SecretBundleContentDetails content =
                (Base64SecretBundleContentDetails) response.getSecretBundle().getSecretBundleContent();
        return new String(Base64.getDecoder().decode(content.getContent()), StandardCharsets.UTF_8);
    }
}
```

Key patterns:
- Both clients use the same `retryConfig` (3 attempts, exponential backoff with jitter)
- SDK timeouts set below function timeout: connect 5s, read 15s
- Namespace fetched once; putObject uses the cached value
- `contentLength` always provided on `PutObjectRequest`

