---
name: monitoring-quarkus-lambda-v3-40
description: "Guides custom CloudWatch metrics from Quarkus 3.40 LTS Lambdas: EMF to stdout, choice of metric approach, bounded dimensions and cost. Use when emitting business or technical metrics. Not for alarms, logging, tracing, built-in Lambda metrics or Quarkus 4."
---

# Monitoring Quarkus AWS Lambda custom metrics 3.40

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1 (`quarkus-amazon-lambda`)** and the CloudWatch EMF specification as published on 2026-10-28. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: custom metrics into CloudWatch (EMF to stdout, `aws-embedded-metrics-java`, Micrometer, Powertools metrics, PutMetricData), dimensions, cardinality and cost. Neighbours: [logging](../logging-quarkus-lambda-v3-40/SKILL.md), [tracing](../tracing-quarkus-lambda-v3-40/SKILL.md) and [handler development](../developing-quarkus-amazon-lambda-v3-40/SKILL.md). Names only: `observing-quarkus-lambda`, `monitoring-cloudwatch-observability` (alarms, dashboards), `provisioning-aws-cloudwatch-v6` (Terraform), `implementing-lambda-powertools-java`, `managing-aws-costs`. Quarkus 4 is out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 (2026-10-19) | https://quarkus.io/releases |
| Extension | `io.quarkus:quarkus-amazon-lambda` 3.40.1.1 | https://quarkus.io/version/3.40/guides/aws-lambda |
| CloudWatch EMF | JSON specification; limits in [Quick Reference](#quick-reference) | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html |
| Micrometer | 1.17.1 managed by the Quarkus 3.40.1.1 BOM (medium confidence) | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/bom/application/pom.xml (partial read) ; https://repo1.maven.org/maven2/io/micrometer/micrometer-bom/1.17.1/micrometer-bom-1.17.1.pom |
| `aws-embedded-metrics` | 4.2.0, `lastUpdated` 2024-08-02, no later release | https://repo1.maven.org/maven2/software/amazon/cloudwatchlogs/aws-embedded-metrics/maven-metadata.xml |
| `powertools-metrics` | 2.11.0, `lastUpdated` 2026-10-06 | https://repo1.maven.org/maven2/software/amazon/lambda/powertools-metrics/maven-metadata.xml |
| Quarkiverse CloudWatch registry | none exists (High, family fact) | https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/ |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- `aws-embedded-metrics-java` last shipped 2024-08-02, more than 12 months ago; the README states no maintenance status (medium confidence, absence of evidence, M4). Treat it as a freshness risk.
- Quarkus 3.40 is community-maintained until 2027-09-30; Quarkus 4.0.0 is "Upcoming" with no date. Pin 3.40.x.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [EMF implementation (Java sketch, handler, test)](./blueprints/emf-implementation.md)
- [Cardinality, cost and built-in metrics](./blueprints/cardinality-cost-and-builtins.md)
- [Verification Loop](./blueprints/verification-loop.md)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Write one EMF document as one complete JSON object on one stdout line.** The log event must be valid JSON "with no additional data at the beginning or end" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). See [patterns](./blueprints/always-do-patterns.md#1-one-document-one-line).
- **Send `_aws.Timestamp` in epoch milliseconds and `_aws.CloudWatchMetrics` with `Namespace`, `Dimensions`, `Metrics`.** A MetricDirective "MUST contain" all three ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). See [patterns](./blueprints/always-do-patterns.md#2-timestamp-and-directive).
- **Make every dimension and metric a flat root member of the right type.** "The root node MUST contain all Target members" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). See [patterns](./blueprints/always-do-patterns.md#3-flat-root-members).
- **Split documents at 100 MetricDefinitions.** The other limits (30 keys per DimensionSet, 100 values per array) are in the patterns blueprint. Over 100 definitions, "CloudWatch does not extract any metrics" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). See [patterns](./blueprints/always-do-patterns.md#4-document-limits).
- **Use only CloudWatch units and keep one unit per metric.** Data points with different units "are aggregated separately" ([metric concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html)). See [patterns](./blueprints/always-do-patterns.md#5-units-and-resolution).
- **Write the invocation's metrics before the handler returns.** Lambda freezes the environment after the invocation ([execution environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). See [patterns](./blueprints/always-do-patterns.md#6-flush-before-return).
- **Keep dimensions to a bounded set; put unbounded identifiers in non-dimension root properties.** Every unique dimension combination becomes a custom metric ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). See [patterns](./blueprints/always-do-patterns.md#7-bounded-dimensions).
- **Read function health from the `AWS/Lambda` built-in metrics.** Lambda sends them automatically at no additional charge ([Lambda metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html)). See [patterns](./blueprints/always-do-patterns.md#8-built-in-metrics).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Metric approach (never a default that relies on an (unverified) option) | a) hand-written EMF to stdout; b) `aws-embedded-metrics` 4.2.0 (last release 2024-08-02, Quarkus/native behaviour unverified); c) Powertools `powertools-metrics` 2.11.0 (Quarkus support not stated on any page, (unverified); Powertools says frameworks are "not officially supported"); d) `quarkus-micrometer` + your own `MeterRegistry` producer with `micrometer-registry-cloudwatch2` (no Quarkiverse registry; push registry on a frozen Lambda is (unverified)); e) OpenTelemetry (same push question); f) `PutMetricData` (network call, IAM action, per-request charge). Propose (a) unless the organisation already standardised on another; record in an ADR. See [decisions](./blueprints/ask-first-decisions.md#d1-metric-approach) | "Which emission path? Is there an existing standard (Powertools, Micrometer, OpenTelemetry)? Can you run a deployed smoke test?" |
| Tenant as a dimension vs tenant in the log (family rule 7) | A: `TenantId` dimension (one metric per tenant combination, per-tenant alarms, needs an ADR when unbounded). B: `tenantId` as a root property plus Logs Insights `stats ... by tenantId`. C: bounded proxy dimension (for example `TenantTier`) plus `tenantId` property. Without an ADR use C. See [decisions](./blueprints/ask-first-decisions.md#d2-tenant-as-dimension-or-in-the-log) | "How many tenants now and at most? Are per-tenant alarms required? Monthly metric budget?" |
| Lambda log format and level when emitting EMF | Text (default) vs JSON with `ApplicationLogLevel` INFO or more detailed vs JSON with WARN or higher (EMF lines without `level` would be dropped, medium confidence). See [decisions](./blueprints/ask-first-decisions.md#d3-lambda-log-format-and-level) | "Which log format did the logging skill select? Is a deployed smoke test of the metric possible?" |
| Resolution 60 s vs 1 s | Default 60; 1 s keeps sub-minute data 3 hours and costs more for alarms. See [decisions](./blueprints/ask-first-decisions.md#d4-resolution) | "Does any metric need sub-minute alarming?" |
| Cold-start visibility | `ColdStart` custom metric (billed) vs `Init Duration` from the `REPORT` line via Logs Insights. See [decisions](./blueprints/ask-first-decisions.md#d5-cold-start-visibility) | "Must the cold-start rate be alarmed or only reported?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Write EMF through the Quarkus logger (`Log.info(emfJson)`), severity high: the default console format prefixes timestamp and level, while EMF needs JSON "with no additional data at the beginning or end" ([Quarkus logging](https://quarkus.io/version/3.40/guides/logging), [EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)); the `quarkus-logging-json` case is in [F1](./blueprints/never-do-patterns.md#f1-emf-through-the-quarkus-logger-severity-high) | `System.out.println(emfJson)`, one raw line ([Lambda Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)) |
| Use `requestId`, `orderId`, `userId` or an unbounded `tenantId` as a dimension; no unbounded tenant dimension without an ADR ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html), [Quarkus Micrometer](https://quarkus.io/version/3.40/guides/telemetry-micrometer)) | Bounded dimensions plus the identifier as a root property (Ask First: tenant) ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)) |
| Re-emit `Invocations`, `Errors`, `Throttles`, `Duration` or `ConcurrentExecutions` as custom metrics ([Lambda metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)) | Read them from `AWS/Lambda`; emit business outcomes only ([Lambda metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html)) |
| Start a custom namespace with `AWS/` ([PutMetricData](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html)) | A custom namespace such as `SaaS/Orders` ([PutMetricData](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html)) |
| Put more than 100 MetricDefinitions in one document ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)) | Chunk into documents of at most 100 ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)) |
| Write the timestamp in seconds or as a string ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)) | Epoch milliseconds within 14 days past and 2 hours future ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)) |
| Publish from a background thread after the handler returns ([execution environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)) | Write synchronously before returning ([execution environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)) |
| Emit NaN, Infinity or out-of-range values ([MetricDatum](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)) | Skip the metric when the value is undefined ([MetricDatum](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| EMF documents per log event | max 100 MetricDefinitions across all directives; over the limit CloudWatch extracts none | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html |
| Keys per DimensionSet | 30 (AWS spec). Powertools page says "9" and "30" on one page (medium confidence, M13): follow the AWS spec | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html ; https://docs.aws.amazon.com/powertools/java/latest/core/metrics/ |
| Values per numeric array / document size | 100 / 1 MB | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html |
| Timestamp window | epoch ms, at most 14 days past and 2 hours future | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html |
| `Unit` default | `None` | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html |
| `StorageResolution` default | `60` (allowed 1 or 60) | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html |
| `quarkus.micrometer.binder-enabled-default` default | `true`; JVM/system meters would become billed custom metrics (medium confidence; page read in part, L6) | https://quarkus.io/version/3.40/guides/telemetry-micrometer |
| Custom metric price | "$0.30 per metric per month for the first 10,000" as quoted for US East (N. Virginia); the page is unversioned and was read as tool summaries (medium confidence) | https://aws.amazon.com/cloudwatch/pricing/ |
| PutMetricData quota | 500 requests per second per Region, adjustable; max 1000 metrics and 1 MB per request | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_limits.html ; https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html |
| Metric visibility after first publish | statistics up to 2 minutes, `list-metrics` up to 15 minutes | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html |
| Metric retention | metrics cannot be deleted; expire 15 months after the last data point | https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html |

## External Resources

All fetched 2026-10-28.

- EMF specification: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
- Lambda metrics: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html
- Quarkus 3.40 Micrometer guide: https://quarkus.io/version/3.40/guides/telemetry-micrometer
- Quarkus 3.40 logging guide: https://quarkus.io/version/3.40/guides/logging
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
