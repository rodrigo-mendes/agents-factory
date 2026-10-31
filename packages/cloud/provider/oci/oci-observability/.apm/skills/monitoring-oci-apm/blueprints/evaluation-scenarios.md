# Evaluation Scenarios — monitoring-oci-apm

## Scenario 1: New OKE Microservice Deployment — Full Stack Observability

```json
{
  "skills": ["monitoring-oci-apm"],
  "query": "We are deploying a new Java 21 microservice called 'order-service' to OCI Kubernetes (OKE) in production. The service uses Oracle Autonomous Database. Set up full observability with distributed tracing, log correlation, and availability monitoring.",
  "expected_behavior": [
    "Creates separate APM domain for production compartment (not shared with staging/dev)",
    "Recommends APM Java Agent over OTel SDK because Oracle Autonomous Database is in use (deep SQL diagnostics)",
    "Provides apm-agent.properties with service.name=order-service, service.version and deployment.environment set via env vars",
    "Shows Logback MDC configuration to inject traceId and spanId into JSON log records",
    "Creates Terraform for oci_apm_synthetics_monitor with REST monitor on /health from ≥3 vantage points",
    "Instructs storing Private Data Key in OCI Vault and injecting via APM_PRIVATE_DATA_KEY env var",
    "Provides OKE Service Gateway routing configuration for private subnet APM agent egress"
  ]
}
```

---

## Scenario 2: Cost Runaway — High-Volume Service Sampling

```json
{
  "skills": ["monitoring-oci-apm"],
  "query": "Our payment service processes 8,000 requests per second in production and our APM bill has tripled this month. Currently we have no sampling configured. How do we control costs without losing visibility into errors?",
  "expected_behavior": [
    "Identifies 100% sampling at 8K req/s as the cost root cause (8K × avg_spans × 3600 = massive event volume)",
    "Recommends tail-based sampling via OTLP Collector — NOT head-based — to retain 100% of ERROR traces",
    "Provides complete OTLP Collector tail_sampling processor config with three policies: ERROR status, latency >2s, 5% probabilistic for OK traces",
    "Does NOT recommend simply reducing sampling rate without mentioning error trace loss implication",
    "Suggests setting OCI Budget alert at 120% of new baseline APM spend as a cost governance control",
    "Mentions DaemonSet deployment (1 Collector per node) as the right OKE pattern for Collector"
  ]
}
```

---

## Scenario 3: Security Audit — Exposed Private Data Key

```json
{
  "skills": ["monitoring-oci-apm"],
  "query": "Our security team found an APM Private Data Key committed in a git repository 3 months ago. What is the blast radius and how do we remediate?",
  "expected_behavior": [
    "Identifies the exact risks: unauthorized span injection (trace data corruption), cost amplification via span flooding, domain endpoint reconnaissance",
    "Provides immediate remediation: rotate key via OCI CLI generate-data-keys command",
    "Shows git history scanning command to confirm scope of exposure",
    "Provides the correct Vault-based storage pattern as the post-remediation architecture",
    "Distinguishes between Public key (safe for browser) and Private key (must be in Vault) — explains why the public key does NOT need the same treatment",
    "Notes that APM Datastore does not support span-level deletion — injected fabricated spans cannot be retroactively purged"
  ]
}
```

---

## Scenario 4: Private Service Synthetic Monitoring

```json
{
  "skills": ["monitoring-oci-apm"],
  "query": "We have an internal REST API running in a private OCI subnet (not internet-accessible) that we need to monitor for availability from inside our VCN. How do we set up synthetic monitoring?",
  "expected_behavior": [
    "Identifies that Oracle Public Vantage Points cannot reach a private subnet service",
    "Recommends Dedicated Vantage Point (oci_apm_synthetics_dedicated_vantage_point) deployed inside the private VCN",
    "Provides Terraform for dedicated VP resource",
    "Explains the Dedicated VP agent calls out to APM Control Plane via Service Gateway (no inbound internet required)",
    "Does NOT suggest making the internal service public as a workaround"
  ]
}
```

---

## Scenario 5: Multi-Environment Setup with Terraform

```json
{
  "skills": ["monitoring-oci-apm"],
  "query": "Set up APM for a three-environment deployment (dev, staging, prod) using Terraform. Dev should use Always Free tier.",
  "expected_behavior": [
    "Creates three separate oci_apm_apm_domain resources in separate compartments — never a single shared domain",
    "Sets is_free_tier=true only for dev domain",
    "Uses defined_tags with operations.environment tag on each domain",
    "Provides Terraform for oci_vault_secret to store Private Data Key per environment",
    "Does NOT create a single domain with environment filtering as an alternative"
  ]
}
```
