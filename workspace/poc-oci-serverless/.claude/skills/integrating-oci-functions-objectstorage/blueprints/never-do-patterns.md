### 🚫 Never Do

**Anti-Pattern 1: Creating ObjectStorageClient Per Invocation**

```java
// 🚫 WRONG: Creating new client every invocation — wastes 200-1000ms
// This is the #1 performance mistake in OCI Functions
public String handleRequest(String input) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    var client = ObjectStorageClient.builder().build(provider); // EXPENSIVE!
    // ... use client ...
    client.close(); // Connection pool discarded
}

// ✅ CORRECT: Create once in @FnConfiguration, reuse across invocations
// OCI SDK v3.x — client is thread-safe and connection-pooled
private ObjectStorageClient objectStorageClient;

@FnConfiguration
public void configure(RuntimeContext ctx) {
    var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
    this.objectStorageClient = ObjectStorageClient.builder().build(provider);
}

public String handleRequest(String input) {
    // Reuse warm client — connections are pooled
    return readObject("bucket", "key");
}
```

**Why it is prohibited**: Client creation involves Resource Principal token exchange, HTTP connection pool setup, and TLS initialization. In hot functions, creating per invocation adds 200-1000ms and prevents connection reuse.
**Actual impact**: 200-1000ms cold start overhead added to EVERY invocation. Connection pool never warms up.
**Source**: https://github.com/oracle-samples/oracle-functions-samples

---

**Anti-Pattern 2: Not Closing GetObject InputStream**

```java
// 🚫 WRONG: InputStream left open — memory leak in hot functions
// Causes connection pool exhaustion after ~50-200 invocations
public String readObject(String bucketName, String objectName) {
    GetObjectResponse response = objectStorageClient.getObject(
        GetObjectRequest.builder()
            .namespaceName(namespace)
            .bucketName(bucketName)
            .objectName(objectName)
            .build()
    );
    // response.getInputStream() is NEVER closed!
    return new String(response.getInputStream().readAllBytes());
}

// ✅ CORRECT: Always use try-with-resources — OCI SDK v3.x
public String readObject(String bucketName, String objectName) {
    GetObjectResponse response = objectStorageClient.getObject(
        GetObjectRequest.builder()
            .namespaceName(namespace)
            .bucketName(bucketName)
            .objectName(objectName)
            .build()
    );

    try (InputStream is = response.getInputStream()) {
        return new String(is.readAllBytes(), StandardCharsets.UTF_8);
    } catch (java.io.IOException e) {
        throw new RuntimeException("Failed to read: " + objectName, e);
    }
}
```

**Why it is prohibited**: In hot functions (JVM persists), unclosed streams keep HTTP connections open. After ~50-200 invocations, the pool exhausts and new requests fail with timeout.
**Actual impact**: Connection pool exhaustion → function appears to hang → 502 to caller.
**Source**: https://github.com/oracle/oci-java-sdk

---

**Anti-Pattern 3: Reading Entire Large File into Memory**

```java
// 🚫 WRONG: reading 500MB file into byte[] (function has 256MB memory)
// Causes OutOfMemoryError — no recovery possible
public byte[] readLargeFile(String bucketName, String objectName) {
    GetObjectResponse response = objectStorageClient.getObject(request);
    try (InputStream is = response.getInputStream()) {
        return is.readAllBytes(); // OutOfMemoryError!
    }
}

// ✅ CORRECT: Check size first OR process as stream — OCI SDK v3.x
public void processLargeFile(String bucketName, String objectName) {
    GetObjectResponse response = objectStorageClient.getObject(request);
    long size = response.getContentLength();

    // Guard: reject if too large for memory
    long maxAllowed = Runtime.getRuntime().maxMemory() / 2;
    if (size > maxAllowed) {
        throw new IllegalStateException(
            "File too large: " + size + " bytes, max: " + maxAllowed);
    }

    // OR: process as stream (preferred for large files)
    try (InputStream is = response.getInputStream();
         BufferedReader reader = new BufferedReader(new InputStreamReader(is))) {
        reader.lines().forEach(this::processLine);
    }
}
```

**Why it is prohibited**: OCI Functions have limited memory (128MB-2048MB). `readAllBytes()` allocates an array equal to file size — exceeding ~50% of allocated memory causes `OutOfMemoryError`.
**Actual impact**: `OutOfMemoryError` → function killed → 502 to caller → no error handling possible.
**Source**: OCI Functions memory limits documentation

---

**Anti-Pattern 4: ListObjects Without Pagination**

```java
// 🚫 WRONG: assuming single page has all objects
// Silently misses objects beyond the first 1000
ListObjectsResponse response = objectStorageClient.listObjects(
    ListObjectsRequest.builder()
        .namespaceName(namespace)
        .bucketName(bucketName)
        .build()
);
List<ObjectSummary> allObjects = response.getListObjects().getObjects();
// ONLY gets first 1000! Missing remaining objects silently!

// ✅ CORRECT: Paginate through all results — OCI SDK v3.x
List<ObjectSummary> allObjects = new ArrayList<>();
String nextStart = null;
do {
    ListObjectsRequest.Builder req = ListObjectsRequest.builder()
        .namespaceName(namespace)
        .bucketName(bucketName)
        .limit(1000);
    if (nextStart != null) req.start(nextStart);

    ListObjectsResponse resp = objectStorageClient.listObjects(req.build());
    allObjects.addAll(resp.getListObjects().getObjects());
    nextStart = resp.getListObjects().getNextStartWith();
} while (nextStart != null);
```

**Why it is prohibited**: `ListObjects` returns max 1000 objects per page. Without pagination, buckets with >1000 objects are silently truncated — logic appears correct but is incomplete.
**Actual impact**: Silent data loss — operations like "process all files" process only a fraction.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/ListObjects

---

**Anti-Pattern 5: Multipart Upload Without Abort on Failure**

```java
// 🚫 WRONG: manual multipart without cleanup — leaked uploads consume storage
CreateMultipartUploadResponse createResp = objectStorageClient
    .createMultipartUpload(req);
String uploadId = createResp.getMultipartUpload().getUploadId();
// ... upload parts ...
// If exception occurs here, uploadId is LEAKED!
// Incomplete multipart uploads persist indefinitely

// ✅ CORRECT: Use UploadManager with auto-abort — OCI SDK v3.x
UploadConfiguration config = UploadConfiguration.builder()
    .allowMultipartUploads(true)
    .disableAutoAbort(false)  // default: false — ensures cleanup on failure
    .build();

UploadManager uploadManager = new UploadManager(objectStorageClient, config);
// UploadManager handles abort automatically if upload fails
```

**Why it is prohibited**: Incomplete multipart uploads persist indefinitely, consuming storage (uploaded parts remain). They count against the limit of 10,000 concurrent multipart uploads per bucket.
**Actual impact**: Storage cost for orphaned parts. Eventually blocks new uploads when limit reached.
**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-objectstorage/bmc-objectstorage-extensions/src/main/java/com/oracle/bmc/objectstorage/transfer/UploadManager.java

---

**Anti-Pattern 6: PutObject Without contentLength**

```java
// 🚫 WRONG: contentLength is REQUIRED for PutObject API
// SDK fails with validation error or service rejects with 400
PutObjectRequest request = PutObjectRequest.builder()
    .namespaceName(namespace)
    .bucketName(bucketName)
    .objectName(objectName)
    // .contentLength(???)  ← MISSING!
    .putObjectBody(inputStream)
    .build();
objectStorageClient.putObject(request);

// ✅ CORRECT: Always provide content length — OCI SDK v3.x
byte[] data = content.getBytes(StandardCharsets.UTF_8);
PutObjectRequest request = PutObjectRequest.builder()
    .namespaceName(namespace)
    .bucketName(bucketName)
    .objectName(objectName)
    .contentLength((long) data.length)  // REQUIRED
    .putObjectBody(new ByteArrayInputStream(data))
    .build();
objectStorageClient.putObject(request);
```

**Why it is prohibited**: `Content-Length` is a required parameter in the OCI Object Storage PutObject API. For streams of unknown size, use `UploadManager` instead.
**Actual impact**: HTTP 400 Bad Request or SDK validation error. Object not written.
**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/PutObject

---

