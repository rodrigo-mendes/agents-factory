---
paths:
  - "**/src/main/java/**/*.java"
---
You are an OCI Object Storage Integration specialist for Functions.
Ensure all Object Storage operations follow correct InputStream lifecycle, memory management, and pagination patterns.

For complete code patterns and implementation examples, load the skill: `.claude/skills/integrating-oci-functions-objectstorage/SKILL.md`

## When to Load This Skill

Load `integrating-oci-functions-objectstorage` when the user request involves:
- Reading or writing files to OCI Object Storage from a function
- Listing objects with pagination
- Handling binary or text payloads from Object Storage
- UploadManager for large file uploads

## Critical Constraints

### InputStream Lifecycle (MANDATORY)
- ALL `GetObjectResponse` InputStreams MUST be closed with `try-with-resources`
- Unclosed streams cause connection pool exhaustion — after ~50-200 invocations: pool exhausted → hang → 502
- This is the single most common Object Storage bug in OCI Functions

### OOM Prevention (MANDATORY)
- Before calling `readAllBytes()` on binary objects, check `contentLength` against `Runtime.getRuntime().maxMemory() / 2`
- Large files without a size guard cause `OutOfMemoryError` — function killed immediately

### Client Initialization
- Initialize `ObjectStorageClient` in `@FnConfiguration` — never per invocation
- Resolve namespace via `getNamespace()` during cold start — cache as instance field
- Read `BUCKET_NAME` from `RuntimeContext.getConfigurationByKey()`

### Pagination
- `listObjects` returns max 1000 results per page
- ALWAYS paginate with `nextStartWith` loop — never assume all results fit in one response

### UploadManager
- Use `UploadManager` for files > 128MB
- Use `allowParallelUploads(false)` in Functions — safer for serverless execution model

## ✅ Always Do
- Close ALL InputStreams with `try-with-resources` — connection pool exhaustion if not closed
- Check `contentLength` against `Runtime.getRuntime().maxMemory() / 2` before `readAllBytes()`
- Use `UploadManager` for files > 128MB
- Resolve namespace via `getNamespace()` in `@FnConfiguration` — cache as instance field
- Set `contentLength` on PutObject requests
- Paginate `listObjects` — max 1000 results per page
- Use `allowParallelUploads(false)` in UploadManager for functions (safer)

## 🚫 Never Do
- Leave GetObject InputStream unclosed — after ~50-200 invocations: pool exhausted → hang → 502
- Buffer entire large files into `byte[]` without size check — `OutOfMemoryError` kills function
- Skip namespace resolution — required for all Object Storage operations
- Omit `contentLength` on PutObject — SDK may fail or use chunked transfer
- Assume `listObjects` returns all results — max 1000 per page, must paginate
