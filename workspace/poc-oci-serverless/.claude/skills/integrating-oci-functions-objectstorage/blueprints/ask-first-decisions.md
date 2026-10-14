### ⚠️ Ask First

**Decision Point 1: Object Storage vs File Storage Service (FSS)**

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| Object Storage (SDK) | Scalability, simplicity, no VCN needed | POSIX semantics, random access | Most serverless use cases |
| File Storage (NFS) | POSIX compatibility, in-place edits | Requires VCN attachment, mount overhead | Legacy code needing filesystem |

**Agent Behavior**:
"Before implementing file operations, ask the user:
'Does the function need POSIX filesystem semantics (random read/write, directory traversal, in-place edits), or is object-level read/write sufficient? Object Storage is strongly preferred for serverless.'"

**Decision Factors**:
- Whether existing code relies on `java.io.File` / `java.nio.file.Path` operations
- Need for shared mutable state between function instances
- Whether function is already VCN-attached

**Source**: https://docs.oracle.com/en-us/iaas/Content/File/Concepts/filestorageoverview.htm

---

**Decision Point 2: Direct PutObject vs UploadManager**

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| Direct PutObject | Simplicity, predictable timing | No per-part retry, 50GiB limit | Files ≤20MB, known small payloads |
| UploadManager | Reliability, large files, auto-optimization | Complexity, thread pool usage | Files >20MB, variable sizes, production |

**Agent Behavior**:
"Before implementing write operations, ask the user:
'What is the maximum expected file size? If consistently <20MB, direct PutObject is simpler. If variable or potentially large, UploadManager is safer.'"

**Decision Factors**:
- Maximum expected file size
- Whether file sizes are predictable or variable
- Function memory allocation (determines multipart part size)

**Source**: https://github.com/oracle/oci-java-sdk/blob/master/bmc-objectstorage/bmc-objectstorage-extensions/src/main/java/com/oracle/bmc/objectstorage/transfer/UploadManager.java

---

**Decision Point 3: Storage Tier for Written Objects**

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| Standard | Access latency, immediate reads | Cost (highest) | Frequently accessed data, active processing |
| InfrequentAccess | Cost (46% less) | Retrieval charge, 31-day min retention | Monthly reports, backups |
| Archive | Cost (90% less) | Hours to restore, 90-day min retention | Compliance archives, audit logs |

**Agent Behavior**:
"Before writing objects, ask the user:
'How frequently will these objects be read after creation? Standard for active use, InfrequentAccess for monthly, Archive for rarely/compliance.'"

**Decision Factors**:
- Read frequency after creation
- Retention requirements
- Cost sensitivity
- Whether immediate access is needed after write

**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/20160918/Object/PutObject

---

**Decision Point 4: Object Naming Strategy**

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| Hierarchical prefixes (`data/2024/01/file.json`) | Human readability, logical grouping | Potential hotspots under high write | Organized data, <100 writes/s |
| UUID-based (`a3f2c91d-4e2b-...`) | Even distribution, no conflicts | Readability | High write throughput, temp files |
| Hash-prefixed (`ab/cd/filename`) | Balanced distribution | Complexity | Very high throughput (>1000 req/s) |

**Agent Behavior**:
"Before defining object naming, ask the user:
'What is the expected write throughput? For <100 writes/s, hierarchical prefixes are readable and fine. For >1000 writes/s, consider hash-prefix or UUID to avoid hotspots.'"

**Decision Factors**:
- Expected write throughput (requests/second)
- Need for human-readable object names in console/logs
- Object name max length is 1024 characters

**Source**: https://docs.oracle.com/iaas/Content/Object/Tasks/managingobjects.htm#namerequirements

---

