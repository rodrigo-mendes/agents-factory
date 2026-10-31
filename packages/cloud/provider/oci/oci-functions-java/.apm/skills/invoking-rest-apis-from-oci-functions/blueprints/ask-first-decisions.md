### ⚠️ Ask First

**Decision Point**: OCI SDK Client vs java.net.http.HttpClient vs Raw HTTP with RequestSigner

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| OCI SDK Typed Client | Type safety, auth, retry, signing | Flexibility | Calling any OCI service with SDK module |
| java.net.http.HttpClient | Zero deps, HTTP/2, async | No OCI signing | External third-party REST APIs |
| OCI SDK RequestSigner | OCI signing for raw HTTP | Convenience | OCI API endpoint without dedicated SDK client |
| Jersey/Apache HttpClient | Features, interceptors | Image size (+20-50MB) | Complex HTTP requirements (rare) |

**Agent Behavior**:
"Before implementing, ask the user:
'Is the target an OCI service (use SDK Typed Client), an external third-party REST API (use java.net.http.HttpClient), or an OCI endpoint without a dedicated SDK client (use RequestSigner)?'"

**Decision Factors**:
- Whether target API is an OCI service or external
- Whether an OCI SDK module exists for the target service
- Container image size constraints
- Need for HTTP/2 or async operations

**Source**: [OCI SDK HTTP Client Choices](https://github.com/oracle/oci-java-sdk/tree/master/bmc-common-httpclient-choices)

---

**Decision Point**: Sync vs Detached function-to-function invocation

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| `fn-invoke-type: sync` (default) | Response data, error visibility | Latency (blocked waiting) | Caller needs the response from target function |
| `fn-invoke-type: detached` | Latency, throughput | Response, error handling | Async processing, fan-out, fire-and-forget |

**Agent Behavior**:
"Before implementing function-to-function invocation, ask:
'Does the calling function need the result from the invoked function, or is this a fire-and-forget pattern?'"

**Decision Factors**:
- Whether response data is needed by the caller
- Acceptable latency budget
- Error handling requirements (detached gives no error feedback)
- Fan-out patterns (detached preferred for parallelism)

**Source**: [InvokeFunction API](https://docs.oracle.com/en-us/iaas/api/#/en/functions/20181201/Function/InvokeFunction)

---

**Decision Point**: Retry strategy for functions with limited time budget

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| SDK Default (8 attempts, 30s max delay) | Resilience against transient failures | May exceed function timeout | Long-running functions (120-300s) |
| Function-scoped (2-3 attempts, proportional delay) | Respects function budget | Fewer retry attempts | Standard functions (30-60s timeout) |
| No retry (fast fail) | Latency, cost | Resilience | Idempotent callers, short timeouts (<15s) |

**Agent Behavior**:
"Before configuring retry, ask:
'What is the function timeout? Retry budget should be less than 50% of total timeout.'"

**Decision Factors**:
- Function timeout value (30s default, max 300s)
- Number of sequential outbound calls in the handler
- Whether the caller (API Gateway, scheduler) already implements retry
- Cost sensitivity (retries consume additional compute)

**Source**: [OCI SDK RetryConfiguration](https://github.com/oracle/oci-java-sdk/blob/master/bmc-common/src/main/java/com/oracle/bmc/retrier/RetryConfiguration.java)

---

**Decision Point**: API credential storage for external REST calls

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| OCI Vault Secrets | Security, rotation, audit trail | Latency (+1 API call on cold start) | API keys, tokens, passwords |
| Function Configuration | Simplicity, zero latency | No rotation, visible in OCI Console | Non-sensitive config: base URLs, feature flags |
| Resource Principal + API GW auth | No secrets at all | Setup complexity | OCI-to-OCI with identity propagation |

**Agent Behavior**:
"Before storing API credentials, ask:
'Is this credential sensitive (API key, password, token)? If yes, use OCI Vault. If it's a non-secret configuration value (base URL, feature flag), Function Configuration is acceptable.'"

**Decision Factors**:
- Sensitivity of the credential
- Compliance requirements (GDPR, LGPD, HIPAA)
- Rotation frequency needed
- Cold start latency tolerance

**Source**: [Oracle Functions Samples](https://github.com/oracle-samples/oracle-functions-samples)

---

