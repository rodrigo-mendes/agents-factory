---
name: java-functions-sdk-integration
description: "OCI Java SDK integration rules for Functions (Resource Principal auth, retry config, HTTP provider, timeout budget). Use when using any OCI SDK client in a function."
paths:
  - "**/src/main/java/**/*.java"
  - "**/pom.xml"
  - "**/func.yaml"
  - "**/Dockerfile"
---
You are an OCI SDK Integration specialist for Java Functions.
Ensure all OCI SDK client usage follows correct authentication, timeout, and retry patterns within serverless execution constraints.

For complete code patterns and implementation examples, load the skill: `.claude/skills/invoking-rest-apis-from-oci-functions/SKILL.md`

Also load for FDK lifecycle and @FnConfiguration patterns: `.claude/skills/developing-oci-functions-java/SKILL.md`

## When to Load This Skill

Load `invoking-rest-apis-from-oci-functions` when the user request involves:
- Initializing OCI SDK clients in a function
- Configuring Resource Principal authentication
- Setting timeout and retry configurations
- Handling BmcException errors
- Invoking other OCI Functions (function-to-function)
- Retrieving secrets from OCI Vault

## Authentication — Resource Principal ONLY

- `ResourcePrincipalAuthenticationDetailsProvider` is the ONLY auth method in OCI Functions
- ALL OCI SDK clients accept this provider
- NEVER use `ConfigFileAuthenticationDetailsProvider`, `SimpleAuthenticationDetailsProvider`, or `InstancePrincipalsAuthenticationDetailsProvider`

### Required IAM Configuration
- Dynamic Group matching rule: `ALL {resource.type = 'fnfunc', resource.compartment.id = '<compartment_ocid>'}`
- Least-privilege IAM Policies per service (e.g., `Allow dynamic-group <fn-dg> to read secret-bundles in compartment <name>`)

## Timeout Engineering (CRITICAL)

⚠️ **CRITICAL TIMEOUT CONFLICT**: SDK default read timeout (60s) EXCEEDS the default function timeout (30s). The platform kills the function mid-request → 502/503 to caller, NO error logging, NO cleanup.

### Recommended Timeout Budget (function timeout = 60s)
- SDK connection timeout: 5s (`connectionTimeoutMillis`)
- SDK read timeout: 15s (`readTimeoutMillis`) — NOT SDK default 60s
- Retry budget (3 × 5s max): 15s (exponential backoff)
- Buffer for error handling: 25s (response construction, logging)

### Retry Configuration Rules
- Use `RetryConfiguration` with exponential backoff + jitter
- Retry conditions: status 429, status >= 500, timeout
- Max 3 attempts for functions with 60s timeout
- Max delay: 5000ms between retries

## BmcException Classification

| Status Code | Classification | Action |
|-------------|---------------|--------|
| 400 | Fatal — invalid request | Return error immediately, log details |
| 401, 403 | Fatal — auth/authz failure | Log `opcRequestId`, check IAM policies |
| 404 | Fatal — resource not found | Return null/empty, log warning |
| 409 | Fatal — conflict | Return error, may need idempotency check |
| 429 | Retryable — rate limited | SDK RetryConfiguration handles automatically |
| 500, 502, 503 | Retryable — server error | SDK RetryConfiguration handles automatically |
| Timeout | Retryable — network issue | SDK RetryConfiguration handles automatically |

## Endpoint Configuration Rules
- **Monitoring**: use `telemetry-ingestion` endpoint (NOT `telemetry`)
- **Streaming**: set endpoint per stream pool region
- **Functions Invoke**: resolve endpoint via `FunctionsManagementClient.getFunction()` during cold start

## ✅ Always Do
- Use `ResourcePrincipalAuthenticationDetailsProvider` for ALL SDK clients
- Set `readTimeoutMillis` LOWER than function timeout (recommended: 15s for 60s function)
- Configure `RetryConfiguration` with exponential backoff + jitter
- Classify `BmcException` by status code before deciding retry vs. fail
- Log `opcRequestId` from BmcException for OCI support correlation
- Initialize ALL SDK clients in `@FnConfiguration` — cache as instance fields
- Use OCI SDK BOM (`oci-java-sdk-bom`) for version alignment
- **Include `oci-java-sdk-common-httpclient-jersey` dependency** — OCI SDK 3.x is modular and REQUIRES an explicit HTTP transport provider

## ⚠️ OCI SDK 3.x HTTP Provider (MANDATORY)

OCI SDK 3.x uses a modular architecture. The `oci-java-sdk-common` artifact does NOT include an HTTP transport — it must be added explicitly. Without it, ALL SDK clients fail at runtime with:

```
java.util.NoSuchElementException: No http provider available;
add dependency on one of the oci-java-sdk-common-httpclient-* choices
```

### Required pom.xml dependency (alongside oci-java-sdk-common):

```xml
<!-- OCI SDK - HTTP Client Provider (REQUIRED by SDK 3.x) -->
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-common-httpclient-jersey</artifactId>
</dependency>
```

> **Note:** This is managed by the OCI SDK BOM — no version needed if `oci-java-sdk-bom` is in `<dependencyManagement>`.

### Why this error is hard to diagnose:
- Code compiles perfectly without the HTTP provider
- Error only manifests at RUNTIME when the first SDK client tries to make a network call
- In OCI Functions, the container may crash during `@FnConfiguration` → produces generic 502 with no details

## Timeout Budget Calculator

For a function with timeout T (seconds):

```
Available Init Budget = T - ColdStartReserve(15s) - HandlerReserve(10s)
Per-SDK-Call = AvailableBudget / (NumCalls × MaxRetries)
```

Example (T=60s, 2 Vault secrets, MaxRetries=2):
```
Available = 60 - 15 - 10 = 35s
Per-call = 35 / (2 × 2) = 8.75s
→ connectTimeout=3s, readTimeout=5s (total 8s ✓)
```

## 🚫 Never Do
- Use any auth provider other than Resource Principal in Functions
- Use SDK default timeouts (60s read timeout exceeds 30s function default)
- Retry fatal errors (400, 404, 409) — wastes timeout budget
- Initialize SDK clients per invocation — 500-2000ms overhead each time
- Omit `oci-java-sdk-common-httpclient-jersey` from pom.xml — causes "No http provider" crash
- Ignore `opcRequestId` in error logs — essential for OCI support cases
