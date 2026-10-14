# Evaluation Scenarios — integrating-oci-functions-objectstorage

## Scenario 1: Canonical — Stream and write a CSV from Object Storage

```json
{
  "skills": ["integrating-oci-functions-objectstorage"],
  "query": "My OCI Function receives an object name via API Gateway, reads the CSV from the 'input-data' bucket, transforms each row, and writes the result to 'output-data'. Show me the Java implementation.",
  "expected_behavior": [
    "ObjectStorageClient initialized in @FnConfiguration with ResourcePrincipalAuthenticationDetailsProvider",
    "Namespace retrieved via getNamespace() — not hardcoded",
    "GetObject wrapped in try-with-resources to close InputStream",
    "Writes via PutObject with explicit contentLength set",
    "Bucket names read from func.yaml config — not hardcoded",
    "ClientConfiguration sets explicit readTimeoutMillis below function timeout",
    "Does NOT call readAllBytes() on the input stream directly for large files"
  ]
}
```

## Scenario 2: Edge — Large file exceeds memory limit

```json
{
  "skills": ["integrating-oci-functions-objectstorage"],
  "query": "My function processes files that can be up to 500MB. It keeps throwing OutOfMemoryError. How do I fix it?",
  "expected_behavior": [
    "Identifies readAllBytes() as the root cause",
    "Recommends buffered streaming with BufferedReader / byte-by-byte processing",
    "Suggests UploadManager for writing large output (auto multipart)",
    "Notes function memory allocation (128-2048MB) constrains the safe in-memory size",
    "Does NOT suggest increasing memory as the sole solution for unbounded files",
    "Considers splitting large files into chunked invocations or using Connector Hub for async processing"
  ]
}
```

## Scenario 3: Edge — Service Gateway vs NAT Gateway for Object Storage access

```json
{
  "skills": ["integrating-oci-functions-objectstorage"],
  "query": "My function is inside a private VCN and cannot reach Object Storage. What routing do I need?",
  "expected_behavior": [
    "Recommends Service Gateway as the preferred path (no internet exposure, no cost per GB)",
    "Distinguishes Service Gateway (OCI service traffic) from NAT Gateway (internet egress)",
    "Notes that Service Gateway requires a route rule in the subnet route table pointing to 'OCI Services'",
    "Does NOT recommend NAT Gateway as equivalent for OCI-internal traffic",
    "References skill `provisioning-oci-networking` for VCN/route configuration details"
  ]
}
```

## Scenario 4: Misuse — Triggering infinite loop via same-bucket writes

```json
{
  "skills": ["integrating-oci-functions-objectstorage"],
  "query": "I have an OCI Events rule that triggers my function when objects are created in 'data-bucket'. My function processes the file and writes the result back to 'data-bucket'.",
  "expected_behavior": [
    "Identifies the infinite trigger loop: output write re-fires the event",
    "Recommends writing output to a separate destination bucket",
    "Alternatively suggests using an object name prefix/suffix convention to filter the trigger rule",
    "Flags this as an Emergency Stop pattern — halt and confirm before generating code",
    "Does NOT generate code that writes back to the same bucket without addressing the loop risk"
  ]
}
```

## Scenario 5: Misuse — Creating ObjectStorageClient per invocation

```json
{
  "skills": ["integrating-oci-functions-objectstorage"],
  "query": "Here is my function — the ObjectStorageClient is created inside the handleRequest method. Is there a problem?",
  "expected_behavior": [
    "Identifies per-invocation client creation as a Never Do pattern",
    "Explains: 200-1000ms overhead per call, connection pool never warms, resource leak",
    "Refactors client initialization into @FnConfiguration method",
    "Stores client as an instance field on the function class",
    "Does NOT leave client creation inside the handler method"
  ]
}
```
