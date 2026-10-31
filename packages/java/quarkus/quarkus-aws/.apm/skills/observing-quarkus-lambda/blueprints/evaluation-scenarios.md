# Evaluation Scenarios: observing-quarkus-lambda

Six scenarios covering canonical path, edge cases, misuse rejection and anti-pattern traps. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (JVM MDC and local tests)](#scenario-2-edge-case-jvm-mdc-and-local-tests)
- [Scenario 3: Misuse Rejection (single pillar or infrastructure)](#scenario-3-misuse-rejection-single-pillar-or-infrastructure)
- [Scenario 4: Anti-Pattern Trap (tenant as dimension)](#scenario-4-anti-pattern-trap-tenant-as-dimension)
- [Scenario 5: Anti-Pattern Trap (default tracing stack)](#scenario-5-anti-pattern-trap-default-tracing-stack)
- [Scenario 6: Edge Case (asked for something no pillar states)](#scenario-6-edge-case-asked-for-something-no-pillar-states)

---

## Scenario 1: Canonical Path

```yaml
id: 1
name: canonical-full-observability-task
skills: ["observing-quarkus-lambda"]
query: "Make my Quarkus 3.40 order Lambda observable: logs, traces and metrics, with the tenant visible in all three."
must_pass:
  - "Asks the three ADR decisions in order (tracing stack, metric approach, tenant representation) before writing code"
  - "Uses AWSRequestId and tenantId in MDC (medium confidence), a tenantId trace annotation, and an EMF line written with System.out.println"
  - "Names the baseline: Mode=Active plus the two X-Ray actions, quarkus-logging-json, explicit log-group retention"
  - "Hands infrastructure to the aws-observability agent and the validating-aws-observability skill by name, without writing Terraform"
must_not:
  - "Picks X-Ray SDK or OpenTelemetry without asking"
  - "Makes tenantId an unbounded dimension without an ADR"
  - "Loads the umbrella and a pillar skill for the same pillar"
```

---

## Scenario 2: Edge Case (JVM MDC and local tests)

```yaml
id: 2
name: edge-jvm-mdc-and-local-proof
skills: ["observing-quarkus-lambda"]
query: "My local test through the mock event server shows requestId in the logs, so is it safe to rely on MDC in the JVM managed runtime?"
must_pass:
  - "Says dev and test go through the poll loop that puts AWSRequestId in MDC, while the JVM managed-runtime path sets none (medium confidence)"
  - "Tells the user to put AWSRequestId and tenantId themselves and clear them in finally (medium confidence)"
  - "Recommends the deployed verification loop and does not assert a trace id in local tests (unverified)"
must_not:
  - "Claims the local test proves the JVM path"
```

---

## Scenario 3: Misuse Rejection (single pillar or infrastructure)

```yaml
id: 3
name: misuse-single-pillar-and-infra
skills: ["observing-quarkus-lambda"]
query: "Only configure the log group retention and the CloudWatch alarm for Errors on my Lambda in Terraform."
must_pass:
  - "States this is not a multi-pillar application task: retention HCL belongs to provisioning-aws-cloudwatch-v6 and alarms to monitoring-cloudwatch-observability, by name only"
  - "For a logs-only application question, points to logging-quarkus-lambda-v3-40 instead of loading the umbrella"
must_not:
  - "Writes Terraform or alarm definitions"
  - "Invents a Terraform resource shape"
```

---

## Scenario 4: Anti-Pattern Trap (tenant as dimension)

```yaml
id: 4
name: trap-tenant-id-dimension
skills: ["observing-quarkus-lambda"]
query: "Add TenantId and requestId as CloudWatch dimensions so I can graph each tenant. We expect thousands of tenants."
must_pass:
  - "Refuses requestId as a dimension and flags an unbounded TenantId dimension as needing an ADR"
  - "Offers tenant option B (root property plus Logs Insights) or C (bounded proxy plus property) and asks tenant count, per-tenant alarms and metric budget"
  - "Keeps the same tenantId key in the MDC and in the trace annotation"
must_not:
  - "Uses a key such as tenant_id for the annotation"
```

---

## Scenario 5: Anti-Pattern Trap (default tracing stack)

```yaml
id: 5
name: trap-default-tracing-stack
skills: ["observing-quarkus-lambda"]
query: "AWS recommends OpenTelemetry, so just add quarkus-opentelemetry and point the OTLP exporter at the X-Ray traces endpoint."
must_pass:
  - "Says the X-Ray SDK is in maintenance mode since 2026-02-25 but is not end of life, and that neither stack is a default"
  - "Says no OTel export route to X-Ray was found documented end to end for a Quarkus 3.40 Lambda (medium confidence, absence of evidence), that the default gRPC OTLP export must never be sent to the X-Ray endpoint (tracing F9, High), and that one documented route must be proven in a PoC"
  - "Asks for an ADR and a PoC of one route"
must_not:
  - "Presents OpenTelemetry as a verified Lambda path"
  - "Sets up the exporter as requested"
```

---

## Scenario 6: Edge Case (asked for something no pillar states)

```yaml
id: 6
name: edge-trace-id-in-logs
skills: ["observing-quarkus-lambda"]
query: "Put the X-Ray trace id into every log line and the EMF document so I can click from a log to its trace."
must_pass:
  - "Says no pillar skill states how to write the trace id into a log line or an EMF property and marks it (unverified)"
  - "Offers the documented join instead: trace annotation tenantId, request id in trace metadata, Logs Insights on mdc.AWSRequestId (medium confidence)"
  - "Suggests a deployed test if the user still wants the trace id"
must_not:
  - "Invents an MDC key or a header read for the trace id"
  - "Reads the trace header by hand instead of pointing to tracing-quarkus-lambda-v3-40"
```
