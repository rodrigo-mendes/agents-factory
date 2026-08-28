---
Full_Name: "AWS X-Ray — Distributed Tracing & Observability"
Cloud_Provider: "AWS"
Architecture_Domain: "Observability / Distributed Tracing"
Target_Edition: "AWS X-Ray Developer Guide — 2026 edition (OpenTelemetry-first; X-Ray SDK/Daemon enter maintenance mode 2026-02-25)"
Architecture_Context: "Microservices and serverless workloads on AWS (general — not scoped by requester; see Open Questions)"
Official_Source_URL: "https://docs.aws.amazon.com/xray/latest/devguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Currency_Threshold: "2027-07-31 — review after this date; the X-Ray SDK/Daemon end-of-support milestone (2027-02-25) falls inside this window"
Domain_Complexity: Complex (observability, security-sensitive, mid-transition to OpenTelemetry)
---

# AWS X-Ray — Distributed Tracing Research (2026 edition)

> **Version Absolutism notice.** This document pins to the **2026 state of AWS X-Ray**, in which
> AWS has declared **OpenTelemetry the primary instrumentation standard** and the classic **X-Ray
> SDKs and X-Ray Daemon enter maintenance mode on 2026-02-25**. Patterns that recommend the X-Ray
> SDK/Daemon for *new* applications are treated as outdated guidance. All sources accessed
> **2026-07-31**.

---

## Executive Summary

AWS X-Ray is AWS's distributed-tracing backend: it receives **segments** from instrumented
compute, groups segments sharing a request into **traces**, and renders a **service graph / trace
map** for latency and error analysis. In the 2026 edition, X-Ray is no longer primarily a
"bring-your-own-SDK" service — it is the **trace store and analytics layer** behind the unified
**CloudWatch observability experience**, and the console has consolidated into the CloudWatch
console's Traces / Trace Map pages. Source: [X-Ray concepts](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html) (accessed 2026-07-31).

**What changed vs. prior editions.** AWS has formally announced that **X-Ray is transitioning to
OpenTelemetry (OTel) as its primary instrumentation standard**. The classic **X-Ray SDKs and the
X-Ray Daemon enter maintenance mode on 2026-02-25** (security fixes only, no new features), with
end-of-support communicated for **2027-02-25**. For new and existing applications AWS now
recommends: instrument with **OpenTelemetry SDKs / AWS Distro for OpenTelemetry (ADOT)**, and
collect with the **OpenTelemetry Collector** or the **CloudWatch agent** (v1.300025.0+) instead of
the X-Ray Daemon. Additionally, **Transaction Search** (GA Nov 2024) lets you ingest **100% of
spans** into a `aws/spans` CloudWatch Logs group in OpenTelemetry semantic-convention format with
W3C trace IDs. Sources: [Migrating from X-Ray instrumentation to OpenTelemetry](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html), [X-Ray SDK and Daemon Support timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html), [CloudWatch Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html) (all accessed 2026-07-31).

**Three most critical guardrails for the given context.** (1) **Instrument new services with
OpenTelemetry/ADOT, not the X-Ray SDK** — the SDK is in maintenance mode. (2) **Never send an
unsampled 100% of traces to X-Ray blindly for high-volume paths** — sampling exists precisely to
control cost and signal; use Transaction Search's span-log model when you genuinely need 100%
visibility. (3) **Propagate context correctly at trust boundaries** — OTel defaults to W3C Trace
Context; you must add the X-Ray propagator when crossing into AWS services (API Gateway, Lambda)
that expect the `X-Amzn-Trace-Id` header, and strip inbound `X-Amzn-Trace-Id` from untrusted
clients.

> ⚠️ **Open question for the requester (Ask-First).** `ARCHITECTURE_CONTEXT` was not supplied. This
> document assumes general microservices + serverless. If the target is specifically serverless
> (Lambda-heavy), container (ECS/EKS), or hybrid/on-prem, the collector topology and Lambda-layer
> guidance below should be narrowed. Confirm before this feeds skill authoring.

---

## Cloud Architecture Glossary

```
Term: Segment
Definition: The unit of data a compute resource sends to X-Ray about its work on a request — host,
  request, response, work done (timing + subsegments), and issues. A single segment document may be
  up to 64 KB.
Provider Docs Section: X-Ray concepts → Segments
Architect Usage: The "server span" of a service. One instrumented service = one segment per traced request.
Common Confusion: Confused with a "trace" (a trace is the collection of ALL segments for one request).
```
```
Term: Subsegment
Definition: A finer breakdown inside a segment — a downstream AWS call, external HTTP call, SQL query,
  or arbitrary code block. Downstream services that don't emit their own segment appear as
  "inferred segments" derived from the caller's subsegment.
Provider Docs Section: X-Ray concepts → Subsegments
Architect Usage: Use to attribute latency to specific dependencies (DynamoDB, S3, third-party APIs).
Common Confusion: Treated as separate traces; they belong to the parent segment.
```
```
Term: Trace / Trace ID
Definition: A trace collects all segments generated by a single request, tracked by a trace ID. Max
  single trace size 500 KB. Trace data and the service graph are retained for 30 days.
Provider Docs Section: X-Ray concepts → Traces
Architect Usage: The end-to-end request unit you search, filter, and bill on.
Common Confusion: X-Ray trace ID format (1-{epoch}-{random}) vs. W3C trace-id (32 hex). OTel uses W3C.
```
```
Term: Service graph / Service map / Edge
Definition: A JSON document (rendered as the "trace map") where each resource sending data is a node
  and edges connect services that serve requests together. Retained 30 days.
Provider Docs Section: X-Ray concepts → Service graph
Architect Usage: First-look triage surface for latency/error hotspots and topology drift.
Common Confusion: "Service map" (visualization) vs "service graph" (underlying JSON).
```
```
Term: Sampling
Definition: The algorithm deciding which requests are traced. Default reservoir: first request each
  second + 5% of additional requests. Configurable via sampling rules.
Provider Docs Section: X-Ray concepts → Sampling
Architect Usage: The primary cost + signal-to-noise control. Disable sampling only for
  state-changing / low-volume critical paths.
Common Confusion: Assuming 100% capture by default — it is NOT; the default is intentionally conservative.
```
```
Term: Tracing header (X-Amzn-Trace-Id)
Definition: HTTP header carrying Root trace ID, optional Parent segment ID, and Sampled decision,
  e.g. Root=1-5759e988-...;Parent=53995c3f42cd8ad8;Sampled=1. May include Lineage from Lambda/AWS.
Provider Docs Section: X-Ray concepts → Tracing header
Architect Usage: The propagation contract between AWS services. Strip from untrusted inbound requests.
Common Confusion: X-Amzn-Trace-Id (AWS) vs. traceparent (W3C, OTel default).
```
```
Term: Annotations vs. Metadata
Definition: Annotations = indexed key-value pairs usable in filter expressions and GetTraceSummaries;
  X-Ray indexes up to 50 annotations per trace. Metadata = non-indexed key-values of any type.
Provider Docs Section: X-Ray concepts → Annotations and metadata
Architect Usage: Put searchable business keys (customer_id, order_id) in annotations; bulk context in metadata.
Common Confusion: Putting high-cardinality searchable keys in metadata (unsearchable) — a common design error.
```
```
Term: Filter expression / Group
Definition: Filter expressions query traces by attributes; a Group persists a filter expression to
  produce its own service graph, trace summaries, and CloudWatch metrics (published every minute).
Provider Docs Section: X-Ray concepts → Filter expressions / Groups
Architect Usage: Groups drive per-domain SLO dashboards and alarms. Note: groups are billed by retrieved traces.
Common Confusion: Editing a group's filter retroactively changes history — it does not (applies to new traces only).
```
```
Term: Errors / Faults / Throttle
Definition: Error = client 4xx; Fault = server 5xx; Throttle = 429. Categorization used across the trace map.
Provider Docs Section: X-Ray concepts → Errors, faults, and exceptions
Architect Usage: Fault vs Error routing decides whether to page a service owner or a caller.
Common Confusion: Treating throttles as generic 4xx errors — X-Ray categorizes 429 separately.
```
```
Term: ADOT (AWS Distro for OpenTelemetry)
Definition: AWS's supported distribution of CNCF OpenTelemetry — SDKs, auto-instrumentation agents,
  and collectors, tested/optimized/secured by AWS; exports to X-Ray, CloudWatch, OpenSearch, AMP.
Provider Docs Section: X-Ray → AWS Distro for OpenTelemetry and AWS X-Ray
Architect Usage: The recommended instrumentation for new workloads sending traces to X-Ray.
Common Confusion: ADOT ≠ raw upstream OTel. ADOT is AWS-supported; both can target X-Ray.
```
```
Term: Transaction Search
Definition: CloudWatch analytics experience ingesting 100% of spans as structured logs into the
  aws/spans log group (OTel semantic-convention format, W3C trace IDs), indexing a configurable
  percentage as X-Ray trace summaries. Supports traces up to 10,000 spans.
Provider Docs Section: Amazon CloudWatch → Transaction Search
Architect Usage: Use when sampling loses signal (rare-error debugging, business-attribute correlation).
Common Confusion: Believing it replaces sampling — it complements it; you choose an indexing percentage.
```
```
Term: CloudWatch Application Signals
Definition: Curated APM layer over spans providing application-centric health, SLOs, and
  service/dependency topology; offers a pre-packaged OTel setup via ADOT / CloudWatch agent.
Provider Docs Section: CloudWatch → Application Signals
Architect Usage: The "golden signals + SLO" layer above raw traces; the recommended onboarding path.
Common Confusion: Application Signals vs. X-Ray — Signals is the APM UX; X-Ray is the trace store beneath it.
```

---

## Framework Pillars — Well-Architected alignment

X-Ray is an **Operational Excellence** (observability) building block of the **AWS Well-Architected
Framework**, with direct ties to **Reliability** (MTTR, failure analysis), **Performance
Efficiency** (latency attribution), **Security** (trace-header trust, encryption of trace data),
and **Cost Optimization** (sampling as a cost lever). Reference: [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/) (accessed 2026-07-31).

```
Pillar: Operational Excellence
Definition: Ability to support development and run workloads effectively, gain insight into operations,
  and continuously improve supporting processes and procedures.
Key Design Principles: Instrument to understand system behavior; make frequent, reversible changes safely.
Applies To context: Distributed tracing is the "gain insight" mechanism — service map + trace timeline
  turn a black-box microservice call chain into an attributable latency/error breakdown.
Assessment Questions: How do you understand the health of your workload? How do you reduce defects and
  remediate quickly? How do you evolve operations?
Source: https://docs.aws.amazon.com/wellarchitected/ (accessed 2026-07-31)
```
```
Pillar: Reliability (supporting)
Definition: Ability of a workload to perform its intended function correctly and consistently.
Applies To context: Traces + errors/faults/throttle categorization drive failure-mode analysis and MTTR.
Source: https://docs.aws.amazon.com/wellarchitected/ (accessed 2026-07-31)
```
```
Pillar: Cost Optimization (supporting)
Definition: Ability to run systems to deliver business value at the lowest price point.
Applies To context: X-Ray sampling rules are the cost lever — recorded traces are billed; sampling <100%
  reduces observability cost while retaining representative signal.
Source: https://aws.amazon.com/xray/pricing/ + X-Ray concepts → Sampling (accessed 2026-07-31)
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Instrument new workloads with OpenTelemetry / ADOT (not the X-Ray SDK)**
- Pillar Alignment: Operational Excellence
- Why: AWS declared OTel the primary instrumentation standard; the X-Ray SDK/Daemon enter
  maintenance mode 2026-02-25 (security fixes only, no new features).
- AWS Services: ADOT SDK / OpenTelemetry SDK → OTel Collector or CloudWatch agent → X-Ray.
- Architecture Decision: Application emits OTLP (http/protobuf on `4318`, gRPC on `4317`) to a local
  collector; collector's `awsxray` exporter (or CloudWatch agent) forwards to X-Ray. Server spans
  become X-Ray segments; other spans become subsegments; attributes become metadata by default.
- Verification: Confirm collector/agent has `xray:PutTraceSegments`; confirm traces appear on the
  CloudWatch Traces/Trace Map page; `aws xray get-trace-summaries --start-time ... --end-time ...`.
- Trade-offs: Migration effort now vs. running on an SDK that stops receiving features/fixes.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html (accessed 2026-07-31)

**Replace the X-Ray Daemon with the CloudWatch agent or OTel Collector**
- Pillar Alignment: Operational Excellence
- Why: The Daemon is in maintenance mode; the CloudWatch agent (v1.300025.0+) and OTel Collector
  both receive OTLP and forward to X-Ray, reducing the number of agents to manage.
- AWS Services: CloudWatch agent OR `otel/opentelemetry-collector-contrib` with `awsproxy` (sampling)
  + `otlp` receiver + `awsxray` exporter.
- Architecture Decision: On EC2/on-prem run one collector per host; on ECS run a sidecar/collector
  task; stop any existing X-Ray Daemon first to avoid UDP port 2000 conflicts.
- Verification: Collector `health_check` extension healthy; `awsproxy` bound to `127.0.0.1:2000` for
  X-Ray remote sampling.
- Trade-offs: Slightly larger agent footprint than the daemon, but unified metrics+logs+traces.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#xray-Daemon-migration (accessed 2026-07-31)

**Apply explicit sampling rules; disable sampling only for critical low-volume paths**
- Pillar Alignment: Cost Optimization + Operational Excellence
- Why: Default reservoir is 1 req/sec + 5% of additional requests. High-volume health checks and
  polling should sample low; state-changing/transactional endpoints may warrant 100%.
- AWS Services: X-Ray sampling rules (usable from OTel via the X-Ray Remote Sampler in Java/.NET/Go
  and ADOT Java/.NET/Python/Node.js).
- Architecture Decision: Define per-service rules keyed on `http.url`/service name; keep a conservative
  default; raise fixed-rate for money-path routes.
- Verification: `aws xray get-sampling-rules`; confirm recorded-trace volume matches expectation on
  the CloudWatch billing/usage view.
- Trade-offs: Higher sampling = higher fidelity + higher cost.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html + X-Ray concepts → Sampling (accessed 2026-07-31)

**Put searchable business keys in annotations (indexed), bulk context in metadata**
- Pillar Alignment: Operational Excellence
- Why: Annotations are indexed for filter expressions / GetTraceSummaries (max 50 per trace);
  metadata is not searchable. For OTel, add attribute keys to `aws.xray.annotations` to index them.
- AWS Services: X-Ray annotations/metadata; OTel span attributes.
- Architecture Decision: `customer_id`, `order_id`, `tenant_id` → annotations; request/response bodies,
  diagnostic blobs → metadata.
- Verification: Filter expression `annotation.order_id = "..."` returns the trace.
- Trade-offs: Annotation cardinality/count is capped (50/trace indexed) — budget them.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-annotations (accessed 2026-07-31)

**Enable Transaction Search when 100% span visibility is required**
- Pillar Alignment: Operational Excellence + Reliability
- Why: Sampling can drop the one trace you need. Transaction Search ingests 100% of spans as
  structured logs (`aws/spans`) and indexes a chosen percentage as X-Ray trace summaries; supports
  traces up to 10,000 spans and enables CloudWatch Logs features (metric filters, data masking).
- AWS Services: CloudWatch Transaction Search, CloudWatch Logs (`aws/spans`), CloudWatch Application Signals.
- Architecture Decision: Enable in CloudWatch/console or via API/CDK; set an indexing percentage that
  balances cost vs. searchable-summary coverage; mask PII via CloudWatch Logs data masking.
- Verification: `aws/spans` log group populated; spans queryable in the Transaction Search visual editor.
- Trade-offs: 100% ingestion adds CloudWatch Logs ingestion cost + indexing cost (see Pricing).
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html (accessed 2026-07-31)

**Encrypt trace data and govern the encryption configuration**
- Pillar Alignment: Security
- Why: Trace data can contain sensitive request context; X-Ray supports encryption configuration
  changes trackable via AWS Config.
- AWS Services: X-Ray encryption config (default AWS-owned key or customer-managed KMS key), AWS Config,
  AWS KMS.
- Architecture Decision: Use a customer-managed KMS key where compliance requires key ownership/rotation;
  record config changes in AWS Config.
- Verification: AWS Config rule / X-Ray console encryption setting shows the KMS key ARN.
- Trade-offs: CMK adds KMS request cost and key-management responsibility.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-api-config.html (accessed 2026-07-31)

### ⚠️ Architectural Decisions (Ask-First)

**Instrumentation stack: raw OpenTelemetry SDK vs. ADOT vs. CloudWatch Application Signals**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Raw OTel SDK + `awsxray` exporter | OpenTelemetry Collector | Vendor-neutrality, portability | You self-support the collector config | Multi-backend / multi-cloud tracing |
  | ADOT | AWS Distro for OpenTelemetry | AWS-tested/secured, X-Ray remote sampling in more langs | Slightly behind upstream OTel releases | AWS-centric, want AWS support |
  | CloudWatch Application Signals | Application Signals (ADOT/agent pre-packaged) | Fastest onboarding, SLOs + topology out of the box | Most opinionated / AWS-coupled | Teams wanting APM+SLO with least setup |

- Cost Profile: Raw OTel/ADOT bill on X-Ray traces recorded/retrieved; Application Signals + Transaction
  Search add CloudWatch Logs ingestion and indexing costs (order of magnitude higher at 100% spans).
- Lock-in Assessment: Raw OTel = lowest lock-in (repoint the exporter); Application Signals = highest
  (AWS-specific APM UX and span-log model).
- Architect Instruction: "Ask whether tracing must also feed a non-AWS backend (Grafana/Datadog/Jaeger)
  before choosing — if yes, favor raw OTel/ADOT collector fan-out over Application Signals."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#opentelemetry-support (accessed 2026-07-31)

**Sampling strategy: head sampling (X-Ray rules) vs. tail sampling (Collector)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Head sampling (X-Ray rules / remote sampler) | X-Ray sampling rules | Simplicity, cost predictability | Can't decide based on trace outcome | Uniform traffic, cost-first |
  | Tail sampling (OTel Collector `tailsamplingprocessor`) | OTel Collector | Keep all error/slow traces regardless of rate | Collector memory/state + buffering complexity | Rare-error / latency-outlier debugging |
  | Transaction Search (100% ingest + % index) | CloudWatch Transaction Search | No dropped spans | Highest ingestion cost | Business-attribute correlation, compliance |

- Cost Profile: Head sampling cheapest; tail sampling moderate (buffering compute); Transaction Search
  highest (100% span ingestion).
- Lock-in Assessment: Tail sampling is OTel-portable; Transaction Search is AWS-specific.
- Architect Instruction: "Ask: 'Is the pain missing error traces, or is it cost?' Missing errors →
  tail sampling or Transaction Search; cost → tighten head sampling rules."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#sampling (accessed 2026-07-31)

**Collector topology: sidecar vs. per-host agent vs. central gateway**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Sidecar collector | ECS/EKS sidecar | Isolation, per-service config | Resource duplication | Strong per-service tenancy |
  | Per-host agent | CloudWatch agent on EC2 | Fewer agents to manage | Shared blast radius | EC2/on-prem fleets |
  | Central gateway collector | OTel Collector cluster | Tail sampling, central policy | Network hop, scaling the gateway | Org-wide sampling/policy control |

- Cost Profile: Sidecar highest per-task overhead; gateway centralizes cost but needs its own scaling.
- Architect Instruction: "Ask whether tail sampling is required — if yes, a central gateway collector
  is effectively mandatory (tail sampling needs all spans of a trace in one place)."
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#xray-Daemon-migration (accessed 2026-07-31)

### 🚫 Anti-Patterns (each with side-by-side ❌ Wrong / ✅ Correct)

**Building new instrumentation on the X-Ray SDK / X-Ray Daemon**
- Risk Level: HIGH
- Why: Operational Excellence — the X-Ray SDKs/Daemon enter maintenance mode 2026-02-25 (security-only)
  and are slated for end-of-support 2027-02-25; new features land only in OpenTelemetry.
- ❌ Wrong: New microservice adds `aws-xray-sdk` and ships the **X-Ray Daemon** as an ECS sidecar on
  UDP 2000 as its long-term tracing stack.
- ✅ Correct: New microservice uses **ADOT / OpenTelemetry SDK** emitting OTLP to a **CloudWatch agent
  (v1.300025.0+)** or **OTel Collector** with the `awsxray` exporter → X-Ray.
- Detection: Grep build manifests for `aws-xray-sdk*`; inventory tasks running `aws-xray-daemon`.
- Impact: Deprecation debt, missed features, forced re-platform before 2027-02-25.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html (accessed 2026-07-31)

**Tracing 100% of high-volume requests through default X-Ray recording without a sampling plan**
- Risk Level: MEDIUM (cost) / HIGH at scale
- Why: Cost Optimization — recorded traces are billed ($5.00 / 1M recorded); unbounded health-check
  and polling traffic can dominate spend and drown signal.
- ❌ Wrong: `awsxray` exporter with `AlwaysOn` sampler on a service serving 50k rps of health checks —
  every probe recorded.
- ✅ Correct: X-Ray sampling rule (reservoir 1/sec + fixed 5%) for read-only/health paths; fixed 100%
  only on money-path routes; OR enable **Transaction Search** with a bounded indexing percentage.
- Detection: CloudWatch usage metrics for `TracesRecorded`; billing anomaly vs. request volume.
- Impact: Cost overrun; noisy service map.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-sampling + https://aws.amazon.com/xray/pricing/ (accessed 2026-07-31)

**Trusting inbound `X-Amzn-Trace-Id` from untrusted clients**
- Risk Level: HIGH
- Why: Security — a client-supplied tracing header can forge trace IDs / sampling decisions and pollute
  or bias your trace data; forwarded `X-Forwarded-For` client IPs can also be forged.
- ❌ Wrong: Public API Gateway / ALB passes any client-provided `X-Amzn-Trace-Id` straight to backends
  as the root context.
- ✅ Correct: Strip/regenerate `X-Amzn-Trace-Id` at the trust boundary (edge) so the first
  X-Ray-integrated service mints the root trace; treat forwarded client IP as untrusted.
- Detection: Inspect edge config; confirm the entry service overwrites inbound tracing headers.
- Impact: Trace poisoning, sampling manipulation, misleading forensics.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-tracingheader (accessed 2026-07-31)

**Storing high-cardinality searchable keys in metadata instead of annotations**
- Risk Level: MEDIUM
- Why: Operational Excellence — metadata is NOT indexed; you cannot filter/search by it, so incident
  correlation by business key fails.
- ❌ Wrong: `segment.putMetadata("order_id", id)` and later trying `metadata.order_id = "123"` in a
  filter expression (unsupported).
- ✅ Correct: `segment.putAnnotation("order_id", id)` (or OTel: add `order_id` to `aws.xray.annotations`)
  so `annotation.order_id = "123"` works; keep ≤50 indexed annotations/trace.
- Detection: Review instrumentation for business keys placed in metadata; test filter expressions.
- Impact: Slow MTTR — cannot pivot from a business event to its trace.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-annotations (accessed 2026-07-31)

**Leaving trace data with default encryption where compliance requires customer-managed keys**
- Risk Level: MEDIUM (context-dependent, can be HIGH under regulation)
- Why: Security/Compliance — regulated workloads may require customer control over encryption keys and
  auditable configuration change tracking.
- ❌ Wrong: X-Ray encryption left on the AWS-owned key with no AWS Config tracking, for a PCI/HIPAA-scoped
  workload whose traces carry request context.
- ✅ Correct: Configure X-Ray to use a **customer-managed KMS key**; track encryption-config changes with
  **AWS Config**; mask PII in spans via CloudWatch Logs data masking when using Transaction Search.
- Detection: X-Ray console encryption setting; AWS Config resource timeline for X-Ray encryption config.
- Impact: Compliance violation; unmanaged key exposure.
- Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-api-config.html (accessed 2026-07-31)

---

## Cloud-Native Design & Operational Patterns

```
Pattern: End-to-end context propagation across AWS services
Category: Communication / Observability
Problem: A request spans API Gateway → Lambda → SQS/SNS/EventBridge → downstream service; without
  consistent trace IDs the trace map breaks into disconnected fragments.
Solution on AWS:
  - OTel default propagation is W3C Trace Context (traceparent). Add the X-Ray Propagator when crossing
    into AWS services that read X-Amzn-Trace-Id (API Gateway active tracing, Lambda).
  - SNS/SQS/EventBridge do PASSIVE instrumentation: an instrumented publisher's tracing header is
    carried to subscribers/targets, preserving the original trace ID.
Services Used: API Gateway (active), Lambda (active/passive), ALB (request tracing header injection),
  SNS/SQS/EventBridge (passive propagation), Step Functions, App Runner, App Mesh.
When to Apply: Any multi-service request path where you need a single connected trace.
When NOT to Apply: Fire-and-forget async with no correlation requirement.
Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Connected traces | Full latency attribution | Must configure propagators correctly at each hop |
  | W3C default | Portable to non-AWS backends | Requires X-Ray propagator add-on for AWS-native hops |
Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services.html (accessed 2026-07-31)
```

```
Operational Domain: Observability (traces tier of metrics/logs/traces)
Pattern: Unified collection via CloudWatch agent (metrics + logs + traces)
RTO/RPO: N/A (telemetry pipeline)
AWS Services: CloudWatch agent v1.300025.0+ (OTLP receiver on 4317/4318, X-Ray tcp_proxy on 2000),
  X-Ray, CloudWatch Logs (aws/spans for Transaction Search).
Architecture: App → OTLP → CloudWatch agent → X-Ray (segments) and/or aws/spans (Transaction Search).
Cost Profile: Medium — one agent replaces the daemon; 100% span ingestion (Transaction Search) is the
  main cost driver, controlled by the indexing percentage.
Automation: Deploy the agent via SSM/ECS task def; store config in SSM Parameter Store; grant
  xray:PutTraceSegments to the agent role/task role.
Runbook Skeleton: Detect (missing traces) → check agent health_check + IAM xray:PutTraceSegments →
  verify OTLP endpoint env (OTEL_EXPORTER_OTLP_TRACES_ENDPOINT) → confirm no port-2000 conflict with a
  leftover X-Ray Daemon → validate on CloudWatch Traces page.
Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#xray-Daemon-migration (accessed 2026-07-31)
```

```
Operational Domain: FinOps for tracing
Pattern: Sampling + indexing budget as a cost control
AWS Services: X-Ray sampling rules, Transaction Search indexing percentage, CloudWatch Logs data masking.
Cost Profile: Traces recorded $5.00/1M; retrieved/scanned $0.50/1M each; free tier 100k recorded +
  1M retrieved/scanned per month; X-Ray Insights billed additionally (per traces recorded). Trace max
  500 KB, 30-day retention at no extra charge. Transaction Search 100% span ingestion adds CloudWatch
  Logs ingestion + indexing cost (see Pricing / verify on CloudWatch pricing page).
Automation: Alarm on TracesRecorded volume; enforce sampling rules via IaC.
Source: https://aws.amazon.com/xray/pricing/ (accessed 2026-07-31)
```

---

## Reference Architectures

```
Reference Architecture: Serverless request tracing (API Gateway → Lambda → DynamoDB)
AWS Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-lambda.html (accessed 2026-07-31)
Context: HTTP API backed by Lambda with a DynamoDB data store.
Services Composition:
  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Edge/API | API Gateway (active tracing) | Samples + injects tracing header, adds a stage node | ALB (request tracing) |
  | Compute | Lambda + AWS Lambda Layer for OpenTelemetry (Application Signals) | Auto-instrument; server span → X-Ray segment | ADOT managed Lambda layer |
  | Data | DynamoDB (inferred segment) | Downstream node derived from caller subsegment | RDS/Aurora (own segment if instrumented) |
  | Store/UX | X-Ray + CloudWatch Traces/Trace Map | Trace storage + visualization | Transaction Search for 100% spans |
Architecture Diagram Description: API Gateway mints/propagates X-Amzn-Trace-Id → Lambda span emitted via
  the OTel Lambda layer (set OTEL_AWS_APPLICATION_SIGNALS_ENABLED=false for tracing-only) → DynamoDB call
  recorded as a subsegment / inferred node.
Key Decisions: Which Lambda layer (Application Signals layer vs. ADOT layer); sampling percentage at API GW.
Scaling Path: Add Transaction Search when sampling loses rare-error visibility; add SLOs via Application Signals.
Cost Baseline: Low-to-medium; dominated by trace volume and any 100% span ingestion.
Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#lambda-instrumentation-migration (accessed 2026-07-31)
```

```
Reference Architecture: Containerized tracing on ECS (OTel Collector sidecar → X-Ray)
AWS Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#ecs-migration (accessed 2026-07-31)
Context: ECS service on bridge networking, app instrumented with OTel/ADOT.
Services Composition:
  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Collector | otel/opentelemetry-collector-contrib OR CloudWatch agent | OTLP receiver + awsxray exporter | Central gateway collector |
  | Config | SSM Parameter Store | Holds collector/agent config | Baked-in config |
  | App | Application container linked to collector | Emits OTLP to collector:4318 | gRPC 4317 |
  | Store | X-Ray | Trace storage | + Transaction Search |
Architecture Diagram Description: App sets OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://<collector>:4318/v1/traces;
  collector `awsxray` exporter (region set) forwards to X-Ray; task role has xray:PutTraceSegments; stop any
  legacy X-Ray Daemon to avoid port-2000 conflicts.
Key Decisions: Sidecar vs. central gateway (tail sampling requires central); bridge vs awsvpc networking.
Scaling Path: Move to a central gateway collector when org-wide tail sampling/policy is needed.
Cost Baseline: Medium.
Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html#ecs-otel (accessed 2026-07-31)
```

---

## Service Equivalence Map — Distributed Tracing / APM across providers

> Included because architects evaluating cross-cloud observability need the mapping. Equivalence ≠
> feature parity — validate against each provider's current docs.

| Capability | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|-----------|-----|--------------|-------|--------------------|
| Distributed tracing backend | AWS X-Ray | Cloud Trace | Application Insights (Azure Monitor) | Application Performance Monitoring (APM) |
| APM / golden-signals layer | CloudWatch Application Signals | Cloud Trace + Cloud Monitoring | Application Insights | APM |
| Span/trace log analytics | CloudWatch Transaction Search (`aws/spans`) | Trace Explorer / Cloud Logging | Log Analytics (Kusto) | Logging Analytics |
| Recommended instrumentation | OpenTelemetry / ADOT | OpenTelemetry (recommended) | OpenTelemetry / Azure Monitor OTel Distro | OpenTelemetry / APM tracer |
| Collector/agent | CloudWatch agent / OTel Collector | OpenTelemetry Collector / Ops Agent | Azure Monitor Agent / OTel Collector | OTel Collector / Management Agent |
| Trace context standard | W3C Trace Context (OTel) / X-Amzn-Trace-Id | W3C Trace Context | W3C Trace Context | W3C Trace Context |
| Metrics | CloudWatch | Cloud Monitoring | Azure Monitor Metrics | OCI Monitoring |
| Logs | CloudWatch Logs | Cloud Logging | Log Analytics | OCI Logging |

Sources: AWS [X-Ray](https://docs.aws.amazon.com/xray/latest/devguide/) ; the equivalence row labels
follow the provider service catalogs referenced in this skill's [research-scope-patterns blueprint](../../.claude/skills/cloud-architecture-researcher/blueprints/research-scope-patterns.md). Cross-provider service names other than AWS are
mapping labels, not version-verified in this pass — **verify against each provider's docs before an
architecture decision** (flagged unverified).

---

## Provider Differentiators (AWS X-Ray, 2026)

```
Differentiator: Transaction Search + aws/spans log group
Category: Observability
Unique Value: 100% span capture as structured CloudWatch Logs in OTel semantic-convention format with
  W3C trace IDs, with a configurable percentage indexed as X-Ray trace summaries; traces up to 10,000 spans.
Architecture Impact: Lets you keep 100% raw spans (for compliance / rare-error hunts) while still
  sampling the indexed summary layer for cost — decouples "capture everything" from "index everything."
When to Leverage: Business-attribute correlation (customer/order), broken-trace elimination, PII-masked spans.
Caveat: 100% ingestion increases CloudWatch Logs + indexing cost; verify current per-GB/index pricing.
Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html (accessed 2026-07-31)
```

```
Differentiator: Native AWS service propagation (active/passive instrumentation)
Category: Observability
Unique Value: API Gateway (active), Lambda (active/passive), ALB (request tracing), and passive
  propagation through SNS/SQS/EventBridge keep the original trace ID across managed AWS boundaries
  without app code — including Amazon Bedrock AgentCore for AI-agent request tracing.
Architecture Impact: You can trace across fully managed, non-instrumentable AWS services via inferred
  segments and propagated headers.
When to Leverage: Serverless / event-driven architectures heavy on managed AWS services.
Caveat: Requires the X-Ray propagator when mixing OTel (W3C default) with AWS-native hops.
Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services.html (accessed 2026-07-31)
```

---

## Scenario Coverage

**Standard Case**: New microservice / serverless workload needing end-to-end tracing.
- Approach: Instrument with ADOT/OTel; collect via CloudWatch agent or OTel Collector; conservative
  head sampling with 100% on money-path routes; annotations for business keys.
- Key Decisions: ADOT vs. raw OTel vs. Application Signals; sampling percentages; propagator config.

**Edge Case**: Rare intermittent errors lost under sampling, or compliance requiring 100% capture.
- Approach: Enable Transaction Search (100% spans to `aws/spans`, bounded index %); or central gateway
  collector with tail sampling to retain all error/slow traces; mask PII via CloudWatch Logs data masking;
  customer-managed KMS key + AWS Config tracking.

**Anti-Pattern Case**: Team proposes standardizing new services on the X-Ray SDK + X-Ray Daemon.
- Clarification: Flag that the SDK/Daemon are in maintenance mode as of 2026-02-25 (EOS 2027-02-25).
  Ask whether tracing must also feed a non-AWS backend, then steer to ADOT/OTel + CloudWatch agent/Collector.

---

## Source Bibliography

### Primary Sources (official AWS docs — accessed 2026-07-31)
- [AWS X-Ray Developer Guide (home)](https://docs.aws.amazon.com/xray/latest/devguide/)
- [X-Ray concepts](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html) — segments, subsegments, traces, sampling, tracing header, annotations/metadata, groups, errors/faults/throttle
- [Migrating from X-Ray instrumentation to OpenTelemetry](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html) — OTel-first guidance, concept mapping, collector/daemon migration, Lambda layers, ECS task defs
- [X-Ray SDK and Daemon Support timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html) — maintenance mode start 2026-02-25
- [Integrating AWS X-Ray with other AWS services](https://docs.aws.amazon.com/xray/latest/devguide/xray-services.html) — active/passive instrumentation across Lambda, API Gateway, ALB, SNS/SQS/EventBridge, Step Functions, App Runner, App Mesh, Beanstalk, Bedrock AgentCore
- [AWS Distro for OpenTelemetry and AWS X-Ray](https://docs.aws.amazon.com/xray/latest/devguide/xray-services-adot.html)
- [Tracking X-Ray encryption configuration changes with AWS Config](https://docs.aws.amazon.com/xray/latest/devguide/xray-api-config.html)
- [CloudWatch Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html) — 100% span ingestion, aws/spans, 10,000-span traces, OTel semantic convention
- [CloudWatch Transaction Search — ingesting spans](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-spans.html)
- [CloudWatch Application Signals (Working with)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Sections.html)
- [AWS X-Ray pricing](https://aws.amazon.com/xray/pricing/) — $5.00/1M recorded, $0.50/1M retrieved, $0.50/1M scanned; free tier 100k recorded + 1M retrieved/scanned; 500 KB max trace; 30-day retention; Insights billed separately
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/)

### Secondary Sources (official AWS blog — cite with date)
- [Announcing AWS X-Ray SDKs/Daemon end-of-support and OpenTelemetry migration](https://aws.amazon.com/blogs/mt/announcing-aws-x-ray-sdks-daemon-end-of-support-and-opentelemetry-migration) — communicates end-of-support 2027-02-25 (2026)
- [AWS X-Ray SDKs/Daemon migration to OpenTelemetry](https://aws.amazon.com/blogs/mt/aws-x-ray-sdks-daemon-migration-to-opentelemetry/) (2026)
- [Adaptive sampling with AWS X-Ray to capture critical spans](https://aws.amazon.com/blogs/mt/adaptive-sampling-with-aws-x-ray-to-capture-critical-spans/) (2025)
- [Amazon CloudWatch launches full visibility into application transactions](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cloudwatch-visibility-application-transactions) — Transaction Search GA, Nov 2024

> ⚠️ **Currency flags.** The "Amazon CloudWatch launches full visibility into application transactions"
> announcement is dated **2024-11** (>12 months old) — retained because it is the GA milestone for
> Transaction Search, which is current stable. The end-of-support date **2027-02-25** is sourced from
> the AWS blog announcement rather than the timeline doc page (whose table showed only the
> maintenance-mode start) — verify the exact EOS date on the timeline page before publishing downstream.

---

## Agent Operation Notes (confidence for downstream skill authoring)

- **High confidence**: OTel-first direction; SDK/Daemon maintenance mode 2026-02-25; core X-Ray concepts,
  limits (64 KB segment, 500 KB trace, 30-day retention, 50 indexed annotations/trace); OTLP ports
  4317/4318 and awsproxy 2000; pricing figures; AWS service integration matrix; Transaction Search model.
- **Medium confidence**: Exact end-of-support date (2027-02-25 — blog-sourced, confirm on timeline page);
  Transaction Search per-GB/index pricing (not itemized on the X-Ray pricing page — confirm on the
  CloudWatch pricing page).
- **Unverified / must confirm**: Non-AWS rows of the Service Equivalence Map (GCP/Azure/OCI labels are
  mapping-only, not version-verified this pass); `ARCHITECTURE_CONTEXT` (requester did not specify —
  assumed general microservices+serverless).
