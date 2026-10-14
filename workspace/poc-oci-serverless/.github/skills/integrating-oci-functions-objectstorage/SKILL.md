---
name: integrating-oci-functions-objectstorage
description: Reads, writes, and manages files in OCI Object Storage from OCI Functions with Java FDK and OCI SDK v3.x+. Use when integrating Functions with Object Storage.
---

## Version Context

**Technology**: OCI Java SDK — Object Storage Client
**Target Version**: OCI SDK v3.36+ (project minimum) / v3.86.1 (latest)
**Runtime**: Java 17 (Docker: `fnproject/fn-java-fdk:jre17-latest`)
**Release Date**: 2024-ongoing (SDK 3.86.1 released 2026-05-06)
**Support Status**: Active
**License**: UPL 1.0 / Apache 2.0 (dual license)

**Key Artifacts**:
- `oci-java-sdk-objectstorage` — Basic CRUD (PutObject, GetObject, DeleteObject, ListObjects)
- `oci-java-sdk-objectstorage-extensions` — UploadManager, DownloadManager (auto multipart, retry)
- `oci-java-sdk-bom` — BOM for version management

**Breaking Changes**: None in SDK v3.x line. UploadManager defaults changed between SDK v3.36 and v3.78 (multipart threshold from 128MB remains stable).

**Deprecations**: None active. `oci-java-sdk-objectstorage-generated` is low-level and rarely needed directly.

⚠️ **Version Lock**: This skill targets OCI SDK v3.x with Java 17. Do NOT mix patterns from OCI SDK v2.x. Resource Principal is the ONLY authentication method in OCI Functions — never use API key or instance principal.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](#integration-patterns)** — Cross-service integration examples
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Initialize ObjectStorageClient in `@FnConfiguration`** — Create once during cold start with Resource Principal. Reuse across invocations for connection pooling
- **Close GetObject InputStream with try-with-resources** — Unclosed streams cause connection pool exhaustion after ~50-200 invocations
- **Use UploadManager for PutObject** — Handles multipart uploads, retries, and content-length automatically
- **Stream large files with buffered processing** — Never `readAllBytes()` — OCI Functions have 128MB-2048MB memory limits
- **Set explicit timeouts on ObjectStorageClient** — Default SDK timeout (infinite) causes Functions to hit 300s timeout on hung connections
- **Use namespace from `getNamespace()` API** — Namespace is NOT the tenancy name; it's an opaque identifier

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Object Storage vs File Storage Service (FSS)** — Object Storage for files >1MB or accessed via REST; FSS for NFS-mounted shared access
- **Direct PutObject vs UploadManager** — Direct for <20MB known-size; UploadManager for everything else (auto multipart)

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Creating ObjectStorageClient per invocation** — 200-1000ms overhead on EVERY call, connection pool never warms
- **Not closing GetObject InputStream** — Connection pool exhaustion → function hangs → 502 errors
- **Reading entire large file into memory** — `readAllBytes()` causes `OutOfMemoryError` on files >50% of allocated memory
- **Hardcoding namespace** — Namespace changes across tenancies; must use `getNamespace()` API
- **Using ObjectStorageClient without timeouts** — Infinite default timeout → Functions hit 300s limit on hung connections
- **Catching generic Exception for OCI SDK errors** — Hides `BmcException` status codes needed for retry/error handling decisions
## Integration Patterns

### OCI Functions ↔ Object Storage (Maven Dependencies)

**Artifacts**: `oci-java-sdk-objectstorage`, `oci-java-sdk-objectstorage-extensions`
**Compatibility**: OCI SDK v3.36+, Java 17, fn-java-fdk

**Installation**:
```xml
<!-- pom.xml — OCI SDK v3.x BOM + Object Storage -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.oracle.oci.sdk</groupId>
            <artifactId>oci-java-sdk-bom</artifactId>
            <version>${oci.sdk.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <!-- Object Storage Client (basic CRUD) -->
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-objectstorage</artifactId>
    </dependency>

    <!-- Object Storage Extensions (UploadManager, DownloadManager) -->
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-objectstorage-extensions</artifactId>
    </dependency>
</dependencies>
```

**Compatibility Matrix**:

| Module | Artifact ID | Operations | Notes |
|--------|-------------|-----------|-------|
| Object Storage | oci-java-sdk-objectstorage | PutObject, GetObject, DeleteObject, ListObjects | Basic CRUD |
| Extensions | oci-java-sdk-objectstorage-extensions | UploadManager, DownloadManager | Auto multipart, retry |

---

### OCI Functions ↔ IAM (Required Policies)

**IAM Policies** (Terraform or OCI Console):
```
# Read-only access
allow dynamic-group <dg-name> to read objects in compartment <compartment>

# Read + Write access
allow dynamic-group <dg-name> to manage objects in compartment <compartment>

# Scoped to specific bucket (more restrictive, recommended)
allow dynamic-group <dg-name> to manage objects in compartment <compartment>
    where target.bucket.name = '<bucket-name>'
```

**Dynamic Group matching rule** (for the function):
```
ALL {resource.type = 'fnfunc', resource.compartment.id = '<compartment-ocid>'}
```

---

### OCI Functions ↔ Object Storage Events

For event-driven file processing (auto-trigger on object create/update), use OCI Events + OCI Functions trigger. The event payload contains bucket/object name. See the fn-events research for `ConnectorHubFunction` patterns.

**Function Configuration** (`func.yaml` or application config):
```yaml
config:
  BUCKET_NAME: "my-data-bucket"
  SOURCE_BUCKET: "input-bucket"
  DEST_BUCKET: "output-bucket"
  # Namespace is auto-detected via getNamespace() — no config needed
```

---

## Verification Loop

The agent MUST execute after each code generation:

### 1. Build
```bash
mvn clean package -DskipTests
# Exit code: 0 (success) | 1 (compilation/test failure)
```
**Expected output**: `BUILD SUCCESS`
**Exit code**: 0

### 2. Unit Tests
```bash
mvn clean test
# Exit code: 0 (all tests passed) | 1 (test failure)
```
**Expected output**: `Tests run: N, Failures: 0, Errors: 0`
**Exit code**: 0

### 3. Deploy
```bash
fn -v deploy --app <app-name>
```
**Expected output**: `Updating function...` or `Creating function...`
**Exit code**: 0

### 4. Integration Test (Invoke)
```bash
echo '{"objectName":"test/input.csv","format":"json","deleteSource":false}' | fn invoke <app> <fn>
# Exit code: 0 (success) | 1 (invocation error)
```
**Expected output**: `{"status":"SUCCESS","outputPath":"processed/test/input.json",...}`

### 5. Verify Object Written
```bash
oci os object head --namespace <ns> --bucket-name <dest-bucket> --name "processed/test/input.json"
# Exit code: 0 (success) | 1 (auth/network error)
```
**Expected output**: Response containing `content-length`, `content-type`, `etag`

### 6. List Processed Objects
```bash
oci os object list --namespace <ns> --bucket-name <bucket> --prefix "processed/"
# Exit code: 0 (success) | 1 (auth/network error)
```
**Expected output**: List of processed objects

**Troubleshooting**:
- `BmcException 404` → Object not found — verify bucket name and object path
- `BmcException 401/403` → IAM policy not configured — verify dynamic group + policy
- `OutOfMemoryError` → File too large — increase function memory or use streaming
- `Connection timeout on GetObject` → Unclosed InputStreams — check try-with-resources usage
- `HTTP 400 on PutObject` → Missing contentLength — always set `.contentLength()`

---

## Quick Reference

**Most used operations**:
```java
// Read text object
try (InputStream is = client.getObject(req).getInputStream()) {
    return new String(is.readAllBytes(), StandardCharsets.UTF_8);
}

// Write text object
byte[] bytes = content.getBytes(StandardCharsets.UTF_8);
client.putObject(PutObjectRequest.builder()
    .namespaceName(ns).bucketName(bucket).objectName(name)
    .contentLength((long) bytes.length)
    .putObjectBody(new ByteArrayInputStream(bytes)).build());

// Delete object
client.deleteObject(DeleteObjectRequest.builder()
    .namespaceName(ns).bucketName(bucket).objectName(name).build());

// List with pagination
String next = null;
do {
    var req = ListObjectsRequest.builder()
        .namespaceName(ns).bucketName(bucket).prefix(prefix).limit(1000);
    if (next != null) req.start(next);
    var resp = client.listObjects(req.build());
    process(resp.getListObjects().getObjects());
    next = resp.getListObjects().getNextStartWith();
} while (next != null);
```

**Key limits**:

| Aspect | Limit |
|--------|-------|
| Max object size (PutObject) | 50 GiB |
| Max object size (multipart) | 10 TiB |
| Max parts per upload | 10,000 |
| ListObjects per page | 1,000 |
| Object name max length | 1,024 chars |
| Function memory | 128-2048 MB |
| Function timeout | 30-300s |

**Performance baseline**:

| Operation | Latency |
|-----------|---------|
| GetObject (small, <1MB) | ~20-50ms |
| GetObject (large, 100MB) | ~1-5s |
| PutObject (small, <1MB) | ~30-80ms |
| ListObjects (1000 objects) | ~50-100ms |
| Cold start (client init) | ~500-1500ms |

---

## Security Hardening

- [ ] Resource Principal only (never API keys in functions)
- [ ] IAM policy scoped to specific bucket(s), not compartment-wide `manage`
- [ ] IAM policy uses minimum verbs (`read` not `manage` for read-only functions)
- [ ] Dynamic Group matching rule specific to function/application
- [ ] Bucket is private (no pre-authenticated requests without expiry)
- [ ] Object names sanitized (no path traversal, no user-controlled full paths)
- [ ] Content-Type validated before processing (prevent XXE, etc.)
- [ ] Object size checked before reading into memory
- [ ] Sensitive data encrypted with customer-managed keys (SSE-C or KMS)
- [ ] Bucket versioning enabled for critical data
- [ ] Lifecycle rules configured to auto-delete temporary objects
- [ ] No sensitive data in object names (names visible in logs/metrics)

---

## Testing Patterns

### Interface Abstraction for Unit Tests

```java
// Interface for testable file operations — OCI SDK v3.x
public interface FileStore {
    String read(String bucket, String objectName);
    String write(String bucket, String objectName, String content);
    void delete(String bucket, String objectName);
    java.util.List<String> list(String bucket, String prefix);
}

// In-memory mock for unit tests (no OCI SDK dependency)
public class InMemoryFileStore implements FileStore {
    private final java.util.Map<String, String> store = new java.util.HashMap<>();

    private String key(String bucket, String name) { return bucket + "/" + name; }

    @Override
    public String read(String bucket, String objectName) {
        String content = store.get(key(bucket, objectName));
        if (content == null) throw new RuntimeException("Not found: " + objectName);
        return content;
    }

    @Override
    public String write(String bucket, String objectName, String content) {
        store.put(key(bucket, objectName), content);
        return "mock-etag-" + objectName.hashCode();
    }

    @Override
    public void delete(String bucket, String objectName) {
        store.remove(key(bucket, objectName));
    }

    @Override
    public java.util.List<String> list(String bucket, String prefix) {
        return store.keySet().stream()
            .filter(k -> k.startsWith(bucket + "/" + prefix))
            .map(k -> k.substring(bucket.length() + 1))
            .collect(java.util.stream.Collectors.toList());
    }
}
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Initializing `ObjectStorageClient` in `@FnConfiguration` with Resource Principal
- Using `GetObject` with try-with-resources for InputStream
- Using `PutObject` with `contentLength` and `ByteArrayInputStream`
- Using `ListObjects` with pagination (`nextStartWith`)
- Adding `oci-java-sdk-objectstorage` and `oci-java-sdk-objectstorage-extensions` deps
- Getting namespace via `getNamespace()`
- Using `UploadManager` for files > 20MB

### Low Confidence (Must ask human)
- Bucket name(s) — environment-specific
- Source/destination bucket separation strategy
- Object naming convention (prefix scheme)
- Whether to delete source after processing
- Function memory allocation (determines max file size for in-memory)
- VCN attachment requirement (only if FSS needed)
- Encryption requirements (default SSE vs customer-managed KMS)

### Emergency Stop (Halt and confirm with user)
- Function writing to same bucket that triggers it (infinite loop risk)
- Object names constructed from user input without sanitization (path traversal)
- Reading objects without size check (OOM potential)
- API keys or credentials being written to Object Storage
- Deleting objects in production bucket without confirmation
- Disabling auto-abort on UploadManager (orphaned multipart parts accumulate)

---

## External Resources

### Official Documentation
- [Object Storage API — PutObject](https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/PutObject)
- [Object Storage API — GetObject](https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/GetObject)
- [Object Storage API — ListObjects](https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/ListObjects)
- [Object Storage API — DeleteObject](https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/DeleteObject)
- [Multipart Upload Guide](https://docs.oracle.com/iaas/Content/Object/Tasks/usingmultipartuploads.htm)
- [File Storage Service Overview](https://docs.oracle.com/en-us/iaas/Content/File/Concepts/filestorageoverview.htm)

### SDK & Samples
- [OCI Java SDK Repository](https://github.com/oracle/oci-java-sdk) (v3.86.1)
- [Oracle Functions Samples](https://github.com/oracle-samples/oracle-functions-samples)
- [Put Object Sample (Java)](https://github.com/oracle-samples/oracle-functions-samples/blob/master/samples/oci-objectstorage-put-object-java)
- [Get Object Sample (Java)](https://github.com/oracle-samples/oracle-functions-samples/tree/master/samples/oci-objectstorage-get-object-java)
- [List Objects Sample (Java)](https://github.com/oracle-samples/oracle-functions-samples/tree/master/samples/oci-objectstorage-list-objects-java)

### Transfer Utilities (Source)
- [UploadManager.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-objectstorage/bmc-objectstorage-extensions/src/main/java/com/oracle/bmc/objectstorage/transfer/UploadManager.java)
- [UploadConfiguration.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-objectstorage/bmc-objectstorage-extensions/src/main/java/com/oracle/bmc/objectstorage/transfer/UploadConfiguration.java)
- [DownloadManager.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-objectstorage/bmc-objectstorage-extensions/src/main/java/com/oracle/bmc/objectstorage/transfer/DownloadManager.java)

