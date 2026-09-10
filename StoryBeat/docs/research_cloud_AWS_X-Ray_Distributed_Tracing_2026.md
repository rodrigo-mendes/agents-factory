# Cloud Architecture Research — AWS X-Ray Distributed Tracing 2026

## Metadata
```yaml
Full_Name: "AWS Observability Architecture - X-Ray Distributed Tracing"
Cloud_Provider: "AWS"
Architecture_Domain: "Observability Architecture - X-Ray Distributed Tracing"
Target_Edition: "AWS X-Ray 2026"
Architecture_Context: "web application"
Official_Source_URL: "https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-31"
Currency_Threshold: "2027-08-31"
Research_Depth: "exhaustive"
Max_Iterations: "8"
Research_Quality_Score: "91%"
Gap_Loop_Ran: "true"
Iterations_Used: "2 (parallel, 5+5 section-investigators across 2 runs)"
Triangulated_Count: "12"
Unverified_Count: "5"
Irresolvable_Count: "4"
```

## Executive Summary

AWS X-Ray is the managed distributed tracing service within the AWS observability stack. It collects request data from compute resources — Lambda, ECS, EC2, Elastic Beanstalk, and API Gateway — and assembles segments and subsegments into a unified trace, generating a service graph that architects and operators use to identify latency bottlenecks, error sources, and downstream dependency failures in web applications and microservices. In 2026, X-Ray is no longer a standalone tool: it is the trace backend for CloudWatch Application Signals, the data source for Transaction Search (full-fidelity span analytics), and the engine behind X-Ray Insights (automated anomaly detection). The resulting observability plane covers metrics, logs, and traces in a single CloudWatch-integrated surface.

The most consequential change in the 2026 edition is that the AWS X-Ray SDKs and X-Ray Daemon entered maintenance mode on February 25, 2026, with full end-of-support on February 25, 2027. AWS now limits SDK and Daemon releases to security patches only and officially directs all new instrumentation to OpenTelemetry — either via the AWS Distro for OpenTelemetry (ADOT) or vanilla OTel SDKs. Alongside this, two GA features have fundamentally changed the observability offering: CloudWatch Application Signals (GA June 2024) delivers automatic instrumentation, service topology, SLOs, real-user monitoring, and AI-powered analysis; and Transaction Search (GA November 2024) ingests 100% of spans as structured logs in the `aws/spans` CloudWatch Logs log group, enabling full-fidelity trace search at scale. The CloudWatch OTel Endpoint allows direct OTLP export to X-Ray without deploying a local collector process.

For web applications in 2026, three architecture guardrails are non-negotiable. First, all new instrumentation must use ADOT — using the legacy X-Ray SDK creates a technical debt path with no future feature development. Second, sampling rules must be defined centrally in the X-Ray console, not locally per SDK instance; per-instance local rules cause effective sampling rates to multiply across fleet members and drive uncontrolled cost. Third, sensitive data — especially PII and credentials — must never appear in X-Ray annotations, which are indexed, searchable, and accessible to any IAM principal with `AWSXrayReadOnlyAccess`; use hashed identifiers and apply KMS encryption.

## Cloud Architecture Glossary

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

```
Term: Segment
Definition: The unit of data sent to X-Ray by a compute resource running application logic. Records resource name, request details (host, method, client address, path, user agent), response details (status, content), timing (start and end times), subsegments, and errors or exceptions. Segment documents may be up to 64 kB in size. In OpenTelemetry terminology, a segment maps to a Server Span.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html
Architect Usage: The top-level unit of work for a single service handling a request. Reference when defining instrumentation scope per compute tier.
Common Confusion: Confused with Trace (which is the collection of all segments for a single end-to-end request) or with Span (the OTel equivalent). A segment is AWS-X-Ray-specific; a Span is the OTel-standard equivalent.
Confidence: 🟢
```

```
Term: Subsegment
Definition: A granular timing record nested within a Segment. Used for downstream calls (AWS SDK calls to DynamoDB, S3, etc.), external HTTP APIs, SQL queries, and arbitrary instrumented code blocks. For services that do not send their own segments (e.g., DynamoDB), X-Ray uses subsegments to generate Inferred Segments. In OTel terminology, a subsegment maps to a non-Server Span.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html
Architect Usage: Instrument every downstream call as a subsegment to achieve call-level latency attribution. Required for generating downstream nodes on the service map for services that do not self-instrument.
Common Confusion: Confused with Segment. Subsegments are always children of a Segment; they represent downstream work, not the top-level service entry point.
Confidence: 🟢
```

```
Term: Trace
Definition: A collection of all Segments and Subsegments generated by a single end-to-end request, identified by a Trace ID. Trace data is retained for 30 days.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html
Architect Usage: The unit of end-to-end visibility. Design instrumentation so every service in a request path contributes a segment to the same trace.
Common Confusion: Confused with Span (OTel) or with Service Graph. A Trace is a single-request data artifact; a Service Graph is a statistical aggregation of many traces.
Confidence: 🟢
```

```
Term: Span (OpenTelemetry)
Definition: The OTel equivalent of X-Ray Segments and Subsegments. Each span includes: name, unique ID, start/end timestamps, span kind, span context, attributes, events, links, status, and parent span reference. Server Spans convert to X-Ray Segments; all other spans convert to X-Ray Subsegments.
Provider Docs Section: X-Ray SDK Migration Guide — https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html
Architect Usage: Use Span terminology when specifying instrumentation requirements for ADOT-based services. Understand the Segment vs. non-Server-Span mapping when comparing X-Ray and OTel data models.
Common Confusion: Confused with X-Ray Segment/Subsegment at a 1:1 level. The mapping is Server Span = Segment; all other spans = Subsegments — not a universal 1:1.
Confidence: 🟢
```

```
Term: Service Graph / Service Map
Definition: A JSON document (Service Graph) and its visual rendering (Service Map in the CloudWatch console) that describes all services and resources involved in traced requests, their interconnections, and aggregate error/fault/throttle rates. Node color coding: Green = success, Red = 500 faults, Yellow = 400 errors, Purple = 429 throttle. Maximum: 10,000 nodes. Data retained for 30 days.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html; Service Map — https://docs.aws.amazon.com/xray/latest/devguide/xray-console-servicemap.html
Architect Usage: Primary visualization for identifying which service in a microservice chain is the latency or fault source. Design URL paths carefully — HTTP integrations with many unique path parameters can exceed the 10,000-node limit.
Common Confusion: Confused with Trace Map (the CloudWatch console term for the same surface). Service Map and Trace Map are the same visualization, now surfaced in CloudWatch console, not the standalone X-Ray console.
Confidence: 🟢
```

```
Term: Sampling / Sampling Rule
Definition: A configurable rule set applied by the X-Ray-enabled service to decide which requests generate trace data. Default rule: reservoir = 1 request/second, fixed rate = 5% of additional requests. Rules have: Priority (1–9999, first match wins), Reservoir, Rate, ServiceName, ServiceType, Host, HTTPMethod, URLPath, ResourceARN, and optional Attributes. Parent-based sampling: the first service makes the decision; all downstream services honor it.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html; Sampling — https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html
Architect Usage: Always define rules centrally in the X-Ray console, not locally in SDK config files. Apply higher-priority rules for critical routes. Configure low/zero rates for health-check endpoints. Temporarily raise rate for targeted debugging via a scoped high-priority rule.
Common Confusion: Confused with head sampling (the keep/drop decision at trace start) vs. tail sampling (decision after full trace is collected). X-Ray uses head sampling. Transaction Search with head sampling = 100% enables full-fidelity span capture.
Confidence: 🟢
```

```
Term: Tracing Header
Definition: The HTTP header `X-Amzn-Trace-Id` that carries the trace ID, parent segment ID, and sampling decision across service boundaries. Format: `Root=1-5759e988-bd862e3fe1be46a994272793;Parent=53995c3f42cd8ad8;Sampled=1`. API Gateway automatically adds this header to all incoming requests that lack it.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html
Architect Usage: Ensure every service that forwards HTTP requests also forwards this header unchanged. For ADOT, the W3C `traceparent` header is the default; configure the X-Ray Propagator in OTel config to ensure AWS service compatibility.
Common Confusion: Confused with W3C Trace Context (`traceparent` header). These are two different propagation formats. ADOT defaults to W3C; legacy X-Ray SDK defaults to `X-Amzn-Trace-Id`. Hybrid environments need both propagators configured.
Confidence: 🟢
```

```
Term: Annotations
Definition: Indexed key-value pairs (string, boolean, or number) attached to a segment or subsegment and used with filter expressions to group or search traces. X-Ray indexes up to 50 annotations per trace. Annotations are visible to any IAM principal with xray:GetTraceSummaries or xray:BatchGetTraces. In OTel, to promote an attribute to an annotation, its key must be added to the `aws.xray.annotations` attribute list.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html
Architect Usage: Use only non-sensitive business identifiers (order ID, tenant ID, feature flag) as annotation values. Never store PII, credentials, or tokens in annotations.
Common Confusion: Confused with Metadata. Annotations are indexed and searchable; Metadata is not indexed and cannot be used in filter expressions. Use Metadata for debug data; use Annotations for searchable correlation keys.
Confidence: 🟢
```

```
Term: Metadata
Definition: Non-indexed key-value pairs with values of any type (including objects and lists), stored in the trace but not searchable via filter expressions. In OTel, span attributes map to X-Ray Metadata by default.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html
Architect Usage: Prefer Metadata over Annotations for debug data, request payloads (sanitized), and structured context that does not need to be searchable.
Common Confusion: Confused with Annotations. The key distinction: Annotations are indexed and queryable; Metadata is not. Metadata can hold complex objects; Annotations are limited to scalar types.
Confidence: 🟢
```

```
Term: X-Ray Group
Definition: A named filter expression that produces its own service graph, trace summaries, and CloudWatch metrics. Groups are billed by the number of retrieved traces matching the filter expression. CloudWatch metrics for matching trace counts are published every minute. Insights must be enabled per group.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html
Architect Usage: Create groups to partition traffic by service tier, environment, or criticality. Use groups to scope Insights anomaly detection. Monitor group-level CloudWatch metrics to detect traffic and error-rate shifts per logical workload segment.
Common Confusion: Confused with AWS resource groups or CloudWatch log groups. An X-Ray Group is a filter-expression-based logical partition of traces within X-Ray, not an AWS resource group or a log group.
Confidence: 🟢
```

```
Term: X-Ray Insights
Definition: A continuous analysis feature that applies statistical modeling to predict expected fault rates per service. An Insight is created when observed fault rates exceed the expected range and is resolved when the rate returns to expected. Deduplicates anomalies across microservices to a single root-cause node. Notifications via Amazon EventBridge (best-effort). Must be enabled per X-Ray Group.
Provider Docs Section: X-Ray Insights — https://docs.aws.amazon.com/xray/latest/devguide/xray-console-insights.html
Architect Usage: Enable Insights on all production groups. Wire EventBridge notifications to SNS or Lambda for automated incident management. Do not rely on EventBridge Insights notifications as guaranteed delivery for critical alerting.
Common Confusion: Confused with CloudWatch Anomaly Detection. Insights is trace-aware, identifies root-cause services within a trace graph, and deduplicates across microservices. CloudWatch Anomaly Detection operates on metric time-series without trace context.
Confidence: 🟢
```

```
Term: Transaction Search
Definition: A CloudWatch Application Signals feature (GA November 2024) that ingests 100% of spans as structured logs in the `aws/spans` CloudWatch Logs log group. Enables full-fidelity search of all span attributes, analytics via a visual editor, trace visualization with up to 10,000 spans, and full OTel semantic convention support. Billed under CloudWatch Logs pricing. Requires head sampling = 100% to capture all spans.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-spans.html
Architect Usage: Enable Transaction Search for customer-facing APIs where debugging specific user requests is required, for compliance use cases needing full trace retention, and for p99 latency debugging. Monitor CloudWatch Logs ingestion costs at high trace volumes.
Common Confusion: Confused with X-Ray trace storage. Transaction Search stores spans in CloudWatch Logs, not in X-Ray trace storage. They coexist: X-Ray holds sampled traces (30-day retention); `aws/spans` holds all spans as logs (CloudWatch Logs retention rules apply).
Confidence: 🟢
```

```
Term: AWS Distro for OpenTelemetry (ADOT)
Definition: An AWS-supported, security-patched distribution of CNCF OpenTelemetry SDKs, auto-instrumentation agents, and the ADOT Collector. Supports instrument-once, export-to-many telemetry (X-Ray, CloudWatch EMF, Amazon Managed Prometheus, Amazon OpenSearch, any OTLP backend). Lambda: AWS-managed Lambda layers. Languages: Go, Java, JavaScript, Python, Ruby, .NET, PHP.
Provider Docs Section: https://aws-otel.github.io/; https://docs.aws.amazon.com/xray/latest/devguide/xray-services-adot.html
Architect Usage: Mandatory for all new instrumentation as of 2026-02-25 (X-Ray SDK maintenance mode). Use ADOT Managed Lambda Layers for Lambda; ADOT Collector sidecar for ECS. ADOT may lag upstream OTel releases slightly.
Common Confusion: Confused with vanilla OpenTelemetry SDK. ADOT adds AWS-specific exporters, resource detectors, X-Ray remote sampling, and AWS support SLAs on top of OTel. Vanilla OTel requires manual AWS-specific configuration.
Confidence: 🟢
```

```
Term: Inferred Segment
Definition: A synthetic segment generated by X-Ray from an upstream subsegment for a downstream service that does not emit its own segment (e.g., Amazon DynamoDB, Amazon RDS). Appears as a node on the service map.
Provider Docs Section: X-Ray Concepts — https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html
Architect Usage: Do not attempt to instrument DynamoDB or RDS to generate their own segments — rely on Inferred Segments from instrumented SDK calls in the calling service.
Common Confusion: Confused with a real segment emitted by the downstream service. An Inferred Segment is constructed by X-Ray from subsegment data; it does not represent direct telemetry from DynamoDB or RDS.
Confidence: 🟢
```

```
Term: CloudWatch Application Signals
Definition: AWS's GA (June 2024) APM solution providing automatic instrumentation across ECS, EKS, Lambda, and EC2; service topology visualization; SLOs (period-based and request-based); real user monitoring (RUM); synthetic monitoring; and AI-powered analysis. Integrates X-Ray tracing into a unified CloudWatch observability plane. Supported languages: Java, Python, Node.js, .NET.
Provider Docs Section: https://aws.amazon.com/xray/; https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Application-Signals-TraceLogCorrelation.html
Architect Usage: Enable Application Signals on all production services to gain automatic SLO generation from trace-derived latency and error-rate metrics without manual CloudWatch metric instrumentation.
Common Confusion: Confused with X-Ray as a standalone product. Application Signals is an APM overlay that uses X-Ray as its trace backend, enriching it with SLOs, RUM, synthetic monitoring, and AI analysis.
Confidence: 🟢
```

## Architecture Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**Pattern 1 — End-to-End Trace Instrumentation via ADOT**
- Pillar Alignment: OPS08-BP03 (Operational Excellence — Analyze Workload Traces; Risk: Medium)
- Why: WAF Operational Excellence requires implementing distributed tracing so that request flows are visible across all service boundaries, enabling root-cause analysis and latency attribution. As of 2026-02-25, X-Ray SDKs and Daemon are in maintenance mode; ADOT is the official instrumentation path. Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/ops_workload_observability_analyze_workload_traces.html
- AWS Services: AWS X-Ray (trace backend), AWS Distro for OpenTelemetry (ADOT SDK + Collector), Amazon API Gateway (REST), AWS Lambda, Amazon ECS, Amazon EC2, AWS CloudWatch Agent
- Architecture Decision:
  - API Gateway (REST only): Enable active tracing on every stage (console: Logs/Tracing tab). API Gateway automatically adds `X-Amzn-Trace-Id` to incoming requests. Only REST APIs are supported.
  - Lambda: Enable Active Tracing per function (Configuration tab → Additional monitoring tools). Bundle the ADOT Managed Lambda Layer. Lambda creates and sends its own segment; annotations and metadata may only be applied to subsegments.
  - ECS Fargate: Add the ADOT Collector as a sidecar container (`public.ecr.aws/aws-observability/aws-otel-collector:latest`) in the task definition. Application container exports OTel telemetry to `http://localhost:4317` (gRPC) or `http://localhost:4318` (HTTP). Task IAM role must grant X-Ray write and SSM read permissions.
  - EC2: Install CloudWatch Agent v1.300025.0 or later. Supports OTel traces without a separate X-Ray Daemon process.
  - DynamoDB / RDS: Instrumented via ADOT AWS SDK instrumentation libraries. These services do not emit their own segments; they appear as Inferred Segments from subsegments in the calling service.
- Verification:
  - API Gateway: AWS CLI `aws apigateway get-stage --rest-api-id <id> --stage-name <name>` — check `tracingEnabled: true`.
  - Lambda: `aws lambda get-function-configuration --function-name <name>` — check `TracingConfig.Mode: Active`.
  - Sampling rules: `aws xray get-sampling-rules`.
  - ECS task: inspect task definition for ADOT sidecar container definition.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-instrumenting-your-app.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-services-lambda.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html (2026-08-30); https://docs.aws.amazon.com/AmazonECS/latest/developerguide/trace-data.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern 2 — Centralized Sampling Rule Configuration**
- Pillar Alignment: OPS04-BP05 (Operational Excellence); Cost Optimization Pillar (COST07 — Optimize over time)
- Why: The default sampling rule (reservoir=1, rate=5%) avoids unbounded cost. Defining rules locally in SDK config files causes each fleet instance to run its own independent reservoir, multiplying effective sampling rates across the fleet. Centralized rules are evaluated per the X-Ray service, not per instance.
- AWS Services: AWS X-Ray (sampling rule store), API Gateway (applies rule for entry point), ADOT Collector (reads remote sampling rules from X-Ray)
- Architecture Decision:
  - Define all sampling rules exclusively in the X-Ray console (or via `aws xray create-sampling-rule` / `update-sampling-rule`).
  - Remove any local sampling rule JSON files from SDK or ADOT Collector config.
  - Set a default low-rate rule (e.g., Reservoir=5, Rate=0.05) as the catch-all.
  - Add higher-priority rules (lower Priority number) for critical routes (e.g., checkout API: Reservoir=50, Rate=0.20).
  - Set health-check endpoint rules to Reservoir=0, Rate=0.01 or Rate=0.00 to suppress noise.
  - Optionally configure `SamplingRateBoost` (`MaxRate`, `CooldownWindowMinutes`) to automatically raise sampling during detected anomalies.
  - For full-fidelity debugging: add a temporary, highest-priority rule scoped by URL path and method with Rate=1.0. Delete after debugging is complete.
- Verification: `aws xray get-sampling-rules` — confirm no local rule JSON files exist in application or collector config.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern 3 — Trace Context Propagation Across All Service Boundaries**
- Pillar Alignment: OPS08-BP03 (Operational Excellence — Analyze Workload Traces; Risk: Medium); REL — Reliability
- Why: If any service fails to forward the trace header, downstream segments cannot attach to the parent trace, producing disconnected nodes in the service map and orphaned segments. The sampling decision is parent-based; a lost header resets the decision.
- AWS Services: Amazon API Gateway, AWS Lambda, Amazon SQS, Amazon SNS, ADOT Collector, X-Ray SDK/ADOT SDK
- Architecture Decision:
  - Synchronous HTTP flows: API Gateway propagates `X-Amzn-Trace-Id` automatically. All downstream HTTP clients must use ADOT-instrumented or X-Ray-instrumented clients.
  - For ADOT: configure the X-Ray Propagator in OTel SDK config alongside the W3C Trace Context propagator. Use ADOT Collector v0.34.0+ (includes AWS X-Ray Exporter v0.86.0+) for W3C trace ID acceptance by X-Ray.
  - Async SQS → Lambda: rely on automatic X-Ray trace linking — do not manually inject trace headers into SQS message attributes.
  - Never use raw HTTP clients without wrapping in the ADOT or X-Ray instrumented client.
  - Remove the `X-Amzn-Trace-Id` header from responses to prevent end-users from reading internal trace IDs. Optionally strip it from incoming requests to prevent end-user injection of sampling decisions.
- Verification: X-Ray Service Map — check for disconnected nodes or services with no upstream edge. These indicate header propagation failures.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern 4 — CloudWatch Logs / Metrics Correlation via Application Signals**
- Pillar Alignment: OPS04-BP05 (Operational Excellence — Correlated observability)
- Why: Without trace ID injection into application logs, correlating a specific trace to a log line requires manual grep across time-range — unreliable and slow. Application Signals injects `trace_id`, `span_id`, and `trace_flags` into logs via OTel context automatically.
- AWS Services: CloudWatch Application Signals, CloudWatch Logs, AWS X-Ray, ADOT
- Architecture Decision:
  - Enable CloudWatch Application Signals on all production services.
  - Java (Spring Boot): add `logging.pattern.level: trace_id=%mdc{trace_id} span_id=%mdc{span_id} trace_flags=%mdc{trace_flags} %5p` to `application.yml`.
  - Python: set environment variable `OTEL_PYTHON_LOG_CORRELATION=true`.
  - Node.js: configure Pino, Winston, or Bunyan OTel auto-instrumentation.
  - ECS and EKS: configure logger to write to stdout so Container Insights can collect logs.
  - EC2: set additional environment variable per Application Signals documentation.
  - Verify the CloudWatch console Trace Map node includes a "View logs" link to the correlated CloudWatch Logs stream.
- Verification: CloudWatch console → Trace Map → select a node → confirm "View logs" link is available and returns log lines containing `trace_id` fields.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Application-Signals-TraceLogCorrelation.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern 5 — KMS Encryption at Rest for Regulated Workloads**
- Pillar Alignment: Security Pillar — SEC08-BP02 (Enforce encryption at rest)
- Why: Default X-Ray encryption uses an AWS-owned key with no CloudTrail audit visibility. For regulated workloads (GDPR, PCI-DSS, HIPAA), auditors require demonstrable key management controls.
- AWS Services: AWS X-Ray, AWS KMS, AWS CloudTrail, AWS IAM
- Architecture Decision:
  - For audit-level compliance: configure AWS managed key (`aws/xray`) via `aws xray put-encryption-config --type KMS --key-id alias/aws/xray`. CloudTrail records every key use event. Cost: KMS API call pricing.
  - For full key control (recommended for regulated workloads): create a symmetric CMK. Grant X-Ray service `kms:GenerateDataKey` and `kms:Decrypt` via the key policy. Restrict `xray:PutEncryptionConfig` via SCP or IAM deny to a break-glass role only.
  - IAM requirements: configuring identity needs `kms:CreateGrant` + `kms:DescribeKey` on the CMK + `xray:PutEncryptionConfig`. Identities viewing encrypted traces need `kms:Decrypt`.
  - Constraints: X-Ray does NOT support asymmetric KMS keys. CMK can reside in a different account. EventBridge (used for Insights notifications) does not support CMK encryption.
  - During encryption config changes: X-Ray may use both old and new settings transiently. Existing data is not re-encrypted.
- Verification: `aws xray get-encryption-config` — confirm `Type: KMS` and `KeyId` matches the expected CMK ARN. CloudTrail — confirm `xray.amazonaws.com` appears as a kms:GenerateDataKey caller.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern 6 — Least-Privilege IAM for Daemon / ADOT Collector**
- Pillar Alignment: Security Pillar — SEC02 (Manage identities for people and machines)
- Why: Granting `xray:*` to compute roles creates a confused-deputy risk — a compromised Lambda or ECS task role could read all traces, modify sampling rules, or change encryption settings.
- AWS Services: AWS IAM, AWS X-Ray, AWS Lambda, Amazon ECS, Amazon EC2
- Architecture Decision:
  - Attach only `AWSXRayDaemonWriteAccess` (ARN: `arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess`) to all compute execution roles.
  - This policy grants exactly: `xray:PutTraceSegments`, `xray:PutTelemetryRecords`, `xray:GetSamplingRules`, `xray:GetSamplingTargets`, `xray:GetSamplingStatisticSummaries` on Resource: `*`.
  - For ECS ADOT task role, additionally grant: `ssm:GetParameters`, `logs:PutLogEvents`, `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:DescribeLogStreams`, `logs:DescribeLogGroups`, `logs:PutRetentionPolicy`.
  - Reserve `AWSXrayFullAccess` for designated observability administrator roles only (not compute roles).
  - Attachment per compute type: EC2 → instance profile role; ECS → task IAM role (distinct from task execution role); Lambda → function execution role; Elastic Beanstalk → default instance profile.
- Verification: IAM Access Analyzer. AWS Config: detect compute roles with `xray:*` attached. `aws iam list-attached-role-policies --role-name <compute-role>`.
- Source: https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSXRayDaemonWriteAccess.html (2026-08-30); https://docs.aws.amazon.com/AmazonECS/latest/developerguide/trace-data.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern 7 — ADOT Collector Sidecar on ECS**
- Pillar Alignment: OPS04-BP05 (Operational Excellence); Reliability — decouple trace collection from application logic
- Why: "Amazon ECS integrates with AWS Distro for OpenTelemetry to collect trace data from your application. Amazon ECS uses an AWS Distro for OpenTelemetry sidecar container to collect and route trace data to AWS X-Ray." (AWS ECS documentation, 2026-08-30). This is the recommended migration path away from the X-Ray Daemon (maintenance mode as of 2026-02-25).
- AWS Services: Amazon ECS Fargate, ADOT Collector (sidecar), AWS X-Ray, Amazon ECR Public (`aws-observability/aws-otel-collector`)
- Architecture Decision:
  - Define an ECS task definition with two containers:
    1. Application container: instrumented with ADOT SDK; exports OTel telemetry to `http://localhost:4317` (gRPC) or `http://localhost:4318` (HTTP/protobuf).
    2. ADOT Collector sidecar: image `public.ecr.aws/aws-observability/aws-otel-collector:latest`; receives telemetry and exports to X-Ray.
  - Specify `taskRoleArn` in the task definition (distinct from task execution role) with `AWSXRayDaemonWriteAccess` plus SSM and CloudWatch Logs permissions.
  - Do not use the legacy X-Ray Daemon sidecar image for new task definitions.
- Verification: `aws ecs describe-task-definition --task-definition <name>` — confirm ADOT Collector container is present; confirm `taskRoleArn` is set and has required permissions.
- Source: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/trace-data.html (2026-08-30)

**Confidence: 🟢**

---

### ⚠️ Architectural Decisions

**Decision Point 1 — Instrumentation SDK: X-Ray SDK vs ADOT vs Vanilla OpenTelemetry**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | X-Ray SDK (maintenance mode as of 2026-02-25) | AWS X-Ray | Simplest migration path for existing AWS-only apps already using X-Ray SDK | No new features; security patches only; AWS-proprietary format; local sampling rules multiply across instances | Only for existing apps where migration cost exceeds benefit in the near term |
  | ADOT (AWS Distro for OpenTelemetry) | X-Ray, CloudWatch, AMP, OpenSearch | AWS-tested OTel distribution; pre-packaged AWS-specific exporters; X-Ray remote sampling supported; AWS support SLA | Lags upstream OTel releases slightly; more configuration than X-Ray SDK | New AWS-hosted applications needing OTel standards with AWS-optimized defaults |
  | Vanilla OpenTelemetry SDK | Any OTLP backend | Vendor-agnostic; portable across cloud providers; full OTel ecosystem; W3C trace context default | Requires manual AWS resource detector configuration; X-Ray remote sampling not available in all languages | Multi-cloud or hybrid environments; organizations standardizing on OTel across providers |

- Cost Profile: All three options incur the same X-Ray trace ingestion cost ($5.00/M traces recorded, $0.50/M retrieved beyond free tier). ADOT and vanilla OTel have no additional SDK licensing cost. ADOT Collector running as ECS sidecar incurs sidecar container compute cost.
- Lock-in Assessment: X-Ray SDK is AWS-proprietary — highest lock-in. ADOT uses OTel wire format with AWS-specific exporters — medium lock-in (exporters are pluggable). Vanilla OTel — lowest lock-in; changing the backend requires only an exporter config change.
- Architect Instruction: "Ask 'Is this a net-new service or an existing X-Ray SDK instrumented service?' when evaluating instrumentation approach. If net-new: mandate ADOT. If existing: evaluate migration cost and set a timeline."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30)

---

**Decision Point 2 — Trace Analysis: X-Ray Sampled Traces vs CloudWatch Transaction Search**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | X-Ray Console (sampled traces) | AWS X-Ray | Lower cost; service map visualization; Insights anomaly detection; filter expressions | Misses unsampled requests; cannot debug specific rare user events | High-volume applications where statistical sampling is sufficient for p50/p95 analysis |
  | CloudWatch Transaction Search (100% spans) | CloudWatch Logs (`aws/spans` log group) | Complete span capture; all span attributes searchable; up to 10,000 spans/trace; full OTel semantic convention support; CloudWatch Logs capabilities (metric filters, data masking) | CloudWatch Logs ingestion cost in addition to X-Ray costs; requires head sampling = 100% for full coverage; significantly increases costs at high volume | Debugging specific customer tickets; mission-critical APIs; compliance requiring full trace retention; p99 latency debugging |

- Cost Profile: X-Ray: $5.00/M traces recorded + $0.50/M retrieved (beyond free tier: 100K recorded, 1M retrieved per month). Transaction Search: CloudWatch Logs ingestion pricing per GB (see cloudwatch/pricing). Both costs apply simultaneously if Transaction Search is enabled alongside X-Ray trace storage.
- Lock-in Assessment: Both are AWS-specific. Transaction Search spans are stored in CloudWatch Logs and can be exported via Subscription Filters to S3 or Kinesis for multi-backend archiving.
- Architect Instruction: "Ask 'Do we need to debug specific individual user requests, or is statistical trace sampling sufficient?' when choosing between X-Ray trace storage and Transaction Search."
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-spans.html (2026-08-30)

---

**Decision Point 3 — Sampling Strategy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Fixed-rate only (e.g., 5%) | AWS X-Ray | Simple configuration | Cost unbounded at high volume; misses rare events | Low-volume services only |
  | Reservoir + fixed-rate (recommended default) | AWS X-Ray | Bounded base cost; guaranteed at least N traces/sec floor | Still misses unsampled requests | Most production applications |
  | Anomaly-driven boost (SamplingRateBoost) | AWS X-Ray | Automatically increases sampling during anomaly detection; configurable MaxRate and CooldownWindowMinutes | Requires explicit configuration | Services with sporadic error spikes needing auto-diagnosis |
  | Transaction Search 100% indexing | CloudWatch Logs | Complete span capture for all requests; customer-level debugging | CloudWatch Logs ingestion cost; highest cost option | Customer-facing APIs requiring per-request debugging |

- Cost Profile: Reservoir + fixed-rate is the most cost-effective for most workloads. 100% indexing via Transaction Search has unbounded cost growth with traffic volume.
- Lock-in Assessment: X-Ray sampling rules are AWS-proprietary. ADOT supports X-Ray remote sampling (reads rules from X-Ray API). Vanilla OTel uses OTel-native sampling that does not read X-Ray rules.
- Architect Instruction: "Ask 'What is the maximum acceptable monthly X-Ray cost?' when defining sampling rules. Use this to calculate the required reservoir and fixed-rate combination for the expected request volume."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html (2026-08-30)

---

**Decision Point 4 — Collector Choice: Self-managed OTel Collector vs ADOT Collector vs CloudWatch Agent**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Self-managed OpenTelemetry Collector | AWS X-Ray (via awsxray exporter) | Full control; tail sampling support; multi-backend export; latest OTel version | Operational overhead; no AWS support SLA | Teams with OTel expertise; tail sampling required for complex trace-based sampling |
  | ADOT Collector | AWS X-Ray, CloudWatch, AMP | AWS-tested and supported; pre-configured AWS exporters; AWS-managed Lambda layers | Lags upstream OTel releases | AWS-only workloads needing OTel with AWS support and Lambda managed layers |
  | CloudWatch Agent (v1.300025.0+) | AWS X-Ray, CloudWatch Metrics, CloudWatch Logs | Unified agent for metrics + logs + traces; single agent per host; AWS-managed | No tail sampling; less flexibility than full OTel Collector | Environments already running CloudWatch Agent; minimize sidecar count; EC2 workloads |

- Cost Profile: All options have the same X-Ray trace ingestion cost. ADOT and CloudWatch Agent are free software; operational cost is EC2/ECS compute for the collector process. Self-managed OTel Collector requires operator time for upgrades and config management.
- Lock-in Assessment: Self-managed OTel Collector has lowest lock-in (standard OTel config). ADOT Collector uses OTel config format — medium lock-in. CloudWatch Agent has highest lock-in (AWS-specific config format).
- Architect Instruction: "Ask 'Is tail sampling required?' when selecting the collector. If yes, self-managed OTel Collector is the only option — neither ADOT nor CloudWatch Agent support tail sampling."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30)

---

### 🚫 Anti-Patterns

**Anti-Pattern 1 — Tracing 100% of Requests at Scale (Sampling Misconfiguration)**
- Risk Level: HIGH
- Why: Beyond the free tier, X-Ray charges $5.00 per million traces recorded and $0.50 per million retrieved. Recording 100% of traces in production at high volume drives unbounded cost. When sampling rules are defined locally (in-code) rather than centrally, each instance runs its own independent reservoir, causing the effective sampling rate to multiply across fleet members. WAF Pillar violations: Cost Optimization, Performance Efficiency.
- ❌ Wrong:
  ```json
  { "Reservoir": 10000, "FixedRate": 1.0 }
  ```
  Local JSON sampling rule file committed per Lambda function, combined with no X-Ray console centralized rules. Result: each Lambda execution environment runs its own reservoir, effectively tracing all requests.
- ✅ Correct: Define sampling rules centrally in the X-Ray console. For health-check endpoints: Reservoir=0, Rate=0.01. For state-modifying endpoints: Reservoir=10–50, Rate=0.10–0.20. For debugging: add a temporary highest-priority rule scoped by URL path and method with Rate=1.0, then delete it after debugging is complete.
- Detection: Monitor Cost Explorer for X-Ray charges trending above expected baseline. Review X-Ray console Sampling page "Trend" column for high match rates. Search codebase for local sampling rule JSON files or SDK sampling config.
- Impact: Cost overrun — unbounded X-Ray charges as traffic scales. No explicit data breach or outage risk, but cost shock can trigger resource restrictions.
- Source: https://aws.amazon.com/xray/pricing/ (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html (2026-08-30)

**Confidence: 🟢**

---

**Anti-Pattern 2 — Logging PII / Secrets into Trace Annotations**
- Risk Level: CRITICAL
- Why: Annotations are indexed key-value pairs visible to any IAM principal with `xray:GetTraceSummaries`, `xray:BatchGetTraces`, or `AWSXrayReadOnlyAccess`. There is no field-level access control within annotations. Sensitive data in annotations is searchable by all trace read-access principals. WAF Pillar violation: Security.
- ❌ Wrong (Python X-Ray SDK):
  ```python
  segment.put_annotation("user_email", request.user.email)
  segment.put_annotation("api_key", request.headers["X-Api-Key"])
  ```
- ✅ Correct: Use hashed or tokenized identifiers for correlation (e.g., `put_annotation("user_id_hash", hash(user_id))`). Use `put_metadata()` (non-indexed) for debug data. Apply KMS encryption (CMK) so that trace data at rest is protected. For OTel: use `aws.xray.annotations` attribute list sparingly with non-sensitive keys only.
- Detection: Grep codebase for `put_annotation` calls and validate that values are not derived from request headers, user objects, authentication tokens, or PII fields. Audit X-Ray annotations in the console for sensitive patterns.
- Impact: PII/credential exposure to any IAM principal with X-Ray read access. GDPR data subject exposure. PCI-DSS credential in-scope data leakage. Compliance violation.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html (2026-08-30)

**Confidence: 🟢**

---

**Anti-Pattern 3 — Missing Trace Context Propagation (Broken Traces)**
- Risk Level: HIGH
- Why: If any service fails to forward the `X-Amzn-Trace-Id` header (or W3C `traceparent` for ADOT), downstream segments cannot attach to the parent trace. This produces disconnected nodes in the service map, orphaned segments, and a reset of the parent-based sampling decision. WAF Pillar violations: Operational Excellence, Reliability.
- ❌ Wrong:
  ```python
  # Raw HTTP call without X-Ray/ADOT instrumented client
  import requests
  response = requests.get("https://internal-service/api")

  # Publishing to SQS without trace context in message attributes (manual approach)
  sqs.send_message(QueueUrl=url, MessageBody=body)  # no trace context forwarding
  ```
- ✅ Correct: Use ADOT-instrumented AWS SDK clients or X-Ray instrumented HTTP clients for all downstream calls. For async SQS → Lambda flows, rely on X-Ray automatic trace linking (do not manually manage trace headers in message attributes). For ADOT, configure the X-Ray Propagator alongside the W3C Trace Context propagator in the OTel SDK config.
- Detection: X-Ray Service Map — look for disconnected nodes or services appearing with no upstream edge. These indicate header propagation failures at a specific service boundary.
- Impact: No end-to-end visibility. Inability to correlate failures across service boundaries. Incorrect root-cause attribution. Sampling decision reset at propagation gap.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30)

**Confidence: 🟢**

---

**Anti-Pattern 4 — No KMS Encryption for Regulated Trace Data**
- Risk Level: MEDIUM-HIGH
- Why: Default encryption uses an AWS-owned key with no CloudTrail audit trail visibility. For regulated workloads, compliance frameworks (PCI-DSS, HIPAA, SOC 2) require the ability to audit, rotate, or revoke encryption keys for data at rest. WAF Pillar violation: Security (SEC08-BP02).
- ❌ Wrong: Trace data stored with default AWS-owned encryption. No CloudTrail key-use events are generated. No ability to revoke access to historical trace data. No key rotation control.
- ✅ Correct: Configure AWS managed key (`aws/xray`) for audit-level compliance (CloudTrail records key use). For full control, create a symmetric CMK with rotation enabled and a key policy granting X-Ray `kms:GenerateDataKey` and `kms:Decrypt`. Restrict `xray:PutEncryptionConfig` to a break-glass role only. Note: X-Ray does not support asymmetric KMS keys.
- Detection: `aws xray get-encryption-config` — check `Type` is `KMS`, not `NONE`. AWS Config rule: detect X-Ray encryption type = NONE for workloads in regulated environments.
- Impact: Compliance violation in regulated industries. No key-revocation ability if trace data is compromised.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html (2026-08-30)

**Confidence: 🟢**

---

**Anti-Pattern 5 — Overly Broad IAM for Trace Ingestion (xray:*)**
- Risk Level: HIGH
- Why: `AWSXrayFullAccess` grants `xray:*`, which includes the ability to modify sampling rules, create/delete groups, read all traces, and change encryption settings. Attaching this to a Lambda execution role or ECS task role creates a confused-deputy risk — a compromised role can exfiltrate all trace data or sabotage observability. WAF Pillar violation: Security.
- ❌ Wrong:
  ```json
  { "Action": "xray:*", "Effect": "Allow", "Resource": "*" }
  ```
  Attached to a Lambda function execution role or ECS task IAM role.
- ✅ Correct: Attach only `AWSXRayDaemonWriteAccess` to compute execution roles. Reserve `AWSXrayFullAccess` for designated observability administrator roles only. For ECS ADOT sidecar, create a dedicated task IAM role with the explicit minimal permission set (see Pattern 6).
- Detection: IAM Access Analyzer — detect policies with `xray:*` attached to compute roles. AWS Config custom rule: Lambda functions or ECS task roles with `xray:*` action. `aws iam simulate-principal-policy`.
- Impact: Compromised compute role can read all trace data (PII/secrets if improperly annotated), alter sampling rules (blind the observability plane), or change encryption settings (disable CMK, removing audit capability).
- Source: https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html (2026-08-30)

**Confidence: 🟢**

---

**Anti-Pattern 6 — Ignoring Trace Retention Limits and Cost Controls**
- Risk Level: MEDIUM
- Why: X-Ray trace data is retained for only 30 days with no configurable longer retention (and no official export mechanism confirmed). X-Ray Groups are billed by retrieved traces matching filter expressions. Without cost controls, charges grow unchecked. WAF Pillar violations: Cost Optimization, Operational Excellence.
- ❌ Wrong: No sampling rules configured (all at 100%), no AWS Budgets alert for X-Ray charges, no review of active X-Ray Groups, no awareness that Transaction Search spans are billed separately under CloudWatch Logs pricing.
- ✅ Correct: Set sampling rules with appropriate reservoir and rate per route. Create AWS Budgets alert for X-Ray service charges. Audit active Groups quarterly — remove unused groups. For long-term trace retention beyond 30 days: [IRRESOLVABLE — no official export mechanism confirmed; this gap remains open].
- Detection: Cost Explorer filtered by X-Ray service. CloudWatch metric for X-Ray group trace counts. `aws xray get-groups` — inventory all active groups.
- Impact: Cost overrun. Trace data loss after 30 days with no recovery path if long-term retention was required.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html (2026-08-30); https://aws.amazon.com/xray/pricing/ (2026-08-30)

**Confidence: 🟢**

**Anti-Pattern 7 — Using X-Ray Active Tracing with HTTP APIs on API Gateway**
- Risk Level: HIGH
- Why: X-Ray active tracing is only supported for API Gateway REST APIs (Regional, edge-optimized, and private endpoint types). HTTP APIs and WebSocket APIs are NOT supported. Attempting to enable X-Ray tracing on an HTTP API stage either silently does nothing or the setting is unavailable. Engineers who migrate from REST to HTTP APIs lose trace visibility without warning.
- ❌ Wrong: Enable X-Ray tracing on an API Gateway HTTP API stage, expecting trace segments to appear on the service map.
- ✅ Correct: Use API Gateway REST API stages for workloads requiring X-Ray distributed tracing. If HTTP API is required for other reasons, instrument at the compute layer (Lambda/ECS) instead of relying on API Gateway active tracing.
- Detection: `aws apigateway get-stages --rest-api-id <id> --query 'item[*].{stageName:stageName,xrayTracing:tracingEnabled}'`. For HTTP APIs: `aws apigatewayv2 get-stages --api-id <id>` — absence of a tracing field confirms HTTP APIs do not expose an X-Ray tracing toggle.
- Impact: Zero X-Ray service map node for the API Gateway layer; blind spot at the entry point; broken trace chain for HTTP API workloads.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html (2026-08-31)

**Confidence: 🟢**

---

**Anti-Pattern 8 — Lambda Left in PassThrough Tracing Mode**
- Risk Level: HIGH
- Why: Lambda's default tracing mode is `PassThrough`, not passive tracing. In PassThrough mode, Lambda forwards the `X-Amzn-Trace-Id` header to downstream services but does NOT automatically send trace segments to X-Ray. If no upstream tracing header is present, Lambda generates one with a decision NOT to sample — producing zero traces.
- ❌ Wrong: Deploy Lambda functions without explicitly setting `TracingConfig: Mode: Active`. Assume that Lambda will automatically trace when called from an instrumented service.
- ✅ Correct: Enable Active tracing on every Lambda function that must produce traces:
  ```bash
  aws lambda update-function-configuration --function-name my-function --tracing-config Mode=Active
  ```
  CloudFormation:
  ```yaml
  TracingConfig:
    Mode: Active  # AWS::Lambda::Function
  # OR
  Tracing: Active  # AWS::Serverless::Function (SAM)
  ```
  When Active tracing is enabled via the Lambda console, Lambda automatically adds `AWSXRayDaemonWriteAccess` permissions to the execution role.
- Detection: `aws lambda list-functions --query 'Functions[?TracingConfig.Mode==\`PassThrough\`].FunctionName'` — returns all Lambda functions in PassThrough mode that may not be sending traces.
- Impact: Zero X-Ray trace data from Lambda functions; invisible compute layer in the service map; debugging requires manual log correlation.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-08-31)

**Confidence: 🟢**

---

**Anti-Pattern 9 — Collector-less ADOT with 100% Sampling (Cost Shock)**
- Risk Level: HIGH
- Why: When sending traces directly to the X-Ray OTLP endpoint WITHOUT an ADOT Collector, the ADOT SDK defaults to `parentbased_always_on` sampling — which samples **100% of traces**. This results in up to **20x higher ingestion volume and costs** compared to the recommended 5% default sampling rate.
- ❌ Wrong: Configure ADOT SDK to export directly to `https://xray.{region}.amazonaws.com/v1/traces` without an ADOT Collector and without setting an explicit sampler. Accept the default `parentbased_always_on` behavior in production.
- ✅ Correct: Either (a) deploy an ADOT Collector with centralized X-Ray sampling rules to control sampling before export, or (b) explicitly set the OTel sampler via `OTEL_TRACES_SAMPLER=parentbased_traceidratio` and `OTEL_TRACES_SAMPLER_ARG=0.05` when using collector-less export.
- Detection: Monitor AWS Cost Explorer for X-Ray trace recording charges. If X-Ray costs grow proportionally to total traffic (not to the expected sampled fraction), the sampling configuration is the cause.
- Impact: Unbudgeted cost; up to 20x the expected X-Ray bill; no service quality improvement over properly sampled traces for most debugging scenarios.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLP-UsingADOT.html (2026-08-31)

**Confidence: 🟡**

## Cloud-Native Design Patterns

**Pattern: ADOT Managed Lambda Layer with X-Ray Auto-Instrumentation**
- Category: Scalability / Observability
- Problem: Lambda functions need distributed tracing without bundling an SDK into the deployment package, and without deploying a separate daemon process. Cold start impact must be minimized.
- Solution on AWS: Use the AWS-managed ADOT Lambda Layer for the target runtime (Go, Java, JavaScript, Python, .NET). Enable Active Tracing on the Lambda function. The layer intercepts SDK calls and exports OTel spans to X-Ray via the CloudWatch OTel Endpoint — no separate collector process required.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Operational simplicity | No sidecar or daemon deployment | Layer version must be updated manually when ADOT releases patches |
  | Cold start | Layer is AWS-managed, optimized for Lambda | Auto-instrumentation agents add some cold-start overhead |
  | Feature currency | AWS-managed updates | ADOT may lag upstream OTel releases |
  | Cost | X-Ray trace ingestion cost only | CloudWatch OTel Endpoint eliminates collector compute cost |

- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-lambda.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern: ECS Fargate Sidecar Observability Pipeline (ADOT Collector)**
- Category: Communication / Observability
- Problem: ECS Fargate tasks cannot run host-level processes. Tracing requires a per-task collection endpoint that receives OTel telemetry from the application container and forwards to X-Ray without host access.
- Solution on AWS: Define an ADOT Collector sidecar container in the ECS task definition. The application container sends OTel spans to `localhost:4317`. The ADOT Collector forwards to X-Ray. The task IAM role provides write access to X-Ray and read access to SSM for Collector config.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | No host access required | Works on Fargate | Sidecar adds resource allocation to task definition |
  | Centralized config | ADOT Collector config in SSM Parameter Store | SSM GetParameters call per task start |
  | Multi-backend export | Single ADOT Collector can export to X-Ray + AMP + CloudWatch | Collector is a single point of failure per task |
  | Decoupled collection | Application code is transport-agnostic | ADOT version lag relative to upstream OTel |

- Source: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/trace-data.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern: Cross-Account Trace Aggregation via CloudWatch OAM**
- Category: Communication / Multi-account Observability
- Problem: In a multi-account AWS organization, trace data is fragmented across accounts. Operators in a central observability account cannot see the full request path spanning multiple source accounts.
- Solution on AWS: Configure CloudWatch Observability Access Manager (OAM). Designate a monitoring account. Link each source account. X-Ray copies traces from source accounts to the monitoring account's X-Ray. Operators access CloudWatch Trace Map in the monitoring account to see the aggregated service map with filter expressions supporting account ID filtering.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Centralized visibility | Single pane of glass across up to 5 monitoring accounts | Copies to 2nd–5th monitoring accounts charged at standard X-Ray pricing to source account |
  | First monitoring account | Free cross-account copy | Additional monitoring accounts incur additional cost |
  | Operational simplicity | No custom aggregation pipeline | Supports up to 5 monitoring accounts per source account |
  | Filter by account | Filter expressions support account ID | — |

- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-crossaccount.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern: X-Ray Insights + EventBridge Automated Incident Pipeline**
- Category: Resilience / Operational Excellence
- Problem: In a microservice mesh, fault propagation from one failing downstream service triggers error increases across multiple upstream services simultaneously. Identifying the original root-cause service manually from the service map is time-consuming.
- Solution on AWS: Enable X-Ray Insights per X-Ray Group. X-Ray Insights applies statistical modeling to predict expected fault rates. When an anomaly is detected, it creates an Insight identifying the root-cause node. Amazon EventBridge delivers the Insight event (`source: aws.xray`, `detail-type: AWS X-Ray Insight Update`) to an SNS topic, Lambda function, or SQS queue. The downstream handler creates a PagerDuty/OpsGenie/Jira incident automatically.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Automated detection | No manual dashboard monitoring required | Insights must be enabled per Group — requires explicit configuration |
  | Root-cause deduplication | Single Insight per fault cascade, not per affected service | — |
  | EventBridge delivery | Native AWS integration | Best-effort delivery — not guaranteed; not suitable for sole alerting mechanism |
  | CMK encryption | N/A | EventBridge does not support CMK for Insights events |

- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-insights.html (2026-08-30)

**Confidence: 🟢**

---

**Pattern: SQS-Lambda Trace Linking (Event Source Trace Propagation)**
- Category: Communication / Async Trace Propagation
- Problem: SQS decouples producers and consumers asynchronously. Standard trace propagation does not work across SQS boundaries — the consumer Lambda function receives no parent trace context from the queue and cannot build a continuous end-to-end trace.
- Solution on AWS: X-Ray auto-links SQS producer traces to Lambda consumer traces. When the X-Ray SDK (or ADOT with AWS SDK auto-instrumentation) is used, the producer's trace ID is embedded in the SQS message attribute. Lambda reads the attribute and links traces at segment level. Limits: maximum 20 producer traces linked per segment; maximum 100 trace links per trace. If the SQS batch size or fanout exceeds these limits, oversampling mitigation is available in Java, Node.js, Python, Go, and .NET X-Ray SDKs to prevent link overflow.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | End-to-end visibility | Connects producer and consumer traces across async boundary | Linked traces are separate trace documents; X-Ray console shows them as linked, not merged |
  | Limits | Automatic within limits (20 traces/segment, 100 links/trace) | Link overflow silently drops additional linkage — requires oversampling mitigation config |
  | SDK support | All major runtimes: Java, Node.js, Python, Go, .NET | Not automatic without ADOT or X-Ray SDK instrumentation on producer |

- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-sqs.html (2026-08-31)

**Confidence: 🟢**

## Security Architecture

**Encryption at Rest — X-Ray Trace Data**
- AWS Services: AWS X-Ray, AWS KMS, AWS CloudTrail, AWS IAM
- Architecture: X-Ray always encrypts traces and service graph data at rest. Three tiers: (1) Default (AWS-owned key, no audit visibility, free); (2) AWS managed key `aws/xray` — CloudTrail records every kms:GenerateDataKey and kms:Decrypt call, pay per KMS API call; (3) Customer managed CMK — full key control (policy, rotation, cross-account), pay for key storage + key use. The CMK may reside in a different account. X-Ray does NOT support asymmetric KMS keys. If X-Ray cannot access the configured key, it stops storing data. Existing data is not re-encrypted when the encryption config changes.
- IAM requirements for CMK: configuring identity needs `kms:CreateGrant` + `kms:DescribeKey` + `xray:PutEncryptionConfig`. Identities viewing encrypted traces need `kms:Decrypt`. To prevent unauthorized config changes: deny `xray:PutEncryptionConfig` via SCP or IAM deny except for a break-glass role.
- Compliance Alignment: SEC08-BP02 (WAF Security Pillar — Enforce encryption at rest). Supports PCI-DSS Requirement 3.5, HIPAA Administrative Safeguards, SOC 2 CC6.7.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html (2026-08-30)

**Confidence: 🟢**

---

**Identity-Based Access Control — X-Ray IAM**
- AWS Services: AWS IAM, AWS X-Ray
- Architecture: X-Ray uses identity-based policies exclusively; it does not support resource-based policies. Three managed policies cover the main roles: `AWSXRayDaemonWriteAccess` (compute/collector write-only), `AWSXrayReadOnlyAccess` (read all traces, service graphs, insights, sampling data), `AWSXrayFullAccess` (xray:* — administrator only). Compute resources (Lambda execution roles, ECS task roles, EC2 instance profiles) must use only `AWSXRayDaemonWriteAccess`. ECS ADOT task roles additionally need SSM and CloudWatch Logs permissions. Elastic Beanstalk includes X-Ray write in its default instance profile.
- Compliance Alignment: SEC02 (WAF Security Pillar — Manage identities for people and machines). SEC03 (Manage permissions). Supports PCI-DSS Requirement 7 (Restrict access to system components).
- Source: https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSXRayDaemonWriteAccess.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html (2026-08-30)

**Confidence: 🟢**

---

**Data Protection — Avoiding Sensitive Data in Traces**
- AWS Services: AWS X-Ray, AWS KMS
- Architecture: X-Ray automatically records: hostname/IP, HTTP method, URL path, user agent, response status, and content length. Segment documents are up to 64 kB. Annotations are indexed and searchable (up to 50 per trace) — never store PII or secrets here. Metadata is non-indexed and not searchable — acceptable for sanitized debug data. Applications should remove or strip the `X-Amzn-Trace-Id` response header to prevent end-user visibility into internal trace IDs. The `X-Forwarded-For` client IP can be forged and must not be trusted for security decisions. SDK-level PII filtering or segment sanitization hooks: [UNVERIFIED — no official X-Ray documentation page confirmed specific SDK sanitization APIs].
- Compliance Alignment: SEC09 (WAF Security Pillar — Protect data in transit and at rest). GDPR Article 25 (Data protection by design). PCI-DSS Requirement 3 (Protect stored account data).
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html (2026-08-30)

**Confidence: 🟢 (pattern); 🔴 (SDK sanitization hooks — UNVERIFIED)**

---

**Cross-Account Observability Security**
- AWS Services: AWS X-Ray, CloudWatch Observability Access Manager (OAM), AWS IAM
- Architecture: Cross-account trace sharing uses CloudWatch OAM. Source accounts link to monitoring accounts. Traces are copied (not moved) from source to monitoring account X-Ray. Filter expressions in the monitoring account support filtering by account ID. Access control in the monitoring account is governed by IAM policies on that account — source account IAM does not control what monitoring account principals can see. First monitoring account copy is free; additional copies (2nd–5th) are charged at standard X-Ray pricing to the source account.
- Compliance Alignment: SEC03 (Manage permissions — ensure least privilege across account boundaries).
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-crossaccount.html (2026-08-30)

**Confidence: 🟢**

**VPC Endpoints (PrivateLink)**
- AWS Services: AWS X-Ray, AWS PrivateLink
- Architecture: X-Ray supports AWS PrivateLink interface VPC endpoints. Endpoint service name: `com.amazonaws.{region}.xray`. Configure a VPC Interface Endpoint for X-Ray to allow ECS tasks, EC2 instances, and Lambda functions in private subnets to send trace data to X-Ray without routing through the public internet. FIPS endpoints available in US commercial regions (suffix `-fips`) and both GovCloud regions.
- Compliance Alignment: Network isolation requirement for regulated workloads (HIPAA, PCI-DSS).
- Source: https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-privatelink-support.html (2026-08-31); https://docs.aws.amazon.com/general/latest/gr/xray.html (2026-08-31)

**Confidence: 🟢**

**CloudTrail Audit Logging for X-Ray**
- AWS Services: AWS X-Ray, AWS CloudTrail
- Architecture: As of March 2024, X-Ray logs the following events to CloudTrail: Data events: `PutTraceSegments`, `GetTraceSummaries`, `BatchGetTraces`. Management event: `GetSamplingStatisticSummaries`. Enable CloudTrail data event logging for X-Ray in regulated environments to audit who is sending and reading trace data.
- Compliance Alignment: Audit trail requirements in NIST 800-53 AU-2 (Audit Events) and SOC 2 CC7.2.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/document-history.html (2026-08-31)

**Confidence: 🟢**

**X-Ray Service Quotas**

| Quota | Default | Adjustable |
|-------|---------|------------|
| Custom sampling rules per region | 25 | Yes |
| Groups per account per region | 25 | No |
| Indexed annotations per trace | 50 | No |
| Segment document size | 64 KB | No |
| Segments per second | 2,600 | No |
| Trace document size | 500 KB | No |
| Trace data retention | 30 days | No |
| Trace data modification period | 7 days | No |

Source: https://docs.aws.amazon.com/general/latest/gr/xray.html (2026-08-31)

**Confidence: 🟢**

## Operational Patterns

**Observability Stack Integration (Three Pillars)**
- RTO/RPO (if applicable): N/A — observability data plane; does not affect application RTO/RPO directly. Trace retention: 30 days. Service graph retention: 30 days.
- AWS Services: AWS X-Ray (traces), Amazon CloudWatch Metrics (metrics), Amazon CloudWatch Logs (logs), CloudWatch Application Signals (unified APM), CloudWatch ServiceLens / Trace Map (correlated view)
- Cost Profile: Medium — X-Ray free tier covers 100K traces/month recorded and 1M retrieved. Beyond free tier: $5.00/M recorded, $0.50/M retrieved. Transaction Search adds CloudWatch Logs ingestion cost. Groups add retrieved-trace costs per matching expression.
- Automation: Automate: sampling rule deployment via IaC (CloudFormation / Terraform aws_xray_sampling_rule); ADOT Collector config in SSM Parameter Store with automated rotation; X-Ray Group creation and Insights enablement. Manual decision points: determining appropriate sampling rates per route (requires traffic profiling); deciding when to enable Transaction Search 100% ingestion vs. accepting sampled coverage.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-cloudwatch.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html (2026-08-30)

**Confidence: 🟢**

---

**Scaling Trace Collection**
- RTO/RPO (if applicable): N/A
- AWS Services: AWS X-Ray, ADOT Collector (ECS sidecar / EC2), CloudWatch Agent, AWS X-Ray Groups
- Cost Profile:
  - Low traffic (< 100K traces/month): Free tier. Default sampling at 1 req/sec + 5% sufficient.
  - Medium traffic (100K–10M traces/month): Tune sampling rules by service and path. Enable Transaction Search selectively. Enable Insights. Cost: $0.50–$50/month in X-Ray charges.
  - High traffic (> 10M traces/month): Partition with X-Ray Groups; apply per-group sampling rules. Enable Transaction Search with CloudWatch Logs metric filters. Consider Application Signals SLOs. Multi-account: CloudWatch OAM.
- Automation: AWS Budget alerts for X-Ray spend threshold. CloudWatch alarm on X-Ray group trace count metrics. Automated cleanup of inactive Groups quarterly via Lambda scheduled event.
- Source: https://aws.amazon.com/xray/pricing/ (2026-08-30, search-confirmed); https://docs.aws.amazon.com/xray/latest/devguide/xray-console-crossaccount.html (2026-08-30)

**Confidence: 🟢**

---

**SDK Migration — X-Ray SDK to ADOT**
- RTO/RPO (if applicable): N/A — migration event; plan for zero-downtime incremental rollout. **Deadline: February 25, 2027 (full end-of-support for X-Ray SDKs and Daemon).**
- AWS Services: AWS X-Ray, AWS Distro for OpenTelemetry (ADOT), AWS Lambda, Amazon ECS, Amazon EC2
- Cost Profile: Migration itself has no direct cost. Post-migration, ADOT incurs the same X-Ray trace ingestion pricing. The ECS ADOT sidecar adds container compute cost per task.
- Automation: Migration guides are available per language: Java, Go, Node.js, .NET, Python, Ruby. Key concept mapping: X-Ray Recorder → OTel Tracer Provider + Tracers; Service Plugins → Resource Detectors; Annotations/Metadata → OTel Attributes; X-Ray Emitter → Span Exporter; X-Ray Daemon → OTel Collector. X-Ray Daemon migration target: CloudWatch Agent (v1.300025.0+) or OTel Collector with `awsxray` exporter. Trace data modification period: you can add data to a recorded trace for up to 7 days after recording.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/document-history.html (2026-08-31); https://docs.aws.amazon.com/general/latest/gr/xray.html (2026-08-31)

**Confidence: 🟢**

**Amazon DevOps Guru Integration**
- RTO/RPO (if applicable): N/A
- AWS Services: Amazon DevOps Guru, AWS X-Ray, Amazon CloudWatch, AWS Config, AWS CloudTrail
- Cost Profile: Medium — DevOps Guru has its own pricing (per resource analyzed).
- Automation: DevOps Guru integrates with X-Ray, CloudWatch, AWS Config, and CloudTrail to produce ML-based anomaly detection and actionable remediation recommendations. Enable DevOps Guru on an account to automatically analyze X-Ray trace anomalies alongside infrastructure metrics.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/ops_workload_observability_analyze_workload_traces.html (2026-08-31)

**Confidence: 🟢**

## Reference Architectures

**Standard Web Application — API Gateway + Lambda + ECS + DynamoDB with X-Ray/ADOT Tracing**
- Context: Three-tier web application with REST API entry point, Lambda-based business logic, ECS microservices, and DynamoDB persistence.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge | Amazon CloudFront | CDN — passes `X-Amzn-Trace-Id` header downstream; does NOT emit its own X-Ray segment [UNVERIFIED — no official page found; header passthrough only] |
  | Load Balancer | Application Load Balancer (ALB) | Injects `X-Amzn-Trace-Id` header with Root only (no Parent field); does NOT appear as a node on the X-Ray service map; does NOT support native active tracing |
  | API Layer | Amazon API Gateway (REST) | Active tracing enabled; auto-injects `X-Amzn-Trace-Id`; sampling rules applied at stage |
  | Compute — Serverless | AWS Lambda + ADOT Managed Lambda Layer | Active tracing; ADOT layer provides auto-instrumentation; subsegments for DynamoDB/SQS calls; containerized Lambda must bake layer contents into image (cannot use Lambda Layers) |
  | Compute — Container (ECS) | Amazon ECS Fargate + ADOT Collector sidecar | Application container exports OTel to ADOT sidecar; sidecar forwards to X-Ray |
  | Compute — Container (EKS) | Amazon EKS + ADOT Operator (EKS Add-On) | CloudWatch Observability EKS Add-On v5.0.0+ for Application Signals; ADOT Operator deploys Collector via CRD; supports annotation-based auto-instrumentation (except Node.js ESM) |
  | Data — NoSQL | Amazon DynamoDB | Instrumented via ADOT AWS SDK library; appears as Inferred Segment in trace |
  | Messaging | Amazon SQS | Async message passing; X-Ray auto-links SQS producer → Lambda consumer traces (max 20 linked traces/segment, max 100 links/trace) |
  | Trace Backend | AWS X-Ray | Receives segments/subsegments; service graph; 30-day retention |
  | APM / SLO | CloudWatch Application Signals | Auto SLO generation from trace-derived metrics; trace/log correlation |
  | Full-fidelity | CloudWatch Transaction Search (`aws/spans`) | 100% span ingestion for specific debugging use cases |
  | Anomaly Detection | X-Ray Insights | Per-Group statistical anomaly detection; EventBridge notifications |
  | Unified View | CloudWatch Trace Map | Service map + correlated CloudWatch Metrics and Logs |
  | IAM | AWS IAM (`AWSXRayDaemonWriteAccess`) | Least-privilege write access on all compute roles |
  | Encryption | AWS KMS (symmetric CMK) | Encrypt trace data at rest for regulated workloads |

- Key Decisions:
  - Use ADOT (not X-Ray SDK) for all new instrumentation.
  - Only REST API type in API Gateway supports active tracing — not HTTP APIs or WebSocket APIs.
  - ALB does NOT appear as a service map node and does NOT support native active tracing. It injects `X-Amzn-Trace-Id` header with Root only (no Parent). The first instrumented downstream service becomes the trace root visible on the service map.
  - Sampling rules defined centrally in X-Ray console; all services read from X-Ray API.
  - Enable Transaction Search for customer support use cases; manage CloudWatch Logs ingestion cost.
  - Enable Insights per Group; wire EventBridge to SNS/Lambda for incident automation.
  - Containerized Lambda (container image) cannot use Lambda Layers — must bake ADOT layer contents into the container image.
- Scaling Path:
  - < 100K traces/month: Free tier covers all costs. Default sampling sufficient.
  - 100K–10M traces/month: Tune per-route sampling rules. Enable Insights. Enable Transaction Search selectively.
  - > 10M traces/month: X-Ray Groups for partitioning. Application Signals SLOs. CloudWatch OAM for multi-account visibility.
  - Multi-account: CloudWatch OAM with monitoring account; up to 5 monitoring accounts per source.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-services-lambda.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html (2026-08-30); https://docs.aws.amazon.com/AmazonECS/latest/developerguide/trace-data.html (2026-08-30)

## Provider Differentiators

**Differentiator 1 — Lambda Native X-Ray Integration**
- Category: Native compute integration
- Unique value: Lambda is the only compute service that runs the X-Ray daemon automatically (Java, Node.js runtimes) and creates both a Lambda service node and a function node on the service map. Passive tracing requires zero configuration when the upstream service is already instrumented. SQS-to-Lambda trace linking produces end-to-end visibility across queue and consumer with no manual header propagation.
- Architecture impact: Reduces instrumentation overhead for event-driven architectures. No separate daemon deployment needed. Enables trace visibility from API Gateway through SQS queues into Lambda consumers as a single end-to-end trace.
- When to leverage: Any Lambda-based API, event processing pipeline, or scheduled workload.
- Caveat: Cannot add annotations to the Lambda-created parent segment — only to subsegments. Active tracing must be enabled per function. X-Ray Lambda layer (legacy SDK) is in maintenance mode as of 2026-02-25; use ADOT Managed Lambda Layer for all new projects.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-lambda.html (2026-08-30)

**Confidence: 🟢**

---

**Differentiator 2 — API Gateway REST Active Tracing**
- Category: Native API layer integration
- Unique value: API Gateway REST APIs support active tracing with configurable sampling rules scoped to API stage, path, or header values. Propagates `X-Amzn-Trace-Id` downstream even when tracing is disabled (passive mode). No application code changes required for trace initiation at the API boundary.
- Architecture impact: Automatic trace initiation for all REST traffic. The first service's sampling decision propagates downstream — configuring sampling at API Gateway controls effective sampling across the entire backend chain.
- When to leverage: All REST API-based backends. This is the recommended tracing entry point for web applications.
- Caveat: Supported only for REST APIs. HTTP APIs and WebSocket APIs are NOT supported — a common adoption blocker. HTTP integrations with many unique URL path parameters can hit the 10,000 service map node limit; use query string parameters instead of path parameters.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html (2026-08-30)

**Confidence: 🟢**

---

**Differentiator 3 — ECS Fargate ADOT Sidecar Pattern**
- Category: Native container integration
- Unique value: Amazon ECS integrates with ADOT as an officially documented sidecar pattern. No host-level access required — works fully on Fargate. The ADOT Collector sidecar serves as a multi-backend observability pipeline (X-Ray, CloudWatch, AMP) from a single container configuration.
- Architecture impact: Each ECS task definition includes an ADOT sidecar alongside the application container. The task IAM role controls X-Ray write access and sampling rule retrieval independently from the task execution role.
- When to leverage: ECS Fargate workloads where host access is unavailable. When a single sidecar must serve both tracing and metrics pipelines.
- Caveat: Requires explicit task IAM role (not execution role) configuration with X-Ray and SSM permissions. ADOT sidecar adds resource overhead per task.
- Source: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/trace-data.html (2026-08-30)

**Confidence: 🟢**

---

**Differentiator 4 — CloudWatch Application Signals (SLOs from Traces)**
- Category: APM and SLO management
- Unique value: Application Signals automatically converts trace-derived latency and fault metrics into SLOs without manual metric instrumentation. Supports period-based and request-based SLOs. Enables error budgets on trace-derived metrics directly.
- Architecture impact: Eliminates the need to build custom SLO dashboards from raw CloudWatch metrics. Auto-generates SLOs for any instrumented service. Integrates RUM and synthetic monitoring with backend trace data.
- When to leverage: Production services requiring SLO-based alerting and error budget tracking. Services with high fluctuation in request volume benefit most from request-based SLOs (vs. period-based).
- Caveat: Supported languages: Java, Python, Node.js, .NET. EKS requires CloudWatch Observability EKS add-on v5.0.0+. Application Signals requires service-linked role on first account-level enablement. Not available in all AWS regions. Node.js ESM modules on EKS require manual Dockerfile-level configuration (annotation-based auto-instrumentation does not work).
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-EKS.html (2026-08-30); https://aws.amazon.com/about-aws/whats-new/2024/09/cloudwatch-application-signals-service-level-objectives (2024-09)

**Confidence: 🟢**

---

**Differentiator 5 — Transaction Search (100% Trace Indexing)**
- Category: Full-fidelity trace analytics
- Unique value: Ingests 100% of spans as structured logs into CloudWatch log group `aws/spans`. Spans in OTel semantic convention format with W3C trace IDs. Supports up to 10,000 spans per trace. Enables free-form analytics on any span attribute including business attributes. CloudWatch Logs capabilities (metric filters, subscription filters, data masking for PII) apply to all spans.
- Architecture impact: Decouples sampling from span capture. Applications send to the X-Ray OTel endpoint; X-Ray auto-converts to semantic convention format before writing to `aws/spans`. Enables complete audit trails of all requests at CloudWatch Logs cost.
- When to leverage: High-cardinality debugging (user-level, order-level trace search). Compliance use cases requiring full trace retention. Cost-effective custom metric extraction via CloudWatch Logs metric filters on span attributes.
- Caveat: Pricing is CloudWatch Logs ingestion pricing — 100% span ingestion at high trace volumes can significantly increase total observability costs. Requires explicit enablement. Requires head sampling = 100% for full span coverage.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html (2026-08-30); https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-spans.html (2026-08-30)

**Confidence: 🟢**

---

**Differentiator 6 — X-Ray Insights Automated Anomaly Detection**
- Category: Automated anomaly detection
- Unique value: X-Ray Insights continuously analyzes trace data using statistical modeling to predict expected fault rates. Creates an Insight when fault rates exceed expected range and tracks it until resolved. Deduplicates anomalies across multiple microservices to identify the single root-cause service — avoiding alert floods when one downstream failure propagates upstream.
- Architecture impact: EventBridge events emitted for each insight lifecycle change (creation, significant change, closure) trigger SNS, Lambda, SQS, or any EventBridge target for automated incident management pipelines. APIs available: `GetInsightSummaries`, `GetInsight`, `GetInsightEvents`, `GetInsightImpactGraph`.
- When to leverage: Production microservice architectures where fault propagation from one service triggers errors across multiple upstream services, making root-cause identification manual and slow.
- Caveat: Must be enabled explicitly per X-Ray Group — not on by default. EventBridge notifications are best-effort and NOT guaranteed. EventBridge does not support CMK encryption for Insights events.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-insights.html (2026-08-30)

**Confidence: 🟢**

---

**Differentiator 7 — CloudWatch ServiceLens / Trace Map (Correlated Observability)**
- Category: Correlated observability (traces + metrics + logs)
- Unique value: ServiceLens (surfaced as X-Ray Trace Map in CloudWatch console) unifies the X-Ray service map with CloudWatch Metrics and CloudWatch Logs. CloudWatch RUM integration extends visibility from backend traces to end-user browser sessions. Single pane of glass across the full observability three-pillar stack.
- Architecture impact: Requires deploying both CloudWatch agent and ADOT Collector (or CloudWatch Agent v1.300025.0+ for unified collection) on each compute tier. CloudWatch agent emits segment-level metrics per service node. RUM JS snippet enables browser-session correlation.
- When to leverage: Multi-tier architectures where a single performance incident may have both infrastructure-level causes (CloudWatch metrics) and application-level manifestations (X-Ray traces) that must be correlated in a single view.
- Caveat: Trace Map and ServiceLens are now converged in the CloudWatch console — the standalone X-Ray console is deprecated. On ECS, may require combined ADOT + CloudWatch agent configuration.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-cloudwatch.html (2026-08-30)

**Confidence: 🟢**

---

**Differentiator 8 — Native OTel via ADOT (Instrument Once, Export to Many)**
- Category: Open standards instrumentation
- Unique value: ADOT is the AWS-supported, security-patched distribution of CNCF OpenTelemetry. Single instrumentation path that simultaneously exports to X-Ray, CloudWatch (EMF metrics), Amazon Managed Service for Prometheus, Amazon OpenSearch, and any OTLP-compliant backend. For Lambda: AWS-managed Lambda layers deliver plug-and-play auto-instrumentation with zero code changes.
- Architecture impact: Instrument application code once; routing to multiple observability backends controlled at the ADOT Collector configuration layer, not in application code. For Lambda, ADOT layers handle both trace exporting to X-Ray and metric exporting to CloudWatch in one layer configuration. For ECS/EKS, the ADOT Collector sidecar is the single collection point for all telemetry signals.
- When to leverage: All new projects (mandatory from 2026 given X-Ray SDK maintenance mode). Mixed AWS/on-premises environments. Organizations adopting OTel as a standard across cloud providers.
- Caveat: ADOT may lag upstream OTel releases. Auto-instrumentation agents add startup latency and cold-start overhead in Lambda. For Node.js ESM modules on EKS, Application Signals auto-instrumentation via annotation does not work — requires manual Dockerfile-level configuration.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-adot.html (2026-08-30)

**Confidence: 🟢**

## Scenario Coverage

**Standard Case**: ADOT-instrumented web application on Lambda + ECS Fargate with API Gateway REST entry point and DynamoDB persistence
- Approach:
  - API Gateway REST stage: active tracing enabled; sampling rules configured centrally in X-Ray console.
  - Lambda functions: ADOT Managed Lambda Layer; Active Tracing enabled per function; subsegments for DynamoDB and SQS calls.
  - ECS Fargate services: ADOT Collector sidecar per task definition; application exports OTel to `localhost:4317`; task IAM role has `AWSXRayDaemonWriteAccess` + SSM permissions.
  - DynamoDB: appears as Inferred Segment from instrumented SDK calls in Lambda/ECS.
  - SQS → Lambda: automatic trace linking.
  - KMS CMK: configured for trace encryption at rest.
  - X-Ray Insights: enabled per production Group; EventBridge → SNS for incident notification.
  - Application Signals: enabled for SLO generation; log correlation via trace/span ID injection.
- Key Decisions:
  - ADOT vs. X-Ray SDK: mandatory ADOT for all new services as of 2026-02-25.
  - Sampling reservoir and rate per route: define based on traffic volume and cost budget.
  - Transaction Search on/off: on for customer-facing checkout API; off for high-volume background processing.
  - CMK vs. AWS managed key: CMK for any service handling PII or regulated data.

**Edge Case**: Service map node limit hit — ALB entry point / 10,000-node service map limit
- Approach:
  - The 10,000-node service map limit is typically hit when API Gateway REST HTTP integrations use URL path parameters with high cardinality (e.g., `/orders/{orderId}/items/{itemId}`) — each unique resolved path generates a separate service node.
  - Resolution: switch to query string parameters (e.g., `/orders/items?orderId=...&itemId=...`) or POST body for high-cardinality identifiers. This reduces path-parameter-derived node counts to one node per route template.
  - ALB as entry point: ALB injects `X-Amzn-Trace-Id` with Root only (no Parent field) into requests to targets. ALB does NOT appear as a node on the X-Ray service map and does NOT support native active tracing. The first downstream instrumented service (e.g., ECS task, Lambda) becomes the visible root service in the service map. Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-elb.html (2026-08-31)
  - CloudFront: [UNVERIFIED] — CloudFront does not emit its own X-Ray segment; it only passes `X-Amzn-Trace-Id` downstream at the origin request level.
  - For HTTP APIs or WebSocket APIs in API Gateway: X-Ray tracing is NOT supported. Architect must either use REST API type or accept that the API Gateway layer will not appear in the service map.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html (2026-08-30); https://docs.aws.amazon.com/xray/latest/devguide/xray-console-servicemap.html (2026-08-30)

**Edge Case**: Lambda deployed as container image requires ADOT auto-instrumentation
- Approach:
  - Lambda functions deployed as container images cannot use Lambda Layers. The ADOT Managed Lambda Layer is not available as a layer attachment for container-image deployments.
  - Resolution: manually bake the ADOT layer contents into the container image during the Docker build process. Set `AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-instrument` environment variable in the function configuration to enable Application Signals auto-instrumentation. Attach the `CloudWatchLambdaApplicationSignalsExecutionRolePolicy` managed policy to the Lambda execution role.
  - For OTEL_SERVICE_NAME: set this environment variable to group multiple Lambda functions into one logical service in the Application Signals service map.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-Lambda.html (2026-08-31)

**Anti-Pattern Case**: Team wants to use HTTP API type in API Gateway with X-Ray tracing; or team proposes using legacy X-Ray SDK for a net-new Lambda function
- Clarification:
  - For HTTP API type: "X-Ray active tracing is not supported for API Gateway HTTP APIs or WebSocket APIs — only REST APIs. If the API requires X-Ray service map visibility and active tracing, it must use REST API type. If HTTP API type is required for other reasons (e.g., JWT authorizers, lower cost, OIDC integration), the API Gateway layer will be absent from the X-Ray service map. Is the team willing to accept this visibility gap, or can the API type be changed to REST?"
  - For legacy X-Ray SDK on net-new Lambda: "The AWS X-Ray SDK entered maintenance mode on February 25, 2026. AWS only releases security patches — no new features, framework support, or non-security bug fixes will be added. All new Lambda instrumentation must use the ADOT Managed Lambda Layer. What is the specific reason for choosing the legacy X-Ray SDK, and can the ADOT layer be used instead?"

## Research Iteration Changelog

> Mandatory when `RESEARCH_DEPTH` is `standard`, `deep`, or `exhaustive`. Omit for `quick`.

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Core concepts | Segment, Subsegment, Trace, Sampling, Tracing Header, Annotations, Metadata, Group, Inferred Segment, Errors/Faults/Throttles concepts | Added — definitions sourced from X-Ray Concepts official doc | https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html (2026-08-30) |
| 1 | Core concepts | X-Ray SDK and Daemon Maintenance Mode (2026-02-25) | Added — SDK/Daemon maintenance mode confirmed; ADOT migration mandated | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30) |
| 1 | Core concepts | CloudWatch Application Signals (GA June 2024) | Added — unified APM, SLOs, RUM, AI analysis | https://aws.amazon.com/xray/ (2026-08-30) |
| 1 | Core concepts | Transaction Search (GA November 2024) | Added — 100% span ingestion into `aws/spans` CloudWatch Logs log group | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-spans.html (2026-08-30) |
| 1 | Core concepts | CloudWatch OTel Endpoint | Added — direct OTLP export to X-Ray without local collector | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30) |
| 1 | Core concepts | X-Ray → OpenTelemetry concept mapping table | Added — full mapping table from SDK migration guide | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (2026-08-30) |
| 1 | Security | KMS encryption tiers (default, AWS managed key, CMK) | Added — CLI commands and IAM requirements confirmed | https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html (2026-08-30) |
| 1 | Security | IAM policies — AWSXRayDaemonWriteAccess exact actions (v2, 2024-02-13) | Added — exact policy JSON confirmed | https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSXRayDaemonWriteAccess.html (2026-08-30) |
| 1 | Security | Cross-account observability via CloudWatch OAM | Added — up to 5 monitoring accounts; first copy free | https://docs.aws.amazon.com/xray/latest/devguide/xray-console-crossaccount.html (2026-08-30) |
| 1 | Security | X-Ray Insights + EventBridge notification | Added — best-effort delivery; CMK not supported for EventBridge | https://docs.aws.amazon.com/xray/latest/devguide/xray-console-insights.html (2026-08-30) |
| 1 | Anti-Patterns | 6 anti-patterns documented with Risk Level, wrong/correct code examples, detection, impact | Added | Multiple X-Ray and IAM official docs (2026-08-30) |
| 1 | Mandatory Patterns | 7 mandatory patterns with Pillar Alignment, Architecture Decision, Verification | Added | Multiple X-Ray, ECS, Lambda official docs (2026-08-30) |
| 1 | Reference Architecture | Full layer/service/purpose table for web application | Added | https://docs.aws.amazon.com/xray/latest/devguide/xray-services.html (2026-08-30) |
| 1 | Provider Differentiators | 8 differentiators documented | Added | Multiple official X-Ray, ECS, Lambda, Application Signals docs (2026-08-30) |
| 1 | Irresolvable Gap | CloudFront native X-Ray segment emission | ⚠️ IRRESOLVABLE — No official page confirmed CloudFront emits its own X-Ray segment; only header propagation documented | — |
| 1 | Irresolvable Gap | ALB native X-Ray active tracing | ⚠️ IRRESOLVABLE (Run 1) — ALB documented to propagate `X-Amzn-Trace-Id` header; no official page confirmed ALB native X-Ray active tracing equivalent to API Gateway | — |
| 1 | Irresolvable Gap | SDK-level PII filtering / segment sanitization hooks | ⚠️ IRRESOLVABLE — No official X-Ray documentation page found describing SDK-level PII filtering or segment sanitization APIs | — |
| 1 | Irresolvable Gap | DynamoDB+X-Ray and RDS+X-Ray dedicated integration pages | ⚠️ IRRESOLVABLE — Inferred from general SDK instrumentation docs; dedicated DynamoDB/RDS+X-Ray integration pages not directly fetched and verified | — |
| 1 | Irresolvable Gap | Long-term trace retention export mechanism beyond 30 days | ⚠️ IRRESOLVABLE — No official X-Ray trace export mechanism for retention beyond 30 days confirmed; Transaction Search (CloudWatch Logs) is a separate store with configurable retention, but not a direct trace export | — |
| 1 | Irresolvable Gap | Specific REL WAF best-practice IDs explicitly referencing X-Ray or distributed tracing | ⚠️ IRRESOLVABLE — WAF Reliability pillar page returned only intro content; specific REL IDs that explicitly reference X-Ray not confirmed from fetched content | — |
| 2 | Irresolvable Gap (ALB) | ALB native X-Ray active tracing | ✅ RESOLVED — xray-services-elb.html confirmed: ALB injects `X-Amzn-Trace-Id` header (Root only, no Parent); does NOT appear as service map node; no active tracing | https://docs.aws.amazon.com/xray/latest/devguide/xray-services-elb.html (2026-08-31) |
| 2 | Operational Patterns | SDK/Daemon full end-of-support date | Added — February 25, 2027 (complete discontinuation; maintenance mode since Feb 25, 2026) | https://docs.aws.amazon.com/xray/latest/devguide/document-history.html (2026-08-31) |
| 2 | Architecture Guardrails | WAF best-practice ID corrected | Updated — OPS08-BP03 (Risk: Medium) "Analyze Workload Traces" replaces incorrectly cited OPS04-BP05 | https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/ops_workload_observability_analyze_workload_traces.html (2026-08-31) |
| 2 | Architecture Guardrails | OTLP endpoint constraints | Added — HTTP 1.1 only (gRPC NOT supported), SigV4 required, 5 MB/request, 10,000 spans/request, 200 KB/span, timestamps within ±2h future / 14 days past | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLP-UsingADOT.html (2026-08-31) |
| 2 | Anti-Patterns | Anti-Pattern 7 — X-Ray with HTTP API on API Gateway | Added — X-Ray active tracing not supported for HTTP or WebSocket APIs | https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html (2026-08-31) |
| 2 | Anti-Patterns | Anti-Pattern 8 — Lambda PassThrough mode | Added — PassThrough is the DEFAULT; Lambda does NOT send segments unless Active tracing is explicitly set | https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html (2026-08-31) |
| 2 | Anti-Patterns | Anti-Pattern 9 — Collector-less ADOT with 100% sampling cost risk | Added — defaults to `parentbased_always_on`; up to 20x cost increase | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLP-UsingADOT.html (2026-08-31) |
| 2 | Security Architecture | VPC Endpoints (PrivateLink) | Added — endpoint service `com.amazonaws.{region}.xray`; FIPS available | https://docs.aws.amazon.com/general/latest/gr/xray.html (2026-08-31) |
| 2 | Security Architecture | CloudTrail data event logging (March 2024) | Added — `PutTraceSegments`, `GetTraceSummaries`, `BatchGetTraces` now logged | https://docs.aws.amazon.com/xray/latest/devguide/document-history.html (2026-08-31) |
| 2 | Security Architecture | Service Quotas table | Added — 8 quotas with adjustability indicators; 7-day modification period, 2,600 segments/sec, 25 groups (not adjustable) | https://docs.aws.amazon.com/general/latest/gr/xray.html (2026-08-31) |
| 2 | Cloud-Native Design Patterns | SQS-Lambda trace linking limits | Added — max 20 traces/segment, max 100 links/trace; oversampling mitigation in 5 runtimes | https://docs.aws.amazon.com/xray/latest/devguide/xray-services-sqs.html (2026-08-31) |
| 2 | Operational Patterns | Amazon DevOps Guru integration | Added — ML-based anomaly detection integrating X-Ray, CloudWatch, AWS Config, CloudTrail | https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/ops_workload_observability_analyze_workload_traces.html (2026-08-31) |
| 2 | Reference Architectures | EKS tier added | Added — EKS + ADOT Operator (EKS Add-On) as container compute tier | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-EKS.html (2026-08-31) |
| 2 | Reference Architectures | Lambda container image caveat | Added — containerized Lambda cannot use Lambda Layers; must bake ADOT layer contents into image | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-Lambda.html (2026-08-31) |
| 2 | Irresolvable Gap | CloudFront native X-Ray segment emission | ⚠️ IRRESOLVABLE — Second run confirmed: no official page found; only header passthrough documented | — |
| 2 | Irresolvable Gap | RDS+X-Ray dedicated integration page | ⚠️ IRRESOLVABLE — Second run confirmed: RDS-specific X-Ray integration page not found; DynamoDB partially resolved via inferred segment behavior | — |
| 2 | Irresolvable Gap | SDK-level PII filtering / segment sanitization hooks | ⚠️ IRRESOLVABLE — Second run confirmed: no official X-Ray SDK sanitization API documented | — |
| 2 | Irresolvable Gap | Long-term trace retention export beyond 30 days | ⚠️ IRRESOLVABLE — Second run confirmed: no direct trace export mechanism found; Transaction Search is a separate store, not a trace export | — |
