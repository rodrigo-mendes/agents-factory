# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Every decision here is put to the user. Record each choice in an ADR.

## Contents

- [D1. Metric approach](#d1-metric-approach)
- [D2. Tenant as dimension or in the log](#d2-tenant-as-dimension-or-in-the-log)
- [D3. Lambda log format and level](#d3-lambda-log-format-and-level)
- [D4. Resolution](#d4-resolution)
- [D5. Cold-start visibility](#d5-cold-start-visibility)

## D1. Metric approach

Propose (a) unless the organisation already standardised on another option. Never present (c) as supported on Quarkus or (d)/(e) as safe on Lambda: two items cannot be settled from documentation. Powertools metrics on Quarkus is not stated on any page (unverified). How a push registry behaves on a frozen Lambda environment is not stated on any official page (unverified; inference only from the [lifecycle page](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| (a) Hand-written EMF to stdout | No extra dependency; synchronous stdout write; format fully specified by the [EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html); works for JVM and native | You implement the 100/30/100 limits and splitting yourself | Default candidate; few, well-known metrics |
| (b) `software.amazon.cloudwatchlogs:aws-embedded-metrics` 4.2.0 | `MetricsLogger` is "thread-safe"; Lambda environment writes "over stdout" (README on main branch, medium confidence) | Last release 2024-08-02 (more than 12 months); behaviour under Quarkus, native and Lambda JSON log format is not stated (unverified) | Team already standardised on it, JVM only, after a deployed test |
| (c) `software.amazon.lambda:powertools-metrics` 2.11.0, functional API | Writes EMF "asynchronously by logging metrics to standard output"; `ColdStart` metric; functional API "eliminates the AspectJ runtime dependency" (docs are the "latest" page, medium confidence) | Powertools tenet: AWS Lambda only, frameworks "not officially supported"; Quarkus compatibility not stated (unverified); "GraalVM support" is one bullet without detail (medium confidence). Use the metrics module only; Powertools Java logging inside Quarkus is (unverified) and the Quarkus logging guide says not to include any Log4j dependency | Organisation uses Powertools in other Java Lambdas; JVM mode after a deployed test |
| (d) `quarkus-micrometer` + own `@Produces MeterRegistry` + `io.micrometer:micrometer-registry-cloudwatch2` 1.17.1 | Familiar Micrometer API; `@Counted` and `@Timed` supported by Quarkus | No Quarkiverse CloudWatch registry exists (High); you write the producer; push registry, default step 1 minute, frozen-environment behaviour (unverified); constructor and SDK client requirements and native support not on the docs page (unverified); default binders on (medium confidence) | Only with an ADR, for example code shared with non-Lambda services |
| (e) OpenTelemetry to the CloudWatch OTLP endpoint | AWS: "For new implementations, we recommend using OpenTelemetry to publish custom metrics"; SigV4, `cloudwatch:PutMetricData` | Periodic export has the same frozen-environment question (unverified); overlaps the [tracing skill](../../tracing-quarkus-lambda-v3-40/SKILL.md) | Only together with the tracing decision |
| (f) `PutMetricData` through the AWS SDK | Immediate API ingestion; up to 150 values per metric | One network call inside the invocation (latency not researched); needs `cloudwatch:PutMetricData`; 500 requests per second per Region quota; per-request charge (price unit ambiguous, unverified) | Metrics that must not depend on log delivery; low-rate jobs |

Micrometer detail for (d): set `quarkus.micrometer.binder-enabled-default=false` or the JVM and system meters are published as billed custom metrics (medium confidence). If (d) or (e) is mandated, force a publish before the handler returns and verify in a deployed function. If (c) is mandated, use the functional API and test in a deployed function.

Ask: "Which emission path? Is there an existing standard (Powertools, Micrometer, OpenTelemetry)? Can a deployed smoke test be run before release?"

## D2. Tenant as dimension or in the log

Family rule 7: no unbounded tenant cardinality without an ADR. CloudWatch "does not aggregate across dimensions for your custom metrics" ([metric concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html)).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. `TenantId` dimension | Per-tenant graphs and alarms on metrics | Every unique dimension combination is a separate metric billed per month (US East $0.30 for the first 10,000, medium confidence); needs an ADR when the tenant count is unbounded | Small, bounded, contractually known tenant set; per-tenant SLO alarms |
| B. `tenantId` property + Logs Insights | No per-tenant metric cost; `stats sum(...) by tenantId, bin(1h)` and `pct(...)` ([Logs Insights stats](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Stats.html)) | Query-time cost (scan price not read, unverified); no metric alarm per tenant; `countDistinct` is approximate at high cardinality | Many or unbounded tenants; reporting, not alerting |
| C. Bounded proxy + property | Bounded metric count (tiers x metrics x dimension sets); per-tenant drill-down in logs | No per-tenant alarms | Default proposal for SaaS without an ADR |

Ask: "How many tenants exist now and at most? Are per-tenant alarms required? What is the monthly metric budget?"

## D3. Lambda log format and level

Each statement is High; their combination for Java and Quarkus is an inference.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Text (default) | "the default log format for all Lambda runtimes is plain text"; EMF lines untouched | No Lambda-side log-level filtering (needs JSON) | No need for filtering |
| JSON, level INFO or more detailed | Lambda "doesn't double-encode any logs that are already JSON encoded", so a raw EMF line should stay at the root (medium confidence); AWS recommends testing EMF after switching | Larger log events | The logging skill chose JSON |
| JSON, level WARN or higher | Fewer application logs | Lambda assigns INFO to JSON lines with a missing or invalid `level` and does not send INFO when the level is WARN, so EMF lines without `level` would be dropped (medium confidence) | Avoid when EMF is used |

Sources: [log format](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html), [log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html), [Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html). The Node.js page warns that switching to JSON can make CloudWatch miss EMF written with `console.log`; no Java-specific statement exists (medium confidence). For Quarkus native on `provided.al2023`, Lambda natively captures JSON application logs only for listed runtimes; for custom runtimes it only sets `AWS_LAMBDA_LOG_FORMAT` and `AWS_LAMBDA_LOG_LEVEL` for the runtime to honour (medium confidence). `LoggingConfig` infrastructure belongs to `provisioning-aws-*-v6` (family rule 4).

Ask: "Which log format did the logging skill select? If JSON, set ApplicationLogLevel to INFO or more detailed and run a deployed smoke test that the metric appears."

## D4. Resolution

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `StorageResolution` 60 (default) | 1-minute data kept 15 days, then rolled up | No sub-minute periods | Almost all business metrics |
| `StorageResolution` 1 | Periods of 1, 5, 10, 30 s | Sub-minute data kept 3 hours; "higher charge for high-resolution alarms"; for EMF alarms flush logs at 5 s or less and consider M out of N alarms ([EMF alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Alarms.html)) | Short spikes that must alarm within seconds |

Source: [metric concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html). Ask: "Does any metric need sub-minute alarming? Default 60."

## D5. Cold-start visibility

| Option | Optimizes | Sacrifices |
|---|---|---|
| `ColdStart` count metric (Powertools adds it with `captureColdStart`) | Alarmable | Billed custom metric; Powertools on Quarkus is (unverified) |
| `Init Duration` from the `REPORT` line via Logs Insights | No metric cost | Not alarmable as a metric; `InitDuration` is not in the `AWS/Lambda` list (medium confidence, absence of evidence) |

`Duration` "does not include cold start time" ([metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)). With SnapStart the restore phase reports through `RESTORE_REPORT`; JVM + SnapStart vs native stays Ask First (family rule 3, see the [developing skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md)). Ask: "Must the cold-start rate be alarmed or only reported?"
