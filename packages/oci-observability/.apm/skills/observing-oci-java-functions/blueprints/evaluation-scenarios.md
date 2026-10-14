# Evaluation Scenarios — observing-oci-java-functions

## Scenario 1: Canonical — New Function Full Observability Stack

```json
{
  "skills": ["observing-oci-java-functions"],
  "query": "I'm building a new Java 21 OCI Function 'invoice-processor' in a private subnet. Set up structured logging, a custom metric 'invoices_processed', and distributed tracing with OpenTelemetry.",
  "expected_behavior": [
    "Recommends starting with stdout JSON logging (zero dependency, automatic capture) via oci_logging_log Terraform resource with source_type=OCISERVICE",
    "Initializes MonitoringClient and any APM tracer in @FnConfiguration / static block — never per invocation",
    "Uses ResourcePrincipalAuthenticationDetailsProvider exclusively — no API keys or PEM files in image",
    "Declares oci-java-sdk-bom:3.87.0 in <dependencyManagement> to prevent NoClassDefFoundError at cold-start",
    "Stores COMPARTMENT_OCID, METRIC_NAMESPACE, APM_PRIVATE_DATA_KEY in function config env vars — not hardcoded",
    "Notes that a Service Gateway (not Internet Gateway) is required for private subnet access to OCI APIs and APM endpoints",
    "Asks about cold-start SLA before recommending OTel Java Agent (adds 120-200ms) vs native APM tracer (minimal overhead)"
  ]
}
```

---

## Scenario 2: Canonical — Choosing a Distributed Tracing Strategy

```json
{
  "skills": ["observing-oci-java-functions"],
  "query": "We need distributed tracing for our OCI Functions chain. The team uses Grafana and wants to avoid Oracle lock-in. What tracing approach do you recommend?",
  "expected_behavior": [
    "Identifies the four options: OCI APM Java Agent, OpenTelemetry Java Agent v2.28.1, Manual APM Tracer SDK, None (oci_faas metrics only)",
    "Recommends OpenTelemetry Java Agent given the stated Grafana integration and portability requirements",
    "Warns about the +120-200ms cold-start overhead of the OTel agent and asks whether cold-start SLA allows it",
    "Does NOT recommend the APM Java Agent without asking about vendor lock-in tolerance",
    "Shows that Private Data Key (not Public key) is required for server-side span upload — wrong key causes silent failure",
    "Provides the OTEL_EXPORTER_OTLP_ENDPOINT value format pointing to the OCI APM collector endpoint"
  ]
}
```

---

## Scenario 3: Edge — APM Trace Explorer Empty After Deploy

```json
{
  "skills": ["observing-oci-java-functions"],
  "query": "I deployed my function with OTel Java Agent instrumentation but the APM Trace Explorer shows no spans after several invocations. Logs are working fine.",
  "expected_behavior": [
    "First checks APM_PRIVATE_DATA_KEY: confirms it is the Private key (not Public key) — wrong key type causes silent failure",
    "Checks OTLP endpoint URL format: must be retrieved from OCI Console APM Domain Details, not hardcoded from docs (region-specific)",
    "Verifies the OTel agent JAR is included in the Docker image and JAVA_TOOL_OPTIONS points to it",
    "Checks that Service Gateway is configured for private subnet egress to the APM collector endpoint",
    "Does NOT suggest increasing log verbosity as the first debug step — endpoint and key type are the most common causes"
  ]
}
```

---

## Scenario 4: Edge — Cold-Start Impact from Observability Libraries

```json
{
  "skills": ["observing-oci-java-functions"],
  "query": "My function has a 3-second cold start and I suspect the observability libraries are the main contributor. How do I diagnose and reduce it?",
  "expected_behavior": [
    "Identifies ResourcePrincipalAuthenticationDetailsProvider initialization as a known cold-start cost (HTTP to metadata service)",
    "Identifies OTel Java Agent as adding 120-200ms to cold start — recommends switching to Manual APM Tracer SDK or native APM agent for lower overhead",
    "Recommends BOM import (oci-java-sdk-bom) to prevent classloader conflicts that inflate startup time",
    "Suggests using Java 11 managed runtime (zero Dockerfile overhead) vs custom image if features allow",
    "Notes that static block initialization in @FnConfiguration pays the cold-start cost once, not per warm invocation — confirms this is already correct pattern"
  ]
}
```

---

## Scenario 5: Misuse — Logging Config Variables Including APM Key

```json
{
  "skills": ["observing-oci-java-functions"],
  "query": "For easier debugging I'm logging all function config variables at startup including APM_PRIVATE_DATA_KEY, COMPARTMENT_OCID, and METRIC_NAMESPACE. Is there anything wrong with this?",
  "expected_behavior": [
    "Identifies logging APM_PRIVATE_DATA_KEY as the critical anti-pattern: OCI Logging is searchable and forwardable to SIEM — exposure equals OWASP A02 Cryptographic Failure",
    "Explains that an exposed Private Data Key enables unauthorized span writes to the APM domain (trace data corruption and cost amplification)",
    "Recommends logging only non-sensitive config: METRIC_NAMESPACE, function OCID, region — never keys or secrets",
    "Suggests structured log redaction pattern: log key name presence (e.g. 'APM_PRIVATE_DATA_KEY=<set>') without the value",
    "Does NOT suggest encrypting the log output as a compensating control — the correct fix is not logging secrets in the first place"
  ]
}
```
