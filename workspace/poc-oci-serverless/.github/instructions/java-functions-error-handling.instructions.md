---
name: java-functions-error-handling
description: OCI Functions error handling and resilience for SDK v3.86+ — BmcException classification, timeout budget management, structured error responses, fallback patterns
applyTo: "**/src/main/java/**/*.java"
---

You are an OCI Functions Error Handling and Resilience specialist.
Ensure all functions handle errors correctly with proper classification, retry logic, and structured responses.

For complete code patterns and implementation examples, load the skill: `.github/skills/invoking-rest-apis-from-oci-functions/SKILL.md`

Also load for SDK client initialization and retry patterns: `.github/skills/developing-oci-functions-java/SKILL.md`

## When to Load This Skill

Load `invoking-rest-apis-from-oci-functions` when the user request involves:
- Handling `BmcException` from OCI SDK calls
- Configuring timeout budgets for downstream calls
- Building structured error responses for API Gateway functions
- Implementing fallback or degraded response patterns

## Exception Classification Strategy

| Exception Type | Classification | API Gateway Response | Action |
|---------------|---------------|---------------------|--------|
| `BmcException` (400) | Fatal | 400 Bad Request | Return error immediately, log details |
| `BmcException` (401/403) | Fatal | 403 Forbidden | Log `opcRequestId`, check IAM policies |
| `BmcException` (404) | Fatal | 404 Not Found | Return null/empty, log warning |
| `BmcException` (409) | Fatal | 409 Conflict | Return error, check idempotency |
| `BmcException` (429) | Retryable | 503 Service Unavailable | SDK RetryConfiguration handles |
| `BmcException` (500/502/503) | Retryable | 503 Service Unavailable | SDK RetryConfiguration handles |
| `BmcException` (timeout) | Retryable | 504 Gateway Timeout | Log, retry or return degraded |
| `HttpTimeoutException` | Retryable | 504 Gateway Timeout | Log, return degraded response |
| `JsonProcessingException` | Fatal | 400 Bad Request | Return "Invalid request body" |
| `IllegalArgumentException` | Fatal | 400 Bad Request | Return input validation error |
| `RuntimeException` (uncaught) | Fatal | 502 Bad Gateway | Function killed, 502 to caller |

## Timeout Budget Management

⚠️ **CRITICAL TIMEOUT CONFLICT**: SDK default read timeout (60s) EXCEEDS the default function timeout (30s). If not configured, the platform kills the function mid-request → 502/503 to caller, NO error logging, NO cleanup, NO graceful degradation.

**Rule**: Sum of all downstream timeouts MUST be ≤ function timeout.

**Recommended budget (function timeout = 60s)**:
- OCI SDK call #1: 15s max (`readTimeoutMillis`)
- OCI SDK call #2: 15s max (`readTimeoutMillis`)
- External API call: 10s max (`HttpRequest.timeout`)
- Buffer: 20s (error handling, response construction, logging)

### Timeout Configuration Checklist
- `func.yaml` timeout: 60s (accommodate all downstream calls + retries)
- `ClientConfiguration.readTimeoutMillis`: 15000 (15s, NOT SDK default 60s)
- `ClientConfiguration.connectionTimeoutMillis`: 5000 (5s)
- `HttpRequest.timeout()`: 10s for external APIs
- `RetryConfiguration` max delay: 5000ms with 3 attempts max

## Structured Error Response Rules

- API Gateway functions (non-void handlers): return structured error response with HTTP status code
- Event-driven functions (void handlers — ConnectorHubFunction, NotificationFunction): throw `RuntimeException` → 502 → SCH/ONS retry
- Uncaught exception in ANY handler: platform returns 502 to caller — no graceful degradation
- Use a centralized `errorResponse(int status, String code, String message)` helper method

## Error Detail Preservation (CRITICAL)

⚠️ **NEVER strip, summarize, or rephrase exception messages in error responses.** The original `e.getMessage()` contains diagnostic gold: HTTP status codes, URLs, timing information, and upstream error details that are essential for debugging deployed functions.

### Rule: Always Include Full Exception Context

```java
// ✅ CORRECT — preserves full diagnostic context
} catch (IOException e) {
    String detail = e.getClass().getName() + ": " + e.getMessage();
    return error(503, Response.error("Service Unavailable", detail));
}
```

```java
// ❌ WRONG — strips the status code, URL, and upstream error
} catch (IOException e) {
    if (e.getMessage().contains("OAuth2")) {
        return error(503, Response.error("Service Unavailable", "OAuth2 authentication failed"));
        // Lost: "with status: 401", "for URL: https://idcs.../token", timing info
    }
}
```

### Why This Matters in Serverless

- OCI Functions have **no SSH access** — you cannot attach a debugger
- OCI Logging may not be configured or accessible — the response IS your only diagnostic channel
- The API response `detalhe` field is often the **only evidence** of what went wrong
- Stripping "with status: 401" from an OAuth error makes it impossible to distinguish:
  - Credentials are null (Vault failed)
  - Credentials are wrong (IDCS rejected)
  - Token URL is wrong (400 vs 401)
  - Network timeout (no status at all)

### Exception Message Content to ALWAYS Preserve

| Exception Source | Message Contains | Diagnostic Value |
|-----------------|-----------------|------------------|
| HttpClient IOException | HTTP status code + URL | Identifies which call failed and why |
| BmcException | opcRequestId + status + service | Enables OCI support correlation |
| OAuth2 failure | Token URL + status + error description | Distinguishes credential vs config vs network |
| Connection timeout | Target host + timeout value | Identifies network vs misconfiguration |
| JAXB/JSON parse | Field name + position + expected type | Pinpoints data format issue |

## Fallback Pattern Rules

- **Degraded response**: when a downstream service is unavailable (503), return cached or partial data instead of failing
- **Error signaling**: void handlers signal errors via `RuntimeException` (no return value to send error status)

## Retry Configuration Rules
- Use SDK `RetryConfiguration` for OCI service calls — handles 429, 5xx, timeouts automatically
- For external HTTP calls: implement manual retry with exponential backoff
- NEVER use `Thread.sleep()` for delays — wastes execution time and billing
- Total retry budget MUST fit within function timeout

## ✅ Always Do
- Classify `BmcException` by status code before deciding retry vs. fail
- Log `opcRequestId` from every BmcException — essential for OCI support
- Reserve buffer time in timeout budget for error handling and response
- Return structured error responses from API Gateway functions
- Use SDK `RetryConfiguration` for OCI service calls
- Handle `HttpTimeoutException` explicitly for external API calls
- Catch ALL exceptions in API Gateway handlers — prevent 502 from uncaught exceptions

## 🚫 Never Do
- Retry fatal errors (400, 404, 409) — wastes timeout budget, same result every time
- Ignore `BmcException.isTimeout()` — different handling than HTTP status errors
- Set SDK timeout equal to or higher than function timeout
- Use `Thread.sleep()` for retry delays in functions
- Expose internal error details or stack traces in API responses
- Let exceptions propagate uncaught from API Gateway functions — causes 502
- Ignore `opcRequestId` in error logging — impossible to troubleshoot without it
