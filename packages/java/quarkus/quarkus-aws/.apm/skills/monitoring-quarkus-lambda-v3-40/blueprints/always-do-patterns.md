# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1, EMF specification fetched 2026-10-28. Java bodies are representative and not compiled.

## Contents

- [1. One document, one line](#1-one-document-one-line)
- [2. Timestamp and directive](#2-timestamp-and-directive)
- [3. Flat root members](#3-flat-root-members)
- [4. Document limits](#4-document-limits)
- [5. Units and resolution](#5-units-and-resolution)
- [6. Flush before return](#6-flush-before-return)
- [7. Bounded dimensions](#7-bounded-dimensions)
- [8. Built-in metrics](#8-built-in-metrics)

## 1. One document, one line

"The LogEvent message MUST be a valid JSON object with no additional data at the beginning or end of the LogEvent message string" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). In Lambda "Anything logged to STDOUT is sent to CloudWatch Logs" ([EMF libraries](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Libraries.html)), and Java code may log with "methods on java.lang.System" ([Lambda Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)).

```java
// Quarkus 3.40.1.1 - representative
System.out.println(root.toString());   // single line, nothing before or after the JSON
```

## 2. Timestamp and directive

`_aws` "MUST be an object" holding `CloudWatchMetrics`; a MetricDirective "MUST contain" `Namespace`, `Dimensions` and `Metrics`. `Timestamp` is milliseconds after 1970-01-01 UTC, "no more than 14 days in the past and no more than 2 hours in the future" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)).

`<epoch-ms-now>` in the examples is a placeholder for the current epoch milliseconds, written as a bare JSON number at runtime.

```json
{"_aws":{"Timestamp":<epoch-ms-now>,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service"]],"Metrics":[{"Name":"OrdersPlaced","Unit":"Count"}]}]},"Service":"orders","OrdersPlaced":1}
```

## 3. Flat root members

The root node must contain every target; targets "cannot be nested objects"; a metric target is a number or an array of numbers; a dimension target is a string of 1 to 1024 printable ASCII characters. An invalid DimensionSet is skipped while the others still publish ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)).

```json
{"Service":"orders"}                   // matches Dimensions [["Service"]]
{"ctx":{"Service":"orders"}}           // does NOT match Dimensions [["ctx.Service"]]
```

## 4. Document limits

| Limit | Value | Effect when exceeded |
|---|---|---|
| MetricDefinitions per log event, counted across all directives | 100 | CloudWatch extracts no metrics from the event |
| Values per numeric array | 100 | no metrics extracted from the event |
| Keys per DimensionSet | 30 | the DimensionSet is invalid |
| Document size | 1 MB | document rejected |

The spec's JSON schema checks 100 per directive only and "does not check the total across all MetricDirectives" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). The Powertools page quotes both "9" and "30" dimensions on one page (medium confidence, M13); follow the AWS spec value 30.

```java
// Quarkus 3.40.1.1 - representative: flush a document every 100 metric definitions
if (pendingDefinitions == 100) { flush(); pendingDefinitions = 0; }
```

## 5. Units and resolution

`Unit` must be a CloudWatch unit; default `None`. Valid values: `Seconds | Microseconds | Milliseconds | Bytes | Kilobytes | Megabytes | Gigabytes | Terabytes | Bits | Kilobits | Megabits | Gigabits | Terabits | Percent | Count | Bytes/Second | Kilobytes/Second | Megabytes/Second | Gigabytes/Second | Terabytes/Second | Bits/Second | Kilobits/Second | Megabits/Second | Gigabits/Second | Terabits/Second | Count/Second | None` ([MetricDatum](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)). Data points with different units "are aggregated separately" ([metric concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html)), so one metric keeps one unit. `StorageResolution` is 1 or 60, default 60 ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). Choosing 1 is Ask First ([D4](./ask-first-decisions.md#d4-resolution)).

```json
{"Name":"OrderLatency","Unit":"Milliseconds","StorageResolution":60}
```

## 6. Flush before return

"Lambda freezes the execution environment when the runtime and each extension have completed"; background work not complete at the end resumes only "if Lambda reuses the execution environment" ([execution environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)).

```java
// Quarkus 3.40.1.1 - representative
try { return process(event); } finally { metrics.flush(); }   // synchronous System.out write
```

## 7. Bounded dimensions

"If you unintentionally create metrics based on high-cardinality dimensions (such as requestId), the embedded metric format will by design create a custom metric corresponding to each unique dimension combination"; the root node "MAY contain any other members", so identifiers stay as plain properties ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). Quarkus: tag values "MUST BE of LOW-CARDINALITY" ([Quarkus Micrometer](https://quarkus.io/version/3.40/guides/telemetry-micrometer)). Family rule 7: no unbounded tenant cardinality without an ADR.

```json
{"_aws":{"Timestamp":<epoch-ms-now>,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service","TenantTier"]],"Metrics":[{"Name":"OrdersPlaced","Unit":"Count"}]}]},
 "Service":"orders","TenantTier":"premium","OrdersPlaced":1,"tenantId":"t-123","requestId":"8f0c"}
```

Never put PII or secrets in EMF properties: they are stored as log data (family rule 7). Tenant strategy is Ask First ([D2](./ask-first-decisions.md#d2-tenant-as-dimension-or-in-the-log)).

## 8. Built-in metrics

Lambda "automatically sends metrics about the invocation to Amazon CloudWatch", needs no extra execution-role permission, "and there's no additional charge for these metrics", in 1-minute intervals ([Lambda metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html)). The list is in [cardinality, cost and built-ins](./cardinality-cost-and-builtins.md#built-in-lambda-metrics-not-to-re-emit).

```bash
# Representative - read the built-in metric, do not re-publish it
aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors \
  --dimensions Name=FunctionName,Value=orders-fn --statistics Sum --period 60 \
  --start-time 2026-10-28T00:00:00Z --end-time 2026-10-28T01:00:00Z
```
