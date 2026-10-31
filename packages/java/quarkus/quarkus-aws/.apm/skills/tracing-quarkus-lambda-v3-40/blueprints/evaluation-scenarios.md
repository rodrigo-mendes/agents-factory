# Evaluation Scenarios: tracing-quarkus-lambda-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (trace header on Java 17+ and native)](#scenario-2-edge-case-trace-header-on-java-17-and-native)
- [Scenario 3: Misuse Rejection (out-of-scope request)](#scenario-3-misuse-rejection-out-of-scope-request)
- [Scenario 4: Anti-Pattern Trap (annotation keys and PII)](#scenario-4-anti-pattern-trap-annotation-keys-and-pii)
- [Scenario 5: Anti-Pattern Trap (OTLP to the X-Ray endpoint)](#scenario-5-anti-pattern-trap-otlp-to-the-x-ray-endpoint)
- [Scenario 6: Edge Case (HTTP API and sampling)](#scenario-6-edge-case-http-api-and-sampling)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-end-to-end-trace-request
skills: ["tracing-quarkus-lambda-v3-40"]
query: "Add tracing to my Quarkus 3.40 Lambda so I see API Gateway -> Lambda -> DynamoDB in X-Ray."
must_pass:
  - "Asks X-Ray SDK vs OpenTelemetry (Ask First C1, ADR) and states the X-Ray SDK has been in maintenance mode since 2026-02-25"
  - "Says that an API Gateway node needs a REST API because an HTTP API has no X-Ray, and points to the HTTP skill's ask-first-decisions"
  - "Requires TracingConfig Mode=Active and the actions xray:PutTraceSegments and xray:PutTelemetryRecords, deferring IaC to provisioning-aws-xray-v6 (no SAM or CDK)"
  - "On the X-Ray path attaches TracingInterceptor to the DynamoDB client; on a native build adds quarkus-amazon-lambda-xray and says it is native-image support, not a tracer"
must_not:
  - "Picks X-Ray SDK or OpenTelemetry without asking"
  - "Claims an OTel to X-Ray export route is documented for a Quarkus Lambda"
  - "Writes Terraform or SAM templates"
```

---

## Scenario 2: Edge Case (trace header on Java 17+ and native)

**Type**: Platform behaviour that differs from older docs

```yaml
id: 2
name: edge-trace-header-system-property
skills: ["tracing-quarkus-lambda-v3-40"]
query: "I read _X_AMZN_TRACE_ID to put the trace ID in my response but it is always null on java21 and in native. Why?"
must_pass:
  - "Says Lambda does not use _X_AMZN_TRACE_ID for Java 17+ and does not define it on OS-only runtimes"
  - "Gives System.getProperty(\"com.amazonaws.xray.traceHeader\") as the replacement"
  - "Mentions that Quarkus sets that property from the Lambda-Runtime-Trace-Id header in its poll loop, and tags which runtime mode uses the loop as (medium confidence)"
  - "Reminds that nothing is sent unless TracingConfig is Mode=Active"
must_not:
  - "Suggests setting _X_AMZN_TRACE_ID manually"
```

---

## Scenario 3: Misuse Rejection (out-of-scope request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-out-of-scope-logging-terraform-powertools
skills: ["tracing-quarkus-lambda-v3-40"]
query: "Write the Terraform for the X-Ray sampling rule, add Powertools tracing and set up JSON logging with the trace ID."
must_pass:
  - "Declines Terraform and points to provisioning-aws-xray-v6 (X-Ray design: tracing-aws-xray)"
  - "Points Powertools tracing to implementing-lambda-powertools-java and says its use inside Quarkus is (unverified)"
  - "Points logging to logging-quarkus-lambda-v3-40 by name"
  - "May still answer the tracing part: Lambda's own sampling is not configurable and stage rules belong to a REST API"
must_not:
  - "Writes HCL or SAM"
  - "Claims Powertools tracing works in Quarkus"
```

---

## Scenario 4: Anti-Pattern Trap (annotation keys and PII)

**Type**: Request that tempts the agent into a forbidden pattern

```yaml
id: 4
name: trap-underscore-key-and-email-annotation
skills: ["tracing-quarkus-lambda-v3-40"]
query: "Annotate every trace with tenant_id and the user's email so support can search by them."
must_pass:
  - "Rejects the email: annotations and metadata are readable by anyone with X-Ray read access (no PII, family rule 7)"
  - "Rejects tenant_id: keys allow alphanumerics and dots only; proposes tenantId or tenant.id"
  - "Annotates a subsegment, not the Lambda function segment"
  - "Asks Ask First C7 (is tenantId opaque and bounded?) and notes only 50 annotations are indexed per trace"
  - "States that how the SDK treats an invalid key is (unverified)"
must_not:
  - "Uses putAnnotation(\"tenant_id\", ...) or puts the email in any annotation, metadata or span attribute"
  - "Enables quarkus.otel.traces.eusp.enabled"
```

---

## Scenario 5: Anti-Pattern Trap (OTLP to the X-Ray endpoint)

**Type**: Plausible shortcut that fails

```yaml
id: 5
name: trap-otlp-grpc-to-xray-endpoint
skills: ["tracing-quarkus-lambda-v3-40"]
query: "We chose OpenTelemetry. Just point quarkus.otel.exporter.otlp.traces.endpoint at https://xray.eu-west-1.amazonaws.com and we are done."
must_pass:
  - "Explains the Quarkus default protocol is grpc, while the endpoint is HTTP only and needs SigV4"
  - "Says plainly that no OTel to X-Ray export route is documented end to end for a Quarkus 3.40 Lambda in the pages read (medium confidence, absence of evidence)"
  - "Lists the AWS-documented routes (UDP span exporter, AWS Lambda Layer for OpenTelemetry, OTLP endpoint) and tags Quarkus wiring and SigV4 as (unverified)"
  - "Asks which route to prove in a PoC and recommends quarkus.otel.simple=true and quarkus.<client>.telemetry.enabled=true meanwhile"
must_not:
  - "Confirms the endpoint setting works"
  - "Picks an export route as the default"
```

---

## Scenario 6: Edge Case (HTTP API and sampling)

**Type**: Conflicting expectations with platform limits

```yaml
id: 6
name: edge-http-api-sampling-published-version
skills: ["tracing-quarkus-lambda-v3-40"]
query: "We use quarkus-amazon-lambda-http on an HTTP API. Add a sampling rule for the function at 50% and flip tracing to Active on version 7."
must_pass:
  - "Says an HTTP API has no X-Ray tracing, so there is no API Gateway segment and no stage rules"
  - "Says Lambda's sampling (1 request/s + 5%) cannot be configured with X-Ray rules for functions"
  - "Says tracing mode cannot change on a published version: set Mode=Active, publish a new version and move the alias"
  - "Offers the REST API option (preview extension) or Lambda-only sampling as an Ask First C3/C5 decision"
must_not:
  - "Creates a rule for AWS::Lambda::Function and promises 50%"
  - "Updates version 7 in place"
```
