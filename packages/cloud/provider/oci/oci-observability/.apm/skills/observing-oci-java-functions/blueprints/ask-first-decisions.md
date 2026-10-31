# Ask First Decisions — OCI Java Functions Observability

## Decision 1: Distributed Tracing Strategy

**When to ask**: Before generating any tracing code. The choice affects build pipeline, cold-start latency, vendor lock-in, and Docker image complexity.

**Questions to ask**:
1. "Do distributed requests span multiple OCI services or function chains?" → No → tracing may not be needed
2. "Is cold-start latency a hard SLA constraint (< 500 ms)?" → Yes → prefer Manual SDK or skip tracing
3. "Does the team need portability to non-OCI backends (Jaeger, Grafana)?" → Yes → OpenTelemetry agent
4. "Is the team already invested in OCI APM Console?" → Yes → OCI APM Java Agent or native tracer

| Option | Cold-Start Impact | Vendor Lock-in | OCI APM Integration | Complexity |
|--------|-------------------|----------------|---------------------|------------|
| **OCI APM Java Agent** (1.17.1.2) | +80–150 ms | High (Oracle FUTC) | Native — direct to APM Trace service | Medium |
| **OpenTelemetry Java Agent** (2.28.1 JAR) | +120–200 ms | Low (CNCF portable) | Via APM OTLP endpoint + Private Data Key | Medium |
| **Manual APM Tracer SDK** (library, no JVM agent) | Minimal | Medium | Native | High (programmatic spans) |
| **None** (oci_faas metrics only) | Zero | None | No distributed tracing | Low |

**Default recommendation**: If cold-start SLA is flexible (> 1s) and the team uses OCI APM Console, use **OpenTelemetry Agent** (portable CNCF standard, maps to APM via OTLP). For tight cold-start budgets, use **Manual APM Tracer SDK**.

**Source**: [OCI APM Overview](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/apm-overview.html) | [OpenTelemetry Java](https://github.com/open-telemetry/opentelemetry-java-instrumentation)

---

## Decision 2: Log Delivery Method

**When to ask**: Before generating logging code. Affects SDK dependencies, IAM policies, and retention configuration.

**Questions to ask**:
1. "Is retention beyond 30 days required?" → Yes → OCI Logging Analytics via Connector Hub
2. "Are logs PII-sensitive requiring an independent audit trail?" → Yes → SDK-based write with separate Log Group
3. "Is the team building for simplicity first?" → Yes → stdout capture (zero extra code, zero IAM for logging)

| Option | Delivery | Latency | Extra IAM | Structured Query | Best When |
|--------|----------|---------|-----------|-----------------|-----------|
| **stdout/stderr capture** | Automatic via platform | < 1s | Log Group + Log on app | Basic filter | Standard invocation logs |
| **`LoggingClient` SDK** (`oci-java-sdk-loggingingestion`) | Programmatic `PutLogs` | +20–50 ms | `use log-content` on DG | Full OCI Logging search | Audit events, custom retention |
| **OCI Logging Analytics** (via Connector Hub) | Log Group → Connector Hub → Log Analytics | Minutes | Connector Hub + Analytics | Full-text, ML anomaly | Analytics, retention > 30d |

**Default recommendation**: Use **stdout capture** for most functions. Graduate to `LoggingClient` SDK only when custom retention policy or PII-separated audit trail is explicitly required.

**Source**: [OCI Logging](https://docs.oracle.com/en-us/iaas/Content/Logging/home.htm) | [OCI Logging Analytics](https://docs.oracle.com/en-us/iaas/logging-analytics/home.htm)

---

## Decision 3: APM Data Key Type

**When to ask**: When configuring APM tracing. Wrong choice causes silent trace upload failure — no error is returned by the APM ingest endpoint.

**Questions to ask**:
1. "Is this code running inside OCI Functions (server-side)?" → Yes → **Private Data Key** (always)
2. "Is this code running in a browser or mobile app?" → Yes → **Public Data Key**

| Option | Authorization | Exposure Risk | Data Visibility | Best When |
|--------|--------------|---------------|-----------------|-----------|
| **Private Data Key** | Read + Write spans | High — never expose to clients | All spans, full trace context | Server-side (OCI Functions) |
| **Public Data Key** | Write-only (upload only) | Low — safe in JavaScript bundles | Upload path only | Browser/mobile RUM |

**Rule**: OCI Functions are always server-side. Always use **Private Data Key** stored as a function config variable (ideally sourced from OCI Vault), never the public key.

```yaml
# ✅ Correct — func.yaml
config:
  APM_PRIVATE_DATA_KEY: "INJECT_FROM_OCI_VAULT"

# ❌ Wrong — public key insufficient for server spans
config:
  APM_PUBLIC_DATA_KEY: "oci:apm:public:..."
```

**Source**: [OCI APM Data Keys](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/create-apm-domain.html)

---

## Decision 4: Java Runtime Version

**When to ask**: At project initialization or when a function needs language features not available in Java 11.

**Questions to ask**:
1. "Does the function use virtual threads for async I/O (Project Loom)?" → Yes → Java 21 custom image
2. "Is GraalVM native-image compilation needed for cold-start reduction?" → Yes → Java 21 + GraalVM CE custom image
3. "Is minimal operational overhead (no custom Dockerfile) preferred?" → Yes → Java 11 managed runtime
4. "Are Java records or sealed classes needed?" → Yes → Java 17+ custom image

| Option | Runtime Management | GraalVM | Records / Virtual Threads | Container Size |
|--------|--------------------|---------|--------------------------|----------------|
| **Java 11** (OCI-managed) | OCI platform | No | No | Smallest |
| **Java 17** (custom Docker) | Self-managed Dockerfile | Partial | Records, Sealed classes | Medium |
| **Java 21** (custom Docker) | Self-managed Dockerfile | Full | Virtual Threads (Loom) | Larger |

**Custom image base images**:
- Build: `fnproject/fn-java-fdk-build:jdk21-1.0.218`
- Runtime: `fnproject/fn-java-fdk:jdk21-1.0.218`

**Default recommendation**: Use **Java 11 managed runtime** for simplicity. Only switch to custom images when a specific Java 17/21 feature is required.

**Source**: [FDK Java Runtime](https://github.com/fnproject/fdk-java) | [OCI Functions Custom Images](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscustomimages.htm)
