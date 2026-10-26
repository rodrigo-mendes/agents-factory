# Diagnostic Decision Trees — debugging-deployed-functions

## Decision Tree by HTTP Status

### 502 — Container Crash

```
502 (no response body from function)
├── Dockerfile has CMD?
│   ├── NO → Add CMD ["class::handler"] → REBUILD
│   └── YES → continue
├── ClassNotFoundException in OCI logs?
│   ├── YES → Fix class path in CMD or dependency
│   └── NO → continue
├── NoSuchElementException: "No http provider"?
│   ├── YES → Add oci-java-sdk-common-httpclient-jersey to pom.xml → REBUILD
│   └── NO → continue
├── @FnConfiguration exception (uncaught)?
│   ├── YES → Wrap configure() body in try-catch (initError pattern)
│   └── NO → continue
└── OutOfMemoryError?
    ├── YES → Increase function memory_in_mbs
    └── NO → Enable OCI Logging, check container logs
```

### 503 — Dependency Unavailable

```
503 + response body
├── "OAuth2 token request failed with status: 401"
│   ├── Credentials are null? (Vault read failed)
│   │   ├── Secret OCID in app config? → Check via OCI CLI
│   │   ├── Secret exists and ACTIVE? → Check IAM policies
│   │   └── "No http provider"? → Missing httpclient-jersey
│   └── Credentials are wrong? (Vault has bad value)
│       └── Verify secret content: oci secrets secret-bundle get
├── "OAuth2 token request failed with status: 400"
│   └── Check scope, grant_type, token URL in app config
├── "connection refused" or "connect timed out"
│   ├── Target is OCI service? → Check Service Gateway + route table
│   ├── Target is internet? → Check NAT Gateway
│   └── Target is private network? → Check NSG/Security List egress rules
└── "DNS resolution failed"
    └── Check VCN DNS resolver configuration
```

### 504 — Timeout Exceeded

```
504 (or function timeout with no response)
├── Calculate timeout budget:
│   Available = FunctionTimeout - ColdStart(15s) - HandlerReserve(10s)
│   PerCall = Available / (NumSDKCalls × MaxRetries)
├── SDK timeouts exceed budget?
│   ├── YES → Reduce MaxAttempts, connectTimeout, readTimeout
│   └── NO → continue
├── Downstream API slow?
│   ├── YES → Increase function timeout_in_seconds
│   └── NO → continue
└── Too many retries on failure?
    └── Reduce MaxAttemptsTerminationStrategy value
```

### 500 — Application Error

```
500 + "Function init failed" + detail
├── Read "detalhe" field in response — it contains the exact exception
├── "Vault secret retrieval failed: ..."
│   └── Fix Vault access (IAM, network, secret OCID)
├── "STORE_SOURCE_BASE_URL is required"
│   └── Missing config in Terraform oci_functions_application.config
├── "No http provider available"
│   └── Add oci-java-sdk-common-httpclient-jersey to pom.xml
└── Other exception
    └── Fix based on exception class and message

500 + "Internal server error" + detail
├── Read "detalhe" field — shows exception class + message
├── NullPointerException
│   └── Check if initialization succeeded (credentials, clients)
├── IOException
│   └── Network issue to downstream service
└── Other
    └── Debug code logic based on exception context
```

---

## Common Root Causes Database

| Error Message | Root Cause | Fix |
|---------------|-----------|-----|
| `NoSuchElementException: No http provider available` | Missing `oci-java-sdk-common-httpclient-jersey` in pom.xml | Add dependency, rebuild |
| 502 with empty response body | Missing `CMD` in Dockerfile | Add `CMD ["class::handler"]` |
| `OAuth2 token request failed with status: 401` | Client credentials are null or invalid | Check Vault secrets, verify base64 decode |
| `OAuth2 token request failed with status: 400` | Wrong scope or token URL | Check STORE_OAUTH_SCOPE, STORE_OAUTH_TOKEN_URL in app config |
| `STORE_SOURCE_BASE_URL is required` | Missing required config in application | Check Terraform `oci_functions_application.config` map |
| `Vault secret retrieval failed: BmcException 404` | Secret OCID incorrect or in wrong compartment | Verify secret OCID, check compartment |
| `Vault secret retrieval failed: BmcException 401` | Dynamic group doesn't include function | Check dynamic group matching rule |
| FDK calls configure() twice | Method named `config()` instead of `configure()` | Rename to `configure()` with `@Override` |
| Function timeout (no response at all) | SDK retry budget exceeds function timeout | Reduce MaxAttempts, connectTimeout, readTimeout |
| `connect timed out` to OCI service | Missing Service Gateway in VCN | Add `oci_core_service_gateway` with route |
| `connect timed out` to internet | Missing NAT Gateway in VCN | Add `oci_core_nat_gateway` with route |
| `ClassNotFoundException` | Dependency not in classpath | Check pom.xml scope (don't use `<scope>provided</scope>` for runtime deps) |
| Container OOM killed | Function memory too low for dependencies | Increase `memory_in_mbs` (256→512 for SDK-heavy functions) |

---

## Timeout Budget Calculator

```
┌─────────────────────────────────────────────────────────┐
│ Function Timeout (T)                                     │
├─────────────────┬───────────────────┬───────────────────┤
│ Cold Start (15s)│ Init Budget       │ Handler Budget     │
│                 │ (configure())     │ (handler())        │
├─────────────────┼───────────────────┼───────────────────┤
│ Fixed overhead  │ SDK calls in init │ Business logic     │
│ JVM + FDK       │ Vault, config     │ HTTP calls, I/O   │
└─────────────────┴───────────────────┴───────────────────┘

Init Budget = T - 15s (cold start) - HandlerReserve
HandlerReserve = max expected handler time (e.g., 30s for REST proxy)

Example: T=60s
  Init Budget = 60 - 15 - 30 = 15s
  2 Vault calls × 2 retries = 4 total calls
  Per call budget = 15s / 4 = 3.75s
  → connectTimeout=2s, readTimeout=3s (safe within budget)
```

---

## Cascading Failures: The Invisibility Amplifier Pattern

### What Is It?

A **cascading failure** occurs when one low-level problem (Layer 0) prevents ALL higher-level problems
from being visible. This causes:
- Multiple deploy cycles with zero progress
- Each fix reveals a NEW problem that was always there but masked
- Total debug time = N problems × deploy cycle time (not fixable in parallel)

### Classic Example (from production incident)

```
CMD missing (Layer 0)
  → Container crashes instantly → Zero logs → Zero error response
    → HTTP provider missing (Layer 1) — INVISIBLE
      → Vault secrets null (Layer 2) — INVISIBLE
        → OAuth credentials wrong (Layer 3) — INVISIBLE
          → Timeout budget exceeded (Layer 4) — INVISIBLE
```

**Result:** 7 deploy cycles, 4 hours of debug. Each cycle revealed only the NEXT problem.

### How to Identify a Cascade

Signs you're in a cascade:
1. **502 with empty body** — the #1 amplifier. Fix this FIRST, always.
2. **Fixing one issue reveals a different error** — not regression, it's the cascade unrolling.
3. **Error has no detail** — means the diagnostic layer itself failed (pre-diagnostic crash).
4. **Multiple seemingly unrelated issues** in a new function — they accumulated during development
   without deploy testing.

### Mitigation Strategy

#### Prevention (before it happens)
1. **Run `scripts/preflight.sh`** — catches Layer 0 issues (CMD, httpclient) before build
2. **Implement `initError` pattern** — prevents silent container death on Layer 1+ issues
3. **Deploy incrementally** — don't accumulate 5 changes before first deploy. Deploy after each
   capability addition

#### Resolution (when already in a cascade)
1. **Fix Layer 0 first** — the one producing 502 with empty body or zero diagnostic info
2. **Expect multiple failures** — after fixing Layer 0, budget for 2-3 more cycles
3. **Don't rollback prematurely** — each cycle REVEALS a problem, which is progress
4. **Track the cascade** — log each version: error seen, fix applied, next error

### Common Layer 0 Amplifiers

| Amplifier | Why It's Devastating | Pre-Flight Check |
|-----------|---------------------|------------------|
| Missing CMD in Dockerfile | Container dies before ANY code runs | `grep "^CMD" Dockerfile` |
| Missing httpclient-jersey | SDK client creation crashes in configure() | `grep httpclient-jersey pom.xml` |
| Uncaught configure() exception | JVM exits, no response ever sent | initError pattern in handler |
| Wrong class in CMD | ClassNotFoundException → immediate crash | Compare CMD with actual class path |
| OutOfMemoryError on cold start | Container killed by platform, no logs | Set memory ≥ 256MB for SDK functions |

### Debug Cycle Budget

When in a known cascade, plan for:
```
Estimated cycles = Number of NEW capabilities since last successful deploy
Estimated time per cycle = build(2min) + push(1min) + deploy(1min) + coldstart(15s) + test(30s) ≈ 5 min
Total estimate = cycles × 5 min

Example: New function with SDK + Vault + OAuth + JAXB (4 capabilities)
  → Budget 4-6 cycles × 5 min = 20-30 min (not 4 hours!)
```

---

## Error Pattern Matching Algorithm

```
1. GET response body (JSON)
2. EXTRACT: http_status, erro, detalhe
3. MATCH by priority:
   a. http_status == 502 AND body is empty → CMD missing
   b. detalhe CONTAINS "No http provider" → httpclient-jersey
   c. detalhe CONTAINS "is required" → missing config key
   d. detalhe CONTAINS "OAuth2" + "401" → Vault credentials
   e. detalhe CONTAINS "connect timed out" → network/gateway
   f. detalhe CONTAINS "BmcException" + extract status code → IAM or resource issue
   g. http_status == 504 → timeout budget
   h. NO MATCH → escalate to user with full error details
```
