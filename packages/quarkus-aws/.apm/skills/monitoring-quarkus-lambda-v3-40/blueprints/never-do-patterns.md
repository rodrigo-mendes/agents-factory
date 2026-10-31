# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1, EMF specification fetched 2026-10-28. Severity wording: low, moderate, high.

## Contents

- [F1. EMF through the Quarkus logger](#f1-emf-through-the-quarkus-logger-severity-high)
- [F2. Unbounded identifiers as dimensions](#f2-unbounded-identifiers-as-dimensions-severity-high)
- [F3. Re-emitting Lambda built-in metrics](#f3-re-emitting-lambda-built-in-metrics-severity-moderate)
- [F4. Namespace starting with AWS/](#f4-namespace-starting-with-aws-severity-moderate)
- [F5. More than 100 metric definitions in one document](#f5-more-than-100-metric-definitions-in-one-document-severity-high)
- [F6. Timestamp in seconds or as a string](#f6-timestamp-in-seconds-or-as-a-string-severity-moderate)
- [F7. Publishing after the handler returns](#f7-publishing-after-the-handler-returns-severity-high)
- [F8. NaN, Infinity or out-of-range values](#f8-nan-infinity-or-out-of-range-values-severity-moderate)

## F1. EMF through the Quarkus logger (severity: high)

The default `quarkus.log.console.format` is `%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n`, which puts data before the JSON; that `quarkus-logging-json` places the text in its own JSON document is (medium confidence), because no page read shows an EMF string passed through it ([Quarkus logging](https://quarkus.io/version/3.40/guides/logging), read to 100,000 of 199,486 characters, L2). EMF requires a JSON object "with no additional data at the beginning or end" and targets on the root ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). Impact: CloudWatch extracts no metric; the failure shows only as EMF validation metrics in the `AWS/Logs` namespace (metric names unverified).

```java
// ❌ WRONG - Quarkus 3.40.1.1
Log.info(emfJson);   // "2026-10-28 10:00:00,123 INFO  [Orders] (main) {...}" or {"message":"{...}"}

// ✅ CORRECT - raw stdout write, one line per EMF document
System.out.println(emfJson);
```

## F2. Unbounded identifiers as dimensions (severity: high)

"Every DimensionSet used creates a new metric"; high-cardinality dimensions create "a custom metric corresponding to each unique dimension combination" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). Quarkus: tag values "MUST BE of LOW-CARDINALITY" ([Quarkus Micrometer](https://quarkus.io/version/3.40/guides/telemetry-micrometer)). Family rule 7: no unbounded tenant dimension without an ADR. Impact: the bill grows with every new value, and metrics cannot be deleted; they expire 15 months after the last data point ([metric concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html)).

```json
// ❌ WRONG - requestId (or an unbounded tenantId) as dimension
{"_aws":{"Timestamp":<epoch-ms-now>,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service","requestId"]],"Metrics":[{"Name":"OrdersPlaced","Unit":"Count"}]}]},"Service":"orders","requestId":"8f0c","OrdersPlaced":1}

// ✅ CORRECT - identifier stays a plain root property
{"_aws":{"Timestamp":<epoch-ms-now>,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service"]],"Metrics":[{"Name":"OrdersPlaced","Unit":"Count"}]}]},"Service":"orders","requestId":"8f0c","OrdersPlaced":1}
```

A tenant dimension for a small known set is an Ask-First decision ([D2](./ask-first-decisions.md#d2-tenant-as-dimension-or-in-the-log)).

## F3. Re-emitting Lambda built-in metrics (severity: moderate)

Lambda already sends `Invocations`, `Errors`, `Throttles`, `Duration`, `ConcurrentExecutions` and more at no additional charge; custom metrics are charged ([Lambda metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html), [metric types](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html)). Impact: duplicate, billed series that can disagree with the authoritative ones (throttled requests are not `Invocations`).

```json
// ❌ WRONG
{"_aws":{"Timestamp":<epoch-ms-now>,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service"]],"Metrics":[{"Name":"Invocations","Unit":"Count"},{"Name":"Errors","Unit":"Count"}]}]},"Service":"orders","Invocations":1,"Errors":0}

// ✅ CORRECT - business outcome only; read AWS/Lambda Errors for function errors
{"_aws":{"Timestamp":<epoch-ms-now>,"CloudWatchMetrics":[{"Namespace":"SaaS/Orders","Dimensions":[["Service"]],"Metrics":[{"Name":"OrdersRejected","Unit":"Count"}]}]},"Service":"orders","OrdersRejected":1}
```

## F4. Namespace starting with `AWS/` (severity: moderate)

"To avoid conflicts with AWS service namespaces, you should not specify a namespace that begins with AWS/" ([PutMetricData](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricData.html)). Impact: collides with or is confused with service namespaces.

```json
// ❌ WRONG
"Namespace": "AWS/Orders"
// ✅ CORRECT
"Namespace": "SaaS/Orders"
```

## F5. More than 100 metric definitions in one document (severity: high)

"If a log event exceeds this limit, CloudWatch does not extract any metrics from it" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). Impact: silent loss of every metric in the event.

```java
// ❌ WRONG - Quarkus 3.40.1.1: one document with 150 MetricDefinitions
for (String m : allMetrics) { directiveMetrics.addObject().put("Name", m); }
System.out.println(root);

// ✅ CORRECT - documents of at most 100 MetricDefinitions
for (List<String> chunk : chunksOf(allMetrics, 100)) { System.out.println(buildDocument(chunk)); }
```

## F6. Timestamp in seconds or as a string (severity: moderate)

Timestamp is an integer of milliseconds, at most 14 days past and 2 hours future; "CloudWatch does not publish metrics that have a time stamp outside this range" ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). Impact: metrics are not published (seconds read as milliseconds fall in 1970).

```json
// ❌ WRONG
"_aws": {"Timestamp": 1793232000, "CloudWatchMetrics": [ ... ]}
// ✅ CORRECT
"_aws": {"Timestamp": <epoch-ms-now>, "CloudWatchMetrics": [ ... ]}
```

## F7. Publishing after the handler returns (severity: high)

The environment is frozen after the invocation; unfinished background work resumes only if the environment is reused, and AWS says to complete it "before the code exits" ([execution environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). Impact: metrics delayed to a later invocation or lost when the environment is reclaimed.

```java
// ❌ WRONG - Quarkus 3.40.1.1
executor.submit(() -> System.out.println(emfJson));
return response;

// ✅ CORRECT
System.out.println(emfJson);
return response;
```

## F8. NaN, Infinity or out-of-range values (severity: moderate)

Values "must be in the range of -2^360 to 2^360" and "special values (for example, NaN, +Infinity, -Infinity) are not supported" ([MetricDatum](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html)); in EMF a value outside the range means "CloudWatch does not publish that metric". Impact: the metric is dropped (how Jackson writes NaN was not researched).

```java
// ❌ WRONG - visits == 0 gives Infinity or NaN
root.put("ConversionRate", orders / visits);

// ✅ CORRECT - skip the metric when undefined
if (visits > 0) { root.put("ConversionRate", (double) orders / visits); }
```
