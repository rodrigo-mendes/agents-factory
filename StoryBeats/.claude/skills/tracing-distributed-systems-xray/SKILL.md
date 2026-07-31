---
name: tracing-distributed-systems-xray
description: "Instruments and configures distributed tracing for AWS microservices and serverless workloads using AWS X-Ray, OpenTelemetry/ADOT, and the CloudWatch observability stack. Use when designing tracing architectures, migrating from the deprecated X-Ray SDK/Daemon to OpenTelemetry, configuring sampling strategies and trace encryption, or enabling Transaction Search for 100% span capture. Targets the 2026 AWS X-Ray state: OpenTelemetry is the primary instrumentation standard; X-Ray SDK and Daemon are in maintenance mode (2026-02-25), end-of-support 2027-02-25."
---

## Function
Specialist in distributed tracing architecture and instrumentation for AWS X-Ray (2026 OTel-first edition) on microservices and serverless workloads.

## Version Context

**Technology**: AWS X-Ray + OpenTelemetry / ADOT
**Target version**: 2026 edition (OTel-first)
**Support status**: X-Ray backend — Active. X-Ray SDK/Daemon — Maintenance-only (EOS 2027-02-25).

**Critical transitions in this edition**:
- X-Ray SDK and X-Ray Daemon → maintenance mode 2026-02-25 (security fixes only, no new features)
- X-Ray SDK and X-Ray Daemon → end-of-support **2027-02-25**
- Primary instrumentation path → OpenTelemetry SDKs / ADOT → OTel Collector or CloudWatch agent (v1.300025.0+)
- X-Ray console → merged into CloudWatch Traces / Trace Map pages
- Transaction Search → GA Nov 2024; supports traces up to 10,000 spans

**Deprecations**:
- `aws-xray-sdk-*` → use OpenTelemetry SDK + `awsxray` exporter
- X-Ray Daemon (UDP 2000) → use CloudWatch agent v1.300025.0+ or OTel Collector

⚠️ **Version Lock**: Reject any pattern recommending the X-Ray SDK or X-Ray Daemon for new applications — maintenance-mode as of 2026-02-25.

---

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 6 mandatory patterns with full config/code examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 3 architectural crossroads: instrumentation stack, sampling strategy, collector topology
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 5 anti-patterns with ❌ wrong / ✅ correct examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Key limits and essential CLI
- **[External Resources](#external-resources)** — Official AWS docs (all accessed 2026-07-31)

---

## Blueprints & Guardrails

### ✅ Always Do

See [Always Do Patterns](./blueprints/always-do-patterns.md) for full config and code examples.

- **Instrument new workloads with OpenTelemetry / ADOT (not the X-Ray SDK)** — SDK is maintenance-mode; all new features land in OTel. Emit OTLP (http `4318` or gRPC `4317`) to a local collector; the `awsxray` exporter converts spans to X-Ray segments/subsegments.
- **Replace the X-Ray Daemon with CloudWatch agent (v1.300025.0+) or OTel Collector** — Daemon is maintenance-mode. Stop any running Daemon first to avoid UDP port 2000 conflicts with the `awsproxy` extension.
- **Apply explicit sampling rules; reserve 100% only for critical low-volume paths** — Default reservoir is 1 req/sec + 5% additional. Configure per-service X-Ray sampling rules; use X-Ray Remote Sampler (ADOT: Java/.NET/Go/Python/Node.js) for dynamic rule updates without redeployment.
- **Put searchable business keys in annotations; put bulk context in metadata** — Annotations are indexed for filter expressions (`annotation.order_id = "123"`); metadata is not. For OTel spans, declare searchable keys under `aws.xray.annotations`. Cap: 50 annotations per trace.
- **Enable Transaction Search when 100% span visibility is required** — Ingests 100% of spans into `aws/spans` CloudWatch Logs group (OTel semantic conventions, W3C trace IDs); set a bounded indexing percentage for X-Ray trace summaries. Supports up to 10,000 spans per trace.
- **Encrypt trace data; use a customer-managed KMS key for regulated workloads** — Trace data may contain sensitive request context. Track config changes via AWS Config; mask PII in `aws/spans` via CloudWatch Logs data masking.

### ⚠️ Ask First

See [Ask First Decisions](./blueprints/ask-first-decisions.md) for full option matrices.

- **Instrumentation stack: raw OTel SDK vs. ADOT vs. CloudWatch Application Signals** — Ask: "Must tracing also feed a non-AWS backend (Grafana/Datadog/Jaeger)?" Yes → raw OTel/ADOT with collector fan-out. AWS-only + fastest onboarding → Application Signals (highest AWS coupling).
- **Sampling strategy: head sampling vs. tail sampling vs. Transaction Search** — Ask: "Is the pain missing error traces, or is it cost?" Missing errors → tail sampling or Transaction Search. Cost reduction → tighten head sampling rules.
- **Collector topology: sidecar vs. per-host agent vs. central gateway** — Ask: "Is tail sampling required?" Yes → central gateway collector is mandatory (tail sampling requires all spans of a trace in one place).

### 🚫 Never Do

See [Never Do Patterns](./blueprints/never-do-patterns.md) for ❌ wrong / ✅ correct code pairs.

- **Build new instrumentation on the X-Ray SDK / Daemon** — EOS 2027-02-25; forces re-platform before deadline. Use ADOT/OTel + CloudWatch agent or OTel Collector.
- **Trace 100% of high-volume requests without a sampling plan** — Recorded traces billed at $5.00/1M; unbounded health-check/polling traffic dominates spend and drowns signal in the service map.
- **Trust inbound `X-Amzn-Trace-Id` from untrusted clients** — Forged headers manipulate trace IDs and sampling decisions (trace poisoning). Strip/regenerate at the trust boundary; the first X-Ray-integrated service mints the root trace.
- **Store searchable high-cardinality keys in metadata** — Metadata is not indexed; filter expressions against metadata silently return nothing. Use `putAnnotation` / `aws.xray.annotations` for any key you will filter on.
- **Leave trace encryption on the AWS-owned default key for regulated workloads** — PCI/HIPAA requires customer control over key rotation and auditable config history. Configure a customer-managed KMS key + AWS Config tracking.

---

## Integration Patterns

See [Ask First Decisions](./blueprints/ask-first-decisions.md) for collector topology diagrams and ECS/Lambda configs.

- **OTel SDK / ADOT ↔ X-Ray** — App emits OTLP → collector with `awsxray` exporter (or CloudWatch agent) → X-Ray. Task/instance IAM role needs `xray:PutTraceSegments` + `xray:PutTelemetryRecords`.
- **API Gateway + Lambda ↔ X-Ray** — Enable API Gateway active tracing (injects `X-Amzn-Trace-Id`); attach AWS Lambda Layer for OpenTelemetry (Application Signals) or ADOT managed layer to Lambda.
- **SNS / SQS / EventBridge ↔ X-Ray** — Passive propagation: publisher tracing header is carried to subscribers/targets automatically, preserving the original trace ID without application code changes.
- **OTel (W3C `traceparent`) ↔ AWS-native hops (`X-Amzn-Trace-Id`)** — Add the X-Ray propagator alongside W3C: `OTEL_PROPAGATORS=tracecontext,xray` at all API Gateway and Lambda boundaries.

**Common problems**:
- **Missing traces after collector migration** → Check collector `health_check`; confirm IAM `xray:PutTraceSegments`; verify `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`; confirm no port-2000 conflict from a residual X-Ray Daemon process.
- **Disconnected trace fragments across services** → Missing X-Ray propagator at an AWS-native hop. Set `OTEL_PROPAGATORS=tracecontext,xray` on all Lambda/API Gateway-connected services.
- **Filter expression `annotation.key = "..."` returns nothing** → Key was stored as metadata, not annotation. Re-instrument with `putAnnotation` or add the key to `aws.xray.annotations` in the OTel config.

---

## Verification Loop

Run after each instrumentation or infrastructure change:

### 1. Confirm traces reach X-Ray
```bash
aws xray get-trace-summaries \
  --start-time $(date -d '5 minutes ago' +%s) \
  --end-time $(date +%s) \
  --region <region>
# Expected: non-empty TraceIds list; no AccessDenied errors
```

### 2. Validate sampling rules
```bash
aws xray get-sampling-rules --region <region>
# Expected: your custom rules listed with correct reservoir and fixed-rate values
```

### 3. Check collector / CloudWatch agent health
```bash
# OTel Collector (health_check extension, default port 13133):
curl -s http://localhost:13133/
# Expected: {"status":"Server available","uptime":"..."}

# CloudWatch agent:
amazon-cloudwatch-agent-ctl -m ec2 -a status
# Expected: "status": "running"
```

### 4. Confirm annotation search
```bash
aws xray get-trace-summaries \
  --filter-expression 'annotation.order_id = "test-001"' \
  --start-time $(date -d '10 minutes ago' +%s) \
  --end-time $(date +%s) \
  --region <region>
# Expected: matching trace(s) returned
```

**Troubleshooting**:
- `AccessDenied` on PutTraceSegments → Add `xray:PutTraceSegments` + `xray:PutTelemetryRecords` to task/instance role
- No traces after 2+ minutes → Verify `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` and that the collector/agent is running on the configured OTLP port
- Port-2000 conflict in logs → Stop the legacy X-Ray Daemon before starting the `awsproxy` extension or CloudWatch agent

---

## Quick Reference

**Essential AWS CLI commands**:
```bash
# List sampling rules
aws xray get-sampling-rules --region <region>

# Retrieve trace summaries (last 5 minutes)
aws xray get-trace-summaries \
  --start-time $(date -d '5 min ago' +%s) --end-time $(date +%s)

# Get a full trace by ID
aws xray batch-get-traces --trace-ids <traceId>

# Check encryption config
aws xray get-encryption-config --region <region>
```

**Critical limits**:

| Resource | Limit | Notes |
|----------|-------|-------|
| Segment document | 64 KB max | Single service per request |
| Trace (all segments) | 500 KB max | End-to-end request |
| Trace retention | 30 days | Included; no extra charge |
| Indexed annotations | 50 per trace | Annotations over cap dropped |
| Transaction Search spans | 10,000 per trace | `aws/spans` log ingestion |
| X-Ray free tier | 100k recorded + 1M retrieved + 1M scanned / month | Per account |
| Recorded trace cost | $5.00 / 1M | Primary billing dimension |
| Retrieved / scanned | $0.50 / 1M each | Query cost |

---

## External Resources

### Official AWS Documentation (accessed 2026-07-31)
- [AWS X-Ray Developer Guide](https://docs.aws.amazon.com/xray/latest/devguide/)
- [X-Ray concepts](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html) — segments, traces, sampling, annotations/metadata, groups
- [Migrating from X-Ray to OpenTelemetry](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html) — OTel-first guidance, Lambda/ECS migration
- [X-Ray SDK and Daemon Support timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html) — maintenance mode 2026-02-25
- [Integrating X-Ray with AWS services](https://docs.aws.amazon.com/xray/latest/devguide/xray-services.html) — API Gateway, Lambda, ALB, SNS/SQS/EventBridge, Bedrock AgentCore
- [CloudWatch Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html)
- [CloudWatch Application Signals](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Sections.html)
- [AWS Distro for OpenTelemetry and X-Ray](https://docs.aws.amazon.com/xray/latest/devguide/xray-services-adot.html)
- [X-Ray encryption config + AWS Config](https://docs.aws.amazon.com/xray/latest/devguide/xray-api-config.html)
- [AWS X-Ray Pricing](https://aws.amazon.com/xray/pricing/)

### AWS Blog (2025-2026)
- [Announcing X-Ray SDKs/Daemon end-of-support and OTel migration](https://aws.amazon.com/blogs/mt/announcing-aws-x-ray-sdks-daemon-end-of-support-and-opentelemetry-migration)
- [Adaptive sampling with AWS X-Ray](https://aws.amazon.com/blogs/mt/adaptive-sampling-with-aws-x-ray-to-capture-critical-spans/) (2025)

### Research Base
- Source: `StoryBeats/docs/research_cloud_AWS_Observability-Distributed-Tracing_XRay-2026.md` (repo root-relative path; research date 2026-07-31; review by 2027-07-31)

> ⚠️ **Currency note**: EOS date 2027-02-25 is blog-sourced — verify against the [X-Ray SDK and Daemon Support timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html) before publishing downstream architecture decisions.
