# Research: Custom metrics from Quarkus 3.40 LTS AWS Lambda functions into Amazon CloudWatch (EMF, Micrometer, Powertools, PutMetricData)

Unit U13 of the quarkus-aws-saas family. Future skill: `monitoring-quarkus-lambda-v3-40` (package `quarkus-aws`).
Source item: "observability in code: business and technical metrics, per-tenant dimensions".
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/_family_facts_v3.40.md`.
Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md` (rules 1, 3, 4, 7, 9-12) and the inherited evidence rule and tag notation (`building-agent-packages/blueprints/policy/`).

All pages were read on **2026-10-28** with the WebFetch tool. Quoted sentences were returned verbatim by the tool (it caps verbatim quotes at about 125 characters, so long passages are paraphrased and not put in quotes). Every `[Sn]` tag resolves to exactly one URL in the [Source Bibliography](#source-bibliography), all read 2026-10-28. Pages read only in part, or that came back with no body text, are listed as coverage limits (L-ids) in [Research Gaps](#research-gaps).

Evidence levels used here. AWS service documentation (CloudWatch, Lambda, API references) is not versioned; it documents the current service and is treated as High, as the family facts do. Library pages that are "latest" or main-branch (Powertools, aws-embedded-metrics-java README, Micrometer docs for a different patch) are at most medium. Pricing is medium (unversioned, region-specific). Inferences that combine two statements are tagged (medium confidence) or (unverified) as stated per item.

Scope boundary. Covered: how a Quarkus 3.40 Lambda emits custom business/technical metrics into CloudWatch, the options and how to choose (Ask-First), EMF document rules and limits, EMF and Lambda log format / log-level filtering, Micrometer status, Powertools Metrics status, PutMetricData (mention only), Lambda built-in metrics not to re-emit, per-tenant dimensions and cardinality/cost, naming and units, native-mode notes. Referenced by name and not repeated: logging (U11), tracing (U12), alarms and dashboards infrastructure (`monitoring-cloudwatch-observability`, `provisioning-aws-cloudwatch-v6`), handler wiring and packaging (U1, `developing-quarkus-amazon-lambda-v3-40`), Lambda IaC (`provisioning-aws-*-v6`, family rule 4). Quarkus 4 is out of scope (family rule 1).

## Contents

- [Metadata](#metadata)
- [Executive Summary](#executive-summary)
- [Architectural Guardrails](#architectural-guardrails): [Mandatory](#-mandatory-patterns), [Conditional](#️-conditional-patterns), [Forbidden](#-forbidden-patterns)
- [Migration Guide](#migration-guide)
- [Implementation Blueprint](#implementation-blueprint)
- [Quality Control](#quality-control)
- [Production Readiness](#production-readiness)
- [Reference Implementations](#reference-implementations)
- [Source Bibliography](#source-bibliography)
- [Research Gaps](#research-gaps)
- [Research Iteration Changelog](#research-iteration-changelog)
- [Completion Checklist](#completion-checklist)
- [Agent Operation Notes](#agent-operation-notes)

---

## Metadata

```yaml
Full_Name: Custom CloudWatch metrics from Quarkus 3.40 LTS AWS Lambda functions (io.quarkus:quarkus-amazon-lambda 3.40.1.1) — CloudWatch Embedded Metric Format (EMF) to stdout, with notes on io.quarkus:quarkus-micrometer, software.amazon.cloudwatchlogs:aws-embedded-metrics, software.amazon.lambda:powertools-metrics and PutMetricData
Target_Version: Quarkus 3.40 LTS, patch 3.40.1.1 (family fact, https://quarkus.io/releases); Micrometer 1.17.1 as managed by the Quarkus 3.40.1.1 BOM [S20] (medium confidence, BOM partly read); aws-embedded-metrics 4.2.0 [S27]; powertools-metrics 2.11.0 [S30]; CloudWatch EMF specification as published on 2026-10-28 [S1]
Release_Date: Quarkus 3.40 released 2026-09-30, 3.40.1.1 on 2026-10-19 (family fact); aws-embedded-metrics 4.2.0 metadata lastUpdated 2024-08-02 [S27]; powertools-metrics metadata lastUpdated 2026-10-06 [S30]
Support_Status: Quarkus 3.40 LTS community-maintained until 2027-09-30 (family fact). aws-embedded-metrics-java: no release after 4.2.0 (2024-08-02) on Maven Central [S27]; the README states no maintenance status [S26] (freshness flag: last release > 12 months). Powertools for AWS Lambda (Java) 2.x active (2.11.0, 2026-10-06) [S30]
Primary_Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html ; https://quarkus.io/version/3.40/guides/telemetry-micrometer
Secondary_Docs: CloudWatch user guide (EMF libraries, EMF alarms, concepts, publishingMetrics, quotas), CloudWatch API reference (PutMetricData, MetricDatum), Lambda developer guide (monitoring-metrics, monitoring-metrics-types, monitoring-metrics-view, log format, log-level filtering, java-logging, nodejs-logging EMF section, runtime environment), Powertools for AWS Lambda (Java) metrics, Micrometer CloudWatch docs, Quarkus 3.40 logging guide
Official_Repo: https://github.com/awslabs/aws-embedded-metrics-java ; https://github.com/quarkiverse/quarkus-micrometer-registry
Registry: https://repo1.maven.org/maven2/ (io/quarkiverse/micrometer/registry/, software/amazon/cloudwatchlogs/aws-embedded-metrics/, software/amazon/lambda/powertools-metrics/, io/micrometer/micrometer-bom/1.17.1/)
Research_Date: 2026-10-28
Domain_Complexity: Standard
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 5
Unverified_Count: 8
Irresolvable_Count: 2
Research_Quality_Score: 88%   # ~84 sourced claims; 8 unverified + 2 irresolvable -> (84-10)/84
Execution_Notes: >
  Caller constraints honoured: no sub-agents (P2.parallel skipped, every page fetched by this agent),
  no plan mode (scope approval relayed by the caller from PIPELINE_STATE.md#approvals, gates G1 and G2
  of 2026-10-28, which this agent read in that file; recorded here as a relay, not as an approval by
  this agent), and the file was written directly instead of through research-synthesizer.
```

---

## Executive Summary

The CloudWatch **embedded metric format (EMF)** "is a JSON specification used to instruct CloudWatch Logs to automatically extract metric values embedded in structured log events" [S1]. In Lambda "no agent is required to send the logs to CloudWatch. Anything logged to STDOUT is sent to CloudWatch Logs through the Lambda Logging Agent" [S2]. A Quarkus 3.40 Lambda (JVM on the Java managed runtime, or native on `provided.al2023`, family fact) can therefore publish custom metrics with no SDK call, no extra IAM action for CloudWatch metrics and no network round trip, by printing one EMF JSON object per log event to `System.out` (Java functions may log through "methods on java.lang.System, or any logging module that writes to stdout or stderr" [S15]). The spec is strict: the log event must be a valid JSON object "with no additional data at the beginning or end", `_aws.CloudWatchMetrics` holds MetricDirectives (`Namespace`, `Dimensions`, `Metrics`), every referenced dimension and metric is a root member, at most 100 MetricDefinitions per log event (otherwise no metric is extracted), at most 30 keys per DimensionSet, at most 100 values per numeric array, and the `Timestamp` is epoch milliseconds within 14 days past and 2 hours future [S1]. Nothing in Quarkus 3.40 is new here; the relevant "changes" are on the AWS side (Lambda advanced logging controls, JSON log format and log-level filtering [S13][S14]) and in library status.

Library status as of 2026-10-28. **Quarkiverse has no CloudWatch Micrometer registry**: the Quarkus 3.40 Micrometer guide and the Quarkiverse docs list azure-monitor, datadog, graphite, influx, jmx, newrelic(-telemetry), otlp, signalfx, stackdriver and statsd, but not CloudWatch [S18][S23], Maven Central has no `quarkus-micrometer-registry-cloudwatch` artifact [S24][S25]. The documented fallback is `io.quarkus:quarkus-micrometer` plus the Micrometer registry dependency and your own `MeterRegistry` producer [S18]; `io.micrometer:micrometer-registry-cloudwatch2` 1.17.1 is managed by `micrometer-bom` 1.17.1 [S21], which the Quarkus 3.40.1.1 BOM imports [S20] (medium confidence, BOM partly read). Micrometer's CloudWatch registry is a push registry with a default step of 1 minute [S22]; no official page states how that behaves on a frozen Lambda environment (unverified, see U3). The official Java EMF client `aws-embedded-metrics` last shipped 4.2.0 on 2024-08-02 [S27]. Powertools for AWS Lambda (Java) `powertools-metrics` 2.11.0 writes EMF to stdout and offers a functional API without AspectJ [S28][S30]; Quarkus is not mentioned on its pages (unverified, IRRESOLVABLE I1). AWS also now says "For new implementations, we recommend using OpenTelemetry to publish custom metrics" [S5]; that path is listed as an option only.

Three critical patterns. (1) Write EMF as a raw single-line JSON object to `System.out`, never through the Quarkus log formatter: the default console format prefixes a timestamp and level [S19] and the JSON log extension wraps the text in its own document [S19], both of which break the spec's root-node rule [S1]. (2) Keep dimensions bounded: "Every DimensionSet used creates a new metric in CloudWatch" and high-cardinality dimensions such as `requestId` create "a custom metric corresponding to each unique dimension combination" [S1]; CloudWatch bills per unique metric [S9] (medium confidence, pricing page); Quarkus says tag values "MUST BE of LOW-CARDINALITY" [S18]. Unbounded identifiers (requestId, tenantId at scale) go into non-dimension root properties and are aggregated with Logs Insights `stats … by` [S1][S32] (family rule 7: no unbounded tenant dimension without an ADR). (3) Do not re-emit what Lambda already sends for free (`Invocations`, `Errors`, `Throttles`, `Duration`, `ConcurrentExecutions`, async and event-source-mapping metrics) [S10][S11]. Domain complexity is **Standard**: one write path with strict format rules, a cost/cardinality decision, and interactions with Lambda log controls and the JVM vs native choice (family rule 3), but no auth or encryption surface.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (official page read for the current service or the exact version) | 🟡 Medium (unversioned library page, partly read page, pricing, or a two-statement inference) | 🔴 Low (community source or inference without an official statement — verify before use)

### ✅ Mandatory Patterns

**A1. One EMF document = one complete JSON object on one stdout line**
> Confidence: 🟢 High | [✓✓ Triangulated | EMF specification [S1] (2026-10-28) + Lambda Java logging guide [S15] (2026-10-28)]
- Why: "The LogEvent message MUST be a valid JSON object with no additional data at the beginning or end of the LogEvent message string" [S1]. Java Lambda code may log with "methods on java.lang.System" [S15]; in Lambda "Anything logged to STDOUT is sent to CloudWatch Logs" [S2].
- Code:
  ```java
  // Quarkus 3.40.1.1 — Representative, not compiled by this research
  // root is a Jackson ObjectNode holding "_aws" plus the target members (see Implementation Blueprint)
  System.out.println(root.toString());   // single line, nothing before or after the JSON
  ```
- Source: [S1], [S15], [S2]

**A2. Always send `_aws.Timestamp` (epoch milliseconds) and `_aws.CloudWatchMetrics` with `Namespace`, `Dimensions`, `Metrics`**
> Confidence: 🟢 High | [✓✓ Triangulated | EMF specification prose [S1] + EMF JSON schema on the same page and the Powertools sample output in the Lambda Java guide [S15]]
- Why: The `_aws` value "MUST be an object" containing `CloudWatchMetrics`, and the spec's JSON schema lists `Timestamp` and `CloudWatchMetrics` as required; a MetricDirective "MUST contain" `Namespace`, `Dimensions` and `Metrics` [S1]. Timestamp values "MUST be expressed as the number of milliseconds after Jan 1, 1970 00:00:00 UTC", "no more than 14 days in the past and no more than 2 hours in the future" [S1].
- Code:
  ```json
  {"_aws":{"Timestamp":1793232000000,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service"]],"Metrics":[{"Name":"OrdersPlaced","Unit":"Count"}]}]},"Service":"orders","OrdersPlaced":1}
  ```
- Source: [S1]

**A3. Every referenced dimension and metric is a flat root member of the right type**
> Confidence: 🟢 High | Single source, versioned-equivalent official spec [S1]
- Why: "The root node MUST contain all Target members" referenced by the MetricDirective; targets "cannot be nested objects"; "A metric target MUST be a numeric value or an array of numeric values"; "A dimension target MUST have a string value" of 1 to 1024 printable ASCII characters [S1]. An invalid DimensionSet is skipped while others still publish [S1].
- Code:
  ```json
  // ✅ flat: "Service":"orders"   ❌ nested: "ctx":{"Service":"orders"} with Dimensions [["ctx.Service"]] does not match
  ```
- Source: [S1]

**A4. Respect the per-document limits and split when needed: ≤ 100 MetricDefinitions per log event, ≤ 30 keys per DimensionSet, ≤ 100 values per numeric array, ≤ 1 MB**
> Confidence: 🟢 High | [✓✓ Triangulated | EMF specification [S1] + Powertools metrics page "Aggregate up to 100 metrics using a single CloudWatch EMF object" [S28] (medium for the Powertools half)]
- Why: More than 100 MetricDefinitions "counted across all of its MetricDirectives" → "CloudWatch does not extract any metrics from it"; a numeric array over 100 members → no metrics extracted from the event; a DimensionSet "MUST NOT contain more than 30 dimension keys"; EMF is limited "to a maximum size of 1 MB" [S1]. The spec's JSON schema checks the 100-limit per directive only, "It does not check the total across all MetricDirectives" [S1].
- Code:
  ```java
  // Quarkus 3.40.1.1 — Representative: flush a document every 100 metric definitions
  if (pendingDefinitions == 100) { flush(); }
  ```
- Source: [S1]

**A5. Use only CloudWatch units, and pick standard (60) or high (1) resolution explicitly**
> Confidence: 🟢 High | [✓✓ Triangulated | MetricDatum API reference [S7] + EMF schema unit pattern [S1]]
- Why: Unit "SHOULD be valid CloudWatch metric units"; default `None` [S1][S4]. Valid values: `Seconds | Microseconds | Milliseconds | Bytes | Kilobytes | Megabytes | Gigabytes | Terabytes | Bits | Kilobits | Megabits | Gigabits | Terabits | Percent | Count | Bytes/Second | Kilobytes/Second | Megabytes/Second | Gigabytes/Second | Terabytes/Second | Bits/Second | Kilobits/Second | Megabits/Second | Gigabits/Second | Terabits/Second | Count/Second | None` [S7]. `StorageResolution` 1 or 60, default 60; "CloudWatch treats 1.0 as 60" [S1]. Data points with different units "are aggregated separately" [S4], so a metric must keep one unit.
- Code:
  ```json
  {"Name":"OrderLatency","Unit":"Milliseconds","StorageResolution":60}
  ```
- Source: [S7], [S1], [S4]

**A6. Write the invocation's metrics before the handler returns**
> Confidence: 🟢 High | Single source [S17]
- Why: "Lambda freezes the execution environment when the runtime and each extension have completed"; background work that "did not complete when the function ended" resumes only "if Lambda reuses the execution environment". "Make sure that any background processes or callbacks in your code are complete before the code exits" [S17]. With no extensions the Shutdown phase lasts "0 ms" [S17].
- Code:
  ```java
  // Quarkus 3.40.1.1 — Representative
  try { return process(event); } finally { metrics.flush(); }   // synchronous System.out write
  ```
- Source: [S17]

**A7. Dimensions only from a bounded set; unbounded identifiers as non-dimension root properties**
> Confidence: 🟢 High | [✓✓ Triangulated | EMF specification high-cardinality note [S1] + Quarkus 3.40 Micrometer guide [S18] (+ CloudWatch OTel best practices [S31])]
- Why: "If you unintentionally create metrics based on high-cardinality dimensions (such as requestId), the embedded metric format will by design create a custom metric corresponding to each unique dimension combination" [S1]. The root node "MAY contain any other members"; the spec's own example carries `requestId` as a plain property [S1]. Quarkus: "Provided tag values MUST BE of LOW-CARDINALITY" and "Tag values should not use end-user data" [S18]. AWS OTel guidance: "Avoid request IDs or UUIDs as label values" [S31]. Family rule 7 adds: no unbounded tenant cardinality without an ADR.
- Code:
  ```json
  {"_aws":{"Timestamp":1793232000000,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service","TenantTier"]],"Metrics":[{"Name":"OrdersPlaced","Unit":"Count"}]}]},
   "Service":"orders","TenantTier":"premium","OrdersPlaced":1,"tenantId":"t-123","requestId":"8f0c…"}
  ```
- Source: [S1], [S18]

**A8. Use the Lambda built-in metrics instead of re-emitting them**
> Confidence: 🟢 High | [✓✓ Triangulated | Lambda monitoring-metrics [S10] + monitoring-metrics-types [S11]]
- Why: "When your AWS Lambda Event Function finishes processing an event, Lambda automatically sends metrics about the invocation to Amazon CloudWatch", with no extra execution-role permission "and there's no additional charge for these metrics"; sent "in 1-minute intervals" [S10]. Namespace `AWS/Lambda`, dimensions `FunctionName`, `Resource`, `ExecutedVersion`, `EventSourceMappingUUID` [S12]. Built-ins include `Invocations`, `Errors`, `DeadLetterErrors`, `DestinationDeliveryFailures`, `Throttles`, `Duration` (supports percentiles; "does not include cold start time"), `PostRuntimeExtensionsDuration`, `IteratorAge`, `OffsetLag`, `ConcurrentExecutions`, `UnreservedConcurrentExecutions`, `ClaimedAccountConcurrency`, provisioned-concurrency metrics, `AsyncEventsReceived`, `AsyncEventAge`, `AsyncEventsDropped`, `RecursiveInvocationsDropped`, and opt-in event-source-mapping metrics [S11].
- Code:
  ```bash
  # Representative — read the built-in metric, do not re-publish it
  aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors \
    --dimensions Name=FunctionName,Value=orders-fn --statistics Sum --period 60 \
    --start-time 2026-10-28T00:00:00Z --end-time 2026-10-28T01:00:00Z
  ```
- Source: [S10], [S11], [S12]

### ⚠️ Conditional Patterns

**C1. How to emit custom metrics from a Quarkus 3.40 Lambda**
> Confidence: 🟡 Medium (option facts are High where cited; the comparison across options is this research's synthesis)
- Options: (a) hand-written EMF to stdout; (b) `software.amazon.cloudwatchlogs:aws-embedded-metrics` 4.2.0; (c) Powertools `software.amazon.lambda:powertools-metrics` 2.11.0, functional API; (d) `io.quarkus:quarkus-micrometer` + `io.micrometer:micrometer-registry-cloudwatch2`; (e) `PutMetricData` through the AWS SDK (mention only); (f) OpenTelemetry to the CloudWatch OTLP endpoint (mention only).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | (a) EMF by hand | No extra dependency; synchronous stdout write; fully specified by [S1]; works with any runtime that writes stdout [S2][S15] | You implement the limits (100 definitions, 30 keys, 100 values) and splitting yourself [S1] | Default candidate for JVM and native; few, well-known metrics |
  | (b) aws-embedded-metrics-java | `MetricsLogger` is "thread-safe"; Lambda environment writes "over stdout" [S26] | Last release 4.2.0 on 2024-08-02 [S27] (> 12 months); Quarkus, native and Lambda JSON-log-format behaviour not stated (unverified, U2) | Team already standardised on it, JVM only, after a test |
  | (c) Powertools metrics 2.11.0 | Writes EMF "asynchronously by logging metrics to standard output", "no impact to Lambda function latency" [S28]; `ColdStart` metric; functional API "eliminates the AspectJ runtime dependency" [S28] | Powertools tenet "AWS Lambda only … Utilities might work with web frameworks … not officially supported" [S29]; Quarkus compatibility not stated (unverified, I1); "GraalVM support" is one bullet without detail [S28] (medium confidence) | Organisation already uses Powertools in other Java Lambdas; JVM mode after a test |
  | (d) Micrometer + cloudwatch2 | Familiar Micrometer API, `@Counted`/`@Timed` supported by Quarkus [S18] | No Quarkus/Quarkiverse extension [S18][S23][S24]; you write the `@Produces MeterRegistry` [S18]; push registry with default step 1 minute [S22]; behaviour on frozen environments not documented (unverified, U3); default binders are enabled (`quarkus.micrometer.binder-enabled-default` default `true`) [S18], so JVM/system meters would also be published as billed custom metrics (medium confidence) | Only with an ADR, e.g. shared code with non-Lambda services |
  | (e) PutMetricData | Immediate API ingestion; Values/Counts arrays up to 150 values [S6] | One network call per batch inside the invocation (latency, unverified figure); needs `cloudwatch:PutMetricData` permission [S31]; quota 500 requests/s per Region, adjustable [S8]; ≤ 1000 metrics and 1 MB per request [S6]; per-request charge [S9] (medium confidence) | Metrics that must not depend on log delivery; low-rate jobs |
  | (f) OpenTelemetry OTLP | AWS's recommendation "for new implementations" [S5]; endpoint `https://monitoring.{region}.amazonaws.com/v1/metrics`, SigV4, `cloudwatch:PutMetricData` [S31] | Periodic export (`PeriodicExportingMetricReader`, 60 s in the AWS example [S31]) has the same frozen-environment question as (d) (unverified, U3); overlaps U12 | Only together with the tracing decision of U12 |

- Agent: "Ask the user which emission path to use; propose (a) unless the organisation already standardised on (b)/(c)/(d)/(f), and record the choice in an ADR. Do not present (c) as Quarkus-supported or (d)/(f) as safe on Lambda."
- Source: [S1], [S2], [S5], [S6], [S8], [S15], [S18], [S22], [S23], [S24], [S26], [S27], [S28], [S29], [S31]

**C2. Tenant as a dimension vs tenant in the log only (Logs Insights)**
> Confidence: 🟡 Medium (cost figures from the pricing page; mechanics High)
- Options: (A) `TenantId` as a dimension; (B) `tenantId` as a non-dimension EMF property, aggregated with Logs Insights; (C) a bounded proxy dimension (for example `TenantTier` or `Plan`) plus `tenantId` as a property.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | (A) TenantId dimension | Per-tenant graphs and alarms on CloudWatch metrics directly | Every unique dimension combination is a separate metric [S4][S1]; billed per metric per month, prorated hourly, $0.30/metric for the first 10,000 in US East (N. Virginia) [S9] (medium confidence); CloudWatch "does not aggregate across dimensions for your custom metrics" — you only get the combinations you published [S4]; family rule 7 requires an ADR when tenant count is unbounded | Small, bounded, contractually known tenant set; per-tenant SLO alarms needed |
  | (B) tenantId property + Logs Insights | No per-tenant metric cost; root members that are not dimensions stay in the log [S1]; `stats sum(...) by tenantId, bin(1h)` and `pct(...)` are available [S32] | Query-time cost and latency instead of a metric (Logs Insights scan pricing not read, unverified U7); no metric alarm per tenant; `countDistinct` is approximate at high cardinality [S32] | Many or unbounded tenants; per-tenant reporting, not alerting |
  | (C) Bounded proxy + property | Bounded metric count (tiers × metrics × dimension sets), per-tenant drill-down in logs | Per-tenant alarms still not possible | Default proposal for SaaS (aligns with family rule 7) |

- Agent: "Ask how many tenants exist now and at most, whether per-tenant alarms are required, and the monthly metric budget. Without an ADR, use (C)."
- Source: [S1], [S4], [S9], [S32]

**C3. Lambda log format (Text vs JSON) and application log level when emitting EMF**
> Confidence: 🟡 Medium (each statement High; their combination for Java/Quarkus is an inference)
- Options: (A) keep the default Text format; (B) JSON format with `ApplicationLogLevel` INFO (or more detailed); (C) JSON format with `ApplicationLogLevel` WARN/ERROR/FATAL.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | (A) Text (default) | "the default log format for all Lambda runtimes is plain text" [S13]; EMF lines are untouched | No Lambda log-level filtering (requires JSON) [S14] | No need for Lambda-side filtering |
  | (B) JSON, level ≤ INFO | Structured system logs; "Lambda doesn't double-encode any logs that are already JSON encoded" [S13][S15], so a raw EMF line should stay at the root (medium confidence, M9); AWS recommends testing EMF after switching to JSON [S13] | Larger log events (JSON metadata) [S13] | U11 chose JSON logs |
  | (C) JSON, level > INFO | Fewer application logs | Lambda assigns level INFO to JSON lines with a missing or invalid `"level"` [S14] and does not send INFO when the level is WARN [S14] → EMF lines without a `level` field would be dropped (medium confidence, M8) | Avoid when EMF is used |

- Notes: The Node.js page warns that switching to JSON can make CloudWatch unable to recognise EMF written with `console.log`, and that direct `stdout` writes avoid it [S16]; no Java-specific statement exists (medium confidence). For Quarkus native on `provided.al2023`, JSON application logs are natively captured only for listed runtimes ("For other managed Lambda runtimes, Lambda currently only natively supports capturing system logs in structured JSON format") [S13], and for custom runtimes Lambda only sets `AWS_LAMBDA_LOG_LEVEL` / `AWS_LAMBDA_LOG_FORMAT` for the runtime to honour [S14] (medium confidence, M10). Infrastructure for `LoggingConfig` belongs to `provisioning-aws-*-v6` (family rule 4).
- Agent: "Ask which log format U11 selected; if JSON, require ApplicationLogLevel INFO or more detailed and a deployed smoke test that the metric appears."
- Source: [S13], [S14], [S15], [S16]

**C4. Standard (60 s) vs high resolution (1 s)**
> Confidence: 🟢 High (mechanics) / 🟡 Medium (cost wording)
- Options: `StorageResolution` 60 (default) or 1 [S1].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | 60 | Default; 1-minute data kept 15 days, then rolled up [S4] | No sub-minute periods [S4] | Almost all business metrics |
  | 1 | Sub-minute insight; periods 1/5/10/30 s [S4] | Sub-minute data kept 3 hours [S4]; "higher charge for high-resolution alarms" [S4]; for EMF alarms on high-resolution metrics AWS advises flushing logs at ≤ 5 s, and "If you are using Lambda … consider using M out of N alarms" [S3] | Short-lived spikes that must alarm within seconds |

- Agent: "Ask whether any metric needs sub-minute alarming; default 60."
- Source: [S1], [S3], [S4]

**C5. Cold-start visibility**
> Confidence: 🟡 Medium
- Options: (A) emit a `ColdStart` count metric from the first invocation (Powertools does this with `captureColdStart`, adding `FunctionName` and `Service` dimensions [S28]); (B) read `Init Duration` from the `REPORT` line ("For the first request served, the amount of time it took the runtime to load the function and run code outside of the handler method" [S15]) with Logs Insights.
- Tradeoffs: (A) is a custom metric (billed) [S9]; (B) has no metric cost. `InitDuration` is not in the `AWS/Lambda` metric list on [S11] (medium confidence, absence of evidence, M6); `Duration` "does not include cold start time" [S11]. With SnapStart the restore phase reports via `RESTORE_REPORT` [S17]; JVM+SnapStart vs native stays an Ask-First (family rule 3).
- Agent: "Ask whether cold-start rate must be alarmed (A) or only reported (B)."
- Source: [S11], [S15], [S17], [S28]

### 🚫 Forbidden Patterns

**F1. Writing EMF through the Quarkus logger**
> Severity: High
> Confidence: 🟢 High
- Why: The default `quarkus.log.console.format` is `%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n` [S19], which puts data before the JSON; `quarkus-logging-json` overrides console formatting and places the text in its own JSON document [S19]. EMF requires the JSON object with "no additional data at the beginning or end" and targets on the root node [S1].
- Impact: CloudWatch extracts no metric; the failure is only visible as EMF parsing/validation metrics in the `AWS/Logs` namespace [S1].
- ❌ Wrong:
  ```java
  // Quarkus 3.40.1.1
  Log.info(emfJson);   // becomes "2026-10-28 10:00:00,123 INFO  [Orders] (main) {...}" or {"message":"{...}"}
  ```
- ✅ Correct:
  ```java
  // Quarkus 3.40.1.1 — raw stdout write, one line per EMF document
  System.out.println(emfJson);
  ```
- Source: [S1], [S19], [S15]

**F2. Unbounded identifiers as dimensions (requestId, orderId, userId, tenantId without ADR)**
> Severity: High
> Confidence: 🟢 High
- Why: "Every DimensionSet used creates a new metric"; high-cardinality dimensions create "a custom metric corresponding to each unique dimension combination" [S1]; Quarkus: tag values "MUST BE of LOW-CARDINALITY" [S18]; family rule 7.
- Impact: Custom-metric bill grows with every new value [S1][S9]; metrics cannot be deleted and expire only after 15 months without data [S4].
- ❌ Wrong:
  ```json
  {"_aws":{"Timestamp":1793232000000,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service","requestId"]],"Metrics":[{"Name":"OrdersPlaced","Unit":"Count"}]}]},"Service":"orders","requestId":"8f0c…","OrdersPlaced":1}
  ```
- ✅ Correct:
  ```json
  {"_aws":{"Timestamp":1793232000000,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service"]],"Metrics":[{"Name":"OrdersPlaced","Unit":"Count"}]}]},"Service":"orders","requestId":"8f0c…","OrdersPlaced":1}
  ```
- Source: [S1], [S18], [S4]

**F3. Re-emitting Lambda built-in metrics as custom metrics**
> Severity: Moderate
> Confidence: 🟢 High
- Why: Lambda already sends `Invocations`, `Errors`, `Throttles`, `Duration`, `ConcurrentExecutions` and more at no additional charge [S10][S11]; custom metrics are charged [S10].
- Impact: Duplicate, billed series that can disagree with the authoritative ones (for example, throttled requests are not `Invocations` [S11]).
- ❌ Wrong:
  ```json
  {"_aws":{"Timestamp":1793232000000,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service"]],"Metrics":[{"Name":"Invocations","Unit":"Count"},{"Name":"Errors","Unit":"Count"}]}]},"Service":"orders","Invocations":1,"Errors":0}
  ```
- ✅ Correct:
  ```json
  {"_aws":{"Timestamp":1793232000000,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service"]],"Metrics":[{"Name":"OrdersRejected","Unit":"Count"}]}]},"Service":"orders","OrdersRejected":1}
  ```
  (business outcome only; read `AWS/Lambda` `Errors` for function errors)
- Source: [S10], [S11]

**F4. A custom namespace starting with `AWS/`**
> Severity: Moderate
> Confidence: 🟢 High
- Why: "To avoid conflicts with AWS service namespaces, you should not specify a namespace that begins with AWS/" [S6]; AWS namespaces use `AWS/{service}` [S4].
- Impact: Collides with or is confused with service namespaces.
- ❌ Wrong:
  ```json
  "Namespace": "AWS/Orders"
  ```
- ✅ Correct:
  ```json
  "Namespace": "SaaS/Orders"
  ```
- Source: [S6], [S4]

**F5. More than 100 metric definitions in one EMF document**
> Severity: High
> Confidence: 🟢 High
- Why: "If a log event exceeds this limit, CloudWatch does not extract any metrics from it" [S1].
- Impact: Silent loss of every metric in that event.
- ❌ Wrong:
  ```java
  // Quarkus 3.40.1.1 — one document with 150 MetricDefinitions
  for (String m : allMetrics) { directiveMetrics.addObject().put("Name", m); }
  System.out.println(root);
  ```
- ✅ Correct:
  ```java
  // Quarkus 3.40.1.1 — split into documents of at most 100 MetricDefinitions
  for (List<String> chunk : chunksOf(allMetrics, 100)) { System.out.println(buildDocument(chunk)); }
  ```
- Source: [S1]

**F6. Timestamp in seconds, as an ISO string, or outside the accepted window**
> Severity: Moderate
> Confidence: 🟢 High
- Why: Timestamp is a number of milliseconds since the epoch, at most 14 days past and 2 hours future; "CloudWatch does not publish metrics that have a time stamp outside this range" [S1]. The schema types it as integer [S1].
- Impact: Metrics are not published (seconds read as milliseconds fall in 1970).
- ❌ Wrong:
  ```json
  "_aws": {"Timestamp": 1793232000, "CloudWatchMetrics": [ … ]}
  ```
- ✅ Correct:
  ```json
  "_aws": {"Timestamp": 1793232000000, "CloudWatchMetrics": [ … ]}
  ```
- Source: [S1]

**F7. Publishing metrics from a background thread after the handler returns**
> Severity: High
> Confidence: 🟢 High
- Why: The environment is frozen after the invocation; unfinished background work only resumes if the environment is reused, and AWS says to complete it "before the code exits" [S17].
- Impact: Metrics delayed to a later invocation or lost when the environment is reclaimed [S17].
- ❌ Wrong:
  ```java
  // Quarkus 3.40.1.1
  executor.submit(() -> System.out.println(emfJson));
  return response;
  ```
- ✅ Correct:
  ```java
  // Quarkus 3.40.1.1
  System.out.println(emfJson);
  return response;
  ```
- Source: [S17]

**F8. NaN, Infinity or out-of-range values**
> Severity: Moderate
> Confidence: 🟢 High
- Why: Values "must be in the range of -2^360 to 2^360" and "special values (for example, NaN, +Infinity, -Infinity) are not supported" [S7]; in EMF, a value outside the range means "CloudWatch does not publish that metric" [S1].
- Impact: The metric is dropped (Jackson writes `NaN` as a JSON token only when non-standard numbers are enabled; behaviour not researched).
- ❌ Wrong:
  ```java
  root.put("ConversionRate", orders / visits);   // visits == 0 -> Infinity or NaN
  ```
- ✅ Correct:
  ```java
  if (visits > 0) { root.put("ConversionRate", (double) orders / visits); }   // skip the metric otherwise
  ```
- Source: [S7], [S1]

---

## Migration Guide

> Confidence: 🟡 Medium | Sources: Maven Central metadata [S27][S30], Quarkus 3.40 Micrometer guide [S18], Lambda log-format page [S13]. No official "metrics migration guide" for Quarkus 3.40 exists (absence of evidence).

**Breaking Changes / status changes relevant to this unit**:
- No Quarkus 3.40-specific metrics break was found. The Quarkus-maintained Micrometer extensions are `micrometer`, `micrometer-registry-prometheus` and `micrometer-opentelemetry` [S18]; CloudWatch has never appeared in the Quarkiverse registry set on Central [S24] (medium confidence, absence of evidence).
- Lambda advanced logging controls: JSON log format and log-level filtering are opt-in; changing the format affects only new logs [S13]. AWS warns that Node.js EMF users must upgrade libraries when switching to JSON [S2][S13]; there is no equivalent Java statement (medium confidence).
- Lambda documentation now names functions "Event Functions" and adds Lambda Managed Instances, which "only support JSON log format" [S13]. Managed Instances support concurrent invocations [S17]; this research does not cover Quarkus on Managed Instances.
- aws-embedded-metrics-java: last version 4.2.0 (2024-08-02) [S27]; flagged by the freshness rule.
- Powertools for AWS Lambda (Java) 2.x: supports Java 17 to 25 [S29]; the Lambda guide's Powertools SAM sample still uses `java11` [S15] (see contradiction C-2 in Research Gaps). A v1 → v2 metrics migration guide was not read (unverified).

**Upgrade Steps** (for a function that today calls PutMetricData per invocation and moves to EMF):
1. Keep the namespace, metric names, units and dimension names identical, or the new series are separate metrics [S4].
2. Replace the SDK call with an EMF line written before the handler returns (A1, A6).
3. Remove `cloudwatch:PutMetricData` from the execution role only if nothing else uses it (permission named in [S31]); Terraform changes go to `provisioning-aws-*-v6` (family rule 4).
4. Deploy, invoke, and confirm the metric with `aws cloudwatch list-metrics` (a new metric can take up to 15 minutes to appear there, 2 minutes for statistics [S5]).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| io.quarkus:quarkus-amazon-lambda | 3.40.1.1 | 3.40.x | family fact |
| io.quarkus:quarkus-micrometer | 3.40.1.1 (BOM) | 3.40.x | only for option C1(d) [S18] |
| io.micrometer:micrometer-registry-cloudwatch2 | 1.17.1 | 1.17.1 | managed by micrometer-bom 1.17.1 [S21], imported by Quarkus BOM 3.40.1.1 [S20] (medium confidence) |
| software.amazon.cloudwatchlogs:aws-embedded-metrics | 4.2.0 | 4.2.0 | latest on Central [S27]; Quarkus/native (unverified) |
| software.amazon.lambda:powertools-metrics | 2.11.0 | 2.11.0 | latest on Central [S30]; Quarkus (unverified) |
| Lambda runtime (JVM) | java17.al2023 / java21 / java25 | — | family fact |
| Lambda runtime (native) | provided.al2023 | — | family fact (pairing medium) |

---

## Implementation Blueprint

> Confidence: 🟢 High for the document shape [S1]; the Java class is a representative sketch, not compiled (Quarkus 3.40.1.1).

**Lifecycle** (option C1(a), hand-written EMF, JVM or native):
```java
// Quarkus 3.40.1.1 — Representative, not compiled by this research.
// Assumes a Jackson ObjectMapper bean is available (io.quarkus:quarkus-jackson); whether
// quarkus-amazon-lambda brings it transitively was not verified (U6).
package com.example.metrics;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class OrderMetrics {

    private static final String NAMESPACE = "SaaS/Orders";   // not "AWS/..." [S6]
    private final ObjectMapper mapper;

    OrderMetrics(ObjectMapper mapper) {
        this.mapper = mapper;
    }

    /** Writes one EMF document synchronously; call before the handler returns [S17]. */
    public void orderPlaced(String service, String tenantTier, String tenantId,
                            String requestId, double latencyMs) {
        ObjectNode root = mapper.createObjectNode();
        ObjectNode aws = root.putObject("_aws");
        aws.put("Timestamp", System.currentTimeMillis());           // epoch ms [S1]
        ObjectNode directive = aws.putArray("CloudWatchMetrics").addObject();
        directive.put("Namespace", NAMESPACE);
        directive.putArray("Dimensions").addArray().add("Service").add("TenantTier"); // bounded [S1]
        ArrayNode metrics = directive.putArray("Metrics");           // <= 100 per event [S1]
        metrics.addObject().put("Name", "OrdersPlaced").put("Unit", "Count");
        metrics.addObject().put("Name", "OrderLatency").put("Unit", "Milliseconds");

        root.put("Service", service);          // dimension targets: flat strings [S1]
        root.put("TenantTier", tenantTier);
        root.put("OrdersPlaced", 1);           // metric targets: numbers [S1]
        root.put("OrderLatency", latencyMs);
        root.put("tenantId", tenantId);        // property only (C2 option C, family rule 7)
        root.put("requestId", requestId);      // property only [S1]

        System.out.println(root.toString());   // one line, raw stdout [S1][S15]
    }
}
```

**Integration**: Quarkus 3.40 Lambda handler ↔ EMF
```java
// Quarkus 3.40.1.1 — Representative. Handler wiring (QuarkusStreamHandler, quarkus.lambda.handler) is U1.
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import jakarta.inject.Inject;
import jakarta.inject.Named;

@Named("orders")
public class OrdersHandler implements RequestHandler<OrderRequest, OrderResponse> {

    @Inject OrderMetrics metrics;
    @Inject OrderService service;

    @Override
    public OrderResponse handleRequest(OrderRequest in, Context ctx) {
        long start = System.nanoTime();
        OrderResponse out = service.place(in);          // tenant resolved from the token (family rule 6)
        double ms = (System.nanoTime() - start) / 1_000_000.0;
        metrics.orderPlaced("orders", out.tenantTier(), out.tenantId(), ctx.getAwsRequestId(), ms);
        return out;                                      // metrics already written [S17]
    }
}
```

**Per-tenant reporting without per-tenant metrics** (C2 option B/C), CloudWatch Logs Insights:
```
stats sum(OrdersPlaced) as orders, pct(OrderLatency, 95) as p95 by tenantId, bin(1h)
```
(`stats`, `sum`, `pct`, `by` and `bin` are documented on [S32]; visualisations are limited to 100 bars [S32].)

**Option C1(d) sketch, only with an ADR** (Micrometer; frozen-environment behaviour unverified, U3):
```xml
<!-- Quarkus 3.40.1.1 — Representative. No Quarkiverse CloudWatch extension exists [S23][S24]. -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-micrometer</artifactId>
</dependency>
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-registry-cloudwatch2</artifactId> <!-- 1.17.1 via micrometer-bom [S21] -->
</dependency>
```
```properties
# Quarkus 3.40.1.1 — keys from the Micrometer guide [S18]
quarkus.micrometer.binder-enabled-default=false   # default true: avoid publishing JVM/system meters as billed custom metrics (medium confidence)
```
The `MeterRegistry` must come from your own `@Produces` method configured through MicroProfile Config [S18]; the CloudWatch registry's own constructor arguments and SDK client were not researched (unverified, U4).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Quarkus 3.40.1.1, AWS CLI v2)

# 1. Unit test: the serializer emits valid EMF (see Mocking below)
./mvnw -q test
# Expected: tests green; each captured stdout line parses as JSON with _aws.Timestamp and _aws.CloudWatchMetrics

# 2. Check the function's logging config (if U11 chose JSON, ApplicationLogLevel must be INFO or more detailed)
aws lambda get-function-configuration --function-name orders-fn --query LoggingConfig
# Expected: {"LogFormat": "Text", ...} or {"LogFormat": "JSON", "ApplicationLogLevel": "INFO", ...}

# 3. Invoke once, then look for the metric (new metrics: up to 2 min for statistics, up to 15 min in list-metrics [S5])
aws cloudwatch list-metrics --namespace SaaS/Orders --metric-name OrdersPlaced
# Expected: one entry per published dimension combination, e.g. Service=orders, TenantTier=premium

# 4. Confirm the number of series stays bounded (cost guard, family rule 7)
aws cloudwatch list-metrics --namespace SaaS/Orders --query 'length(Metrics)'
# Expected: <= (metrics x dimension sets x allowed dimension values) agreed in the ADR
```
EMF parsing and validation failures are reported as metrics in the `AWS/Logs` namespace [S1]; the metric names were not read (unverified).

**Mocking** (no AWS call; capture stdout and parse, the approach Powertools documents for its own output [S28]):
```java
// Quarkus 3.40.1.1 — Representative plain JUnit 5 test of the serializer (no Quarkus boot needed)
import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import org.junit.jupiter.api.Test;

class OrderMetricsTest {
    @Test
    void writesOneValidEmfLine() throws Exception {
        PrintStream original = System.out;
        ByteArrayOutputStream captured = new ByteArrayOutputStream();
        System.setOut(new PrintStream(captured));
        try {
            new OrderMetrics(new ObjectMapper()).orderPlaced("orders", "premium", "t-1", "r-1", 12.5);
        } finally {
            System.setOut(original);
        }
        String[] lines = captured.toString().trim().split("\n");
        assertEquals(1, lines.length);
        JsonNode root = new ObjectMapper().readTree(lines[0]);
        assertTrue(root.at("/_aws/Timestamp").isIntegralNumber());
        JsonNode dir = root.at("/_aws/CloudWatchMetrics/0");
        assertEquals("SaaS/Orders", dir.get("Namespace").asText());
        assertFalse(dir.get("Dimensions").toString().contains("tenantId"));   // family rule 7
        assertTrue(dir.get("Metrics").size() <= 100);                          // [S1]
        assertTrue(root.get("OrdersPlaced").isNumber());
    }
}
```
Testing of the deployed Lambda through the mock event server and `quarkus-junit` + RestAssured is covered by U6 (family fact: `quarkus-test-amazon-lambda` was removed in 3.31).

---

## Production Readiness

- **Performance**: EMF is a stdout write; Powertools describes its EMF path as having "no impact to Lambda function latency" [S28] (medium confidence). PutMetricData adds a network call per request batch (latency figure unverified). JSON log format increases log size [S13].
- **Scalability**: EMF limits per event: 100 MetricDefinitions, 30 keys per DimensionSet, 100 values per array, 1 MB [S1]. PutMetricData: 1000 metrics and 1 MB per request, 150 values per metric, 30 dimensions [S6]; 500 requests/s per Region, adjustable [S8]. EMF delivery is "at least one time … duplicate metric values may occasionally occur" [S1]. EMF metrics depend on log processing, so alarm periods must allow for log delivery [S3].
- **Cost**: each unique namespace + name + dimension combination is a metric [S4][S28]; $0.30 per metric per month for the first 10,000, prorated by the hour, free tier 10 custom metrics, prices "based on US East (N. Virginia)" [S9] (medium confidence, M1). Metrics cannot be deleted; they expire 15 months after the last data point [S4]. Log ingestion is billed separately (examples use $0.50 per GB) [S9] (medium confidence).
- **Monitoring**: business metrics in a custom namespace; function health from `AWS/Lambda` (`Errors`, `Throttles`, `Duration` p95/p99, `ConcurrentExecutions`) [S11]; EMF pipeline health in `AWS/Logs` [S1]. Alarm and dashboard infrastructure: `monitoring-cloudwatch-observability`, `provisioning-aws-cloudwatch-v6` (names only).
- **Security**: never put PII or secrets in EMF properties (they are stored as log data, family rule 7); EMF needs no `cloudwatch:PutMetricData` permission, which is required for PutMetricData and OTLP [S31] (the absence of a requirement for EMF is not stated on a page: medium confidence, absence of evidence).
- **Native mode**: hand-written EMF uses only `System.out` and JSON serialisation; native compatibility of aws-embedded-metrics-java (README silent [S26]), of Powertools metrics with AspectJ ("GraalVM support" bullet only [S28]) and of `micrometer-registry-cloudwatch2` were not documented (unverified, U2, U4, I1). Lambda's JSON application-log handling for OS-only runtimes: see C3 (medium confidence).

---

## Reference Implementations

- AWS EMF specification example document and JSON schema [S1].
- AWS Node.js page: writing EMF directly to `stdout` as one JSON line per event (pattern transferable to `System.out`) [S16].
- AWS Lambda Java logging guide: Powertools SAM sample with a `ColdStart` EMF document in the log output [S15].
- awslabs/aws-embedded-metrics-java README (`MetricsLogger`, `putDimensions`, `putMetric`, `putProperty`, `flush`; `EnvironmentOverride` values Local, Lambda, Agent, EC2, ECS; default namespace `aws-embedded-metrics`) [S26] (medium confidence, main branch).
- Powertools for AWS Lambda (Java) metrics: `MetricsFactory.getMetricsInstance()`, `MetricsBuilder`, `@FlushMetrics(captureColdStart = true)`, `addMetadata` for "high cardinal data", `POWERTOOLS_METRICS_NAMESPACE`, `POWERTOOLS_SERVICE_NAME`, `POWERTOOLS_METRICS_DISABLED` for tests [S28] (medium confidence).
- Quarkus 3.40 Micrometer guide: `MeterRegistry` injection, `Counter.builder`, `Timer.builder`, `@Counted`, `@Timed`, custom registry via `@Produces` [S18].

---

## Source Bibliography

**Primary** (all read 2026-10-28):
- [S1] CloudWatch EMF specification — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html — read in full
- [S2] CloudWatch EMF client libraries — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Libraries.html — read in full
- [S3] CloudWatch EMF alarms — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Alarms.html — read in full
- [S4] CloudWatch metrics concepts — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html — read in full
- [S5] Publish custom metrics (PutMetricData / EMF) — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html — read in full
- [S6] PutMetricData API reference — https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html — read in full
- [S7] MetricDatum API reference — https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html — read in full
- [S8] CloudWatch service quotas — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_limits.html — CloudWatch quota table read (L5)
- [S9] Amazon CloudWatch pricing — https://aws.amazon.com/cloudwatch/pricing/ — read in two passes by tool summary (L4), medium
- [S10] Lambda: Using CloudWatch metrics — https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html — read in full
- [S11] Lambda: Types of metrics — https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html — read in full
- [S12] Lambda: Viewing metrics — https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-view.html — read in full
- [S13] Lambda: JSON and plain text log formats — https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html — read in full
- [S14] Lambda: Log-level filtering — https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html — read in full
- [S15] Lambda: Log and monitor Java functions — https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html — read in full
- [S16] Lambda: Log and monitor Node.js functions (EMF section) — https://docs.aws.amazon.com/lambda/latest/dg/nodejs-logging.html — read in full
- [S17] Lambda execution environment lifecycle — https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html — read in full
- [S18] Quarkus 3.40 Micrometer Metrics guide — https://quarkus.io/version/3.40/guides/telemetry-micrometer — received ~55,000 characters by tool estimate, answered as summary with quotes (L6)
- [S19] Quarkus 3.40 Logging guide — https://quarkus.io/version/3.40/guides/logging — chars 0–100000 of 199486 (L2)
- [S20] Quarkus BOM source at tag 3.40.1.1 — https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/bom/application/pom.xml — chars 0–200000 of 318246 (L3)
- [S21] Micrometer BOM 1.17.1 POM — https://repo1.maven.org/maven2/io/micrometer/micrometer-bom/1.17.1/micrometer-bom-1.17.1.pom — read
- [S22] Micrometer CloudWatch registry docs (page version 1.17.2) — https://docs.micrometer.io/micrometer/reference/implementations/cloudwatch.html — read, medium (patch differs from 1.17.1)
- [S23] Quarkiverse Micrometer Registry docs (dev) — https://docs.quarkiverse.io/quarkus-micrometer-registry/dev/ — read
- [S24] Maven Central listing io/quarkiverse/micrometer/registry/ — https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/ — read
- [S25] Maven Central quarkus-micrometer-registry-cloudwatch metadata — https://repo1.maven.org/maven2/io/quarkiverse/micrometer/registry/quarkus-micrometer-registry-cloudwatch/maven-metadata.xml — HTTP 404
- [S26] awslabs/aws-embedded-metrics-java README — https://github.com/awslabs/aws-embedded-metrics-java — main branch, medium
- [S27] Maven Central aws-embedded-metrics metadata — https://repo1.maven.org/maven2/software/amazon/cloudwatchlogs/aws-embedded-metrics/maven-metadata.xml — read
- [S28] Powertools for AWS Lambda (Java) Metrics — https://docs.aws.amazon.com/powertools/java/latest/core/metrics/ (redirect target of https://docs.powertools.aws.dev/lambda/java/latest/core/metrics/) — read, medium ("latest" page with a "not viewing the latest version" banner; snippets show 2.11.0)
- [S29] Powertools for AWS Lambda (Java) home — https://docs.aws.amazon.com/powertools/java/latest/ — read, medium
- [S30] Maven Central powertools-metrics metadata — https://repo1.maven.org/maven2/software/amazon/lambda/powertools-metrics/maven-metadata.xml — read
- [S31] CloudWatch: Publish custom metrics with OpenTelemetry — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/metrics-otel-send.html — read in full
- [S32] CloudWatch Logs Insights `stats` — https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Stats.html — read in full

**Validation** (search only, not evidence):
- [S33] WebSearch "quarkus-micrometer-registry-cloudwatch quarkiverse" (2026-10-28) — no CloudWatch registry found; pointed to [S23], https://github.com/quarkiverse/quarkus-micrometer-registry
- [S34] WebSearch "Powertools for AWS Lambda Java Quarkus support metrics" (2026-10-28) — no official Quarkus statement found
- [S35] Lambda advanced logging controls — https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-advanced.html — returned title only, no body (L1)

**Family facts used** (not re-fetched): Quarkus 3.40 LTS dates and 3.40.1.1 patch (https://quarkus.io/releases); Lambda runtimes java17.al2023/java21/java25 and provided.al2023 (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html); native packaging as `bootstrap` and handler wiring (https://quarkus.io/guides/aws-lambda); `quarkus-test-amazon-lambda` removed in 3.31.

---

## Research Gaps

> Every gap that survives all gap-loop iterations also appears as an IRRESOLVABLE row in the Research Iteration Changelog.

Unverified (U):
- U1 Quarkus compatibility of Powertools metrics (annotation with AspectJ weaving on CDI beans, functional API inside `QuarkusStreamHandler`). Same item as I1.
- U2 aws-embedded-metrics-java 4.2.0 behaviour under Lambda JSON log format, in Quarkus, and in native image — README silent [S26].
- U3 Data loss or delay of push registries (Micrometer step registry, OTel periodic reader) on frozen Lambda environments — inference from [S17][S22][S31]; no official page states it. Same item as I2.
- U4 `micrometer-registry-cloudwatch2` constructor/SDK client requirements and native-image support — not on [S22].
- U5 PutMetricData request price: the tool returned "$0.01/M requests" [S9]; unit ambiguous.
- U6 Whether `quarkus-amazon-lambda` 3.40.1.1 brings a Jackson `ObjectMapper` bean transitively.
- U7 CloudWatch Logs Insights price per GB scanned — not found in the parts of [S9] that were read.
- U8 Names of the `AWS/Logs` metrics that report EMF parsing/validation failures — linked from [S1], not read.

Irresolvable (I):
```
Gap: I1 — Powertools for AWS Lambda (Java) 2.11.0 metrics on Quarkus 3.40 (JVM and native)
Impact: C1(c) cannot be recommended as supported; must stay Ask-First with a test
Workaround: use C1(a) hand-written EMF; if Powertools is mandated, use the functional API and test in a deployed function
Follow-up: https://github.com/aws-powertools/powertools-lambda-java issues/discussions; Powertools docs "frameworks" pages
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: I2 — Official statement on push metric registries (Micrometer CloudWatch, OTel periodic export) in frozen Lambda environments
Impact: C1(d)/(f) risk of lost/late data is an inference only
Workaround: prefer EMF (synchronous stdout); if (d)/(f) is mandated, force a publish before the handler returns and verify in a deployed test
Follow-up: Micrometer CloudWatch docs for the 1.17.x line; AWS Lambda + OpenTelemetry (ADOT) docs (U12)
§7-ref: Iteration 3 — IRRESOLVABLE
```

Medium (M):
- M1 Pricing figures ($0.30/metric first 10,000, free tier 10 metrics, $0.50/GB ingestion in examples), US East (N. Virginia), unversioned page [S9].
- M2 Micrometer 1.17.1 and the micrometer-bom import in the Quarkus 3.40.1.1 BOM (BOM partly read) [S20][S21].
- M3 Micrometer CloudWatch docs read at 1.17.2, not 1.17.1 [S22].
- M4 aws-embedded-metrics-java README is main-branch [S26].
- M5 Powertools pages are "latest" with a "not viewing the latest version" banner while Central's latest is 2.11.0 [S28][S29][S30].
- M6 `InitDuration` is not a listed `AWS/Lambda` metric (absence of evidence) [S11].
- M7 No Quarkiverse CloudWatch registry (absence of evidence, strongly supported by [S18][S23][S24][S25]).
- M8 EMF lines without `"level"` are dropped when `ApplicationLogLevel` is WARN or higher (inference from two High statements on [S14]).
- M9 A raw EMF line written to `System.out` on the Java runtime with JSON log format stays at the root (from "doesn't double-encode … already JSON encoded" [S13][S15]; AWS recommends testing).
- M10 Quarkus native (`provided.al2023`) gets no Lambda-side JSON application-log capture/filtering unless the runtime honours `AWS_LAMBDA_LOG_FORMAT` / `AWS_LAMBDA_LOG_LEVEL` [S13][S14].
- M11 Default Micrometer binders would publish JVM/system meters as billed custom metrics (inference from [S18] defaults and [S4]).

Coverage limits (L):
- L1 [S35] monitoring-cloudwatchlogs-advanced.html returned no body text.
- L2 [S19] Quarkus logging guide: chars 0–100000 of 199486.
- L3 [S20] Quarkus BOM pom.xml: chars 0–200000 of 318246.
- L4 [S9] pricing page: read as tool summaries in two passes (0–100000, 100000–154061); only quoted figures used.
- L5 [S8] quotas page: only the CloudWatch metrics/API table was inspected.
- L6 [S18] Micrometer guide: tool-estimated ~55,000 characters, answered as summary with short quotes.
- L7 All pages: WebFetch caps verbatim quotes at ~125 characters.

Contradictions found:
- C-1 Powertools metrics page states "CloudWatch EMF supports a max of 9 dimensions per metric" and, on the same page, "Maximum of 30 dimensions" [S28]; the AWS EMF spec says a DimensionSet "MUST NOT contain more than 30 dimension keys" [S1] and CloudWatch allows "up to 30 dimensions" per metric [S4][S6]. Follow the AWS spec (30); treat the Powertools "9" as stale. URLs: https://docs.aws.amazon.com/powertools/java/latest/core/metrics/ vs https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
- C-2 Powertools home says Java "from 17 to 25" [S29]; the Lambda Java logging guide's Powertools SAM walkthrough requires "Java 11" and uses `--runtime java11` [S15]. Treat the Lambda sample as outdated. URLs: https://docs.aws.amazon.com/powertools/java/latest/ vs https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html
- C-3 Micrometer docs page is 1.17.2 [S22] while Quarkus 3.40.1.1 manages 1.17.1 [S20] — version mismatch of the doc, not a content conflict.
- No family fact was contradicted.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Conditional C1(d) | Does `quarkus-micrometer-registry-cloudwatch` exist for Quarkus 3.40? | Resolved: not in Quarkus guide, Quarkiverse docs or Central; fallback = quarkus-micrometer + micrometer-registry-cloudwatch2 1.17.1 | [S18] [S23] [S24] [S25] [S21] (2026-10-28) |
| 1 | Conditional C1(d) | Micrometer version managed by Quarkus 3.40.1.1 | Added: 1.17.1, micrometer-bom imported (medium, partly read) | [S20] [S21] (2026-10-28) |
| 2 | Conditional C1(c) | Powertools metrics on Quarkus | ⚠️ IRRESOLVABLE — no official page mentions Quarkus; tenet says frameworks "not officially supported" | [S28] [S29] [S34] |
| 2 | Conditional C1(b) | aws-embedded-metrics-java status | Resolved: 4.2.0, lastUpdated 2024-08-02; README silent on Quarkus/native/JSON log format (U2 stays unverified) | [S26] [S27] (2026-10-28) |
| 3 | Conditional C3 | EMF vs Lambda JSON log format and log-level filtering for Java | Updated: "no double-encoding" (High), missing level → INFO and filtered (High), combination medium (M8, M9); advanced-controls page empty (L1) | [S13] [S14] [S15] [S16] (2026-10-28) |
| 3 | Conditional C1(d)/(f) | Official statement on push registries in frozen Lambda | ⚠️ IRRESOLVABLE — lifecycle page covers background work generally; nothing specific to metric registries | [S17] [S22] [S31] |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (EMF, aws-embedded-metrics-java, Micrometer, PutMetricData, Powertools, built-in metrics, tenant cardinality/cost, naming and units, native notes)
- [x] Pattern counts driven by domain needs (8 mandatory, 5 conditional, 8 forbidden)
- [x] Every anti-pattern has alternative (❌/✅ for F1–F8; alternatives are High options only, family rule 9)
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (handler ↔ EMF, Logs Insights query, Micrometer sketch)
- [x] Sources dated and linked (S1–S35, 2026-10-28)
- [x] Security documented
- [x] 1+ copy-paste working example (EMF JSON documents; Java classes marked representative, not compiled)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep) or noted as single-source High (A3, A6 are single official sources; per the evidence rule a single versioned/official source does not lower to medium)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in the changelog (I1 → iteration 2, I2 → iteration 3)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1–A8 and F1–F8 — EMF document shape and limits [S1], units [S7], `AWS/` namespace rule [S6], flush before return [S17], bounded dimensions [S1][S18], use of `AWS/Lambda` built-ins [S10][S11].
- **Medium Confidence (validate with user)**: C1 emission path, C2 tenant strategy, C3 log format/level interplay (M8–M10), C4 resolution, C5 cold-start metric; all pricing figures (M1); Micrometer version pairing (M2, M3); library status pages (M4, M5).
- **Low Confidence (must ask human)**: U1–U8, I1 (Powertools on Quarkus), I2 (push registries on frozen Lambdas).
- **Edge Cases (pause)**: Lambda Managed Instances (JSON-only logs, concurrent invocations [S13][S17]) are out of scope; per-tenant dimensions above a bounded set need an ADR (family rule 7); JVM+SnapStart vs native remains an ADR (family rule 3).
- **Emergency Stop**: none triggered — official AWS and Quarkus 3.40 sources exist for every High claim; Quarkus 3.40 is the current LTS.
