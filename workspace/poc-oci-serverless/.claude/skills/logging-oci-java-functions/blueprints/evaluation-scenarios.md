# Evaluation Scenarios — logging-oci-java-functions

Three scenarios to verify the skill activates correctly and produces safe, production-ready output.

---

## Scenario 1: Greenfield Function — Add Full Logging Stack

```json
{
  "skills": ["logging-oci-java-functions"],
  "query": "I have a new OCI Java Function (FDK 1.1.12) with no logging configured. Add structured logging so I can see logs in OCI Console and query them by field.",
  "expected_behavior": [
    "Adds SLF4J 2.0.16 + Logback 1.5.18 + logstash-logback-encoder:8.0 to pom.xml",
    "Creates logback.xml with LogstashEncoder outputting JSON to stdout",
    "Provisions oci_logging_log Terraform resource with source_type=OCISERVICE and category=invoke",
    "Installs SLF4JBridgeHandler in @FnConfiguration to silence OCI SDK JUL noise",
    "Adds MDC.clear() in a finally block inside handleRequest",
    "Does NOT add custom metrics or APM tracing (out of scope for this skill)"
  ]
}
```

---

## Scenario 2: Audit Log to Separate Log Group via SDK

```json
{
  "skills": ["logging-oci-java-functions"],
  "query": "I need to write audit log entries (order events) to a separate OCI Log Group with 90-day retention, using the LoggingIngestionClient. The function already uses Logback for stdout logging.",
  "expected_behavior": [
    "Adds oci-java-sdk-loggingingestion and oci-java-sdk-common-httpclient-jersey3 to pom.xml via OCI SDK BOM",
    "Initializes LoggingIngestionClient with ResourcePrincipalAuthenticationDetailsProvider in @FnConfiguration (not per-invocation)",
    "Collects LogEntry objects in a List during invocation and calls putLogs() once in the finally block",
    "Does NOT call putLogs in a background thread",
    "Provisions a separate oci_logging_log resource with log_type=CUSTOM and retention_duration=90",
    "IAM policy grants use log-content (not manage logs) scoped to the audit log group",
    "putLogs failure is caught and logged as warn — function execution continues"
  ]
}
```

---

## Scenario 3: Security Review — Detect and Fix Logging Anti-Patterns

```json
{
  "skills": ["logging-oci-java-functions"],
  "query": "Review this function code for logging security issues:\n\npublic String handleRequest(Map<String,String> request) {\n  log.info('Request: {}', request);\n  log.debug('Config: {}', ctx.getConfiguration());\n  MDC.put('userId', request.get('userId'));\n  return process(request);\n}",
  "expected_behavior": [
    "Flags log.info('Request: {}', request) — may log PII/credentials (OWASP A09, GDPR)",
    "Flags log.debug('Config: {}', ctx.getConfiguration()) — may expose secret config keys (OWASP A09)",
    "Flags missing MDC.clear() — warm invocation MDC leak (silent log-correlation corruption)",
    "Provides corrected code logging only non-sensitive identifiers (e.g., orderId)",
    "Adds MDC.clear() in a finally block",
    "Does NOT suggest disabling logging entirely — recommends safe selective field logging"
  ]
}
```
